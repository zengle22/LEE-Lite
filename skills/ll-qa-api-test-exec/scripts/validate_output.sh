#!/usr/bin/env bash
# validate_output.sh — Validate evidence outputs for ll-qa-api-test-exec
set -euo pipefail
EVIDENCE_DIR="${1:-}"
SPEC_PATH="${2:-}"

if [[ -z "${EVIDENCE_DIR}" ]]; then echo "FAIL: evidence_dir required"; exit 1; fi
if [[ ! -d "${EVIDENCE_DIR}" ]]; then echo "FAIL: evidence directory not found: ${EVIDENCE_DIR}"; exit 1; fi

# Check evidence YAML files exist
EVIDENCE_FILES=$(find "${EVIDENCE_DIR}" -name "*.evidence.yaml" -type f 2>/dev/null)
if [[ -z "${EVIDENCE_FILES}" ]]; then
  echo "FAIL: no evidence YAML files found in ${EVIDENCE_DIR}"
  exit 1
fi

# Validate each evidence file passes validate_evidence schema check
ERRORS=0
for f in ${EVIDENCE_FILES}; do
  python -m cli.lib.qa_schemas --type evidence "${f}" || ERRORS=$((ERRORS + 1))
done

if [[ ${ERRORS} -gt 0 ]]; then
  echo "FAIL: ${ERRORS} evidence file(s) failed schema validation"
  exit 1
fi

echo "OK: all evidence files validated (${EVIDENCE_DIR})"
