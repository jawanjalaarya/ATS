from typing import Optional

from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    """Request schema for login endpoint."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Response schema for token operations."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Internal schema for decoded JWT payload data."""

    email: Optional[str] = None
