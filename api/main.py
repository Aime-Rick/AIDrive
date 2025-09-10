from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, Response
import google_auth_oauthlib.flow
import os
import tempfile
from api.schemas import (
    StandardResponse, UserRequest, UploadFileRequest, CreateFolderRequest, 
    DownloadFileRequest, PopulateVectorDBRequest, QueryRequest
)
from api.utils import create_user, sign_in_user, sign_out_user, delete_user, save_user_credentials
from rag.drive_utils import upload_to_drive, get_drive_contents, create_drive_folder, download_file
from rag.load import load_any_file, populate_vector_db
from rag.retrieve import generate_answer


# FastAPI app
app = FastAPI()

# Add session middleware for OAuth state management
# Simple in-memory session store (use Redis/DB in production)
session_store = {}

CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/drive.install",
          "https://www.googleapis.com/auth/drive.appdata",
          "https://www.googleapis.com/auth/drive.metadata",
          "https://www.googleapis.com/auth/drive"]  # Scope for Google Ads

REDIRECT_URI = "http://localhost:8000/oauth2callback"


@app.post("/users/signup", response_model=StandardResponse, tags=["Users"])
async def create_new_user(request: UserRequest):
    """Creates a new user."""
    try:
        response = create_user(request.email, request.password)
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"User creation failed: {e}")


@app.post("/users/signin", response_model=StandardResponse, tags=["Users"])
async def sign_in_existing_user(request: UserRequest):
    """Signs in a user."""
    try:
        response = sign_in_user(request.email, request.password)
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Sign in failed: {e}")


@app.post("/users/signout", response_model=StandardResponse, tags=["Users"])
async def sign_out_current_user():
    """Signs out the current user."""
    try:
        response = sign_out_user()
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sign out failed: {e}")
    
@app.delete("/users/{user_id}", response_model=StandardResponse, tags=["Users"])
async def delete_user_api(user_id: str):
    """Deletes a user by their ID."""
    try:
        response = delete_user(user_id)
        return {"status": "success", "data": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User deletion failed: {e}")


# app.get("/entry")
# def index():
#     return HTMLResponse(
#         '<h1>Google Ads OAuth2</h1>'
#         '<a href="/authorize">Authorize with Google</a>'
#     )

@app.get("/authorize")
def authorize(request: Request):
    """Step 1: Redirect user to Google's OAuth2 consent screen."""
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type="offline",           # ensures we get a refresh token
        include_granted_scopes="true",   # incremental auth
        prompt="consent"                 # force user consent screen
    )

    # Store state in session
    # Simple session management - in production use proper session middleware
    session_store["oauth_state"] = state

    return RedirectResponse(authorization_url)

@app.get("/oauth2callback")
def oauth2callback(request: Request):
    """Step 2: Handle Google's redirect and exchange code for tokens."""
    state = session_store.get("oauth_state")

    # Recreate flow object with state
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = REDIRECT_URI

    # Full redirect URL (includes ?code=...)
    authorization_response = str(request.url)

    # Exchange auth code for tokens
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    # Save tokens in session (in real app: save securely in DB)
    creds = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes)
    }
    save_user_credentials(creds)
    return {"status": "success", "data": "Credentials saved successfully."}


# --- Drive Management Endpoints ---

@app.post("/drive/upload", response_model=StandardResponse, tags=["Drive"])
async def upload_file_to_drive(
    file: UploadFile = File(...),
    folder_id: str = "root"
):
    """Upload a file to Google Drive."""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Upload to Drive
        file_id = upload_to_drive(temp_file_path, file.filename, folder_id)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        if file_id:
            return {"status": "success", "data": {"file_id": file_id, "message": "File uploaded successfully"}}
        else:
            raise HTTPException(status_code=500, detail="Failed to upload file to Drive")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@app.get("/drive/files", response_model=StandardResponse, tags=["Drive"])
async def get_drive_files(name: str = None, folder_id: str = "root"):
    """Get files from Google Drive."""
    try:
        files = get_drive_contents(name=name, folder_id=folder_id)
        return {"status": "success", "data": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {e}")


@app.post("/drive/folder", response_model=StandardResponse, tags=["Drive"])
async def create_folder(request: CreateFolderRequest):
    """Create a new folder in Google Drive."""
    try:
        folder_id = create_drive_folder(request.folder_name, request.parent_folder_id)
        if folder_id:
            return {"status": "success", "data": {"folder_id": folder_id, "message": "Folder created successfully"}}
        else:
            raise HTTPException(status_code=500, detail="Failed to create folder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Folder creation failed: {e}")


@app.post("/drive/download", tags=["Drive"])
async def download_and_load_file(request: DownloadFileRequest):
    """Download a file from Google Drive and load it to Supabase."""
    try:
        # Get file info first
        files = get_drive_contents()
        target_file = None
        for file in files:
            if file['id'] == request.file_id:
                target_file = file
                break
        
        if not target_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file extension
        file_name = target_file['name']
        ext = "." + file_name.split(".")[-1] if "." in file_name else ""
        
        # Load file to database
        load_any_file(request.file_id, ext)
        
        return {"status": "success", "data": {"message": "File downloaded and loaded to database successfully"}}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download and load failed: {e}")


# --- Vector Database Endpoints ---

@app.post("/vector-db/populate", response_model=StandardResponse, tags=["Vector Database"])
async def populate_vector_database(request: PopulateVectorDBRequest):
    """Populate the vector database with files from Google Drive."""
    try:
        if request.file_ids:
            # Get file info for specific files
            all_files = get_drive_contents()
            target_files = [f for f in all_files if f['id'] in request.file_ids]
        else:
            # Get all files if no specific files provided
            target_files = get_drive_contents()
        
        populate_vector_db(target_files)
        
        return {
            "status": "success", 
            "data": {
                "message": f"Vector database populated with {len(target_files)} files",
                "processed_files": len(target_files)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector database population failed: {e}")


@app.post("/vector-db/initialize", response_model=StandardResponse, tags=["Vector Database"])
async def initialize_vector_database():
    """Initialize and populate the vector database with all files from Google Drive."""
    try:
        files = get_drive_contents()
        populate_vector_db(files)
        
        return {
            "status": "success", 
            "data": {
                "message": f"Vector database initialized with {len(files)} files",
                "total_files": len(files)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector database initialization failed: {e}")


# --- RAG Query Endpoint ---

@app.post("/rag/query", response_model=StandardResponse, tags=["RAG"])
async def query_documents(request: QueryRequest):
    """Generate an answer based on user query using RAG."""
    try:
        answer = generate_answer(request.query, request.top_k)
        
        return {
            "status": "success", 
            "data": {
                "query": request.query,
                "answer": answer
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {e}")


# --- Health Check ---

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "success", "data": {"message": "API is running"}}

