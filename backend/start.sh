#!/usr/bin/env bash
set -euo pipefail
cd backend
python -m alembic -c alembic.ini upgrade head
cd ..
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-10000}"

