"""V6 Phase 5 Tests: Shadow Mode + Progressive Enablement

Tests:
- PipelineMode enum values
- get/set pipeline mode
- should_run_legacy gating
- should_run_v6 gating
- is_shadow_mode detection
- Pipeline status summary
- Publisher shadow mode (skip webhook/Telegram)
- Worker task gating (legacy skipped in v6 mode, V6 skipped in legacy mode)
- Admin pipeline-mode endpoint
- Admin pipeline-status endpoint
- Admin config includes pipeline_mode
- Migration 0009 adds pipeline_mode column
"""

import os
import json
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

os.environ["APP_ENV"] = "test"

from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import (
    AppConfig,
    ContentPipelineItem,
    Draft,
    DraftStatus,
    PipelineMode,
    PipelineStatus,
    PostFormat,
    PostTone,
    PublishedPost,
)


def fresh_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class TestPipelineModeEnum(unittest.TestCase):
    """PipelineMode enum has expected values."""

    def test_enum_members(self):
        self.assertEqual(PipelineMode.legacy.value, "LEGACY")
        self.assertEqual(PipelineMode.shadow.value, "SHADOW")
        self.assertEqual(PipelineMode.v6.value, "V6")
        self.assertEqual(PipelineMode.disabled.value, "DISABLED")

    def test_enum_count(self):
        self.assertEqual(len(PipelineMode), 4)


class TestAppConfigPipelineMode(unittest.TestCase):
    """AppConfig includes pipeline_mode column."""

    def test_default_mode(self):
        db = fresh_db()
        config = AppConfig(id=1)
        db.add(config)
        db.commit()
        db.refresh(config)
        self.assertEqual(config.pipeline_mode, PipelineMode.legacy)

    def test_set_mode(self):
        db = fresh_db()
        config = AppConfig(id=1, pipeline_mode=PipelineMode.shadow)
        db.add(config)
        db.commit()
        db.refresh(config)
        self.assertEqual(config.pipeline_mode, PipelineMode.shadow)


