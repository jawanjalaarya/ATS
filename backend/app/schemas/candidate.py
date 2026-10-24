import json
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


def _coerce_list(v: Any) -> list:
    """Coerce a value to a list — handles None, JSON strings, and actual lists."""
    if v is None:
        return []
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return []
    if isinstance(v, list):
        return v
    return []


class CandidateBase(BaseModel):
    """Base candidate schema with all parsed profile fields."""

    name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)
    experience: List[dict] = Field(default_factory=list)
    projects: List[dict] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)

    # Validators to handle SQLite JSON-as-string and NULL values
    @field_validator("skills", "certifications", "achievements", mode="before")
    @classmethod
    def coerce_string_list(cls, v: Any) -> list:
        return _coerce_list(v)

    @field_validator("education", "experience", "projects", mode="before")
    @classmethod
    def coerce_dict_list(cls, v: Any) -> list:
        return _coerce_list(v)


class CandidateCreate(CandidateBase):
    """Schema for creating a candidate (used internally by parser)."""

    pass


class CandidateUpdate(BaseModel):
    """Schema for partially updating a candidate (review/edit form per D-10)."""

    name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[List[dict]] = None
    experience: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    certifications: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    status: Optional[str] = None


class CandidateResponse(CandidateBase):
    """Full candidate response including database-generated fields."""

    id: int
    resume_path: Optional[str] = None
    original_filename: Optional[str] = None
    status: str = "complete"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CandidateListResponse(BaseModel):
    """Consistent list response contract."""

    items: List[CandidateResponse]
    total: int
