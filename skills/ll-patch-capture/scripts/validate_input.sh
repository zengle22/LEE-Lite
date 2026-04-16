#!/usr/bin/env bash
# validate_input.sh — Validate input document for ll-patch-capture
set -euo pipefail

INPUT_PATH="${1:-}"
if [[ -z "${INPUT_PATH}" ]]; then echo "FAIL: input_path required"; exit 1; fi
if [[ ! -f "${INPUT_PATH}" ]]; then echo "FAIL: file not found: ${INPUT_PATH}"; exit 1; fi

# Validate that the file is parseable YAML (if it's a YAML document)
# SECURITY: pass path via sys.argv, NOT string interpolation
python -c "
import yaml, sys
try:
    with open(sys.argv[1], encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, (dict, list)):
        print('FAIL: input document is not valid YAML')
        sys.exit(1)
    print('OK: input document validated')
except yaml.YAMLError as e:
    print(f'FAIL: invalid YAML: {e}')
    sys.exit(1)
" "${INPUT_PATH}"
