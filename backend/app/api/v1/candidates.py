"""Candidates API router — upload, CRUD, and download endpoints.

All endpoints require JWT authentication with at least recruiter role.
Resume files are stored at RESUME_DIR with UUID filenames for security.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import String
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.core.parser import determine_parse_status, extract_text, parse_resume_text
from app.core.screening import ScreeningEngine
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.screening_result import ScreeningResult
from app.models.user import User
from app.schemas.candidate import CandidateListResponse, CandidateResponse, CandidateUpdate
from app.schemas.screening import ScreeningResultResponse, ScreeningTriggerResponse

router = APIRouter()

# --- Constants ---
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _redact_candidate(resp: "CandidateResponse") -> "CandidateResponse":
    """Redact PII from a candidate response for anonymous screening (D-02, D-04).

    Replaces name with 'Candidate #{id}', clears email, phone, and personal URLs.
    """
    resp.name = f"Candidate #{resp.id}"
    resp.email = None
    resp.phone = None
    resp.linkedin_url = None
    resp.github_url = None
    resp.portfolio_url = None
    resp.resume_path = None
    resp.original_filename = None
    return resp
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
BROWSER_FALLBACK_MIME_TYPES = {
    "application/octet-stream",
    "binary/octet-stream",
    "application/x-pdf",
    "application/x-download",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per D-12

# Use relative path for local development, absolute path for Docker
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_parent_dir = os.path.dirname(_base_dir)
RESUME_DIR = os.getenv("RESUME_DIR", os.path.join(_parent_dir, "data", "resumes"))

# Magic bytes for file content validation
_PDF_MAGIC = b"%PDF"
_DOCX_MAGIC = b"PK\x03\x04"


def _validate_file(filename: str, content: bytes, content_type: str) -> tuple[str, str]:
    """Validate uploaded file. Returns (extension, error_message|None).

    Checks: extension, size, emptiness, MIME type, magic bytes.
    Raises HTTPException 422 on validation failure.
    """
    # 1. Extension check
    ext = os.path.splitext(filename)[1].lower() if filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF and DOCX files are accepted.",
        )

    # 2. Empty file check
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This file appears to be damaged and cannot be processed.",
        )

    # 3. File size check
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File exceeds 10 MB limit.",
        )

    # 4. MIME type check
    allowed_mime = content_type in ALLOWED_MIME_TYPES or content_type in BROWSER_FALLBACK_MIME_TYPES
    if content_type and not allowed_mime:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid file type. Only PDF and DOCX files are accepted.",
        )

    # 5. Magic bytes validation
    if ext == ".pdf" and not content[:4].startswith(_PDF_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid file type. Only PDF and DOCX files are accepted.",
        )
    if ext == ".docx" and not content[:4].startswith(_DOCX_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid file type. Only PDF and DOCX files are accepted.",
        )

    return ext


def _process_upload(
    content: bytes,
    ext: str,
    original_filename: str,
    job_id: Optional[int],
    db: Session,
) -> Candidate:
    """Process a validated upload: save file, parse, create/update candidate.

    Returns the Candidate ORM instance.
    Raises HTTPException 422 if file cannot be parsed.
    """
    # Generate UUID filename
    uuid_filename = f"{uuid.uuid4()}{ext}"
    os.makedirs(RESUME_DIR, exist_ok=True)
    file_path = os.path.join(RESUME_DIR, uuid_filename)

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text
    raw_text = extract_text(file_path)
    if not raw_text or not raw_text.strip():
        # Cleanup the file on parse failure
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This file appears to be damaged and cannot be processed.",
        )

    # Parse resume text
    parsed = parse_resume_text(raw_text)
    parse_status = determine_parse_status(parsed)

    # Check for duplicate email (D-15)
    existing_candidate = None
    if parsed.get("email"):
        existing_candidate = (
            db.query(Candidate).filter(Candidate.email == parsed["email"]).first()
        )

    if existing_candidate:
        # Update existing candidate with new parsed data
        existing_candidate.name = parsed.get("name") or existing_candidate.name
        existing_candidate.phone = parsed.get("phone") or existing_candidate.phone
        existing_candidate.location = parsed.get("location") or existing_candidate.location
        existing_candidate.linkedin_url = parsed.get("linkedin_url") or existing_candidate.linkedin_url
        existing_candidate.github_url = parsed.get("github_url") or existing_candidate.github_url
        existing_candidate.portfolio_url = parsed.get("portfolio_url") or existing_candidate.portfolio_url
        existing_candidate.skills = parsed.get("skills", existing_candidate.skills)
        existing_candidate.education = parsed.get("education", existing_candidate.education)
        existing_candidate.experience = parsed.get("experience", existing_candidate.experience)
        existing_candidate.projects = parsed.get("projects", existing_candidate.projects)
        existing_candidate.certifications = parsed.get("certifications", existing_candidate.certifications)
        existing_candidate.achievements = parsed.get("achievements", existing_candidate.achievements)

        # Remove old resume file if it exists and differs
        if existing_candidate.resume_path and existing_candidate.resume_path != file_path:
            old_path = existing_candidate.resume_path
            if os.path.exists(old_path):
                os.remove(old_path)

        existing_candidate.resume_path = file_path
        existing_candidate.original_filename = original_filename
        existing_candidate.status = parse_status
        existing_candidate.updated_at = datetime.utcnow()

        candidate = existing_candidate

        # Link to job if provided (D-16)
        if job_id is not None:
            existing_app = (
                db.query(Application)
                .filter(
                    Application.job_id == job_id,
                    Application.candidate_id == candidate.id,
                )
                .first()
            )
            if not existing_app:
                app_record = Application(job_id=job_id, candidate_id=candidate.id)
                db.add(app_record)
    else:
        # Create new candidate
        now = datetime.utcnow()
        candidate = Candidate(
            name=parsed.get("name"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            location=parsed.get("location"),
            linkedin_url=parsed.get("linkedin_url"),
            github_url=parsed.get("github_url"),
            portfolio_url=parsed.get("portfolio_url"),
            skills=parsed.get("skills", []),
            education=parsed.get("education", []),
            experience=parsed.get("experience", []),
            projects=parsed.get("projects", []),
            certifications=parsed.get("certifications", []),
            achievements=parsed.get("achievements", []),
            resume_path=file_path,
            original_filename=original_filename,
            status=parse_status,
            created_at=now,
            updated_at=now,
        )
        db.add(candidate)
        db.flush()  # Get candidate.id for application linking

        # Link to job if provided (D-14)
        if job_id is not None:
            app_record = Application(job_id=job_id, candidate_id=candidate.id)
            db.add(app_record)

    db.commit()
    db.refresh(candidate)

    # Auto-trigger screening when linked to a job (SCR-01)
    if job_id is not None:
        try:
            _run_screening(candidate.id, job_id, db)
        except Exception:
            pass  # Non-fatal: screening can be re-triggered manually

    return candidate


# ---------------------------------------------------------------------------
# Screening helper
# ---------------------------------------------------------------------------


def _run_screening(
    candidate_id: int,
    job_id: int,
    db: Session,
) -> ScreeningResult:
    """Run the ScreeningEngine for a candidate-job pair.

    Upserts (create or update) the ScreeningResult for the application.
    Idempotent — re-running updates the existing result.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")

    # Fetch or create Application record
    application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate_id,
            Application.job_id == job_id,
        )
        .first()
    )
    if not application:
        application = Application(candidate_id=candidate_id, job_id=job_id)
        db.add(application)
        db.flush()

    # Run scoring engine
    engine = ScreeningEngine()
    result_data = engine.screen(candidate, job)

    # Upsert screening result
    existing = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.application_id == application.id)
        .first()
    )
    if existing:
        for field, value in result_data.items():
            setattr(existing, field, value)
        screening_result = existing
    else:
        screening_result = ScreeningResult(
            application_id=application.id,
            **result_data,
        )
        db.add(screening_result)

    db.commit()
    db.refresh(screening_result)
    return screening_result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    job_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> CandidateResponse:
    """Upload a single PDF/DOCX resume.

    Validates file, extracts text, parses profile, and creates/updates candidate.
    Duplicate emails update the existing candidate and link to the new job.
    """
    content = await file.read()
    ext = _validate_file(file.filename or "", content, file.content_type or "")
    candidate = _process_upload(content, ext, file.filename or "unknown", job_id, db)
    return CandidateResponse.model_validate(candidate)


