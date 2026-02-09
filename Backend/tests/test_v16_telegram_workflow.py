"""Tests for v5.1 Telegram Approval Workflow Enhancement.

Validates:
- Draft notification formatting
- Inline keyboard generation
- Telegram message sending (mocked)
- Bot command handlers
- Callback query handlers
"""

import os
import tempfile
import unittest
import uuid
from unittest.mock import MagicMock, patch

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v16_test.db")
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
from app.models import Draft, DraftStatus, PostFormat, PostTone


class DraftNotificationFormattingTest(unittest.TestCase):
    """Tests for draft notification text formatting."""

    def test_format_draft_notification_basic(self):
        from app.services.telegram_service import format_draft_notification

        draft = Draft(
            id=uuid.uuid4(),
            pillar_theme="Adtech fundamentals",
            sub_theme="Programmatic buying",
            format=PostFormat.text,
            tone=PostTone.educational,
            content_body="Test content for LinkedIn post.",
            status=DraftStatus.pending,
            guardrail_check_passed=True,
        )

        text = format_draft_notification(draft)

        self.assertIn("Draft Ready for Approval", text)
        self.assertIn("Adtech fundamentals", text)
        self.assertIn("Programmatic buying", text)
        self.assertIn("TEXT", text)
        self.assertIn("EDUCATIONAL", text)
        self.assertIn("Test content for LinkedIn post", text)
        self.assertIn("/approve", text)
        self.assertIn("/reject", text)
        self.assertIn("/preview", text)

    def test_format_draft_notification_with_guardrail_warning(self):
        from app.services.telegram_service import format_draft_notification

        draft = Draft(
            id=uuid.uuid4(),
            pillar_theme="AI in advertising",
            sub_theme="Generative creative",
            format=PostFormat.image,
            tone=PostTone.opinionated,
            content_body="Content with guardrail issues.",
            status=DraftStatus.pending,
            guardrail_check_passed=False,
        )

        text = format_draft_notification(draft)

        self.assertIn("⚠️ Check manually", text)

    def test_format_draft_notification_with_sources(self):
        import json
        from app.services.telegram_service import format_draft_notification

        draft = Draft(
            id=uuid.uuid4(),
            pillar_theme="Agentic AI",
            sub_theme="AI bidding agents",
            format=PostFormat.carousel,
            tone=PostTone.direct,
            content_body="AI bidding post content.",
            status=DraftStatus.pending,
            guardrail_check_passed=True,
            source_citations=json.dumps([
                {"source": "AdExchanger", "url": "https://adexchanger.com/article1"},
                {"source": "Digiday", "url": "https://digiday.com/article2"},
            ]),
        )

        text = format_draft_notification(draft)

        self.assertIn("Sources:", text)
        self.assertIn("AdExchanger", text)
        self.assertIn("Digiday", text)


class InlineKeyboardGenerationTest(unittest.TestCase):
    """Tests for inline keyboard button generation."""

    def test_build_draft_keyboard(self):
        from app.services.telegram_service import build_draft_keyboard

        draft_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        keyboard = build_draft_keyboard(draft_id)

        # Should have 2 rows
        self.assertEqual(len(keyboard), 2)

        # First row: Approve, Reject
        self.assertEqual(len(keyboard[0]), 2)
        self.assertIn("Approve", keyboard[0][0]["text"])
        self.assertIn("Reject", keyboard[0][1]["text"])

        # Second row: Preview
        self.assertEqual(len(keyboard[1]), 1)
        self.assertIn("Preview", keyboard[1][0]["text"])

        # Callback data should use short ID
        self.assertTrue(keyboard[0][0]["callback_data"].startswith("approve:"))
        self.assertTrue(keyboard[0][1]["callback_data"].startswith("reject:"))
        self.assertTrue(keyboard[1][0]["callback_data"].startswith("preview:"))


