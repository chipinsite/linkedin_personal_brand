# Handover Document

**Prepared:** 2026-02-11 00:30 SAST
**Repository:** `/Users/sphiwemawhayi/Personal Brand`
**Branch:** `main`
**Latest commit:** Pending (v6.4 changes uncommitted)

## 1. Executive Summary
The single-user LinkedIn personal brand tool is at `v6.4` (V6 Phase 5: Shadow Mode + Progressive Enablement — **all 5 V6 phases complete**) and deployed on Railway at v5.5.

Current state:
- Backend API: 320 tests passing, full AI content pipeline with all 6 V6 agents (Scout, Writer, Editor, Publisher, Promoter, Morgan PM), pipeline API routes, Celery worker integration with 12 tasks, pipeline mode controls (legacy/shadow/v6/disabled), JWT auth, Telegram workflows, LinkedIn metrics, comment handling, Zapier webhook integration.
- Frontend console: 67 tests passing, accessible UI with ARIA landmarks, 5 views (Dashboard, Content, Pipeline, Engagement, Settings), pipeline mode selector and mode indicator.
- End-to-end smoke path (`backend tests + frontend tests + frontend build`) passes.
- **Production deployment live on Railway** at v5.5 with 4 services (backend-api, backend-worker, backend-beat, frontend).

Builds completed this session:
- `v6.4` V6 Phase 5: Shadow mode, progressive enablement, pipeline mode controls
- `v6.3` V6 Phase 4: Morgan PM self-healing agent, frontend Pipeline view
- `v6.2` V6 Phase 3: Publisher + Promoter agents, pipeline API routes, Celery task integration
- `v6.1` V6 Phase 2: Scout, Writer, Editor agents, PRODUCT_CONTEXT.md loader, textstat readability scoring
- `v6.0` V6 Phase 1: pipeline foundation, claim locks, status transitions

## 2. What Was Completed This Session

### 2.0 v6.4 — Shadow Mode + Progressive Enablement (Phase 5 of 5 — FINAL)
- Pipeline mode system (`PipelineMode` enum with 4 states):
  - `legacy` — default, only legacy workflow tasks run, V6 tasks skip
  - `shadow` — both run, V6 Publisher skips webhook/Telegram (dry-run validation)
  - `v6` — only V6 pipeline tasks run, legacy tasks skip
  - `disabled` — emergency stop for all pipeline activity
- Pipeline mode service (`services/pipeline_mode.py`):
  - `get_pipeline_mode()`, `set_pipeline_mode()` — persisted on AppConfig
  - `should_run_legacy()`, `should_run_v6()`, `is_shadow_mode()` — gating helpers
  - `get_pipeline_status_summary()` — admin aggregation
- Worker task gating:
  - All 8 content tasks (2 legacy, 6 V6) check pipeline mode before executing
  - Tasks return `"skipped:pipeline_mode"` when mode excludes them
  - Graceful fallback: if pipeline_mode column doesn't exist yet, tasks run normally
- Publisher shadow mode:
  - Accepts `shadow_mode` parameter
  - In shadow: still creates PublishedPost, transitions pipeline item, but skips webhook and Telegram
- Admin endpoints:
  - `POST /admin/pipeline-mode/{mode}` — switch mode with audit logging
  - `GET /admin/pipeline-status` — full mode summary with task gating visibility
  - `GET /admin/config` now includes `pipeline_mode` field
- Migration `0009_pipeline_mode.py`:
  - Adds `pipeline_mode` column to `app_config` (default: `legacy`)
  - PostgreSQL native enum conversion using proven sa.String + raw SQL pattern
- Frontend Settings view: pipeline mode selector with 4 mode buttons, contextual descriptions
- Frontend Pipeline view: mode indicator banner for non-V6 modes (LEGACY/SHADOW/DISABLED warnings)
- 35 new backend tests across 12 test classes
- 6 new frontend tests

