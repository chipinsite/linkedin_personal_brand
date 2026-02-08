from __future__ import annotations

from fastapi import Header, HTTPException, status

from ..config import settings


def _write_key() -> str | None:
    return settings.app_write_api_key or settings.app_api_key


def _read_keys() -> list[str]:
    keys: list[str] = []
    if settings.app_read_api_key:
        keys.append(settings.app_read_api_key)
    if _write_key():
        keys.append(_write_key() or "")
    return [k for k in keys if k]


def require_read_access(x_api_key: str | None = Header(default=None)) -> None:
    if not settings.auth_enforce_read:
        return
    valid = _read_keys()
    if not valid:
        return
    if x_api_key not in valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def require_write_access(x_api_key: str | None = Header(default=None)) -> None:
    # Backward-compatible: if no write key is set, writes remain open for local/dev use.
    configured = _write_key()
    if not configured:
        return
    if x_api_key != configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
