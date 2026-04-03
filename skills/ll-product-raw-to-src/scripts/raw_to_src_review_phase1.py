#!/usr/bin/env python3
"""
ADR-039 phase-1 review helpers for raw-to-src.
"""

from __future__ import annotations

from typing import Any

from cli.lib.product_review_phase1 import (
    count_review_phase1_defect_blockers,
    default_phase1_coverage,
    review_phase1_contract_metadata,
    validate_review_phase1_fields,
    PHASE1_REQUIRED_CHECKS,
)
from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section
from raw_to_src_common import WORKFLOW_KEY


def _count_blockers(structural_issues: list[dict[str, Any]], defects: list[dict[str, Any]]) -> int:
    return len(structural_issues) + count_review_phase1_defect_blockers(defects)


def build_raw_to_src_document_test_report(
    *,
    run_id: str,
    candidate: dict[str, Any],
    structural_report: dict[str, Any],
    defects: list[dict[str, Any]],
    acceptance_report: dict[str, Any],
    action: str,
    revision_request_ref: str,
) -> dict[str, Any]:
    structural_issues = list(structural_report.get("issues", []))
    defect_labels = [str(item.get("type") or item.get("title") or "unknown") for item in defects]
    structural_labels = [str(item.get("type") or item.get("code") or "structural_issue") for item in structural_issues]
    ready_for_gate_review = action == "next_skill"
    revision_context = candidate.get("revision_context") if isinstance(candidate.get("revision_context"), dict) else {}

    recommended_actor = {
        "next_skill": "external_gate_review",
        "retry": "executor_local_patch",
        "human_handoff": "supervisor_handoff",
        "blocked": "human_owner_decision",
    }.get(action, "external_gate_review")
    if action == "retry":
        fixability = build_fixability_section(
            recommended_next_action=action,
            recommended_actor=recommended_actor,
            mechanical_fixable=len(structural_labels),
            local_semantic_fixable=len(defect_labels),
        )
    elif action == "human_handoff":
        fixability = build_fixability_section(
            recommended_next_action=action,
            recommended_actor=recommended_actor,
            human_judgement_required=max(1, len(defect_labels)),
        )
    elif action == "blocked":
        fixability = build_fixability_section(
            recommended_next_action=action,
            recommended_actor=recommended_actor,
            human_judgement_required=max(1, len(defect_labels) + len(structural_labels)),
        )
    else:
        fixability = build_fixability_section(
            recommended_next_action="submit_to_external_gate",
            recommended_actor=recommended_actor,
        )

    report = build_document_test_report(
        workflow_key=WORKFLOW_KEY,
        run_id=run_id,
        tested_at=str(acceptance_report.get("created_at") or ""),
        defect_list=structural_issues + defects,
        revision_request_ref=revision_request_ref,
        structural={
            "package_integrity": bool(structural_report.get("input_valid")) and bool(structural_report.get("intake_valid")),
            "traceability_integrity": bool(candidate.get("source_refs")) and bool(candidate.get("source_provenance_map")),
            "blocking": bool(structural_issues),
        },
        logic_consistency={
            "checked_topics": ["problem_statement", "key_constraints", "scope_boundary", "acceptance_alignment"],
            "conflicts_found": defect_labels,
            "severity": "blocking" if defect_labels else "none",
            "blocking": bool(defect_labels),
        },
        downstream_readiness={
            "downstream_target": "product.src-to-epic",
            "consumption_contract_ref": "skills/ll-product-raw-to-src/ll.contract.yaml#validation.document_test.downstream_consumption_contract",
            "ready_for_gate_review": ready_for_gate_review,
            "blocking_gaps": structural_labels + defect_labels,
            "missing_contracts": [],
            "assumption_leaks": list(acceptance_report.get("acceptance_findings", [])),
        },
        semantic_drift={
            "revision_context_present": bool(revision_request_ref or revision_context),
            "drift_detected": False,
            "drift_items": [],
            "semantic_lock_preserved": True,
        },
        fixability=fixability,
    )
    report["coverage"] = default_phase1_coverage()
    report["required_checks"] = list(PHASE1_REQUIRED_CHECKS)
    report["blocker_count"] = _count_blockers(structural_issues, defects)
    report["review_phase1"] = review_phase1_contract_metadata()
    return report
