from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, audit, candidates, interviews, jobs, settings as settings_api, users
from app.core.config import settings

app = FastAPI(
    title="ATS API",
    version="1.0.0",
    description="AI-Powered Resume Screening & Applicant Tracking System API",
)

# CORS middleware — must be added before routers
# allow_credentials=True requires specific origins (not wildcard) — security requirement
cors_origins = [origin.strip() for origin in settings.CORS_ORIGIN.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router: login, me, logout
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"],
)

# Users router: admin-only user management
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"],
)

# Jobs router: job management for recruiters and admins
app.include_router(
    jobs.router,
    prefix="/api/v1/jobs",
    tags=["jobs"],
)


# Candidates router: resume upload, CRUD, download
app.include_router(
    candidates.router,
    prefix="/api/v1/candidates",
    tags=["candidates"],
)

# Settings router: admin-only global configuration
app.include_router(
    settings_api.router,
    prefix="/api/v1/settings",
    tags=["settings"],
)

# Interviews router: scheduling and management
app.include_router(
    interviews.router,
    prefix="/api/v1/interviews",
    tags=["interviews"],
)

# Audit router: admin-only immutable audit log viewer
app.include_router(
    audit.router,
    prefix="/api/v1/audit",
    tags=["audit"],
)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint for Docker and load balancer monitoring."""
    return {"status": "healthy"}
