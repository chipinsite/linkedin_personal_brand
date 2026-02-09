"""Tests for v5.3 Comment Handling & Escalation.

Validates:
- Enhanced comment triage with MEDIA_INQUIRY
- Auto-reply generation service
- Suggested reply generation
- Escalation notification formatting
- Engagement service comment processing
- Escalation resolution endpoints
"""

import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v18_test.db")
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
from app.models import Comment, Draft, DraftStatus, PostFormat, PostTone, PublishedPost


class CommentTriageEnhancedTest(unittest.TestCase):
    """Tests for enhanced comment triage."""

    def test_media_inquiry_detection(self):
        from app.services.comment_triage import triage_comment, HighValueReason

        # Interview request
        result = triage_comment("Would you be open to an interview for our podcast?", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.MEDIA_INQUIRY)
        self.assertFalse(result.auto_reply)

        # Quote request
        result = triage_comment("Can we quote you in our upcoming article?", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.MEDIA_INQUIRY)

        # Podcast invitation
        result = triage_comment("Would love to have you on my podcast to discuss this", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.MEDIA_INQUIRY)

    def test_partnership_signals(self):
        from app.services.comment_triage import triage_comment, HighValueReason

        result = triage_comment("Would love to collaborate on this topic!", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.PARTNERSHIP_SIGNAL)

        result = triage_comment("Let's work together on something", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.PARTNERSHIP_SIGNAL)

    def test_technical_questions(self):
        from app.services.comment_triage import triage_comment, HighValueReason

        result = triage_comment("How does this work in practice?", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.TECHNICAL_QUESTION)

        result = triage_comment("Could you clarify what you mean by 'agentic'?", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.TECHNICAL_QUESTION)

    def test_objections(self):
        from app.services.comment_triage import triage_comment, HighValueReason

        result = triage_comment("I disagree with this take entirely", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.OBJECTION)

        result = triage_comment("That's not true, the data shows otherwise", None)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.OBJECTION)

    def test_influential_commenter(self):
        from app.services.comment_triage import triage_comment, HighValueReason

        result = triage_comment("Great post!", 15000)
        self.assertTrue(result.high_value)
        self.assertEqual(result.reason, HighValueReason.INFLUENTIAL)
        self.assertFalse(result.auto_reply)

    def test_auto_reply_eligible(self):
        from app.services.comment_triage import triage_comment

        result = triage_comment("Great insights, thanks for sharing!", None)
        self.assertFalse(result.high_value)
        self.assertIsNone(result.reason)
        self.assertTrue(result.auto_reply)

    def test_do_not_engage(self):
        from app.services.comment_triage import triage_comment

        # Spam link
        result = triage_comment("Check out https://spam.com for free stuff!", None)
        self.assertFalse(result.high_value)
        self.assertFalse(result.auto_reply)

        # Promotional
        result = triage_comment("Buy now and get 50% off!", None)
        self.assertFalse(result.high_value)
        self.assertFalse(result.auto_reply)

    def test_emoji_only(self):
        from app.services.comment_triage import triage_comment

        result = triage_comment("👍🔥", None)
        self.assertFalse(result.high_value)
        self.assertFalse(result.auto_reply)


class AutoReplyGenerationTest(unittest.TestCase):
    """Tests for auto-reply generation."""

    def test_generate_auto_reply_fallback(self):
        from app.services.comment_reply import generate_auto_reply

        reply = generate_auto_reply("Great post, very insightful!")
        self.assertIsInstance(reply, str)
        self.assertTrue(len(reply) > 0)

    def test_generate_auto_reply_consistent_for_same_comment(self):
        from app.services.comment_reply import generate_auto_reply

        reply1 = generate_auto_reply("Same comment text here")
        reply2 = generate_auto_reply("Same comment text here")
        # In mock mode, same comment should get same reply (hash-based)
        self.assertEqual(reply1, reply2)

    def test_generate_auto_reply_with_context(self):
        from app.services.comment_reply import generate_auto_reply

        reply = generate_auto_reply(
            "This is very helpful!",
            post_summary="Post about AI in advertising"
        )
        self.assertIsInstance(reply, str)


