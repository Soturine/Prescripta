#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
trap 'kill 0' EXIT
(cd "$ROOT/backend" && "$ROOT/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
(cd "$ROOT/frontend" && VITE_API_URL=http://127.0.0.1:8000/api npm run dev -- --host 127.0.0.1 --port 5173) &
wait
