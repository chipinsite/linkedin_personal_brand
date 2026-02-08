from __future__ import annotations

from dataclasses import dataclass

from ..config import settings


DO_NOT_ENGAGE_MARKERS = ["http://", "https://", "buy now", "subscribe", "free crypto"]
SENSITIVE_MARKERS = ["politics", "religion", "war", "violence"]


@dataclass
class TriageResult:
    high_value: bool
    reason: str | None
    auto_reply: bool


def triage_comment(comment_text: str, follower_count: int | None) -> TriageResult:
    text = comment_text.strip()
    lowered = text.lower()

    if not text:
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    if all(ch in {"!", "?", ".", ",", " ", "\U0001F44D", "\U0001F525"} for ch in text):
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    if any(marker in lowered for marker in DO_NOT_ENGAGE_MARKERS):
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    if follower_count and follower_count >= settings.escalation_follower_threshold:
        return TriageResult(high_value=True, reason="INFLUENTIAL", auto_reply=False)

    if "collaborate" in lowered or "partner" in lowered or "opportunity" in lowered:
        return TriageResult(high_value=True, reason="PARTNERSHIP_SIGNAL", auto_reply=False)

    if "why" in lowered or "how" in lowered or "can you explain" in lowered:
        return TriageResult(high_value=True, reason="TECHNICAL_QUESTION", auto_reply=False)

    if "disagree" in lowered or "not true" in lowered:
        return TriageResult(high_value=True, reason="OBJECTION", auto_reply=False)

    return TriageResult(high_value=False, reason=None, auto_reply=True)
