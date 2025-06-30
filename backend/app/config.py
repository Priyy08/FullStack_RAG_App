import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Determine the directory where this config.py lives
BASE_DIR = Path(__file__).parent.resolve()

# 2. Construct the full path to the .env file
ENV_PATH = BASE_DIR / ".env"

# 3. Load the .env file (if it exists). This ensures environment variables
#    are injected before we read them below.
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # You may choose to log or warn here if .env is essential.
    print(f"[config] Warning: .env not found at {ENV_PATH!r}. "
          "Ensure environment variables are set by other means if needed.")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "wasserstoff_project")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") # <--- ADD THIS LINE

QDRANT_CLUSTER_URL = os.getenv("QDRANT_CLUSTER_URL")
QDRANT_COLLECTION_NAME=os.getenv("QDRANT_COLLECTION_NAME")

# This can be any model from sentence-transformers
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# LLM model on Groq
LLM_MODEL = "llama3-8b-8192"

# UPLOAD_DIR = "data" # Removed as it's no longer used