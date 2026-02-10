"""Tests for Zapier webhook integration.

Covers:
- Webhook payload format and delivery
- Retry behavior on failure
- Notification logging (channel="webhook")
- Webhook skipped when URL not configured
- Admin webhook-status endpoint
- Admin webhook-test endpoint
- Integration: webhook fires on publish-due and draft approve
"""

import json
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

# Configure env before importing app modules.
DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_webhook_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

from fastapi.testclient import TestClient

from app.db import SessionLocal, engine
from app.main import app
from app.models import NotificationLog, PublishedPost


class WebhookServiceTest(unittest.TestCase):
    """Unit tests for webhook_service.py functions."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_01_webhook_skipped_when_not_configured(self):
        """When ZAPIER_WEBHOOK_URL is not set, send_webhook returns False without error."""
        from app.services.webhook_service import send_webhook

        db = SessionLocal()
        try:
            result = send_webhook(db=db, event="test.event", data={"key": "value"})
            self.assertFalse(result)
        finally:
            db.close()

    @patch("app.services.webhook_service.settings")
    @patch("app.services.webhook_service.httpx.post")
    def test_02_webhook_sends_correct_payload(self, mock_post, mock_settings):
        """Webhook POSTs correct JSON envelope with event and data."""
        mock_settings.zapier_webhook_url = "https://hooks.zapier.com/test/123"
        mock_settings.zapier_webhook_secret = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        from app.services.webhook_service import send_webhook

        db = SessionLocal()
        try:
            result = send_webhook(
                db=db,
                event="post.publish_ready",
                data={"post_id": "abc-123", "content": "Hello LinkedIn!"},
            )
            self.assertTrue(result)
            self.assertTrue(mock_post.called)

            # Verify payload structure
            call_kwargs = mock_post.call_args
            sent_bytes = call_kwargs.kwargs.get("content") or call_kwargs[1].get("content")
            sent_payload = json.loads(sent_bytes)
            self.assertEqual(sent_payload["event"], "post.publish_ready")
            self.assertIn("timestamp", sent_payload)
            self.assertEqual(sent_payload["data"]["post_id"], "abc-123")
            self.assertEqual(sent_payload["data"]["content"], "Hello LinkedIn!")
        finally:
            db.close()

    @patch("app.services.webhook_service.settings")
    @patch("app.services.webhook_service.httpx.post")
    def test_03_webhook_retries_on_failure(self, mock_post, mock_settings):
        """Webhook retries up to MAX_RETRIES on HTTP errors."""
        mock_settings.zapier_webhook_url = "https://hooks.zapier.com/test/123"
        mock_settings.zapier_webhook_secret = None

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        from app.services.webhook_service import send_webhook

        db = SessionLocal()
        try:
            with patch("app.services.webhook_service.time.sleep"):
                result = send_webhook(
                    db=db,
                    event="test.retry",
                    data={"test": True},
                )
            self.assertFalse(result)
            # Should have tried 3 times (MAX_RETRIES)
            self.assertEqual(mock_post.call_count, 3)
        finally:
            db.close()

    @patch("app.services.webhook_service.settings")
    @patch("app.services.webhook_service.httpx.post")
    def test_04_webhook_logs_to_notification_logs(self, mock_post, mock_settings):
        """Successful and failed webhook deliveries are logged in notification_logs."""
        mock_settings.zapier_webhook_url = "https://hooks.zapier.com/test/123"
        mock_settings.zapier_webhook_secret = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        from app.services.webhook_service import send_webhook

        db = SessionLocal()
        try:
            send_webhook(db=db, event="test.log", data={"logged": True})

            log = (
                db.query(NotificationLog)
                .filter(NotificationLog.channel == "webhook")
                .filter(NotificationLog.event_type == "test.log")
                .order_by(NotificationLog.created_at.desc())
                .first()
            )
            self.assertIsNotNone(log)
            self.assertTrue(log.success)
            self.assertIn("test.log", log.payload)
        finally:
            db.close()

    @patch("app.services.webhook_service.settings")
    @patch("app.services.webhook_service.httpx.post")
    def test_05_webhook_hmac_signature(self, mock_post, mock_settings):
        """When webhook secret is set, X-Webhook-Signature header is included."""
        mock_settings.zapier_webhook_url = "https://hooks.zapier.com/test/123"
        mock_settings.zapier_webhook_secret = "my_secret_key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        from app.services.webhook_service import send_webhook

        db = SessionLocal()
        try:
            send_webhook(db=db, event="test.signed", data={"secure": True})

            call_kwargs = mock_post.call_args
            headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
            self.assertIn("X-Webhook-Signature", headers)
            self.assertTrue(len(headers["X-Webhook-Signature"]) > 0)
        finally:
            db.close()


class WebhookAdminEndpointTest(unittest.TestCase):
    """Tests for admin webhook-status and webhook-test endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_06_webhook_status_endpoint(self):
        """GET /admin/webhook-status returns expected structure."""
        resp = self.client.get("/admin/webhook-status")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("configured", body)
        self.assertIn("url_set", body)
        self.assertIn("deliveries_24h", body)
        self.assertIn("success", body["deliveries_24h"])
        self.assertIn("failed", body["deliveries_24h"])

    @patch("app.routes.admin.send_test_webhook")
    def test_07_webhook_test_endpoint(self, mock_test):
        """POST /admin/webhook-test calls send_test_webhook and returns result."""
        mock_test.return_value = {
            "success": True,
            "status_code": 200,
            "response_time_ms": 150.5,
            "error": None,
        }

        resp = self.client.post("/admin/webhook-test")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["status_code"], 200)


