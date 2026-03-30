#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_ui.py freeze-guard --artifacts-dir "$1"
