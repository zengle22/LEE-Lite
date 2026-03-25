#!/usr/bin/env bash
set -euo pipefail

python scripts/src_to_epic.py validate-input --input "$1"
