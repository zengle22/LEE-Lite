#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/validate_output.sh <artifact-path>"
  exit 1
fi

ARTIFACT_PATH="$1"

if [ ! -f "$ARTIFACT_PATH" ]; then
  echo "Artifact not found: $ARTIFACT_PATH"
  exit 1
fi

echo "Validate $ARTIFACT_PATH against output/contract.yaml and output/schema.json"
echo "Replace this placeholder with project-specific lee validation commands."
