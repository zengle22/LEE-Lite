#!/usr/bin/env bash
# run.sh - Calls test_orchestrator.run_spec_test() via Python
#
# Per ADR-054 §2.6.4 this script orchestrates:
#   Step 1: provision_environment() → ENV file
#   Step 2: spec_to_testset() → SPEC_ADAPTER_COMPAT file
#   Step 3: execute_test_exec_skill() → test execution
#   Step 4: update_manifest() → manifest update

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../../../../.. && pwd)}"

# Parse required environment variables (set by command.py handler)
FEAT_REF="${FEAT_REF:-}"
PROTO_REF="${PROTO_REF:-}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
APP_URL="${APP_URL:-http://localhost:3000}"
API_URL="${API_URL:-}"
MODALITY="${MODALITY:-api}"
COVERAGE_MODE="${COVERAGE_MODE:-smoke}"
RESUME="${RESUME:-false}"
RESUME_FROM="${RESUME_FROM:-}"

# Build Python command
PYTHON_CMD="from pathlib import Path
from cli.lib.test_orchestrator import run_spec_test
import json
import sys

try:
    result = run_spec_test(
        workspace_root=Path('$WORKSPACE_ROOT'),
        feat_ref='$FEAT_REF' if '$FEAT_REF' else None,
        proto_ref='$PROTO_REF' if '$PROTO_REF' else None,
        base_url='$BASE_URL',
        app_url='$APP_URL',
        api_url='$API_URL' if '$API_URL' else None,
        modality='$MODALITY',
        coverage_mode='$COVERAGE_MODE',
        resume=$RESUME,
        resume_from='$RESUME_FROM' if '$RESUME_FROM' else None,
    )
    print(json.dumps({
        'run_id': result.run_id,
        'executed': len(result.case_results),
        'manifest_items': len(result.manifest_items),
        'candidate_path': result.candidate_path,
    }))
    sys.exit(0)
except Exception as e:
    print(json.dumps({'error': str(e)}))
    sys.exit(1)
"

python -c "$PYTHON_CMD"
