"""Regression tests for v4.5 startup self-check and DB diagnostic endpoint.

Covers:
- check_schema on a healthy (migrated) database
- check_schema on a completely empty database (no tables)
- check_schema on a database with some tables missing
- startup_schema_check raises SchemaError when tables are missing
- GET /health/db endpoint returns expected structure
"""

import unittest

from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

from app.db import engine, Base
from app.main import app
from app.services.db_check import check_schema, startup_schema_check, SchemaError, REQUIRED_TABLES


class SchemaCheckHealthyTest(unittest.TestCase):
    """Test check_schema against the app's engine (tables created by test imports)."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_healthy_schema_reports_ok(self):
        result = check_schema(engine)
        self.assertTrue(result["ok"])
        self.assertEqual(result["missing"], [])
        for table in REQUIRED_TABLES:
            self.assertTrue(result["tables"][table], f"Expected {table} to exist")

    def test_startup_check_passes_on_healthy_db(self):
        # Should not raise
        startup_schema_check(engine)


class SchemaCheckEmptyDbTest(unittest.TestCase):
    """Test check_schema against a completely empty in-memory database."""

    def test_empty_db_reports_all_missing(self):
        empty_engine = create_engine("sqlite:///:memory:")
        result = check_schema(empty_engine)
        self.assertFalse(result["ok"])
        self.assertEqual(set(result["missing"]), REQUIRED_TABLES)
        for table in REQUIRED_TABLES:
            self.assertFalse(result["tables"][table])
        empty_engine.dispose()

    def test_startup_check_raises_on_empty_db(self):
        empty_engine = create_engine("sqlite:///:memory:")
        with self.assertRaises(SchemaError) as ctx:
            startup_schema_check(empty_engine)
        self.assertIn("Missing tables", str(ctx.exception))
        empty_engine.dispose()


class SchemaCheckPartialDbTest(unittest.TestCase):
    """Test check_schema when only some tables exist."""

    def test_partial_schema_reports_missing(self):
        partial_engine = create_engine("sqlite:///:memory:")
        with partial_engine.connect() as conn:
            conn.execute(text("CREATE TABLE drafts (id INTEGER PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE comments (id INTEGER PRIMARY KEY)"))
            conn.commit()

        result = check_schema(partial_engine)
        self.assertFalse(result["ok"])
        self.assertTrue(result["tables"]["drafts"])
        self.assertTrue(result["tables"]["comments"])
        self.assertFalse(result["tables"]["published_posts"])
        self.assertIn("published_posts", result["missing"])
        partial_engine.dispose()


class HealthDbEndpointTest(unittest.TestCase):
    """Test GET /health/db endpoint."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_health_db_returns_200(self):
        resp = self.client.get("/health/db")
        self.assertEqual(resp.status_code, 200)

    def test_health_db_structure(self):
        resp = self.client.get("/health/db")
        body = resp.json()
        self.assertIn("database_url", body)
        self.assertIn("migration", body)
        self.assertIn("schema", body)
        self.assertIn("ok", body["schema"])
        self.assertIn("tables", body["schema"])
        self.assertIn("missing", body["schema"])
        self.assertIn("current_head", body["migration"])

    def test_health_db_schema_ok(self):
        resp = self.client.get("/health/db")
        body = resp.json()
        self.assertTrue(body["schema"]["ok"])
        self.assertEqual(body["schema"]["missing"], [])

    def test_health_db_url_redacted(self):
        resp = self.client.get("/health/db")
        body = resp.json()
        url = body["database_url"]
        # Should not contain raw credentials
        self.assertNotIn("password", url.lower())


if __name__ == "__main__":
    unittest.main()
