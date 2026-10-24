# Internal Applicant Tracking System (ATS)

An internal applicant-tracking system designed for HR recruiters and administrators. The platform supports candidate tracking, job administration, screening, and structured hiring decisions with a focus on an approachable, accessible, and fast interface.

## Tech Stack
- **Backend:** Python / FastAPI / SQLite
- **Frontend:** Vite (React/Vue)
- **Deployment:** Docker & Docker Compose

## Requirements
- Python 3.10+ (for local development)
- Node.js 18+ (for local development)
- Docker & Docker Compose (for containerized deployment)

## Environment Setup

The application requires environment variables to run. A template is provided in `.env.example`.

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in the required variables. 

### Required API Keys and Secrets

- `SECRET_KEY`: Used for JWT token signing. This **must** be a unique and secure random string.
  - **How to get one:** You can generate a strong random key by running the following command in your terminal:
    ```bash
    python -c "import secrets; print(secrets.token_urlsafe(64))"
    ```
  - **No external third-party API keys** (like OpenAI, Stripe, etc.) are required by default to run the core ATS application.

## Running the Application

### Option 1: Docker (Recommended)
The easiest way to run the application along with its dependencies is using Docker Compose.

```bash
# Build and start the containers
docker-compose up --build
```
This will start:
- Backend API on `http://localhost:8000`
- Frontend Development Server on `http://localhost:5173`

Data is persisted in Docker named volumes (`ats_db_data` and `ats_resume_uploads`).

### Option 2: Local Development
To run the backend and frontend separately for development:

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Application Access
- **Frontend App:** http://localhost:5173
- **API Health Check:** http://localhost:8000/health
