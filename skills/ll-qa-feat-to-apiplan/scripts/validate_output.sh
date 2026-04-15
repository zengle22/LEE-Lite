#!/usr/bin/env bash
# validate_output.sh — Validate output for ll-qa-feat-to-apiplan
# Usage: ./validate_output.sh <output_path>
set -euo pipefail

OUTPUT_PATH="${1:-}"

if [[ -z "${OUTPUT_PATH}" ]]; then
  echo "FAIL: output_path is required"
  exit 1
fi

if [[ ! -f "${OUTPUT_PATH}" ]]; then
  echo "FAIL: output file not found: ${OUTPUT_PATH}"
  exit 1
fi

# Validate against ADR-047 plan schema
python -m cli.lib.qa_schemas --type plan "${OUTPUT_PATH}"
exit_code=$?

if [[ ${exit_code} -ne 0 ]]; then
  echo "FAIL: output does not conform to api-test-plan schema"
  exit 1
fi

echo "OK: output validated against schema"
