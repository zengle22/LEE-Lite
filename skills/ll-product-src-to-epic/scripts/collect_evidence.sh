#!/usr/bin/env bash
set -euo pipefail

python scripts/src_to_epic.py collect-evidence --artifacts-dir "$1"
