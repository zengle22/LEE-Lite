#!/usr/bin/env bash
# validate_input.sh — Validate all 5 input artifacts for ll-qa-gate-evaluate
# Usage: ./validate_input.sh <api_manifest> <e2e_manifest> <api_settlement> <e2e_settlement> <waivers>
set -euo pipefail

API_MANIFEST="${1:-}"
E2E_MANIFEST="${2:-}"
API_SETTLEMENT="${3:-}"
E2E_SETTLEMENT="${4:-}"
WAIVERS="${5:-}"

# Check all 5 files exist
if [[ ! -f "${API_MANIFEST}" ]]; then echo "FAIL: file not found: ${API_MANIFEST}"; exit 1; fi
if [[ ! -f "${E2E_MANIFEST}" ]]; then echo "FAIL: file not found: ${E2E_MANIFEST}"; exit 1; fi
if [[ ! -f "${API_SETTLEMENT}" ]]; then echo "FAIL: file not found: ${API_SETTLEMENT}"; exit 1; fi
if [[ ! -f "${E2E_SETTLEMENT}" ]]; then echo "FAIL: file not found: ${E2E_SETTLEMENT}"; exit 1; fi
if [[ ! -f "${WAIVERS}" ]]; then echo "FAIL: file not found: ${WAIVERS}"; exit 1; fi

# Validate API manifest
python -m cli.lib.qa_schemas --type manifest "${API_MANIFEST}"
if [[ $? -ne 0 ]]; then
  echo "FAIL: API manifest does not conform to schema"
  exit 1
fi

# Validate E2E manifest
python -m cli.lib.qa_schemas --type manifest "${E2E_MANIFEST}"
if [[ $? -ne 0 ]]; then
  echo "FAIL: E2E manifest does not conform to schema"
  exit 1
fi

# Validate API settlement
python -m cli.lib.qa_schemas --type settlement "${API_SETTLEMENT}"
if [[ $? -ne 0 ]]; then
  echo "FAIL: API settlement does not conform to schema"
  exit 1
fi

# Validate E2E settlement
python -m cli.lib.qa_schemas --type settlement "${E2E_SETTLEMENT}"
if [[ $? -ne 0 ]]; then
  echo "FAIL: E2E settlement does not conform to schema"
  exit 1
fi

# Validate waivers file is valid YAML
python -c "import yaml, sys; yaml.safe_load(open('${WAIVERS}'))" || {
  echo "FAIL: waivers file is not valid YAML"
  exit 1
}

echo "OK: all 5 inputs validated"
