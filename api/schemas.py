from pydantic import BaseModel
from typing import List, Dict, Any, Literal

# --- Standardized Response Model ---

class StandardResponse(BaseModel):
    status: Literal["success", "error"]
    data: Dict[str, Any] | List[Any] | None = None
    message: str | None = None

# --- Drive and RAG Request Models ---
class UserRequest(BaseModel):
    email: str
    password: str
    
class UploadFileRequest(BaseModel):
    folder_id: str = "root"

class CreateFolderRequest(BaseModel):
    folder_name: str
    parent_folder_id: str = None

class DownloadFileRequest(BaseModel):
    file_id: str

class PopulateVectorDBRequest(BaseModel):
    file_ids: List[str] = None

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

