#!/usr/bin/env bash
set -euo pipefail

python scripts/proto_to_ui.py validate-output --artifacts-dir "$1"
