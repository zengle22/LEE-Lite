#!/usr/bin/env bash
# run.sh — Entry point for ll-qa-settlement skill
# Usage: ./run.sh --manifest-path <path> [--chain api|e2e] [--output-dir <path>] [--workspace <dir>]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
MANIFEST_PATH=""
CHAIN="api"
OUTPUT_DIR=""
WORKSPACE="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --manifest-path) MANIFEST_PATH="$2"; shift 2;;
    --chain) CHAIN="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

if [[ -z "${MANIFEST_PATH}" ]]; then
  echo "Error: --manifest-path is required"
  exit 1
fi

# Validate chain value
if [[ "${CHAIN}" != "api" && "${CHAIN}" != "e2e" ]]; then
  echo "Error: --chain must be 'api' or 'e2e', got '${CHAIN}'"
  exit 1
fi

# Default output directory
OUTPUT_DIR="${OUTPUT_DIR:-${WORKSPACE}/ssot/tests/.artifacts/settlement}"

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Validate input before running
bash "${SCRIPT_DIR}/validate_input.sh" "${MANIFEST_PATH}"

# Run the skill via CLI protocol
python -m cli skill settlement \
  --request <(cat <<EOF
{
  "api_version": "v1",
  "command": "skill.settlement",
  "request_id": "req-$(date +%s)-$$",
  "payload": {
    "manifest_path": "${MANIFEST_PATH}",
    "chain": "${CHAIN}",
    "output_dir": "${OUTPUT_DIR}"
  },
  "trace": {}
}
EOF
) \
  --response-out "${OUTPUT_DIR}/response.json" \
  --workspace-root "${WORKSPACE}"

# Validate output
OUTPUT_FILE="${OUTPUT_DIR}/${CHAIN}-settlement-report.yaml"
if [[ -f "${OUTPUT_FILE}" ]]; then
  bash "${SCRIPT_DIR}/validate_output.sh" "${OUTPUT_FILE}"
fi
