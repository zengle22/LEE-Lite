#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_proto.py validate-output --artifacts-dir "$1"

# Silent override prevention — lightweight product_boundary check (D-07)
python cli/lib/silent_override.py check \
  --output "$1" \
  --frz "$FRZ_ID" \
  --mode product_boundary
