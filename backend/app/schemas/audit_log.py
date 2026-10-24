"""Pydantic schemas for audit log entries."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Read-only audit log entry response."""

    id: int
    user_id: int
    user_email: str
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit log entries."""

    items: List[AuditLogResponse]
    total: int
