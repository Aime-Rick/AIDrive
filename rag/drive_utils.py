import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import dotenv
import os
from googleapiclient.http import MediaIoBaseDownload
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from api.utils import get_user_credentials

dotenv.load_dotenv()

mime_types = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".rtf": "application/rtf",
    ".zip": "application/zip",
    ".epub": "application/epub+zip",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".tsv": "text/tab-separated-values",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".odp": "application/vnd.oasis.opendocument.presentation",
    ".svg": "image/svg+xml",
    ".mp4": "application/mp4",
    ".mov": "application/vnd.google-apps.video",
    ".avi": "application/vnd.google-apps.video",
    ".mkv": "application/vnd.google-apps.video",
    ".mp3": "application/vnd.google-apps.audio",
    ".wav": "application/vnd.google-apps.audio",
    ".flac": "application/vnd.google-apps.audio",
    ".aac": "application/vnd.google-apps.audio",    
}

def get_drive_service():
    """Get Google Drive service with user credentials."""
    try:
        creds_data = get_user_credentials()
        if not creds_data:
            raise Exception("No credentials found. Please authenticate first.")
        
        creds_dict = creds_data[0] if creds_data else {}
        
        creds = Credentials(
            token=creds_dict.get("token"),
            refresh_token=creds_dict.get("refresh_token"),
            token_uri=creds_dict.get("token_uri"),
            client_id=creds_dict.get("client_id"),
            client_secret=creds_dict.get("client_secret"),
            scopes=creds_dict.get("scopes", [])
        )
        
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"Error getting Drive service: {e}")
        return None

def upload_to_drive(file_path, file_name, folder_id='root'):
    try:
        service = get_drive_service()
        if not service:
            return None
            
        file_metadata = {"name": file_name, "parents": [folder_id]}
        file_extension = "." + file_name.split(".")[-1] if "." in file_name else ".txt"

        media = MediaFileUpload(
            file_path, mimetype=mime_types.get(file_extension, "application/octet-stream"), resumable=True
        )
        # pylint: disable=maybe-no-member
        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        print(f'File ID: "{file.get("id")}".')
        return file.get("id")

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def get_drive_contents(name=None, folder_id='root'):
    try:
        service = get_drive_service()
        if not service:
            return []
            
        query = "trashed = false"
        if name:
            query += f" and name contains '{name}'"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = service.files().list(q=query, spaces="drive", fields="files(id, name, mimeType)").execute()
        return results.get("files", [])

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def create_drive_folder(folder_name, parent_folder_id=None):
  try:
    service = get_drive_service()
    if not service:
        return None
        
    if parent_folder_id:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }
    else:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

    # pylint: disable=maybe-no-member
    file = service.files().create(body=file_metadata, fields="id").execute()
    print(f'Folder ID: "{file.get("id")}".')
    return file.get("id")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None
  
def download_file(real_file_id):
  """Downloads a file
  Args:
      real_file_id: ID of the file to download
  Returns : IO object with location.

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  # SCOPES = ["https://www.googleapis.com/auth/drive.file",
  #         "https://www.googleapis.com/auth/drive.install",
  #         "https://www.googleapis.com/auth/drive.appdata",
  #         "https://www.googleapis.com/auth/drive.metadata",
  #         "https://www.googleapis.com/auth/drive"]
  # creds = None
  # # The file token.json stores the user's access and refresh tokens, and is
  # # created automatically when the authorization flow completes for the first
  # # time.
  # if os.path.exists("/home/ricko/ai-drive/rag/credentials/token.json"):
  #   creds = Credentials.from_authorized_user_file("/home/ricko/ai-drive/rag/credentials/token.json", SCOPES)
  # # If there are no (valid) credentials available, let the user log in.
  # if not creds or not creds.valid:
  #   if creds and creds.expired and creds.refresh_token:
  #     creds.refresh(Request())
  #   else:
  #     flow = InstalledAppFlow.from_client_secrets_file(
  #         "/home/ricko/ai-drive/rag/credentials/credentials.json", SCOPES
  #     )
  #     creds = flow.run_local_server()
  #   # Save the credentials for the next run
  #   with open("/home/ricko/ai-drive/rag/credentials/token.json", "w") as token:
  #     token.write(creds.to_json())
  try:
    service = get_drive_service()
    if not service:
        return None
        
    file_id = real_file_id

    # pylint: disable=maybe-no-member
    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
      status, done = downloader.next_chunk()
      print(f"Download {int(status.progress() * 100)}.")

  except HttpError as error:
    print(f"An error occurred: {error}")
    file = None

  return file.getvalue() if file else None

