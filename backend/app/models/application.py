"""Application model — links candidates to jobs with workflow status tracking.

Implements the candidate workflow state machine:
Applied → Screening → Shortlisted → Interview → Selected | Rejected
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


# Valid application status transitions
VALID_STATUSES = {"applied", "screening", "shortlisted", "interview", "selected", "rejected"}
STATUS_TRANSITIONS = {
    "applied": {"screening", "rejected"},
    "screening": {"shortlisted", "rejected"},
    "shortlisted": {"interview", "rejected"},
    "interview": {"selected", "rejected"},
    "selected": set(),   # Terminal state
    "rejected": set(),   # Terminal state
}


class Application(Base):
    """Application model linking candidates to jobs with workflow state.

    Maps to existing applications table. Extended with status and timestamps
    for the candidate workflow state machine (CAND-03).
    """

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="applied", index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())