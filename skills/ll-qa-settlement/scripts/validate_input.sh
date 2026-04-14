#!/usr/bin/env bash
# validate_input.sh — Validate input for ll-qa-settlement
set -euo pipefail

MANIFEST_PATH="${1:-}"
if [[ -z "${MANIFEST_PATH}" ]]; then echo "FAIL: manifest_path required"; exit 1; fi
if [[ ! -f "${MANIFEST_PATH}" ]]; then echo "FAIL: file not found: ${MANIFEST_PATH}"; exit 1; fi

python -m cli.lib.qa_schemas --type manifest "${MANIFEST_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: input does not conform to manifest schema"; exit 1; fi

echo "OK: input validated"
