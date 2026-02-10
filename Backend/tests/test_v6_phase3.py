"""V6 Phase 3 Tests.

Covers:
- Publisher agent (READY_TO_PUBLISH → PUBLISHED with webhook + Telegram + PublishedPost)
- Promoter agent (PUBLISHED → AMPLIFIED → DONE with engagement prompt)
- Pipeline API routes (overview, listing, filtering, detail, transition, agent triggers)
- Worker task registry and Celery configuration
"""

import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v6_phase3_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ["LLM_MOCK_MODE"] = "true"

from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import (
    ContentPipelineItem,
    Draft,
    DraftStatus,
    PipelineStatus,
    PostFormat,
    PostTone,
    PublishedPost,
    SocialStatus,
)

# Ensure all tables exist in test DB
Base.metadata.create_all(engine)

from app.services.claim_lock import attempt_claim, release_claim
from app.services.pipeline import (
    create_pipeline_item,
    get_items_by_status,
    transition,
)


def _create_draft(db, content="Test draft content about AI in advertising and programmatic buying."):
    """Helper: create a test draft."""
    draft = Draft(
        pillar_theme="Adtech fundamentals",
        sub_theme="Programmatic buying",
        format=PostFormat.text,
        tone=PostTone.educational,
        content_body=content,
        status=DraftStatus.approved,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def _create_pipeline_item_at_status(db, status, draft=None):
    """Helper: create a pipeline item at a specific status with optional linked draft."""
    item = ContentPipelineItem(
        status=status,
        pillar_theme="Adtech fundamentals",
        sub_theme="Programmatic buying",
        topic_keyword="AI in advertising test",
        draft_id=draft.id if draft else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Publisher Agent
# ─────────────────────────────────────────────────────────────────────────────


class TestPublisherAgent(unittest.TestCase):
    """Test Publisher agent behavior."""

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        # Clean up test data
        self.db.query(PublishedPost).delete()
        self.db.query(ContentPipelineItem).delete()
        self.db.query(Draft).delete()
        self.db.commit()
        self.db.close()

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_publisher_creates_published_post(self, mock_telegram, mock_webhook):
        """Publisher should create a PublishedPost record linked to the draft."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish, draft=draft
        )

        from app.services.agents.publisher import process_one_item

        # Claim first
        attempt_claim(self.db, item.id, "publish", "test-pub-001")

        result = process_one_item(self.db, item, "test-pub-001")
        self.assertTrue(result)

        # Verify PublishedPost was created
        posts = self.db.query(PublishedPost).filter_by(draft_id=draft.id).all()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].content_body, draft.content_body)
        self.assertIsNotNone(posts[0].scheduled_time)

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_publisher_fires_webhook(self, mock_telegram, mock_webhook):
        """Publisher should fire post.publish_ready webhook."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish, draft=draft
        )

        from app.services.agents.publisher import process_one_item

        attempt_claim(self.db, item.id, "publish", "test-pub-002")
        process_one_item(self.db, item, "test-pub-002")

        mock_webhook.assert_called_once()
        call_kwargs = mock_webhook.call_args
        self.assertEqual(call_kwargs.kwargs.get("event") or call_kwargs[1].get("event", call_kwargs[0][1] if len(call_kwargs[0]) > 1 else None), "post.publish_ready")

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_publisher_sends_telegram(self, mock_telegram, mock_webhook):
        """Publisher should send Telegram manual-publish reminder."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish, draft=draft
        )

        from app.services.agents.publisher import process_one_item

        attempt_claim(self.db, item.id, "publish", "test-pub-003")
        process_one_item(self.db, item, "test-pub-003")

        mock_telegram.assert_called_once()
        call_kwargs = mock_telegram.call_args
        # Check event_type in kwargs
        event_type = call_kwargs.kwargs.get("event_type", "")
        self.assertEqual(event_type, "V6_PUBLISH_READY")

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_publisher_transitions_to_published(self, mock_telegram, mock_webhook):
        """Publisher should transition item to PUBLISHED status."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish, draft=draft
        )

        from app.services.agents.publisher import process_one_item

        attempt_claim(self.db, item.id, "publish", "test-pub-004")
        process_one_item(self.db, item, "test-pub-004")

        self.db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.published)

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_publisher_skips_no_draft(self, mock_telegram, mock_webhook):
        """Publisher should skip items without a draft_id."""
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish
        )

        from app.services.agents.publisher import process_one_item

        attempt_claim(self.db, item.id, "publish", "test-pub-005")
        result = process_one_item(self.db, item, "test-pub-005")

        self.assertFalse(result)
        mock_webhook.assert_not_called()

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_run_publisher_batch(self, mock_telegram, mock_webhook):
        """run_publisher should process multiple READY_TO_PUBLISH items."""
        draft1 = _create_draft(self.db, "First draft about AI advertising.")
        draft2 = _create_draft(self.db, "Second draft about programmatic buying.")
        _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish, draft=draft1
        )
        _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish, draft=draft2
        )

        from app.services.agents.publisher import run_publisher

        count = run_publisher(self.db, max_items=5)
        self.assertEqual(count, 2)

    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_run_publisher_no_items(self, mock_telegram, mock_webhook):
        """run_publisher should return 0 when no items available."""
        from app.services.agents.publisher import run_publisher

        count = run_publisher(self.db)
        self.assertEqual(count, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Promoter Agent
# ─────────────────────────────────────────────────────────────────────────────


class TestPromoterAgent(unittest.TestCase):
    """Test Promoter agent behavior."""

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.query(ContentPipelineItem).delete()
        self.db.query(Draft).delete()
        self.db.commit()
        self.db.close()

    @patch("app.services.agents.promoter.send_telegram_message")
    def test_promoter_sends_engagement_prompt(self, mock_telegram):
        """Promoter should send Telegram engagement reminder."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.published, draft=draft
        )

        from app.services.agents.promoter import process_one_item

        attempt_claim(self.db, item.id, "promote", "test-promo-001")
        result = process_one_item(self.db, item, "test-promo-001")

        self.assertTrue(result)
        mock_telegram.assert_called_once()
        call_kwargs = mock_telegram.call_args
        self.assertEqual(call_kwargs.kwargs.get("event_type", ""), "V6_ENGAGEMENT_PROMPT")

    @patch("app.services.agents.promoter.send_telegram_message")
    def test_promoter_transitions_to_done(self, mock_telegram):
        """Promoter should transition PUBLISHED → AMPLIFIED → DONE."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.published, draft=draft
        )

        from app.services.agents.promoter import process_one_item

        attempt_claim(self.db, item.id, "promote", "test-promo-002")
        process_one_item(self.db, item, "test-promo-002")

        self.db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.done)

    @patch("app.services.agents.promoter.send_telegram_message")
    def test_promoter_sets_social_status(self, mock_telegram):
        """Promoter should set social_status to MONITORING_COMPLETE."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.published, draft=draft
        )

        from app.services.agents.promoter import process_one_item

        attempt_claim(self.db, item.id, "promote", "test-promo-003")
        process_one_item(self.db, item, "test-promo-003")

        self.db.refresh(item)
        self.assertEqual(item.social_status, SocialStatus.monitoring_complete)

    @patch("app.services.agents.promoter.send_telegram_message")
    def test_run_promoter_batch(self, mock_telegram):
        """run_promoter should process multiple PUBLISHED items."""
        for i in range(3):
            draft = _create_draft(self.db, f"Draft {i} about AI in advertising.")
            _create_pipeline_item_at_status(
                self.db, PipelineStatus.published, draft=draft
            )

        from app.services.agents.promoter import run_promoter

        count = run_promoter(self.db, max_items=5)
        self.assertEqual(count, 3)

    @patch("app.services.agents.promoter.send_telegram_message")
    def test_run_promoter_no_items(self, mock_telegram):
        """run_promoter should return 0 when no items available."""
        from app.services.agents.promoter import run_promoter

        count = run_promoter(self.db)
        self.assertEqual(count, 0)

    @patch("app.services.agents.promoter.send_telegram_message")
    def test_promoter_handles_no_draft(self, mock_telegram):
        """Promoter should handle items without a draft gracefully."""
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.published
        )

        from app.services.agents.promoter import process_one_item

        attempt_claim(self.db, item.id, "promote", "test-promo-004")
        result = process_one_item(self.db, item, "test-promo-004")

        # Should still succeed — draft content is optional for engagement prompt
        self.assertTrue(result)
        self.db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.done)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Pipeline API Routes
# ─────────────────────────────────────────────────────────────────────────────


class TestPipelineOverviewEndpoint(unittest.TestCase):
    """Test GET /pipeline/overview endpoint."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_overview_returns_status_counts(self):
        """Pipeline overview should return status_counts, total, and claimed."""
        resp = self.client.get("/pipeline/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status_counts", data)
        self.assertIn("total", data)
        self.assertIn("claimed", data)

    def test_overview_has_all_statuses(self):
        """Pipeline overview should include all pipeline statuses."""
        resp = self.client.get("/pipeline/overview")
        data = resp.json()
        expected_statuses = [
            "backlog", "todo", "writing", "review",
            "ready_to_publish", "published", "amplified", "done",
        ]
        for status in expected_statuses:
            self.assertIn(status, data["status_counts"])


