#!/usr/bin/env bash
# validate_output.sh — Validate generated patch YAML for ll-patch-capture
set -euo pipefail

OUTPUT_PATH="${1:-}"
if [[ -z "${OUTPUT_PATH}" ]]; then echo "FAIL: output_path required"; exit 1; fi
if [[ ! -f "${OUTPUT_PATH}" ]]; then echo "FAIL: output file not found: ${OUTPUT_PATH}"; exit 1; fi

if ! python -m cli.lib.patch_schema --type patch "${OUTPUT_PATH}"; then
    echo "FAIL: invalid patch output"
    exit 1
fi
echo "OK: output validated"
