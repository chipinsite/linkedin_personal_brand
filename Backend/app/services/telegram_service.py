from __future__ import annotations

import json

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import NotificationLog


def send_telegram_message(db: Session, text: str, event_type: str) -> bool:
    payload = {"chat_id": settings.telegram_chat_id, "text": text}

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        db.add(
            NotificationLog(
                channel="telegram",
                event_type=event_type,
                payload=json.dumps(payload),
                success=False,
                error_message="Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID",
            )
        )
        db.commit()
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        response = httpx.post(url, json=payload, timeout=10)
        ok = response.status_code == 200
        db.add(
            NotificationLog(
                channel="telegram",
                event_type=event_type,
                payload=json.dumps(payload),
                success=ok,
                error_message=None if ok else response.text,
            )
        )
        db.commit()
        return ok
    except Exception as exc:  # noqa: BLE001
        db.add(
            NotificationLog(
                channel="telegram",
                event_type=event_type,
                payload=json.dumps(payload),
                success=False,
                error_message=str(exc),
            )
        )
        db.commit()
        return False
