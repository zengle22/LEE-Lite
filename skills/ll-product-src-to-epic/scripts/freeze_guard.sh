#!/usr/bin/env bash
set -euo pipefail

python scripts/src_to_epic.py freeze-guard --artifacts-dir "$1"
