#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/validate_output.sh <artifact-path>"
  exit 1
fi

ARTIFACT_PATH="$1"

if [ ! -e "$ARTIFACT_PATH" ]; then
  echo "Artifact not found: $ARTIFACT_PATH"
  exit 1
fi

python scripts/epic_to_feat.py validate-output --artifacts-dir "$ARTIFACT_PATH"
