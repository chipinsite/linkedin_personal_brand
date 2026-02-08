import json
import os
import tempfile
import unittest
import uuid
from datetime import timedelta

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v04_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

from fastapi.testclient import TestClient

from app.config import settings
from app.db import SessionLocal, engine
from app.main import app
from app.models import Comment, PublishedPost
from app.services.engagement import polling_interval_for_post_age


class V04MonitoringPollingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.original_mode = settings.linkedin_api_mode
        cls.original_token = settings.linkedin_api_token
        cls.original_mock = settings.linkedin_mock_comments_json

    @classmethod
    def tearDownClass(cls):
        settings.linkedin_api_mode = cls.original_mode
        settings.linkedin_api_token = cls.original_token
        settings.linkedin_mock_comments_json = cls.original_mock
        engine.dispose()

    def test_confirm_publish_sets_monitoring_window(self):
        draft_resp = self.client.post("/drafts/generate")
        self.assertEqual(draft_resp.status_code, 200)
        draft_id = draft_resp.json()["id"]

        approve_resp = self.client.post(f"/drafts/{draft_id}/approve", json={})
        self.assertEqual(approve_resp.status_code, 200)

        posts_resp = self.client.get("/posts")
        post = next(p for p in posts_resp.json() if p["draft_id"] == draft_id)

        confirm_resp = self.client.post(
            f"/posts/{post['id']}/confirm-manual-publish",
            json={"linkedin_post_url": "https://linkedin.com/feed/update/urn:li:activity:12345"},
        )
        self.assertEqual(confirm_resp.status_code, 200)
        body = confirm_resp.json()
        self.assertIsNotNone(body["comment_monitoring_started_at"])
        self.assertIsNotNone(body["comment_monitoring_until"])
        self.assertIsNone(body["last_comment_poll_at"])

    def test_due_polling_uses_monitor_window_and_updates_last_poll(self):
        settings.linkedin_api_mode = "api"
        settings.linkedin_api_token = "dummy-token"

        draft_resp = self.client.post("/drafts/generate")
        draft_id = draft_resp.json()["id"]
        self.client.post(f"/drafts/{draft_id}/approve", json={})
        post = next(p for p in self.client.get("/posts").json() if p["draft_id"] == draft_id)

        self.client.post(
            f"/posts/{post['id']}/confirm-manual-publish",
            json={"linkedin_post_url": "https://linkedin.com/feed/update/urn:li:activity:54321"},
        )

        settings.linkedin_mock_comments_json = json.dumps(
            {
                "urn:li:activity:54321": [
                    {
                        "linkedin_comment_id": "c-100",
                        "commenter_name": "Jordan",
                        "comment_text": "How would you phase this rollout?",
                        "commenter_follower_count": 120,
                    }
                ]
            }
        )

        poll_resp = self.client.post("/engagement/poll")
        self.assertEqual(poll_resp.status_code, 200)
        self.assertEqual(poll_resp.json()["status"], "ok")
        self.assertEqual(poll_resp.json()["new_comments"], 1)

        db = SessionLocal()
        try:
            db_post = db.query(PublishedPost).filter(PublishedPost.id == uuid.UUID(post["id"])).first()
            self.assertIsNotNone(db_post.last_comment_poll_at)
            comments = db.query(Comment).filter(Comment.published_post_id == db_post.id).all()
            self.assertEqual(len(comments), 1)
        finally:
            db.close()

    def test_polling_interval_by_post_age(self):
        self.assertEqual(polling_interval_for_post_age(timedelta(minutes=30)), timedelta(minutes=10))
        self.assertEqual(polling_interval_for_post_age(timedelta(hours=4)), timedelta(minutes=30))
        self.assertEqual(polling_interval_for_post_age(timedelta(hours=20)), timedelta(hours=2))


if __name__ == "__main__":
    unittest.main()
