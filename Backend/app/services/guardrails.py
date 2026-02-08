from __future__ import annotations

import re

BANNED_PHRASES = [
    "game changer",
    "disrupt",
    "synergy",
    "leverage",
    "pivot",
    "deep dive",
    "unpack",
    "double down",
    "move the needle",
    "low hanging fruit",
]

UNVERIFIED_CLAIM_MARKERS = [
    "according to research",
    "studies show",
    "everyone knows",
    "proven that",
]

SUSPICIOUS_PERCENT_RE = re.compile(r"(?<!\d)\d{1,3}%")
URL_RE = re.compile(r"https?://")
TAG_RE = re.compile(r"@\w+")
ENGAGEMENT_BAIT_MARKERS = [
    "like if you agree",
    "comment yes",
    "drop yes",
    "tag a friend",
    "follow for more",
]


class GuardrailResult:
    def __init__(self, passed: bool, violations: list[str]):
        self.passed = passed
        self.violations = violations


def validate_post(content: str) -> GuardrailResult:
    violations: list[str] = []
    lowered = content.lower()

    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            violations.append(f"BANNED_PHRASE:{phrase}")

    hashtags = re.findall(r"#[A-Za-z0-9_]+", content)
    if len(hashtags) > 3:
        violations.append("HASHTAG_LIMIT_EXCEEDED")

    mentions = TAG_RE.findall(content)
    if len(mentions) > 3:
        violations.append("MENTION_OVERUSE")

    if len(content.split()) > 300:
        violations.append("WORD_LIMIT_EXCEEDED")

    if any(marker in lowered for marker in UNVERIFIED_CLAIM_MARKERS):
        violations.append("UNVERIFIED_CLAIM_LANGUAGE")

    percent_claims = SUSPICIOUS_PERCENT_RE.findall(content)
    if percent_claims and not URL_RE.search(content):
        violations.append("STAT_WITHOUT_SOURCE")

    quote_count = content.count('"') + content.count("'")
    if quote_count >= 4 and not URL_RE.search(content):
        violations.append("QUOTE_WITHOUT_SOURCE")

    if URL_RE.search(content):
        violations.append("EXTERNAL_LINK_IN_BODY")

    if any(marker in lowered for marker in ENGAGEMENT_BAIT_MARKERS):
        violations.append("ENGAGEMENT_BAIT_LANGUAGE")

    return GuardrailResult(passed=len(violations) == 0, violations=violations)
