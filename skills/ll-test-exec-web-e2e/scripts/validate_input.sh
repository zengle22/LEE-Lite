#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/validate_input.sh <request-json>"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
normalized="${1}.normalized.json"
trap 'rm -f "$normalized"' EXIT
python "$SCRIPT_DIR/normalize_request.py" --input "$1" --output "$normalized"
python "$SCRIPT_DIR/../../test-exec-common/test_exec_skill_guard.py" validate-input --modality web "$normalized"
