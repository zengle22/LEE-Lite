#!/usr/bin/env bash
set -euo pipefail
OUTPUT_DIR="${1:-}"
if [[ -z "${OUTPUT_DIR}" ]]; then echo "FAIL: output_dir required"; exit 1; fi
if [[ ! -d "${OUTPUT_DIR}" ]]; then echo "FAIL: output directory not found"; exit 1; fi
PY_FILES=$(find "${OUTPUT_DIR}" -name "*.py" -type f 2>/dev/null)
if [[ -z "${PY_FILES}" ]]; then echo "FAIL: no .py files found in output directory"; exit 1; fi
ERRORS=0
for f in ${PY_FILES}; do
  python -m py_compile "${f}" 2>&1 || ERRORS=$((ERRORS + 1))
done
if [[ ${ERRORS} -gt 0 ]]; then echo "FAIL: ${ERRORS} file(s) failed py_compile"; exit 1; fi
echo "OK: all generated .py files compile successfully"
