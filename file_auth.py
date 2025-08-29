# file_auth.py

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
import json

load_dotenv()


# Load the environment variable and parse as a dict
service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=["https://www.googleapis.com/auth/drive.readonly"],
)

FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

def list_pdf_files_in_folder(folder_id):
    pdf_files = []
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    results = drive_service.files().list(q=query,fields="files(id, name)").execute()
    for file in results['files']:
        pdf_files.append((file['id'], file['name']))
    return pdf_files

def download_pdf(file_id, dest_path):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.close()

