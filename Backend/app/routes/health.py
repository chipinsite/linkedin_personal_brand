import re

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..db import engine, get_db
from ..middleware.request_id import get_request_id
from ..services.db_check import check_schema

import redis as redis_lib

router = APIRouter()

# Pattern to redact credentials from DB URLs (user:password@host)
_CRED_RE = re.compile(r"://[^@]+@")


def _redact_url(url: str) -> str:
    """Redact credentials from a database URL for safe display."""
    return _CRED_RE.sub("://***@", url)


def _migration_head() -> dict:
    """Check current alembic migration head."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            rows = [r[0] for r in result]
            return {"current_head": rows[0] if rows else None, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"current_head": None, "error": str(exc)}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/deep")
def deep_health(db: Session = Depends(get_db)):
    db_ok = False
    redis_ok = False
    db_error = None
    redis_error = None

    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        db_error = str(exc)

    try:
        client = redis_lib.Redis.from_url(settings.redis_url, socket_timeout=2)
        redis_ok = bool(client.ping())
    except Exception as exc:  # noqa: BLE001
        redis_error = str(exc)

    overall = "ok" if db_ok and redis_ok else "degraded"
    return {
        "status": overall,
        "checks": {
            "database": {"ok": db_ok, "error": db_error},
            "redis": {"ok": redis_ok, "error": redis_error},
        },
    }


@router.get("/health/readiness")
def readiness(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as exc:  # noqa: BLE001
        return {"ready": False, "error": str(exc)}


@router.get("/health/db")
def db_diagnostic():
    """Diagnostic endpoint showing DB URL (redacted), migration head, and table status."""
    db_url = _redact_url(str(engine.url))
    migration = _migration_head()
    schema = check_schema(engine)

    return {
        "database_url": db_url,
        "migration": migration,
        "schema": {
            "ok": schema["ok"],
            "tables": schema["tables"],
            "missing": schema["missing"],
        },
    }


@router.get("/health/full")
def full_health(db: Session = Depends(get_db)):
    """Aggregated health check combining all sub-checks into a single response."""
    # Basic health
    basic = {"status": "ok"}

    # Database readiness
    db_ok = False
    db_error = None
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        db_error = str(exc)

    # Redis
    redis_ok = False
    redis_error = None
    try:
        client = redis_lib.Redis.from_url(settings.redis_url, socket_timeout=2)
        redis_ok = bool(client.ping())
    except Exception as exc:  # noqa: BLE001
        redis_error = str(exc)

    # Schema
    schema = check_schema(engine)

    # Migration
    migration = _migration_head()

    # Overall status
    all_ok = db_ok and redis_ok and schema["ok"]
    overall = "ok" if all_ok else "degraded"

    return {
        "status": overall,
        "app_env": settings.app_env,
        "request_id": get_request_id(),
        "checks": {
            "heartbeat": basic,
            "database": {"ok": db_ok, "error": db_error},
            "redis": {"ok": redis_ok, "error": redis_error},
            "schema": {"ok": schema["ok"], "missing": schema["missing"]},
            "migration": migration,
        },
    }
