#!/usr/bin/env bash
# run.sh — Entry point for ll-patch-aware-context skill
# Usage: ./run.sh resolve --feat-ref FEAT-001 [--output-dir <path>] [--ai-reasoning "<text>"]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Auto-detect workspace root 3 levels up from script dir
# skills/ll-patch-aware-context/scripts/  -> 3 levels up to repo root
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Defaults
OUTPUT_DIR="${WORKSPACE_ROOT}/ssot/tests/.artifacts/patch-context"
FEAT_REF=""
AI_REASONING=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    resolve)
      COMMAND="$1"
      shift
      ;;
    --feat-ref) FEAT_REF="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --ai-reasoning) AI_REASONING="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "${FEAT_REF}" ]]; then
  echo "Error: --feat-ref is required"
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Delegate to Python script
exec python "${SCRIPT_DIR}/patch_aware_context.py" resolve \
  --workspace-root "${WORKSPACE_ROOT}" \
  --feat-ref "${FEAT_REF}" \
  --output-dir "${OUTPUT_DIR}" \
  ${AI_REASONING:+--ai-reasoning "${AI_REASONING}"}