@router.post("/upload-batch", status_code=status.HTTP_200_OK)
async def upload_batch(
    files: List[UploadFile] = File(...),
    job_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> dict:
    """Upload multiple resumes. Processes all files; reports per-file status."""
    results: list[dict] = []

    for upload_file in files:
        try:
            content = await upload_file.read()
            ext = _validate_file(
                upload_file.filename or "", content, upload_file.content_type or ""
            )
            candidate = _process_upload(
                content, ext, upload_file.filename or "unknown", job_id, db
            )
            results.append(
                {
                    "filename": upload_file.filename,
                    "status": "success",
                    "candidate": CandidateResponse.model_validate(candidate).model_dump(mode="json"),
                    "error": None,
                }
            )
        except HTTPException as exc:
            results.append(
                {
                    "filename": upload_file.filename,
                    "status": "error",
                    "candidate": None,
                    "error": exc.detail,
                }
            )

    return {"results": results}


@router.get("/", response_model=CandidateListResponse)
def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Search by name, email, or skills"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: name, email, created_at, status"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    skills_filter: Optional[str] = Query(None, alias="skills", description="Comma-separated skills to filter by"),
    location_filter: Optional[str] = Query(None, alias="location"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> CandidateListResponse:
    """List candidates with search, sort, filter, and pagination (CAND-01).

    Supports text search across name/email/skills, status filtering,
    skills filtering, location filtering, and configurable sort order.
    """
    from app.core.audit import log_audit_action

    query = db.query(Candidate)

    # Status filter
    if status_filter:
        query = query.filter(Candidate.status == status_filter)

    # Text search across name, email, skills JSON
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Candidate.name.ilike(search_term))
            | (Candidate.email.ilike(search_term))
            | (Candidate.skills.cast(String).ilike(search_term))
        )

    # Skills filter (comma-separated, match any)
    if skills_filter:
        for skill in skills_filter.split(","):
            skill_term = f"%{skill.strip()}%"
            query = query.filter(Candidate.skills.cast(String).ilike(skill_term))

    # Location filter
    if location_filter:
        query = query.filter(Candidate.location.ilike(f"%{location_filter}%"))

    # Sort — whitelist allowed sort fields to prevent SQL injection
    allowed_sort_fields = {"name", "email", "created_at", "status", "location"}
    sort_field = sort_by if sort_by in allowed_sort_fields else "created_at"
    sort_column = getattr(Candidate, sort_field)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()
    candidates = query.offset(skip).limit(limit).all()

    # Audit log the listing action (D-09)
    log_audit_action(
        db=db,
        user=current_user,
        action="candidate.list",
        resource_type="candidate",
        metadata={"search": search, "filters": {"status": status_filter, "skills": skills_filter}},
    )
    db.commit()

    # Apply anonymous screening redaction (D-02, D-04)
    from app.api.v1.settings import is_anonymous_screening_enabled

    anonymous = is_anonymous_screening_enabled(db)

    items = []
    for c in candidates:
        resp = CandidateResponse.model_validate(c)
        if anonymous and current_user.role != "admin":
            resp = _redact_candidate(resp)
        items.append(resp)

    return CandidateListResponse(items=items, total=total)


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> CandidateResponse:
    """Get a single candidate by ID. Applies anonymous redaction if enabled (D-02)."""
    from app.api.v1.settings import is_anonymous_screening_enabled

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )
    resp = CandidateResponse.model_validate(candidate)
    if is_anonymous_screening_enabled(db) and current_user.role != "admin":
        resp = _redact_candidate(resp)
    return resp


