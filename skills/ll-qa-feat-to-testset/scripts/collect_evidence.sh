#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_testset.py collect-evidence --artifacts-dir "$1"
