#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_testset.py validate-output --artifacts-dir "$1"