class TestPipelineItemsEndpoint(unittest.TestCase):
    """Test GET /pipeline/items endpoint."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_list_items_returns_list(self):
        """Items endpoint should return a list."""
        resp = self.client.get("/pipeline/items")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_list_items_with_status_filter(self):
        """Items endpoint should accept status filter."""
        resp = self.client.get("/pipeline/items?status=BACKLOG")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_list_items_invalid_status(self):
        """Items endpoint should reject invalid status."""
        resp = self.client.get("/pipeline/items?status=INVALID")
        self.assertEqual(resp.status_code, 400)

    def test_item_serialization(self):
        """Pipeline items should have expected fields."""
        db = SessionLocal()
        try:
            item = create_pipeline_item(
                db, pillar_theme="test", sub_theme="test", topic_keyword="serialization test"
            )
            resp = self.client.get(f"/pipeline/items/{item.id}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("id", data)
            self.assertIn("status", data)
            self.assertIn("pillar_theme", data)
            self.assertIn("revision_count", data)
            self.assertIn("quality_score", data)
        finally:
            db.query(ContentPipelineItem).delete()
            db.commit()
            db.close()


class TestPipelineItemDetailEndpoint(unittest.TestCase):
    """Test GET /pipeline/items/{id} endpoint."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_nonexistent_item(self):
        """Should return 404 for nonexistent item."""
        fake_id = uuid.uuid4()
        resp = self.client.get(f"/pipeline/items/{fake_id}")
        self.assertEqual(resp.status_code, 404)

    def test_get_existing_item(self):
        """Should return item details for existing item."""
        db = SessionLocal()
        try:
            item = create_pipeline_item(
                db, pillar_theme="detail test", topic_keyword="detail endpoint"
            )
            resp = self.client.get(f"/pipeline/items/{item.id}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["pillar_theme"], "detail test")
            self.assertEqual(data["status"], "BACKLOG")
        finally:
            db.query(ContentPipelineItem).delete()
            db.commit()
            db.close()


class TestPipelineTransitionEndpoint(unittest.TestCase):
    """Test POST /pipeline/items/{id}/transition endpoint."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_valid_transition(self):
        """Should allow valid transition BACKLOG → TODO."""
        db = SessionLocal()
        try:
            item = create_pipeline_item(db, pillar_theme="transition test")
            resp = self.client.post(
                f"/pipeline/items/{item.id}/transition",
                json={"to_status": "TODO"},
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "TODO")
        finally:
            db.query(ContentPipelineItem).delete()
            db.commit()
            db.close()

    def test_invalid_transition(self):
        """Should reject invalid transition BACKLOG → PUBLISHED."""
        db = SessionLocal()
        try:
            item = create_pipeline_item(db, pillar_theme="invalid transition test")
            resp = self.client.post(
                f"/pipeline/items/{item.id}/transition",
                json={"to_status": "PUBLISHED"},
            )
            self.assertEqual(resp.status_code, 422)
        finally:
            db.query(ContentPipelineItem).delete()
            db.commit()
            db.close()

    def test_transition_nonexistent_item(self):
        """Should return 404 for nonexistent item."""
        fake_id = uuid.uuid4()
        resp = self.client.post(
            f"/pipeline/items/{fake_id}/transition",
            json={"to_status": "TODO"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_transition_invalid_status_name(self):
        """Should return 400 for invalid target status name."""
        db = SessionLocal()
        try:
            item = create_pipeline_item(db, pillar_theme="bad status test")
            resp = self.client.post(
                f"/pipeline/items/{item.id}/transition",
                json={"to_status": "NONEXISTENT"},
            )
            self.assertEqual(resp.status_code, 400)
        finally:
            db.query(ContentPipelineItem).delete()
            db.commit()
            db.close()


class TestPipelineAgentTriggerEndpoints(unittest.TestCase):
    """Test POST /pipeline/run/{agent} endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @patch("app.services.agents.scout.run_scout", return_value=[])
    def test_trigger_scout(self, mock_scout):
        """Should trigger Scout agent."""
        resp = self.client.post("/pipeline/run/scout")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["agent"], "scout")
        self.assertIn("items_created", data)

    @patch("app.services.agents.writer.run_writer", return_value=0)
    def test_trigger_writer(self, mock_writer):
        """Should trigger Writer agent."""
        resp = self.client.post("/pipeline/run/writer")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["agent"], "writer")
        self.assertIn("items_written", data)

    @patch("app.services.agents.editor.run_editor", return_value=0)
    def test_trigger_editor(self, mock_editor):
        """Should trigger Editor agent."""
        resp = self.client.post("/pipeline/run/editor")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["agent"], "editor")
        self.assertIn("items_passed", data)

    @patch("app.services.agents.publisher.run_publisher", return_value=0)
    def test_trigger_publisher(self, mock_publisher):
        """Should trigger Publisher agent."""
        resp = self.client.post("/pipeline/run/publisher")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["agent"], "publisher")
        self.assertIn("items_published", data)

    @patch("app.services.agents.promoter.run_promoter", return_value=0)
    def test_trigger_promoter(self, mock_promoter):
        """Should trigger Promoter agent."""
        resp = self.client.post("/pipeline/run/promoter")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["agent"], "promoter")
        self.assertIn("items_promoted", data)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Full Pipeline Flow (End-to-End)
