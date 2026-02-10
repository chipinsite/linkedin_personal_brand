"""Webhook Service.

Fires HTTP POST requests to a configurable Zapier webhook URL at key workflow events.
The primary event is `post.publish_ready` — Zapier receives the post content and publishes
it to LinkedIn automatically.

All webhook deliveries are logged to `notification_logs` (channel="webhook").
Retries up to 3 times with exponential backoff. Non-blocking: catches all exceptions
so the main request never fails due to a webhook error.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import NotificationLog

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]
TIMEOUT_SECONDS = 15


def _log_webhook(
    db: Session,
    event_type: str,
    payload: dict,
    success: bool,
    error_message: str | None = None,
    status_code: int | None = None,
    response_time_ms: float | None = None,
) -> None:
    """Log webhook delivery attempt to notification_logs."""
    meta = {**payload}
    if status_code is not None:
        meta["_status_code"] = status_code
    if response_time_ms is not None:
        meta["_response_time_ms"] = round(response_time_ms, 1)

    db.add(
        NotificationLog(
            channel="webhook",
            event_type=event_type,
            payload=json.dumps(meta),
            success=success,
            error_message=error_message,
        )
    )
    db.commit()


def _sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Create HMAC-SHA256 signature for webhook payload verification."""
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()


def _build_webhook_payload(event: str, data: dict[str, Any]) -> dict:
    """Build the standard webhook payload envelope."""
    return {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def is_webhook_configured() -> bool:
    """Check if a webhook URL is configured."""
    return bool(settings.zapier_webhook_url)


def send_webhook(
    db: Session,
    event: str,
    data: dict[str, Any],
) -> bool:
    """Fire a webhook POST to the configured Zapier URL.

    Args:
        db: Database session for logging.
        event: Event name (e.g. "post.publish_ready").
        data: Event-specific payload data.

    Returns:
        True if webhook was delivered successfully, False otherwise.
    """
    if not is_webhook_configured():
        logger.debug("Webhook not configured, skipping event=%s", event)
        return False

    webhook_url = settings.zapier_webhook_url
    payload = _build_webhook_payload(event, data)
    payload_bytes = json.dumps(payload).encode("utf-8")

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if settings.zapier_webhook_secret:
        headers["X-Webhook-Signature"] = _sign_payload(
            payload_bytes, settings.zapier_webhook_secret
        )

    last_error: str | None = None
    for attempt in range(MAX_RETRIES):
        try:
            start = time.monotonic()
            response = httpx.post(
                webhook_url,
                content=payload_bytes,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )
            elapsed_ms = (time.monotonic() - start) * 1000

            if response.status_code < 400:
                _log_webhook(
                    db,
                    event,
                    payload,
                    success=True,
                    status_code=response.status_code,
                    response_time_ms=elapsed_ms,
                )
                logger.info(
                    "Webhook delivered: event=%s status=%s time=%.0fms",
                    event,
                    response.status_code,
                    elapsed_ms,
                )
                return True

            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.warning(
                "Webhook attempt %d/%d failed: %s",
                attempt + 1,
                MAX_RETRIES,
                last_error,
            )
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "Webhook attempt %d/%d error: %s",
                attempt + 1,
                MAX_RETRIES,
                last_error,
            )

        # Backoff before next retry (skip sleep on last attempt)
        if attempt < MAX_RETRIES - 1:
            time.sleep(BACKOFF_SECONDS[attempt])

    # All retries exhausted
    _log_webhook(
        db,
        event,
        payload,
        success=False,
        error_message=last_error,
    )
    logger.error("Webhook delivery failed after %d attempts: event=%s", MAX_RETRIES, event)
    return False


def send_test_webhook(webhook_url: str | None = None) -> dict:
    """Send a test payload to verify webhook connectivity.

    Args:
        webhook_url: Optional override URL. Defaults to configured URL.

    Returns:
        Dict with success, status_code, response_time_ms, and error fields.
    """
    url = webhook_url or settings.zapier_webhook_url
    if not url:
        return {"success": False, "error": "No webhook URL configured"}

    payload = _build_webhook_payload("webhook.test", {
        "message": "Test webhook from LinkedIn Personal Brand Autoposter",
        "test": True,
    })
    payload_bytes = json.dumps(payload).encode("utf-8")

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if settings.zapier_webhook_secret:
        headers["X-Webhook-Signature"] = _sign_payload(
            payload_bytes, settings.zapier_webhook_secret
        )

    try:
        start = time.monotonic()
        response = httpx.post(url, content=payload_bytes, headers=headers, timeout=TIMEOUT_SECONDS)
        elapsed_ms = (time.monotonic() - start) * 1000

        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "response_time_ms": round(elapsed_ms, 1),
            "error": None if response.status_code < 400 else response.text[:200],
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}
