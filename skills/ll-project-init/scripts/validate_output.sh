#!/usr/bin/env bash
set -euo pipefail

python scripts/workflow_runtime.py validate-output --artifacts-dir "$1"
