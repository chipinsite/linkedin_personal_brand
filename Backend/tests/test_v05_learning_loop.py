import json
import os
import tempfile
import unittest

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v05_test.db")
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
from app.models import LearningWeight


class V05LearningLoopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def _create_post(self) -> str:
        draft = self.client.post("/drafts/generate").json()
        self.client.post(f"/drafts/{draft['id']}/approve", json={})
        posts = self.client.get("/posts").json()
        post = next(p for p in posts if p["draft_id"] == draft["id"])
        return post["id"]

    def test_recompute_learning_weights_from_metrics(self):
        post_a = self._create_post()
        post_b = self._create_post()

        # High-performing post
        resp_a = self.client.post(
            f"/posts/{post_a}/metrics",
            json={"impressions": 1000, "reactions": 90, "comments_count": 20, "shares": 10},
        )
        self.assertEqual(resp_a.status_code, 200)

        # Lower-performing post
        resp_b = self.client.post(
            f"/posts/{post_b}/metrics",
            json={"impressions": 1000, "reactions": 5, "comments_count": 1, "shares": 0},
        )
        self.assertEqual(resp_b.status_code, 200)

        rec = self.client.post("/learning/recompute")
        self.assertEqual(rec.status_code, 200)

        weights_resp = self.client.get("/learning/weights")
        self.assertEqual(weights_resp.status_code, 200)
        weights = weights_resp.json()

        format_weights = json.loads(weights["format_weights_json"])
        tone_weights = json.loads(weights["tone_weights_json"])

        self.assertAlmostEqual(sum(format_weights.values()), 1.0, places=4)
        self.assertAlmostEqual(sum(tone_weights.values()), 1.0, places=4)

        db = SessionLocal()
        try:
            row = db.query(LearningWeight).filter(LearningWeight.id == 1).first()
            self.assertIsNotNone(row)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
