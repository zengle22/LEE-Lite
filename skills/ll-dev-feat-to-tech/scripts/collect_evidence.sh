#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/collect_evidence.sh <artifacts-dir>"
  exit 1
fi

python scripts/feat_to_tech.py collect-evidence --artifacts-dir "$1"
