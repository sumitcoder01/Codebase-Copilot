import os
import uuid
import logging
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import Response 

from app.utils import (
    extract_zip, 
    load_and_chunk_codebase, 
    VectorStoreManager
)
from langgraph_graph import stream_graph

log = logging.getLogger(__name__)
router = APIRouter()

SESSIONS_DIR = "sessions"
SESSIONS_CODE_DIR = "sessions_code"

@router.post("/repo/upload")
async def upload_repo(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    log.info(f"Starting new session: {session_id}")
    session_path = os.path.join(SESSIONS_DIR, session_id)
    session_code_path = os.path.join(SESSIONS_CODE_DIR, session_id)
    zip_path = os.path.join(session_path, file.filename)
    try:
        os.makedirs(session_path, exist_ok=True)
        os.makedirs(session_code_path, exist_ok=True)
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        log.info(f"Saved uploaded zip file to: {zip_path}")
        extract_zip(zip_path, session_code_path)
        documents = load_and_chunk_codebase(session_code_path)
        if documents:
            vsm = VectorStoreManager(session_id)
            vsm.create_vector_store(documents)
        else:
            log.warning(f"No documents were found to process for session {session_id}.")
        return {"session_id": session_id, "message": "Repository processed successfully."}
    except Exception as e:
        log.error(f"Error processing upload for session {session_id}: {e}", exc_info=True)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
        if os.path.exists(session_code_path):
            shutil.rmtree(session_code_path)
        raise HTTPException(status_code=500, detail=f"Failed to process repository: {e}")
    finally:
        await file.close()

@router.post("/chat/{session_id}")
async def chat_with_agent(session_id: str, query: str = Body(..., embed=True)):
    """
    Handles a chat message from the user for a specific session.
    This is now a regular, non-streaming endpoint.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required.")
    log.info(f"Received chat request for session '{session_id}': '{query}'")

    try:
        # 2. Collect all parts of the generator into a single string.
        full_response = "".join(list(stream_graph(session_id=session_id, query=query)))
        
        # 3. Return a regular Response object.
        return Response(content=full_response, media_type="text/plain")
        
    except FileNotFoundError:
        log.error(f"Chat failed for session '{session_id}': Vector store not found.")
        raise HTTPException(status_code=404, detail="Session not found or vector store is missing.")
    except Exception as e:
        log.error(f"An unexpected error occurred during chat for session '{session_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")