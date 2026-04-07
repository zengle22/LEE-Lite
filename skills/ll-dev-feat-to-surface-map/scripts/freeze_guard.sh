#!/usr/bin/env bash
set -euo pipefail
python scripts/feat_to_surface_map.py freeze-guard --artifacts-dir "$1"
