import os
import tempfile
import unittest

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v03_test.db")
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
from app.db import engine
from app.main import app
from app.services.guardrails import validate_post


class V03SecurityAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.original_api_key = settings.app_api_key

    @classmethod
    def tearDownClass(cls):
        settings.app_api_key = cls.original_api_key
        engine.dispose()

    def test_write_auth_enforced_when_key_configured(self):
        settings.app_api_key = "secret-key"

        blocked = self.client.post("/admin/posting/off")
        self.assertEqual(blocked.status_code, 401)

        allowed = self.client.post("/admin/posting/off", headers={"x-api-key": "secret-key"})
        self.assertEqual(allowed.status_code, 200)

        logs = self.client.get("/admin/audit-logs")
        self.assertEqual(logs.status_code, 200)
        actions = [row["action"] for row in logs.json()]
        self.assertIn("admin.posting_off", actions)

        reset = self.client.post("/admin/posting/on", headers={"x-api-key": "secret-key"})
        self.assertEqual(reset.status_code, 200)

    def test_guardrail_flags_unverified_statements(self):
        content = (
            "Studies show campaign performance improved by 47% across the market. "
            "Everyone knows this is proven that automation always wins."
        )
        result = validate_post(content)
        self.assertFalse(result.passed)
        self.assertIn("UNVERIFIED_CLAIM_LANGUAGE", result.violations)
        self.assertIn("STAT_WITHOUT_SOURCE", result.violations)

    def test_guardrail_blocks_links_and_engagement_bait(self):
        content = (
            "Like if you agree with this trend. "
            "Read more at https://example.com/long-report "
            "@a @b @c @d #one #two #three #four"
        )
        result = validate_post(content)
        self.assertFalse(result.passed)
        self.assertIn("ENGAGEMENT_BAIT_LANGUAGE", result.violations)
        self.assertIn("EXTERNAL_LINK_IN_BODY", result.violations)
        self.assertIn("MENTION_OVERUSE", result.violations)
        self.assertIn("HASHTAG_LIMIT_EXCEEDED", result.violations)


if __name__ == "__main__":
    unittest.main()
