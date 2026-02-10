"""Tests for V6 Phase 4: Morgan PM self-healing agent, pipeline health,
and expanded pipeline routes/worker integration.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# ── Environment setup ────────────────────────────────────────────────────────
DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v6_phase4_test.db")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["APP_ENV"] = "test"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ["LLM_API_KEY"] = ""

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, ContentPipelineItem, PipelineStatus, SocialStatus, Draft, PostFormat, PostTone, DraftStatus

engine = create_engine(f"sqlite+pysqlite:///{DB_PATH}")
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def _fresh_db():
    db = Session()
    db.query(ContentPipelineItem).delete()
    db.query(Draft).delete()
    db.commit()
    return db


def _make_item(db, status=PipelineStatus.backlog, **kwargs):
    """Create a pipeline item with given status and optional overrides."""
    item = ContentPipelineItem(
        status=status,
        pillar_theme=kwargs.get("pillar_theme", "Adtech fundamentals"),
        sub_theme=kwargs.get("sub_theme", "Programmatic buying"),
        topic_keyword=kwargs.get("topic_keyword", "test-topic"),
        **{k: v for k, v in kwargs.items() if k not in ("pillar_theme", "sub_theme", "topic_keyword")},
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ── Test: Stale Claim Recovery ────────────────────────────────────────────────

class TestStaleClaimeRecovery(unittest.TestCase):
    """Morgan should release pipeline items with expired claims."""

    def test_releases_stale_claim(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        # Simulate a stale claim (claimed 60 minutes ago)
        item.claimed_by = "writer-001"
        item.claimed_at = datetime.now(timezone.utc) - timedelta(minutes=60)
        item.claim_stage = "writing"
        item.claim_expires_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        db.commit()

        from app.services.agents.morgan import recover_stale_claims
        recoveries = recover_stale_claims(db, max_age_minutes=30)

        self.assertEqual(len(recoveries), 1)
        self.assertEqual(recoveries[0]["action"], "stale_claim_released")
        self.assertEqual(recoveries[0]["previous_worker"], "writer-001")

        # Verify claim is actually released
        db.refresh(item)
        self.assertIsNone(item.claimed_by)
        self.assertIsNone(item.claimed_at)
        db.close()

    def test_ignores_fresh_claims(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        # Fresh claim (just now)
        item.claimed_by = "writer-002"
        item.claimed_at = datetime.now(timezone.utc)
        item.claim_stage = "writing"
        item.claim_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.commit()

        from app.services.agents.morgan import recover_stale_claims
        recoveries = recover_stale_claims(db, max_age_minutes=30)

        self.assertEqual(len(recoveries), 0)

        # Verify claim is still held
        db.refresh(item)
        self.assertEqual(item.claimed_by, "writer-002")
        db.close()

    def test_recovers_multiple_stale_claims(self):
        db = _fresh_db()
        past = datetime.now(timezone.utc) - timedelta(minutes=60)
        for i in range(3):
            item = _make_item(db, status=PipelineStatus.review)
            item.claimed_by = f"editor-{i}"
            item.claimed_at = past
            item.claim_stage = "review"
            item.claim_expires_at = past + timedelta(minutes=30)
            db.commit()

        from app.services.agents.morgan import recover_stale_claims
        recoveries = recover_stale_claims(db, max_age_minutes=30)
        self.assertEqual(len(recoveries), 3)
        db.close()


# ── Test: Error Reset ─────────────────────────────────────────────────────────

class TestErrorReset(unittest.TestCase):
    """Morgan should reset errored items that are stuck without progress."""

    def test_resets_writing_error_to_todo(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        item.last_error = "Writer failed: LLM timeout"
        item.updated_at = datetime.now(timezone.utc) - timedelta(minutes=120)
        db.commit()

        from app.services.agents.morgan import reset_errored_items
        resets = reset_errored_items(db, stale_minutes=60)

        self.assertEqual(len(resets), 1)
        self.assertEqual(resets[0]["from_status"], "writing")
        self.assertEqual(resets[0]["to_status"], "todo")

        db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.todo)
        self.assertIsNone(item.last_error)
        db.close()

    def test_resets_review_error_to_todo(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.review)
        item.last_error = "Editor failed: readability check crash"
        item.updated_at = datetime.now(timezone.utc) - timedelta(minutes=120)
        db.commit()

        from app.services.agents.morgan import reset_errored_items
        resets = reset_errored_items(db, stale_minutes=60)

        self.assertEqual(len(resets), 1)
        db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.todo)
        db.close()

    def test_resets_ready_to_publish_error_to_backlog(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.ready_to_publish)
        item.last_error = "Publisher failed: webhook timeout"
        item.updated_at = datetime.now(timezone.utc) - timedelta(minutes=120)
        db.commit()

        from app.services.agents.morgan import reset_errored_items
        resets = reset_errored_items(db, stale_minutes=60)

        self.assertEqual(len(resets), 1)
        db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.backlog)
        db.close()

    def test_skips_recently_updated_errors(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        item.last_error = "Writer failed: LLM timeout"
        item.updated_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        from app.services.agents.morgan import reset_errored_items
        resets = reset_errored_items(db, stale_minutes=60)

        self.assertEqual(len(resets), 0)
        db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.writing)
        db.close()

    def test_skips_claimed_errored_items(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        item.last_error = "Writer failed"
        item.updated_at = datetime.now(timezone.utc) - timedelta(minutes=120)
        item.claimed_by = "writer-003"
        item.claimed_at = datetime.now(timezone.utc)
        db.commit()

        from app.services.agents.morgan import reset_errored_items
        resets = reset_errored_items(db, stale_minutes=60)

        self.assertEqual(len(resets), 0)
        db.close()

    def test_skips_max_auto_resets_exceeded(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        item.last_error = "Writer failed"
        item.updated_at = datetime.now(timezone.utc) - timedelta(minutes=120)
        # max_revisions=3, MORGAN_MAX_AUTO_RESETS=2, so skip at revision_count >= 5
        item.revision_count = 5
        item.max_revisions = 3
        db.commit()

        from app.services.agents.morgan import reset_errored_items
        resets = reset_errored_items(db, stale_minutes=60)

        self.assertEqual(len(resets), 0)
        db.close()


# ── Test: Health Report ───────────────────────────────────────────────────────

class TestHealthReport(unittest.TestCase):
    """Morgan should generate accurate pipeline health reports."""

    def test_healthy_pipeline(self):
        db = _fresh_db()
        _make_item(db, status=PipelineStatus.done)
        _make_item(db, status=PipelineStatus.backlog)

        from app.services.agents.morgan import generate_health_report
        report = generate_health_report(db)

        self.assertEqual(report["health_status"], "healthy")
        self.assertEqual(report["stale_claims"], 0)
        self.assertEqual(report["errored_items"], 0)
        self.assertEqual(report["stuck_items"], 0)
        self.assertIn("overview", report)
        self.assertIn("checked_at", report)
        db.close()

    def test_degraded_with_errored_items(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        item.last_error = "Writer timeout"
        db.commit()

        from app.services.agents.morgan import generate_health_report
        report = generate_health_report(db)

        self.assertEqual(report["health_status"], "degraded")
        self.assertEqual(report["errored_items"], 1)
        db.close()

    def test_unhealthy_with_stale_claims(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.writing)
        item.claimed_by = "writer-ghost"
        item.claimed_at = datetime.now(timezone.utc) - timedelta(minutes=60)
        item.claim_stage = "writing"
        db.commit()

        from app.services.agents.morgan import generate_health_report
        report = generate_health_report(db)

        self.assertEqual(report["health_status"], "unhealthy")
        self.assertGreaterEqual(report["stale_claims"], 1)
        db.close()

    def test_degraded_with_stuck_items(self):
        db = _fresh_db()
        item = _make_item(db, status=PipelineStatus.todo)
        item.updated_at = datetime.now(timezone.utc) - timedelta(hours=5)
        db.commit()

        from app.services.agents.morgan import generate_health_report
        report = generate_health_report(db)

        self.assertEqual(report["health_status"], "degraded")
        self.assertGreaterEqual(report["stuck_items"], 1)
        db.close()


# ── Test: Full Morgan Run ─────────────────────────────────────────────────────

class TestFullMorganRun(unittest.TestCase):
    """run_morgan() should execute all three phases and return a summary."""

    def test_full_run_no_issues(self):
        db = _fresh_db()
        _make_item(db, status=PipelineStatus.done)

        from app.services.agents.morgan import run_morgan
        result = run_morgan(db)

        self.assertEqual(result["stale_claims_recovered"], 0)
        self.assertEqual(result["errored_items_reset"], 0)
        self.assertEqual(result["health"]["health_status"], "healthy")
        self.assertIn("recoveries", result)
        self.assertIn("resets", result)
        db.close()

    def test_full_run_with_stale_claim_and_error(self):
        db = _fresh_db()
        # Stale claim
        stale = _make_item(db, status=PipelineStatus.writing)
        stale.claimed_by = "writer-ghost"
        stale.claimed_at = datetime.now(timezone.utc) - timedelta(minutes=60)
        stale.claim_stage = "writing"
        db.commit()

        # Errored item
        errored = _make_item(db, status=PipelineStatus.review)
        errored.last_error = "Editor crashed"
        errored.updated_at = datetime.now(timezone.utc) - timedelta(minutes=120)
        db.commit()

        from app.services.agents.morgan import run_morgan
        result = run_morgan(db)

        self.assertEqual(result["stale_claims_recovered"], 1)
        self.assertEqual(result["errored_items_reset"], 1)
        db.close()


# ── Test: Pipeline Health Route ───────────────────────────────────────────────

class TestPipelineHealthRoute(unittest.TestCase):
    """GET /pipeline/health should return a health report."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def test_returns_health_report(self):
        resp = self.client.get("/pipeline/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("health_status", data)
        self.assertIn("overview", data)
        self.assertIn("stale_claims", data)
        self.assertIn("errored_items", data)
        self.assertIn("stuck_items", data)


# ── Test: Morgan Trigger Route ────────────────────────────────────────────────

class TestMorganTriggerRoute(unittest.TestCase):
    """POST /pipeline/run/morgan should trigger Morgan PM."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def test_trigger_morgan(self):
        resp = self.client.post("/pipeline/run/morgan")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["agent"], "morgan")
        self.assertIn("stale_claims_recovered", data)
        self.assertIn("errored_items_reset", data)
        self.assertIn("health", data)


# ── Test: Worker Task Registry ────────────────────────────────────────────────

class TestWorkerMorganTask(unittest.TestCase):
    """Morgan task should be registered in TASK_REGISTRY."""

    def test_morgan_in_registry(self):
        from app.worker import TASK_REGISTRY
        self.assertIn("v6_run_morgan", TASK_REGISTRY)

    def test_morgan_callable(self):
        from app.worker import TASK_REGISTRY
        self.assertTrue(callable(TASK_REGISTRY["v6_run_morgan"]))

    def test_total_tasks_is_12(self):
        from app.worker import TASK_REGISTRY
        self.assertEqual(len(TASK_REGISTRY), 12)


if __name__ == "__main__":
    unittest.main()
