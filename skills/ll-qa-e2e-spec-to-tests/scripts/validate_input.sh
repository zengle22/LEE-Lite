#!/usr/bin/env bash
set -euo pipefail
SPEC_PATH="${1:-}"
if [[ -z "${SPEC_PATH}" ]]; then echo "FAIL: spec_path required"; exit 1; fi
if [[ ! -f "${SPEC_PATH}" ]]; then echo "FAIL: file not found: ${SPEC_PATH}"; exit 1; fi
python -m cli.lib.qa_schemas --type e2e_spec "${SPEC_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: invalid e2e_spec input"; exit 1; fi
echo "OK: e2e_spec input validated"
