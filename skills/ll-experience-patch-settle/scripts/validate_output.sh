#!/usr/bin/env bash
# validate_output.sh — Post-settlement output validation for ll-experience-patch-settle
# Usage: ./validate_output.sh <resolved_patches.yaml>
set -euo pipefail

OUTPUT_PATH="${1:-}"
if [[ -z "${OUTPUT_PATH}" ]]; then
  echo "FAIL: resolved_patches.yaml path required"
  exit 1
fi
if [[ ! -f "${OUTPUT_PATH}" ]]; then
  echo "FAIL: resolved_patches.yaml not found: ${OUTPUT_PATH}"
  exit 1
fi

# Validate YAML structure and required fields
# SECURITY: pass path via sys.argv, NOT string interpolation
python3 -c "
import yaml, sys

path = sys.argv[1]

try:
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
except yaml.YAMLError as e:
    print('FAIL: invalid YAML in resolved_patches.yaml: ' + str(e))
    sys.exit(1)

if not isinstance(data, dict):
    print('FAIL: resolved_patches.yaml is not a valid YAML dict')
    sys.exit(1)

# Check settlement_report top-level key exists
if 'settlement_report' not in data:
    print('FAIL: missing settlement_report top-level key')
    sys.exit(1)

report = data['settlement_report']

# Check generated_at is non-empty
if not report.get('generated_at'):
    print('FAIL: settlement_report.generated_at is empty or missing')
    sys.exit(1)

# Check total_settled > 0
total = report.get('total_settled', 0)
if not isinstance(total, int) or total <= 0:
    print('FAIL: settlement_report.total_settled must be > 0, got: ' + str(total))
    sys.exit(1)

# Check results is a non-empty list
results = report.get('results')
if not isinstance(results, list) or len(results) == 0:
    print('FAIL: settlement_report.results is not a non-empty list')
    sys.exit(1)

# Verify total_settled matches results count
if total != len(results):
    print('FAIL: total_settled (' + str(total) + ') does not match results count (' + str(len(results)) + ')')
    sys.exit(1)

print('OK: settlement report validated (' + str(total) + ' patches settled)')
" "${OUTPUT_PATH}"
