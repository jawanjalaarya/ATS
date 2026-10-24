from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class DimensionBreakdown(BaseModel):
    """Generic schema for a single dimension's match breakdown."""

    required_matched: Optional[list[str]] = None
    required_missing: Optional[list[str]] = None
    preferred_matched: Optional[list[str]] = None
    preferred_missing: Optional[list[str]] = None
    candidate_years: Optional[float] = None
    required_min: Optional[int] = None
    required_max: Optional[int] = None
    meets_minimum: Optional[bool] = None
    candidate_level: Optional[str] = None
    required_level: Optional[str] = None
    meets_requirement: Optional[bool] = None
    matched_keywords: Optional[list[str]] = None
    missing_keywords: Optional[list[str]] = None
    total_keywords: Optional[int] = None
    raw_cosine: Optional[float] = None
    scaled_score: Optional[float] = None
    omitted: Optional[bool] = None
    reason: Optional[str] = None


class ScreeningBreakdown(BaseModel):
    """Full structured breakdown stored in the explanation JSON column."""

    skills: Optional[dict[str, Any]] = None
    experience: Optional[dict[str, Any]] = None
    education: Optional[dict[str, Any]] = None
    projects: Optional[dict[str, Any]] = None
    certifications: Optional[dict[str, Any]] = None
    semantic: Optional[dict[str, Any]] = None


class ScreeningResultResponse(BaseModel):
    """API response schema for a screening result."""

    id: int
    application_id: int
    overall_score: Optional[float] = None
    skills_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    projects_score: Optional[float] = None
    certification_score: Optional[float] = None
    semantic_score: Optional[float] = None
    explanation: Optional[ScreeningBreakdown] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ScreeningTriggerResponse(BaseModel):
    """Response returned when screening is triggered."""

    message: str
    candidate_id: int
    job_id: int
    result: ScreeningResultResponse
