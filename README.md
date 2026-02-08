# LinkedIn Personal Brand Autoposter

Full-stack workspace for autonomous LinkedIn brand operations with backend workflow control and frontend operations console.

## Version status

- Backend through `v0.9` implemented and tested.
- Frontend operations console implemented.
- `v4.8` baseline smoke test is available and passing (45 backend tests + 51 frontend tests + frontend build).
- Single-user operational mode is complete and release-ready.

## Run locally

### 1. Backend setup

```bash
cd /Users/sphiwemawhayi/Personal\ Brand/Backend
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/alembic upgrade head
./.venv/bin/uvicorn app.main:app --reload
```

`DATABASE_URL` now defaults to local SQLite in `.env.example`, so first-run setup works without PostgreSQL.
If you want PostgreSQL instead, override `DATABASE_URL` in `/Users/sphiwemawhayi/Personal Brand/Backend/.env`.
Relative SQLite paths are normalized to the backend project root, so migrations and runtime always target the same local DB file.

### 2. Frontend setup

```bash
cd /Users/sphiwemawhayi/Personal\ Brand/Frontend
npm install
cp .env.example .env
npm run dev
```

Frontend default URL: `http://127.0.0.1:5173`  
Backend default URL: `http://127.0.0.1:8000`

## v1.0 smoke test

From project root:

```bash
./scripts/v1_smoke.sh
```

This runs:

- backend full unit suite (`v0.1` to `v0.9`)
- frontend automated smoke tests
- frontend production build

## Play mode

For a quick interactive local run:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
./scripts/run_play_mode.sh
```

If you prefer separate terminals:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
./scripts/run_backend.sh
```

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
./scripts/run_frontend.sh
```

### Play-mode E2E runner

For one-command Dashboard/Settings flow verification:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
./scripts/play_mode_e2e.sh
```

If local port binding is restricted (sandbox/CI):

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
PLAY_E2E_SKIP_SERVERS=1 ./scripts/play_mode_e2e.sh
```

### Live API walkthrough

With backend running, validate core API behavior:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
./scripts/live_api_walkthrough.sh
```

Optional mutating walkthrough:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
RUN_MUTATING=1 ./scripts/live_api_walkthrough.sh
```

If API key auth is enabled:

```bash
cd /Users/sphiwemawhayi/Personal\ Brand
API_KEY=your_key_here ./scripts/live_api_walkthrough.sh
```

### Play checklist

At `http://127.0.0.1:5173`:

- click `Bootstrap demo` in the `Playground` panel for one-click seeded workflow data
- check `Manual Publish Assistant` and resolve any checklist warnings before publish confirmation
- click `Generate`, then `Approve`/`Reject` on pending drafts
- click `Create Draft` to add a manual draft
- click `Run Due` and `Confirm publish` in Publishing
- use `Queue filter` in Publishing to focus `Due now`, `Unpublished`, or `Published` posts
- review `Operational Alerts` on Dashboard for kill switch, posting, due queue, and escalation warnings
- use `Snooze 2h` on specific dashboard alerts to temporarily reduce repeated noise
- use `Clear Snoozes` and the snoozed countdown summary to safely restore hidden alerts
- snooze countdowns now auto-refresh each minute without manual refresh
- export full operational backup from `Settings` via `Export Backup`
- view and queue preferences now persist across page reloads
- use `Reset UI Preferences` in `Settings` to restore default view/filter state
- update metrics with `Update metrics`
- add a comment with `Add Comment`
- review high-value items in the `Escalations` panel
- run `Poll`, `Ingest`, `Recompute`, and `Send`
- test `Kill ON/OFF` and `Posting ON/OFF`
- use `Settings` to inspect `Algorithm Alignment` and recent `Audit Trail` entries
- use `Audit filter` in `Settings` to narrow entries by action/actor/resource

## Alignment rule

All feature changes must remain aligned with:

- `/Users/sphiwemawhayi/Personal Brand/linkedinAlgos.md`

This includes content quality constraints, anti-spam behavior, posting cadence discipline, and engagement timing rules.
