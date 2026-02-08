from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
from sqlalchemy.orm import Session

from ..models import SourceMaterial
from .llm import summarize_source

DEFAULT_FEEDS = [
    "https://digiday.com/feed/",
    "https://www.adexchanger.com/feed/",
    "https://www.campaignlive.com/rss/news",
]

PILLAR_KEYWORDS = {
    "Adtech fundamentals": ["programmatic", "measurement", "attribution", "retail media", "supply path"],
    "Agentic AI in Adtech": ["agent", "autonomous", "bidding", "optimization", "orchestration"],
    "AI in advertising": ["generative", "ai", "model", "predictive", "machine learning"],
}


def _parse_published(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _score_item(text: str) -> tuple[float, str | None]:
    lowered = text.lower()
    best_score = 0.0
    best_pillar = None
    for pillar, keywords in PILLAR_KEYWORDS.items():
        score = float(sum(1 for word in keywords if word in lowered))
        if score > best_score:
            best_score = score
            best_pillar = pillar
    return best_score, best_pillar


def ingest_feed_entries(db: Session, source_name: str, entries: list[dict], max_items: int = 10) -> int:
    created = 0
    for entry in entries[:max_items]:
        url = entry.get("link")
        title = (entry.get("title") or "Untitled").strip()
        if not url:
            continue

        exists = db.query(SourceMaterial).filter(SourceMaterial.url == url).first()
        if exists:
            continue

        content = entry.get("summary") or entry.get("description") or title
        score, pillar = _score_item(f"{title} {content}")
        summary = summarize_source(source_name=source_name, title=title, content=content)

        source = SourceMaterial(
            source_name=source_name,
            title=title[:512],
            url=url[:1024],
            published_at=_parse_published(entry.get("published")),
            summary_text=summary,
            relevance_score=score,
            pillar_theme=pillar,
        )
        db.add(source)
        created += 1

    db.commit()
    return created


def ingest_feeds(db: Session, feed_urls: list[str], max_items_per_feed: int = 10) -> int:
    total_created = 0
    for url in feed_urls:
        parsed = feedparser.parse(url)
        source_name = parsed.feed.get("title") or url
        entries = [
            {
                "title": e.get("title"),
                "link": e.get("link"),
                "summary": e.get("summary") or e.get("description"),
                "published": e.get("published"),
            }
            for e in parsed.entries
        ]
        total_created += ingest_feed_entries(db, source_name=source_name, entries=entries, max_items=max_items_per_feed)
    return total_created


def select_research_context(db: Session, pillar: str, limit: int = 3) -> tuple[str, str]:
    results = (
        db.query(SourceMaterial)
        .filter(SourceMaterial.pillar_theme == pillar)
        .order_by(SourceMaterial.relevance_score.desc(), SourceMaterial.created_at.desc())
        .limit(limit)
        .all()
    )
    if not results:
        fallback = db.query(SourceMaterial).order_by(SourceMaterial.created_at.desc()).limit(limit).all()
        results = fallback

    if not results:
        return "", json.dumps([])

    lines = []
    citations = []
    for item in results:
        lines.append(f"- {item.source_name}: {item.summary_text or item.title}")
        citations.append({"source": item.source_name, "title": item.title, "url": item.url})

    return "\n".join(lines), json.dumps(citations)
