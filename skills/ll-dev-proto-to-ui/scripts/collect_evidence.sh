#!/usr/bin/env bash
set -euo pipefail

python scripts/proto_to_ui.py collect-evidence --artifacts-dir "$1"
