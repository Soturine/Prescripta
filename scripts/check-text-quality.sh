#!/usr/bin/env sh
set -eu
python "$(dirname "$0")/check_text_quality.py" "$@"
