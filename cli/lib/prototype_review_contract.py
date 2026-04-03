"""Structured prototype review contract helpers."""

from __future__ import annotations

from typing import Any


REQUIRED_CHECKS = [
    "journey_check",
    "cta_hierarchy_check",
    "flow_consistency_check",
    "state_experience_check",
    "feat_alignment_check",
]


def build_prototype_review(
    *,
    verdict: str,
    review_contract_ref: str,
    reviewer_identity: str,
    reviewed_at: str,
    checks: dict[str, dict[str, Any]],
    blocking_points: list[dict[str, Any]] | None = None,
    human_adjustments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    completed = [name for name in REQUIRED_CHECKS if name in checks]
    not_checked = [name for name in REQUIRED_CHECKS if name not in checks]
    payload: dict[str, Any] = {
        "verdict": verdict,
        "review_contract_ref": review_contract_ref,
        "coverage_declaration": {
            "required_checks": REQUIRED_CHECKS,
            "completed_checks": completed,
            "not_checked": not_checked,
        },
        "blocking_points": blocking_points or [],
        "human_adjustments": human_adjustments or [],
        "reviewer_identity": reviewer_identity,
        "reviewed_at": reviewed_at,
    }
    payload.update(checks)
    return payload


def validate_prototype_review(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("verdict") not in {"approved", "revise", "rejected"}:
        errors.append("prototype review verdict must be approved, revise, or rejected")
    if not str(review.get("review_contract_ref") or "").strip():
        errors.append("prototype review must include review_contract_ref")
    coverage = review.get("coverage_declaration")
    if not isinstance(coverage, dict):
        errors.append("prototype review must include coverage_declaration")
        return errors
    if coverage.get("not_checked"):
        errors.append("prototype review coverage_declaration.not_checked must be empty")
    for key in REQUIRED_CHECKS:
        section = review.get(key)
        if not isinstance(section, dict):
            errors.append(f"prototype review missing structured check: {key}")
            continue
        if "passed" not in section:
            errors.append(f"prototype review check missing passed flag: {key}")
        if "issues" not in section:
            errors.append(f"prototype review check missing issues list: {key}")
    return errors
