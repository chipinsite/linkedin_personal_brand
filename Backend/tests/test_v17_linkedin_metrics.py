"""Tests for v5.2 LinkedIn Read Integration - Metrics Fetching.

Validates:
- Post metrics dataclass and parsing
- Mock metrics loading
- Metrics fetching function
- Engagement service metrics polling
- Engagement routes metrics endpoint
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v17_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["TELEGRAM_CHAT_ID"] = "12345"
os.environ["LLM_MOCK_MODE"] = "true"

from fastapi.testclient import TestClient

from app.db import SessionLocal, engine
from app.main import app
from app.models import Draft, DraftStatus, PostFormat, PostTone, PublishedPost


class LinkedInPostMetricsTest(unittest.TestCase):
    """Tests for LinkedInPostMetrics dataclass."""

    def test_metrics_dataclass_defaults(self):
        from app.services.linkedin import LinkedInPostMetrics

        metrics = LinkedInPostMetrics()
        self.assertEqual(metrics.impressions, 0)
        self.assertEqual(metrics.reactions, 0)
        self.assertEqual(metrics.comments_count, 0)
        self.assertEqual(metrics.shares, 0)
        self.assertEqual(metrics.engagement_rate, 0.0)

    def test_metrics_engagement_rate_calculation(self):
        from app.services.linkedin import LinkedInPostMetrics

        metrics = LinkedInPostMetrics(
            impressions=1000,
            reactions=50,
            comments_count=10,
            shares=5,
        )
        # (50 + 10 + 5) / 1000 * 100 = 6.5%
        self.assertEqual(metrics.engagement_rate, 6.5)

    def test_metrics_zero_impressions_no_divide_error(self):
        from app.services.linkedin import LinkedInPostMetrics

        metrics = LinkedInPostMetrics(
            impressions=0,
            reactions=10,
            comments_count=5,
            shares=2,
        )
        self.assertEqual(metrics.engagement_rate, 0.0)


class MetricsParsingTest(unittest.TestCase):
    """Tests for metrics response parsing."""

    def test_parse_direct_fields(self):
        from app.services.linkedin import _parse_metrics_response

        payload = {
            "impressions": 5000,
            "reactions": 100,
            "comments": 25,
            "shares": 10,
        }
        metrics = _parse_metrics_response(payload)
        self.assertEqual(metrics.impressions, 5000)
        self.assertEqual(metrics.reactions, 100)
        self.assertEqual(metrics.comments_count, 25)
        self.assertEqual(metrics.shares, 10)

    def test_parse_alternative_field_names(self):
        from app.services.linkedin import _parse_metrics_response

        payload = {
            "views": 3000,
            "likes": 75,
            "numComments": 15,
            "reposts": 8,
        }
        metrics = _parse_metrics_response(payload)
        self.assertEqual(metrics.impressions, 3000)
        self.assertEqual(metrics.reactions, 75)
        self.assertEqual(metrics.comments_count, 15)
        self.assertEqual(metrics.shares, 8)

    def test_parse_elements_structure(self):
        from app.services.linkedin import _parse_metrics_response

        payload = {
            "elements": [
                {
                    "impressionCount": 10000,
                    "likeCount": 200,
                    "commentCount": 50,
                    "shareCount": 20,
                }
            ]
        }
        metrics = _parse_metrics_response(payload)
        self.assertEqual(metrics.impressions, 10000)
        self.assertEqual(metrics.reactions, 200)
        self.assertEqual(metrics.comments_count, 50)
        self.assertEqual(metrics.shares, 20)

    def test_parse_statistics_block(self):
        from app.services.linkedin import _parse_metrics_response

        payload = {
            "statistics": {
                "impressions": 7500,
                "reactions": 150,
                "comments": 35,
                "shares": 12,
            }
        }
        metrics = _parse_metrics_response(payload)
        self.assertEqual(metrics.impressions, 7500)
        self.assertEqual(metrics.reactions, 150)
        self.assertEqual(metrics.comments_count, 35)
        self.assertEqual(metrics.shares, 12)

    def test_parse_empty_payload(self):
        from app.services.linkedin import _parse_metrics_response

        payload = {}
        metrics = _parse_metrics_response(payload)
        self.assertEqual(metrics.impressions, 0)
        self.assertEqual(metrics.reactions, 0)


class MockMetricsTest(unittest.TestCase):
    """Tests for mock metrics support."""

    def test_mock_metrics_loading(self):
        from app.services.linkedin import _mock_metrics_for_post

        mock_data = json.dumps({
            "post123": {
                "impressions": 2500,
                "reactions": 60,
                "comments": 15,
                "shares": 5,
            }
        })

        import app.services.linkedin as linkedin_module
        original_setting = linkedin_module.settings.linkedin_mock_metrics_json
        linkedin_module.settings.linkedin_mock_metrics_json = mock_data

        try:
            metrics = _mock_metrics_for_post("post123")
            self.assertIsNotNone(metrics)
            self.assertEqual(metrics.impressions, 2500)
            self.assertEqual(metrics.reactions, 60)
        finally:
            linkedin_module.settings.linkedin_mock_metrics_json = original_setting

    def test_mock_metrics_missing_post(self):
        from app.services.linkedin import _mock_metrics_for_post

        mock_data = json.dumps({
            "post123": {"impressions": 1000}
        })

        import app.services.linkedin as linkedin_module
        original_setting = linkedin_module.settings.linkedin_mock_metrics_json
        linkedin_module.settings.linkedin_mock_metrics_json = mock_data

        try:
            metrics = _mock_metrics_for_post("nonexistent")
            self.assertIsNone(metrics)
        finally:
            linkedin_module.settings.linkedin_mock_metrics_json = original_setting


class FetchPostMetricsTest(unittest.TestCase):
    """Tests for fetch_post_metrics function."""

    def test_fetch_returns_empty_when_not_configured(self):
        from app.services.linkedin import fetch_post_metrics

        import app.services.linkedin as linkedin_module
        original_mode = linkedin_module.settings.linkedin_api_mode
        original_token = linkedin_module.settings.linkedin_api_token
        original_mock = linkedin_module.settings.linkedin_mock_metrics_json

        linkedin_module.settings.linkedin_api_mode = "manual"
        linkedin_module.settings.linkedin_api_token = None
        linkedin_module.settings.linkedin_mock_metrics_json = ""

        try:
            metrics = fetch_post_metrics("test_post_id")
            self.assertEqual(metrics.impressions, 0)
            self.assertEqual(metrics.reactions, 0)
        finally:
            linkedin_module.settings.linkedin_api_mode = original_mode
            linkedin_module.settings.linkedin_api_token = original_token
            linkedin_module.settings.linkedin_mock_metrics_json = original_mock

    def test_fetch_uses_mock_when_available(self):
        from app.services.linkedin import fetch_post_metrics

        mock_data = json.dumps({
            "mock_post_id": {
                "impressions": 5000,
                "reactions": 100,
                "comments": 25,
                "shares": 10,
            }
        })

        import app.services.linkedin as linkedin_module
        original_mock = linkedin_module.settings.linkedin_mock_metrics_json
        linkedin_module.settings.linkedin_mock_metrics_json = mock_data

        try:
            metrics = fetch_post_metrics("mock_post_id")
            self.assertEqual(metrics.impressions, 5000)
            self.assertEqual(metrics.reactions, 100)
        finally:
            linkedin_module.settings.linkedin_mock_metrics_json = original_mock


class EngagementServiceMetricsTest(unittest.TestCase):
    """Tests for engagement service metrics polling."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    def test_poll_metrics_returns_not_configured_when_disabled(self):
        from app.services.engagement import poll_and_store_metrics

        import app.services.linkedin as linkedin_module
        original_mode = linkedin_module.settings.linkedin_api_mode
        original_mock = linkedin_module.settings.linkedin_mock_metrics_json

        linkedin_module.settings.linkedin_api_mode = "manual"
        linkedin_module.settings.linkedin_mock_metrics_json = ""

        try:
            result = poll_and_store_metrics(db=self.db)
            self.assertEqual(result["status"], "not_configured")
        finally:
            linkedin_module.settings.linkedin_api_mode = original_mode
            linkedin_module.settings.linkedin_mock_metrics_json = original_mock

    def test_poll_metrics_updates_posts(self):
        from app.services.engagement import poll_and_store_metrics

        # Create a draft and published post
        draft = Draft(
            pillar_theme="Test pillar",
            sub_theme="Test sub",
            format=PostFormat.text,
            tone=PostTone.direct,
            content_body="Test content for metrics",
            status=DraftStatus.approved,
            guardrail_check_passed=True,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        post = PublishedPost(
            draft_id=draft.id,
            content_body=draft.content_body,
            format=draft.format,
            tone=draft.tone,
            linkedin_post_id="test_metrics_post",
            linkedin_post_url="https://linkedin.com/posts/test",
            published_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        # Set up mock metrics
        mock_data = json.dumps({
            "test_metrics_post": {
                "impressions": 3000,
                "reactions": 80,
                "comments": 20,
                "shares": 8,
            }
        })

        import app.services.linkedin as linkedin_module
        original_mode = linkedin_module.settings.linkedin_api_mode
        original_mock = linkedin_module.settings.linkedin_mock_metrics_json

        linkedin_module.settings.linkedin_api_mode = "api"
        linkedin_module.settings.linkedin_mock_metrics_json = mock_data

        try:
            result = poll_and_store_metrics(db=self.db)
            self.assertEqual(result["status"], "ok")
            self.assertGreaterEqual(result["updated_posts"], 1)

            # Verify post was updated
            self.db.refresh(post)
            self.assertEqual(post.impressions, 3000)
            self.assertEqual(post.reactions, 80)
        finally:
            linkedin_module.settings.linkedin_api_mode = original_mode
            linkedin_module.settings.linkedin_mock_metrics_json = original_mock


class EngagementRoutesMetricsTest(unittest.TestCase):
    """Tests for engagement routes metrics endpoint."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_poll_metrics_endpoint_returns_200(self):
        response = self.client.post("/engagement/poll-metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("updated_posts", data)

    def test_poll_metrics_endpoint_creates_audit_log(self):
        from app.db import SessionLocal
        from app.models import AuditLog

        response = self.client.post("/engagement/poll-metrics")
        self.assertEqual(response.status_code, 200)

        db = SessionLocal()
        try:
            log = db.query(AuditLog).filter(
                AuditLog.action == "engagement.poll_metrics"
            ).order_by(AuditLog.created_at.desc()).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.resource_type, "post")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
