#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py validate-output --artifacts-dir "$1"

# Silent override prevention — full FRZ anchor comparison (D-07)
python cli/lib/silent_override.py check \
  --output "$1" \
  --frz "$FRZ_ID" \
  --mode full
