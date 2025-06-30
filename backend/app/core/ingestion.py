import os
import io
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
# import requests # Removed, InferenceClient handles HTTP
import logging
from typing import List
from huggingface_hub import InferenceClient # Added
import numpy as np # Added for ndarray handling

# from app.config import UPLOAD_DIR # Removed UPLOAD_DIR import
from app.services.qdrant_service import qdrant_service

# --- IMPORT THE NEW, POWERFUL TEXT SPLITTER ---
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# --- CONFIGURE THE TEXT SPLITTER ---
# This splitter is the industry standard for robustly chunking documents.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # Target size for each chunk in characters
    chunk_overlap=150,  # Number of characters to overlap between chunks
    length_function=len,
    is_separator_regex=False,
    separators=["\n\n", "\n", " ", ""] # How it tries to split text, in order of priority
)

# --- Hugging Face InferenceClient Initialization ---
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
HF_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

if not HF_API_TOKEN:
    logging.warning("HF_API_TOKEN not set in environment variables. InferenceClient might fail for protected models or if rate limits are hit.")

try:
    inference_client = InferenceClient(token=HF_API_TOKEN)
    logging.info(f"HuggingFace InferenceClient initialized. Using model: {HF_MODEL_ID} for feature extraction when called.")
except Exception as e:
    logging.error(f"Failed to initialize HuggingFace InferenceClient: {e}", exc_info=True)
    inference_client = None # Set to None to indicate failure, will be checked in generate_embeddings_batch

# --- New Embedding Function using InferenceClient ---
def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    if not inference_client:
        logging.error("HuggingFace InferenceClient is not available.")
        raise RuntimeError("HuggingFace InferenceClient not initialized properly.")
    if not texts:
        return []

    try:
        embeddings_output = inference_client.feature_extraction(text=texts, model=HF_MODEL_ID)
        # logging.info(f"HF API raw response type: {type(embeddings_output)}") # Keep for debugging if desired
        # logging.info(f"HF API raw response value: {str(embeddings_output)[:1000]}") # Log part of value

        if isinstance(embeddings_output, np.ndarray):
            # Convert numpy.ndarray to list of lists
            embeddings_list = embeddings_output.tolist()
            # logging.info(f"Converted np.ndarray of shape {embeddings_output.shape} to list.")
        elif isinstance(embeddings_output, list):
            # If it's already a list (e.g. list of lists, or list of floats for single input)
            embeddings_list = embeddings_output
        else:
            logging.error(f"HF API returned an unexpected type: {type(embeddings_output)}. Value: {str(embeddings_output)[:500]}")
            raise ValueError(f"Unsupported type from Hugging Face API: {type(embeddings_output)}")

        # Validation logic (now applied to embeddings_list)
        # This validation expects List[List[float]]
        if not (isinstance(embeddings_list, list) and \
                all(isinstance(emb, list) and all(isinstance(f, (float, int)) for f in emb) for emb in embeddings_list)):

            # Handle case where a single text input might have returned a single embedding (List[float])
            # which after tolist() (if it was np.array([1,2,3])) would be List[float]
            # or if API returned List[float] directly for single input.
            if isinstance(embeddings_list, list) and len(texts) == 1 and \
               all(isinstance(f, (float, int)) for f in embeddings_list): # Allow int if numpy converts e.g. 0.0 to 0
                # logging.info("HF API (or numpy conversion) resulted in a flat list for single text input. Wrapping it to List[List[float]].")
                # Ensure all elements are float if they were int
                return [[float(f) for f in embeddings_list]]

            logging.error(f"Post-conversion, embeddings are not in List[List[float]] format. Type: {type(embeddings_list)}. Value: {str(embeddings_list)[:500]}")
            raise ValueError("Embeddings from Hugging Face API, after processing, are not in the expected format (List[List[float]]).")

        # Ensure all numbers within are floats and counts match
        if len(embeddings_list) != len(texts):
            logging.error(f"Mismatched number of embeddings after processing. Expected {len(texts)}, got {len(embeddings_list)}.")
            raise ValueError("Mismatched number of embeddings from Hugging Face API after processing.")

        final_embeddings = [[float(f) for f in emb] for emb in embeddings_list]
        return final_embeddings

    except Exception as e:
        logging.error(f"Error during HuggingFace feature_extraction or subsequent processing: {e}", exc_info=True)
        raise RuntimeError(f"Failed to generate embeddings via HuggingFace API: {e}")
# --- End of New Embedding Function ---

