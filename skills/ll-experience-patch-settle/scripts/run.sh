#!/usr/bin/env bash
# run.sh — Entry point for ll-experience-patch-settle skill
# Usage: ./run.sh --feat-id <id> [--workspace <dir>] [--change-class <visual|interaction|semantic>] [--auto-approve]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
FEAT_ID=""
WORKSPACE="${PWD}"
CHANGE_CLASS_FILTER=""
AUTO_APPROVE="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --feat-id) FEAT_ID="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    --change-class) CHANGE_CLASS_FILTER="$2"; shift 2;;
    --auto-approve) AUTO_APPROVE="true"; shift;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "${FEAT_ID}" ]]; then
  echo "Error: --feat-id is required"
  exit 1
fi

# Security: validate FEAT_ID before any filesystem operations
if ! echo "${FEAT_ID}" | grep -qE '^[a-zA-Z0-9][a-zA-Z0-9._-]*$'; then
    echo "Error: --feat-id contains invalid characters"
    exit 1
fi

# Resolve output directory
OUTPUT_DIR="${WORKSPACE}/ssot/experience-patches/${FEAT_ID}"

# Validate inputs before running settlement
if [[ -d "${OUTPUT_DIR}" ]]; then
  bash "${SCRIPT_DIR}/validate_input.sh" "${OUTPUT_DIR}"
fi

# SECURITY: construct JSON using Python to avoid bash string interpolation injection
export REQ_ID="req-$(date +%s)-$$"
export FEAT_ID="${FEAT_ID}"
export CHANGE_CLASS_FILTER="${CHANGE_CLASS_FILTER:-}"
export AUTO_APPROVE="${AUTO_APPROVE}"

REQUEST_JSON=$(python3 -c "
import json, os
print(json.dumps({
    'api_version': 'v1',
    'command': 'skill.patch-settle',
    'request_id': os.environ.get('REQ_ID', 'req-unknown'),
    'payload': {
        'feat_id': os.environ['FEAT_ID'],
        'change_class_filter': os.environ.get('CHANGE_CLASS_FILTER', ''),
        'auto_approve': os.environ.get('AUTO_APPROVE', 'true') == 'true',
    },
    'trace': {}
}))" 2>/dev/null)

# Run the skill via CLI protocol
python -m cli skill patch-settle \
  --request <(echo "${REQUEST_JSON}") \
  --response-out "${OUTPUT_DIR}/response.json" \
  --workspace-root "${WORKSPACE}"

# Validate output if settlement report was generated
if [[ -f "${OUTPUT_DIR}/resolved_patches.yaml" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_DIR}/resolved_patches.yaml"
fi
