import os
import tempfile
import unittest

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v02_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ["LLM_PROVIDER"] = "claude"
os.environ["LLM_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.db import engine
from app.main import app
from app.models import SourceMaterial
from app.services.research_ingestion import ingest_feed_entries


class V02ResearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_ingest_entries_and_generate_grounded_draft(self):
        db = SessionLocal()
        try:
            entries = [
                {
                    "title": "Programmatic measurement shifts in 2026",
                    "link": "https://example.com/adtech-measurement",
                    "summary": "Measurement and attribution in programmatic media is changing with privacy constraints.",
                    "published": "Fri, 06 Feb 2026 08:00:00 GMT",
                },
                {
                    "title": "AI bidding agents in retail media",
                    "link": "https://example.com/ai-bidding",
                    "summary": "Autonomous bidding and optimization loops are becoming practical in retail media.",
                    "published": "Fri, 06 Feb 2026 09:00:00 GMT",
                },
            ]
            created = ingest_feed_entries(db, source_name="Test Feed", entries=entries, max_items=10)
            self.assertEqual(created, 2)
        finally:
            db.close()

        sources_resp = self.client.get("/sources")
        self.assertEqual(sources_resp.status_code, 200)
        self.assertGreaterEqual(len(sources_resp.json()), 2)

        generate_resp = self.client.post("/drafts/generate")
        self.assertEqual(generate_resp.status_code, 200)
        draft = generate_resp.json()
        self.assertIsNotNone(draft["source_citations"])
        self.assertIn("https://example.com", draft["source_citations"])

    def test_source_deduplication_by_url(self):
        db = SessionLocal()
        try:
            seed_entries = [
                {
                    "title": "Initial URL entry",
                    "link": "https://example.com/adtech-measurement",
                    "summary": "Seed record for dedupe test.",
                    "published": "Fri, 06 Feb 2026 10:00:00 GMT",
                }
            ]
            ingest_feed_entries(db, source_name="Test Feed", entries=seed_entries, max_items=10)

            entries = [
                {
                    "title": "Duplicate URL entry",
                    "link": "https://example.com/adtech-measurement",
                    "summary": "This should be skipped due to dedupe.",
                    "published": "Fri, 06 Feb 2026 10:00:00 GMT",
                }
            ]
            created = ingest_feed_entries(db, source_name="Test Feed", entries=entries, max_items=10)
            self.assertEqual(created, 0)

            count = db.query(SourceMaterial).filter(SourceMaterial.url == "https://example.com/adtech-measurement").count()
            self.assertEqual(count, 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
