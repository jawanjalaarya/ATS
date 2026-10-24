import json
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def _coerce_json_list(v: Any) -> list:
    """Coerce a value to a list - handles None, JSON strings, double-encoded strings."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        # Strip surrounding single quotes (SQLite artifact)
        cleaned = v.strip("'")
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, str):
                # Double-encoded
                inner = json.loads(parsed)
                if isinstance(inner, list):
                    return inner
        except (json.JSONDecodeError, TypeError):
            pass
        return []
    return []


class JobBase(BaseModel):
    """Base job schema with common fields."""
    
    title: str = Field(..., max_length=100)
    department: str
    description: str
    location: str
    work_mode: Literal["remote", "hybrid", "on-site"]
    employment_type: Literal["full-time", "part-time", "contract", "internship"]
    min_experience: int = Field(..., ge=0)
    max_experience: int = Field(..., ge=0)
    education_requirement: Literal["high_school", "associate", "bachelor", "master", "phd", "none"] = "none"
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    status: Literal["draft", "active", "paused", "closed"] = "draft"
    
    # Individual weight columns per D-02
    weight_skills: int = Field(20, ge=0, le=100)
    weight_experience: int = Field(20, ge=0, le=100)
    weight_education: int = Field(20, ge=0, le=100)
    weight_projects: int = Field(20, ge=0, le=100)
    weight_certs: int = Field(20, ge=0, le=100)
    
    # JSON skill/cert columns per D-07
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    required_certs: List[str] = Field(default_factory=list)
    preferred_certs: List[str] = Field(default_factory=list)

    @field_validator("required_skills", "preferred_skills", "required_certs", "preferred_certs", mode="before")
    @classmethod
    def coerce_json_list(cls, v: Any) -> list:
        return _coerce_json_list(v)

    @model_validator(mode='after')
    def validate_weight_sum(self) -> 'JobBase':
        """Validate that active jobs have weights totaling exactly 100% per D-03."""
        if self.status == "active":
            total = (
                self.weight_skills +
                self.weight_experience +
                self.weight_education +
                self.weight_projects +
                self.weight_certs
            )
            if total != 100:
                raise ValueError("Active jobs must have weights totaling exactly 100%")
        return self

    @model_validator(mode='after')
    def validate_experience_range(self) -> 'JobBase':
        """Validate that min_experience <= max_experience."""
        if self.min_experience > self.max_experience:
            raise ValueError("min_experience must be less than or equal to max_experience")
        return self

    @model_validator(mode='after')
    def validate_salary_range(self) -> 'JobBase':
        """Validate that salary_min <= salary_max when both provided."""
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min must be less than or equal to salary_max")
        return self


class JobCreate(JobBase):
    """Schema for creating a new job with complete validation."""
    pass


class JobUpdate(BaseModel):
    """Schema for partially updating a job (PATCH operations)."""
    
    title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[Literal["remote", "hybrid", "on-site"]] = None
    employment_type: Optional[Literal["full-time", "part-time", "contract", "internship"]] = None
    min_experience: Optional[int] = Field(None, ge=0)
    max_experience: Optional[int] = Field(None, ge=0)
    education_requirement: Optional[Literal["high_school", "associate", "bachelor", "master", "phd", "none"]] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    status: Optional[Literal["draft", "active", "paused", "closed"]] = None
    
    # Individual weight columns
    weight_skills: Optional[int] = Field(None, ge=0, le=100)
    weight_experience: Optional[int] = Field(None, ge=0, le=100)
    weight_education: Optional[int] = Field(None, ge=0, le=100)
    weight_projects: Optional[int] = Field(None, ge=0, le=100)
    weight_certs: Optional[int] = Field(None, ge=0, le=100)
    
    # JSON skill/cert columns
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    required_certs: Optional[List[str]] = None
    preferred_certs: Optional[List[str]] = None


class JobResponse(JobBase):
    """Full job response schema including database-generated fields."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    
    # Computed field from Application count
    applicant_count: int

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Consistent list response contract."""
    
    items: List[JobResponse]
    total: int