#!/usr/bin/env bash
# validate_input.sh — Validate input for render-testset-view
# Accepts variable number of file path arguments
# Determines schema type by checking file content for top-level keys
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "FAIL: at least one input file path required"
  exit 1
fi

detect_schema_type() {
  local file="$1"
  python3 -c "
import yaml, sys
with open('${file}', 'r') as f:
    data = yaml.safe_load(f) or {}
if 'api_test_plan' in data or 'feature_id' in data:
    print('plan')
elif 'api_coverage_manifest' in data or 'items' in data:
    print('manifest')
elif 'api_test_spec' in data or 'case_id' in data:
    print('spec')
elif 'settlement_report' in data or 'chain' in data or 'summary' in data:
    print('settlement')
else:
    print('unknown')
" 2>/dev/null || echo "unknown"
}

ERRORS=0

for input_file in "$@"; do
  # Check file exists
  if [[ ! -f "${input_file}" ]]; then
    echo "FAIL: file not found: ${input_file}"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Detect schema type from file content
  schema_type=$(detect_schema_type "${input_file}")

  if [[ "${schema_type}" == "unknown" ]]; then
    echo "WARN: could not detect schema type for ${input_file}, skipping validation"
    continue
  fi

  # Validate against schema
  python -m cli.lib.qa_schemas --type "${schema_type}" "${input_file}"
  if [[ $? -ne 0 ]]; then
    echo "FAIL: ${input_file} does not conform to ${schema_type} schema"
    ERRORS=$((ERRORS + 1))
  fi
done

if [[ ${ERRORS} -gt 0 ]]; then
  echo "FAIL: ${ERRORS} validation error(s)"
  exit 1
fi

echo "OK: all inputs validated"
