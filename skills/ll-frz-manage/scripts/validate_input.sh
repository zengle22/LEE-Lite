#!/usr/bin/env bash
# Validate input for ll-frz-manage
# Usage: validate_input.sh <doc_dir>
set -euo pipefail
doc_dir="${1:?doc_dir required}"
if [ ! -d "$doc_dir" ]; then
  echo "ERROR: doc_dir '$doc_dir' is not a directory" >&2
  exit 2
fi
echo "OK: input directory validated"
exit 0
