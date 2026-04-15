#!/usr/bin/env bash
# validate_input.sh — Validate input for ll-qa-api-manifest-init
set -euo pipefail

PLAN_PATH="${1:-}"
if [[ -z "${PLAN_PATH}" ]]; then echo "FAIL: plan_path required"; exit 1; fi
if [[ ! -f "${PLAN_PATH}" ]]; then echo "FAIL: file not found: ${PLAN_PATH}"; exit 1; fi

python -m cli.lib.qa_schemas --type plan "${PLAN_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: input does not conform to api-test-plan schema"; exit 1; fi

echo "OK: input validated"
