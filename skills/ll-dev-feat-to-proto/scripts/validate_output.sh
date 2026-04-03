#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_proto.py validate-output --artifacts-dir "$1"