### 2.1 v6.3 — Morgan PM + Frontend Pipeline Panel (Phase 4 of 5)
- Morgan PM self-healing agent (`agents/morgan.py`):
  - `recover_stale_claims()` — finds and force-releases expired claim locks
  - `reset_errored_items()` — resets stuck errored items: WRITING→TODO, REVIEW→TODO, READY_TO_PUBLISH→BACKLOG; skips recently updated, claimed, or max-auto-reset-exceeded items
  - `generate_health_report()` — aggregates stale claims, errored items, stuck items; determines health as "healthy"/"degraded"/"unhealthy"
  - `run_morgan()` — orchestrates all three phases
- Pipeline API additions:
  - `POST /pipeline/run/morgan` — trigger Morgan PM with audit logging
  - `GET /pipeline/health` — read-only pipeline health report
- Worker updates:
  - `v6_run_morgan` Celery task + beat schedule (every 15 minutes)
  - TASK_REGISTRY now has 12 entries (6 legacy + 6 V6)
- Frontend Pipeline view (`PipelineView.jsx`):
  - Health status banner for degraded/unhealthy pipeline
  - 4 MetricCard overview (Backlog, In progress, Ready/Published, Done)
  - Clickable 8-stage pipeline visualization with status counts
  - 6 agent control buttons (Scout, Writer, Editor, Publisher, Promoter, Morgan)
  - Pipeline items list with status filter dropdown
  - Error, quality, revision display per item
  - Loading spinner, error state, empty state handling
- Pipeline API client methods (6 methods in api.js)
- Pipeline nav item in Sidebar + version to v6.3
- 20 new backend tests, 10 new frontend tests

### 2.2 v6.2 — Publisher + Promoter + Pipeline API + Celery (Phase 3 of 5)
- Publisher agent, Promoter agent, pipeline API routes, Celery worker with 11 tasks
- 36 new backend tests

### 2.3 v6.1 — V6 Agent Services (Phase 2 of 5)
- PRODUCT_CONTEXT.md loader, Scout, Writer, Editor agents
- 36 new backend tests

### 2.4 v6.0 — V6 Pipeline Foundation (Phase 1 of 5)
- content_pipeline_items table, claim-lock service, status transition engine
- 23 new backend tests

## 3. Production Environment — Railway

### 3.1 Project Details
- **Project:** `lavish-exploration` (ID: `4845c253-180c-4444-bc76-cfb744bfd12d`)
- **Environment:** `production`
- **Backend URL:** `https://backend-api-production-1841.up.railway.app`
- **Frontend URL:** `https://frontend-production-3aa4.up.railway.app`
- **PostgreSQL:** `postgres-3sua.railway.internal:5432/railway` (public: `turntable.proxy.rlwy.net:12118`)
- **Redis:** `redis.railway.internal:6379`

### 3.2 Service IDs
| Service | ID |
|---------|---|
| backend-api | `7439580a-7001-42d4-bfe0-54ba8fbc2607` |
| backend-worker | `7c31d048-6134-47a1-8059-556c27e6c915` |
| backend-beat | `3993f8ba-abfd-4c82-b142-af84374f1fb0` |
| frontend | `163f25d3-c7cc-47b1-84a6-9e9b91d97973` |

### 3.3 User Account
- Username: `sphiwe`
- Email: `sphiwemawhayi@hotmail.com`
- Password: `testpass123`

### 3.4 Critical Deployment Pattern
This is a monorepo. **Must use `railway up --path-as-root Backend/` (or `Frontend/`)** for manual deploys. GitHub-based auto-builds fail because the Dockerfile is not at the repo root.

**Deploy sequence for backend changes:**
```bash
cd "/Users/sphiwemawhayi/Personal Brand"

# Deploy to backend-api
railway link --project 4845c253-180c-4444-bc76-cfb744bfd12d -s backend-api -e production
railway up --path-as-root Backend/

# Deploy to backend-worker
railway link --project 4845c253-180c-4444-bc76-cfb744bfd12d -s backend-worker -e production
railway up --path-as-root Backend/

# Deploy to backend-beat
railway link --project 4845c253-180c-4444-bc76-cfb744bfd12d -s backend-beat -e production
railway up --path-as-root Backend/
```

