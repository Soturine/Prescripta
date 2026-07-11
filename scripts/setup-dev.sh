#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/backend/requirements.txt"
npm --prefix "$ROOT/frontend" ci
echo "Ambiente instalado. Execute scripts/dev.sh."
