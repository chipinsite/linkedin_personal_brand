from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db

import redis as redis_lib

router = APIRouter()


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
