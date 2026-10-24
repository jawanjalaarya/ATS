"""Pydantic schemas for interview CRUD operations."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    """Request body for scheduling a new interview."""

    application_id: int
    candidate_id: int
    job_id: int
    interviewer_name: str = Field(..., min_length=1, max_length=200)
    interviewer_email: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=15, le=480)
    location: Optional[str] = None
    notes: Optional[str] = None
    questions: List[str] = Field(default_factory=list)


class InterviewUpdate(BaseModel):
    """Request body for updating/rescheduling an interview."""

    interviewer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    interviewer_email: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    questions: Optional[List[str]] = None


class InterviewResponse(BaseModel):
    """Full interview response."""

    id: int
    application_id: int
    candidate_id: int
    job_id: int
    interviewer_name: str
    interviewer_email: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int
    location: Optional[str] = None
    notes: Optional[str] = None
    status: str
    questions: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterviewListResponse(BaseModel):
    """Paginated list of interviews."""

    items: List[InterviewResponse]
    total: int
