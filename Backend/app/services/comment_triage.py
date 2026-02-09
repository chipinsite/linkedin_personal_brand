from __future__ import annotations

from dataclasses import dataclass

from ..config import settings


DO_NOT_ENGAGE_MARKERS = ["http://", "https://", "buy now", "subscribe", "free crypto"]
SENSITIVE_MARKERS = ["politics", "religion", "war", "violence"]
MEDIA_INQUIRY_MARKERS = ["interview", "quote", "article", "feature", "podcast", "panel", "speak"]
PARTNERSHIP_MARKERS = ["collaborate", "partner", "opportunity", "work together", "connect"]
TECHNICAL_QUESTION_MARKERS = ["why", "how", "can you explain", "what do you mean", "could you clarify"]
OBJECTION_MARKERS = ["disagree", "not true", "incorrect", "wrong", "but actually"]


# High-value reason codes matching CLAUDE.md section 5.3
class HighValueReason:
    PARTNERSHIP_SIGNAL = "PARTNERSHIP_SIGNAL"
    TECHNICAL_QUESTION = "TECHNICAL_QUESTION"
    OBJECTION = "OBJECTION"
    INFLUENTIAL = "INFLUENTIAL"
    MEDIA_INQUIRY = "MEDIA_INQUIRY"


@dataclass
class TriageResult:
    high_value: bool
    reason: str | None
    auto_reply: bool


def triage_comment(comment_text: str, follower_count: int | None) -> TriageResult:
    """Triage a comment to determine if it's high-value and how to respond.

    High-value reasons (per CLAUDE.md section 5.3):
    - PARTNERSHIP_SIGNAL: Mentions collaboration, partnership, business opportunity
    - TECHNICAL_QUESTION: Asks for detailed explanation or expertise
    - OBJECTION: Disagrees with the post or raises counterarguments
    - INFLUENTIAL: Account has > escalation_follower_threshold followers
    - MEDIA_INQUIRY: Mentions interview, quote, or article

    Args:
        comment_text: The comment text to analyze
        follower_count: Commenter's follower count (if known)

    Returns:
        TriageResult with high_value flag, reason, and auto_reply eligibility
    """
    text = comment_text.strip()
    lowered = text.lower()

    # Empty or whitespace-only
    if not text:
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    # Emoji-only or punctuation-only comments
    if all(ch in {"!", "?", ".", ",", " ", "\U0001F44D", "\U0001F525", "\U0001F64F", "\U0001F44F"} for ch in text):
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    # Do not engage with spam or promotional content
    if any(marker in lowered for marker in DO_NOT_ENGAGE_MARKERS):
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    # Do not engage with sensitive topics
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        return TriageResult(high_value=False, reason=None, auto_reply=False)

    # High-value checks (order matters - more specific first)

    # Media inquiry - interview/podcast/article requests
    if any(marker in lowered for marker in MEDIA_INQUIRY_MARKERS):
        return TriageResult(high_value=True, reason=HighValueReason.MEDIA_INQUIRY, auto_reply=False)

    # Influential commenter
    if follower_count and follower_count >= settings.escalation_follower_threshold:
        return TriageResult(high_value=True, reason=HighValueReason.INFLUENTIAL, auto_reply=False)

    # Partnership signals
    if any(marker in lowered for marker in PARTNERSHIP_MARKERS):
        return TriageResult(high_value=True, reason=HighValueReason.PARTNERSHIP_SIGNAL, auto_reply=False)

    # Objections or challenges (check before technical questions to avoid false positives from "show" containing "how")
    if any(marker in lowered for marker in OBJECTION_MARKERS):
        return TriageResult(high_value=True, reason=HighValueReason.OBJECTION, auto_reply=False)

    # Technical questions requiring expertise
    if any(marker in lowered for marker in TECHNICAL_QUESTION_MARKERS):
        return TriageResult(high_value=True, reason=HighValueReason.TECHNICAL_QUESTION, auto_reply=False)

    # Default: eligible for auto-reply
    return TriageResult(high_value=False, reason=None, auto_reply=True)
