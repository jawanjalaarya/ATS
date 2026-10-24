from typing import Annotated, Callable, Optional

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User


def get_current_user(
    access_token: Annotated[Optional[str], Cookie()] = None,
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts and validates the JWT from the HTTP-only cookie.

    Expects the cookie value to be in format: "Bearer <jwt_token>"

    Raises:
        HTTPException 401: If token is missing, malformed, user not found, or inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if access_token is None:
        raise credentials_exception

    # Extract JWT from "Bearer <token>" format
    if not access_token.startswith("Bearer "):
        raise credentials_exception

    token = access_token[len("Bearer "):]

    try:
        payload = verify_token(token)
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
        )

    return user


def require_role(required_role: str) -> Callable:
    """
    Dependency factory that returns a FastAPI dependency enforcing a minimum role.

    Role hierarchy: admin > recruiter
    - require_role("admin") → only admin users
    - require_role("recruiter") → admin OR recruiter users

    Args:
        required_role: The minimum required role ("admin" or "recruiter").

    Returns:
        A FastAPI dependency that validates the current user's role.
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        # Admin has superuser access — can access any route
        if current_user.role == "admin":
            return current_user

        # Recruiter can only access recruiter-level routes
        if current_user.role == required_role:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}",
        )

    return role_checker
