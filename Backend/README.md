# Backend

## Local dev

1. Copy `.env.example` to `.env` and fill in secrets.
   - Keep `AUTO_CREATE_TABLES=false` for migration-first workflow.
2. Start infra:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand

docker-compose up -d
```

3. Create a virtualenv and install deps:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand/Backend

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Run the API:

```bash
uvicorn app.main:app --reload
```

5. Apply database migrations:

```bash
alembic upgrade head
```

6. Run Celery worker:

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

7. Run Celery beat (scheduler):

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

8. Run Telegram bot:

```bash
python -m app.telegram.bot
```

## v0.1 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_*.py'
```

## v0.2 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v02_*.py'
```

## v0.3 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v03_*.py'
```

## v0.4 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v04_*.py'
```

## v0.5 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v05_*.py'
```

## v0.6 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v06_*.py'
```

## v0.7 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v07_*.py'
```

## v0.8 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v08_*.py'
```

## v0.9 smoke test

From `/Users/sphiwemawhayi/Personal Brand/Backend`:

```bash
python3 -m unittest discover -v -s tests -p 'test_v09_*.py'
```

## v1.0 baseline smoke (full-stack)

From `/Users/sphiwemawhayi/Personal Brand`:

```bash
./scripts/v1_smoke.sh
```

## Implemented workflow

- `POST /drafts/generate`: creates a system draft, applies guardrails, and pushes approval text to Telegram.
  - If fallback regeneration still fails guardrails, the draft is auto-rejected with `rejection_reason=GUARDRAIL_FAILURE`.
- `POST /drafts/{id}/approve`: approves and schedules post time (random in configured window if not supplied).
- `POST /drafts/{id}/reject`: rejects pending draft.
- `POST /posts/publish-due`: sends one manual publish reminder for each due approved post.
- `POST /posts/{id}/confirm-manual-publish`: records LinkedIn URL and marks post as published.
- `POST /comments`: stores comment, runs triage, escalates high-value comments, and sends capped auto-replies.
- `POST /sources/ingest`: ingests RSS feeds into source storage.
- `GET /sources`: lists ingested source material.
- `POST /engagement/poll`: polls LinkedIn read scaffold and stores comments.
- `GET /engagement/status`: shows monitored/active/due post counts for comment polling.
- `GET /admin/audit-logs`: lists recent audit events.
- `POST /posts/{id}/metrics`: records post metrics and an engagement snapshot.
- `GET /learning/weights`: returns active learning weights.
- `POST /learning/recompute`: recomputes learning weights from post performance.
- `GET /reports/daily`: builds a daily performance summary.
- `POST /reports/daily/send`: sends daily summary to Telegram.
- `GET /health/deep`: deep dependency checks (DB + Redis).
- `GET /health/readiness`: readiness check for DB access.

## v0.2 research + LLM

- Research ingestion job runs daily at `02:00` (`ingest_research_sources`).
- Draft generation uses source summaries from ingested materials.
- Drafts include JSON source citations for traceability.
- Claude generation is used when `LLM_PROVIDER=claude` and `LLM_API_KEY` is configured.
- If Claude is unavailable, deterministic fallback generation is used.

## v0.3 security + observability

- Optional API key protection for all mutating endpoints via `APP_API_KEY` and `x-api-key` header.
- Audit log persistence for API and worker write operations (`audit_logs` table).
- Guardrails now flag unverified-claim language and unsourced percentage claims.
- LinkedIn read polling scaffold wired into API and Celery task paths (manual/no-token mode returns `not_configured`).

## v0.4 monitoring + polling windows

- Manual publish confirmation now starts a 48-hour comment monitoring window on the post.
- Polling intervals are age-aware:
- first 2 hours: 10 minutes
- hours 2 to 12: 30 minutes
- hours 12 to 48: 2 hours
- Polling tracks `last_comment_poll_at` to avoid over-polling.
- LinkedIn comment fetch contract supports deterministic mock payloads via `LINKEDIN_MOCK_COMMENTS_JSON`.

## v0.5 learning loop

- Engagement snapshots are stored in `engagement_metrics`.
- Adaptive selection weights are stored in `learning_weights`.
- Weight recomputation blends observed performance with default priors.
- Draft generation now uses persisted adaptive weights for format and tone selection.
- Nightly recompute task runs at `23:30` (`recompute_learning`).

## v0.6 LinkedIn adapter

- Added LinkedIn API adapter error taxonomy:
- `LinkedInApiError`, `LinkedInAuthError`, `LinkedInRateLimitError`.
- Added pagination handling over LinkedIn comment pages.
- Added retry handling for transient/5xx failures.
- Added deterministic mock paging contract support in `LINKEDIN_MOCK_COMMENTS_JSON`.

## v0.7 auth profiles

- Added separate keys:
- `APP_READ_API_KEY`
- `APP_WRITE_API_KEY`
- Added `AUTH_ENFORCE_READ` for optional read-endpoint protection.
- Kept backward compatibility with `APP_API_KEY` for write auth.

## v0.8 reporting

- Added daily report aggregation endpoint (`/reports/daily`).
- Added report send endpoint (`/reports/daily/send`) with Telegram delivery.
- Added scheduled daily summary send task at `18:30`.

## v0.9 ops readiness

- Added `Backend/Makefile` for setup/test/migrate/lint shortcuts.
- Added CI workflow: `.github/workflows/backend-ci.yml`.
- Added deep health and readiness endpoints for runtime diagnostics.

## LinkedIn algorithm alignment (enforced)

- Rule source: `/Users/sphiwemawhayi/Personal Brand/linkedinAlgos.md`.
- Quality and anti-spam controls:
- engagement bait language blocked
- excessive mentions blocked (`>3`)
- excessive hashtags blocked (`>3`)
- external links in post body blocked
- Frequency control:
- production draft generation guarded to prevent unusually high posting frequency bursts
- Golden hour support:
- golden-hour engagement prompt sent after manual publish confirmation
- Ranking alignment:
- post prompts enforce niche topical consistency and dwell-time-friendly structure
- Monitoring alignment:
- comment polling follows 10m/30m/2h window schedule across 48 hours
- Inspect current enforcement via:
- `GET /admin/algorithm-alignment`

## Telegram commands

- `/start`
- `/pending`
- `/approve <draft_id>`
- `/reject <draft_id> <reason>`
