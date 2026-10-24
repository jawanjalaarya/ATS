from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Candidate(Base):
    """Full Candidate model mapping all migration-defined columns plus resume fields.

    Maps to the candidates table from the initial schema migration.
    Adds resume_path and original_filename for file tracking (D-01, D-02).
    name and email are nullable to support pending_review status (D-10).
    """

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, unique=True, index=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
    skills = Column(JSON, default=list)
    education = Column(JSON, default=list)
    experience = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    achievements = Column(JSON, default=list)
    resume_path = Column(String, nullable=True)
    original_filename = Column(String, nullable=True)
    status = Column(String, default="complete")  # complete | pending_review
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