@router.patch("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: int,
    update_data: CandidateUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> CandidateResponse:
    """Update candidate fields. Auto-promotes pending_review → complete when name+email present."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )

    # Apply non-None fields
    fields = update_data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(candidate, field, value)

    # Auto-promote: if name and email are both present and status was pending_review
    if candidate.status == "pending_review" and candidate.name and candidate.email:
        candidate.status = "complete"

    db.commit()
    db.refresh(candidate)
    return CandidateResponse.model_validate(candidate)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> None:
    """Delete candidate, remove physical resume file, and log audit event (AUD-03).

    Audit log retains only candidate_id and 'Deleted Candidate' label (D-10).
    No PII is stored in the audit record after deletion.
    """
    from app.core.audit import log_audit_action

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )

    # Remove physical file synchronously
    if candidate.resume_path and os.path.exists(candidate.resume_path):
        os.remove(candidate.resume_path)

    # Log deletion with minimal PII metadata (D-09, D-10)
    log_audit_action(
        db=db,
        user=current_user,
        action="candidate.deleted",
        resource_type="candidate",
        resource_id=candidate_id,
        metadata={"candidate_id": candidate_id, "label": "Deleted Candidate"},
    )

    # Delete related records (notes, applications) via CASCADE, then candidate
    db.delete(candidate)
    db.commit()


@router.get("/{candidate_id}/resume")
def download_resume(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> FileResponse:
    """Download resume file for authenticated users (D-03).

    Returns 403 if anonymous screening is enabled and user is a recruiter.
    Never exposes the filesystem path in the response.
    """
    from app.api.v1.settings import is_anonymous_screening_enabled

    # Block recruiter downloads during anonymous screening (D-03)
    if is_anonymous_screening_enabled(db) and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resume downloads are disabled during anonymous screening mode",
        )

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )

    if not candidate.resume_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume file available for this candidate",
        )

    if not os.path.exists(candidate.resume_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on disk",
        )

    # Determine media type from extension
    ext = os.path.splitext(candidate.resume_path)[1].lower()
    media_type = (
        "application/pdf"
        if ext == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # Use original filename for download
    download_name = candidate.original_filename or f"resume{ext}"

    return FileResponse(
        path=candidate.resume_path,
        media_type=media_type,
        filename=download_name,
    )


@router.post("/{candidate_id}/screen/{job_id}", response_model=ScreeningTriggerResponse)
def screen_candidate(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> ScreeningTriggerResponse:
    """Trigger screening for a candidate against a specific job.

    Computes all dimension scores (skills, experience, education, projects,
    certifications, semantic similarity) and stores the explainable breakdown.
    Idempotent — re-running updates the existing screening result.
    """
    screening_result = _run_screening(candidate_id, job_id, db)
    return ScreeningTriggerResponse(
        message="Screening completed",
        candidate_id=candidate_id,
        job_id=job_id,
        result=ScreeningResultResponse.model_validate(screening_result),
    )


@router.get("/{candidate_id}/screening/{job_id}", response_model=ScreeningResultResponse)
def get_screening_result(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> ScreeningResultResponse:
    """Retrieve the latest screening result for a candidate-job pair."""
    application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate_id,
            Application.job_id == job_id,
        )
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No application found for this candidate-job pair",
        )

    result = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.application_id == application.id)
        .first()
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No screening result found — trigger screening first",
        )

    return ScreeningResultResponse.model_validate(result)


# ---------------------------------------------------------------------------
# PDF & CSV Report Exports (ANA-03, D-13, D-14, D-15, D-16)
# ---------------------------------------------------------------------------


@router.get("/{candidate_id}/export/pdf")
def export_candidate_pdf(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
):
    """Generate and stream a candidate profile PDF (D-14, D-16).

    Ephemeral: generated in-memory, never written to disk.
    Redacts PII if anonymous screening is enabled (D-15).
    """
    from fastapi.responses import StreamingResponse

    from app.api.v1.settings import is_anonymous_screening_enabled
    from app.core.pdf_generator import generate_candidate_pdf

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate with id {candidate_id} not found")

    anonymous = is_anonymous_screening_enabled(db) and current_user.role != "admin"

    candidate_data = {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "skills": candidate.skills,
        "experience": candidate.experience,
        "education": candidate.education,
        "status": candidate.status,
    }

    buffer = generate_candidate_pdf(candidate_data, anonymous=anonymous)

    filename = f"candidate_{candidate_id}_profile.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/csv")
def export_candidates_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
):
    """Generate and stream a CSV of all candidates (D-14, D-16).

    Ephemeral: generated in-memory, never written to disk.
    Redacts PII if anonymous screening is enabled (D-15).
    """
    from fastapi.responses import StreamingResponse

    from app.api.v1.settings import is_anonymous_screening_enabled
    from app.core.pdf_generator import generate_candidates_csv

    anonymous = is_anonymous_screening_enabled(db) and current_user.role != "admin"

    candidates = db.query(Candidate).all()
    candidates_data = [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "location": c.location,
            "skills": c.skills or [],
            "status": c.status,
            "created_at": str(c.created_at) if c.created_at else "",
        }
        for c in candidates
    ]

    buffer = generate_candidates_csv(candidates_data, anonymous=anonymous)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="candidates_export.csv"'},
    )


# ---------------------------------------------------------------------------
# Application Status Workflow (CAND-03)
# ---------------------------------------------------------------------------


class StatusTransitionRequest(BaseModel):
    """Request body for transitioning application status."""

    new_status: str


class ApplicationStatusResponse(BaseModel):
    """Response after a status transition."""

    id: int
    job_id: int
    candidate_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("/{candidate_id}/applications", response_model=list[ApplicationStatusResponse])
def list_candidate_applications(
    candidate_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> list[ApplicationStatusResponse]:
    """List all job applications for a candidate with their workflow status."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate with id {candidate_id} not found")

    applications = db.query(Application).filter(Application.candidate_id == candidate_id).all()
    return [ApplicationStatusResponse.model_validate(a) for a in applications]


