from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.core.database import Base


class Job(Base):
    """Job SQLAlchemy model with individual weight columns and JSON skills/certs.
    
    Per Context decisions:
    - Individual weight columns (D-02) with 20% defaults
    - JSON storage for skills/certs (D-06) 
    - Separate required/preferred columns (D-07)
    - CHECK constraints for enum validation (D-08, D-09, D-10)
    - Soft archive via archived_at timestamp (D-05)
    """

    __tablename__ = "jobs"

    # Primary key and basic fields
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)

    # Work and employment fields
    work_mode = Column(String, nullable=False)
    employment_type = Column(String, nullable=False)
    min_experience = Column(Integer, nullable=False)
    max_experience = Column(Integer, nullable=False)
    education_requirement = Column(String, nullable=False)

    # Salary fields (optional)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)

    # Individual weight columns per D-02 (default 20% each)
    weight_skills = Column(Integer, default=20, nullable=False)
    weight_experience = Column(Integer, default=20, nullable=False)
    weight_education = Column(Integer, default=20, nullable=False)
    weight_projects = Column(Integer, default=20, nullable=False)
    weight_certs = Column(Integer, default=20, nullable=False)

    # JSON skill/cert columns per D-07 (separate required/preferred)
    required_skills = Column(JSON, default=list, nullable=False)
    preferred_skills = Column(JSON, default=list, nullable=False)
    required_certs = Column(JSON, default=list, nullable=False)
    preferred_certs = Column(JSON, default=list, nullable=False)

    # Status and archive
    status = Column(String, default="draft", nullable=False)
    archived_at = Column(DateTime, nullable=True)  # Soft archive per D-05

    # Audit timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # CHECK constraints for enums per D-08, D-09, D-10
    __table_args__ = (
        CheckConstraint(
            "work_mode IN ('remote', 'hybrid', 'on-site')",
            name="ck_job_work_mode"
        ),
        CheckConstraint(
            "employment_type IN ('full-time', 'part-time', 'contract', 'internship')",
            name="ck_job_employment_type"
        ),
        CheckConstraint(
            "education_requirement IN ('high_school', 'associate', 'bachelor', 'master', 'phd', 'none')",
            name="ck_job_education_requirement"
        ),
        CheckConstraint(
            "status IN ('draft', 'active', 'paused', 'closed')",
            name="ck_job_status"
        ),
    )