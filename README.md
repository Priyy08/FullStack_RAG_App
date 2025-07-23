# Advanced RAG Application

An advanced RAG (Retrieval Augmented Generation) application that can extract answers from an uploaded knowledge base. It uses Groq LLM API, Qdrant vector database (in-memory for sessions), FastAPI backend, and a React+Vite frontend.

## Live Application Link(Try it out!) : https://full-stack-rag-prpj6a96b-priyy08s-projects.vercel.app/


## Features (after recent updates)

-   **In-Memory Document Handling**: Uploaded documents (up to 75 per session) are processed and stored in memory for the duration of the user's session.
-   **Session-Specific Q&A**: The RAG system retrieves answers only from documents uploaded within the current session.
-   **Data Transience**: Document data is lost when the user session ends (e.g., page refresh with cleared cookies, or session timeout).
-   **Dockerized**: Fully containerized for easy deployment using Docker and Docker Compose.

## Prerequisites

-   [Docker](https://www.docker.com/get-started)
-   [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)
-   A Groq API Key

## Running Locally with Docker Compose

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file in the root of the project directory (next to `docker-compose.yml`) with the following content:
    ```env
    # Required: Your Groq API Key
    GROQ_API_KEY=your_groq_api_key_here

    # Required: A strong secret key for session management
    SESSION_SECRET_KEY=a_very_strong_random_secret_key_here

    # Required: Your Hugging Face API Token (User Access Token with read permissions)
    # This is needed by sentence-transformers to download certain models.
    HF_API_TOKEN=your_hf_api_token_here

    # Optional: Qdrant configuration (if using a persistent/external Qdrant instance)
    # QDRANT_API_KEY=your_qdrant_api_key_if_needed
    # QDRANT_CLUSTER_URL=your_qdrant_cluster_url_if_needed

    # Optional: Comma-separated list of allowed frontend origins for CORS (e.g., your Vercel URL)
    # If not set, backend defaults to allowing http://localhost:3000
    # Example: FRONTEND_ORIGINS=https://your-frontend.vercel.app,http://another-frontend-domain.com
    FRONTEND_ORIGINS=
    ```
    Replace `your_groq_api_key_here`, `a_very_strong_random_secret_key_here`, and `your_hf_api_token_here` with your actual keys.
    Optionally, set `FRONTEND_ORIGINS` if you plan to deploy the frontend to a different URL than the default.

3.  **Build and Run the Application:**
    Open your terminal in the project root and run:
    ```bash
    docker-compose up --build
    ```
    This command will:
    -   Build the Docker images for both the frontend and backend services (if not already built or if changes were made).
    -   Start the containers for both services.
    -   The `--build` flag ensures images are rebuilt if there are changes to Dockerfiles or application code.

4.  **Access the Application:**
    -   **Frontend:** Open your web browser and go to [http://localhost:3000](http://localhost:3000)
    -   **Backend API (for direct access/testing):** Accessible at [http://localhost:8000](http://localhost:8000). For example, a health check might be at `http://localhost:8000/health` (if such an endpoint exists). API calls like `/api/upload` are proxied from the frontend.

5.  **Stopping the Application:**
    To stop the application, press `Ctrl+C` in the terminal where `docker-compose up` is running. To remove the containers, networks, and volumes created by `docker-compose up`, run:
    ```bash
    docker-compose down
    ```

## Deployment to Cloud Platforms

The application is containerized using Docker, making it suitable for deployment to various cloud platforms that support containers. Here's a general outline:

1.  **Build Docker Images:**
    Build production-ready Docker images for the frontend and backend using the provided Dockerfiles.
    ```bash
    docker build -t your-repo/rag-app-backend:latest ./backend/app
    docker build -t your-repo/rag-app-frontend:latest ./frontend
    ```
    Replace `your-repo` with your Docker Hub username or private registry path.

2.  **Push Images to a Container Registry:**
    Push the built images to a container registry like Docker Hub, Google Container Registry (GCR), Amazon Elastic Container Registry (ECR), Azure Container Registry (ACR), etc.
    ```bash
    docker push your-repo/rag-app-backend:latest
    docker push your-repo/rag-app-frontend:latest
    ```

3.  **Deploy to a Cloud Service:**
    Choose a cloud service that can run containers. Examples include:
    -   **AWS:** Elastic Kubernetes Service (EKS), Elastic Container Service (ECS), AWS App Runner.
    -   **Google Cloud:** Google Kubernetes Engine (GKE), Cloud Run.
    -   **Azure:** Azure Kubernetes Service (AKS), Azure Container Instances (ACI), Azure App Service.
    -   **Others:** DigitalOcean App Platform, Heroku (using Docker deploys).

    When deploying:
    -   Ensure the necessary environment variables (especially `GROQ_API_KEY`, `SESSION_SECRET_KEY`, `HF_API_TOKEN`, and `FRONTEND_ORIGINS`) are securely configured in the cloud environment for the backend service.
    -   The `FRONTEND_ORIGINS` variable should be set to the URL(s) of your deployed frontend (e.g., your Vercel app URL) to allow cross-origin requests.
    -   Configure port mappings correctly. The backend typically runs on port 8000 internally, and the frontend (Nginx) on port 80. Your cloud service will provide a way to expose these to the internet, often via load balancers or ingress controllers.
    -   Set up networking so the frontend can reach the backend. If they are deployed as separate services, the frontend will need the backend's internal or external address. The Nginx proxy configuration in the frontend (`proxy_pass http://backend:8000;`) might need to be updated to the backend's actual service discovery name or URL within your cloud environment if not using a simple `backend` hostname.

## Deploying to Vercel (Frontend) and Backend Hosting Alternatives

This section provides guidance on deploying the frontend to Vercel and discusses options for hosting the backend, given Vercel's limitations for this project's current backend architecture on its free tier.

### 1. Deploying the Frontend to Vercel

Vercel is an excellent platform for hosting static frontends like our React+Vite application.

**Steps:**

1.  **Sign up/Login to Vercel:** Use your GitHub, GitLab, or Bitbucket account.
2.  **Create a New Project:**
    *   Click "Add New..." -> "Project".
    *   Import the Git repository containing this application.
3.  **Configure the Project:**
    *   **Framework Preset:** Vercel should automatically detect "Vite". If not, select it.
    *   **Root Directory:** Crucially, set this to `frontend`. This tells Vercel where your frontend code and `package.json` are located.
    *   **Build and Output Settings:**
        *   **Build Command:** Vercel will likely default to `npm run build` (or `vite build`). This should be correct.
        *   **Output Directory:** Vercel will likely default to `dist`. This is correct for Vite.
        *   **Install Command:** Vercel will likely default to `npm install`.
    *   **Environment Variables (Optional for Frontend):**
        *   If your backend is hosted on a different domain (see below), you'll need to set an environment variable for your frontend to know the API endpoint. For example:
            `VITE_API_BASE_URL = https://your-backend-service-url.com`
            Your frontend code (e.g., in `ChatInterface.jsx` or `UploadForm.jsx`) would then use `import.meta.env.VITE_API_BASE_URL` to construct API request URLs.
        *   If you keep the Nginx proxy setup for `/api` calls *and* deploy your backend to a service that Vercel can proxy to (less common for free tier cross-platform), this might not be needed. However, for a distinct backend deployment, `VITE_API_BASE_URL` is standard.
4.  **Deploy:** Click the "Deploy" button. Vercel will build and deploy your frontend.
5.  **Access:** Vercel will provide you with a public URL (e.g., `your-project-name.vercel.app`).

### 2. Backend Deployment Considerations for Vercel

As detailed in previous analyses, deploying the current FastAPI backend (with its in-memory session storage, in-memory Qdrant, and large ML model dependencies) directly to Vercel's free/hobby tier Serverless Functions is **not recommended due to fundamental architectural mismatches and resource limitations.**

Key challenges include:
-   **Statelessness:** Vercel Functions are stateless; our backend's in-memory session data would be lost.
-   **Dependency Size:** Sentence Transformers and PyTorch are likely too large for Vercel's serverless function size limits.
-   **Execution Time:** Processing multiple documents and running embeddings could exceed time limits.

### 3. Alternative Platforms for Hosting the Backend (Docker)

It's recommended to deploy the existing Dockerized FastAPI backend to a platform more suited for long-running Docker containers. The Vercel-hosted frontend will then make API calls to this externally hosted backend.

**Recommended Platforms (Free/Hobby Tiers):**

*   **Render:**
    *   **Deployment:** Deploy as a "Web Service" using Docker. Connect your Git repo, set the "Root Directory" to `backend/app` (or ensure your Dockerfile is at the root of what Render checks out for the service).
    *   **Environment Variables:** Set `GROQ_API_KEY`, `SESSION_SECRET_KEY`, `HF_API_TOKEN`, `FRONTEND_ORIGINS` (to your Vercel frontend URL), etc., in the Render dashboard.
    *   **URL:** Render will provide a public `.onrender.com` URL for your backend. Use this as `VITE_API_BASE_URL` in your Vercel frontend settings.
*   **Fly.io:**
    *   **Deployment:** Use `flyctl` to deploy your backend Docker image.
    *   **Environment Variables:** Set secrets using `flyctl secrets set`.
    *   **URL:** Fly.io provides a public `.fly.dev` URL.
*   **Railway.app:**
    *   **Deployment:** Connect your Git repo; Railway can detect and build from the `backend/app/Dockerfile`.
    *   **Environment Variables:** Configure in the Railway dashboard.
    *   **URL:** Railway provides a public URL.

**General Steps for Backend Deployment on Alternatives:**

1.  Choose a platform from the list above.
2.  Sign up and follow their documentation for deploying a Dockerized web service.
3.  Ensure your backend's `Dockerfile` (located at `backend/app/Dockerfile`) is correctly referenced.
4.  Set the required environment variables (`GROQ_API_KEY`, `SESSION_SECRET_KEY`, `HF_API_TOKEN`, `FRONTEND_ORIGINS`) in the chosen platform's settings. For `FRONTEND_ORIGINS`, use the URL of your Vercel-deployed frontend.
5.  Once deployed, the platform will give you a public URL for your backend (e.g., `https://my-rag-backend.onrender.com`).

### 4. Connecting Vercel Frontend to External Backend

1.  Once your backend is deployed on an alternative platform and you have its public URL.
2.  Go to your Vercel project settings.
3.  Under "Environment Variables", add `VITE_API_BASE_URL` with the value of your backend's public URL (e.g., `https://my-rag-backend.onrender.com`).
4.  **Important:** Your frontend application code (e.g., `axios` instances or `fetch` calls in your `.jsx` files) must be updated to use this environment variable to prefix API calls. For Vite, environment variables prefixed with `VITE_` are exposed to the client-side code via `import.meta.env.VITE_VARIABLE_NAME`.
    For example, instead of `fetch('/api/upload')`, you would use `fetch(\`\${import.meta.env.VITE_API_BASE_URL}/api/upload\`)`.
5.  Redeploy your Vercel frontend if prompted, or new builds will pick up the environment variable.

This hybrid approach (frontend on Vercel, backend on a Docker-friendly PaaS) is common for full-stack applications leveraging the strengths of each platform.
