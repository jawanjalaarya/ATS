"""Settings API router — admin-only global configuration management.

Exposes system settings (like anonymous_screening toggle) to admin users only (D-01).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.settings import SystemSetting
from app.models.user import User
from app.schemas.settings import SettingResponse, SettingsListResponse, SettingUpdate

router = APIRouter()


def get_setting(db: Session, key: str) -> str:
    """Get a setting value by key, returning empty string if not found."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    return setting.value if setting else ""


def is_anonymous_screening_enabled(db: Session) -> bool:
    """Check if anonymous screening is currently enabled."""
    return get_setting(db, "anonymous_screening") == "true"


@router.get("/", response_model=SettingsListResponse)
def list_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> SettingsListResponse:
    """List all system settings. Admin only."""
    settings = db.query(SystemSetting).all()
    return SettingsListResponse(
        items=[SettingResponse(key=s.key, value=s.value) for s in settings]
    )


@router.get("/{key}", response_model=SettingResponse)
def get_setting_endpoint(
    key: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> SettingResponse:
    """Get a single setting by key. Admin only."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{key}' not found")
    return SettingResponse(key=setting.key, value=setting.value)


@router.put("/{key}", response_model=SettingResponse)
def update_setting(
    key: str,
    body: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SettingResponse:
    """Create or update a system setting. Admin only (D-01)."""
    from app.core.audit import log_audit_action

    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    old_value = setting.value if setting else None

    if setting:
        setting.value = body.value
    else:
        setting = SystemSetting(key=key, value=body.value)
        db.add(setting)

    log_audit_action(
        db=db,
        user=current_user,
        action="setting.updated",
        resource_type="setting",
        metadata={"key": key, "old_value": old_value, "new_value": body.value},
    )

    db.commit()
    db.refresh(setting)
    return SettingResponse(key=setting.key, value=setting.value)
