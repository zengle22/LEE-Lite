#!/usr/bin/env bash
set -euo pipefail

python scripts/tech_to_impl.py validate-input --input "$1" --feat-ref "$2" --tech-ref "$3"

