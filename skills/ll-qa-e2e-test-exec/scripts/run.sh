#!/usr/bin/env bash
# run.sh — Code-driven entry point for ll-qa-e2e-test-exec
# This skill is CODE-DRIVEN (not Prompt-first). Execution happens via e2e_test_exec.py.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPEC_PATH=""
TEST_DIR=""
MANIFEST_PATH=""
OUTPUT_DIR=""
WORKSPACE="${PWD}"
TARGET_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --spec-path) SPEC_PATH="$2"; shift 2;;
    --test-dir) TEST_DIR="$2"; shift 2;;
    --manifest-path) MANIFEST_PATH="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --workspace) WORKSPACE="$2"; shift 2;;
    --target-url) TARGET_URL="$2"; shift 2;;
    *) shift;;
  esac
done

# Require essential inputs
if [[ -z "${SPEC_PATH}" ]]; then echo "Error: --spec-path required"; exit 1; fi
if [[ -z "${TEST_DIR}" ]]; then echo "Error: --test-dir required"; exit 1; fi
if [[ -z "${MANIFEST_PATH}" ]]; then echo "Error: --manifest-path required"; exit 1; fi

# Validate inputs
bash "${SCRIPT_DIR}/validate_input.sh" "${SPEC_PATH}" "${TEST_DIR}" "${MANIFEST_PATH}"

RUN_ID="run-$(date +%s)-$$"
EVIDENCE_DIR="${OUTPUT_DIR:-${WORKSPACE}/ssot/tests/.artifacts/evidence/e2e/${RUN_ID}}"
mkdir -p "${EVIDENCE_DIR}"

# Ensure Playwright installed
if [ ! -d "${WORKSPACE}/node_modules/@playwright/test" ]; then
  echo "Installing @playwright/test..."
  cd "${WORKSPACE}" && npm install @playwright/test@^1.58.2
fi
npx playwright install chromium

# Execute via Python module (code-driven, not LLM)
python -c "
import sys; sys.path.insert(0, '${WORKSPACE}/cli/lib')
from e2e_test_exec import run_e2e_test_exec
result = run_e2e_test_exec(
    spec_path='${SPEC_PATH}',
    test_dir='${TEST_DIR}',
    manifest_path='${MANIFEST_PATH}',
    evidence_dir='${EVIDENCE_DIR}',
    run_id='${RUN_ID}',
    target_url='${TARGET_URL}',
)
import json; print(json.dumps(result, indent=2, default=str))
"

# Validate outputs
bash "${SCRIPT_DIR}/validate_output.sh" "${EVIDENCE_DIR}"
