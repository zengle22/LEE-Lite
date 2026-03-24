#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/freeze_guard.sh <artifacts-dir>"
  exit 1
fi

python scripts/epic_to_feat.py freeze-guard --artifacts-dir "$1"
