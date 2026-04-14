#!/usr/bin/env bash
set -euo pipefail
OUTPUT_PATH="${1:-}"
if [[ -z "${OUTPUT_PATH}" ]]; then echo "FAIL: output_path required"; exit 1; fi
if [[ ! -f "${OUTPUT_PATH}" ]]; then echo "FAIL: output file not found"; exit 1; fi
python -m cli.lib.qa_schemas --type settlement "${OUTPUT_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: invalid settlement output"; exit 1; fi
echo "OK: output validated"
