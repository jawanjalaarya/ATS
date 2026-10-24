"""Interviews API router — CRUD for interview scheduling (INT-01).

Supports creating, viewing, rescheduling, and cancelling interviews.
All actions are audit-logged.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.audit import log_audit_action
from app.core.database import get_db
from app.models.interview import Interview
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate,
    InterviewListResponse,
    InterviewResponse,
    InterviewUpdate,
)

router = APIRouter()

VALID_INTERVIEW_STATUSES = {"scheduled", "completed", "cancelled"}


@router.get("/", response_model=InterviewListResponse)
def list_interviews(
    candidate_id: int | None = Query(None, description="Filter by candidate"),
    job_id: int | None = Query(None, description="Filter by job"),
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> InterviewListResponse:
    """List interviews with optional filters."""
    query = db.query(Interview)

    if candidate_id is not None:
        query = query.filter(Interview.candidate_id == candidate_id)
    if job_id is not None:
        query = query.filter(Interview.job_id == job_id)
    if status_filter:
        query = query.filter(Interview.status == status_filter)

    query = query.order_by(Interview.scheduled_at.desc())
    total = query.count()
    interviews = query.offset(skip).limit(limit).all()

    return InterviewListResponse(
        items=[InterviewResponse.model_validate(i) for i in interviews],
        total=total,
    )


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("recruiter")),
) -> InterviewResponse:
    """Get a single interview by ID."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return InterviewResponse.model_validate(interview)


@router.post("/", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview(
    body: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> InterviewResponse:
    """Schedule a new interview (INT-01). Audit-logged."""
    interview = Interview(
        application_id=body.application_id,
        candidate_id=body.candidate_id,
        job_id=body.job_id,
        interviewer_name=body.interviewer_name,
        interviewer_email=body.interviewer_email,
        scheduled_at=body.scheduled_at,
        duration_minutes=body.duration_minutes,
        location=body.location,
        notes=body.notes,
        questions=body.questions,
        status="scheduled",
    )
    db.add(interview)

    log_audit_action(
        db=db,
        user=current_user,
        action="interview.scheduled",
        resource_type="interview",
        metadata={
            "candidate_id": body.candidate_id,
            "job_id": body.job_id,
            "interviewer": body.interviewer_name,
        },
    )

    db.commit()
    db.refresh(interview)
    return InterviewResponse.model_validate(interview)


@router.patch("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: int,
    body: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> InterviewResponse:
    """Update/reschedule an interview. Validates status transitions."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status == "cancelled":
        raise HTTPException(status_code=422, detail="Cannot modify a cancelled interview")

    fields = body.model_dump(exclude_unset=True)

    # Validate status if being changed
    if "status" in fields:
        new_status = fields["status"]
        if new_status not in VALID_INTERVIEW_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_INTERVIEW_STATUSES))}",
            )

    for field, value in fields.items():
        setattr(interview, field, value)

    action = "interview.rescheduled" if "scheduled_at" in fields else "interview.updated"
    if "status" in fields and fields["status"] == "cancelled":
        action = "interview.cancelled"

    log_audit_action(
        db=db,
        user=current_user,
        action=action,
        resource_type="interview",
        resource_id=interview.id,
        metadata={"changes": list(fields.keys())},
    )

    db.commit()
    db.refresh(interview)
    return InterviewResponse.model_validate(interview)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> None:
    """Cancel an interview (sets status to cancelled)."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    interview.status = "cancelled"

    log_audit_action(
        db=db,
        user=current_user,
        action="interview.cancelled",
        resource_type="interview",
        resource_id=interview.id,
        metadata={"candidate_id": interview.candidate_id},
    )

    db.commit()


# ---------------------------------------------------------------------------
# Deterministic Question Generation (INT-02, D-05, D-06, D-07, D-08)
# ---------------------------------------------------------------------------

import hashlib
import json
import os
import random


def _load_templates() -> dict:
    """Load interview question templates from local JSON config (D-06)."""
    templates_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "core", "interview_templates.json")
    # Resolve relative to this file's actual location
    templates_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core", "interview_templates.json")
    with open(templates_path, "r") as f:
        return json.load(f)


def _generate_questions(
    candidate_skills: list[str],
    job_title: str,
    candidate_id: int,
    job_id: int,
) -> list[str]:
    """Generate exactly 5 deterministic interview questions (D-05, D-08).

    Uses keyword matching against candidate skills and job title.
    Deterministic: same inputs always produce same output (seeded RNG).
    Distribution: 2 technical, 1 behavioral, 1 project, 1 role-specific.
    """
    templates = _load_templates()
    categories = templates["categories"]
    distribution = templates["generation_rules"]["distribution"]

    # Create deterministic seed from candidate+job pair
    seed_str = f"{candidate_id}:{job_id}:{','.join(sorted(candidate_skills))}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    # Normalize skills and title for matching
    match_terms = [s.lower() for s in candidate_skills] + [job_title.lower()]

    questions: list[str] = []

    for category_key, count in distribution.items():
        category = categories.get(category_key, {})
        pool = category.get("questions", [])

        # Score questions by keyword relevance
        scored = []
        for q in pool:
            keywords = [k.lower() for k in q.get("keywords", [])]
            if not keywords:
                score = 0.5  # Neutral — can be selected if no better match
            else:
                matches = sum(1 for term in match_terms for kw in keywords if kw in term)
                score = matches
            scored.append((score, q["text"]))

        # Sort by score descending, break ties deterministically
        scored.sort(key=lambda x: (-x[0], x[1]))

        # Pick top-N, with randomized selection among tied scores
        if len(scored) > count:
            # Group by top score
            top_score = scored[0][0]
            top_group = [s for s in scored if s[0] == top_score]
            if len(top_group) >= count:
                selected = rng.sample(top_group, count)
            else:
                selected = top_group + scored[len(top_group):count]
        else:
            selected = scored[:count]

        questions.extend([text for _, text in selected])

    return questions[:5]  # Enforce exactly 5


@router.post("/{interview_id}/generate-questions", response_model=InterviewResponse)
def generate_interview_questions(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter")),
) -> InterviewResponse:
    """Generate deterministic interview questions for an interview (INT-02).

    Uses local template matching based on candidate skills and job title.
    Questions are saved to the interview record but can be edited before saving.
    """
    from app.models.candidate import Candidate
    from app.models.job import Job

    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
    job = db.query(Job).filter(Job.id == interview.job_id).first()

    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Associated candidate or job not found")

    questions = _generate_questions(
        candidate_skills=candidate.skills or [],
        job_title=job.title or "",
        candidate_id=candidate.id,
        job_id=job.id,
    )

    interview.questions = questions

    log_audit_action(
        db=db,
        user=current_user,
        action="interview.questions_generated",
        resource_type="interview",
        resource_id=interview.id,
        metadata={"question_count": len(questions), "candidate_id": candidate.id},
    )

    db.commit()
    db.refresh(interview)
    return InterviewResponse.model_validate(interview)
