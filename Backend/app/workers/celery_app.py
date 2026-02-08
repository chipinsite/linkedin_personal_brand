from celery import Celery
from celery.schedules import crontab

from ..config import settings

celery_app = Celery(
    "linkedbrand",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    timezone=settings.timezone,
    enable_utc=True,
    task_routes={
        "app.workers.tasks.*": {"queue": "default"},
    }
)

celery_app.conf.beat_schedule = {
    "send-daily-summary-report": {
        "task": "app.workers.tasks.send_daily_summary_report",
        "schedule": crontab(hour=18, minute=30),
    },
    "recompute-learning-weights": {
        "task": "app.workers.tasks.recompute_learning",
        "schedule": crontab(hour=23, minute=30),
    },
    "ingest-research-sources": {
        "task": "app.workers.tasks.ingest_research_sources",
        "schedule": crontab(hour=2, minute=0),
    },
    "generate-daily-draft": {
        "task": "app.workers.tasks.generate_daily_draft",
        "schedule": crontab(hour=4, minute=0),
    },
    "check-due-posts": {
        "task": "app.workers.tasks.schedule_posts",
        "schedule": crontab(minute="*/5"),
    },
    "poll-comments": {
        "task": "app.workers.tasks.poll_comments",
        "schedule": crontab(minute="*/10"),
    },
}