### 3.5 Migration Status
7 migrations applied on production PostgreSQL (0008 + 0009 pending deploy):
- `0001_initial` — core tables
- `0002_sources_and_citations` — source_materials table
- `0003_audit_logs` — audit_logs table
- `0004_comment_monitoring_windows` — monitoring fields
- `0005_learning_metrics` — engagement_metrics and learning_weights
- `0006_user_auth` — users and refresh_tokens
- `0007_webhook_config` — zapier webhook columns
- `0008_v6_pipeline` — content_pipeline_items table (**NOT YET DEPLOYED**)
- `0009_pipeline_mode` — pipeline_mode column on app_config (**NOT YET DEPLOYED**)

## 4. Test Coverage Summary
| Suite | Count | Status |
|-------|-------|--------|
| Backend (pytest) | 320 | All pass |
| Frontend (vitest) | 67 | All pass |
| Frontend build | 1 | Pass |

## 5. Key Files Added/Modified This Session

### V6 Phase 5 (v6.4)
- `Backend/app/models.py` (modified) — PipelineMode enum + AppConfig column
- `Backend/alembic/versions/0009_pipeline_mode.py` (new) — pipeline_mode migration
- `Backend/app/services/pipeline_mode.py` (new) — mode management, gating, shadow detection
- `Backend/app/services/config_state.py` (modified) — pipeline mode accessor
- `Backend/app/worker.py` (modified) — task gating on 8 content tasks
- `Backend/app/services/agents/publisher.py` (modified) — shadow_mode parameter
- `Backend/app/routes/admin.py` (modified) — pipeline-mode + pipeline-status endpoints
- `Backend/tests/test_v6_phase5_shadow_mode.py` (new) — 35 tests
- `Frontend/src/services/api.js` (modified) — 2 pipeline mode API methods
- `Frontend/src/components/views/SettingsView.jsx` (modified) — pipeline mode selector
- `Frontend/src/components/views/PipelineView.jsx` (modified) — mode indicator banner
- `Frontend/src/components/layout/Sidebar.jsx` (modified) — version v6.4
- `Frontend/src/__tests__/App.test.jsx` (modified) — 6 new tests

### V6 Phase 4 (v6.3)
- `Backend/app/services/agents/morgan.py` (new) — Morgan PM self-healing agent
- `Backend/app/routes/pipeline.py` (modified) — Morgan trigger + health endpoints
- `Backend/app/worker.py` (modified) — Morgan task, beat schedule, 12 total tasks
- `Backend/tests/test_v6_phase4_morgan.py` (new) — 20 tests
- `Backend/tests/test_v6_phase3.py` (modified) — task count fix 11→12
- `Frontend/src/components/views/PipelineView.jsx` (new) — pipeline operations view
- `Frontend/src/services/api.js` (modified) — 6 pipeline API methods
- `Frontend/src/App.jsx` (modified) — PipelineView registration
- `Frontend/src/components/layout/Sidebar.jsx` — Pipeline nav, version v6.3
- `Frontend/src/__tests__/App.test.jsx` (modified) — 10 pipeline tests

### V6 Phase 3 (v6.2)
- `Backend/app/services/agents/publisher.py` (new) — Zapier webhook + PublishedPost creator
- `Backend/app/services/agents/promoter.py` (new) — engagement prompt + lifecycle completer
- `Backend/app/routes/pipeline.py` (new) — pipeline API routes with agent triggers
- `Backend/app/worker.py` (new) — Celery tasks and beat schedule
- `Backend/tests/test_v6_phase3.py` (new) — 36 tests

### V6 Phase 2 (v6.1)
- `Backend/app/services/product_context.py` (new) — PRODUCT_CONTEXT.md parser
- `Backend/app/services/agents/{__init__,scout,writer,editor}.py` (new)
- `Backend/tests/test_v6_phase2_agents.py` (new) — 36 tests