# ─────────────────────────────────────────────────────────────────────────────


class TestFullPipelineFlow(unittest.TestCase):
    """Test a complete item flowing through Publisher → Promoter."""

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.query(PublishedPost).delete()
        self.db.query(ContentPipelineItem).delete()
        self.db.query(Draft).delete()
        self.db.commit()
        self.db.close()

    @patch("app.services.agents.promoter.send_telegram_message")
    @patch("app.services.agents.publisher.send_webhook")
    @patch("app.services.agents.publisher.send_telegram_message")
    def test_ready_to_publish_to_done(self, mock_pub_tg, mock_webhook, mock_promo_tg):
        """Item should flow READY_TO_PUBLISH → PUBLISHED → AMPLIFIED → DONE."""
        draft = _create_draft(self.db)
        item = _create_pipeline_item_at_status(
            self.db, PipelineStatus.ready_to_publish, draft=draft
        )

        # Publisher phase
        from app.services.agents.publisher import run_publisher

        pub_count = run_publisher(self.db, max_items=1)
        self.assertEqual(pub_count, 1)

        self.db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.published)

        # Promoter phase
        from app.services.agents.promoter import run_promoter

        promo_count = run_promoter(self.db, max_items=1)
        self.assertEqual(promo_count, 1)

        self.db.refresh(item)
        self.assertEqual(item.status, PipelineStatus.done)
        self.assertEqual(item.social_status, SocialStatus.monitoring_complete)

        # Verify PublishedPost was created
        posts = self.db.query(PublishedPost).filter_by(draft_id=draft.id).all()
        self.assertEqual(len(posts), 1)


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Worker Task Registry
# ─────────────────────────────────────────────────────────────────────────────


