import unittest

from fastapi.testclient import TestClient

from app.config import settings
from app.db import engine
from app.main import app


class V07AuthProfilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.orig_enforce_read = settings.auth_enforce_read
        cls.orig_read_key = settings.app_read_api_key
        cls.orig_write_key = settings.app_write_api_key
        cls.orig_compat_key = settings.app_api_key

    @classmethod
    def tearDownClass(cls):
        settings.auth_enforce_read = cls.orig_enforce_read
        settings.app_read_api_key = cls.orig_read_key
        settings.app_write_api_key = cls.orig_write_key
        settings.app_api_key = cls.orig_compat_key
        engine.dispose()

    def test_read_write_key_profiles(self):
        settings.auth_enforce_read = True
        settings.app_read_api_key = "read-key"
        settings.app_write_api_key = "write-key"
        settings.app_api_key = None

        denied_read = self.client.get("/posts")
        self.assertEqual(denied_read.status_code, 401)

        allowed_read = self.client.get("/posts", headers={"x-api-key": "read-key"})
        self.assertEqual(allowed_read.status_code, 200)

        denied_write = self.client.post("/admin/posting/off", headers={"x-api-key": "read-key"})
        self.assertEqual(denied_write.status_code, 401)

        allowed_write = self.client.post("/admin/posting/off", headers={"x-api-key": "write-key"})
        self.assertEqual(allowed_write.status_code, 200)

        self.client.post("/admin/posting/on", headers={"x-api-key": "write-key"})


if __name__ == "__main__":
    unittest.main()
