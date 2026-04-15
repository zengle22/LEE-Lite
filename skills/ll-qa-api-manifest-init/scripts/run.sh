#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-api-manifest-init skill
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

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

if [[ -z "${PLAN_PATH}" ]]; then
  echo "Error: --plan-path is required"; exit 1
fi

bash "${SCRIPT_DIR}/validate_input.sh" "${PLAN_PATH}"

python -m cli skill api-manifest-init \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.api-manifest-init",
  "request_id": "req-$(date +%s)-$$",
  "payload": {
    "plan_path": "${PLAN_PATH}",
    "output_path": "${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/api-manifest-init/api-coverage-manifest.yaml}"
  },
  "trace": {}
}
EOF
) \
  --response-out "${WORKSPACE}/.artifacts/qa/api-manifest-init/response.json" \
  --workspace-root "${WORKSPACE}"

OUTPUT_FILE="${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/api-manifest-init/api-coverage-manifest.yaml}"
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
fi
