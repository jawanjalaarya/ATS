from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate, JobListResponse, JobResponse, JobUpdate

router = APIRouter()


def _extract_validation_error_message(error: ValidationError) -> str:
    """Extract a user-friendly message from a Pydantic ValidationError."""
    errors = error.errors()
    if errors:
        # Get the first error's message or context message
        first_error = errors[0]
        if "ctx" in first_error and "error" in first_error["ctx"]:
            return str(first_error["ctx"]["error"])
        return first_error.get("msg", str(error))
    return str(error)


def _calculate_applicant_count(db: Session, job_id: int) -> int:
    """Calculate real applicant count using Application model COUNT() queries."""
    return db.query(func.count(Application.id)).filter(Application.job_id == job_id).scalar() or 0


def _job_to_response(db: Session, job: Job) -> JobResponse:
    """Convert Job model to JobResponse with real applicant_count.
    
    Handles missing timestamps by using current time as default.
    """
    now = datetime.utcnow()
    job_dict = {
        "id": job.id,
        "title": job.title,
        "department": job.department,
        "description": job.description,
        "location": job.location,
        "work_mode": job.work_mode,
        "employment_type": job.employment_type,
        "min_experience": job.min_experience,
        "max_experience": job.max_experience,
        "education_requirement": job.education_requirement,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "status": job.status,
        "weight_skills": job.weight_skills,
        "weight_experience": job.weight_experience,
        "weight_education": job.weight_education,
        "weight_projects": job.weight_projects,
        "weight_certs": job.weight_certs,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "required_certs": job.required_certs,
        "preferred_certs": job.preferred_certs,
        "created_at": job.created_at or now,  # Use current time if None
        "updated_at": job.updated_at or now,  # Use current time if None
        "archived_at": job.archived_at,
        "applicant_count": _calculate_applicant_count(db, job.id)
    }
    return JobResponse(**job_dict)


