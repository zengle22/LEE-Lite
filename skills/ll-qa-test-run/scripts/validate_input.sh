#!/usr/bin/env bash
# validate_input.sh - Validates ll-qa-test-run input parameters
#
# Per ADR-054 §2.6.4 input validation:
# - feat_ref or proto_ref must be provided
# - app_url must be valid URL for E2E chain
# - chain must be api|e2e|both

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get parameters from environment or arguments
FEAT_REF="${FEAT_REF:-}"
PROTO_REF="${PROTO_REF:-}"
APP_URL="${APP_URL:-http://localhost:3000}"
CHAIN="${CHAIN:-api}"

error() {
    echo "ERROR: $1" >&2
    exit 1
}

# Validate: feat_ref or proto_ref must be provided
if [[ -z "$FEAT_REF" && -z "$PROTO_REF" ]]; then
    error "Either --feat-ref or --proto-ref must be provided"
fi

# Validate: chain must be api, e2e, or both
if [[ ! "$CHAIN" =~ ^(api|e2e|both)$ ]]; then
    error "Invalid --chain value: $CHAIN. Must be api, e2e, or both"
fi

# Validate: app_url must be valid URL for E2E chain
if [[ "$CHAIN" =~ ^(e2e|both)$ ]]; then
    if [[ ! "$APP_URL" =~ ^https?:// ]]; then
        error "Invalid --app-url value: $APP_URL. Must be a valid URL for E2E chain"
    fi
fi

echo "Input validation passed"
exit 0
