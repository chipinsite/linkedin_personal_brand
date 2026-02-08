"""Structured logging configuration.

In production (log_json=True or app_env=prod), outputs JSON lines.
In dev mode, uses standard human-readable format.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Minimal JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_entry["request_id"] = request_id
        return json.dumps(log_entry, default=str)


def configure_logging(*, level: str = "INFO", json_format: bool = False) -> None:
    """Configure root logger with appropriate formatter and level."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicate output
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s [%(name)s] %(message)s")
        )

    root.addHandler(handler)