### V6 Phase 1 (v6.0)
- `Backend/app/models.py` — PipelineStatus, SocialStatus, ContentPipelineItem
- `Backend/alembic/versions/0008_v6_pipeline.py` (new)
- `Backend/app/services/{claim_lock,pipeline}.py` (new)
- `Backend/tests/test_v6_pipeline_foundation.py` (new) — 23 tests

## 6. API Endpoints Summary (New This Session)

### Pipeline Routes (v6.2 + v6.3)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pipeline/overview` | Aggregated status counts |
| GET | `/pipeline/items` | List items (optional `?status=` filter) |
| GET | `/pipeline/items/{id}` | Item detail |
| POST | `/pipeline/items/{id}/transition` | Manual status transition |
| POST | `/pipeline/run/scout` | Trigger Scout agent |
| POST | `/pipeline/run/writer` | Trigger Writer agent |
| POST | `/pipeline/run/editor` | Trigger Editor agent |
| POST | `/pipeline/run/publisher` | Trigger Publisher agent |
| POST | `/pipeline/run/promoter` | Trigger Promoter agent |
| POST | `/pipeline/run/morgan` | Trigger Morgan PM agent (v6.3) |
| GET | `/pipeline/health` | Pipeline health report (v6.3) |

### Admin Routes (v6.4)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/pipeline-mode/{mode}` | Switch pipeline mode (legacy/shadow/v6/disabled) |
| GET | `/admin/pipeline-status` | Pipeline mode summary with task gating |

## 7. Known Outstanding Work

### 7.1 Immediate: Deploy v6.0-v6.4 to Railway
- Commit and push all v6 changes
- Deploy to all 3 backend services (`railway up --path-as-root Backend/`)
- Deploy to frontend service (`railway up --path-as-root Frontend/`)
- Migrations 0008 + 0009 will run automatically via docker-entrypoint.sh

### 7.3 Zapier Setup (carried forward)
- User needs to create Zapier account and set `ZAPIER_WEBHOOK_URL`

### 7.4 Medium-priority
- Form label-to-input associations (htmlFor/id) across frontend views
- Auth key rotation endpoint
- Rate limiting on API endpoints

### 7.5 Strategic scope gaps (intentionally out of current scope)
- Multi-user/role-based operation
- Direct LinkedIn API write automation
- WhatsApp/Email notification channels

## 8. First 30 Minutes for Next Agent

1. Sync and verify:
```bash
cd "/Users/sphiwemawhayi/Personal Brand"
git pull
git status
```

2. Run full smoke:
```bash
./scripts/v1_smoke.sh
```
Expected: 320 backend tests, 67 frontend tests, build passes.

3. Check production health:
```bash
curl https://backend-api-production-1841.up.railway.app/health
curl https://backend-api-production-1841.up.railway.app/health/db
```

4. For local development:
```bash
cd Backend
./.venv/bin/alembic upgrade head
./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 9. V6 Pipeline Architecture Summary

### Status Flow
```
BACKLOG → TODO → WRITING → REVIEW → READY_TO_PUBLISH → PUBLISHED → AMPLIFIED → DONE
                    ↑         |
                    └─────────┘  (revision loop)
