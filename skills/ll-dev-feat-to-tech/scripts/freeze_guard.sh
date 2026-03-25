#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/freeze_guard.sh <artifacts-dir>"
  exit 1
fi

python scripts/feat_to_tech.py validate-package-readiness --artifacts-dir "$1"
