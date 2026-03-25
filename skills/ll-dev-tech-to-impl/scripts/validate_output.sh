#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py validate-output --artifacts-dir "$1"

