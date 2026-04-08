#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section, validate_document_test_report


def build_document_test(
    *,
    run_id: str,
    tested_at: str,
    bundle: dict[str, Any],
    defects: list[dict[str, Any]],
    revision_context: dict[str, Any] | None,
) -> dict[str, Any]:
    blocking = [item for item in defects if str(item.get("check") or "").strip()]
    blocking_names = [str(item.get("check") or "").strip() for item in blocking]
    if bundle.get("completeness_result") == "fail" and not blocking_names:
        blocking_names = [str(item).strip() for item in (bundle.get("open_questions") or []) if str(item).strip()]
    outcome_ready = bundle.get("completeness_result") != "fail"
    blocking_detected = bool(blocking_names)
    defect_list = [{"severity": "P1", "type": item.get("check"), "title": item.get("check")} for item in blocking]
    if not defect_list and blocking_names:
        defect_list = [{"severity": "P1", "type": "open_question_blocker", "title": name} for name in blocking_names]
    return build_document_test_report(
        workflow_key="dev.feat-to-ui",
        run_id=run_id,
        tested_at=tested_at,
        defect_list=defect_list,
        revision_request_ref=str((revision_context or {}).get("revision_request_ref") or ""),
        structural={"package_integrity": True, "traceability_integrity": bool(bundle.get("source_refs")), "blocking": False},
        logic_consistency={
            "checked_topics": ["user_paths", "state_model", "field_boundary", "feedback_rules", "ui_tech_boundary"],
            "conflicts_found": blocking_names,
            "severity": "blocking" if blocking else "none",
            "blocking": bool(blocking),
        },
        downstream_readiness={
            "downstream_target": "downstream_ui_implementation_consumer",
            "consumption_contract_ref": "skills/ll-dev-feat-to-ui/ll.contract.yaml#validation.document_test.downstream_consumption_contract",
            "ready_for_gate_review": outcome_ready,
            "blocking_gaps": blocking_names,
            "missing_contracts": [],
            "assumption_leaks": list(bundle.get("open_questions") or []),
        },
        semantic_drift={
            "revision_context_present": bool(revision_context),
            "drift_detected": False,
            "drift_items": [],
            "semantic_lock_preserved": True,
        },
        fixability=build_fixability_section(
            recommended_next_action="workflow_rebuild" if blocking_detected else "external_gate_review",
            recommended_actor="workflow_rebuild" if blocking_detected else "external_gate_review",
            rebuild_required=len(blocking_names),
        ),
    )


def validate_document_test(path_payload: dict[str, Any]) -> list[str]:
    return validate_document_test_report(path_payload)
