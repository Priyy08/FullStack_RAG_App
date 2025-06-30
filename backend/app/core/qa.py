import logging # Ensure logging is imported
from collections import defaultdict
from app.services.llm_service import llm_service
from app.core.state import in_memory_storage # Changed import to app.core.state
# Import generate_embeddings_batch from ingestion.py
from app.core.ingestion import extract_text_from_file, text_splitter, generate_embeddings_batch
from qdrant_client import QdrantClient, models
# from sentence_transformers import SentenceTransformer # Removed
# from app.config import EMBEDDING_MODEL # Removed
import uuid
from typing import List # Ensure List is imported for type hints if not already

# The global qdrant_service is no longer used here directly for search,
# as generate_answer will build its own temporary Qdrant index for session data.
# from app.services.qdrant_service import qdrant_service


def generate_answer(query: str, session_id: str): # Signature changed
    """The main two-phase Q&A logic, now session-specific."""
    print(f"\n--- New Query Received for Session {session_id}: '{query}' ---")

    session_files = in_memory_storage.get(session_id, [])
    if not session_files:
        return {
            "individual_answers": [],
            "themed_summary": "No documents found for this session. Please upload documents first.",
            "error": "No documents in session"
        }

    # Embedding model is no longer loaded locally. Vector size is hardcoded for all-MiniLM-L6-v2.
    vector_size = 384

    # Initialize in-memory Qdrant client
    try:
        qdrant_client = QdrantClient(location=":memory:")
        # Using a more generic temp collection name as it's per-call, session_id makes it unique enough if needed for debugging
        temp_collection_name = f"session_query_collection_{session_id}_{str(uuid.uuid4())[:4]}"

        qdrant_client.recreate_collection(
            collection_name=temp_collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE), # Use hardcoded vector_size
        )
    except Exception as e:
        logging.error(f"[QA] Failed to initialize in-memory Qdrant for session {session_id}: {e}")
        return {"error": f"Failed to initialize in-memory Qdrant: {e}"}

    # Process files and chunk them
    all_document_chunks_for_session = []
    for file_info in session_files:
        try:
            # extract_text_from_file returns list of dicts {'page_number': X, 'content': Y}
            pages_data = extract_text_from_file(file_info['content'], file_info['filename'])
            if not pages_data:
                print(f"[QA] No text extracted from file: {file_info['filename']}")
                continue

            for page_idx, page_content in enumerate(pages_data): # Use enumerate for paragraph index if page_content is just text
                # Assuming page_content is a dict like {'page_number': Z, 'content': 'text...'}
                actual_page_content = page_content.get('content', '')
                page_number = page_content.get('page_number', page_idx + 1)

                page_text_chunks = text_splitter.split_text(actual_page_content)

                for para_idx, chunk_text in enumerate(page_text_chunks):
                    all_document_chunks_for_session.append({
                        "doc_id": file_info['filename'],
                        "text": chunk_text,
                        "page": page_number,
                        "paragraph": para_idx + 1,
                    })
        except Exception as e:
            print(f"[QA] 🚨 ERROR: Failed processing file {file_info['filename']}: {e}")
            # Optionally skip this file and continue
            continue

    if not all_document_chunks_for_session:
        return {
            "individual_answers": [],
            "themed_summary": "No text content could be processed from the uploaded documents for this session.",
            "error": "No processable content in session documents"
        }

    # Get embeddings for all chunks using Hugging Face API
    chunk_texts = [chunk['text'] for chunk in all_document_chunks_for_session]

    logging.info(f"[QA] Requesting embeddings for {len(chunk_texts)} chunks using generate_embeddings_batch for session {session_id}...")
    try:
        # Use the new generate_embeddings_batch function
        all_embeddings = generate_embeddings_batch(chunk_texts)

        # generate_embeddings_batch already checks for len(all_embeddings) == len(texts)
        # and raises ValueError if mismatch, or RuntimeError for other API issues.

        for i, chunk_dict in enumerate(all_document_chunks_for_session):
            chunk_dict['vector'] = all_embeddings[i] # Add 'vector' key

    except (ValueError, RuntimeError) as e: # Catch errors from generate_embeddings_batch
        logging.error(f"[QA] Failed to get document chunk embeddings for session {session_id}: {e}")
        return {"error": f"Failed to get document embeddings: {e}"}
    except Exception as e: # Catch any other unexpected errors
        logging.error(f"[QA] Unexpected error during document embedding for session {session_id}: {e}")
        return {"error": f"Unexpected error during document embedding: {e}"}

    # Upsert points (now with pre-computed vectors) to Qdrant
    points_to_upsert = []
    for chunk_with_vector in all_document_chunks_for_session:
        unique_name = f"{chunk_with_vector['doc_id']}-{chunk_with_vector['page']}-{chunk_with_vector['paragraph']}"
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_name))
        points_to_upsert.append(models.PointStruct(
            id=point_id,
            vector=chunk_with_vector['vector'], # Use pre-computed vector
            payload=chunk_with_vector
        ))

    if points_to_upsert:
        try:
            qdrant_client.upsert(collection_name=temp_collection_name, points=points_to_upsert, wait=True)
        except Exception as e:
            logging.error(f"[QA] Failed to upsert points to in-memory Qdrant for session {session_id}: {e}")
            return {"error": f"Failed to upsert points to in-memory Qdrant: {e}"}

    # 1. Get embedding for the query
    logging.info(f"[QA] Requesting query embedding using generate_embeddings_batch for session {session_id}...")
    try:
        # Use the new generate_embeddings_batch function
        query_embeddings = generate_embeddings_batch([query]) # Pass query as a list

        # generate_embeddings_batch returns List[List[float]]. For a single query, this will be [[...]].
        # It also handles the case where API might return just List[float] for single item list and wraps it.
        if not query_embeddings or not query_embeddings[0]: # Check if the outer list or inner list is empty
            logging.error(f"[QA] Failed to get a valid embedding for the query via API for session {session_id}.")
            return {"error": "Failed to generate embedding for the query."}
        query_vector = query_embeddings[0]
    except (ValueError, RuntimeError) as e: # Catch errors from generate_embeddings_batch
        logging.error(f"[QA] Failed to get query embedding for session {session_id}: {e}")
        return {"error": f"Failed to get query embedding: {e}"}
    except Exception as e: # Catch any other unexpected errors
        logging.error(f"[QA] Unexpected error during query embedding for session {session_id}: {e}")
        return {"error": f"Unexpected error during query embedding: {e}"}

    # 2. Retrieve relevant chunks from the temporary session collection
    try:
        search_result = qdrant_client.search(
            collection_name=temp_collection_name,
            query_vector=query_vector,
            limit=15, # Keep limit similar to original
            with_payload=True
        )
        retrieved_chunks = [hit.payload for hit in search_result]
    except Exception as e:
        print(f"[QA] 🚨 ERROR: Failed to search in-memory Qdrant: {e}")
        return {"error": f"Failed to search in-memory Qdrant: {e}"}

    if not retrieved_chunks:
        return {
            "individual_answers": [],
            "themed_summary": "No relevant information found in the uploaded documents for your query.",
            "error": "No relevant chunks found in session documents"
        }

    # Group chunks by document (this logic remains the same)
    chunks_by_doc = defaultdict(list)
    for chunk in retrieved_chunks:
        chunks_by_doc[chunk['doc_id']].append(chunk)

    # 2. Per-Document Extraction
    individual_answers = []
    for doc_id, chunks in chunks_by_doc.items():
        context = "\n".join([f"Page {c['page']}, Paragraph {c['paragraph']}: {c['text']}" for c in chunks])
        prompt = f"""
        Based ONLY on the following context from document '{doc_id}', answer the user's question.
        If the context does not contain the answer, state that.
        Provide the answer and the most relevant citation (page and paragraph).
        Format the output as:
        Answer: [Your answer here]
        Citation: Page [page_number], Para [paragraph_number]

        Context:
        ---
        {context}
        ---
        User Question: {query}
        """
        response = llm_service.get_response(prompt, system_prompt="You are a precise extraction assistant.")
        
        # Simple parsing of the response
        answer_text = response.split("Answer:")[1].split("Citation:")[0].strip()
        citation_text = response.split("Citation:")[1].strip() if "Citation:" in response else "N/A"
        
        individual_answers.append({
            "document_id": doc_id,
            "extracted_answer": answer_text,
            "citation": citation_text
        })
    
    # 3. Cross-Document Synthesis
    synthesis_prompt = f"""
    You are a research analyst. You have been provided with several answers to the question "{query}" from different documents.
    Your task is to identify 1 to 3 main themes or viewpoints from these answers.
    For each theme:
    1. Give it a short, descriptive title (e.g., "Theme 1 - Regulatory Impact").
    2. Write a synthesized summary of the theme based on the provided answers.
    3. Cite the document IDs that support this theme.

    Provided Answers:
    ---
    {individual_answers}
    ---
    """
    themed_summary = llm_service.get_response(synthesis_prompt, system_prompt="You are a research synthesis expert.")

    return {
        "individual_answers": individual_answers,
        "themed_summary": themed_summary,
    }