@router.patch("/{candidate_id}/applications/{application_id}/status", response_model=ApplicationStatusResponse)
def transition_application_status(
    candidate_id: int,
    application_id: int,
    body: StatusTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> ApplicationStatusResponse:
    """Transition an application's workflow status (CAND-03).

    Validates transitions against the state machine:
    Applied → Screening → Shortlisted → Interview → Selected/Rejected
    """
    from app.core.audit import log_audit_action
    from app.models.application import STATUS_TRANSITIONS, VALID_STATUSES

    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.candidate_id == candidate_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    new_status = body.new_status.lower()
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    current_status = application.status or "applied"
    allowed_transitions = STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_transitions:
        raise HTTPException(
            status_code=422,
            detail=f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed: {', '.join(sorted(allowed_transitions)) or 'none (terminal state)'}",
        )

    old_status = application.status
    application.status = new_status

    log_audit_action(
        db=db,
        user=current_user,
        action="application.status_changed",
        resource_type="application",
        resource_id=application.id,
        metadata={"candidate_id": candidate_id, "from": old_status, "to": new_status},
    )

    db.commit()
    db.refresh(application)
    return ApplicationStatusResponse.model_validate(application)


# ---------------------------------------------------------------------------
# Candidate Comparison (CAND-04)
# ---------------------------------------------------------------------------


@router.post("/compare")
def compare_candidates(
    candidate_ids: list[int] = Query(..., alias="ids", description="2-4 candidate IDs to compare"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> dict:
    """Compare 2-4 candidates side by side (CAND-04).

    Returns structured comparison data for the frontend grid.
    Applies anonymous redaction if enabled.
    """
    from app.api.v1.settings import is_anonymous_screening_enabled

    if len(candidate_ids) < 2 or len(candidate_ids) > 4:
        raise HTTPException(status_code=422, detail="Provide between 2 and 4 candidate IDs")

    candidates = db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    if len(candidates) != len(candidate_ids):
        raise HTTPException(status_code=404, detail="One or more candidates not found")

    anonymous = is_anonymous_screening_enabled(db) and current_user.role != "admin"

    comparison = []
    for c in candidates:
        comparison.append({
            "id": c.id,
            "name": f"Candidate #{c.id}" if anonymous else c.name,
            "email": None if anonymous else c.email,
            "location": c.location,
            "skills": c.skills or [],
            "experience_count": len(c.experience) if c.experience else 0,
            "education_count": len(c.education) if c.education else 0,
            "certifications_count": len(c.certifications) if c.certifications else 0,
            "status": c.status,
        })

    return {"candidates": comparison}


# ---------------------------------------------------------------------------
# Candidate Notes Endpoints (CAND-05)
# ---------------------------------------------------------------------------


class NoteCreate(BaseModel):
    """Request body for creating a note."""

    content: str = Field(..., min_length=1, max_length=5000)


class NoteResponse(BaseModel):
    """Response schema for a candidate note."""

    id: int
    candidate_id: int
    user_id: int
    user_email: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """List of notes for a candidate."""

    items: list[NoteResponse]
    total: int


@router.get("/{candidate_id}/notes", response_model=NoteListResponse)
def list_candidate_notes(
    candidate_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> NoteListResponse:
    """List all private recruiter notes for a candidate."""
    from app.models.candidate_note import CandidateNote

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )

    notes = (
        db.query(CandidateNote)
        .filter(CandidateNote.candidate_id == candidate_id)
        .order_by(CandidateNote.created_at.desc())
        .all()
    )
    return NoteListResponse(
        items=[NoteResponse.model_validate(n) for n in notes],
        total=len(notes),
    )


@router.post("/{candidate_id}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_candidate_note(
    candidate_id: int,
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> NoteResponse:
    """Add a private recruiter note to a candidate (D-09)."""
    from app.core.audit import log_audit_action
    from app.models.candidate_note import CandidateNote

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with id {candidate_id} not found",
        )

    note = CandidateNote(
        candidate_id=candidate_id,
        user_id=current_user.id,
        user_email=current_user.email,
        content=note_data.content,
    )
    db.add(note)

    log_audit_action(
        db=db,
        user=current_user,
        action="candidate.note_created",
        resource_type="candidate",
        resource_id=candidate_id,
        metadata={"note_id": None},  # Will be set after flush
    )

    db.commit()
    db.refresh(note)
    return NoteResponse.model_validate(note)
