import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from retriever import retrieve_relevant_chunks_from_chroma, initialize_chroma_collection  # You'll write the init function
from ask_llm import ask_llm

# Load environment variables from .env
load_dotenv()

# Flask app
app = Flask(__name__)

# --- INITIALIZE CHROMA COLLECTION (run once at startup) ---
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "solar_docs")
chroma_collection = initialize_chroma_collection(CHROMA_PATH, CHROMA_COLLECTION_NAME)


# --- Optional: home and health check routes for monitoring ---
@app.route('/')
def home():
    return '''
    <h1>Solar Assistant Bot Server</h1>
    <p>This server handles POST requests at <code>/chatbot</code> from Google Chat.</p>
    <p>To test, use curl or Postman to POST JSON messages.</p>
    '''

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

# --- GOOGLE CHATBOT main webhook ---
@app.route('/chatbot', methods=['POST'])
def chatbot():
    event = request.json

    # Only respond to user MESSAGE events
    if event.get('type') == 'MESSAGE':
        user_message = event['message']['text']
        # 1. Retrieve relevant document chunks from ChromaDB
        top_chunks, _ = retrieve_relevant_chunks_from_chroma(user_message, chroma_collection)
        # 2. Build prompt for LLM
        context = "\n\n".join(top_chunks)
        prompt = f"Based only on the following context:\n\n{context}\n\nAnswer this:\n{user_message}"
        # 3. Call your LLM module
        bot_response = ask_llm(prompt)
        # 4. Reply to chat with model's response
        return jsonify({"text": bot_response})

    # Return a blank JSON for non-message events (added/removal, etc.)
    return jsonify({})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
