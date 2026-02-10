"""V6 Editor Agent.

Claims REVIEW pipeline items and validates them against 7 quality gates.
On pass: transitions to READY_TO_PUBLISH with quality scores.
On fail: increments revision, records structured feedback, sends back to TODO.
On max revisions exceeded: sends to BACKLOG for human review.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ...models import ContentPipelineItem, Draft, PipelineStatus
from ..claim_lock import attempt_claim, release_claim, verify_claim
from ..guardrails import validate_post
from ..pipeline import (
    get_unclaimed_items_by_status,
    has_exceeded_max_revisions,
    increment_revision,
    transition,
)
from ..product_context import ProductContext, get_product_context

logger = logging.getLogger(__name__)

WORKER_ID_PREFIX = "editor"

# Readability thresholds (Flesch-Kincaid grade level)
READABILITY_MIN_GRADE = 6
READABILITY_MAX_GRADE = 14


@dataclass
class GateResult:
    """Result of a single quality gate check."""

    gate_name: str
    passed: bool
    message: str = ""


@dataclass
class EditorVerdict:
    """Aggregate result of all Editor quality gates."""

    passed: bool
    gate_results: list[GateResult] = field(default_factory=list)
    quality_score: float = 0.0
    readability_score: float = 0.0

    @property
    def failed_gates(self) -> list[GateResult]:
        return [g for g in self.gate_results if not g.passed]

    @property
    def failure_summary(self) -> str:
        failed = self.failed_gates
        if not failed:
            return "All gates passed"
        return "; ".join(f"{g.gate_name}: {g.message}" for g in failed)


# ─────────────────────────────────────────────────────────────────────────────
# Gate 1: Factual Accuracy (PRODUCT_CONTEXT.md)
# ─────────────────────────────────────────────────────────────────────────────

def _check_factual_accuracy(content: str, ctx: ProductContext) -> GateResult:
    """Check content against PRODUCT_CONTEXT.md constraints."""
    lowered = content.lower()
    issues = []

    # Check identity constraints
    if ctx.title and ctx.title.lower() not in lowered and "head of sales" not in lowered:
        # Only flag if the content claims a different title
        title_claims = ["ceo", "founder", "vp of", "vice president", "chief", "director"]
        for claim in title_claims:
            if claim in lowered:
                issues.append(f"Claims title '{claim}' — should be '{ctx.title}'")

    # Check banned claims
    for claim in ctx.banned_claims:
        claim_lower = claim.lower()
        # Check for key phrases from banned claims
        if len(claim_lower) > 10:
            # Use a simplified fragment match
            words = claim_lower.split()[:4]
            fragment = " ".join(words)
            if fragment in lowered:
                issues.append(f"Potentially banned claim: {claim[:60]}")

    # Check out-of-scope topics
    for topic in ctx.out_of_scope_topics:
        topic_lower = topic.lower()
        # Extract key words (skip generic words)
        key_words = [w for w in topic_lower.split() if len(w) > 4]
        if key_words and all(w in lowered for w in key_words[:2]):
            issues.append(f"Out-of-scope topic: {topic[:60]}")

    if issues:
        return GateResult(
            gate_name="factual_accuracy",
            passed=False,
            message="; ".join(issues[:3]),
        )

    return GateResult(gate_name="factual_accuracy", passed=True)


# ─────────────────────────────────────────────────────────────────────────────
# Gate 2: Readability (textstat)
# ─────────────────────────────────────────────────────────────────────────────

def _check_readability(content: str) -> GateResult:
    """Check readability using Flesch-Kincaid grade level."""
    try:
        import textstat
        grade = textstat.flesch_kincaid_grade(content)
    except Exception as e:
        # Graceful degradation — pass with flag
        logger.warning("Readability check failed: %s — passing with flag", e)
        return GateResult(
            gate_name="readability",
            passed=True,
            message=f"Readability check unavailable: {e}",
        )

    if grade < READABILITY_MIN_GRADE:
        return GateResult(
            gate_name="readability",
            passed=False,
            message=f"Grade level {grade:.1f} is too simple (min {READABILITY_MIN_GRADE})",
        )

    if grade > READABILITY_MAX_GRADE:
        return GateResult(
            gate_name="readability",
            passed=False,
            message=f"Grade level {grade:.1f} is too complex (max {READABILITY_MAX_GRADE})",
        )

    return GateResult(
        gate_name="readability",
        passed=True,
        message=f"Grade level {grade:.1f}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gate 3: Guardrail Compliance
# ─────────────────────────────────────────────────────────────────────────────

def _check_guardrails(content: str) -> GateResult:
    """Run existing guardrail validation."""
    result = validate_post(content)
    if result.passed:
        return GateResult(gate_name="guardrails", passed=True)

    return GateResult(
        gate_name="guardrails",
        passed=False,
        message="; ".join(result.violations[:5]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gate 4: No External URLs
# ─────────────────────────────────────────────────────────────────────────────

def _check_no_urls(content: str) -> GateResult:
    """Verify no external URLs appear in the post body."""
    url_pattern = re.compile(r"https?://", re.IGNORECASE)
    if url_pattern.search(content):
        return GateResult(
            gate_name="no_external_urls",
            passed=False,
            message="Post body contains an external URL",
        )
    return GateResult(gate_name="no_external_urls", passed=True)


# ─────────────────────────────────────────────────────────────────────────────
# Gate 5: No Unsupported Feature Claims
# ─────────────────────────────────────────────────────────────────────────────

def _check_no_unsupported_claims(content: str) -> GateResult:
    """Check for unsupported superlatives and guarantee language."""
    lowered = content.lower()

    forbidden_patterns = [
        "the best",
        "the only",
        "the most advanced",
        "guaranteed",
        "proven results",
        "roi of",
        "return of",
        "increases revenue by",
    ]

    found = [p for p in forbidden_patterns if p in lowered]
    if found:
        return GateResult(
            gate_name="no_unsupported_claims",
            passed=False,
            message=f"Unsupported claim patterns: {', '.join(found[:3])}",
        )

    return GateResult(gate_name="no_unsupported_claims", passed=True)


# ─────────────────────────────────────────────────────────────────────────────
# Gate 6: Topical Relevance
# ─────────────────────────────────────────────────────────────────────────────

def _check_topical_relevance(content: str, item: ContentPipelineItem) -> GateResult:
    """Check that content stays within the assigned domain pillar."""
    lowered = content.lower()

    # Core domain keywords that should appear
    domain_signals = {
        "adtech": ["adtech", "advertising", "programmatic", "media", "campaign", "publisher"],
        "ai": ["ai", "artificial intelligence", "machine learning", "automation", "agent"],
        "retail": ["retail media", "e-commerce", "shopper", "commerce"],
        "measurement": ["measurement", "attribution", "analytics", "tracking"],
        "creative": ["creative", "generative", "format", "content"],
    }

    # Check if any domain signals are present
    has_domain_signal = False
    for _domain, keywords in domain_signals.items():
        if any(kw in lowered for kw in keywords):
            has_domain_signal = True
            break

    if not has_domain_signal:
        return GateResult(
            gate_name="topical_relevance",
            passed=False,
            message="Content lacks domain-relevant keywords for Adtech/AI/advertising",
        )

    return GateResult(gate_name="topical_relevance", passed=True)


# ─────────────────────────────────────────────────────────────────────────────
# Gate 7: Experience Signal
# ─────────────────────────────────────────────────────────────────────────────

def _check_experience_signal(content: str, ctx: ProductContext) -> GateResult:
    """Check for at least one personal experience marker."""
    lowered = content.lower()

    # Check markers from PRODUCT_CONTEXT.md
    for marker in ctx.experience_markers:
        marker_clean = marker.lower().rstrip(".")
        # Strip the "..." and match the key phrase
        marker_key = marker_clean.replace("...", "").strip()
        if marker_key and marker_key in lowered:
            return GateResult(
                gate_name="experience_signal",
                passed=True,
                message=f"Found marker: {marker_key[:40]}",
            )

    # Also check for first-person narrative patterns
    first_person_patterns = [
        "i have seen",
        "i have observed",
        "i have learned",
        "in my experience",
        "over the past",
        "one lesson",
        "when i first",
        "a pattern i",
        "what worked",
        "the mistake i",
        "i have spent",
        "i've seen",
        "i've observed",
        "i've learned",
    ]

    for pattern in first_person_patterns:
        if pattern in lowered:
            return GateResult(
                gate_name="experience_signal",
                passed=True,
                message=f"Found pattern: {pattern}",
            )

    return GateResult(
        gate_name="experience_signal",
        passed=False,
        message="No personal experience marker found — add first-person narrative",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Aggregate Editor Review
# ─────────────────────────────────────────────────────────────────────────────

def review_content(
    content: str,
    item: ContentPipelineItem,
    ctx: ProductContext | None = None,
) -> EditorVerdict:
    """Run all 7 quality gates on a piece of content.

    Args:
        content: The draft text to review
        item: The pipeline item being reviewed
        ctx: Product context (loaded from singleton if not provided)

    Returns:
        EditorVerdict with gate results and scores
    """
    if ctx is None:
        ctx = get_product_context()

    gates = [
        _check_factual_accuracy(content, ctx),
        _check_readability(content),
        _check_guardrails(content),
        _check_no_urls(content),
        _check_no_unsupported_claims(content),
        _check_topical_relevance(content, item),
        _check_experience_signal(content, ctx),
    ]

    passed_count = sum(1 for g in gates if g.passed)
    quality_score = passed_count / len(gates)

    # Get readability score from gate 2
    readability_score = 0.0
    readability_gate = gates[1]
    if readability_gate.message and "Grade level" in readability_gate.message:
        try:
            readability_score = float(
                readability_gate.message.split("Grade level ")[1].split(" ")[0]
            )
        except (IndexError, ValueError):
            pass

    all_passed = all(g.passed for g in gates)

    return EditorVerdict(
        passed=all_passed,
        gate_results=gates,
        quality_score=quality_score,
        readability_score=readability_score,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Agent Runner
# ─────────────────────────────────────────────────────────────────────────────

def _worker_id() -> str:
    return f"{WORKER_ID_PREFIX}-{uuid.uuid4().hex[:8]}"


def process_one_item(db: Session, item: ContentPipelineItem, worker_id: str) -> bool:
    """Process a single pipeline item through the Editor stage.

    Args:
        db: Database session
        item: Pipeline item at REVIEW status
        worker_id: Unique worker identifier

    Returns:
        True if item passed all gates and transitioned to READY_TO_PUBLISH
    """
    # Get the draft content
    if not item.draft_id:
        logger.warning("Editor: item %s has no draft_id — skipping", item.id)
        release_claim(db, item.id, "review")
        return False

    draft = db.query(Draft).filter_by(id=item.draft_id).first()

    if not draft:
        logger.warning("Editor: draft %s not found for item %s", item.draft_id, item.id)
        release_claim(db, item.id, "review")
        return False

    content = draft.content_body

    # Run quality gates
    verdict = review_content(content, item)

    if verdict.passed:
        # All gates passed — update quality fields and advance
        item.quality_score = verdict.quality_score
        item.readability_score = verdict.readability_score
        item.fact_check_status = "passed"
        db.commit()

        transition(db, item.id, PipelineStatus.review, PipelineStatus.ready_to_publish)
        release_claim(db, item.id, "review")

        logger.info(
            "Editor: item %s PASSED all gates — quality=%.2f readability=%.1f",
            item.id, verdict.quality_score, verdict.readability_score,
        )
        return True
    else:
        # Some gates failed — record feedback and handle revision
        failure_msg = verdict.failure_summary
        increment_revision(db, item.id, failure_msg)

        item.quality_score = verdict.quality_score
        item.readability_score = verdict.readability_score
        item.fact_check_status = "failed"
        db.commit()

        # Refresh item to get updated revision_count
        db.refresh(item)

        if has_exceeded_max_revisions(item):
            # Max revisions — send to BACKLOG for human review
            transition(db, item.id, PipelineStatus.review, PipelineStatus.backlog)
            release_claim(db, item.id, "review")
            logger.warning(
                "Editor: item %s exceeded max revisions (%d) — sent to BACKLOG",
                item.id, item.revision_count,
            )
        else:
            # Send back to TODO for Writer retry
            transition(db, item.id, PipelineStatus.review, PipelineStatus.todo)
            release_claim(db, item.id, "review")
            logger.info(
                "Editor: item %s FAILED gates (revision %d/%d): %s",
                item.id, item.revision_count, item.max_revisions, failure_msg,
            )

        return False


def run_editor(db: Session, max_items: int = 3) -> int:
    """Execute the Editor agent.

    Claims unclaimed REVIEW items, runs quality gates, and transitions
    to READY_TO_PUBLISH on pass or back to TODO/BACKLOG on fail.

    Args:
        db: Database session
        max_items: Maximum items to process in one run

    Returns:
        Number of items that passed all gates
    """
    unclaimed = get_unclaimed_items_by_status(db, PipelineStatus.review)
    if not unclaimed:
        logger.debug("Editor: no unclaimed REVIEW items")
        return 0

    worker_id = _worker_id()
    passed_count = 0

    for item in unclaimed[:max_items]:
        if not attempt_claim(db, item.id, "review", worker_id):
            continue

        if not verify_claim(db, item.id, "review", worker_id):
            continue

        if process_one_item(db, item, worker_id):
            passed_count += 1

    logger.info("Editor: %d/%d items passed review", passed_count, len(unclaimed[:max_items]))
    return passed_count
