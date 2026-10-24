"""AuditLog model — immutable, append-only audit trail.

Each entry records a single action taken by a user on the system.
No update or delete operations are exposed (D-12).
"""

from sqlalchemy import Column, DateTime, Integer, String, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """Immutable audit log entry.

    Fields:
        user_id: The user who performed the action.
        user_email: Denormalized email for display without joins.
        action: Machine-readable action type (e.g. 'candidate.view', 'candidate.delete').
        resource_type: The type of resource acted upon (e.g. 'candidate', 'job').
        resource_id: The ID of the resource, if applicable.
        metadata: Additional context as JSON (e.g. candidate name at time of action).
        created_at: Immutable timestamp of when the action occurred.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String, nullable=False)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)
    resource_id = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now(), index=True)
