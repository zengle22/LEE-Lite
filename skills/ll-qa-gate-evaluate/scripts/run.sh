#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-gate-evaluate skill
# Usage: ./run.sh --api-manifest <path> --e2e-manifest <path> --api-settlement <path> --e2e-settlement <path> --waivers <path> [--output <path>] [--workspace <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
API_MANIFEST=""
E2E_MANIFEST=""
API_SETTLEMENT=""
E2E_SETTLEMENT=""
WAIVERS=""
OUTPUT_PATH=""
WORKSPACE="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-manifest) API_MANIFEST="$2"; shift 2;;
    --e2e-manifest) E2E_MANIFEST="$2"; shift 2;;
    --api-settlement) API_SETTLEMENT="$2"; shift 2;;
    --e2e-settlement) E2E_SETTLEMENT="$2"; shift 2;;
    --waivers) WAIVERS="$2"; shift 2;;
    --output) OUTPUT_PATH="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

# Collect missing inputs
MISSING=""
if [[ -z "${API_MANIFEST}" ]]; then MISSING="${MISSING} --api-manifest"; fi
if [[ -z "${E2E_MANIFEST}" ]]; then MISSING="${MISSING} --e2e-manifest"; fi
if [[ -z "${API_SETTLEMENT}" ]]; then MISSING="${MISSING} --api-settlement"; fi
if [[ -z "${E2E_SETTLEMENT}" ]]; then MISSING="${MISSING} --e2e-settlement"; fi
if [[ -z "${WAIVERS}" ]]; then MISSING="${MISSING} --waivers"; fi

if [[ -n "${MISSING}" ]]; then
  echo "Error: missing required arguments:${MISSING}"
  exit 1
fi

# Validate all 5 inputs before running skill
bash "${SCRIPT_DIR}/validate_input.sh" \
  "${API_MANIFEST}" \
  "${E2E_MANIFEST}" \
  "${API_SETTLEMENT}" \
  "${E2E_SETTLEMENT}" \
  "${WAIVERS}"

# Default output path
OUTPUT_FILE="${OUTPUT_PATH:-${WORKSPACE}/ssot/tests/.artifacts/settlement/release_gate_input.yaml}"

# Run the skill via CLI protocol
python -m cli skill gate-evaluate \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.gate-evaluate",
  "request_id": "req-$(date +%s)-$$",
  "payload": {
    "api_manifest": "${API_MANIFEST}",
    "e2e_manifest": "${E2E_MANIFEST}",
    "api_settlement": "${API_SETTLEMENT}",
    "e2e_settlement": "${E2E_SETTLEMENT}",
    "waivers": "${WAIVERS}",
    "output_path": "${OUTPUT_FILE}"
  },
  "trace": {}
}
EOF
) \
  --response-out "${WORKSPACE}/.artifacts/qa/gate-evaluate/response.json" \
  --workspace-root "${WORKSPACE}"

# Validate output
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
else
  echo "FAIL: output file was not generated: ${OUTPUT_FILE}"
  exit 1
fi