class SuggestedRepliesTest(unittest.TestCase):
    """Tests for suggested reply generation."""

    def test_generate_suggested_replies_partnership(self):
        from app.services.comment_reply import generate_suggested_replies

        replies = generate_suggested_replies(
            "Would love to collaborate!",
            "PARTNERSHIP_SIGNAL",
        )
        self.assertEqual(len(replies), 3)
        self.assertTrue(all(isinstance(r, str) for r in replies))

    def test_generate_suggested_replies_technical(self):
        from app.services.comment_reply import generate_suggested_replies

        replies = generate_suggested_replies(
            "How does this work?",
            "TECHNICAL_QUESTION",
        )
        self.assertEqual(len(replies), 3)

    def test_generate_suggested_replies_objection(self):
        from app.services.comment_reply import generate_suggested_replies

        replies = generate_suggested_replies(
            "I disagree with this approach",
            "OBJECTION",
        )
        self.assertEqual(len(replies), 3)

    def test_generate_suggested_replies_media(self):
        from app.services.comment_reply import generate_suggested_replies

        replies = generate_suggested_replies(
            "Would you be available for an interview?",
            "MEDIA_INQUIRY",
        )
        self.assertEqual(len(replies), 3)

    def test_generate_suggested_replies_unknown_reason(self):
        from app.services.comment_reply import generate_suggested_replies

        replies = generate_suggested_replies(
            "Some comment",
            "UNKNOWN_REASON",
        )
        self.assertEqual(len(replies), 3)


class EscalationNotificationTest(unittest.TestCase):
    """Tests for escalation notification formatting."""

    def test_format_escalation_notification(self):
        from app.services.telegram_service import format_escalation_notification

        text = format_escalation_notification(
            comment_text="Would love to collaborate on AI content!",
            commenter_name="John Smith",
            commenter_profile_url="https://linkedin.com/in/johnsmith",
            commenter_follower_count=5000,
            high_value_reason="PARTNERSHIP_SIGNAL",
            post_url="https://linkedin.com/posts/test123",
        )

        self.assertIn("High Value Comment Detected", text)
        self.assertIn("John Smith", text)
        self.assertIn("5,000", text)
        self.assertIn("Partnership signal", text)
        self.assertIn("Would love to collaborate", text)

    def test_format_escalation_with_suggested_replies(self):
        from app.services.telegram_service import format_escalation_notification

        text = format_escalation_notification(
            comment_text="Can I interview you?",
            commenter_name="Jane Doe",
            commenter_profile_url=None,
            commenter_follower_count=None,
            high_value_reason="MEDIA_INQUIRY",
            post_url=None,
            suggested_replies=["Reply 1", "Reply 2", "Reply 3"],
        )

        self.assertIn("Suggested Replies:", text)
        self.assertIn("1. Reply 1", text)
        self.assertIn("2. Reply 2", text)
        self.assertIn("3. Reply 3", text)

    def test_build_escalation_keyboard(self):
        from app.services.telegram_service import build_escalation_keyboard

        keyboard = build_escalation_keyboard("a1b2c3d4-e5f6-7890")

        self.assertEqual(len(keyboard), 1)
        self.assertEqual(len(keyboard[0]), 2)
        self.assertIn("Resolved", keyboard[0][0]["text"])
        self.assertIn("Ignore", keyboard[0][1]["text"])
        self.assertTrue(keyboard[0][0]["callback_data"].startswith("resolve:"))


