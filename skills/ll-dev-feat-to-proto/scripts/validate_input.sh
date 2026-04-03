#!/usr/bin/env bash
set -euo pipefail

python scripts/feat_to_proto.py validate-input --input "$1" --feat-ref "$2"
