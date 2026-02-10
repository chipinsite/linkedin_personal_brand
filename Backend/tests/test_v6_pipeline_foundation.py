"""V6 Pipeline Foundation Tests.

Covers:
- Pipeline item creation and model integrity
- Status transition validation (valid and invalid paths)
- Atomic claim lock lifecycle (attempt, verify, release)
- Concurrent claim attempt (second claimer fails)
- Stale claim detection and force release
- Revision increment and max revision check
- Pipeline overview counts
- Unclaimed item queries
- db_check includes new table
"""

import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v6_pipeline_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

from app.db import SessionLocal, engine
from app.main import app
from app.models import ContentPipelineItem, PipelineStatus, SocialStatus
from app.services.claim_lock import (
    attempt_claim,
    find_stale_claims,
    force_release_claim,
    release_claim,
    verify_claim,
)
from app.services.pipeline import (
    ALLOWED_TRANSITIONS,
    TransitionError,
    create_pipeline_item,
    get_items_by_status,
    get_pipeline_overview,
    get_unclaimed_items_by_status,
    has_exceeded_max_revisions,
    increment_revision,
    is_valid_transition,
    transition,
)
from app.services.db_check import REQUIRED_TABLES


class TestPipelineItemCreation(unittest.TestCase):
    """Test creating pipeline items and model field defaults."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_create_item_defaults(self):
        item = create_pipeline_item(
            self.db,
            pillar_theme="Adtech fundamentals",
            sub_theme="Programmatic buying",
            topic_keyword="real-time bidding",
        )
        self.assertIsNotNone(item.id)
        self.assertEqual(item.status, PipelineStatus.backlog)
        self.assertEqual(item.revision_count, 0)
        self.assertEqual(item.max_revisions, 3)
        self.assertIsNone(item.claimed_by)
        self.assertIsNone(item.draft_id)
        self.assertIsNone(item.quality_score)
        self.assertIsNone(item.social_status)
        self.assertEqual(item.pillar_theme, "Adtech fundamentals")
        self.assertEqual(item.sub_theme, "Programmatic buying")
        self.assertEqual(item.topic_keyword, "real-time bidding")

    def test_create_item_with_explicit_status(self):
        item = create_pipeline_item(
            self.db,
            pillar_theme="AI in advertising",
            status=PipelineStatus.todo,
        )
        self.assertEqual(item.status, PipelineStatus.todo)


class TestStatusTransitions(unittest.TestCase):
    """Test pipeline status transition validation and execution."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_valid_transition_backlog_to_todo(self):
        self.assertTrue(is_valid_transition(PipelineStatus.backlog, PipelineStatus.todo))

    def test_valid_transition_todo_to_writing(self):
        self.assertTrue(is_valid_transition(PipelineStatus.todo, PipelineStatus.writing))

    def test_valid_transition_review_to_ready(self):
        self.assertTrue(is_valid_transition(PipelineStatus.review, PipelineStatus.ready_to_publish))

    def test_valid_transition_review_to_todo_revision(self):
        self.assertTrue(is_valid_transition(PipelineStatus.review, PipelineStatus.todo))

    def test_valid_transition_full_happy_path(self):
        """Validate the full happy path: BACKLOG → TODO → WRITING → REVIEW → READY → PUBLISHED → AMPLIFIED → DONE."""
        path = [
            PipelineStatus.backlog,
            PipelineStatus.todo,
            PipelineStatus.writing,
            PipelineStatus.review,
            PipelineStatus.ready_to_publish,
            PipelineStatus.published,
            PipelineStatus.amplified,
            PipelineStatus.done,
        ]
        for i in range(len(path) - 1):
            self.assertTrue(
                is_valid_transition(path[i], path[i + 1]),
                f"Transition {path[i].name} → {path[i + 1].name} should be valid",
            )

    def test_invalid_transition_backlog_to_published(self):
        self.assertFalse(is_valid_transition(PipelineStatus.backlog, PipelineStatus.published))

    def test_invalid_transition_done_to_anything(self):
        for ps in PipelineStatus:
            if ps != PipelineStatus.done:
                self.assertFalse(
                    is_valid_transition(PipelineStatus.done, ps),
                    f"DONE → {ps.name} should be invalid",
                )

    def test_transition_execution_happy_path(self):
        item = create_pipeline_item(self.db, pillar_theme="Test")
        updated = transition(self.db, item.id, PipelineStatus.backlog, PipelineStatus.todo)
        self.assertEqual(updated.status, PipelineStatus.todo)

    def test_transition_execution_invalid_raises(self):
        item = create_pipeline_item(self.db, pillar_theme="Test")
        with self.assertRaises(TransitionError):
            transition(self.db, item.id, PipelineStatus.backlog, PipelineStatus.published)

    def test_transition_concurrent_modification_raises(self):
        """Transition fails if item status doesn't match expected from_status."""
        item = create_pipeline_item(self.db, pillar_theme="Test")
        # Item is at BACKLOG, but we try from TODO
        with self.assertRaises(TransitionError) as ctx:
            transition(self.db, item.id, PipelineStatus.todo, PipelineStatus.writing)
        self.assertIn("Concurrent modification", str(ctx.exception))

    def test_transition_nonexistent_item_raises(self):
        fake_id = uuid.uuid4()
        with self.assertRaises(ValueError):
            transition(self.db, fake_id, PipelineStatus.backlog, PipelineStatus.todo)


