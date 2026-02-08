"""JWT token service for authentication."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pydantic import BaseModel

from ..config import settings


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (user_id)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    type: str  # Token type: "access" or "refresh"
    jti: str | None = None  # JWT ID for refresh tokens


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token expiration in seconds


class InvalidTokenError(Exception):
    """Raised when a token is invalid."""

    pass


class ExpiredTokenError(Exception):
    """Raised when a token has expired."""

    pass


def create_access_token(
    user_id: str | uuid.UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: The user's unique identifier.
        expires_delta: Optional custom expiration time.

    Returns:
        The encoded JWT access token.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: str | uuid.UUID,
    expires_delta: timedelta | None = None,
) -> tuple[str, str, datetime]:
    """Create a JWT refresh token.

    Args:
        user_id: The user's unique identifier.
        expires_delta: Optional custom expiration time.

    Returns:
        Tuple of (encoded token, token ID for storage, expiration datetime).
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    jti = str(uuid.uuid4())

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "jti": jti,
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def create_token_pair(user_id: str | uuid.UUID) -> tuple[TokenPair, str, datetime]:
    """Create an access and refresh token pair.

    Args:
        user_id: The user's unique identifier.

    Returns:
        Tuple of (TokenPair, refresh token JTI for storage, refresh expiration).
    """
    access_token = create_access_token(user_id)
    refresh_token, jti, refresh_expires = create_refresh_token(user_id)

    expires_in = settings.jwt_access_token_expire_minutes * 60

    token_pair = TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )

    return token_pair, jti, refresh_expires


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode.

    Returns:
        The decoded token payload.

    Raises:
        InvalidTokenError: If the token is invalid.
        ExpiredTokenError: If the token has expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            type=payload.get("type", "access"),
            jti=payload.get("jti"),
        )
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {e}")


def verify_access_token(token: str) -> str:
    """Verify an access token and return the user ID.

    Args:
        token: The JWT access token.

    Returns:
        The user ID from the token.

    Raises:
        InvalidTokenError: If the token is invalid or not an access token.
        ExpiredTokenError: If the token has expired.
    """
    payload = decode_token(token)
    if payload.type != "access":
        raise InvalidTokenError("Token is not an access token")
    return payload.sub


def verify_refresh_token(token: str) -> tuple[str, str]:
    """Verify a refresh token and return user ID and token ID.

    Args:
        token: The JWT refresh token.

    Returns:
        Tuple of (user_id, jti) from the token.

    Raises:
        InvalidTokenError: If the token is invalid or not a refresh token.
        ExpiredTokenError: If the token has expired.
    """
    payload = decode_token(token)
    if payload.type != "refresh":
        raise InvalidTokenError("Token is not a refresh token")
    if not payload.jti:
        raise InvalidTokenError("Refresh token missing JTI")
    return payload.sub, payload.jti
