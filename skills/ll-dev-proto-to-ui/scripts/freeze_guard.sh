#!/usr/bin/env bash
set -euo pipefail

python scripts/proto_to_ui.py freeze-guard --artifacts-dir "$1"
