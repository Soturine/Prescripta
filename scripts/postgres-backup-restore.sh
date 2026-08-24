#!/usr/bin/env bash
set -euo pipefail

: "${PRESCRIPTA_BACKUP_SOURCE_URL:?source URL required}"
: "${PRESCRIPTA_RESTORE_TARGET_URL:?restore target URL required}"

work_dir="$(mktemp -d)"
trap 'rm -rf -- "$work_dir"' EXIT
dump_file="$work_dir/prescripta.dump"

started="$(date +%s)"
pg_dump --format=custom --no-owner --no-acl \
  --file="$dump_file" "$PRESCRIPTA_BACKUP_SOURCE_URL"
sha256sum "$dump_file" > "$dump_file.sha256"
sha256sum --check "$dump_file.sha256"
pg_restore --exit-on-error --no-owner --no-acl \
  --dbname="$PRESCRIPTA_RESTORE_TARGET_URL" "$dump_file"

source_probe="$(psql "$PRESCRIPTA_BACKUP_SOURCE_URL" -Atqc 'SELECT count(*) FROM qualification_probe')"
restore_probe="$(psql "$PRESCRIPTA_RESTORE_TARGET_URL" -Atqc 'SELECT count(*) FROM qualification_probe')"
test "$source_probe" = "$restore_probe"

elapsed="$(( $(date +%s) - started ))"
printf '{"schema":"postgres-recovery-v1","probe_rows":%s,"elapsed_seconds":%s,"checksum_verified":true}\n' \
  "$restore_probe" "$elapsed"