class TestClaimLock(unittest.TestCase):
    """Test atomic claim lock lifecycle."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_claim_lifecycle(self):
        item = create_pipeline_item(self.db, pillar_theme="Claim test")

        # Attempt claim
        result = attempt_claim(self.db, item.id, "writing", "worker-1")
        self.assertTrue(result)

        # Verify claim
        verified = verify_claim(self.db, item.id, "writing", "worker-1")
        self.assertTrue(verified)

        # Release claim
        released = release_claim(self.db, item.id, "writing")
        self.assertTrue(released)

        # Verify after release fails
        verified_after = verify_claim(self.db, item.id, "writing", "worker-1")
        self.assertFalse(verified_after)

    def test_concurrent_claim_fails(self):
        item = create_pipeline_item(self.db, pillar_theme="Concurrent test")

        # Worker 1 claims
        result1 = attempt_claim(self.db, item.id, "writing", "worker-1")
        self.assertTrue(result1)

        # Worker 2 tries to claim same item — should fail
        result2 = attempt_claim(self.db, item.id, "writing", "worker-2")
        self.assertFalse(result2)

        # Worker 1 still holds claim
        self.assertTrue(verify_claim(self.db, item.id, "writing", "worker-1"))

        # Cleanup
        release_claim(self.db, item.id, "writing")

    def test_verify_wrong_worker_fails(self):
        item = create_pipeline_item(self.db, pillar_theme="Verify test")
        attempt_claim(self.db, item.id, "review", "worker-A")

        # Different worker fails verification
        self.assertFalse(verify_claim(self.db, item.id, "review", "worker-B"))

        # Cleanup
        release_claim(self.db, item.id, "review")

    def test_stale_claim_detection(self):
        item = create_pipeline_item(self.db, pillar_theme="Stale test")
        attempt_claim(self.db, item.id, "writing", "worker-old")

        # Manually backdate the claim
        db_item = self.db.query(ContentPipelineItem).filter(ContentPipelineItem.id == item.id).first()
        db_item.claimed_at = datetime.now(timezone.utc) - timedelta(minutes=60)
        self.db.commit()

        stale = find_stale_claims(self.db, max_age_minutes=30)
        stale_ids = [s.id for s in stale]
        self.assertIn(item.id, stale_ids)

        # Force release
        force_released = force_release_claim(self.db, item.id)
        self.assertTrue(force_released)

        # No longer stale
        stale_after = find_stale_claims(self.db, max_age_minutes=30)
        stale_ids_after = [s.id for s in stale_after]
        self.assertNotIn(item.id, stale_ids_after)


class TestRevisionTracking(unittest.TestCase):
    """Test revision increment and max revision check."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_increment_revision(self):
        item = create_pipeline_item(self.db, pillar_theme="Revision test")
        self.assertEqual(item.revision_count, 0)

        updated = increment_revision(self.db, item.id, "Editor: readability too low")
        self.assertEqual(updated.revision_count, 1)
        self.assertEqual(updated.last_error, "Editor: readability too low")

    def test_max_revision_check(self):
        item = create_pipeline_item(self.db, pillar_theme="Max rev test")
        self.assertFalse(has_exceeded_max_revisions(item))

        for i in range(3):
            item = increment_revision(self.db, item.id, f"Failure {i+1}")

        self.assertTrue(has_exceeded_max_revisions(item))


class TestPipelineQueries(unittest.TestCase):
    """Test pipeline query helpers."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_overview_counts(self):
        overview = get_pipeline_overview(self.db)
        self.assertIn("status_counts", overview)
        self.assertIn("total", overview)
        self.assertIn("claimed", overview)
        # Should have a count for every status
        for ps in PipelineStatus:
            self.assertIn(ps.name, overview["status_counts"])

    def test_get_items_by_status(self):
        item = create_pipeline_item(self.db, pillar_theme="Query test")
        items = get_items_by_status(self.db, PipelineStatus.backlog)
        ids = [i.id for i in items]
        self.assertIn(item.id, ids)

    def test_get_unclaimed_items(self):
        item = create_pipeline_item(self.db, pillar_theme="Unclaimed test")
        unclaimed = get_unclaimed_items_by_status(self.db, PipelineStatus.backlog)
        ids = [i.id for i in unclaimed]
        self.assertIn(item.id, ids)

        # Claim it
        attempt_claim(self.db, item.id, "writing", "worker-x")
        unclaimed_after = get_unclaimed_items_by_status(self.db, PipelineStatus.backlog)
        ids_after = [i.id for i in unclaimed_after]
        self.assertNotIn(item.id, ids_after)

        # Cleanup
        release_claim(self.db, item.id, "writing")


class TestDbCheckInclusion(unittest.TestCase):
    """Verify content_pipeline_items is in the required tables set."""

    def test_required_tables_includes_pipeline(self):
        self.assertIn("content_pipeline_items", REQUIRED_TABLES)


if __name__ == "__main__":
    unittest.main()
