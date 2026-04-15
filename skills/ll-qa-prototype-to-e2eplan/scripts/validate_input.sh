#!/usr/bin/env bash
# validate_input.sh — Validate input for ll-qa-prototype-to-e2eplan
set -euo pipefail

PROTO_PATH="${1:-}"
if [[ -z "${PROTO_PATH}" ]]; then echo "FAIL: prototype_path required"; exit 1; fi
if [[ ! -f "${PROTO_PATH}" ]]; then echo "FAIL: file not found: ${PROTO_PATH}"; exit 1; fi

for section in "id:" "title:" "entry_point" "journey"; do
  if ! grep -q "${section}" "${PROTO_PATH}" 2>/dev/null; then
    echo "FAIL: prototype missing section: ${section}"; exit 1
  fi
done
echo "OK: input validated"
