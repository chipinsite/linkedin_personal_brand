"""Pipeline mode management service.

Controls which pipeline (legacy, V6, or both in shadow mode) is active.
Provides gating functions for task execution and mode transitions.

Modes:
- legacy: Only legacy workflow tasks run (default, current behavior)
- shadow: Both legacy and V6 run, but V6 Publisher does NOT publish (dry-run)
- v6: Only V6 pipeline tasks run, legacy tasks are no-ops
- disabled: All pipeline/content tasks are no-ops (emergency stop, beyond kill switch)
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..models import AppConfig, PipelineMode
from .config_state import get_or_create_app_config

logger = logging.getLogger(__name__)


def get_pipeline_mode(db: Session) -> PipelineMode:
    """Return the current pipeline mode from AppConfig."""
    config = get_or_create_app_config(db)
    # Handle case where column doesn't exist yet (pre-migration)
    mode = getattr(config, "pipeline_mode", None)
    if mode is None:
        return PipelineMode.legacy
    return mode


def set_pipeline_mode(db: Session, mode: PipelineMode) -> PipelineMode:
    """Update the pipeline mode.

    Args:
        db: Database session
        mode: New pipeline mode to set

    Returns:
        The new pipeline mode
    """
    config = get_or_create_app_config(db)
    config.pipeline_mode = mode
    db.commit()
    logger.info("Pipeline mode changed to: %s", mode.value)
    return mode


def should_run_legacy(db: Session) -> bool:
    """Return True if legacy workflow tasks should execute.

    Legacy runs in:
    - legacy mode (default)
    - shadow mode (legacy continues normally alongside V6)

    Legacy does NOT run in:
    - v6 mode (V6 pipeline is primary)
    - disabled mode (everything stopped)
    """
    mode = get_pipeline_mode(db)
    return mode in (PipelineMode.legacy, PipelineMode.shadow)


def should_run_v6(db: Session) -> bool:
    """Return True if V6 pipeline agent tasks should execute.

    V6 runs in:
    - v6 mode (V6 is primary)
    - shadow mode (V6 runs but Publisher doesn't publish)

    V6 does NOT run in:
    - legacy mode (only legacy workflow)
    - disabled mode (everything stopped)
    """
    mode = get_pipeline_mode(db)
    return mode in (PipelineMode.v6, PipelineMode.shadow)


def is_shadow_mode(db: Session) -> bool:
    """Return True if running in shadow mode.

    In shadow mode:
    - Legacy tasks run normally (drafts, publish-due, etc.)
    - V6 agents run through their full pipeline
    - V6 Publisher processes items but does NOT fire webhooks or Telegram
    - V6 Publisher still creates PublishedPost records (for tracking/comparison)
    - Morgan PM still monitors and heals the V6 pipeline
    """
    return get_pipeline_mode(db) == PipelineMode.shadow


def get_pipeline_status_summary(db: Session) -> dict:
    """Return a summary of the pipeline mode and operational state.

    Used by admin endpoints to provide visibility into which systems are active.
    """
    from .config_state import is_kill_switch_on, is_posting_enabled

    mode = get_pipeline_mode(db)
    kill = is_kill_switch_on(db)
    posting = is_posting_enabled(db)

    return {
        "pipeline_mode": mode.value,
        "kill_switch": kill,
        "posting_enabled": posting,
        "legacy_active": mode in (PipelineMode.legacy, PipelineMode.shadow) and not kill,
        "v6_active": mode in (PipelineMode.v6, PipelineMode.shadow) and not kill,
        "v6_publishing_enabled": mode == PipelineMode.v6 and not kill,
        "shadow_mode": mode == PipelineMode.shadow,
        "all_disabled": mode == PipelineMode.disabled or kill,
        "mode_descriptions": {
            "legacy": "Only legacy workflow runs. V6 pipeline tasks are skipped.",
            "shadow": "Both legacy and V6 run. V6 processes content but does NOT publish (dry-run).",
            "v6": "Only V6 pipeline runs. Legacy draft generation and publish-due are skipped.",
            "disabled": "All pipeline and content tasks are stopped.",
        },
    }
