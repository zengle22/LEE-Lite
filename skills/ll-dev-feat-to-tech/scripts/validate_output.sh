#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/validate_output.sh <artifacts-dir>"
  exit 1
fi

python scripts/feat_to_tech.py validate-output --artifacts-dir "$1"

# Silent override prevention — full FRZ anchor comparison (D-07)
python cli/lib/silent_override.py check \
  --output "$1" \
  --frz "$FRZ_ID" \
  --mode full
