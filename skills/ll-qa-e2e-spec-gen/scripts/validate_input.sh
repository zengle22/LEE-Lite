#!/usr/bin/env bash
set -euo pipefail
MANIFEST_PATH="${1:-}"
if [[ -z "${MANIFEST_PATH}" ]]; then echo "FAIL: manifest_path required"; exit 1; fi
if [[ ! -f "${MANIFEST_PATH}" ]]; then echo "FAIL: file not found"; exit 1; fi
python -m cli.lib.qa_schemas --type manifest "${MANIFEST_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: invalid manifest input"; exit 1; fi
echo "OK: input validated"
