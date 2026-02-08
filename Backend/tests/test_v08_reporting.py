import unittest

from fastapi.testclient import TestClient

from app.db import engine
from app.main import app


class V08ReportingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def _create_published_post_with_metrics(self) -> str:
        draft = self.client.post("/drafts/generate").json()
        self.client.post(f"/drafts/{draft['id']}/approve", json={})
        post = next(p for p in self.client.get("/posts").json() if p["draft_id"] == draft["id"])
        self.client.post(
            f"/posts/{post['id']}/confirm-manual-publish",
            json={"linkedin_post_url": "https://linkedin.com/feed/update/urn:li:activity:rep1"},
        )
        self.client.post(
            f"/posts/{post['id']}/metrics",
            json={"impressions": 500, "reactions": 20, "comments_count": 7, "shares": 3},
        )
        self.client.post(
            "/comments",
            json={
                "published_post_id": post["id"],
                "commenter_name": "Ruth",
                "comment_text": "Interesting perspective",
                "commenter_follower_count": 50,
            },
        )
        return post["id"]

    def test_daily_report_and_send(self):
        self._create_published_post_with_metrics()

        report = self.client.get("/reports/daily")
        self.assertEqual(report.status_code, 200)
        body = report.json()
        self.assertGreaterEqual(body["posts_published"], 1)
        self.assertGreaterEqual(body["total_impressions"], 500)

        send_resp = self.client.post("/reports/daily/send")
        self.assertEqual(send_resp.status_code, 200)
        self.assertIn("sent", send_resp.json())


if __name__ == "__main__":
    unittest.main()
