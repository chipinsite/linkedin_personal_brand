import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone

# Configure env before importing app modules.
DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v01_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.db import engine
from app.main import app
from app.models import PublishedPost


class V01SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_01_generate_approve_publish_and_comment(self):
        generate_resp = self.client.post("/drafts/generate")
        self.assertEqual(generate_resp.status_code, 200)
        draft = generate_resp.json()
        self.assertEqual(draft["status"], "PENDING")

        approve_resp = self.client.post(f"/drafts/{draft['id']}/approve", json={})
        self.assertEqual(approve_resp.status_code, 200)

        posts_resp = self.client.get("/posts")
        self.assertEqual(posts_resp.status_code, 200)
        posts = posts_resp.json()
        self.assertGreaterEqual(len(posts), 1)
        post = next(p for p in posts if p["draft_id"] == draft["id"])

        db = SessionLocal()
        try:
            db_post = db.query(PublishedPost).filter(PublishedPost.id == uuid.UUID(post["id"])).first()
            db_post.scheduled_time = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        due_resp = self.client.post("/posts/publish-due")
        self.assertEqual(due_resp.status_code, 200)
        self.assertGreaterEqual(due_resp.json()["processed"], 1)

        confirm_resp = self.client.post(
            f"/posts/{post['id']}/confirm-manual-publish",
            json={"linkedin_post_url": "https://linkedin.com/feed/update/test-post"},
        )
        self.assertEqual(confirm_resp.status_code, 200)
        confirmed = confirm_resp.json()
        self.assertIsNotNone(confirmed["published_at"])

        comment_resp = self.client.post(
            "/comments",
            json={
                "published_post_id": post["id"],
                "commenter_name": "Alex",
                "comment_text": "How would you apply this in a lean team?",
                "commenter_follower_count": 150,
            },
        )
        self.assertEqual(comment_resp.status_code, 200)
        comment = comment_resp.json()
        self.assertTrue(comment["is_high_value"])
        self.assertEqual(comment["high_value_reason"], "TECHNICAL_QUESTION")
        self.assertFalse(comment["auto_reply_sent"])

    def test_02_posting_toggle_blocks_generation(self):
        off_resp = self.client.post("/admin/posting/off")
        self.assertEqual(off_resp.status_code, 200)

        blocked_resp = self.client.post("/drafts/generate")
        self.assertEqual(blocked_resp.status_code, 409)

        on_resp = self.client.post("/admin/posting/on")
        self.assertEqual(on_resp.status_code, 200)

        unblocked_resp = self.client.post("/drafts/generate")
        self.assertEqual(unblocked_resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
