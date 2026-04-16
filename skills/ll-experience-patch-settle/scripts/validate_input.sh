#!/usr/bin/env bash
# validate_input.sh — Pre-settlement input validation for ll-experience-patch-settle
# Usage: ./validate_input.sh <feat_dir>
set -euo pipefail

FEAT_DIR="${1:-}"
if [[ -z "${FEAT_DIR}" ]]; then
  echo "FAIL: feat_dir required"
  exit 1
fi

# Check FEAT_DIR exists and is a directory
if [[ ! -d "${FEAT_DIR}" ]]; then
  echo "FAIL: feat_dir not found: ${FEAT_DIR}"
  exit 1
fi

# Check patch_registry.json exists
REGISTRY="${FEAT_DIR}/patch_registry.json"
if [[ ! -f "${REGISTRY}" ]]; then
  echo "FAIL: patch_registry.json not found in ${FEAT_DIR}"
  exit 1
fi

# Check at least one UXPATCH-*.yaml file exists
shopt -s nullglob
PATCH_FILES=("${FEAT_DIR}"/UXPATCH-*.yaml)
shopt -u nullglob
if [[ ${#PATCH_FILES[@]} -eq 0 ]]; then
  echo "FAIL: no UXPATCH-*.yaml files found in ${FEAT_DIR}"
  exit 1
fi
PATCH_COUNT=${#PATCH_FILES[@]}

# Validate patch_registry.json is valid JSON
# SECURITY: pass path via sys.argv, NOT string interpolation
python3 -c "
import json, sys
try:
    with open(sys.argv[1], encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict) or 'patches' not in data:
        print('FAIL: patch_registry.json missing required structure')
        sys.exit(1)
    print('OK: input validated (' + str(len(data['patches'])) + ' patches registered, ' + sys.argv[2] + ' patch files found)')
except json.JSONDecodeError as e:
    print('FAIL: invalid JSON in patch_registry.json: ' + str(e))
    sys.exit(1)
" "${REGISTRY}" "${PATCH_COUNT}"
