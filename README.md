# LinkedIn Personal Brand Autoposter

Full-stack workspace for autonomous LinkedIn brand operations with backend workflow control and frontend operations console.

## Version status

- Backend through `v0.9` implemented and tested.
- Frontend operations console implemented.
- `v1.5` baseline smoke test is available and passing (backend tests + frontend tests + frontend build).

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

## Alignment rule

All feature changes must remain aligned with:

- `/Users/sphiwemawhayi/Personal Brand/linkedinAlgos.md`

This includes content quality constraints, anti-spam behavior, posting cadence discipline, and engagement timing rules.
