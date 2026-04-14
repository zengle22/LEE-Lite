#!/usr/bin/env bash
# validate_output.sh — Validate release_gate_input.yaml output for ll-qa-gate-evaluate
# Usage: ./validate_output.sh <output_path>
set -euo pipefail

OUTPUT_PATH="${1:-}"
if [[ -z "${OUTPUT_PATH}" ]]; then echo "FAIL: output_path required"; exit 1; fi
if [[ ! -f "${OUTPUT_PATH}" ]]; then echo "FAIL: output file not found"; exit 1; fi

# Validate gate evaluation output structure
python3 -c "
import yaml
import sys
import re

with open('${OUTPUT_PATH}') as f:
    data = yaml.safe_load(f)

# Check top-level key
if 'gate_evaluation' not in data:
    print('FAIL: invalid gate evaluation output: missing top-level key gate_evaluation')
    sys.exit(1)

gate = data['gate_evaluation']

# Check final_decision enum
final_decision = gate.get('final_decision')
if final_decision not in ('pass', 'fail', 'conditional_pass'):
    print(f'FAIL: invalid gate evaluation output: final_decision must be pass/fail/conditional_pass, got {final_decision!r}')
    sys.exit(1)

# Check evidence_hash is 64-char hex string
evidence_hash = gate.get('evidence_hash')
if not evidence_hash or not re.match(r'^[a-f0-9]{64}$', evidence_hash):
    print(f'FAIL: invalid gate evaluation output: evidence_hash must be 64-char hex string, got {evidence_hash!r}')
    sys.exit(1)

# Check all 7 anti_laziness_checks fields
checks = gate.get('anti_laziness_checks', {})
required_checks = [
    'manifest_frozen',
    'cut_records_valid',
    'pending_waivers_counted',
    'evidence_consistent',
    'min_exception_coverage',
    'no_evidence_not_executed',
    'evidence_hash_binding',
]
missing = [c for c in required_checks if c not in checks]
if missing:
    print(f'FAIL: invalid gate evaluation output: missing anti_laziness_checks: {missing}')
    sys.exit(1)

print('OK: output validated')
"