def process_and_ingest_doc(file_content: bytes, filename: str): # Signature changed
    """
    Processes a single document, chunks it intelligently, gets embeddings via HF InferenceClient, and prepares for ingestion.
    This version uses a robust, page-aware chunking strategy.
    """
    print(f"\n--- [INGESTION] Starting processing for: {filename} ---") # Used filename as doc_id

    # The extract_text_from_file function now returns a list of page content
    # file_path.suffix won't work, so we need to pass filename to extract_text_from_file
    pages_data = extract_text_from_file(file_content, filename)
    
    if not pages_data:
        print(f"[INGESTION] 🚨 WARNING: No text was extracted from {filename}. Ingestion skipped.")
        return f"Warning: No text could be extracted from {filename}."

    print(f"[INGESTION] Extracted content from {len(pages_data)} pages.")

    all_chunks = []
    # Process each page's content separately to preserve page numbers
    for page in pages_data:
        # Use the powerful text_splitter on this page's content
        page_chunks = text_splitter.split_text(page['content'])
        
        for i, chunk_text in enumerate(page_chunks):
            all_chunks.append({
                "doc_id": filename, # Used filename as doc_id
                "text": chunk_text,
                "page": page['page_number'],
                "paragraph": i + 1,  # This is now the chunk number within the page
            })

    if not all_chunks:
        print(f"[INGESTION] 🚨 WARNING: Text was extracted, but no valid chunks were created for {filename}.")
        return f"Warning: No valid chunks were created for {filename}."

    print(f"[INGESTION] Created a total of {len(all_chunks)} chunks for {filename}.")

    # Get embeddings for all chunks using Hugging Face API
    chunk_texts = [chunk['text'] for chunk in all_chunks]

    if not chunk_texts:
        print(f"[INGESTION] No text in chunks to embed for {filename}.")
        # This case should ideally be caught by "no valid chunks were created"
        return f"Warning: No text content in chunks for {filename}."

    print(f"[INGESTION] Requesting embeddings for {len(chunk_texts)} chunks using InferenceClient for {filename}...")
    try:
        # Replace call to old function with the new one
        embeddings = generate_embeddings_batch(chunk_texts)

        # The check for len(embeddings) != len(all_chunks) is now inside generate_embeddings_batch
        # or should be re-verified if generate_embeddings_batch could return partial results on error.
        # Assuming generate_embeddings_batch raises an error or returns correctly sized list.

        for i, chunk in enumerate(all_chunks):
            chunk['vector'] = embeddings[i] # Add 'vector' key to each chunk

    except RuntimeError as e: # Catch RuntimeError from generate_embeddings_batch
        # Using print for user-facing messages in process_and_ingest_doc as before, logging is used within generate_embeddings_batch
        print(f"[INGESTION] 🚨 CRITICAL: Failed to get embeddings for {filename}. Error: {e}")
        return f"Error: Failed to get embeddings for {filename} due to: {e}"
    except Exception as e: # Catch any other unexpected errors during embedding
        print(f"[INGESTION] 🚨 CRITICAL: Unexpected error during embedding process for {filename}. Error: {e}")
        return f"Error: Unexpected error during embedding for {filename} due to: {e}"

    print(f"[INGESTION] Embeddings received. Upserting {len(all_chunks)} chunks with vectors to Qdrant for {filename}...")
    
    try:
        # IMPORTANT: qdrant_service.upsert_chunks will need modification in the next step
        # to accept chunks that already contain a 'vector' field and not try to embed them again.
        qdrant_service.upsert_chunks(all_chunks)
        print(f"[INGESTION] ✅ Successfully initiated ingestion for {len(all_chunks)} chunks from {filename}.")
        return f"Successfully initiated ingestion for {len(all_chunks)} chunks from {filename}."
    except Exception as e:
        print(f"[INGESTION] 🚨 CRITICAL: Failed to upsert pre-embedded chunks to Qdrant for {filename}. Error: {e}")
        return f"Error: Failed to upsert pre-embedded chunks to Qdrant for {filename}."

def extract_text_from_file(file_content: bytes, filename: str) -> List[dict]: # Signature changed, ensure List is from typing
    """
    Extracts text from various file types, returning a list of dictionaries,
    where each dictionary represents a page and its content.
    """
    # Determine file extension from filename
    extension = Path(filename).suffix.lower() # Used Path here just for suffix, consider os.path.splitext

    if extension == ".pdf":
        return extract_text_from_pdf(file_content, filename) # Pass content and filename
    elif extension in [".png", ".jpg", ".jpeg"]:
        try:
            image = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(image)
            # For single images, treat it as a single page
            return [{"page_number": 1, "content": text}] if text else []
        except Exception as e:
            print(f"[EXTRACT-IMG] Error processing image {filename}: {e}")
            return []
    elif extension == ".txt":
        try:
            text = file_content.decode('utf-8')
            # For text files, treat it as a single page
            return [{"page_number": 1, "content": text}] if text else []
        except UnicodeDecodeError as e:
            print(f"[EXTRACT-TXT] Error decoding text file {filename} as UTF-8: {e}. Trying with 'latin-1'.")
            try:
                text = file_content.decode('latin-1') # Fallback for other common encodings
                return [{"page_number": 1, "content": text}] if text else []
            except Exception as e_latin1:
                print(f"[EXTRACT-TXT] Error decoding text file {filename} with 'latin-1': {e_latin1}")
                return []
        except Exception as e:
            print(f"[EXTRACT-TXT] Error processing text file {filename}: {e}")
            return []
    else:
        print(f"[EXTRACT] Unsupported file type: {extension} for file {filename}")
        return []

def extract_text_from_pdf(file_content: bytes, filename: str) -> list[dict]: # Signature changed
    """
    Extracts text from a PDF page by page using file content.
    """
    pages_content = []
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        for page_num, page in enumerate(doc):
            text = page.get_text().strip()
            if not text:  # If page has no text, try OCR
                print(f"[EXTRACT-PDF] Page {page_num+1} of {filename} has no text, attempting OCR...")
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img).strip()

            if text:
                pages_content.append({
                    "page_number": page_num + 1,
                    "content": text
                })
        doc.close() # Close the document
        print(f"[EXTRACT-PDF] Found content on {len(pages_content)} pages in {filename}.")
    except Exception as e:
        print(f"[EXTRACT-PDF] Error processing PDF {filename}: {e}")
        # Ensure doc is closed if it was opened
        if 'doc' in locals() and doc:
            doc.close()
        return [] # Return empty list on error
    return pages_content