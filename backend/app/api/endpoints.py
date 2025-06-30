from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request # Added Request
from typing import List
import uuid # Added uuid
import logging # Added for logging in handle_query
from pathlib import Path
# from app.config import UPLOAD_DIR # Removed UPLOAD_DIR import
from app.core.ingestion import process_and_ingest_doc
from app.core.qa import generate_answer
from app.core.state import in_memory_storage # Import from state.py

router = APIRouter()

# Global in-memory storage - REMOVED, now imported from app.core.state
# in_memory_storage = {}

@router.post("/upload")
async def upload_documents(request: Request, files: List[UploadFile] = File(...)): # Added request: Request
    if len(files) > 75:
        raise HTTPException(status_code=400, detail="Cannot upload more than 75 files at a time.")
    
    ingestion_results = []
    # Get or create a unique session ID
    session_id = request.session.setdefault('session_id', str(uuid.uuid4()))

    # Initialize storage for the session if it doesn't exist
    if session_id not in in_memory_storage:
        in_memory_storage[session_id] = []

    for file in files:
        try:
            file_content = await file.read()
            # Store file under the specific session_id
            in_memory_storage[session_id].append({"filename": file.filename, "content": file_content})
            
            # Process and ingest the document.
            # Note: process_and_ingest_doc currently processes documents one by one.
            # If it's meant to build a knowledge base for the session, its interaction
            # with in_memory_storage or Qdrant might need to be session-aware.
            result = process_and_ingest_doc(file_content, file.filename)
            ingestion_results.append({"filename": file.filename, "status": "success", "message": result})
        except Exception as e:
            ingestion_results.append({"filename": file.filename, "status": "error", "message": str(e)})

    return {"results": ingestion_results}

@router.post("/query")
async def handle_query(request: Request, query: str = Form(...)):
    logging.info(f"--- Query Request Received ---")
    logging.info(f"Raw query received: '{query}'")

    if not query:
        logging.error("Query is empty or not provided.")
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    session_id = request.session.get('session_id')
    logging.info(f"Session ID from request: {session_id}")

    if not session_id:
        logging.error("No session_id found in request session.")
        raise HTTPException(status_code=400, detail="No session found. Please upload documents first.")

    logging.info(f"Checking in_memory_storage for session_id: {session_id}")
    # Ensure in_memory_storage is accessible here (it should be if imported correctly)
    if session_id not in in_memory_storage:
        logging.error(f"session_id '{session_id}' not found as a key in in_memory_storage.")
        raise HTTPException(status_code=400, detail=f"Session ID {session_id} not found in storage. Please upload documents.")

    if not in_memory_storage[session_id]: # Check if the list of documents for the session is empty
        logging.error(f"No documents (empty list) found in in_memory_storage for session_id '{session_id}'.")
        raise HTTPException(status_code=400, detail=f"No documents found in session {session_id}. Please upload documents again.")

    logging.info(f"Session and documents found for session_id '{session_id}'. Proceeding to generate_answer.")
    try:
        response = generate_answer(query=query, session_id=session_id)
        return response
    except Exception as e:
        logging.error(f"Exception during generate_answer for session_id '{session_id}': {e}", exc_info=True)
        # It's generally better to return a 500 for unexpected server errors from generate_answer
        raise HTTPException(status_code=500, detail=f"An error occurred while generating answer: {str(e)}")