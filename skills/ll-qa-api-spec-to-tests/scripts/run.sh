#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-api-spec-to-tests
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_PATH=""
OUTPUT_DIR=""
WORKSPACE="${PWD}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --spec-path) SPEC_PATH="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) shift;;
  esac
done
if [[ -z "${SPEC_PATH}" ]]; then echo "Error: --spec-path required"; exit 1; fi
bash "${SCRIPT_DIR}/validate_input.sh" "${SPEC_PATH}"
OUTPUT_PATH="${OUTPUT_DIR:-${WORKSPACE}/ssot/tests/api/tests/}"
mkdir -p "${OUTPUT_PATH}"
python -m cli skill api-spec-to-tests \
  --request <(echo "{\"api_version\":\"v1\",\"command\":\"skill.api-spec-to-tests\",\"request_id\":\"req-$(date +%s)-$$\",\"payload\":{\"spec_path\":\"${SPEC_PATH}\",\"output_dir\":\"${OUTPUT_PATH}\"},\"trace\":{}}") \
  --response-out "${WORKSPACE}/.artifacts/qa/api-spec-to-tests/response.json" \
  --workspace-root "${WORKSPACE}"
if [[ -d "${OUTPUT_PATH}" ]] && find "${OUTPUT_PATH}" -name "*.py" -print -quit 2>/dev/null | grep -q .; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_PATH}"
fi
