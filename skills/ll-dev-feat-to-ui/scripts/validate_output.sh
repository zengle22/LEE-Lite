#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_ui_route.py validate-output --artifacts-dir "$1"

# Silent override prevention — JRN/SM anchors only (D-07)
python cli/lib/silent_override.py check \
  --output "$1" \
  --frz "$FRZ_ID" \
  --mode journey_sm
