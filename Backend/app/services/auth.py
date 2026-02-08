"""Authentication service supporting both API key and JWT authentication."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db

if TYPE_CHECKING:
    from ..models import User


def _write_key() -> str | None:
    return settings.app_write_api_key or settings.app_api_key


def _read_keys() -> list[str]:
    keys: list[str] = []
    if settings.app_read_api_key:
        keys.append(settings.app_read_api_key)
    if _write_key():
        keys.append(_write_key() or "")
    return [k for k in keys if k]


def _validate_api_key_read(api_key: str | None) -> bool:
    """Validate API key for read access."""
    if not settings.auth_enforce_read:
        return True
    valid = _read_keys()
    if not valid:
        return True
    return api_key in valid


def _validate_api_key_write(api_key: str | None) -> bool:
    """Validate API key for write access."""
    configured = _write_key()
    if not configured:
        return True
    return api_key == configured


def _validate_jwt_token(authorization: str | None, db: Session) -> "User | None":
    """Validate JWT token and return user if valid."""
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]

    # Import here to avoid circular imports
    from .jwt_service import ExpiredTokenError, InvalidTokenError, verify_access_token
    from .user_service import get_user_by_id

    try:
        user_id = verify_access_token(token)
        user = get_user_by_id(db, uuid.UUID(user_id))
        if user and user.is_active:
            return user
    except (ExpiredTokenError, InvalidTokenError):
        pass

    return None


def require_read_access(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> None:
    """Dependency for read access - accepts either API key or JWT.

    For backward compatibility:
    - If auth_mode is 'api_key', only API key auth is accepted
    - If auth_mode is 'jwt', JWT is preferred but API key fallback works
    - If no auth configured, access is allowed
    """
    # Try JWT first if auth_mode is 'jwt'
    if settings.auth_mode == "jwt":
        user = _validate_jwt_token(authorization, db)
        if user:
            return  # JWT valid

    # Fall back to API key validation
    if _validate_api_key_read(x_api_key):
        return

    # If we get here and auth_mode is jwt, give JWT-specific error
    if settings.auth_mode == "jwt" and authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def require_write_access(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> None:
    """Dependency for write access - accepts either API key or JWT.

    For backward compatibility:
    - If auth_mode is 'api_key', only API key auth is accepted
    - If auth_mode is 'jwt', JWT is preferred but API key fallback works
    - If no auth configured, access is allowed
    """
    # Try JWT first if auth_mode is 'jwt'
    if settings.auth_mode == "jwt":
        user = _validate_jwt_token(authorization, db)
        if user:
            return  # JWT valid

    # Fall back to API key validation
    if _validate_api_key_write(x_api_key):
        return

    # If we get here and auth_mode is jwt, give JWT-specific error
    if settings.auth_mode == "jwt" and authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def get_authenticated_user(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> "User | None":
    """Get the authenticated user from JWT if available.

    Returns None if using API key auth (for backward compatibility).
    """
    if settings.auth_mode == "jwt":
        user = _validate_jwt_token(authorization, db)
        if user:
            return user
    return None


def get_actor_name(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> str:
    """Get actor name for audit logging.

    Returns username if JWT authenticated, 'api' if API key authenticated.
    """
    if settings.auth_mode == "jwt":
        user = _validate_jwt_token(authorization, db)
        if user:
            return user.username
    return "api"