```

### Agent Responsibilities
| Agent | Input Status | Output Status | Role | Status |
|-------|-------------|--------------|------|--------|
| Scout | (source_materials) | BACKLOG | Scans sources, seeds topics | Done (v6.1) |
| Writer | TODO | REVIEW | Claims items, generates drafts | Done (v6.1) |
| Editor | REVIEW | READY_TO_PUBLISH or TODO | 7 quality gates, revision loop | Done (v6.1) |
| Publisher | READY_TO_PUBLISH | PUBLISHED | Webhook + PublishedPost + Telegram | Done (v6.2) |
| Promoter | PUBLISHED | DONE | Engagement prompts, lifecycle completion | Done (v6.2) |
| Morgan | (all) | (all) | PM self-healing, stale claim recovery, error reset, health monitoring | Done (v6.3) |

### Celery Beat Schedule (v6.3)
| Task | Schedule | Agent |
|------|----------|-------|
| v6-scout-scan | Every 6 hours at :15 | Scout |
| v6-writer-generate | Every 2 hours at :30 | Writer |
| v6-editor-review | Every 2 hours at :45 | Editor |
| v6-publisher-publish | Every 30 minutes | Publisher |
| v6-promoter-engage | Every hour at :10 | Promoter |
| v6-morgan-heal | Every 15 minutes | Morgan PM |

### Pipeline Mode (v6.4)
| Mode | Legacy Tasks | V6 Tasks | V6 Publishing | Use Case |
|------|-------------|----------|---------------|----------|
| `legacy` | Run | Skip | N/A | Default, current behavior |
| `shadow` | Run | Run | Dry-run (no webhook/Telegram) | Safe parallel validation |
| `v6` | Skip | Run | Full | V6 is primary |
| `disabled` | Skip | Skip | N/A | Emergency stop |

### Phase Plan
| Phase | Scope | Status |
|-------|-------|--------|
| 1. Foundation | Pipeline table, claim locks, transitions | **Done (v6.0)** |
| 2. Writer/Editor | Scout + Writer + Editor agents, PRODUCT_CONTEXT | **Done (v6.1)** |
| 3. Publisher/Promoter | Publisher + Promoter, pipeline API, Celery | **Done (v6.2)** |
| 4. Morgan + UI | PM self-healing, frontend pipeline panel | **Done (v6.3)** |
| 5. Shadow + Cutover | Shadow mode, progressive enablement | **Done (v6.4)** |

### Key Services
- `app/services/claim_lock.py` — atomic claim management for multi-worker safety
- `app/services/pipeline.py` — status transitions, queries, revision tracking
- `app/services/pipeline_mode.py` — mode management, task gating, shadow mode detection
- `app/services/product_context.py` — PRODUCT_CONTEXT.md parser for Editor fact-checking
- `app/services/agents/scout.py` — source scanner, BACKLOG seeder
- `app/services/agents/writer.py` — draft generator using content_engine
- `app/services/agents/editor.py` — 7 quality gates with revision loop
- `app/services/agents/publisher.py` — webhook publisher, PublishedPost creator (shadow mode support)
- `app/services/agents/promoter.py` — engagement prompt sender, lifecycle completer
- `app/services/agents/morgan.py` — self-healing PM: stale claim recovery, error reset, health monitoring
- `app/routes/pipeline.py` — pipeline API routes with agent triggers + health endpoint
- `app/worker.py` — Celery tasks and beat schedule (12 total, mode-gated)

## 10. Troubleshooting

### Railway deploy fails after env var change
**Cause:** Changing env vars triggers GitHub-based auto-build which fails (monorepo).
**Fix:** Manually deploy with `railway up --path-as-root Backend/` for each service.

### PostgreSQL enum errors
**Cause:** SQLAlchemy `sa.Enum` in `create_table` always fires `CREATE TYPE`.
**Fix:** Already resolved in `0001_initial.py`. Uses `sa.String` then raw SQL ALTER for PostgreSQL.

### textstat NLTK cmudict missing
**Cause:** textstat requires NLTK cmudict corpus for Flesch-Kincaid scoring.
**Fix:** Run `import nltk; nltk.download('cmudict')` or Editor gate gracefully degrades.

### Celery tasks not running
**Cause:** Redis not available or Celery not imported.
**Fix:** Worker gracefully falls back. Use pipeline API agent triggers (`POST /pipeline/run/{agent}`) for manual execution.

## 11. Documentation + Process Rules
- Build logging mandatory via `AGENT_BUILD_LOG.md`
- Rules codified in `DOCUMENTATION_RULES.md`
- `CLAUDE.md` is spec + version history source of truth
- `linkedinAlgos.md` is mandatory alignment guidance for content/publishing behavior
- `PRODUCT_CONTEXT.md` is the single source of truth for Editor fact-checking

---
Handover complete.
