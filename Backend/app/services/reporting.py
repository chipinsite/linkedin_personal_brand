from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from ..models import Comment, PublishedPost
from .telegram_service import send_telegram_message


@dataclass
class DailyReport:
    report_date: date
    posts_published: int
    total_impressions: int
    total_reactions: int
    total_comments: int
    total_shares: int
    avg_engagement_rate: float
    auto_replies_sent: int
    escalations: int



def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min).replace(tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end



def build_daily_report(db: Session, for_date: date | None = None) -> DailyReport:
    target = for_date or datetime.now(timezone.utc).date()
    start, end = _day_bounds(target)

    posts = (
        db.query(PublishedPost)
        .filter(PublishedPost.published_at.is_not(None))
        .filter(PublishedPost.published_at >= start)
        .filter(PublishedPost.published_at < end)
        .all()
    )

    post_ids = [p.id for p in posts]
    comments = []
    if post_ids:
        comments = db.query(Comment).filter(Comment.published_post_id.in_(post_ids)).all()

    impressions = sum(int(p.impressions or 0) for p in posts)
    reactions = sum(int(p.reactions or 0) for p in posts)
    comments_count = sum(int(p.comments_count or 0) for p in posts)
    shares = sum(int(p.shares or 0) for p in posts)
    rates = [float(p.engagement_rate or 0.0) for p in posts if p.engagement_rate is not None]
    avg_rate = (sum(rates) / len(rates)) if rates else 0.0

    auto_replies = sum(1 for c in comments if c.auto_reply_sent)
    escalations = sum(1 for c in comments if c.escalated)

    return DailyReport(
        report_date=target,
        posts_published=len(posts),
        total_impressions=impressions,
        total_reactions=reactions,
        total_comments=comments_count,
        total_shares=shares,
        avg_engagement_rate=avg_rate,
        auto_replies_sent=auto_replies,
        escalations=escalations,
    )



def send_daily_report_telegram(db: Session, report: DailyReport) -> bool:
    text = (
        f"Daily LinkedIn Summary - {report.report_date.isoformat()}\\n\\n"
        f"Posts published: {report.posts_published}\\n"
        f"Impressions: {report.total_impressions}\\n"
        f"Reactions: {report.total_reactions}\\n"
        f"Comments: {report.total_comments}\\n"
        f"Shares: {report.total_shares}\\n"
        f"Average engagement rate: {report.avg_engagement_rate:.4f}\\n"
        f"Auto replies sent: {report.auto_replies_sent}\\n"
        f"Escalations: {report.escalations}"
    )
    return send_telegram_message(db=db, text=text, event_type="DAILY_SUMMARY")
