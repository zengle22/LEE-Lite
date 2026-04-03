#!/usr/bin/env bash
set -euo pipefail

python scripts/proto_to_ui.py validate-input --input "$1"