class WebhookIntegrationTest(unittest.TestCase):
    """Tests that webhook fires correctly during workflow events."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    @patch("app.services.workflow.send_webhook")
    def test_08_webhook_fires_on_publish_due(self, mock_webhook):
        """When publish-due runs, webhook fires with post.publish_ready event."""
        mock_webhook.return_value = True

        # Create and approve a draft
        gen = self.client.post("/drafts/generate")
        self.assertEqual(gen.status_code, 200)
        draft = gen.json()

        approve = self.client.post(f"/drafts/{draft['id']}/approve", json={})
        self.assertEqual(approve.status_code, 200)

        # Get the post and backdate its scheduled_time
        posts = self.client.get("/posts").json()
        post = next(p for p in posts if p["draft_id"] == draft["id"])

        db = SessionLocal()
        try:
            db_post = db.query(PublishedPost).filter(PublishedPost.id == uuid.UUID(post["id"])).first()
            db_post.scheduled_time = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        # Trigger publish-due
        due_resp = self.client.post("/posts/publish-due")
        self.assertEqual(due_resp.status_code, 200)

        # Verify webhook was called with correct event
        self.assertTrue(mock_webhook.called)
        call_kwargs = mock_webhook.call_args
        self.assertEqual(call_kwargs.kwargs.get("event") or call_kwargs[1].get("event", call_kwargs[0][1] if len(call_kwargs[0]) > 1 else None), "post.publish_ready")

    @patch("app.routes.drafts.send_webhook")
    def test_09_webhook_fires_on_draft_approve(self, mock_webhook):
        """When a draft is approved, webhook fires with draft.approved event."""
        mock_webhook.return_value = True

        gen = self.client.post("/drafts/generate")
        self.assertEqual(gen.status_code, 200)
        draft = gen.json()

        approve = self.client.post(f"/drafts/{draft['id']}/approve", json={})
        self.assertEqual(approve.status_code, 200)

        self.assertTrue(mock_webhook.called)
        call_args = mock_webhook.call_args
        # Check event is draft.approved (could be positional or keyword)
        event = call_args.kwargs.get("event")
        if event is None and len(call_args.args) > 1:
            event = call_args.args[1]
        self.assertEqual(event, "draft.approved")

    @patch("app.routes.posts.send_webhook")
    def test_10_webhook_fires_on_manual_publish_confirm(self, mock_webhook):
        """When manual publish is confirmed, webhook fires with post.published event."""
        mock_webhook.return_value = True

        gen = self.client.post("/drafts/generate")
        self.assertEqual(gen.status_code, 200)
        draft = gen.json()

        approve = self.client.post(f"/drafts/{draft['id']}/approve", json={})
        self.assertEqual(approve.status_code, 200)

        posts = self.client.get("/posts").json()
        post = next(p for p in posts if p["draft_id"] == draft["id"])

        confirm = self.client.post(
            f"/posts/{post['id']}/confirm-manual-publish",
            json={"linkedin_post_url": "https://linkedin.com/feed/update/webhook-test"},
        )
        self.assertEqual(confirm.status_code, 200)

        self.assertTrue(mock_webhook.called)
        call_args = mock_webhook.call_args
        event = call_args.kwargs.get("event")
        if event is None and len(call_args.args) > 1:
            event = call_args.args[1]
        self.assertEqual(event, "post.published")


if __name__ == "__main__":
    unittest.main()
