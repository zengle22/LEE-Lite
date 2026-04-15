#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-e2e-spec-gen
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MANIFEST_PATH=""
OUTPUT_PATH=""
WORKSPACE="${PWD}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest-path) MANIFEST_PATH="$2"; shift 2;;
    --output) OUTPUT_PATH="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) shift;;
  esac
done
if [[ -z "${MANIFEST_PATH}" ]]; then echo "Error: --manifest-path required"; exit 1; fi
bash "${SCRIPT_DIR}/validate_input.sh" "${MANIFEST_PATH}"
OUTPUT_FILE="${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/e2e-spec-gen/e2e-journey-spec.yaml}"
mkdir -p "$(dirname "${OUTPUT_FILE}")"
python -m cli skill e2e-spec-gen \
  --request <(echo "{\"api_version\":\"v1\",\"command\":\"skill.e2e-spec-gen\",\"request_id\":\"req-$(date +%s)-$$\",\"payload\":{\"manifest_path\":\"${MANIFEST_PATH}\",\"output_path\":\"${OUTPUT_FILE}\"},\"trace\":{}}") \
  --response-out "${WORKSPACE}/.artifacts/qa/e2e-spec-gen/response.json" \
  --workspace-root "${WORKSPACE}"
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
fi
