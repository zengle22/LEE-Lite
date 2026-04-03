#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_ui_route.py validate-input --input "$1" --feat-ref "$2"
