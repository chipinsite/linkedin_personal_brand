#!/bin/bash
set -e

# Run database migrations before starting any service.
# This is safe to run on every startup — Alembic is idempotent.
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

case "${SERVICE}" in
  api)
    echo "Starting API server on port ${PORT:-8000}..."
    exec uvicorn app.main:app \
      --host 0.0.0.0 \
      --port "${PORT:-8000}" \
      --workers 2 \
      --log-level info
    ;;
  worker)
    echo "Starting Celery worker..."
    exec celery -A app.workers.celery_app worker \
      --loglevel=info \
      --concurrency=2
    ;;
  beat)
    echo "Starting Celery beat scheduler..."
    exec celery -A app.workers.celery_app beat \
      --loglevel=info
    ;;
  *)
    echo "Unknown SERVICE: ${SERVICE}. Use api, worker, or beat."
    exit 1
    ;;
esac
