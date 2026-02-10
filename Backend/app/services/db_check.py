"""Startup database schema validation.

Checks that expected tables exist in the connected database and logs
clear human-readable messages when the schema is incomplete.
"""

import logging

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

REQUIRED_TABLES = frozenset({
    "drafts",
    "published_posts",
    "comments",
    "app_config",
    "source_materials",
    "audit_logs",
    "notification_logs",
    "engagement_metrics",
    "learning_weights",
    "users",
    "refresh_tokens",
    "content_pipeline_items",
})


def check_schema(engine: Engine) -> dict:
    """Validate that all required tables exist in the database.

    Returns a dict with:
        - ok: bool
        - tables: dict mapping table name -> exists bool
        - missing: list of missing table names
    """
    try:
        inspector = sa_inspect(engine)
        existing = set(inspector.get_table_names())
    except Exception as exc:
        logger.error("DB schema check failed: could not inspect database: %s", exc)
        return {
            "ok": False,
            "tables": {t: False for t in sorted(REQUIRED_TABLES)},
            "missing": sorted(REQUIRED_TABLES),
            "error": str(exc),
        }

    table_status = {t: (t in existing) for t in sorted(REQUIRED_TABLES)}
    missing = [t for t, exists in table_status.items() if not exists]

    return {
        "ok": len(missing) == 0,
        "tables": table_status,
        "missing": missing,
    }


def startup_schema_check(engine: Engine) -> None:
    """Run schema check at startup. Logs errors if tables are missing.

    Raises SchemaError if required tables are absent so the app can
    fail fast with a clear message rather than returning 500s.
    """
    result = check_schema(engine)

    if result["ok"]:
        logger.info("DB schema check passed: all %d required tables present.", len(REQUIRED_TABLES))
        return

    missing = result["missing"]
    logger.error(
        "DB SCHEMA INCOMPLETE: %d required table(s) missing: %s. "
        "Run 'alembic upgrade head' to apply migrations before starting the app.",
        len(missing),
        ", ".join(missing),
    )
    raise SchemaError(
        f"Database schema is incomplete. Missing tables: {', '.join(missing)}. "
        "Run 'alembic upgrade head' to create the schema."
    )


class SchemaError(Exception):
    """Raised when required database tables are missing at startup."""
