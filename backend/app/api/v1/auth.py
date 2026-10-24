from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, verify_token
from app.models.user import User
from app.schemas.auth import UserLogin
from app.schemas.user import User as UserSchema

router = APIRouter()

_COOKIE_NAME = "access_token"
_COOKIE_MAX_AGE = 1800  # 30 minutes in seconds
# Sliding session: renew token if it expires within this many minutes
_SLIDING_RENEWAL_THRESHOLD_MINUTES = 15


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set the HTTP-only JWT cookie on the response."""
    response.set_cookie(
        key=_COOKIE_NAME,
        value=f"Bearer {token}",
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear the HTTP-only JWT cookie from the response."""
    response.delete_cookie(
        key=_COOKIE_NAME,
        httponly=True,
        samesite="lax",
    )


@router.post("/login")
async def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    """
    Authenticate a user and set an HTTP-only JWT cookie.

    Returns:
        Success message with user role.

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
        )

    access_token = create_access_token(data={"sub": user.email})
    _set_auth_cookie(response, access_token)

    return {"message": "Login successful", "role": user.role}


@router.get("/me", response_model=UserSchema)
async def get_me(
    response: Response,
    current_user: User = Depends(get_current_user),
    access_token: Annotated[Optional[str], Cookie()] = None,
) -> User:
    """
    Return the current authenticated user's profile.

    Implements sliding session renewal: if the token expires within
    SLIDING_RENEWAL_THRESHOLD_MINUTES, a fresh 30-minute token is issued.
    The original token content is never re-exposed.
    """
    # Sliding session renewal: issue new token if expiring soon
    if access_token and access_token.startswith("Bearer "):
        raw_token = access_token[len("Bearer "):]
        try:
            payload = verify_token(raw_token)
            exp = payload.get("exp")
            if exp:
                expiry_time = datetime.fromtimestamp(exp, tz=timezone.utc)
                remaining = expiry_time - datetime.now(timezone.utc)
                if remaining <= timedelta(minutes=_SLIDING_RENEWAL_THRESHOLD_MINUTES):
                    new_token = create_access_token(data={"sub": current_user.email})
                    _set_auth_cookie(response, new_token)
        except Exception:
            pass  # Token already validated by get_current_user, don't fail here

    return current_user


@router.post("/logout")
async def logout(response: Response) -> dict:
    """
    Invalidate the session by clearing the HTTP-only JWT cookie.

    Stateless logout per D-04 — no server-side token revocation.
    """
    _clear_auth_cookie(response)
    return {"message": "Logged out successfully"}
