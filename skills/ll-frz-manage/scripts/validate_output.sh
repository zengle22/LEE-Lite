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
exit 0
