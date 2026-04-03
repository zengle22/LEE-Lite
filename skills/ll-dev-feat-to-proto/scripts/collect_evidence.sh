#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_proto.py collect-evidence --artifacts-dir "$1"
