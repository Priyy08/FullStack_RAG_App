from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware # Added import
from app.api import endpoints
import os # Re-added os import for environment variables
# from app.config import UPLOAD_DIR # UPLOAD_DIR is no longer used

app = FastAPI(title="Wasserstoff AI Intern Task")

# Create upload directory if it doesn't exist - REMOVED as UPLOAD_DIR is no longer used
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# Add SessionMiddleware - BEFORE CORS or other middlewares that might use session
# Use an environment variable for the secret key, with a fallback for development.
# For production, SESSION_SECRET_KEY should be set to a strong, random string.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", "your-fallback-dev-secret-key-here"),
    same_site="none",    # allow cross-site
    https_only=True
)

# CORS Middleware to allow frontend to connect
# Default allowed origins (for local development)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://full-stack-rag-app.vercel.app",https://pm-wasserstoff-ai-intern-task-5oqy-hxa11czsr-priyy08s-projects.vercel.app","https://pm-wasserstoff-ai-intern-task-5oqy.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Document Research & Theme Identification Chatbot API"}
