# LinkedIn Personal Brand V6 Execution Plan

## Scope Lock

This V6 build is strictly for **LinkedIn personal brand operations**.

### In scope
- LinkedIn content ideation, drafting, review, approval, publish support, and performance learning.
- LinkedIn-native distribution workflows (post optimization, engagement loops, comment operations).
- LinkedIn-specific quality gates, analytics, and operational controls.
- Domain focus locked to:
  - Adtech
  - Retail Media
  - AI ad platforms
  - Personal operating lessons from 20+ years of commercial work experience

### Out of scope (hard no for V6)
- Multi-platform publishing abstractions.
- X/Twitter, Instagram, TikTok, YouTube, Reddit, Facebook workflows.
- Generic “social channel” architecture.
- Any UI or backend naming that implies cross-platform support.

## V6 Goal

Upgrade from v5.5 to a reliable, autonomous-enough **LinkedIn-only** pipeline with specialist agents, strict quality gates, and claim-locking safety under concurrency.

## LinkedIn Positioning Lock (Content Strategy)

All generated content and topic selection must stay inside this identity:
- Senior practitioner voice grounded in 20+ years of experience.
- Core subject areas: Adtech, Retail Media, AI ad platform execution.
- Practical, operator-level insights over generic thought leadership.
- Personal lessons, field-tested frameworks, and execution tradeoffs over hype narratives.

Content outside this positioning is treated as out-of-scope and rejected by Editor.

## Current Repo Baseline (already implemented)

- Backend: FastAPI + SQLAlchemy + Alembic + Celery + Redis.
- Existing content generation, guardrails, draft approval flow, Telegram ops, audit logging.
- Existing models for drafts, published posts, comments, learning metrics.
- Production on Railway with API/worker/beat split.
- Current LinkedIn publishing behavior (from handover/docs):
  - Human approval remains required before publish.
  - Manual publish flow is primary (`/posts/publish-due` reminder + `/posts/{id}/confirm-manual-publish` confirmation).
  - Optional webhook handoff exists (`post.publish_ready`) via Zapier integration.
  - 48-hour comment monitoring starts after publish confirmation.
  - Golden-hour engagement support remains active after confirmation.

## V6 Target Architecture (LinkedIn-only)

Pipeline:
`Scout -> Writer -> Editor -> Publisher -> LinkedIn Promoter -> Analytics/PM`

Status flow:
`BACKLOG -> TODO -> WRITING -> REVIEW -> READY_TO_PUBLISH -> PUBLISHED -> AMPLIFIED -> DONE`

## Agent Definitions (LinkedIn-only)

1. Scout
- Finds LinkedIn-relevant topics and angle opportunities.
- Seeds backlog with keyword/topic intent and content angle metadata.
- Must prioritize Adtech, Retail Media, and AI ad platform themes only.

2. Writer
- Produces LinkedIn draft variants using your brand voice and product constraints.
- Does not publish and does not skip review.
- Must include personal experience framing where relevant (first-hand lessons from 20+ years).

3. Editor
- Hard gate for quality and factual accuracy.
- Rejects and returns structured revision notes to Writer.
- Rejects any draft that drifts outside the locked domain focus.

4. Publisher
- Handles approval-ready queue and publish handoff logic tied to LinkedIn workflow.
- Verifies link safety and publish prerequisites.
- Enforces posting cadence limits (minimum 1, maximum 3 posts per calendar day).

5. LinkedIn Promoter
- Handles LinkedIn-only amplification actions and marks social completion.
- Includes duplicate-prevention claim handling.

6. Morgan (PM/Ops)
- Detects bottlenecks, stale claims, queue starvation, and retries.
- Triggers additional runs when thresholds are breached.

## Data Model Changes

Add new pipeline table so existing v5 entities continue to work:

### New table: `content_pipeline_items`
- `id`
- `draft_id` (FK to drafts)
- `status`
- `writer_claim`
- `editor_claim`
- `publisher_claim`
- `promoter_claim`
- `quality_score`
- `readability_score`
- `fact_check_status`
- `revision_count`
- `social_status`
- `last_error`
- `next_run_at`
- `created_at`
- `updated_at`

### Optional config table/fields for gates
- readability minimum
- max revision attempts
- required checklist flags
- banned LinkedIn claims/phrases
- allowed domain topics (Adtech, Retail Media, AI ad platforms)
- experience anchor requirement flag (personal lessons signal)
- daily minimum posts target (`1`)
- daily maximum posts cap (`3`)

### Migration
- Add Alembic migration:
`/Users/sphiwemawhayi/Personal Brand/Backend/alembic/versions/0008_v6_linkedin_pipeline.py`

## Claim Locking Design (non-negotiable)

All stage workers must use claim + verify logic:

1. Query eligible items where stage claim is empty.
2. Attempt atomic claim write with unique claim id.
3. Re-fetch and verify claim owner is current worker.
4. Process item.
5. Update status and clear/rotate claim as designed.

Apply this pattern for Writer, Editor, Publisher, Promoter.

## LinkedIn Quality Gates

Editor must block promotion/publish unless all pass:

