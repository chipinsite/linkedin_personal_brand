from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.audit import log_audit
from ..services.auth import require_read_access, require_write_access
from ..services.reporting import build_daily_report, send_daily_report_telegram

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily")
def daily_report(for_date: date | None = None, db: Session = Depends(get_db), _auth: None = Depends(require_read_access)):
    report = build_daily_report(db=db, for_date=for_date)
    return {
        "report_date": report.report_date.isoformat(),
        "posts_published": report.posts_published,
        "total_impressions": report.total_impressions,
        "total_reactions": report.total_reactions,
        "total_comments": report.total_comments,
        "total_shares": report.total_shares,
        "avg_engagement_rate": report.avg_engagement_rate,
        "auto_replies_sent": report.auto_replies_sent,
        "escalations": report.escalations,
    }


@router.post("/daily/send")
def send_daily_report(
    for_date: date | None = None,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_write_access),
):
    report = build_daily_report(db=db, for_date=for_date)
    success = send_daily_report_telegram(db=db, report=report)
    log_audit(
        db=db,
        actor="api",
        action="report.daily.send",
        resource_type="notification",
        detail={"date": report.report_date.isoformat(), "success": success},
    )
    return {"sent": success, "date": report.report_date.isoformat()}
