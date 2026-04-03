#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_ui_route.py freeze-guard --artifacts-dir "$1"
