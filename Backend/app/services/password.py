"""Password hashing service using bcrypt."""

from __future__ import annotations

import hashlib
import secrets

import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash of the password.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The bcrypt hash to verify against.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        password_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def generate_token() -> str:
    """Generate a cryptographically secure random token.

    Returns:
        A 64-character hex token.
    """
    return secrets.token_hex(32)


def hash_token(token: str) -> str:
    """Hash a token for storage using SHA-256.

    We use SHA-256 for tokens (not bcrypt) because:
    - Tokens are already random and high-entropy
    - We need fast comparison for frequent token checks
    - SHA-256 is sufficient for hashing random tokens

    Args:
        token: The plaintext token to hash.

    Returns:
        The SHA-256 hash of the token.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
