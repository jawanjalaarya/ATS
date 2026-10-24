"""System settings model — stores global configuration flags.

Key-value configuration stored in the database. The anonymous_screening
flag controls PII redaction across candidate endpoints (D-01).
"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class SystemSetting(Base):
    """Key-value configuration pair stored in the database."""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(String, nullable=False, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
