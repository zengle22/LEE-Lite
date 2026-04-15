#!/usr/bin/env bash
# validate_input.sh — Validate input for ll-qa-feat-to-apiplan
# Usage: ./validate_input.sh <feat_path> <feat_ref> <tech_ref>
set -euo pipefail

FEAT_PATH="${1:-}"

if [[ -z "${FEAT_PATH}" ]]; then
  echo "FAIL: feat_path is required"
  exit 1
fi

if [[ ! -f "${FEAT_PATH}" ]]; then
  echo "FAIL: feat file not found: ${FEAT_PATH}"
  exit 1
fi

# Check FEAT has required sections
for section in "id:" "title:" "status:" "Scope:" "Acceptance"; do
  if ! grep -q "${section}" "${FEAT_PATH}" 2>/dev/null; then
    echo "FAIL: FEAT missing required section: ${section}"
    exit 1
  fi
done

echo "OK: input validated"
