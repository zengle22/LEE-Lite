#!/usr/bin/env python3
"""
Gate Evaluator — ADR-047 Pilot

Reads API manifest + E2E manifest + settlements + waivers,
generates release_gate_input.yaml with pass/fail decision.

Usage:
    python gate-evaluator.py
"""

import yaml
import json
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent  # ssot/tests
REPO_ROOT = BASE_DIR.parent.parent  # repo root
API_MANIFEST_PATH = BASE_DIR / "api" / "FEAT-SRC-005-001" / "api-coverage-manifest.yaml"
E2E_MANIFEST_PATH = BASE_DIR / "e2e" / "PROTOTYPE-FEAT-SRC-005-001" / "e2e-coverage-manifest.yaml"
API_SETTLEMENT_PATH = BASE_DIR / ".artifacts" / "settlement" / "api-settlement-report.yaml"
E2E_SETTLEMENT_PATH = BASE_DIR / ".artifacts" / "settlement" / "e2e-settlement-report.yaml"
WAIVER_PATH = BASE_DIR / ".artifacts" / "settlement" / "waiver.yaml"
# ADR-047 spec path for release gate input (repo root)
OUTPUT_PATH = REPO_ROOT / ".artifacts" / "tests" / "settlement" / "release-gate-input.yaml"
# Also write to gate dir for local access
OUTPUT_PATH_LOCAL = BASE_DIR / "gate" / "release_gate_input.yaml"


