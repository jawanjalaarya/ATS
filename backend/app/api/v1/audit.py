"""Audit Log API router — admin-only read access to system audit trail.

No update or delete endpoints are exposed (D-12 — immutable logs).
Only admin users can access these endpoints (D-11).
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action_filter: Optional[str] = Query(None, alias="action"),
    resource_type_filter: Optional[str] = Query(None, alias="resource_type"),
    user_id_filter: Optional[int] = Query(None, alias="user_id"),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> AuditLogListResponse:
    """List audit log entries in reverse chronological order. Admin only (D-11).

    Supports filtering by action type, resource type, and user ID.
    No update or delete operations are available (D-12).
    """
    query = db.query(AuditLog)

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if resource_type_filter:
        query = query.filter(AuditLog.resource_type == resource_type_filter)
    if user_id_filter is not None:
        query = query.filter(AuditLog.user_id == user_id_filter)

    query = query.order_by(AuditLog.created_at.desc())
    total = query.count()
    logs = query.offset(skip).limit(limit).all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
    )
