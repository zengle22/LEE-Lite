#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: scripts/freeze_guard.sh <artifacts-dir>"
  echo "Compatibility wrapper for scripts/validate_package_readiness.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/validate_package_readiness.sh" "$1"
