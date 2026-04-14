#!/usr/bin/env bash
# run.sh — Entry point for render-testset-view skill
# Usage: ./run.sh --api-plan <path> --api-manifest <path> --api-spec <path> --api-settlement <path>
#                [--e2e-plan <path> --e2e-manifest <path> --e2e-spec <path> --e2e-settlement <path>]
#                [--output <path>] [--workspace <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
API_PLAN=""
API_MANIFEST=""
API_SPEC=""
API_SETTLEMENT=""
E2E_PLAN=""
E2E_MANIFEST=""
E2E_SPEC=""
E2E_SETTLEMENT=""
OUTPUT_PATH=""
WORKSPACE="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-plan) API_PLAN="$2"; shift 2;;
    --api-manifest) API_MANIFEST="$2"; shift 2;;
    --api-spec) API_SPEC="$2"; shift 2;;
    --api-settlement) API_SETTLEMENT="$2"; shift 2;;
    --e2e-plan) E2E_PLAN="$2"; shift 2;;
    --e2e-manifest) E2E_MANIFEST="$2"; shift 2;;
    --e2e-spec) E2E_SPEC="$2"; shift 2;;
    --e2e-settlement) E2E_SETTLEMENT="$2"; shift 2;;
    --output) OUTPUT_PATH="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

# Check that at least one complete chain (4 artifacts) is provided
API_COMPLETE=false
E2E_COMPLETE=false

if [[ -n "${API_PLAN}" && -n "${API_MANIFEST}" && -n "${API_SPEC}" && -n "${API_SETTLEMENT}" ]]; then
  API_COMPLETE=true
fi

if [[ -n "${E2E_PLAN}" && -n "${E2E_MANIFEST}" && -n "${E2E_SPEC}" && -n "${E2E_SETTLEMENT}" ]]; then
  E2E_COMPLETE=true
fi

if [[ "${API_COMPLETE}" == "false" && "${E2E_COMPLETE}" == "false" ]]; then
  echo "Error: At least one complete chain (API or E2E) with all 4 artifacts is required"
  echo "  API chain: --api-plan --api-manifest --api-spec --api-settlement"
  echo "  E2E chain: --e2e-plan --e2e-manifest --e2e-spec --e2e-settlement"
  exit 1
fi

# Collect all provided input paths for validation
INPUT_PATHS=()
if [[ "${API_COMPLETE}" == "true" ]]; then
  INPUT_PATHS+=("${API_PLAN}" "${API_MANIFEST}" "${API_SPEC}" "${API_SETTLEMENT}")
fi
if [[ "${E2E_COMPLETE}" == "true" ]]; then
  INPUT_PATHS+=("${E2E_PLAN}" "${E2E_MANIFEST}" "${E2E_SPEC}" "${E2E_SETTLEMENT}")
fi

# Validate input before running
bash "${SCRIPT_DIR}/validate_input.sh" "${INPUT_PATHS[@]}"

# Set default output path if not provided
OUTPUT_FILE="${OUTPUT_PATH:-${WORKSPACE}/ssot/tests/.artifacts/testset-view.json}"

# Run the skill via CLI protocol
python -m cli skill render-testset-view \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.render-testset-view",
  "request_id": "req-$(date +%s)-$$",
  "payload": {
    "api_plan_path": "${API_PLAN}",
    "api_manifest_path": "${API_MANIFEST}",
    "api_spec_path": "${API_SPEC}",
    "api_settlement_path": "${API_SETTLEMENT}",
    "e2e_plan_path": "${E2E_PLAN}",
    "e2e_manifest_path": "${E2E_MANIFEST}",
    "e2e_spec_path": "${E2E_SPEC}",
    "e2e_settlement_path": "${E2E_SETTLEMENT}",
    "output_path": "${OUTPUT_FILE}"
  },
  "trace": {}
}
EOF
) \
  --response-out "${WORKSPACE}/.artifacts/qa/render-testset-view/response.json" \
  --workspace-root "${WORKSPACE}"

# Validate output
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
else
  echo "Error: output file not created at ${OUTPUT_FILE}"
  exit 1
fi
