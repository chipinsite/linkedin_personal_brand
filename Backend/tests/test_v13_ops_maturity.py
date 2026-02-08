"""Regression tests for v4.7 operational maturity features.

Covers:
- Structured JSON logging formatter
- Request ID middleware (generation and propagation)
- GET /health/full aggregated endpoint
- Deploy profile config defaults
"""

import json
import logging
import unittest

from fastapi.testclient import TestClient

from app.db import engine, Base
from app.main import app
from app.logging_config import JSONFormatter, configure_logging
from app.middleware.request_id import RequestIdMiddleware, request_id_var, get_request_id
from app.config import settings


class JSONFormatterTest(unittest.TestCase):
    """Test the structured JSON log formatter."""

    def test_json_formatter_produces_valid_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello %s",
            args=("world",),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["logger"], "test.logger")
        self.assertEqual(parsed["message"], "Hello world")
        self.assertIn("timestamp", parsed)

    def test_json_formatter_includes_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Failed",
                args=(),
                exc_info=sys.exc_info(),
            )
        output = formatter.format(record)
        parsed = json.loads(output)
        self.assertIn("exception", parsed)
        self.assertIn("ValueError", parsed["exception"])

    def test_json_formatter_includes_request_id_when_set(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="With request context",
            args=(),
            exc_info=None,
        )
        record.request_id = "abc-123"
        output = formatter.format(record)
        parsed = json.loads(output)
        self.assertEqual(parsed["request_id"], "abc-123")


class RequestIdMiddlewareTest(unittest.TestCase):
    """Test request ID generation and propagation."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_response_contains_x_request_id_header(self):
        resp = self.client.get("/health")
        self.assertIn("x-request-id", resp.headers)
        rid = resp.headers["x-request-id"]
        self.assertTrue(len(rid) > 0)

    def test_propagates_incoming_request_id(self):
        custom_id = "my-trace-id-12345"
        resp = self.client.get("/health", headers={"x-request-id": custom_id})
        self.assertEqual(resp.headers["x-request-id"], custom_id)

    def test_generates_unique_ids_for_different_requests(self):
        resp1 = self.client.get("/health")
        resp2 = self.client.get("/health")
        self.assertNotEqual(
            resp1.headers["x-request-id"],
            resp2.headers["x-request-id"],
        )


class HealthFullEndpointTest(unittest.TestCase):
    """Test GET /health/full aggregated endpoint."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_health_full_returns_200(self):
        resp = self.client.get("/health/full")
        self.assertEqual(resp.status_code, 200)

    def test_health_full_structure(self):
        resp = self.client.get("/health/full")
        body = resp.json()
        self.assertIn("status", body)
        self.assertIn("app_env", body)
        self.assertIn("request_id", body)
        self.assertIn("checks", body)
        checks = body["checks"]
        self.assertIn("heartbeat", checks)
        self.assertIn("database", checks)
        self.assertIn("redis", checks)
        self.assertIn("schema", checks)
        self.assertIn("migration", checks)

    def test_health_full_database_ok(self):
        resp = self.client.get("/health/full")
        body = resp.json()
        self.assertTrue(body["checks"]["database"]["ok"])

    def test_health_full_schema_ok(self):
        resp = self.client.get("/health/full")
        body = resp.json()
        self.assertTrue(body["checks"]["schema"]["ok"])
        self.assertEqual(body["checks"]["schema"]["missing"], [])

    def test_health_full_includes_request_id(self):
        custom_id = "trace-for-full-health"
        resp = self.client.get("/health/full", headers={"x-request-id": custom_id})
        body = resp.json()
        self.assertEqual(body["request_id"], custom_id)


class DeployProfileTest(unittest.TestCase):
    """Test deploy profile configuration defaults."""

    def test_app_env_is_set(self):
        # When run in the test suite APP_ENV is set to "test" by earlier modules;
        # standalone default would be "dev".  Either is valid – just verify it's populated.
        self.assertIn(settings.app_env, ("dev", "test"))

    def test_default_log_level_is_info(self):
        self.assertEqual(settings.log_level.upper(), "INFO")

    def test_log_json_default_is_false(self):
        self.assertFalse(settings.log_json)


if __name__ == "__main__":
    unittest.main()
