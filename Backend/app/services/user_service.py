"""User service for authentication and user management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import RefreshToken, User
from .password import hash_password, hash_token, verify_password

if TYPE_CHECKING:
    pass


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    pass


class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid."""

    pass


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user that already exists."""

    pass


class InactiveUserError(Exception):
    """Raised when trying to authenticate an inactive user."""

    pass


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """Get a user by their ID."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get a user by their email address."""
    stmt = select(User).where(User.email == email.lower())
    return db.scalars(stmt).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Get a user by their username."""
    stmt = select(User).where(User.username == username.lower())
    return db.scalars(stmt).first()


def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    full_name: str | None = None,
    is_superuser: bool = False,
) -> User:
    """Create a new user.

    Args:
        db: Database session.
        email: User's email address.
        username: User's username.
        password: User's plaintext password.
        full_name: User's full name (optional).
        is_superuser: Whether the user is a superuser.

    Returns:
        The created user.

    Raises:
        UserAlreadyExistsError: If email or username already exists.
    """
    email_lower = email.lower()
    username_lower = username.lower()

    # Check for existing user
    if get_user_by_email(db, email_lower):
        raise UserAlreadyExistsError(f"Email {email} is already registered")
    if get_user_by_username(db, username_lower):
        raise UserAlreadyExistsError(f"Username {username} is already taken")

    user = User(
        email=email_lower,
        username=username_lower,
        password_hash=hash_password(password),
        full_name=full_name,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    email_or_username: str,
    password: str,
) -> User:
    """Authenticate a user by email/username and password.

    Args:
        db: Database session.
        email_or_username: User's email or username.
        password: User's plaintext password.

    Returns:
        The authenticated user.

    Raises:
        InvalidCredentialsError: If credentials are invalid.
        InactiveUserError: If the user is inactive.
    """
    # Try email first, then username
    user = get_user_by_email(db, email_or_username)
    if not user:
        user = get_user_by_username(db, email_or_username)

    if not user:
        raise InvalidCredentialsError("Invalid email/username or password")

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email/username or password")

    if not user.is_active:
        raise InactiveUserError("User account is inactive")

    # Update last login time
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return user


def update_user_password(
    db: Session,
    user: User,
    new_password: str,
) -> User:
    """Update a user's password.

    Args:
        db: Database session.
        user: The user to update.
        new_password: The new plaintext password.

    Returns:
        The updated user.
    """
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def store_refresh_token(
    db: Session,
    user_id: uuid.UUID,
    token_jti: str,
    expires_at: datetime,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> RefreshToken:
    """Store a refresh token in the database.

    Args:
        db: Database session.
        user_id: The user's ID.
        token_jti: The JWT ID to hash and store.
        expires_at: Token expiration time.
        user_agent: Client user agent (optional).
        ip_address: Client IP address (optional).

    Returns:
        The stored refresh token record.
    """
    token = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token_jti),
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def validate_refresh_token(
    db: Session,
    user_id: uuid.UUID,
    token_jti: str,
) -> RefreshToken | None:
    """Validate a refresh token exists and is not revoked.

    Args:
        db: Database session.
        user_id: The user's ID from the token.
        token_jti: The JWT ID from the token.

    Returns:
        The refresh token record if valid, None otherwise.
    """
    token_hash = hash_token(token_jti)
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.now(timezone.utc),
    )
    return db.scalars(stmt).first()


def revoke_refresh_token(
    db: Session,
    user_id: uuid.UUID,
    token_jti: str,
) -> bool:
    """Revoke a specific refresh token.

    Args:
        db: Database session.
        user_id: The user's ID.
        token_jti: The JWT ID of the token to revoke.

    Returns:
        True if token was found and revoked, False otherwise.
    """
    token_hash = hash_token(token_jti)
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked_at.is_(None),
    )
    token = db.scalars(stmt).first()
    if token:
        token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return True
    return False


def revoke_all_user_tokens(
    db: Session,
    user_id: uuid.UUID,
) -> int:
    """Revoke all refresh tokens for a user.

    Args:
        db: Database session.
        user_id: The user's ID.

    Returns:
        Number of tokens revoked.
    """
    now = datetime.now(timezone.utc)
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    )
    tokens = db.scalars(stmt).all()
    count = 0
    for token in tokens:
        token.revoked_at = now
        count += 1
    db.commit()
    return count


def cleanup_expired_tokens(db: Session) -> int:
    """Remove expired refresh tokens from the database.

    Args:
        db: Database session.

    Returns:
        Number of tokens deleted.
    """
    now = datetime.now(timezone.utc)
    stmt = select(RefreshToken).where(RefreshToken.expires_at < now)
    tokens = db.scalars(stmt).all()
    count = len(tokens)
    for token in tokens:
        db.delete(token)
    db.commit()
    return count
