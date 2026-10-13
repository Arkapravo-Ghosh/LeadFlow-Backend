#!/bin/sh
set -eu
# Fail deployment before accepting requests if a migration cannot complete.
uv run --no-dev alembic upgrade head
exec uv run --no-dev uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