class TestWorkerTaskRegistry(unittest.TestCase):
    """Test worker task definitions and registry."""

    def test_task_registry_exists(self):
        """Worker should export a TASK_REGISTRY dict."""
        from app.worker import TASK_REGISTRY
        self.assertIsInstance(TASK_REGISTRY, dict)

    def test_task_registry_has_legacy_tasks(self):
        """TASK_REGISTRY should include legacy workflow tasks."""
        from app.worker import TASK_REGISTRY
        expected = [
            "create_system_draft",
            "publish_due",
            "poll_comments",
            "ingest_research",
            "recompute_learning",
            "send_daily_summary",
        ]
        for task_name in expected:
            self.assertIn(task_name, TASK_REGISTRY, f"Missing task: {task_name}")

    def test_task_registry_has_v6_tasks(self):
        """TASK_REGISTRY should include V6 pipeline agent tasks."""
        from app.worker import TASK_REGISTRY
        expected = [
            "v6_run_scout",
            "v6_run_writer",
            "v6_run_editor",
            "v6_run_publisher",
            "v6_run_promoter",
        ]
        for task_name in expected:
            self.assertIn(task_name, TASK_REGISTRY, f"Missing V6 task: {task_name}")

    def test_task_functions_are_callable(self):
        """All registered task functions should be callable."""
        from app.worker import TASK_REGISTRY
        for name, func in TASK_REGISTRY.items():
            self.assertTrue(callable(func), f"Task {name} is not callable")

    def test_total_task_count(self):
        """TASK_REGISTRY should have 12 tasks (6 legacy + 6 V6)."""
        from app.worker import TASK_REGISTRY
        self.assertEqual(len(TASK_REGISTRY), 12)


if __name__ == "__main__":
    unittest.main()
