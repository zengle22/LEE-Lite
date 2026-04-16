#!/usr/bin/env bash
# run.sh — Entry point for ll-patch-capture skill
# Usage: ./run.sh --feat-id <id> --input-type <prompt|document> --input-value <text|path> [--workspace <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
FEAT_ID=""
INPUT_TYPE=""
INPUT_VALUE=""
WORKSPACE="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --feat-id) FEAT_ID="$2"; shift 2;;
    --input-type) INPUT_TYPE="$2"; shift 2;;
    --input-value) INPUT_VALUE="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "${FEAT_ID}" ]]; then
  echo "Error: --feat-id is required"
  exit 1
fi

if [[ -z "${INPUT_TYPE}" ]]; then
  echo "Error: --input-type is required"
  exit 1
fi

if [[ "${INPUT_TYPE}" != "prompt" && "${INPUT_TYPE}" != "document" ]]; then
  echo "Error: --input-type must be 'prompt' or 'document', got '${INPUT_TYPE}'"
  exit 1
fi

if [[ -z "${INPUT_VALUE}" ]]; then
  echo "Error: --input-value is required"
  exit 1
fi

# Default output directory
OUTPUT_DIR="${WORKSPACE}/ssot/experience-patches/${FEAT_ID}"

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Validate input before running
if [[ "${INPUT_TYPE}" == "document" ]]; then
  bash "${SCRIPT_DIR}/validate_input.sh" "${INPUT_VALUE}"
fi

# SECURITY: construct JSON using Python to avoid injection
export REQ_ID="req-$(date +%s)-$$"
export FEAT_ID="${FEAT_ID}"
export INPUT_TYPE="${INPUT_TYPE}"
export INPUT_VALUE="${INPUT_VALUE}"

REQUEST_JSON=$(python3 -c "
import json, os
print(json.dumps({
    'api_version': 'v1',
    'command': 'skill.patch-capture',
    'request_id': os.environ.get('REQ_ID', 'req-unknown'),
    'payload': {
        'feat_id': os.environ['FEAT_ID'],
        'input_type': os.environ['INPUT_TYPE'],
        'input_value': os.environ['INPUT_VALUE'],
    },
    'trace': {}
}))" 2>/dev/null)

python -m cli skill patch-capture \
  --request <(echo "${REQUEST_JSON}") \
  --response-out "${OUTPUT_DIR}/response.json" \
  --workspace-root "${WORKSPACE}"

# Validate output if patch file was generated
PATCH_FILE=$(ls "${OUTPUT_DIR}"/UXPATCH-*.yaml 2>/dev/null | head -1 || true)
if [[ -n "${PATCH_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${PATCH_FILE}"
fi
