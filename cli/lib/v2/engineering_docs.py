"""Step_2 — Engineering documents check.

Truth source: design.md §impl-verify step_2.
"""

from __future__ import annotations

from typing import Any


def check_engineering_docs(gsd_delivery: dict[str, Any]) -> dict[str, Any]:
    """Check engineering artifact completeness and quality.

    Returns dict with engineering_docs, missing_docs, doc_quality_warnings.
    """
    docs = gsd_delivery.get("engineering_artifacts", {})
    missing: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required = {
        "change_description": (50, "change_description_too_brief"),
        "rollback_plan": (0, "rollback_plan_missing"),
    }
    recommended = {
        "key_decisions": (20, "decision_missing_rationale"),
        "dependency_changes": (0, "dependency_changes_missing"),
        "known_issues": (0, "known_issues_missing"),
    }

    for key, (min_len, warning_key) in required.items():
        value = docs.get(key, "")
        if not value or (min_len > 0 and len(value) < min_len):
            missing.append({"doc_type": key, "severity": "high"})

    for key, (min_len, warning_key) in recommended.items():
        value = docs.get(key, "")
        if not value:
            missing.append({"doc_type": key, "severity": "medium"})
        elif min_len > 0 and len(value) < min_len:
            warnings.append({"type": warning_key, "doc": key})

    # Quality checks
    change_desc = docs.get("change_description", "")
    if change_desc and len(change_desc) < 50:
        warnings.append({"type": "change_description_too_brief", "doc": "change_description"})

    if missing:
        severity = max((m["severity"] for m in missing), key=lambda s: {"high": 2, "medium": 1, "low": 0}.get(s, 0))
        engineering_docs = "fail" if severity == "high" else "partial"
    else:
        engineering_docs = "pass"

    return {
        "engineering_docs": engineering_docs,
        "missing_docs": missing,
        "doc_quality_warnings": warnings,
    }