class TelegramMessageSendingTest(unittest.TestCase):
    """Tests for Telegram message sending functions."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    @patch("app.services.telegram_service._is_telegram_configured", return_value=True)
    @patch("app.services.telegram_service.httpx.post")
    def test_send_telegram_message_success(self, mock_post, mock_configured):
        from app.services.telegram_service import send_telegram_message

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = send_telegram_message(
            db=self.db,
            text="Test message",
            event_type="TEST",
        )

        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("app.services.telegram_service._is_telegram_configured", return_value=True)
    @patch("app.services.telegram_service.httpx.post")
    def test_send_telegram_message_with_keyboard(self, mock_post, mock_configured):
        from app.services.telegram_service import send_telegram_message_with_keyboard

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        keyboard = [[{"text": "Button", "callback_data": "test:data"}]]
        result = send_telegram_message_with_keyboard(
            db=self.db,
            text="Test message with keyboard",
            event_type="TEST_KEYBOARD",
            inline_keyboard=keyboard,
        )

        self.assertTrue(result)
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        self.assertIn("reply_markup", payload)
        self.assertIn("inline_keyboard", payload["reply_markup"])

    def test_send_telegram_message_missing_credentials(self):
        from app.services.telegram_service import send_telegram_message

        # Temporarily clear credentials
        import app.services.telegram_service as ts
        original_check = ts._is_telegram_configured

        ts._is_telegram_configured = lambda: False

        try:
            result = send_telegram_message(
                db=self.db,
                text="Test message",
                event_type="TEST",
            )
            self.assertFalse(result)
        finally:
            ts._is_telegram_configured = original_check


class DraftApprovalNotificationTest(unittest.TestCase):
    """Tests for the combined draft approval notification."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    @patch("app.services.telegram_service._is_telegram_configured", return_value=True)
    @patch("app.services.telegram_service.httpx.post")
    def test_send_draft_approval_notification(self, mock_post, mock_configured):
        from app.services.telegram_service import send_draft_approval_notification

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        draft = Draft(
            id=uuid.uuid4(),
            pillar_theme="Adtech fundamentals",
            sub_theme="Retail media",
            format=PostFormat.text,
            tone=PostTone.educational,
            content_body="Retail media insights for LinkedIn.",
            status=DraftStatus.pending,
            guardrail_check_passed=True,
        )

        result = send_draft_approval_notification(db=self.db, draft=draft)

        self.assertTrue(result)
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]

        # Should have inline keyboard
        self.assertIn("reply_markup", payload)
        # Should have formatted text
        self.assertIn("Draft Ready for Approval", payload["text"])


class BotCommandHelpersTest(unittest.TestCase):
    """Tests for bot helper functions."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    def test_get_draft_by_full_id(self):
        from app.telegram.bot import _get_draft_by_id

        # Create a test draft
        draft = Draft(
            pillar_theme="Test pillar",
            sub_theme="Test sub",
            format=PostFormat.text,
            tone=PostTone.direct,
            content_body="Test content",
            status=DraftStatus.pending,
            guardrail_check_passed=True,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        # Should find by full UUID
        found = _get_draft_by_id(self.db, str(draft.id))
        self.assertIsNotNone(found)
        self.assertEqual(found.id, draft.id)

    def test_get_draft_by_short_id(self):
        from app.telegram.bot import _get_draft_by_id

        # Create a test draft
        draft = Draft(
            pillar_theme="Test pillar short",
            sub_theme="Test sub short",
            format=PostFormat.image,
            tone=PostTone.exploratory,
            content_body="Short ID test content",
            status=DraftStatus.pending,
            guardrail_check_passed=True,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        # Should find by short ID prefix
        short_id = str(draft.id)[:8]
        found = _get_draft_by_id(self.db, short_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, draft.id)

    def test_get_draft_not_found(self):
        from app.telegram.bot import _get_draft_by_id

        found = _get_draft_by_id(self.db, "nonexistent")
        self.assertIsNone(found)


class WorkflowIntegrationTest(unittest.TestCase):
    """Tests for workflow integration with Telegram notifications."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    @patch("app.services.telegram_service._is_telegram_configured", return_value=True)
    @patch("app.services.telegram_service.httpx.post")
    def test_draft_generation_sends_notification(self, mock_post, mock_configured):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Generate a draft via API
        response = self.client.post("/drafts/generate")

        # Should have called Telegram API
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_post.called)

        # Check notification was for draft approval
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        self.assertIn("Draft Ready for Approval", payload["text"])


if __name__ == "__main__":
    unittest.main()
