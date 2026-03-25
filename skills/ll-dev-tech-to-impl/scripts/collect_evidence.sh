#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py collect-evidence --artifacts-dir "$1"

