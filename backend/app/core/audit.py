"""Explicit audit logging helper (D-09).

Called directly inside API endpoint handlers to record actions.
Writes directly to the audit_logs table — no middleware or decorators.
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_audit_action(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Record an audit action in the database.

    Args:
        db: Active database session.
        user: The authenticated user performing the action.
        action: Machine-readable action (e.g. 'candidate.create', 'candidate.delete').
        resource_type: Resource category ('candidate', 'job', 'interview', etc.).
        resource_id: Optional ID of the resource acted upon.
        metadata: Optional JSON-serializable context dict.
            For deletions: contains only candidate_id and 'Deleted Candidate' label (D-10).

    Returns:
        The created AuditLog instance.
    """
    entry = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_=metadata or {},
    )
    db.add(entry)
    db.flush()  # Ensure ID is assigned without full commit (caller controls transaction)
    return entry
