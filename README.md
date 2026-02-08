# LinkedIn Personal Brand Autoposter

Full-stack workspace for autonomous LinkedIn brand operations with backend workflow control and frontend operations console.

## Version status

- Backend through `v0.9` implemented and tested.
- Frontend operations console implemented.
- `v1.8` baseline smoke test is available and passing (backend tests + frontend tests + frontend build).

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

### Play checklist

At `http://127.0.0.1:5173`:

- click `Bootstrap demo` in the `Playground` panel for one-click seeded workflow data
- click `Generate`, then `Approve`/`Reject` on pending drafts
- click `Create Draft` to add a manual draft
- click `Run Due` and `Confirm publish` in Publishing
- update metrics with `Update metrics`
- add a comment with `Add Comment`
- run `Poll`, `Ingest`, `Recompute`, and `Send`
- test `Kill ON/OFF` and `Posting ON/OFF`

## Alignment rule

All feature changes must remain aligned with:

- `/Users/sphiwemawhayi/Personal Brand/linkedinAlgos.md`

This includes content quality constraints, anti-spam behavior, posting cadence discipline, and engagement timing rules.
