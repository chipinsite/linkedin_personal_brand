"""Tests for v5.0 AI Content Generation Engine.

Validates:
- Content pyramid structure
- Topic selection with recent sub-theme avoidance
- Format and tone weighted selection
- LLM client mock mode behavior
- Draft generation workflow
- Guardrail validation integration
- Content API endpoints
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v15_test.db")
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
os.environ["LLM_MOCK_MODE"] = "true"

from fastapi.testclient import TestClient

from app.db import SessionLocal, engine
from app.main import app
from app.models import Draft, DraftStatus, PostFormat, PostTone, PublishedPost


class ContentPyramidStructureTest(unittest.TestCase):
    """Tests for content pyramid data structure."""

    def test_pillar_themes_count(self):
        from app.services.content_pyramid import PILLAR_THEMES

        self.assertEqual(len(PILLAR_THEMES), 3)
        self.assertIn("Adtech fundamentals and market dynamics", PILLAR_THEMES)
        self.assertIn("Agentic AI applications in advertising technology", PILLAR_THEMES)
        self.assertIn("Artificial intelligence in advertising operations and strategy", PILLAR_THEMES)

    def test_sub_themes_per_pillar(self):
        from app.services.content_pyramid import PILLAR_SUB_THEMES

        for pillar, sub_themes in PILLAR_SUB_THEMES.items():
            self.assertGreaterEqual(len(sub_themes), 4)
            self.assertLessEqual(len(sub_themes), 6)

    def test_post_angles_count(self):
        from app.services.content_pyramid import POST_ANGLES

        self.assertEqual(len(POST_ANGLES), 8)

    def test_post_angle_structure(self):
        from app.services.content_pyramid import POST_ANGLES

        for angle in POST_ANGLES:
            self.assertIsNotNone(angle.id)
            self.assertIsNotNone(angle.name)
            self.assertIsNotNone(angle.description)
            self.assertIsNotNone(angle.prompt_guidance)


class TopicSelectionTest(unittest.TestCase):
    """Tests for topic selection logic."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    def test_select_topic_returns_valid_combination(self):
        from app.services.content_pyramid import PILLAR_SUB_THEMES, select_topic

        topic = select_topic(self.db)

        self.assertIn(topic.pillar_theme, PILLAR_SUB_THEMES.keys())
        self.assertIn(topic.sub_theme, PILLAR_SUB_THEMES[topic.pillar_theme])
        self.assertIsNotNone(topic.post_angle)

    def test_select_topic_avoids_recent_sub_themes(self):
        from app.services.content_pyramid import select_topic

        # Create a published post from today
        draft = Draft(
            pillar_theme="Adtech fundamentals and market dynamics",
            sub_theme="Programmatic buying",
            format=PostFormat.text,
            tone=PostTone.educational,
            content_body="Test content for programmatic buying",
            status=DraftStatus.approved,
            guardrail_check_passed=True,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        published = PublishedPost(
            draft_id=draft.id,
            published_at=datetime.now(timezone.utc),
            content_body=draft.content_body,
            format=draft.format,
            tone=draft.tone,
        )
        self.db.add(published)
        self.db.commit()

        # Run topic selection multiple times
        selections = [select_topic(self.db) for _ in range(10)]

        # Should not select "Programmatic buying" as it was used recently
        selected_sub_themes = [s.sub_theme for s in selections]
        self.assertNotIn("Programmatic buying", selected_sub_themes)


class WeightedSelectionTest(unittest.TestCase):
    """Tests for format and tone weighted selection."""

    def test_default_format_weights_sum_to_one(self):
        from app.services.content_engine import DEFAULT_FORMAT_WEIGHTS

        total = sum(DEFAULT_FORMAT_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_default_tone_weights_sum_to_one(self):
        from app.services.content_engine import DEFAULT_TONE_WEIGHTS

        total = sum(DEFAULT_TONE_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_select_format_returns_valid_format(self):
        from app.services.content_engine import select_format

        for _ in range(10):
            fmt = select_format()
            self.assertIn(fmt, PostFormat)

    def test_select_tone_returns_valid_tone(self):
        from app.services.content_engine import select_tone

        for _ in range(10):
            tone = select_tone()
            self.assertIn(tone, PostTone)


class LLMClientMockModeTest(unittest.TestCase):
    """Tests for LLM client mock mode behavior."""

    def test_mock_mode_enabled_without_api_key(self):
        from app.services.llm_client import is_mock_mode

        self.assertTrue(is_mock_mode())

    def test_mock_response_structure(self):
        from app.services.llm_client import generate_text

        response = generate_text(
            user_prompt="Generate a test post about programmatic buying",
            system_prompt="You are a LinkedIn content writer.",
        )

        self.assertTrue(response.is_mock)
        self.assertIsNotNone(response.content)
        self.assertGreater(len(response.content), 0)
        self.assertGreater(response.total_tokens, 0)

    def test_mock_response_contains_expected_structure(self):
        from app.services.llm_client import generate_text

        response = generate_text(
            user_prompt="Write a post about AI bidding agents",
            system_prompt="You are a LinkedIn content writer.",
        )

        # Mock response should contain meaningful content
        self.assertIn("#", response.content)  # Should have hashtags


class DraftGenerationWorkflowTest(unittest.TestCase):
    """Tests for the full draft generation workflow."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()

    def test_generate_draft_creates_record(self):
        from app.services.content_engine import generate_draft

        result = generate_draft(self.db)

        self.assertIsNotNone(result.draft)
        self.assertIsNotNone(result.draft.id)
        self.assertIsNotNone(result.draft.content_body)
        self.assertIn(result.draft.format, PostFormat)
        self.assertIn(result.draft.tone, PostTone)

    def test_generate_draft_passes_guardrails_in_mock_mode(self):
        from app.services.content_engine import generate_draft

        result = generate_draft(self.db)

        # Mock mode generates compliant content
        self.assertTrue(result.success)
        self.assertTrue(result.draft.guardrail_check_passed)
        self.assertLessEqual(result.attempts, 3)

    def test_generate_draft_with_overrides(self):
        from app.services.content_engine import generate_draft

        result = generate_draft(
            self.db,
            pillar_override="Adtech fundamentals and market dynamics",
            sub_theme_override="Retail media",
            format_override=PostFormat.image,
            tone_override=PostTone.opinionated,
        )

        self.assertEqual(result.draft.pillar_theme, "Adtech fundamentals and market dynamics")
        self.assertEqual(result.draft.sub_theme, "Retail media")
        self.assertEqual(result.draft.format, PostFormat.image)
        self.assertEqual(result.draft.tone, PostTone.opinionated)


class ContentAPIEndpointsTest(unittest.TestCase):
    """Tests for content API endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_generate_draft_endpoint(self):
        response = self.client.post(
            "/content/generate-draft",
            json={},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["draft"])
        self.assertLessEqual(data["attempts"], 3)

    def test_generate_draft_endpoint_with_overrides(self):
        response = self.client.post(
            "/content/generate-draft",
            json={
                "pillar_override": "Agentic AI applications in advertising technology",
                "sub_theme_override": "AI bidding agents",
                "format_override": "CAROUSEL",
                "tone_override": "DIRECT",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["draft"]["pillar_theme"], "Agentic AI applications in advertising technology")
        self.assertEqual(data["draft"]["sub_theme"], "AI bidding agents")
        self.assertEqual(data["draft"]["format"], "CAROUSEL")
        self.assertEqual(data["draft"]["tone"], "DIRECT")

    def test_pyramid_endpoint(self):
        response = self.client.get("/content/pyramid")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data["pillars"]), 3)
        self.assertEqual(len(data["post_angles"]), 8)
        self.assertIn("Adtech fundamentals and market dynamics", data["sub_themes"])

    def test_weights_endpoint(self):
        response = self.client.get("/content/weights")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("format_weights", data)
        self.assertIn("tone_weights", data)
        # Weights use enum values (uppercase)
        self.assertIn("TEXT", data["format_weights"])
        self.assertIn("EDUCATIONAL", data["tone_weights"])


class BrandVoiceRulesTest(unittest.TestCase):
    """Tests for brand voice and banned phrases."""

    def test_banned_phrases_defined(self):
        from app.services.content_engine import BANNED_PHRASES

        self.assertIn("game changer", BANNED_PHRASES)
        self.assertIn("synergy", BANNED_PHRASES)
        self.assertIn("leverage", BANNED_PHRASES)

    def test_brand_voice_rules_defined(self):
        from app.services.content_engine import BRAND_VOICE_RULES

        self.assertIn("first person singular", BRAND_VOICE_RULES.lower())
        self.assertIn("complete sentences", BRAND_VOICE_RULES.lower())


if __name__ == "__main__":
    unittest.main()