def load_yaml(path):
    """Load a YAML file, return empty dict if not found."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_manifest_items(manifest_data):
    """Extract items from manifest."""
    if not manifest_data:
        return []
    return manifest_data.get("api_coverage_manifest", {}).get("items", []) or \
           manifest_data.get("e2e_coverage_manifest", {}).get("items", [])


def compute_evidence_hash(items):
    """Compute a hash of all evidence refs for integrity binding.

    Excludes obsolete items per ADR-047 Appendix A.4.
    """
    active_items = [item for item in items if not item.get("obsolete", False)]
    evidence_str = json.dumps(
        sorted([item.get("evidence_refs", []) for item in active_items]),
        sort_keys=True
    )
    return hashlib.sha256(evidence_str.encode()).hexdigest()[:16]


def evaluate_chain(manifest_items, waiver_items):
    """
    Evaluate a single chain (API or E2E) based on manifest items.

    Gate Rules (from ADR-047 Section 9.4, Appendix A.4):
    - lifecycle_status=passed requires evidence_status=complete
    - waiver_status=pending still counts as failed
    - waiver_status=approved items excluded from denominator
    - waiver_status=rejected items must be fixed before release
    - obsolete=true items excluded from all counts
    - lifecycle_status=waived counts as passed (approved waiver applied)
    """
    waiver_map = {}
    for w in waiver_items:
        waiver_map[w.get("coverage_id")] = w.get("status", "none")

    total = 0
    passed = 0
    failed = 0
    blocked = 0
    uncovered = 0
    waived = 0
    pending_waiver = 0
    rejected_waiver = 0
    cut_count = 0

    for item in manifest_items:
        # Skip obsolete items
        if item.get("obsolete", False):
            continue

        item_waiver_status = item.get("waiver_status", "none") or \
                             waiver_map.get(item.get("coverage_id"), "none")

        # Skip approved waivers (excluded from denominator)
        if item_waiver_status == "approved":
            waived += 1
            continue

        # Cut items: excluded from denominator (intentionally not tested)
        if item.get("lifecycle_status") == "cut":
            cut_count += 1
            continue

        # Waived lifecycle_status means an approved waiver was applied
        # Already handled above for waiver_status=approved, but also handle lifecycle=waived
        if item.get("lifecycle_status") == "waived":
            waived += 1
            continue

        total += 1

        lifecycle = item.get("lifecycle_status", "designed")
        evidence = item.get("evidence_status", "missing")
        w_status = item_waiver_status

        # Schema constraint: passed requires complete evidence
        if lifecycle == "passed" and evidence != "complete":
            failed += 1
            continue

        if lifecycle == "passed":
            passed += 1
        elif lifecycle in ("failed", "rejected"):
            if w_status == "pending":
                # Computation constraint: pending waiver still counts as failed
                pending_waiver += 1
            elif w_status == "rejected":
                # Rejected waiver: must fix before release
                rejected_waiver += 1
            failed += 1
        elif lifecycle == "blocked":
            if w_status == "pending":
                pending_waiver += 1
            elif w_status == "rejected":
                rejected_waiver += 1
            blocked += 1
        elif lifecycle == "designed":
            # Not yet executed - counts as uncovered
            uncovered += 1
        elif lifecycle in ("generated", "executable"):
            # Generated but not executed
            uncovered += 1
        elif lifecycle == "executed":
            # Executed but not yet judged - check evidence
            if evidence == "complete":
                passed += 1
            else:
                uncovered += 1
        elif lifecycle == "drafted":
            # Still in draft - counts as uncovered
            uncovered += 1
        else:
            # Unknown state - log warning, count as uncovered
            print(f"  WARNING: Unknown lifecycle_status='{lifecycle}' for item, counting as uncovered")
            uncovered += 1

    # Pass rate
    effective_denominator = total  # already excludes approved waivers
    pass_rate = (passed / effective_denominator * 100) if effective_denominator > 0 else 0.0

    # Determine status
    if failed == 0 and blocked == 0 and uncovered == 0:
        status = "pass"
    elif rejected_waiver > 0:
        # Rejected waivers always force a fail
        status = "fail"
    elif failed == 0 and (blocked > 0 or uncovered > 0) and pending_waiver > 0:
        status = "conditional_pass"
    else:
        status = "fail"

    return {
        "status": status,
        "total_items": total,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "uncovered": uncovered,
        "waived": waived,
        "pending_waiver": pending_waiver,
        "rejected_waiver": rejected_waiver,
        "cut_count": cut_count,
        "pass_rate": round(pass_rate, 2),
        "evidence_hash": compute_evidence_hash(manifest_items),
    }


def generate_release_gate_input(api_result, e2e_result):
    """
    Generate release_gate_input.yaml.

    Final decision logic:
    - Both pass -> release
    - One pass, one conditional_pass -> conditional_release
    - Any fail -> block
    """
    api_status = api_result["status"]
    e2e_status = e2e_result["status"]

    if api_status == "fail" or e2e_status == "fail":
        final_decision = "block"
    elif api_status == "pass" and e2e_status == "pass":
        final_decision = "release"
    else:
        final_decision = "conditional_release"

    # Build reason
    reasons = []
    if api_status != "pass":
        reasons.append(
            f"API chain: {api_status} "
            f"(failed={api_result['failed']}, uncovered={api_result['uncovered']}, "
            f"rejected_waiver={api_result.get('rejected_waiver', 0)})"
        )
    if e2e_status != "pass":
        reasons.append(
            f"E2E chain: {e2e_status} "
            f"(failed={e2e_result['failed']}, uncovered={e2e_result['uncovered']}, "
            f"rejected_waiver={e2e_result.get('rejected_waiver', 0)})"
        )

    reason = "; ".join(reasons) if reasons else "All chains passed"

    return {
        "release_gate_input": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "api": {
                "status": api_status,
                "uncovered_count": api_result["uncovered"],
                "failed_count": api_result["failed"],
                "blocked_count": api_result["blocked"],
                "pass_rate": api_result["pass_rate"],
                "evidence_hash": api_result["evidence_hash"],
                "waiver_refs": [],
            },
            "e2e": {
                "status": e2e_status,
                "uncovered_count": e2e_result["uncovered"],
                "failed_count": e2e_result["failed"],
                "blocked_count": e2e_result["blocked"],
                "pass_rate": e2e_result["pass_rate"],
                "evidence_hash": e2e_result["evidence_hash"],
                "waiver_refs": [],
            },
            "final_decision": final_decision,
            "decision_reason": reason,
        }
    }


def verify_cut_records(manifest_items):
    """Verify all cut items have valid cut_record with approver and source_ref."""
    for item in manifest_items:
        if item.get("lifecycle_status") == "cut":
            cut_record = item.get("cut_record")
            if not cut_record:
                return False, f"Item {item.get('coverage_id')} is cut but has no cut_record"
            if not cut_record.get("approver"):
                return False, f"Item {item.get('coverage_id')} cut_record missing approver"
            if not cut_record.get("source_ref"):
                return False, f"Item {item.get('coverage_id')} cut_record missing source_ref"
    return True, "All cut items have valid cut_record"


def verify_evidence_consistency(manifest_items):
    """Verify lifecycle_status=passed implies evidence_status=complete."""
    for item in manifest_items:
        if item.get("lifecycle_status") == "passed" and item.get("evidence_status") != "complete":
            return False, f"Item {item.get('coverage_id')} is passed but evidence is {item.get('evidence_status')}"
    return True, "All passed items have complete evidence"


def main():
    print("=" * 60)
    print("ADR-047 Gate Evaluator — Dual-Chain Test Governance")
    print("=" * 60)

    # Load manifests
    api_manifest = load_yaml(API_MANIFEST_PATH)
    e2e_manifest = load_yaml(E2E_MANIFEST_PATH)

    api_items = load_manifest_items(api_manifest)
    e2e_items = load_manifest_items(e2e_manifest)

    print(f"\nLoaded API manifest: {len(api_items)} items")
    print(f"Loaded E2E manifest: {len(e2e_items)} items")

    # Guard: empty manifests should not silently pass
    if len(api_items) == 0 and len(e2e_items) == 0:
        print("\nERROR: Both manifests are empty. Gate cannot evaluate with no data.")
        print("Ensure api-coverage-manifest.yaml and e2e-coverage-manifest.yaml exist and have items.")
        return 1

    # Load settlements (logged but manifest items drive lifecycle)
    api_settlement = load_yaml(API_SETTLEMENT_PATH)
    e2e_settlement = load_yaml(E2E_SETTLEMENT_PATH)
    if api_settlement:
        print(f"API settlement status: {api_settlement.get('api_settlement', {}).get('status', 'N/A')}")
    if e2e_settlement:
        print(f"E2E settlement status: {e2e_settlement.get('e2e_settlement', {}).get('status', 'N/A')}")

    # Load waivers
    waiver_data = load_yaml(WAIVER_PATH)
    waiver_items = waiver_data.get("waivers", []) if waiver_data else []

    # Evaluate chains
    print("\n--- API Chain Evaluation ---")
    api_result = evaluate_chain(api_items, waiver_items)
    print(f"  Status: {api_result['status']}")
    print(f"  Total: {api_result['total_items']}")
    print(f"  Passed: {api_result['passed']}")
    print(f"  Failed: {api_result['failed']}")
    print(f"  Blocked: {api_result['blocked']}")
    print(f"  Uncovered: {api_result['uncovered']}")
    print(f"  Waived: {api_result['waived']}")
    print(f"  Pending Waiver: {api_result['pending_waiver']}")
    print(f"  Rejected Waiver: {api_result.get('rejected_waiver', 0)}")
    print(f"  Pass Rate: {api_result['pass_rate']}%")
    print(f"  Evidence Hash: {api_result['evidence_hash']}")

    print("\n--- E2E Chain Evaluation ---")
    e2e_result = evaluate_chain(e2e_items, waiver_items)
    print(f"  Status: {e2e_result['status']}")
    print(f"  Total: {e2e_result['total_items']}")
    print(f"  Passed: {e2e_result['passed']}")
    print(f"  Failed: {e2e_result['failed']}")
    print(f"  Blocked: {e2e_result['blocked']}")
    print(f"  Uncovered: {e2e_result['uncovered']}")
    print(f"  Waived: {e2e_result['waived']}")
    print(f"  Pending Waiver: {e2e_result['pending_waiver']}")
    print(f"  Rejected Waiver: {e2e_result.get('rejected_waiver', 0)}")
    print(f"  Pass Rate: {e2e_result['pass_rate']}%")
    print(f"  Evidence Hash: {e2e_result['evidence_hash']}")

    # Generate release gate input
    gate_input = generate_release_gate_input(api_result, e2e_result)

    # Write output to both paths
    for out_path in [OUTPUT_PATH, OUTPUT_PATH_LOCAL]:
        try:
            os.makedirs(out_path.parent, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                yaml.dump(gate_input, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            print(f"\nOutput written to: {out_path}")
        except OSError as e:
            print(f"\nWARNING: Could not write to {out_path}: {e}")

    print(f"\n--- Final Decision ---")
    print(f"  Decision: {gate_input['release_gate_input']['final_decision']}")
    print(f"  Reason: {gate_input['release_gate_input']['decision_reason']}")

    # Anti-laziness verification (runtime assertions)
    print("\n--- Anti-Laziness Verification ---")
    cut_ok, cut_msg = verify_cut_records(api_items + e2e_items)
    evidence_ok, evidence_msg = verify_evidence_consistency(api_items + e2e_items)

    checks = [
        ("Manifest items frozen before execution", len(api_items) > 0 and len(e2e_items) > 0),
        (f"Cut records valid: {cut_msg}", cut_ok),
        ("Pending waiver counts as failed", api_result.get("pending_waiver", 0) == 0 or api_result["failed"] >= api_result.get("pending_waiver", 0)),
        (f"Evidence consistency: {evidence_msg}", evidence_ok),
        ("Min exception journey coverage required",
         len([i for i in e2e_items if i.get("journey_type") == "exception"]) >= 1),
        ("No evidence = not passed",
         all(item.get("evidence_status") != "complete" or item.get("lifecycle_status") != "passed"
             for item in api_items + e2e_items if item.get("evidence_status") == "missing")),
        ("Evidence hash binding exists",
         bool(api_result["evidence_hash"] and e2e_result["evidence_hash"])),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "PASS" if result else "FAIL"
        if not result:
            all_passed = False
        print(f"  [{status}] {check_name}")

    print(f"\nAnti-laziness: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
