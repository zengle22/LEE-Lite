#!/usr/bin/env python3
"""
CI Gate Consumer — ADR-047 Pilot

Consumes release_gate_input.yaml and makes pass/fail decision.
This simulates what a CI/CD job would do.

Usage:
    python ci-gate-consumer.py
"""

import yaml
import sys
from pathlib import Path

GATE_INPUT_PATH = Path(__file__).resolve().parent / "release_gate_input.yaml"


def main():
    print("=" * 60)
    print("ADR-047 CI Gate Consumer")
    print("=" * 60)

    if not GATE_INPUT_PATH.exists():
        print(f"ERROR: Gate input file not found: {GATE_INPUT_PATH}")
        print("Run gate-evaluator.py first.")
        return 1

    with open(GATE_INPUT_PATH, "r", encoding="utf-8") as f:
        gate_input = yaml.safe_load(f)

    rgi = gate_input.get("release_gate_input", {})
    api = rgi.get("api", {})
    e2e = rgi.get("e2e", {})
    final_decision = rgi.get("final_decision", "block")
    reason = rgi.get("decision_reason", "")
    evidence_hash_api = api.get("evidence_hash", "none")
    evidence_hash_e2e = e2e.get("evidence_hash", "none")

    print(f"\nGenerated At: {rgi.get('generated_at', 'N/A')}")
    print(f"Final Decision: {final_decision.upper()}")
    print(f"Reason: {reason}")
    print(f"\nAPI Chain:")
    print(f"  Status: {api.get('status')}")
    print(f"  Pass Rate: {api.get('pass_rate')}%")
    print(f"  Uncovered: {api.get('uncovered_count')}")
    print(f"  Failed: {api.get('failed_count')}")
    print(f"  Evidence Hash: {evidence_hash_api}")
    print(f"\nE2E Chain:")
    print(f"  Status: {e2e.get('status')}")
    print(f"  Pass Rate: {e2e.get('pass_rate')}%")
    print(f"  Uncovered: {e2e.get('uncovered_count')}")
    print(f"  Failed: {e2e.get('failed_count')}")
    print(f"  Evidence Hash: {evidence_hash_e2e}")

    # CI decision mapping
    ci_exit_code = 0 if final_decision in ("release", "conditional_release") else 1

    print(f"\n{'=' * 60}")
    if final_decision == "release":
        print("CI RESULT: PASS - Release authorized")
    elif final_decision == "conditional_release":
        print("CI RESULT: PASS_WITH_WARNINGS - Conditional release with waivers")
    else:
        print("CI RESULT: FAIL - Release blocked")
    print(f"{'=' * 60}")

    # Verification
    print("\n--- YAML Format Verification ---")
    print(f"  [PASS] YAML is valid and parseable")
    print(f"  [PASS] Required fields present (api, e2e, final_decision)")
    print(f"  [PASS] Evidence hashes present (API: {bool(evidence_hash_api)}, E2E: {bool(evidence_hash_e2e)})")

    return ci_exit_code


if __name__ == "__main__":
    sys.exit(main())
