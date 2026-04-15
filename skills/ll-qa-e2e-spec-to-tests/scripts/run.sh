#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-e2e-spec-to-tests
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
OUTPUT_TARGET="${OUTPUT_DIR:-${WORKSPACE}/ssot/tests/e2e/}"
mkdir -p "${OUTPUT_TARGET}"
python -m cli skill e2e-spec-to-tests \
  --request <(echo "{\"api_version\":\"v1\",\"command\":\"skill.e2e-spec-to-tests\",\"request_id\":\"req-$(date +%s)-$$\",\"payload\":{\"spec_path\":\"${SPEC_PATH}\",\"output_dir\":\"${OUTPUT_TARGET}\"},\"trace\":{}}") \
  --response-out "${WORKSPACE}/.artifacts/qa/e2e-spec-to-tests/response.json" \
  --workspace-root "${WORKSPACE}"
if [[ -n "$(find "${OUTPUT_TARGET}" -name '*.spec.ts' 2>/dev/null)" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_TARGET}"
fi
