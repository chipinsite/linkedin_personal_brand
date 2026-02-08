import json
import unittest

import httpx

from app.config import settings
from app.services.linkedin import (
    LinkedInAuthError,
    fetch_recent_comments_for_post,
)


class V06LinkedInAdapterTest(unittest.TestCase):
    def setUp(self):
        self.orig_mode = settings.linkedin_api_mode
        self.orig_token = settings.linkedin_api_token
        self.orig_mock = settings.linkedin_mock_comments_json

    def tearDown(self):
        settings.linkedin_api_mode = self.orig_mode
        settings.linkedin_api_token = self.orig_token
        settings.linkedin_mock_comments_json = self.orig_mock

    def test_mock_contract_pages_and_dedup(self):
        settings.linkedin_mock_comments_json = json.dumps(
            {
                "post-1": {
                    "pages": [
                        [
                            {"linkedin_comment_id": "c-1", "commenter_name": "A", "comment_text": "one"},
                            {"linkedin_comment_id": "c-2", "commenter_name": "B", "comment_text": "two"},
                        ],
                        [
                            {"linkedin_comment_id": "c-2", "commenter_name": "B", "comment_text": "two-dupe"},
                            {"linkedin_comment_id": "c-3", "commenter_name": "C", "comment_text": "three"},
                        ],
                    ]
                }
            }
        )

        comments = fetch_recent_comments_for_post("post-1")
        self.assertEqual([c.linkedin_comment_id for c in comments], ["c-1", "c-2", "c-3"])

    def test_api_contract_pagination(self):
        settings.linkedin_api_mode = "api"
        settings.linkedin_api_token = "dummy"
        settings.linkedin_mock_comments_json = ""

        responses = [
            {
                "elements": [
                    {"id": "c-10", "message": "first", "actor": {"name": "Alex"}},
                ],
                "paging": {"nextStart": 1},
            },
            {
                "elements": [
                    {"id": "c-11", "message": "second", "actor": {"name": "Busi"}},
                ],
                "paging": {},
            },
        ]

        call_count = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            idx = call_count["n"]
            call_count["n"] += 1
            return httpx.Response(200, json=responses[idx])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            comments = fetch_recent_comments_for_post("post-contract", _client=client)
        finally:
            client.close()

        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].linkedin_comment_id, "c-10")
        self.assertEqual(comments[1].linkedin_comment_id, "c-11")

    def test_api_auth_error(self):
        settings.linkedin_api_mode = "api"
        settings.linkedin_api_token = "dummy"
        settings.linkedin_mock_comments_json = ""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, text="unauthorized")

        client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            with self.assertRaises(LinkedInAuthError):
                fetch_recent_comments_for_post("post-auth", _client=client)
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
