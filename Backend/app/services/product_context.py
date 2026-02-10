"""PRODUCT_CONTEXT.md loader for V6 Editor agent fact-checking.

Parses the structured Markdown file and exposes typed helpers for
identity constraints, banned claims, domain topics, experience markers,
banned phrases, and engagement bait.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Default location relative to the repo root
_DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__),  # app/services/
    "..", "..", "..",            # → repo root (Personal Brand/)
    "PRODUCT_CONTEXT.md",
)


@dataclass
class ProductContext:
    """Parsed product context for Editor validation."""

    # Section 1
    name: str = ""
    title: str = ""
    experience_descriptor: str = ""
    geographic_focus: str = ""

    # Section 2
    in_scope_topics: list[str] = field(default_factory=list)
    out_of_scope_topics: list[str] = field(default_factory=list)

    # Section 3
    banned_claims: list[str] = field(default_factory=list)

    # Section 4
    banned_phrases: list[str] = field(default_factory=list)
    engagement_bait: list[str] = field(default_factory=list)

    # Section 7
    experience_markers: list[str] = field(default_factory=list)

    # Raw text for fallback pattern matching
    raw_text: str = ""


def _extract_list_items(text: str, section_header: str, stop_headers: list[str] | None = None) -> list[str]:
    """Extract bullet-point items from a markdown section."""
    # Find the section
    pattern = re.escape(section_header)
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return []

    start = match.end()

    # Find where the section ends (next ## or specified headers)
    end = len(text)
    if stop_headers:
        for sh in stop_headers:
            next_match = re.search(re.escape(sh), text[start:], re.IGNORECASE)
            if next_match:
                end = min(end, start + next_match.start())
    else:
        next_section = re.search(r"\n##\s", text[start:])
        if next_section:
            end = start + next_section.start()

    section_text = text[start:end]

    # Extract lines starting with -
    items = []
    for line in section_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- "):
            item = stripped[2:].strip().strip('"').strip("'")
            if item:
                items.append(item)

    return items


def load_product_context(filepath: str | None = None) -> ProductContext:
    """Load and parse PRODUCT_CONTEXT.md.

    Args:
        filepath: Path to the markdown file. Defaults to repo-root PRODUCT_CONTEXT.md.

    Returns:
        Parsed ProductContext object. Returns empty context if file is missing.
    """
    path = filepath or os.path.normpath(_DEFAULT_PATH)

    if not os.path.exists(path):
        logger.warning("PRODUCT_CONTEXT.md not found at %s — using empty context", path)
        return ProductContext()

    raw = Path(path).read_text(encoding="utf-8")

    ctx = ProductContext(raw_text=raw)

    # Section 1: Professional Identity
    name_match = re.search(r"\*\*Name:\*\*\s*(.+)", raw)
    if name_match:
        ctx.name = name_match.group(1).strip()

    title_match = re.search(r"\*\*Current title:\*\*\s*(.+)", raw)
    if title_match:
        ctx.title = title_match.group(1).strip()

    exp_match = re.search(r"\*\*Years of experience:\*\*\s*(.+)", raw)
    if exp_match:
        ctx.experience_descriptor = exp_match.group(1).strip()

    geo_match = re.search(r"\*\*Geographic focus:\*\*\s*(.+)", raw)
    if geo_match:
        ctx.geographic_focus = geo_match.group(1).strip()

    # Section 2: Domain topics
    ctx.in_scope_topics = _extract_list_items(
        raw,
        "### Primary Domains (In Scope)",
        stop_headers=["### Adjacent Topics", "### Out of Scope"],
    )
    # Also gather sub-bullets under each Domain heading
    for domain_header in ["#### Domain 1:", "#### Domain 2:", "#### Domain 3:"]:
        ctx.in_scope_topics.extend(_extract_list_items(
            raw, domain_header,
            stop_headers=["#### Domain", "### Adjacent", "### Out of Scope", "---"],
        ))

    ctx.out_of_scope_topics = _extract_list_items(
        raw,
        "### Out of Scope (Never Write About)",
        stop_headers=["---"],
    )

    # Section 3: Banned claims
    ctx.banned_claims = _extract_list_items(
        raw,
        "### Claims I Must NOT Make",
        stop_headers=["---"],
    )

    # Section 4: Banned phrases
    ctx.banned_phrases = _extract_list_items(
        raw,
        "### Banned Phrases",
        stop_headers=["### Engagement Bait", "---"],
    )

    # Engagement bait
    ctx.engagement_bait = _extract_list_items(
        raw,
        "### Engagement Bait (Never Used)",
        stop_headers=["---"],
    )

    # Section 7: Experience markers
    ctx.experience_markers = _extract_list_items(
        raw,
        "### Experience Signal Markers",
        stop_headers=["---"],
    )

    logger.info(
        "Product context loaded: %d in-scope topics, %d out-of-scope, "
        "%d banned claims, %d banned phrases, %d experience markers",
        len(ctx.in_scope_topics),
        len(ctx.out_of_scope_topics),
        len(ctx.banned_claims),
        len(ctx.banned_phrases),
        len(ctx.experience_markers),
    )

    return ctx


# Singleton cached context
_cached_context: ProductContext | None = None


def get_product_context(filepath: str | None = None) -> ProductContext:
    """Get the product context (cached after first load)."""
    global _cached_context
    if _cached_context is None:
        _cached_context = load_product_context(filepath)
    return _cached_context


def reload_product_context(filepath: str | None = None) -> ProductContext:
    """Force reload the product context."""
    global _cached_context
    _cached_context = load_product_context(filepath)
    return _cached_context
