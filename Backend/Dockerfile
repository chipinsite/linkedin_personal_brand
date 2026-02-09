# ── Backend Dockerfile ──────────────────────────────────────────
# Multi-stage build for the FastAPI + Celery backend.
# Supports three runtime targets via the SERVICE env var:
#   SERVICE=api      → uvicorn (default)
#   SERVICE=worker   → celery worker
#   SERVICE=beat     → celery beat
# ────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed by psycopg (PostgreSQL) and bcrypt
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# ── Dependencies stage ──────────────────────────────────────────
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Runtime stage ───────────────────────────────────────────────
FROM base AS runtime

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Default port (Railway injects $PORT at runtime)
ENV PORT=8000

# SERVICE determines which process runs:
#   api    → FastAPI via uvicorn  (default)
#   worker → Celery worker
#   beat   → Celery beat scheduler
ENV SERVICE=api

# Health check for the API service
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Entrypoint script handles SERVICE routing
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE ${PORT}

ENTRYPOINT ["/docker-entrypoint.sh"]
