#!/usr/bin/env bash
# validate_output.sh — Validate output for render-testset-view
# Accepts output path as $1
set -euo pipefail

OUTPUT_PATH="${1:-}"
if [[ -z "${OUTPUT_PATH}" ]]; then
  echo "FAIL: output_path required"
  exit 1
fi

if [[ ! -f "${OUTPUT_PATH}" ]]; then
  echo "FAIL: output file not found: ${OUTPUT_PATH}"
  exit 1
fi

# Validate output structure using inline Python
python3 -c "
import json, sys

with open('${OUTPUT_PATH}', 'r') as f:
    data = json.load(f)

errors = []

# Check required top-level string fields
for key in ['assigned_id', 'test_set_ref', 'title']:
    if key not in data:
        errors.append(f'missing required key: {key}')
    elif not isinstance(data[key], str) or len(data[key]) == 0:
        errors.append(f'{key} must be a non-empty string')

# Check functional_areas is non-empty array
if 'functional_areas' not in data:
    errors.append('missing required key: functional_areas')
elif not isinstance(data['functional_areas'], list) or len(data['functional_areas']) == 0:
    errors.append('functional_areas must be a non-empty array')

# Check coverage_matrix is array with required fields
if 'coverage_matrix' not in data:
    errors.append('missing required key: coverage_matrix')
elif not isinstance(data['coverage_matrix'], list):
    errors.append('coverage_matrix must be an array')
elif len(data['coverage_matrix']) == 0:
    errors.append('coverage_matrix must be non-empty')
else:
    for i, entry in enumerate(data['coverage_matrix']):
        if not isinstance(entry, dict):
            errors.append(f'coverage_matrix[{i}] must be an object')
            continue
        if 'coverage_id' not in entry:
            errors.append(f'coverage_matrix[{i}] missing coverage_id')
        if 'capability' not in entry:
            errors.append(f'coverage_matrix[{i}] missing capability')
        if 'lifecycle_status' not in entry:
            errors.append(f'coverage_matrix[{i}] missing lifecycle_status')
        if 'passed' not in entry:
            errors.append(f'coverage_matrix[{i}] missing passed')
        if 'failed' not in entry:
            errors.append(f'coverage_matrix[{i}] missing failed')

if errors:
    for e in errors:
        print(f'FAIL: invalid testset view output: {e}')
    sys.exit(1)

print('OK: output validated')
"
