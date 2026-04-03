#!/usr/bin/env python3
"""
ADR-039 phase-1 review helpers for epic-to-feat.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.product_review_phase1 import (
    count_review_phase1_defect_blockers,
    default_phase1_coverage,
    review_phase1_contract_metadata,
    validate_review_phase1_fields,
    PHASE1_REQUIRED_CHECKS,
)
from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section


WORKFLOW_KEY = "product.epic-to-feat"
def _count_blockers(defects: list[dict[str, Any]]) -> int:
    return count_review_phase1_defect_blockers(defects)


def build_epic_to_feat_document_test_report(generated: Any) -> dict[str, Any]:
    revision_context = generated.json_payload.get("revision_context") if isinstance(generated.json_payload.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or "").strip()
    defects = list(generated.defect_list)
    downstream_targets = [
        str(item.get("workflow") or "").strip()
        for item in generated.handoff.get("target_workflows", [])
        if isinstance(item, dict) and str(item.get("workflow") or "").strip()
    ]
    semantic_drift = generated.semantic_drift_check
    review_report = generated.review_report if isinstance(generated.review_report, dict) else {}

    report = build_document_test_report(
        workflow_key=WORKFLOW_KEY,
        run_id=str(generated.frontmatter["workflow_run_id"]),
        tested_at=str(generated.acceptance_report["created_at"]),
        defect_list=defects,
        revision_request_ref=revision_request_ref,
        structural={
            "package_integrity": True,
            "traceability_integrity": bool(generated.json_payload.get("source_refs")) and bool(generated.json_payload.get("traceability")),
            "blocking": False,
        },
        logic_consistency={
            "checked_topics": ["feat_boundary", "acceptance_inheritance", "dependency_boundary", "authoritative_artifact_mapping"],
            "conflicts_found": [str(item.get("title") or item.get("severity") or "unknown") for item in defects],
            "severity": "blocking" if defects else "none",
            "blocking": bool(defects),
        },
        downstream_readiness={
            "downstream_target": downstream_targets,
            "consumption_contract_ref": "skills/ll-product-epic-to-feat/ll.contract.yaml#validation.document_test.downstream_consumption_contract",
            "ready_for_gate_review": not defects,
            "blocking_gaps": [str(item.get("detail") or item.get("title") or "unknown") for item in defects],
            "missing_contracts": [],
            "assumption_leaks": list(review_report.get("risks") or []),
        },
        semantic_drift={
            "revision_context_present": bool(revision_context),
            "drift_detected": semantic_drift.get("verdict") == "reject",
            "drift_items": list(semantic_drift.get("forbidden_axis_detected") or []) or ([str(semantic_drift.get("summary") or "")] if semantic_drift.get("verdict") == "reject" else []),
            "semantic_lock_preserved": bool(semantic_drift.get("semantic_lock_preserved", True)),
        },
        fixability=build_fixability_section(
            recommended_next_action="rebuild_and_rerun" if defects else "submit_to_external_gate",
            recommended_actor="workflow_rebuild" if defects else "external_gate_review",
            rebuild_required=len(defects),
        ),
    )
    report["coverage"] = default_phase1_coverage()
    report["required_checks"] = list(PHASE1_REQUIRED_CHECKS)
    report["blocker_count"] = _count_blockers(defects)
    report["review_phase1"] = review_phase1_contract_metadata()
    return report
