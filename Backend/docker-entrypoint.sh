#!/bin/bash
set -e

# Run database migrations before starting any service.
# Uses a timeout to avoid blocking if another service holds the Alembic lock.
echo "Running database migrations..."
if timeout 30 alembic upgrade head 2>&1; then
  echo "Migrations complete."
else
  echo "Migration timed out or failed (another service may be running it). Continuing startup..."
fi

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
