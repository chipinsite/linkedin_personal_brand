# LinkedIn Personal Brand Autoposter

Full-stack workspace for autonomous LinkedIn brand operations with backend workflow control and frontend operations console.

## Version status

- Current version: `v6.4` — V6 pipeline complete (all 5 phases: foundation, agents, publisher/promoter, Morgan PM, shadow mode).
- Backend through `v6.4` implemented and tested (320 tests).
- Frontend operations console with pipeline view (67 tests).
- Production deployed at v5.5 on Railway.
- Single-user operational mode is complete and deployment-ready.

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

---

## Deploy to Production

### Option A: Railway (Recommended)

Railway is the simplest path to production. It provides managed PostgreSQL, Redis, and automatic HTTPS.

#### Prerequisites

Before deploying, create accounts and get these credentials:

| Credential | Where to get it |
|---|---|
| **Claude API key** | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| **Telegram bot token** | Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` |
| **JWT secret** | Run `openssl rand -hex 32` in your terminal |

#### Step-by-step Railway deployment

**1. Create Railway project**

Go to [railway.com](https://railway.com), sign up (GitHub login works), and create a new project.

**2. Connect your GitHub repo**

Click "Deploy from GitHub repo" and select this repository.

**3. Add PostgreSQL**

Click "New" → "Database" → "PostgreSQL". Railway auto-injects `DATABASE_URL`.

**4. Add Redis**

Click "New" → "Database" → "Redis". Railway auto-injects `REDIS_URL`.

**5. Create 4 services from the same repo**

You need 4 services all pointing to this repo. For each one, click "New" → "GitHub Repo" → select this repo:

| Service Name | Root Directory | Dockerfile Path | SERVICE env var |
|---|---|---|---|
| `backend-api` | `Backend` | `Backend/Dockerfile` | `api` |
| `backend-worker` | `Backend` | `Backend/Dockerfile` | `worker` |
| `backend-beat` | `Backend` | `Backend/Dockerfile` | `beat` |
| `frontend` | `Frontend` | `Frontend/Dockerfile` | _(not used)_ |

**6. Set environment variables**

In each **backend** service (api, worker, beat), add these variables:

```
SERVICE=api              # (or worker, or beat — per service)
APP_ENV=prod
JWT_SECRET_KEY=<your-generated-secret>
AUTH_MODE=jwt
LLM_API_KEY=<your-claude-api-key>
LLM_PROVIDER=claude
LLM_MODEL=claude-sonnet-4-20250514
LLM_MOCK_MODE=false
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_CHAT_ID=<your-chat-id>
TIMEZONE=Africa/Johannesburg
LOG_JSON=true
LOG_LEVEL=INFO
CORS_ALLOWED_ORIGINS=https://<your-frontend>.railway.app
```

Railway auto-provides `DATABASE_URL` and `REDIS_URL` — link each backend service to your Postgres and Redis add-ons via the "Variables" → "Reference" feature.

For the **frontend** service, set this build arg:

```
VITE_API_BASE_URL=https://<your-backend-api>.railway.app
```

**7. Set health check**

For `backend-api`, go to Settings → Health Check → set path to `/health`.

**8. Deploy**

Railway builds and deploys automatically on push. First deploy takes ~3 minutes.

**9. Create your user account**

```bash
curl -X POST https://<your-backend-api>.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"yourname","password":"your-password"}'
```

**10. Open your app**

Visit `https://<your-frontend>.railway.app` and log in.

---

### Option B: Docker Compose (Self-hosted)

For deployment on any VPS (DigitalOcean, Hetzner, AWS, etc):

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd "Personal Brand"

# 2. Configure secrets
cp .env.production.template .env
# Edit .env and fill in all CHANGE_ME values

# 3. Build and start everything
docker compose -f docker-compose.prod.yml up -d

# 4. Check it's running
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8000/health

# 5. Create your user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","username":"yourname","password":"your-password"}'
```

Frontend: `http://localhost:3000`
Backend API: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

For production, put nginx or Caddy in front with HTTPS (Let's Encrypt).

---

### Deployment files reference

| File | Purpose |
|---|---|
| `Backend/Dockerfile` | Backend image (API, worker, beat via `SERVICE` env var) |
| `Backend/docker-entrypoint.sh` | Startup script: runs migrations then starts the correct service |
| `Frontend/Dockerfile` | Frontend image (Node build → nginx serve) |
| `Frontend/nginx.conf` | SPA routing config for nginx |
| `docker-compose.prod.yml` | Full production stack (Postgres + Redis + 3 backend + frontend) |
| `.env.production.template` | All production env vars documented |
| `railway.toml` | Railway platform configuration |

---

### Production architecture

```
                    ┌──────────────────┐
                    │   Your Browser   │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐    │    ┌─────────▼─────────┐
     │    Frontend      │    │    │   Backend API     │
     │    (nginx)       │    │    │   (FastAPI)       │
     │    port 80/443   │    │    │   port 8000       │
     └─────────────────┘    │    └─────────┬─────────┘
                            │              │
                            │    ┌─────────▼─────────┐
                            │    │   PostgreSQL       │
                            │    │   (data store)     │
                            │    └───────────────────┘
                            │              │
              ┌─────────────┼──────────────┤
              │             │              │
     ┌────────▼────────┐   │   ┌──────────▼──────────┐
     │  Celery Worker   │   │   │  Celery Beat        │
     │  (background     │   │   │  (scheduler)        │
     │   tasks)         │   │   └─────────────────────┘
     └────────┬────────┘   │
              │            │
     ┌────────▼────────────▼───┐
     │       Redis             │
     │       (task queue)      │
     └─────────────────────────┘
```

---

## Alignment rule

All feature changes must remain aligned with:

- `/Users/sphiwemawhayi/Personal Brand/linkedinAlgos.md`

This includes content quality constraints, anti-spam behavior, posting cadence discipline, and engagement timing rules.
