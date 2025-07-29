import os
import uuid
import logging
import shutil
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException, Body

# Import everything we need
from app.utils import (
    extract_zip, 
    load_and_chunk_codebase, 
    VectorStoreManager,
    clone_github_repo
)
from langgraph_graph import stream_graph
from fastapi.responses import Response

log = logging.getLogger(__name__)
router = APIRouter()

SESSIONS_DIR = "sessions"
SESSIONS_CODE_DIR = "sessions_code"

# --- Pydantic Model for GitHub URL Request ---

class RepoURLRequest(BaseModel):
    repo_url: str
    token: Optional[str] = None


# --- Internal Helper Function to Process a Repo ---
def _process_repository(session_code_path: str, session_id: str):
    """Internal function to run the chunking and vector store creation."""
    documents = load_and_chunk_codebase(session_code_path)
    if documents:
        vsm = VectorStoreManager(session_id)
        vsm.create_vector_store(documents)
    else:
        log.warning(f"No documents were found to process for session {session_id}.")

# --- Endpoint 1: For GitHub URL ---
@router.post("/repo/clone")
async def clone_repo_from_url(request: RepoURLRequest):
    """Handles codebase processing from a GitHub URL, with optional token for private repos."""
    session_id = str(uuid.uuid4())
    # IMPORTANT: We will NOT log the token for security reasons.
    log.info(f"Starting new session from URL: {request.repo_url} (token provided: {'yes' if request.token else 'no'})")
    session_code_path = os.path.join(SESSIONS_CODE_DIR, session_id)
    os.makedirs(session_code_path, exist_ok=True)

    try:
        # Pass the token to the cloning utility
        clone_github_repo(request.repo_url, session_code_path, token=request.token)
        _process_repository(session_code_path, session_id)
        return {"session_id": session_id, "message": "Repository cloned and processed successfully."}
    except Exception as e:
        log.error(f"Error processing git repo for session {session_id}: {e}", exc_info=True)
        if os.path.exists(session_code_path):
            shutil.rmtree(session_code_path)
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint 2: For ZIP File Upload ---
@router.post("/repo/upload_zip")
async def upload_repo_from_zip(file: UploadFile = File(...)):
    """Handles codebase processing from a ZIP file upload."""
    session_id = str(uuid.uuid4())
    log.info(f"Starting new session from ZIP: {session_id}")
    session_path = os.path.join(SESSIONS_DIR, session_id)
    session_code_path = os.path.join(SESSIONS_CODE_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)
    os.makedirs(session_code_path, exist_ok=True)
    zip_path = os.path.join(session_path, file.filename)

    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        await file.close()
        
        extract_zip(zip_path, session_code_path)
        _process_repository(session_code_path, session_id)
        return {"session_id": session_id, "message": "ZIP file uploaded and processed successfully."}
    except Exception as e:
        log.error(f"Error processing ZIP file for session {session_id}: {e}", exc_info=True)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
        if os.path.exists(session_code_path):
            shutil.rmtree(session_code_path)
        raise HTTPException(status_code=500, detail=str(e))


# --- The Chat Endpoint remains the same ---
@router.post("/chat/{session_id}")
async def chat_with_agent(session_id: str, query: str = Body(..., embed=True)):
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required.")
    log.info(f"Received chat request for session '{session_id}': '{query}'")
    try:
        full_response = "".join(list(stream_graph(session_id=session_id, query=query)))
        return Response(content=full_response, media_type="text/plain")
    except FileNotFoundError:
        log.error(f"Chat failed for session '{session_id}': Vector store not found.")
        raise HTTPException(status_code=404, detail="Session not found or vector store is missing.")
    except Exception as e:
        log.error(f"An unexpected error occurred during chat for session '{session_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")