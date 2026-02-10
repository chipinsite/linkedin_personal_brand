"""Celery worker and beat schedule for background tasks.

Defines:
- Celery app configuration
- Task definitions for all workflow operations
- V6 pipeline agent tasks (Scout, Writer, Editor, Publisher, Promoter)
- Beat schedule for automated scheduling

Requires Redis as broker/backend. Gracefully imports when Redis
is unavailable (tasks can still be called synchronously in tests).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Try to initialise Celery — graceful fallback if redis/celery not available
try:
    from celery import Celery
    from celery.schedules import crontab

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed — background tasks unavailable")


def create_celery_app() -> "Celery | None":
    """Create and configure the Celery application."""
    if not CELERY_AVAILABLE:
        return None

    broker_url = os.environ.get("CELERY_BROKER_URL", os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    result_backend = os.environ.get("CELERY_RESULT_BACKEND", broker_url)

    app = Celery(
        "personal_brand",
        broker=broker_url,
        backend=result_backend,
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Africa/Johannesburg",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )

    return app


celery_app = create_celery_app()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: get a fresh DB session for each task
# ─────────────────────────────────────────────────────────────────────────────

def _get_db_session():
    """Get a fresh database session for task execution."""
    from .db import SessionLocal
    return SessionLocal()


# ─────────────────────────────────────────────────────────────────────────────
# Legacy Workflow Tasks
# ─────────────────────────────────────────────────────────────────────────────

def _check_should_run_legacy(db):
    """Check if legacy tasks should run based on pipeline mode.

    Returns True if legacy tasks should execute. Returns False and logs
    a skip message if the pipeline mode excludes legacy.
    """
    try:
        from .services.pipeline_mode import should_run_legacy
        if not should_run_legacy(db):
            from .services.pipeline_mode import get_pipeline_mode
            mode = get_pipeline_mode(db)
            logger.info("Task skipped: pipeline mode is '%s' — legacy tasks disabled", mode.value)
            return False
        return True
    except Exception:
        # If pipeline_mode column doesn't exist yet, default to running legacy
        return True


def _check_should_run_v6(db):
    """Check if V6 tasks should run based on pipeline mode.

    Returns True if V6 tasks should execute. Returns False and logs
    a skip message if the pipeline mode excludes V6.
    """
    try:
        from .services.pipeline_mode import should_run_v6
        if not should_run_v6(db):
            from .services.pipeline_mode import get_pipeline_mode
            mode = get_pipeline_mode(db)
            logger.info("Task skipped: pipeline mode is '%s' — V6 tasks disabled", mode.value)
            return False
        return True
    except Exception:
        # If pipeline_mode column doesn't exist yet, default to running V6
        return True


def _task_create_system_draft():
    """Generate a system draft (daily at 04:00)."""
    db = _get_db_session()
    try:
        if not _check_should_run_legacy(db):
            return "skipped:pipeline_mode"
        from .services.workflow import create_system_draft
        draft = create_system_draft(db)
        logger.info("Task: system draft created id=%s", draft.id)
        return str(draft.id)
    except Exception as exc:
        logger.error("Task: system draft creation failed: %s", exc)
        raise
    finally:
        db.close()


def _task_publish_due():
    """Check and notify about due posts (every 5 minutes)."""
    db = _get_db_session()
    try:
        if not _check_should_run_legacy(db):
            return "skipped:pipeline_mode"
        from .services.workflow import publish_due_manual_posts
        count = publish_due_manual_posts(db)
        logger.info("Task: publish-due processed %d posts", count)
        return count
    except Exception as exc:
        logger.error("Task: publish-due failed: %s", exc)
        raise
    finally:
        db.close()


def _task_poll_comments():
    """Poll for new comments on published posts (every 10 minutes)."""
    db = _get_db_session()
    try:
        from .services.engagement import poll_and_store_comments
        result = poll_and_store_comments(db)
        count = result.get("posts_polled", 0) if isinstance(result, dict) else 0
        logger.info("Task: poll-comments processed %d posts", count)
        return count
    except Exception as exc:
        logger.error("Task: poll-comments failed: %s", exc)
        raise
    finally:
        db.close()


def _task_ingest_research():
    """Ingest research sources (daily at 02:00)."""
    db = _get_db_session()
    try:
        from .services.research_ingestion import ingest_feeds
        count = ingest_feeds(db, feed_urls=[])
        logger.info("Task: research ingestion got %d sources", count)
        return count
    except Exception as exc:
        logger.error("Task: research ingestion failed: %s", exc)
        raise
    finally:
        db.close()


def _task_recompute_learning():
    """Recompute learning weights (daily at 23:30)."""
    db = _get_db_session()
    try:
        from .services.learning import recompute_learning_weights
        recompute_learning_weights(db)
        logger.info("Task: learning weights recomputed")
    except Exception as exc:
        logger.error("Task: learning recompute failed: %s", exc)
        raise
    finally:
        db.close()


def _task_send_daily_summary():
    """Send daily summary report (daily at 18:30)."""
    db = _get_db_session()
    try:
        from .services.reporting import build_daily_report, send_daily_report_telegram
        report = build_daily_report(db)
        send_daily_report_telegram(db, report)
        logger.info("Task: daily summary sent")
    except Exception as exc:
        logger.error("Task: daily summary failed: %s", exc)
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# V6 Pipeline Agent Tasks
# ─────────────────────────────────────────────────────────────────────────────

def _task_run_scout():
    """Run the Scout agent to seed pipeline backlog (every 6 hours)."""
    db = _get_db_session()
    try:
        if not _check_should_run_v6(db):
            return "skipped:pipeline_mode"
        from .services.agents.scout import run_scout
        items = run_scout(db)
        logger.info("Task: scout created %d pipeline items", len(items))
        return len(items)
    except Exception as exc:
        logger.error("Task: scout failed: %s", exc)
        raise
    finally:
        db.close()


def _task_run_writer():
    """Run the Writer agent to generate drafts (every 2 hours)."""
    db = _get_db_session()
    try:
        if not _check_should_run_v6(db):
            return "skipped:pipeline_mode"
        from .services.agents.writer import run_writer
        count = run_writer(db)
        logger.info("Task: writer processed %d items", count)
        return count
    except Exception as exc:
        logger.error("Task: writer failed: %s", exc)
        raise
    finally:
        db.close()


def _task_run_editor():
    """Run the Editor agent to review drafts (every 2 hours)."""
    db = _get_db_session()
    try:
        if not _check_should_run_v6(db):
            return "skipped:pipeline_mode"
        from .services.agents.editor import run_editor
        count = run_editor(db)
        logger.info("Task: editor passed %d items", count)
        return count
    except Exception as exc:
        logger.error("Task: editor failed: %s", exc)
        raise
    finally:
        db.close()


def _task_run_publisher():
    """Run the Publisher agent to publish ready content (every 30 minutes)."""
    db = _get_db_session()
    try:
        if not _check_should_run_v6(db):
            return "skipped:pipeline_mode"
        from .services.agents.publisher import run_publisher
        # In shadow mode, publisher runs in dry-run mode (no webhook/Telegram)
        try:
            from .services.pipeline_mode import is_shadow_mode
            shadow = is_shadow_mode(db)
        except Exception:
            shadow = False
        count = run_publisher(db, shadow_mode=shadow)
        logger.info("Task: publisher published %d items (shadow=%s)", count, shadow)
        return count
    except Exception as exc:
        logger.error("Task: publisher failed: %s", exc)
        raise
    finally:
        db.close()


def _task_run_promoter():
    """Run the Promoter agent to send engagement prompts (every hour)."""
    db = _get_db_session()
    try:
        if not _check_should_run_v6(db):
            return "skipped:pipeline_mode"
        from .services.agents.promoter import run_promoter
        count = run_promoter(db)
        logger.info("Task: promoter promoted %d items", count)
        return count
    except Exception as exc:
        logger.error("Task: promoter failed: %s", exc)
        raise
    finally:
        db.close()


def _task_run_morgan():
    """Run the Morgan PM self-healing agent (every 15 minutes)."""
    db = _get_db_session()
    try:
        if not _check_should_run_v6(db):
            return "skipped:pipeline_mode"
        from .services.agents.morgan import run_morgan
        result = run_morgan(db)
        logger.info(
            "Task: morgan — recovered=%d reset=%d health=%s",
            result["stale_claims_recovered"],
            result["errored_items_reset"],
            result["health"]["health_status"],
        )
        return result
    except Exception as exc:
        logger.error("Task: morgan failed: %s", exc)
        raise
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Register tasks and beat schedule with Celery
# ─────────────────────────────────────────────────────────────────────────────

if celery_app is not None:
    # Register all task functions
    create_system_draft = celery_app.task(name="create_system_draft")(_task_create_system_draft)
    publish_due = celery_app.task(name="publish_due")(_task_publish_due)
    poll_comments = celery_app.task(name="poll_comments")(_task_poll_comments)
    ingest_research = celery_app.task(name="ingest_research")(_task_ingest_research)
    recompute_learning = celery_app.task(name="recompute_learning")(_task_recompute_learning)
    send_daily_summary = celery_app.task(name="send_daily_summary")(_task_send_daily_summary)

    # V6 pipeline tasks
    run_scout = celery_app.task(name="v6_run_scout")(_task_run_scout)
    run_writer = celery_app.task(name="v6_run_writer")(_task_run_writer)
    run_editor = celery_app.task(name="v6_run_editor")(_task_run_editor)
    run_publisher = celery_app.task(name="v6_run_publisher")(_task_run_publisher)
    run_promoter = celery_app.task(name="v6_run_promoter")(_task_run_promoter)
    run_morgan = celery_app.task(name="v6_run_morgan")(_task_run_morgan)

    # Beat schedule
    celery_app.conf.beat_schedule = {
        # Legacy workflow tasks
        "daily-draft-generation": {
            "task": "create_system_draft",
            "schedule": crontab(hour=4, minute=0),
        },
        "check-publish-due": {
            "task": "publish_due",
            "schedule": crontab(minute="*/5"),
        },
        "poll-comments": {
            "task": "poll_comments",
            "schedule": crontab(minute="*/10"),
        },
        "daily-research-ingestion": {
            "task": "ingest_research",
            "schedule": crontab(hour=2, minute=0),
        },
        "nightly-learning-recompute": {
            "task": "recompute_learning",
            "schedule": crontab(hour=23, minute=30),
        },
        "daily-summary-report": {
            "task": "send_daily_summary",
            "schedule": crontab(hour=18, minute=30),
        },
        # V6 pipeline agent tasks
        "v6-scout-scan": {
            "task": "v6_run_scout",
            "schedule": crontab(hour="*/6", minute=15),  # Every 6 hours at :15
        },
        "v6-writer-generate": {
            "task": "v6_run_writer",
            "schedule": crontab(hour="*/2", minute=30),  # Every 2 hours at :30
        },
        "v6-editor-review": {
            "task": "v6_run_editor",
            "schedule": crontab(hour="*/2", minute=45),  # Every 2 hours at :45
        },
        "v6-publisher-publish": {
            "task": "v6_run_publisher",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
        "v6-promoter-engage": {
            "task": "v6_run_promoter",
            "schedule": crontab(hour="*/1", minute=10),  # Every hour at :10
        },
        "v6-morgan-heal": {
            "task": "v6_run_morgan",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
    }

    logger.info(
        "Celery configured: %d tasks, %d beat schedules",
        len([create_system_draft, publish_due, poll_comments, ingest_research,
             recompute_learning, send_daily_summary, run_scout, run_writer,
             run_editor, run_publisher, run_promoter, run_morgan]),
        len(celery_app.conf.beat_schedule),
    )
else:
    logger.info("Celery not available — task functions defined but not registered")


# ─────────────────────────────────────────────────────────────────────────────
# Exports for direct invocation (tests, API triggers)
# ─────────────────────────────────────────────────────────────────────────────

# These are always available regardless of Celery status
TASK_REGISTRY = {
    "create_system_draft": _task_create_system_draft,
    "publish_due": _task_publish_due,
    "poll_comments": _task_poll_comments,
    "ingest_research": _task_ingest_research,
    "recompute_learning": _task_recompute_learning,
    "send_daily_summary": _task_send_daily_summary,
    "v6_run_scout": _task_run_scout,
    "v6_run_writer": _task_run_writer,
    "v6_run_editor": _task_run_editor,
    "v6_run_publisher": _task_run_publisher,
    "v6_run_promoter": _task_run_promoter,
    "v6_run_morgan": _task_run_morgan,
}
