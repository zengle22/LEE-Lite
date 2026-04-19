#!/usr/bin/env bash
# Validate output for ll-frz-manage
# Usage: validate_output.sh <frz_yaml_path>
set -euo pipefail
frz_path="${1:?frz_yaml_path required}"
if [ ! -f "$frz_path" ]; then
  echo "ERROR: FRZ YAML file not found: $frz_path" >&2
  exit 2
fi
# Use --file to avoid shell injection (Winston)
python -c "
import sys
from cli.lib.frz_schema import MSCValidator
report = MSCValidator.validate_file(sys.argv[1])
print(f'MSC valid: {report[\"msc_valid\"]}')
if not report['msc_valid']:
    print(f'Missing dimensions: {report[\"missing\"]}')
    sys.exit(1)
" "$frz_path"
echo "OK: output validated"

# Check revise-specific fields if revision_type is "revise"
# Try yq first, fall back to python
revision_type=""
if command -v yq &>/dev/null; then
    revision_type=$(yq '.revision_type // "new"' "$frz_path" 2>/dev/null || echo "")
fi
if [ -z "$revision_type" ]; then
    revision_type=$(python -c "
import sys, yaml
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
print(data.get('revision_type', 'new'))
" "$frz_path" 2>/dev/null || echo "new")
fi

if [ "$revision_type" = "revise" ]; then
    prev_frz=""
    reason=""
    if command -v yq &>/dev/null; then
        prev_frz=$(yq '.previous_frz_ref // ""' "$frz_path" 2>/dev/null || echo "")
        reason=$(yq '.revision_reason // ""' "$frz_path" 2>/dev/null || echo "")
    fi
    if [ -z "$prev_frz" ] || [ -z "$reason" ]; then
        prev_frz=$(python -c "
import sys, yaml
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
print(data.get('previous_frz_ref', ''))
" "$frz_path" 2>/dev/null || echo "")
        reason=$(python -c "
import sys, yaml
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
print(data.get('revision_reason', ''))
" "$frz_path" 2>/dev/null || echo "")
    fi
    if [ -z "$prev_frz" ]; then
        echo "WARNING: revise operation missing previous_frz_ref"
    fi
    if [ -z "$reason" ]; then
        echo "WARNING: revise operation missing revision_reason"
    fi
fi

exit 0
