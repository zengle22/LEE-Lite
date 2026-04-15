#!/usr/bin/env bash
# validate_output.sh — Validate output for ll-qa-prototype-to-e2eplan
set -euo pipefail

OUTPUT_PATH="${1:-}"
if [[ -z "${OUTPUT_PATH}" ]]; then echo "FAIL: output_path required"; exit 1; fi
if [[ ! -f "${OUTPUT_PATH}" ]]; then echo "FAIL: output file not found: ${OUTPUT_PATH}"; exit 1; fi

python -m cli.lib.qa_schemas --type plan "${OUTPUT_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: output does not conform to e2e-journey-plan schema"; exit 1; fi

echo "OK: output validated against schema"
