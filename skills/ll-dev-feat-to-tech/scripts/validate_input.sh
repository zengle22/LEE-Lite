#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: scripts/validate_input.sh <feat-package-dir> <feat-ref>"
  exit 1
fi

python scripts/feat_to_tech.py validate-input --input "$1" --feat-ref "$2"
