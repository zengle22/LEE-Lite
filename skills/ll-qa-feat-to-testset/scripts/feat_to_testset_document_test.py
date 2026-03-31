#!/usr/bin/env python3
"""ADR-033 document-test helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section


def build_document_test(
    *,
    run_id: str,
    tested_at: str,
    bundle_json: dict[str, Any],
    semantic_drift_check: dict[str, Any],
    defects: list[dict[str, Any]],
    downstream_target: str,
    required_environment_inputs: dict[str, Any] | None,
    revision_context: dict[str, Any] | None,
    ready_for_gate_review: bool,
) -> dict[str, Any]:
    titles = [str(item.get("title") or item.get("check") or "").strip() for item in defects if str(item.get("title") or item.get("check") or "").strip()]
    missing_contracts = [
        category for category, values in (required_environment_inputs or {}).items() if not [str(item).strip() for item in (values or []) if str(item).strip()]
    ]
    fixability = build_fixability_section(
        recommended_next_action="workflow_rebuild" if defects else "submit_to_external_gate",
        recommended_actor="workflow_rebuild" if defects else "external_gate_review",
        rebuild_required=len(defects),
    )
    return build_document_test_report(
        workflow_key="qa.feat-to-testset",
        run_id=run_id,
        tested_at=tested_at,
        defect_list=defects,
        revision_request_ref=str((revision_context or {}).get("revision_request_ref") or ""),
        structural={"package_integrity": True, "traceability_integrity": bool(bundle_json.get("source_refs")), "blocking": False},
        logic_consistency={"checked_topics": ["analysis", "strategy", "traceability", "handoff"], "conflicts_found": titles, "severity": "blocking" if defects else "none", "blocking": bool(defects)},
        downstream_readiness={
            "downstream_target": downstream_target,
            "consumption_contract_ref": "skills/ll-qa-feat-to-testset/ll.contract.yaml#validation.document_test.downstream_consumption_contract",
            "ready_for_gate_review": ready_for_gate_review,
            "blocking_gaps": titles,
            "missing_contracts": missing_contracts,
            "assumption_leaks": [],
        },
        semantic_drift={
            "revision_context_present": bool(revision_context),
            "drift_detected": semantic_drift_check.get("verdict") == "reject",
            "drift_items": list(semantic_drift_check.get("forbidden_axis_detected") or []),
            "semantic_lock_preserved": semantic_drift_check.get("semantic_lock_preserved", True),
        },
        fixability=fixability,
    )
