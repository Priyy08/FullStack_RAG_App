# Stage 1: Base image with Python
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install Tesseract OCR and clean up apt cache
# Tesseract is needed for OCR capabilities in document processing
RUN apt-get update && \
    apt-get install -y tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and group for better security
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

# Copy the application code into the /app/app directory
# The WORKDIR is /app, so this copies host's ./app to container's /app/app
COPY ./app /app/app

# Set environment variable placeholders
# These should be overridden at runtime with actual secrets/configurations
ENV SESSION_SECRET_KEY="changeme_in_production_via_env_var"
ENV GROQ_API_KEY="changeme_in_production_via_env_var"
ENV HF_API_TOKEN="changeme_in_production_via_env_var"
ENV QDRANT_API_KEY="changeme_in_production_via_env_var"
ENV QDRANT_CLUSTER_URL="changeme_in_production_via_env_var"
# Add other ENV vars as needed, e.g., for QDRANT_COLLECTION_NAME if it varies by environment

# Change ownership of the app directory to the new user
# This ensures appuser can write to /app if needed (e.g. for logs, though not currently used)
# and owns the /app/app code directory.
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Command to run the application
# Uvicorn will look for 'app' in 'app.main', which translates to /app/app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
