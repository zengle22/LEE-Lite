#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-feat-to-apiplan skill
# Usage: ./run.sh --feat-path <path> [--output <path>] [--workspace <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
FEAT_PATH=""
OUTPUT_PATH=""
WORKSPACE="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --feat-path) FEAT_PATH="$2"; shift 2;;
    --output) OUTPUT_PATH="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "${FEAT_PATH}" ]]; then
  echo "Error: --feat-path is required"
  exit 1
fi

# Validate input before running
bash "${SCRIPT_DIR}/validate_input.sh" "${FEAT_PATH}" "" ""

# Run the skill via CLI protocol
python -m cli skill feat-to-apiplan \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.feat-to-apiplan",
  "request_id": "req-$(date +%s)-$$",
  "payload": {
    "feat_path": "${FEAT_PATH}",
    "output_path": "${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/feat-to-apiplan/api-test-plan.yaml}"
  },
  "trace": {}
}
EOF
) \
  --response-out "${WORKSPACE}/.artifacts/qa/feat-to-apiplan/response.json" \
  --workspace-root "${WORKSPACE}"

# Validate output
OUTPUT_FILE="${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/feat-to-apiplan/api-test-plan.yaml}"
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
fi
