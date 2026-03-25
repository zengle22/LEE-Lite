#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py freeze-guard --artifacts-dir "$1"

