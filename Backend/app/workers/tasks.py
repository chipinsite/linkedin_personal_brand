from datetime import datetime, timezone

from ..config import settings
from ..db import SessionLocal
from ..services.audit import log_audit
from ..services.engagement import poll_and_store_comments
from ..services.learning import recompute_learning_weights
from ..services.research_ingestion import DEFAULT_FEEDS, ingest_feeds
from ..services.reporting import build_daily_report, send_daily_report_telegram
from ..services.workflow import create_system_draft, publish_due_manual_posts
from .celery_app import celery_app


@celery_app.task
def send_daily_summary_report():
    db = SessionLocal()
    try:
        report = build_daily_report(db=db)
        sent = send_daily_report_telegram(db=db, report=report)
        log_audit(
            db=db,
            actor="worker",
            action="report.daily.send",
            resource_type="notification",
            detail={"date": report.report_date.isoformat(), "success": sent},
        )
        return {
            "status": "ok" if sent else "failed",
            "date": report.report_date.isoformat(),
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


@celery_app.task
def recompute_learning():
    db = SessionLocal()
    try:
        row = recompute_learning_weights(db)
        log_audit(
            db=db,
            actor="worker",
            action="learning.recompute",
            resource_type="learning_weight",
            resource_id="1",
        )
        return {
            "status": "ok",
            "updated_at": row.updated_at.isoformat(),
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


@celery_app.task
def ingest_research_sources():
    db = SessionLocal()
    try:
        configured = [item.strip() for item in settings.research_feed_urls.split(",") if item.strip()]
        feeds = configured or DEFAULT_FEEDS
        created = ingest_feeds(db=db, feed_urls=feeds, max_items_per_feed=10)
        log_audit(
            db=db,
            actor="worker",
            action="source.ingest",
            resource_type="source_material",
            detail={"created": created, "feeds_count": len(feeds)},
        )
        return {
            "status": "ok",
            "created": created,
            "feeds_count": len(feeds),
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


@celery_app.task
def generate_daily_draft():
    db = SessionLocal()
    try:
        try:
            draft = create_system_draft(db)
            log_audit(
                db=db,
                actor="worker",
                action="draft.generate",
                resource_type="draft",
                resource_id=str(draft.id),
                detail={"status": draft.status.value},
            )
            return {
                "status": "ok",
                "draft_id": str(draft.id),
                "ran_at": datetime.now(timezone.utc).isoformat(),
            }
        except RuntimeError as exc:
            return {
                "status": "skipped",
                "reason": str(exc),
                "ran_at": datetime.now(timezone.utc).isoformat(),
            }
    finally:
        db.close()


@celery_app.task
def schedule_posts():
    db = SessionLocal()
    try:
        processed = publish_due_manual_posts(db)
        log_audit(
            db=db,
            actor="worker",
            action="post.publish_due",
            resource_type="published_post",
            detail={"processed": processed},
        )
        return {
            "status": "ok",
            "processed": processed,
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


@celery_app.task
def poll_comments():
    db = SessionLocal()
    try:
        result = poll_and_store_comments(db=db, since_minutes=15)
        log_audit(
            db=db,
            actor="worker",
            action="engagement.poll",
            resource_type="comment",
            detail=result,
        )
        return {
            "status": result.get("status"),
            "processed_posts": result.get("processed_posts"),
            "new_comments": result.get("new_comments"),
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()
