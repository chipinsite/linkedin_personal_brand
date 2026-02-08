import os
import tempfile
import unittest

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v10_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

from fastapi.testclient import TestClient

from app.db import engine
from app.main import app


class V10StateExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_export_state_returns_single_user_backup_payload(self):
        draft_resp = self.client.post("/drafts/generate")
        self.assertEqual(draft_resp.status_code, 200)
        draft_id = draft_resp.json()["id"]
        self.client.post(f"/drafts/{draft_id}/approve", json={})

        export_resp = self.client.get("/admin/export-state")
        self.assertEqual(export_resp.status_code, 200)
        payload = export_resp.json()

        self.assertIn("generated_at", payload)
        self.assertIn("meta", payload)
        self.assertEqual(payload["meta"]["mode"], "single-user")

        for key in [
            "config",
            "drafts",
            "posts",
            "comments",
            "sources",
            "audit_logs",
            "learning_weights",
            "engagement_metrics",
            "notifications",
        ]:
            self.assertIn(key, payload)
            self.assertIsInstance(payload[key], list)

        self.assertGreaterEqual(len(payload["drafts"]), 1)
        self.assertGreaterEqual(len(payload["posts"]), 1)


if __name__ == "__main__":
    unittest.main()
