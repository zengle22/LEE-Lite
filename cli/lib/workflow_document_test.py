"""Shared helpers for ADR-033 document-test reports."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


TOP_LEVEL_FIELDS = (
    "workflow_key",
    "run_id",
    "tested_at",
    "test_outcome",
    "defect_counts",
    "recommended_next_action",
    "recommended_actor",
    "sections",
)

SECTION_FIELDS = (
    "structural",
    "logic_consistency",
    "downstream_readiness",
    "semantic_drift",
    "fixability",
)

TEST_OUTCOMES = {
    "no_blocking_defect_found",
    "blocking_defect_found",
    "inconclusive",
    "not_applicable",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _defect_label(defect: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = _text(defect.get(key))
        if value:
            return value
    return "unknown"


def build_fixability_section(
    *,
    recommended_next_action: str,
    recommended_actor: str,
    mechanical_fixable: int = 0,
    local_semantic_fixable: int = 0,
    rebuild_required: int = 0,
    human_judgement_required: int = 0,
) -> dict[str, Any]:
    return {
        "mechanical_fixable": mechanical_fixable,
        "local_semantic_fixable": local_semantic_fixable,
        "rebuild_required": rebuild_required,
        "human_judgement_required": human_judgement_required,
        "recommended_next_action": recommended_next_action,
        "recommended_actor": recommended_actor,
    }


def build_defect_counts(defect_list: list[dict[str, Any]]) -> dict[str, Any]:
    by_severity = Counter(_defect_label(defect, "severity", "type", "title") for defect in defect_list)
    by_type = Counter(_defect_label(defect, "type", "title", "severity") for defect in defect_list)
    return {
        "total": len(defect_list),
        "by_severity": dict(by_severity),
        "by_type": dict(by_type),
    }


def infer_test_outcome(
    *,
    structural: Mapping[str, Any],
    logic_consistency: Mapping[str, Any],
    downstream_readiness: Mapping[str, Any],
    semantic_drift: Mapping[str, Any],
    fixability: Mapping[str, Any],
) -> str:
    if any(
        [
            bool(structural.get("blocking")),
            bool(logic_consistency.get("blocking")),
            bool(downstream_readiness.get("blocking_gaps")),
            bool(semantic_drift.get("drift_detected")),
            int(fixability.get("rebuild_required") or 0) > 0,
            int(fixability.get("human_judgement_required") or 0) > 0,
        ]
    ):
        return "blocking_defect_found"
    return "no_blocking_defect_found"


def build_document_test_report(
    *,
    workflow_key: str,
    run_id: str,
    tested_at: str,
    defect_list: list[dict[str, Any]],
    structural: Mapping[str, Any],
    logic_consistency: Mapping[str, Any],
    downstream_readiness: Mapping[str, Any],
    semantic_drift: Mapping[str, Any],
    fixability: Mapping[str, Any],
    revision_request_ref: str = "",
) -> dict[str, Any]:
    report = {
        "workflow_key": workflow_key,
        "run_id": run_id,
        "tested_at": tested_at,
        "test_outcome": infer_test_outcome(
            structural=structural,
            logic_consistency=logic_consistency,
            downstream_readiness=downstream_readiness,
            semantic_drift=semantic_drift,
            fixability=fixability,
        ),
        "defect_counts": build_defect_counts(defect_list),
        "recommended_next_action": _text(fixability.get("recommended_next_action")),
        "recommended_actor": _text(fixability.get("recommended_actor")),
        "sections": {
            "structural": dict(structural),
            "logic_consistency": dict(logic_consistency),
            "downstream_readiness": dict(downstream_readiness),
            "semantic_drift": dict(semantic_drift),
            "fixability": dict(fixability),
        },
    }
    if revision_request_ref:
        report["revision_request_ref"] = revision_request_ref
    return report


def validate_document_test_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in TOP_LEVEL_FIELDS:
        if field not in report:
            errors.append(f"document-test-report.json missing top-level field: {field}")

    test_outcome = _text(report.get("test_outcome"))
    if test_outcome and test_outcome not in TEST_OUTCOMES:
        errors.append(f"document-test-report.json has invalid test_outcome: {test_outcome}")

    sections = report.get("sections")
    if not isinstance(sections, Mapping):
        return errors + ["document-test-report.json sections must be an object."]

    for field in SECTION_FIELDS:
        if field not in sections:
            errors.append(f"document-test-report.json missing section: {field}")

    structural = sections.get("structural")
    if isinstance(structural, Mapping):
        for field in ("package_integrity", "traceability_integrity", "blocking"):
            if field not in structural:
                errors.append(f"document-test-report.json structural missing field: {field}")

    logic = sections.get("logic_consistency")
    if isinstance(logic, Mapping):
        for field in ("checked_topics", "conflicts_found", "severity", "blocking"):
            if field not in logic:
                errors.append(f"document-test-report.json logic_consistency missing field: {field}")

    downstream = sections.get("downstream_readiness")
    if isinstance(downstream, Mapping):
        for field in ("downstream_target", "consumption_contract_ref", "ready_for_gate_review", "blocking_gaps", "missing_contracts", "assumption_leaks"):
            if field not in downstream:
                errors.append(f"document-test-report.json downstream_readiness missing field: {field}")

    drift = sections.get("semantic_drift")
    if isinstance(drift, Mapping):
        for field in ("revision_context_present", "drift_detected", "drift_items", "semantic_lock_preserved"):
            if field not in drift:
                errors.append(f"document-test-report.json semantic_drift missing field: {field}")

    fixability = sections.get("fixability")
    if isinstance(fixability, Mapping):
        for field in (
            "mechanical_fixable",
            "local_semantic_fixable",
            "rebuild_required",
            "human_judgement_required",
            "recommended_next_action",
            "recommended_actor",
        ):
            if field not in fixability:
                errors.append(f"document-test-report.json fixability missing field: {field}")
    return errors
