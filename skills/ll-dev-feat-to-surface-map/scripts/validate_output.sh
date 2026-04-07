#!/usr/bin/env bash
set -euo pipefail
python scripts/feat_to_surface_map.py validate-output --artifacts-dir "$1"
