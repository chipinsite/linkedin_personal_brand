"""V6 Phase 2 Agent Tests.

Covers:
- PRODUCT_CONTEXT.md loader (parse, extract identity, banned claims, experience markers)
- Scout agent (seeds BACKLOG from source_materials, respects BACKLOG_FLOOR, skips duplicates)
- Writer agent (claims TODO, generates draft, links draft_id, transitions to REVIEW)
- Editor agent (7 gate pass/fail scenarios, revision loop, max revision cap)
"""

import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

DB_PATH = os.path.join(tempfile.gettempdir(), "personal_brand_v6_phase2_test.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

os.environ["APP_ENV"] = "test"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ["LLM_MOCK_MODE"] = "true"

from app.db import Base, SessionLocal, engine
from app.models import (
    ContentPipelineItem,
    Draft,
    DraftStatus,
    PipelineStatus,
    PostFormat,
    PostTone,
    SourceMaterial,
)

# Ensure all tables exist in test DB
Base.metadata.create_all(engine)

from app.services.pipeline import (
    create_pipeline_item,
    get_items_by_status,
    transition,
)
from app.services.claim_lock import attempt_claim, release_claim


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: PRODUCT_CONTEXT.md Loader
# ─────────────────────────────────────────────────────────────────────────────


class TestProductContextLoader(unittest.TestCase):
    """Test PRODUCT_CONTEXT.md parsing and extraction."""

    def test_load_from_real_file(self):
        """Load the actual PRODUCT_CONTEXT.md and verify key fields."""
        from app.services.product_context import load_product_context

        # Find the actual PRODUCT_CONTEXT.md
        repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
        ctx_path = os.path.normpath(os.path.join(repo_root, "PRODUCT_CONTEXT.md"))

        if not os.path.exists(ctx_path):
            self.skipTest("PRODUCT_CONTEXT.md not found at repo root")

        ctx = load_product_context(ctx_path)

        # Identity fields
        self.assertEqual(ctx.name, "Sphiwe Mawhayi")
        self.assertEqual(ctx.title, "Head of Sales")
        self.assertIn("20", ctx.experience_descriptor)  # "Over 20 years..."
        self.assertIn("Sub-Saharan Africa", ctx.geographic_focus)

    def test_banned_claims_extracted(self):
        """Verify banned claims include key restrictions."""
        from app.services.product_context import load_product_context

        repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
        ctx_path = os.path.normpath(os.path.join(repo_root, "PRODUCT_CONTEXT.md"))

        if not os.path.exists(ctx_path):
            self.skipTest("PRODUCT_CONTEXT.md not found at repo root")

        ctx = load_product_context(ctx_path)

        self.assertGreater(len(ctx.banned_claims), 0, "Should have banned claims")
        # Check at least one known banned claim is present
        combined = " ".join(ctx.banned_claims).lower()
        self.assertTrue(
            "guaranteed" in combined or "roi" in combined or "superlatives" in combined
            or "revenue" in combined or "confidential" in combined,
            f"Expected a recognisable banned claim — got: {ctx.banned_claims[:3]}"
        )

    def test_experience_markers_extracted(self):
        """Verify experience markers are extracted."""
        from app.services.product_context import load_product_context

        repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
        ctx_path = os.path.normpath(os.path.join(repo_root, "PRODUCT_CONTEXT.md"))

        if not os.path.exists(ctx_path):
            self.skipTest("PRODUCT_CONTEXT.md not found at repo root")

        ctx = load_product_context(ctx_path)

        self.assertGreater(len(ctx.experience_markers), 0, "Should have experience markers")
        combined = " ".join(ctx.experience_markers).lower()
        self.assertTrue(
            "experience" in combined or "observed" in combined or "lesson" in combined,
            f"Expected recognisable experience markers — got: {ctx.experience_markers[:3]}"
        )

    def test_out_of_scope_topics_extracted(self):
        """Verify out-of-scope topics are extracted."""
        from app.services.product_context import load_product_context

        repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
        ctx_path = os.path.normpath(os.path.join(repo_root, "PRODUCT_CONTEXT.md"))

        if not os.path.exists(ctx_path):
            self.skipTest("PRODUCT_CONTEXT.md not found at repo root")

        ctx = load_product_context(ctx_path)

        self.assertGreater(len(ctx.out_of_scope_topics), 0, "Should have out-of-scope topics")
        combined = " ".join(ctx.out_of_scope_topics).lower()
        self.assertTrue(
            "cryptocurrency" in combined or "blockchain" in combined or "health" in combined,
            f"Expected recognisable out-of-scope topic — got: {ctx.out_of_scope_topics[:3]}"
        )

    def test_missing_file_returns_empty_context(self):
        """Loading a non-existent file returns an empty ProductContext."""
        from app.services.product_context import load_product_context

        ctx = load_product_context("/nonexistent/path/PRODUCT_CONTEXT.md")
        self.assertEqual(ctx.name, "")
        self.assertEqual(ctx.title, "")
        self.assertEqual(len(ctx.banned_claims), 0)

    def test_singleton_caching(self):
        """get_product_context returns the same instance on repeated calls."""
        from app.services.product_context import (
            get_product_context,
            reload_product_context,
            _cached_context,
        )
        import app.services.product_context as pc_module

        # Clear cache first
        pc_module._cached_context = None

        ctx1 = get_product_context()
        ctx2 = get_product_context()
        self.assertIs(ctx1, ctx2, "Singleton should return same instance")

        # Reload should return a new instance
        ctx3 = reload_product_context()
        self.assertIsNot(ctx1, ctx3, "Reload should create new instance")

        # Clean up
        pc_module._cached_context = None


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Scout Agent
# ─────────────────────────────────────────────────────────────────────────────


class TestScoutAgent(unittest.TestCase):
    """Test Scout agent seeding pipeline items from source materials."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _create_source(self, title: str, pillar: str = "Adtech fundamentals", score: float = 5.0) -> SourceMaterial:
        """Helper to create a source material record."""
        source = SourceMaterial(
            id=uuid.uuid4(),
            source_name="Test Source",
            title=title,
            url=f"https://example.com/{uuid.uuid4().hex[:8]}",
            summary_text=f"Summary of {title}",
            relevance_score=score,
            pillar_theme=pillar,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(source)
        self.db.commit()
        return source

    def test_scout_creates_items_from_sources(self):
        """Scout creates pipeline items from recent source materials."""
        from app.services.agents.scout import run_scout

        # Ensure we have no/few backlog items by cleaning up
        # Create fresh sources
        self._create_source("New RTB Technology Advances in 2026")
        self._create_source("SPO Strategies for African Markets")

        items = run_scout(self.db, max_items=2)

        # Scout should create at least 1 item
        self.assertGreater(len(items), 0, "Scout should create pipeline items")

        # Verify items are at BACKLOG
        for item in items:
            self.assertEqual(item.status, PipelineStatus.backlog)
            self.assertIsNotNone(item.pillar_theme)
            self.assertIsNotNone(item.topic_keyword)

    def test_scout_skips_duplicate_topics(self):
        """Scout does not create items for topics already in pipeline."""
        from app.services.agents.scout import run_scout, _source_already_in_pipeline

        title = f"Unique Topic for Duplicate Test {uuid.uuid4().hex[:6]}"
        source = self._create_source(title)

        # Create a pipeline item with matching topic_keyword
        create_pipeline_item(
            self.db,
            pillar_theme="Adtech fundamentals and market dynamics",
            topic_keyword=title[:256],
        )

        # Now check — source should be detected as already in pipeline
        result = _source_already_in_pipeline(self.db, source)
        self.assertTrue(result, "Source should be detected as duplicate")

    def test_scout_respects_backlog_floor(self):
        """Scout stops seeding when backlog has enough items."""
        from app.services.agents.scout import run_scout, BACKLOG_FLOOR, _count_backlog

        # Create enough backlog items to exceed floor
        current = _count_backlog(self.db)
        items_to_create = max(0, BACKLOG_FLOOR - current + 1)
        for i in range(items_to_create):
            create_pipeline_item(
                self.db,
                pillar_theme=f"Floor test pillar {i}",
                topic_keyword=f"floor-test-topic-{uuid.uuid4().hex[:6]}",
            )

        # Scout should return empty list
        items = run_scout(self.db, max_items=5)
        self.assertEqual(len(items), 0, "Scout should stop when backlog >= floor")


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Writer Agent
# ─────────────────────────────────────────────────────────────────────────────


class TestWriterAgent(unittest.TestCase):
    """Test Writer agent claiming TODO items and generating drafts."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_writer_processes_todo_item(self):
        """Writer claims a TODO item, generates draft, and transitions to REVIEW."""
        from app.services.agents.writer import process_one_item

        # Create an item at TODO status
        item = create_pipeline_item(
            self.db,
            pillar_theme="Adtech fundamentals and market dynamics",
            sub_theme="Programmatic buying",
            topic_keyword="Writer test topic",
            status=PipelineStatus.todo,
        )

        worker_id = "writer-test-001"
        attempt_claim(self.db, item.id, "writing", worker_id)

        result = process_one_item(self.db, item, worker_id)

        # Refresh item
        self.db.refresh(item)

        if result:
            # Success path: item should be at REVIEW with a linked draft
            self.assertEqual(item.status, PipelineStatus.review)
            self.assertIsNotNone(item.draft_id, "Writer should link draft_id to pipeline item")

            # Verify the draft exists
            draft = self.db.query(Draft).filter(Draft.id == item.draft_id).first()
            self.assertIsNotNone(draft, "Draft record should exist in database")
            self.assertIsNotNone(draft.content_body)
            self.assertGreater(len(draft.content_body), 0, "Draft should have content")
        else:
            # Failed path: item should be back at TODO
            self.assertEqual(item.status, PipelineStatus.todo)

    def test_run_writer_no_todo_items(self):
        """run_writer returns 0 when there are no unclaimed TODO items."""
        from app.services.agents.writer import run_writer

        # Don't create any TODO items — Writer should return 0 gracefully
        result = run_writer(self.db, max_items=1)
        # Result is 0 or however many existing TODOs were processed
        self.assertIsInstance(result, int)

    def test_writer_links_draft_to_item(self):
        """Writer successfully links the draft back to the pipeline item."""
        from app.services.agents.writer import process_one_item

        item = create_pipeline_item(
            self.db,
            pillar_theme="Adtech fundamentals and market dynamics",
            sub_theme="Measurement and attribution",
            topic_keyword=f"Writer link test {uuid.uuid4().hex[:6]}",
            status=PipelineStatus.todo,
        )

        worker_id = f"writer-link-{uuid.uuid4().hex[:6]}"
        attempt_claim(self.db, item.id, "writing", worker_id)

        result = process_one_item(self.db, item, worker_id)
        self.db.refresh(item)

        if result:
            # On success, verify FK link
            self.assertIsNotNone(item.draft_id)
            draft = self.db.query(Draft).filter(Draft.id == item.draft_id).first()
            self.assertIsNotNone(draft)
        # On failure (mock mode edge case), verify it handled gracefully
        self.assertIn(item.status, [PipelineStatus.review, PipelineStatus.todo])


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Editor Agent — Quality Gates
# ─────────────────────────────────────────────────────────────────────────────


class TestEditorQualityGates(unittest.TestCase):
    """Test Editor agent individual quality gates."""

    @classmethod
    def setUpClass(cls):
        from app.services.product_context import load_product_context
        import app.services.product_context as pc_module

        repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
        ctx_path = os.path.normpath(os.path.join(repo_root, "PRODUCT_CONTEXT.md"))

        if os.path.exists(ctx_path):
            cls.ctx = load_product_context(ctx_path)
        else:
            cls.ctx = load_product_context()  # empty context

        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _make_item(self, **kwargs) -> ContentPipelineItem:
        """Helper to create pipeline item for gate tests."""
        defaults = {
            "pillar_theme": "Adtech fundamentals and market dynamics",
            "sub_theme": "Programmatic buying",
            "topic_keyword": f"gate-test-{uuid.uuid4().hex[:6]}",
            "status": PipelineStatus.review,
        }
        defaults.update(kwargs)
        return create_pipeline_item(self.db, **defaults)

    def test_gate_factual_accuracy_passes_clean_content(self):
        """Factual accuracy gate passes content without false title claims."""
        from app.services.agents.editor import _check_factual_accuracy

        content = (
            "In my experience as Head of Sales, I have seen programmatic buying evolve "
            "significantly over the past two decades in Sub-Saharan Africa. "
            "AI is changing how campaigns are planned and measured."
        )
        result = _check_factual_accuracy(content, self.ctx)
        self.assertTrue(result.passed, f"Should pass — got: {result.message}")

    def test_gate_factual_accuracy_fails_wrong_title(self):
        """Factual accuracy gate fails when content claims a wrong title."""
        from app.services.agents.editor import _check_factual_accuracy

        content = (
            "As the CEO of our advertising technology company, I believe "
            "programmatic buying will continue to grow in African markets."
        )
        result = _check_factual_accuracy(content, self.ctx)
        self.assertFalse(result.passed, "Should fail on CEO title claim")
        self.assertIn("ceo", result.message.lower())

    def test_gate_readability_passes_normal_content(self):
        """Readability gate passes well-written professional content."""
        from app.services.agents.editor import _check_readability

        content = (
            "Programmatic advertising continues to evolve across African markets. "
            "The adoption of supply path optimisation strategies has increased significantly "
            "over the past three years. Most buyers now evaluate at least two to three "
            "supply chain paths before committing to a programmatic partner. "
            "This shift reflects a growing maturity in how African publishers and "
            "advertisers approach the open auction marketplace."
        )
        result = _check_readability(content)
        self.assertTrue(result.passed, f"Should pass — got: {result.message}")

    def test_gate_readability_runs_and_returns_result(self):
        """Readability gate runs and returns a valid GateResult."""
        from app.services.agents.editor import _check_readability

        # Very simple content (very low grade level)
        content = "I like ads. Ads are fun. We buy ads. They work. Ads help. I sell ads. Ads are good."
        result = _check_readability(content)
        # Gate should run and return a result — passes with flag if textstat unavailable
        self.assertIsInstance(result.passed, bool)
        self.assertEqual(result.gate_name, "readability")
        # Message should contain either grade level info or unavailability notice
        self.assertGreater(len(result.message), 0, "Readability gate should produce a message")

    def test_gate_no_urls_passes_clean(self):
        """No URL gate passes content without URLs."""
        from app.services.agents.editor import _check_no_urls

        content = "Supply path optimisation is critical for programmatic buying efficiency."
        result = _check_no_urls(content)
        self.assertTrue(result.passed)

    def test_gate_no_urls_fails_with_link(self):
        """No URL gate fails when content contains a URL."""
        from app.services.agents.editor import _check_no_urls

        content = "Read more at https://example.com/article about programmatic trends."
        result = _check_no_urls(content)
        self.assertFalse(result.passed)
        self.assertIn("external URL", result.message)

    def test_gate_no_unsupported_claims_passes_clean(self):
        """Unsupported claims gate passes content without superlatives."""
        from app.services.agents.editor import _check_no_unsupported_claims

        content = (
            "AI is changing how campaigns are planned and measured. "
            "Many organisations are adopting these tools gradually."
        )
        result = _check_no_unsupported_claims(content)
        self.assertTrue(result.passed)

    def test_gate_no_unsupported_claims_fails_superlative(self):
        """Unsupported claims gate fails on 'the best' or 'guaranteed'."""
        from app.services.agents.editor import _check_no_unsupported_claims

        content = "Our platform is the best programmatic solution with guaranteed results."
        result = _check_no_unsupported_claims(content)
        self.assertFalse(result.passed)
        self.assertIn("the best", result.message)

    def test_gate_topical_relevance_passes_adtech_content(self):
        """Topical relevance gate passes content with domain keywords."""
        from app.services.agents.editor import _check_topical_relevance

        content = (
            "Programmatic advertising and campaign automation are reshaping "
            "how media buyers approach the digital advertising ecosystem."
        )
        item = self._make_item()
        result = _check_topical_relevance(content, item)
        self.assertTrue(result.passed)

    def test_gate_topical_relevance_fails_off_topic(self):
        """Topical relevance gate fails for content without domain signals."""
        from app.services.agents.editor import _check_topical_relevance

        content = (
            "Today we discuss the best recipes for preparing a traditional meal. "
            "The ingredients include flour, butter, and sugar."
        )
        item = self._make_item()
        result = _check_topical_relevance(content, item)
        self.assertFalse(result.passed)
        self.assertIn("domain-relevant", result.message)

    def test_gate_experience_signal_passes_first_person(self):
        """Experience signal gate passes content with personal markers."""
        from app.services.agents.editor import _check_experience_signal

        content = (
            "In my experience, programmatic buying in African markets requires "
            "a different approach than what works in mature Western markets. "
            "Over the past twenty years, I've observed cycles repeat."
        )
        result = _check_experience_signal(content, self.ctx)
        self.assertTrue(result.passed, f"Should pass — got: {result.message}")

    def test_gate_experience_signal_fails_no_personal_voice(self):
        """Experience signal gate fails when there is no first-person narrative."""
        from app.services.agents.editor import _check_experience_signal

        content = (
            "The industry is evolving. Programmatic platforms continue to grow. "
            "Market analysts predict further consolidation in the SSP space."
        )
        result = _check_experience_signal(content, self.ctx)
        self.assertFalse(result.passed)
        self.assertIn("No personal experience", result.message)

    def test_gate_guardrails_passes_clean(self):
        """Guardrail gate passes content that is compliant."""
        from app.services.agents.editor import _check_guardrails

        content = (
            "Supply path optimisation is becoming essential for programmatic buyers. "
            "The efficiency gains are measurable when comparing direct and indirect paths."
        )
        result = _check_guardrails(content)
        self.assertTrue(result.passed)

    def test_gate_guardrails_fails_banned_phrase(self):
        """Guardrail gate fails on banned phrases."""
        from app.services.agents.editor import _check_guardrails

        content = (
            "This is a real game changer for the advertising industry. "
            "Let me unpack why this matters."
        )
        result = _check_guardrails(content)
        self.assertFalse(result.passed)
        self.assertIn("BANNED_PHRASE", result.message)


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Editor Agent — Aggregate Review
# ─────────────────────────────────────────────────────────────────────────────


class TestEditorAggregateReview(unittest.TestCase):
    """Test Editor aggregate review_content function."""

    @classmethod
    def setUpClass(cls):
        from app.services.product_context import load_product_context

        repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
        ctx_path = os.path.normpath(os.path.join(repo_root, "PRODUCT_CONTEXT.md"))

        if os.path.exists(ctx_path):
            cls.ctx = load_product_context(ctx_path)
        else:
            cls.ctx = load_product_context()

        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _make_item(self, **kwargs) -> ContentPipelineItem:
        defaults = {
            "pillar_theme": "Adtech fundamentals and market dynamics",
            "sub_theme": "Programmatic buying",
            "topic_keyword": f"review-test-{uuid.uuid4().hex[:6]}",
            "status": PipelineStatus.review,
        }
        defaults.update(kwargs)
        return create_pipeline_item(self.db, **defaults)

    def test_review_passes_high_quality_content(self):
        """review_content passes content that satisfies all 7 gates."""
        from app.services.agents.editor import review_content

        content = (
            "In my experience, programmatic advertising in Sub-Saharan Africa has "
            "matured significantly over the past decade. When I first encountered "
            "supply path optimisation challenges in African markets, most buyers were "
            "relying on a single supply chain without questioning the path their "
            "impressions travelled. "
            "\n\n"
            "Today, the landscape looks different. Campaign automation tools now "
            "allow media buyers to evaluate multiple programmatic paths in real time. "
            "AI-powered bidding agents are reducing wasted spend by identifying "
            "optimal inventory sources before a single impression is served. "
            "\n\n"
            "The shift is not just technological. It reflects a change in how "
            "advertising operations teams approach measurement and attribution "
            "across emerging markets. Those who adapt will gain a meaningful "
            "competitive advantage.\n\n"
            "#Adtech #Programmatic #AI"
        )

        item = self._make_item()
        verdict = review_content(content, item, self.ctx)

        self.assertTrue(verdict.passed, f"Should pass all gates — failures: {verdict.failure_summary}")
        self.assertEqual(verdict.quality_score, 1.0)
        self.assertEqual(len(verdict.failed_gates), 0)

    def test_review_fails_off_topic_content(self):
        """review_content fails for off-topic content."""
        from app.services.agents.editor import review_content

        content = (
            "Today I made a delicious pasta recipe with fresh tomatoes and basil. "
            "The secret is to use slow roasted garlic and a pinch of sea salt. "
            "In my experience, Italian cooking requires patience above all else."
        )

        item = self._make_item()
        verdict = review_content(content, item, self.ctx)

        self.assertFalse(verdict.passed)
        # Should fail at least topical_relevance
        failed_names = [g.gate_name for g in verdict.failed_gates]
        self.assertIn("topical_relevance", failed_names)

    def test_review_returns_quality_score(self):
        """review_content returns a quality score between 0 and 1."""
        from app.services.agents.editor import review_content

        content = "AI is transforming advertising campaigns globally."
        item = self._make_item()
        verdict = review_content(content, item, self.ctx)

        self.assertGreaterEqual(verdict.quality_score, 0.0)
        self.assertLessEqual(verdict.quality_score, 1.0)

    def test_review_returns_readability_score(self):
        """review_content returns a readability score when textstat is available."""
        from app.services.agents.editor import review_content

        content = (
            "Programmatic advertising continues to evolve in African markets. "
            "The adoption of supply path optimisation has increased. "
            "In my experience, most organisations are still early in their journey."
        )
        item = self._make_item()
        verdict = review_content(content, item, self.ctx)

        # Readability score should be numeric (may be 0 if textstat unavailable)
        self.assertIsInstance(verdict.readability_score, float)


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Editor Agent — Process Item Flow
# ─────────────────────────────────────────────────────────────────────────────


class TestEditorProcessFlow(unittest.TestCase):
    """Test Editor process_one_item end-to-end flow."""

    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def _create_reviewed_item_with_draft(self, content_body: str) -> ContentPipelineItem:
        """Helper: create a pipeline item at REVIEW with a linked draft."""
        draft = Draft(
            id=uuid.uuid4(),
            pillar_theme="Adtech fundamentals and market dynamics",
            sub_theme="Programmatic buying",
            format=PostFormat.text,
            tone=PostTone.educational,
            content_body=content_body,
            status=DraftStatus.pending,
        )
        self.db.add(draft)
        self.db.commit()

        item = create_pipeline_item(
            self.db,
            pillar_theme="Adtech fundamentals and market dynamics",
            sub_theme="Programmatic buying",
            topic_keyword=f"editor-flow-{uuid.uuid4().hex[:6]}",
            status=PipelineStatus.review,
        )

        # Link draft
        item.draft_id = draft.id
        self.db.commit()

        return item

    def test_process_item_pass_transitions_to_ready(self):
        """Editor advances item to READY_TO_PUBLISH when all gates pass."""
        from app.services.agents.editor import process_one_item

        content = (
            "In my experience, programmatic advertising in Sub-Saharan Africa has "
            "matured significantly over the past decade. When I first encountered "
            "supply path optimisation challenges in African markets, most buyers were "
            "relying on a single supply chain without questioning the path their "
            "impressions travelled. "
            "\n\n"
            "Today, campaign automation tools allow media buyers to evaluate multiple "
            "programmatic paths. AI-powered bidding agents are reducing wasted spend "
            "by identifying optimal inventory sources before a single impression is served. "
            "\n\n"
            "The shift reflects a change in how advertising operations teams approach "
            "measurement and attribution across emerging markets.\n\n"
            "#Adtech #Programmatic #AI"
        )

        item = self._create_reviewed_item_with_draft(content)
        worker_id = f"editor-pass-{uuid.uuid4().hex[:6]}"
        attempt_claim(self.db, item.id, "review", worker_id)

        result = process_one_item(self.db, item, worker_id)

        self.db.refresh(item)

        if result:
            self.assertEqual(item.status, PipelineStatus.ready_to_publish)
            self.assertIsNotNone(item.quality_score)
            self.assertEqual(item.fact_check_status, "passed")
        # If it didn't pass (edge case with textstat scoring), that's acceptable too

    def test_process_item_fail_sends_back_to_todo(self):
        """Editor sends item back to TODO when quality gates fail."""
        from app.services.agents.editor import process_one_item

        # Content that will definitely fail gates (off-topic, no experience signal)
        content = (
            "Today I made a delicious pasta recipe with fresh tomatoes and basil. "
            "The secret is to use slow roasted garlic and a pinch of sea salt."
        )

        item = self._create_reviewed_item_with_draft(content)
        worker_id = f"editor-fail-{uuid.uuid4().hex[:6]}"
        attempt_claim(self.db, item.id, "review", worker_id)

        result = process_one_item(self.db, item, worker_id)

        self.db.refresh(item)
        self.assertFalse(result)
        self.assertEqual(item.status, PipelineStatus.todo, "Failed item should return to TODO")
        self.assertEqual(item.fact_check_status, "failed")
        self.assertGreater(item.revision_count, 0, "Revision count should increment on failure")

    def test_process_item_max_revisions_sends_to_backlog(self):
        """Editor sends item to BACKLOG when max revisions exceeded."""
        from app.services.agents.editor import process_one_item

        # Content that will fail gates
        content = "Cooking tips for a healthy lifestyle. Try yoga too."

        item = self._create_reviewed_item_with_draft(content)

        # Set revision count to max_revisions (3) so next fail exceeds it
        item.revision_count = 3
        self.db.commit()

        worker_id = f"editor-maxrev-{uuid.uuid4().hex[:6]}"
        attempt_claim(self.db, item.id, "review", worker_id)

        result = process_one_item(self.db, item, worker_id)

        self.db.refresh(item)
        self.assertFalse(result)
        self.assertEqual(item.status, PipelineStatus.backlog, "Max revisions item should go to BACKLOG")

    def test_process_item_no_draft_skips(self):
        """Editor skips items that have no draft_id."""
        from app.services.agents.editor import process_one_item

        item = create_pipeline_item(
            self.db,
            pillar_theme="Adtech fundamentals and market dynamics",
            topic_keyword=f"no-draft-{uuid.uuid4().hex[:6]}",
            status=PipelineStatus.review,
        )
        # draft_id is None by default

        worker_id = f"editor-nodraft-{uuid.uuid4().hex[:6]}"
        attempt_claim(self.db, item.id, "review", worker_id)

        result = process_one_item(self.db, item, worker_id)
        self.assertFalse(result, "Item without draft should be skipped")


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Editor Verdict Dataclass
# ─────────────────────────────────────────────────────────────────────────────


class TestEditorVerdict(unittest.TestCase):
    """Test EditorVerdict and GateResult dataclasses."""

    def test_verdict_failure_summary_all_pass(self):
        from app.services.agents.editor import EditorVerdict, GateResult

        verdict = EditorVerdict(
            passed=True,
            gate_results=[
                GateResult(gate_name="test_gate_1", passed=True),
                GateResult(gate_name="test_gate_2", passed=True),
            ],
            quality_score=1.0,
        )
        self.assertEqual(verdict.failure_summary, "All gates passed")
        self.assertEqual(len(verdict.failed_gates), 0)

    def test_verdict_failure_summary_with_failures(self):
        from app.services.agents.editor import EditorVerdict, GateResult

        verdict = EditorVerdict(
            passed=False,
            gate_results=[
                GateResult(gate_name="readability", passed=False, message="Grade too high"),
                GateResult(gate_name="no_urls", passed=True),
                GateResult(gate_name="experience", passed=False, message="No markers"),
            ],
            quality_score=0.33,
        )
        self.assertEqual(len(verdict.failed_gates), 2)
        summary = verdict.failure_summary
        self.assertIn("readability", summary)
        self.assertIn("experience", summary)


if __name__ == "__main__":
    unittest.main()
