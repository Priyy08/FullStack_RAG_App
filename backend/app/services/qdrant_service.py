from qdrant_client import QdrantClient, models
# from sentence_transformers import SentenceTransformer # Removed
from typing import List # Added for type hinting
import uuid

# --- STEP 1: Update imports from config ---
# EMBEDDING_MODEL is no longer used here directly
from app.config import QDRANT_API_KEY, QDRANT_CLUSTER_URL, QDRANT_COLLECTION_NAME
# If EMBEDDING_MODEL was only used here, its import can be removed from config too eventually.


class QdrantService:
    def __init__(self):
        # --- STEP 2: Reconfigure the QdrantClient for Cloud ---
        # The QdrantClient is smart enough to use the key when provided.
        # For Qdrant Cloud, we use the 'url' parameter instead of 'host' and 'port'.
        self.client = QdrantClient(
            url=QDRANT_CLUSTER_URL, 
            api_key=QDRANT_API_KEY,
        )
        # --------------------------------------------------------

        # self.embedding_model = SentenceTransformer(EMBEDDING_MODEL) # Removed
        # Assuming all-MiniLM-L6-v2 which has a dimension of 384.
        # This should ideally be configurable if the model can change.
        self.vector_size = 384
        self.collection_name = QDRANT_COLLECTION_NAME
        # The setup_collection call will now happen on your remote cluster
        self.setup_collection()

    def setup_collection(self):
        """Creates the collection in your Qdrant Cloud cluster if it doesn't exist."""
        try:
            # This request now goes to your cloud instance
            self.client.get_collection(collection_name=self.collection_name)
            print(f"Collection '{self.collection_name}' already exists in Qdrant Cloud.")
        except Exception as e:
            # If it doesn't exist, we create it remotely
            print(f"Collection '{self.collection_name}' not found. Creating it in Qdrant Cloud...")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
            )
            print("Collection created successfully.")


    def upsert_chunks(self, chunks: List[dict]): # Added type hint, chunks now contain 'vector'
        # Chunks are now expected to have a 'vector' key with pre-computed embeddings.
        points = []
        for i, chunk in enumerate(chunks):
            if 'vector' not in chunk:
                # Handle error or skip: chunk is missing pre-computed vector
                print(f"Warning: Chunk at index {i} is missing 'vector'. Skipping.") # Or raise error
                continue

            # vector = self.embedding_model.encode(chunk['text']).tolist() # Removed: vector is pre-computed
            
            # --- STEP 2: THIS IS THE FIX --- (UUID generation logic remains)
            # Instead of using hash(), we generate a stable and valid UUID.
            # We use uuid5 which creates a consistent UUID based on a namespace and a name.
            # This ensures that if you re-upload the same document, you get the same IDs,
            # which is great for preventing duplicates.
            unique_name = f"{chunk['doc_id']}-{chunk['page']}-{chunk['paragraph']}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_name))
            # --------------------------------

            points.append(models.PointStruct(
                id=point_id, # Use the new, valid UUID string
                vector=chunk['vector'], # Use pre-computed vector from chunk
                payload=chunk # Payload should not contain the vector itself if it's large,
                              # but current payload structure is fine.
            ))
            
        if points:
            # This part is now sending valid data
            self.client.upsert(collection_name=self.collection_name, points=points, wait=True)

    def search(self, query_vector: List[float], limit=15): # Signature changed
        # query_vector is now passed directly, no local embedding generation.
        # query_vector = self.embedding_model.encode(query_text).tolist() # Removed
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )
        return [hit.payload for hit in search_result]

# This instance will now connect to your cloud cluster when the app starts.
qdrant_service = QdrantService()