#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-prototype-to-e2eplan skill
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

PROTO_PATH=""
OUTPUT_PATH=""
WORKSPACE="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --proto-path) PROTO_PATH="$2"; shift 2;;
    --output) OUTPUT_PATH="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) shift;;
  esac
done

if [[ -z "${PROTO_PATH}" ]]; then
  echo "Error: --proto-path is required"; exit 1
fi

bash "${SCRIPT_DIR}/validate_input.sh" "${PROTO_PATH}"

python -m cli skill prototype-to-e2eplan \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.prototype-to-e2eplan",
  "request_id": "req-$(date +%s)-$$",
  "payload": {
    "prototype_path": "${PROTO_PATH}",
    "output_path": "${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/prototype-to-e2eplan/e2e-journey-plan.yaml}"
  },
  "trace": {}
}
EOF
) \
  --response-out "${WORKSPACE}/.artifacts/qa/prototype-to-e2eplan/response.json" \
  --workspace-root "${WORKSPACE}"

OUTPUT_FILE="${OUTPUT_PATH:-${WORKSPACE}/.artifacts/qa/prototype-to-e2eplan/e2e-journey-plan.yaml}"
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
fi
