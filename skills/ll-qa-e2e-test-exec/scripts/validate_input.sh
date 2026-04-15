#!/usr/bin/env bash
# validate_input.sh — Validate inputs for ll-qa-e2e-test-exec
set -euo pipefail
SPEC_PATH="${1:-}"
TEST_DIR="${2:-}"
MANIFEST_PATH="${3:-}"

if [[ -z "${SPEC_PATH}" ]]; then echo "FAIL: spec_path required"; exit 1; fi
if [[ ! -f "${SPEC_PATH}" ]]; then echo "FAIL: spec file not found: ${SPEC_PATH}"; exit 1; fi

# Validate e2e spec passes schema validation
python -m cli.lib.qa_schemas --type e2e_spec "${SPEC_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: invalid e2e_spec input"; exit 1; fi

if [[ -z "${TEST_DIR}" ]]; then echo "FAIL: test_dir required"; exit 1; fi
if [[ ! -d "${TEST_DIR}" ]]; then echo "FAIL: test directory not found: ${TEST_DIR}"; exit 1; fi

# Check test_dir has at least one .spec.ts file
TS_FILES=$(find "${TEST_DIR}" -name "*.spec.ts" -type f 2>/dev/null)
if [[ -z "${TS_FILES}" ]]; then echo "FAIL: no .spec.ts test files found in ${TEST_DIR}"; exit 1; fi

if [[ -z "${MANIFEST_PATH}" ]]; then echo "FAIL: manifest_path required"; exit 1; fi
if [[ ! -f "${MANIFEST_PATH}" ]]; then echo "FAIL: manifest file not found: ${MANIFEST_PATH}"; exit 1; fi

# Validate manifest passes schema validation
python -m cli.lib.qa_schemas --type manifest "${MANIFEST_PATH}"
if [[ $? -ne 0 ]]; then echo "FAIL: invalid manifest input"; exit 1; fi

echo "OK: all inputs validated"
