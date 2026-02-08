import unittest

from fastapi.testclient import TestClient

from app.db import engine
from app.main import app


class V09OpsHealthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_deep_health_structure(self):
        resp = self.client.get("/health/deep")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn(body["status"], ["ok", "degraded"])
        self.assertIn("database", body["checks"])
        self.assertIn("redis", body["checks"])

    def test_readiness_endpoint(self):
        resp = self.client.get("/health/readiness")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("ready", body)


if __name__ == "__main__":
    unittest.main()
