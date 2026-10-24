"""Interview model — tracks interview scheduling, status, and details.

Supports scheduling, rescheduling, and cancellation workflows (INT-01).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class Interview(Base):
    """Interview record linking a candidate application to a scheduled meeting."""

    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    interviewer_name = Column(String, nullable=False)
    interviewer_email = Column(String, nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    location = Column(String, nullable=True)  # Room name, video link, etc.
    notes = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="scheduled", index=True)
    # status: scheduled | completed | cancelled
    questions = Column(JSON, default=list)  # Generated interview questions
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
