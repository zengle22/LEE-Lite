#!/usr/bin/env bash
set -euo pipefail

python scripts/workflow_runtime.py validate-package-readiness --artifacts-dir "$1"
