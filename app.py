# app.py

import os
import platform
import asyncio
import streamlit as st
import fitz  # PyMuPDF

from retriever import ingest_pdfs_and_store_chroma, retrieve_relevant_chunks_from_chroma
from ask_llm import ask_openrouter
import chromadb
from file_auth import list_pdf_files_in_folder, download_pdf, FOLDER_ID

# ✅ Windows async fix
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

st.set_page_config(page_title="🔆 Solar Assistant", layout="centered")
st.title("🔆 Solar Regulation & Finance Assistant")

# Setup persistent ChromaDB
CHROMA_PATH = "./chroma_db"
if "chroma_collection" not in st.session_state:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    st.session_state["chroma_collection"] = client.get_or_create_collection("solar_docs")

st.markdown("Fetching latest PDF files from Google Drive folder...")

pdf_dir = "./downloaded_pdfs"
os.makedirs(pdf_dir, exist_ok=True)

# Download all PDFs from Google Drive
pdf_files = list_pdf_files_in_folder(FOLDER_ID)
pdf_names = []
pdf_texts = []

for file_id, file_name in pdf_files:
    dest_path = os.path.join(pdf_dir, file_name)
    pdf_names.append(file_name)
    if not os.path.exists(dest_path):  # avoid re-downloading
        download_pdf(file_id, dest_path)
    doc = fitz.open(dest_path)
    full_text = "\n".join([page.get_text() for page in doc])
    pdf_texts.append(full_text)

if pdf_names:
    st.success(f"Found {len(pdf_names)} PDF files from Google Drive: {', '.join(pdf_names)}")
    with st.spinner("🔎 Embedding and storing data in ChromaDB..."):
        ingest_pdfs_and_store_chroma(pdf_texts, pdf_names, st.session_state["chroma_collection"])
else:
    st.error("No PDFs found in the Drive folder.")

user_query = st.text_input("Ask your question:")

if user_query and st.session_state.get("chroma_collection"):
    with st.spinner("🔍 Retrieving relevant context from ChromaDB..."):
        top_chunks, top_chunk_metas = retrieve_relevant_chunks_from_chroma(
            user_query, st.session_state["chroma_collection"]
        )
        context = "\n\n".join(top_chunks)
        response = ask_openrouter(f"Based only on the following context:\n\n{context}\n\nAnswer this:\n{user_query}")

    st.markdown("### 📌 Answer")
    st.success(response.strip())

    with st.expander("🔍 Context Chunks"):
        for i, chunk in enumerate(top_chunks):
            st.markdown(f"**Chunk {i+1}:**")
            st.code(chunk)
