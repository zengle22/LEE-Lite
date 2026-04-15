#!/usr/bin/env bash
set -euo pipefail
OUTPUT_DIR="${1:-}"
if [[ -z "${OUTPUT_DIR}" ]]; then echo "FAIL: output_dir required"; exit 1; fi
SPEC_FILES=$(find "${OUTPUT_DIR}" -name '*.spec.ts' 2>/dev/null | wc -l)
if [[ "${SPEC_FILES}" -eq 0 ]]; then echo "FAIL: no .spec.ts files found in ${OUTPUT_DIR}"; exit 1; fi
for f in "${OUTPUT_DIR}"/*.spec.ts; do
  if ! grep -q "@playwright/test" "${f}"; then
    echo "FAIL: ${f} missing @playwright/test import"; exit 1
  fi
done
echo "OK: output validated (${SPEC_FILES} .spec.ts files)"
