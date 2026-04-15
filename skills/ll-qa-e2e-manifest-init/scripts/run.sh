#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-e2e-manifest-init
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAN_PATH=""
OUTPUT_PATH=""
WORKSPACE="${PWD}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan-path) PLAN_PATH="$2"; shift 2;;
    --output) OUTPUT_PATH="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) shift;;
  esac
done
if [[ -z "${PLAN_PATH}" ]]; then echo "Error: --plan-path required"; exit 1; fi
bash "${SCRIPT_DIR}/validate_input.sh" "${PLAN_PATH}"
OUTPUT_FILE="${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/e2e-manifest-init/e2e-coverage-manifest.yaml}"
mkdir -p "$(dirname "${OUTPUT_FILE}")"
python -m cli skill e2e-manifest-init \
  --request <(echo "{\"api_version\":\"v1\",\"command\":\"skill.e2e-manifest-init\",\"request_id\":\"req-$(date +%s)-$$\",\"payload\":{\"plan_path\":\"${PLAN_PATH}\",\"output_path\":\"${OUTPUT_FILE}\"},\"trace\":{}}") \
  --response-out "${WORKSPACE}/.artifacts/qa/e2e-manifest-init/response.json" \
  --workspace-root "${WORKSPACE}"
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
fi
