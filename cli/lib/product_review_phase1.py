#!/usr/bin/env python3
"""
Shared ADR-039 phase-1 review contract helpers for product workflows.
"""

from __future__ import annotations

from typing import Any, Mapping


PHASE1_ARTIFACT_FAMILY = "src_or_feat"
PHASE1_RISK_PROFILES = ("default",)
PHASE1_COVERAGE_DIMENSIONS = (
    "ssot_alignment",
    "object_completeness",
    "contract_completeness",
    "state_transition_closure",
    "failure_path",
    "testability",
)
PHASE1_REQUIRED_CHECKS = PHASE1_COVERAGE_DIMENSIONS
PHASE1_GATE_BLOCK_CONDITIONS = (
    "missing_coverage",
    "required_check_not_checked",
    "blocker_count_gt_zero",
)
BLOCKER_SEVERITIES = {"P0", "P1"}


def review_phase1_contract_metadata() -> dict[str, Any]:
    return {
        "artifact_family": PHASE1_ARTIFACT_FAMILY,
        "risk_profiles": list(PHASE1_RISK_PROFILES),
        "coverage_dimensions": list(PHASE1_COVERAGE_DIMENSIONS),
        "required_checks": list(PHASE1_REQUIRED_CHECKS),
        "gate_block_conditions": list(PHASE1_GATE_BLOCK_CONDITIONS),
    }


def default_phase1_coverage() -> dict[str, str]:
    return {
        "ssot_alignment": "checked",
        "object_completeness": "checked",
        "contract_completeness": "checked",
        "state_transition_closure": "partial",
        "failure_path": "partial",
        "testability": "partial",
    }


def count_review_phase1_defect_blockers(defects: list[dict[str, Any]]) -> int:
    return sum(1 for item in defects if str(item.get("severity") or "").strip().upper() in BLOCKER_SEVERITIES)


def validate_review_phase1_fields(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    coverage = report.get("coverage")
    if not isinstance(coverage, Mapping):
        return ["document-test-report.json missing review phase-1 coverage object."]

    coverage_keys = set(str(key) for key in coverage.keys())
    expected_keys = set(PHASE1_COVERAGE_DIMENSIONS)
    missing_keys = [key for key in PHASE1_COVERAGE_DIMENSIONS if key not in coverage_keys]
    unknown_keys = sorted(coverage_keys - expected_keys)
    errors.extend(f"document-test-report.json coverage missing required dimension: {key}" for key in missing_keys)
    errors.extend(f"document-test-report.json coverage contains unsupported dimension: {key}" for key in unknown_keys)

    required_checks = report.get("required_checks")
    if not isinstance(required_checks, list):
        errors.append("document-test-report.json missing required_checks list.")
    else:
        missing_required = [key for key in PHASE1_REQUIRED_CHECKS if key not in required_checks]
        errors.extend(f"document-test-report.json required_checks missing phase-1 dimension: {key}" for key in missing_required)
        for key in PHASE1_REQUIRED_CHECKS:
            if str(coverage.get(key) or "").strip() == "not_checked":
                errors.append(f"document-test-report.json coverage marks required dimension as not_checked: {key}")

    blocker_count = report.get("blocker_count")
    if not isinstance(blocker_count, int):
        errors.append("document-test-report.json blocker_count must be an integer.")
    elif blocker_count < 0:
        errors.append("document-test-report.json blocker_count must be >= 0.")
    elif blocker_count > 0:
        errors.append(f"document-test-report.json blocker_count must be 0 for freeze-ready handoff; got {blocker_count}.")
    return errors