1. Brand/product factual accuracy against:
`/Users/sphiwemawhayi/Personal Brand/PRODUCT_CONTEXT.md`
2. Readability threshold.
3. Guardrail compliance (existing + LinkedIn-specific constraints).
4. Internal reference/link validity for publish-ready content.
5. No unsupported feature claims.
6. Topical relevance to Adtech, Retail Media, or AI ad platforms.
7. Voice includes practical personal-experience signal where appropriate.

Failed item goes back to Writer with structured revision notes and incremented `revision_count`.

## Scheduling (Celery Beat)

Initial cadence:
- Scout: every 6 hours
- Writer: every 1 hour
- Editor: every 1 hour
- Publisher: every 3 hours
- LinkedIn Promoter: 2x daily
- Morgan PM: 3x daily

Publish-frequency rules (hard constraints):
- Floor: target at least 1 post/day when `posting_enabled=true` and approvals exist.
- Cap: never publish more than 3 posts/day.
- Keep publish times inside configured window (`posting_window_start` to `posting_window_end`; currently default `08:00` to `17:00`).
- Preserve anti-burst behavior from existing frequency guardrails.

Execution-mode alignment (current spec):
- Default mode for V6 remains manual-first and compliant:
  - Human approves content.
  - System sends publish-ready notification/handoff.
  - User confirms publish with LinkedIn URL.
- Existing optional Zapier handoff stays supported but does not bypass human approval requirements in V6.

Files:
- `/Users/sphiwemawhayi/Personal Brand/Backend/app/workers/tasks.py`
- `/Users/sphiwemawhayi/Personal Brand/Backend/app/workers/celery_app.py`

## API and UI Additions

### Backend
Add pipeline routes:
- `/pipeline/overview`
- `/pipeline/items`
- `/pipeline/items/{id}/retry`
- `/pipeline/items/{id}/force-transition`
- `/pipeline/claims/stale`

File:
- `/Users/sphiwemawhayi/Personal Brand/Backend/app/routes/pipeline.py`

### Frontend
Add LinkedIn pipeline operations panel:
- queue by stage
- blocked/rejected counts
- stale claim alerts
- retry and force-transition controls

Files:
- `/Users/sphiwemawhayi/Personal Brand/Frontend/src/services/api.js`
- `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/DashboardView.jsx`
- `/Users/sphiwemawhayi/Personal Brand/Frontend/src/components/views/ContentView.jsx`

## Testing Plan

Add backend tests:
- `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v19_linkedin_pipeline_locking.py`
- `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v20_linkedin_editor_gates.py`
- `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v21_linkedin_pipeline_orchestration.py`
- `/Users/sphiwemawhayi/Personal Brand/Backend/tests/test_v22_linkedin_promoter_dedupe.py`

Add frontend tests for pipeline visibility/actions:
- `/Users/sphiwemawhayi/Personal Brand/Frontend/src/__tests__/App.pipeline.test.jsx`

## Delivery Phases

### Phase 1: Pipeline Foundation (Days 1-2)
- Add migration + ORM + schemas.
- Add claim-lock helper.
- Add base pipeline status transitions.

Exit criteria:
- Migration applies cleanly.
- Claims can be created/verified safely in tests.

### Phase 2: Writer/Editor Revision Loop (Days 3-5)
- Integrate Writer stage output into pipeline items.
- Implement Editor gates + rejection loop.

Exit criteria:
- Failed drafts auto-return with revision notes.
- Revision caps enforced.

### Phase 3: Publisher/Promoter Reliability (Days 6-7)
- Add publish-ready checks.
- Add LinkedIn promoter dedupe with `social_status`.
- Implement day-level publish counter enforcement (`<=3/day`) and minimum cadence alerting (`<1/day`).

Exit criteria:
- No duplicate amplify actions in concurrency tests.
- No day exceeds 3 published posts.

### Phase 4: PM Self-Healing + Observability (Days 8-9)
- Add Morgan PM sweeps for stuck items and stale claims.
- Add overview/alerts endpoints and UI panel.
- Add daily cadence alerts:
  - warning if zero published posts by end-of-window risk point
  - block when attempting to exceed 3/day

Exit criteria:
- Stuck items detected and recoverable via controlled retries.

### Phase 5: Shadow Run and Controlled Cutover (Days 10-14)
- Run in shadow mode first.
- Enable stage automation progressively.

Exit criteria:
- Stable queue flow.
- No manual DB repair required.
- Clear KPI trend on LinkedIn outcomes.

## Success Metrics (LinkedIn-only)

- Draft throughput and acceptance rate.
- First-pass pass rate vs revision rate.
- Time-in-stage and stuck-item count.
- Duplicate action rate (must trend to zero).
- LinkedIn impressions, engagement rate, comments quality, follower growth trend.
- Daily publish cadence compliance:
  - days meeting minimum 1 post target
  - zero days exceeding 3 posts
- Niche relevance compliance:
  - percentage of posts classified as Adtech/Retail Media/AI ad platform relevant
- Experience-led voice compliance:
  - percentage of posts passing personal-experience signal checks

## Change Control Rule

Any new requirement that introduces non-LinkedIn channels is deferred to post-V6 and must not alter this V6 execution path.