class TestGetSetPipelineMode(unittest.TestCase):
    """pipeline_mode service get/set operations."""

    def test_get_default_mode(self):
        db = fresh_db()
        from app.services.pipeline_mode import get_pipeline_mode
        mode = get_pipeline_mode(db)
        self.assertEqual(mode, PipelineMode.legacy)

    def test_set_and_get_mode(self):
        db = fresh_db()
        from app.services.pipeline_mode import get_pipeline_mode, set_pipeline_mode
        set_pipeline_mode(db, PipelineMode.v6)
        self.assertEqual(get_pipeline_mode(db), PipelineMode.v6)

    def test_set_shadow_mode(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, get_pipeline_mode
        set_pipeline_mode(db, PipelineMode.shadow)
        self.assertEqual(get_pipeline_mode(db), PipelineMode.shadow)


class TestShouldRunLegacy(unittest.TestCase):
    """Legacy task gating based on pipeline mode."""

    def test_legacy_mode_runs_legacy(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_legacy
        set_pipeline_mode(db, PipelineMode.legacy)
        self.assertTrue(should_run_legacy(db))

    def test_shadow_mode_runs_legacy(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_legacy
        set_pipeline_mode(db, PipelineMode.shadow)
        self.assertTrue(should_run_legacy(db))

    def test_v6_mode_skips_legacy(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_legacy
        set_pipeline_mode(db, PipelineMode.v6)
        self.assertFalse(should_run_legacy(db))

    def test_disabled_mode_skips_legacy(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_legacy
        set_pipeline_mode(db, PipelineMode.disabled)
        self.assertFalse(should_run_legacy(db))


class TestShouldRunV6(unittest.TestCase):
    """V6 task gating based on pipeline mode."""

    def test_v6_mode_runs_v6(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_v6
        set_pipeline_mode(db, PipelineMode.v6)
        self.assertTrue(should_run_v6(db))

    def test_shadow_mode_runs_v6(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_v6
        set_pipeline_mode(db, PipelineMode.shadow)
        self.assertTrue(should_run_v6(db))

    def test_legacy_mode_skips_v6(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_v6
        set_pipeline_mode(db, PipelineMode.legacy)
        self.assertFalse(should_run_v6(db))

    def test_disabled_mode_skips_v6(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, should_run_v6
        set_pipeline_mode(db, PipelineMode.disabled)
        self.assertFalse(should_run_v6(db))


class TestIsShadowMode(unittest.TestCase):
    """Shadow mode detection."""

    def test_shadow_mode_true(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, is_shadow_mode
        set_pipeline_mode(db, PipelineMode.shadow)
        self.assertTrue(is_shadow_mode(db))

    def test_legacy_not_shadow(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, is_shadow_mode
        set_pipeline_mode(db, PipelineMode.legacy)
        self.assertFalse(is_shadow_mode(db))

    def test_v6_not_shadow(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, is_shadow_mode
        set_pipeline_mode(db, PipelineMode.v6)
        self.assertFalse(is_shadow_mode(db))


class TestPipelineStatusSummary(unittest.TestCase):
    """Pipeline status summary aggregation."""

    def test_legacy_mode_summary(self):
        db = fresh_db()
        from app.services.pipeline_mode import get_pipeline_status_summary
        summary = get_pipeline_status_summary(db)
        self.assertEqual(summary["pipeline_mode"], "LEGACY")
        self.assertTrue(summary["legacy_active"])
        self.assertFalse(summary["v6_active"])
        self.assertFalse(summary["shadow_mode"])
        self.assertFalse(summary["v6_publishing_enabled"])

    def test_shadow_mode_summary(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, get_pipeline_status_summary
        set_pipeline_mode(db, PipelineMode.shadow)
        summary = get_pipeline_status_summary(db)
        self.assertEqual(summary["pipeline_mode"], "SHADOW")
        self.assertTrue(summary["legacy_active"])
        self.assertTrue(summary["v6_active"])
        self.assertTrue(summary["shadow_mode"])
        self.assertFalse(summary["v6_publishing_enabled"])

    def test_v6_mode_summary(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, get_pipeline_status_summary
        set_pipeline_mode(db, PipelineMode.v6)
        summary = get_pipeline_status_summary(db)
        self.assertEqual(summary["pipeline_mode"], "V6")
        self.assertFalse(summary["legacy_active"])
        self.assertTrue(summary["v6_active"])
        self.assertTrue(summary["v6_publishing_enabled"])

    def test_disabled_mode_summary(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, get_pipeline_status_summary
        set_pipeline_mode(db, PipelineMode.disabled)
        summary = get_pipeline_status_summary(db)
        self.assertTrue(summary["all_disabled"])
        self.assertFalse(summary["legacy_active"])
        self.assertFalse(summary["v6_active"])

    def test_kill_switch_overrides_mode(self):
        db = fresh_db()
        from app.services.pipeline_mode import set_pipeline_mode, get_pipeline_status_summary
        set_pipeline_mode(db, PipelineMode.v6)
        config = db.query(AppConfig).first()
        config.kill_switch = True
        db.commit()
        summary = get_pipeline_status_summary(db)
        self.assertTrue(summary["all_disabled"])
        self.assertFalse(summary["v6_active"])


class TestPublisherShadowMode(unittest.TestCase):
    """Publisher agent behavior in shadow mode."""

    def setUp(self):
        self.db = fresh_db()
        # Create a draft
        self.draft = Draft(
            pillar_theme="Adtech fundamentals",
            sub_theme="Programmatic buying",
            format=PostFormat.text,
            tone=PostTone.educational,
            content_body="Test content for shadow mode publishing.",
            status=DraftStatus.approved,
        )
        self.db.add(self.draft)
        self.db.commit()
        self.db.refresh(self.draft)

        # Create a pipeline item at READY_TO_PUBLISH
        self.item = ContentPipelineItem(
            draft_id=self.draft.id,
            status=PipelineStatus.ready_to_publish,
            pillar_theme="Adtech fundamentals",
            sub_theme="Programmatic buying",
            topic_keyword="programmatic",
        )
        self.db.add(self.item)
        self.db.commit()
        self.db.refresh(self.item)

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_normal_mode_fires_webhook(self, mock_telegram, mock_webhook):
        from app.services.agents.publisher import run_publisher
        count = run_publisher(self.db, shadow_mode=False)
        self.assertEqual(count, 1)
        mock_webhook.assert_called_once()
        mock_telegram.assert_called_once()

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_shadow_mode_skips_webhook(self, mock_telegram, mock_webhook):
        from app.services.agents.publisher import run_publisher
        count = run_publisher(self.db, shadow_mode=True)
        self.assertEqual(count, 1)
        # In shadow mode, webhook and Telegram should NOT be called
        mock_webhook.assert_not_called()
        mock_telegram.assert_not_called()

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_shadow_mode_still_creates_published_post(self, mock_telegram, mock_webhook):
        from app.services.agents.publisher import run_publisher
        run_publisher(self.db, shadow_mode=True)
        # PublishedPost should still be created for tracking
        posts = self.db.query(PublishedPost).all()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].draft_id, self.draft.id)

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_shadow_mode_still_transitions_item(self, mock_telegram, mock_webhook):
        from app.services.agents.publisher import run_publisher
        run_publisher(self.db, shadow_mode=True)
        self.db.refresh(self.item)
        self.assertEqual(self.item.status, PipelineStatus.published)


class TestAdminPipelineModeEndpoint(unittest.TestCase):
    """Admin endpoint for changing pipeline mode."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def test_change_to_shadow_mode(self):
        resp = self.client.post("/admin/pipeline-mode/shadow")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["pipeline_mode"], "SHADOW")

    def test_change_to_v6_mode(self):
        resp = self.client.post("/admin/pipeline-mode/v6")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["pipeline_mode"], "V6")

    def test_change_to_legacy_mode(self):
        resp = self.client.post("/admin/pipeline-mode/legacy")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["pipeline_mode"], "LEGACY")

    def test_invalid_mode_returns_error(self):
        resp = self.client.post("/admin/pipeline-mode/invalid")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("error", data)

    def test_change_to_disabled_mode(self):
        resp = self.client.post("/admin/pipeline-mode/disabled")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["pipeline_mode"], "DISABLED")


class TestAdminPipelineStatusEndpoint(unittest.TestCase):
    """Admin endpoint for pipeline status summary."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def test_pipeline_status_returns_summary(self):
        resp = self.client.get("/admin/pipeline-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("pipeline_mode", data)
        self.assertIn("legacy_active", data)
        self.assertIn("v6_active", data)
        self.assertIn("shadow_mode", data)
        self.assertIn("mode_descriptions", data)


class TestAdminConfigIncludesMode(unittest.TestCase):
    """GET /admin/config includes pipeline_mode."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def test_config_has_pipeline_mode(self):
        resp = self.client.get("/admin/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("pipeline_mode", data)


class TestMigration0009(unittest.TestCase):
    """Migration 0009 adds pipeline_mode column."""

    def test_column_exists_on_app_config(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = sa_inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("app_config")]
        self.assertIn("pipeline_mode", columns)


if __name__ == "__main__":
    unittest.main()