@router.get("/", response_model=JobListResponse)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by job status"),
    include_archived: bool = Query(False, description="Include archived jobs"),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> JobListResponse:
    """List jobs with JobListResponse format. Default excludes archived per D-05."""
    query = db.query(Job)
    
    # Apply status filter
    if status:
        query = query.filter(Job.status == status)
    
    # Apply archive filter per D-05 policy
    if not include_archived:
        query = query.filter(Job.archived_at.is_(None))
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    jobs = query.offset(skip).limit(limit).all()
    
    # Convert to JobResponse with real applicant counts
    job_responses = [_job_to_response(db, job) for job in jobs]
    
    return JobListResponse(items=job_responses, total=total)


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> JobResponse:
    """Create job with JobCreate validation per D-04 (any recruiter/admin)."""
    try:
        # Validate by re-creating the JobCreate instance
        # This ensures all validators run properly
        validated_data = JobCreate(
            title=job_data.title,
            department=job_data.department,
            description=job_data.description,
            location=job_data.location,
            work_mode=job_data.work_mode,
            employment_type=job_data.employment_type,
            min_experience=job_data.min_experience,
            max_experience=job_data.max_experience,
            education_requirement=job_data.education_requirement,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            status=job_data.status,
            weight_skills=job_data.weight_skills,
            weight_experience=job_data.weight_experience,
            weight_education=job_data.weight_education,
            weight_projects=job_data.weight_projects,
            weight_certs=job_data.weight_certs,
            required_skills=job_data.required_skills,
            preferred_skills=job_data.preferred_skills,
            required_certs=job_data.required_certs,
            preferred_certs=job_data.preferred_certs,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_extract_validation_error_message(e),
        )
    
    now = datetime.utcnow()
    new_job = Job(
        title=validated_data.title,
        department=validated_data.department,
        description=validated_data.description,
        location=validated_data.location,
        work_mode=validated_data.work_mode,
        employment_type=validated_data.employment_type,
        min_experience=validated_data.min_experience,
        max_experience=validated_data.max_experience,
        education_requirement=validated_data.education_requirement,
        salary_min=validated_data.salary_min,
        salary_max=validated_data.salary_max,
        status=validated_data.status,
        weight_skills=validated_data.weight_skills,
        weight_experience=validated_data.weight_experience,
        weight_education=validated_data.weight_education,
        weight_projects=validated_data.weight_projects,
        weight_certs=validated_data.weight_certs,
        required_skills=validated_data.required_skills,
        preferred_skills=validated_data.preferred_skills,
        required_certs=validated_data.required_certs,
        preferred_certs=validated_data.preferred_certs,
        created_at=now,
        updated_at=now,
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return _job_to_response(db, new_job)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> JobResponse:
    """Get single job with real applicant_count calculation."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    return _job_to_response(db, job)


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> JobResponse:
    """Update job per D-04 (any recruiter/admin can edit any job). Merges patch into existing job before validation."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    # Merge patch values into existing job
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    # Validate merged full state by creating a JobCreate from the merged job
    # This enforces active job weight validation on the merged result
    merged_data = {
        "title": job.title,
        "department": job.department,
        "description": job.description,
        "location": job.location,
        "work_mode": job.work_mode,
        "employment_type": job.employment_type,
        "min_experience": job.min_experience,
        "max_experience": job.max_experience,
        "education_requirement": job.education_requirement,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "status": job.status,
        "weight_skills": job.weight_skills,
        "weight_experience": job.weight_experience,
        "weight_education": job.weight_education,
        "weight_projects": job.weight_projects,
        "weight_certs": job.weight_certs,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "required_certs": job.required_certs,
        "preferred_certs": job.preferred_certs,
    }
    
    try:
        # This will raise ValidationError if weights don't sum to 100% for active jobs
        JobCreate(**merged_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_extract_validation_error_message(e),
        )
    
    # Explicitly set updated_at timestamp
    job.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    
    return _job_to_response(db, job)


@router.patch("/{job_id}/close", response_model=JobResponse)
def close_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> JobResponse:
    """Set status to 'closed' per D-04."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    job.status = "closed"
    db.commit()
    db.refresh(job)
    
    return _job_to_response(db, job)


@router.patch("/{job_id}/archive", response_model=JobResponse)
def archive_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> JobResponse:
    """Set archived_at timestamp per D-05 (soft delete only)."""
    from datetime import datetime
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    job.archived_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    return _job_to_response(db, job)


@router.patch("/{job_id}/restore", response_model=JobResponse)
def restore_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> JobResponse:
    """Clear archived_at timestamp per D-05."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    
    job.archived_at = None
    db.commit()
    db.refresh(job)
    
    return _job_to_response(db, job)


# ---------------------------------------------------------------------------
# Dashboard Analytics Aggregates (ANA-01, ANA-02)
# ---------------------------------------------------------------------------


@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> dict:
    """Get aggregated statistics for the analytics dashboard.

    Returns counts and breakdowns for jobs, candidates, applications, and interviews.
    """
    from app.models.candidate import Candidate
    from app.models.interview import Interview

    # Job stats
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    active_jobs = db.query(func.count(Job.id)).filter(Job.status == "active").scalar() or 0

    # Candidate stats
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0

    # Application stats
    total_applications = db.query(func.count(Application.id)).scalar() or 0

    # Application status breakdown
    status_counts = (
        db.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )
    applications_by_status = {status: count for status, count in status_counts}

    # Interview stats
    total_interviews = db.query(func.count(Interview.id)).scalar() or 0
    scheduled_interviews = (
        db.query(func.count(Interview.id))
        .filter(Interview.status == "scheduled")
        .scalar() or 0
    )

    # Jobs by department
    dept_counts = (
        db.query(Job.department, func.count(Job.id))
        .group_by(Job.department)
        .all()
    )
    jobs_by_department = [{"name": dept or "Unassigned", "count": count} for dept, count in dept_counts]

    return {
        "summary": {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "total_candidates": total_candidates,
            "total_applications": total_applications,
            "total_interviews": total_interviews,
            "scheduled_interviews": scheduled_interviews,
        },
        "applications_by_status": applications_by_status,
        "jobs_by_department": jobs_by_department,
    }
