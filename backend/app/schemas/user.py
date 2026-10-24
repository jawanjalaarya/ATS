from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base schema with common user fields."""

    email: EmailStr
    role: Literal["admin", "recruiter"]
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user (includes plaintext password)."""

    password: str


class UserUpdate(BaseModel):
    """Schema for partially updating a user (all fields optional)."""

    email: Optional[EmailStr] = None
    role: Optional[Literal["admin", "recruiter"]] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Full user response schema including database-generated fields."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
