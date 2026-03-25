#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/validate_output.sh <artifacts-dir>"
  exit 1
fi

python scripts/feat_to_tech.py validate-output --artifacts-dir "$1"
