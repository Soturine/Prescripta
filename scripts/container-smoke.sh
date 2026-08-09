#!/usr/bin/env bash
set -Eeuo pipefail

compose=(docker compose --project-name prescripta-smoke)

cleanup() {
  status=$?
  if [[ $status -ne 0 ]]; then
    "${compose[@]}" logs --no-color --tail=120 || true
  fi
  if [[ "${PRESCRIPTA_KEEP_CONTAINERS:-false}" != "true" ]]; then
    "${compose[@]}" down --volumes --remove-orphans || true
  fi
  exit "$status"
}
trap cleanup EXIT

"${compose[@]}" config --quiet
"${compose[@]}" build backend frontend
"${compose[@]}" up --detach --wait

curl --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8080/healthz >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8080/ >/dev/null

test "$("${compose[@]}" exec -T backend id -u)" != "0"
test "$("${compose[@]}" exec -T frontend id -u)" != "0"

"${compose[@]}" run --rm migrate
"${compose[@]}" restart backend
"${compose[@]}" up --detach --wait backend frontend
curl --fail --silent --show-error http://127.0.0.1:8000/health >/dev/null

echo "Container smoke OK: build, migration, health, restart and non-root verified."
