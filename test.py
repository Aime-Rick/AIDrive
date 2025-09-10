import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from pprint import pprint

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/drive.install",
          "https://www.googleapis.com/auth/drive.appdata",
          "https://www.googleapis.com/auth/drive.metadata",
          "https://www.googleapis.com/auth/drive"]

def main(name=None, folder_id='root'):
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "/home/ricko/ai-drive/rag/credentials/credentials.json", SCOPES
      )
      creds = flow.run_local_server()
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
        service = build("drive", "v3", credentials=creds)

    # file_metadata = {"name": "download.png"}
    # media = MediaFileUpload("download.png", mimetype="image/png")
    # # pylint: disable=maybe-no-member
    # file = (
    #     service.files()
    #     .create(body=file_metadata, media_body=media, fields="id")
    #     .execute()
    # )
    # print(f'File ID: {file.get("id")}')
        query = "trashed = false"
        if name:
            query += f" and name contains '{name}'"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = service.files().list(q=query, pageSize=20, spaces="drive", fields="files(id, name, mimeType)").execute()
        pprint(results, indent=2)

  except HttpError as error:
    print(f"An error occurred: {error}")
    file = None




if __name__ == "__main__":
  main()