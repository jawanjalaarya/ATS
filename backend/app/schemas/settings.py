"""Pydantic schemas for system settings."""

from pydantic import BaseModel


class SettingResponse(BaseModel):
    """Response for a single setting."""

    key: str
    value: str

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    """Request body for updating a setting."""

    value: str


class SettingsListResponse(BaseModel):
    """Response for all settings."""

    items: list[SettingResponse]