class EscalationRoutesTest(unittest.TestCase):
    """Tests for escalation API endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Create test draft and post
        cls.draft = Draft(
            pillar_theme="Test",
            sub_theme="Test",
            format=PostFormat.text,
            tone=PostTone.direct,
            content_body="Test content",
            status=DraftStatus.approved,
            guardrail_check_passed=True,
        )
        cls.db.add(cls.draft)
        cls.db.commit()
        cls.db.refresh(cls.draft)

        cls.post = PublishedPost(
            draft_id=cls.draft.id,
            content_body=cls.draft.content_body,
            format=cls.draft.format,
            tone=cls.draft.tone,
            linkedin_post_id="test_post_escalation",
            linkedin_post_url="https://linkedin.com/posts/test",
            published_at=datetime.now(timezone.utc),
        )
        cls.db.add(cls.post)
        cls.db.commit()
        cls.db.refresh(cls.post)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    def test_create_escalated_comment(self):
        response = self.client.post("/comments", json={
            "published_post_id": str(self.post.id),
            "commenter_name": "Test User",
            "comment_text": "Would love to collaborate with you!",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_high_value"])
        self.assertEqual(data["high_value_reason"], "PARTNERSHIP_SIGNAL")
        self.assertTrue(data["escalated"])

    def test_list_escalated_comments(self):
        response = self.client.get("/comments/escalated")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_get_suggested_replies(self):
        # First create an escalated comment
        create_response = self.client.post("/comments", json={
            "published_post_id": str(self.post.id),
            "commenter_name": "Tech User",
            "comment_text": "How does this AI bidding work exactly?",
        })
        self.assertEqual(create_response.status_code, 200)
        comment_id = create_response.json()["id"]

        # Get suggested replies
        response = self.client.get(f"/comments/{comment_id}/suggested-replies")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggested_replies", data)
        self.assertEqual(len(data["suggested_replies"]), 3)

    def test_resolve_escalation(self):
        # Create escalated comment
        create_response = self.client.post("/comments", json={
            "published_post_id": str(self.post.id),
            "commenter_name": "Resolve Test",
            "comment_text": "Can I interview you for my podcast?",
        })
        self.assertEqual(create_response.status_code, 200)
        comment_id = create_response.json()["id"]

        # Resolve it
        response = self.client.post(
            f"/comments/{comment_id}/resolve-escalation",
            json={"action": "replied", "reply_text": "Thanks for reaching out!"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["manual_reply_sent"])
        self.assertEqual(data["manual_reply_text"], "Thanks for reaching out!")

    def test_resolve_escalation_ignore(self):
        # Create escalated comment
        create_response = self.client.post("/comments", json={
            "published_post_id": str(self.post.id),
            "commenter_name": "Ignore Test",
            "comment_text": "I totally disagree with everything here",
        })
        self.assertEqual(create_response.status_code, 200)
        comment_id = create_response.json()["id"]

        # Ignore it
        response = self.client.post(
            f"/comments/{comment_id}/resolve-escalation",
            json={"action": "ignored"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["manual_reply_sent"])
        self.assertIn("IGNORED", data["manual_reply_text"])


class EngagementServiceCommentProcessingTest(unittest.TestCase):
    """Tests for engagement service comment processing with new features."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    @patch("app.services.telegram_service._is_telegram_configured", return_value=True)
    @patch("app.services.telegram_service.httpx.post")
    def test_escalation_triggers_notification(self, mock_post, mock_configured):
        from app.services.engagement import poll_and_store_comments
        import json

        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create test draft and post
        draft = Draft(
            pillar_theme="Test pillar",
            sub_theme="Test sub",
            format=PostFormat.text,
            tone=PostTone.direct,
            content_body="Test content for escalation",
            status=DraftStatus.approved,
            guardrail_check_passed=True,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        now = datetime.now(timezone.utc)
        post = PublishedPost(
            draft_id=draft.id,
            content_body=draft.content_body,
            format=draft.format,
            tone=draft.tone,
            linkedin_post_id="test_escalation_notify",
            linkedin_post_url="https://linkedin.com/posts/test",
            published_at=now,
            comment_monitoring_started_at=now,
            comment_monitoring_until=now + timedelta(hours=48),
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        # Set up mock comments with high-value comment
        mock_comments = json.dumps({
            "test_escalation_notify": [
                {
                    "id": "comment_esc_1",
                    "commenter_name": "Partner Person",
                    "comment_text": "Would love to collaborate with you on this!",
                }
            ]
        })

        import app.services.linkedin as linkedin_module
        original_mode = linkedin_module.settings.linkedin_api_mode
        original_mock = linkedin_module.settings.linkedin_mock_comments_json

        linkedin_module.settings.linkedin_api_mode = "api"
        linkedin_module.settings.linkedin_mock_comments_json = mock_comments

        try:
            result = poll_and_store_comments(db=self.db)
            self.assertEqual(result["status"], "ok")
            self.assertGreaterEqual(result["escalations"], 1)
            # Telegram notification should have been called
            self.assertTrue(mock_post.called)
        finally:
            linkedin_module.settings.linkedin_api_mode = original_mode
            linkedin_module.settings.linkedin_mock_comments_json = original_mock


if __name__ == "__main__":
    unittest.main()
