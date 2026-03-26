#!/usr/bin/env python3
"""
Record builders for raw-to-src runtime artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from raw_to_src_common import WORKFLOW_KEY, iso_now


SKILL_ID = "ll-product-raw-to-src"
STRUCTURAL_BUDGET = 3
SEMANTIC_BUDGET = 2
TOTAL_BUDGET = 4


def stage(
    stage_id: str,
    status: str,
    details: str,
    role: str,
    input_refs: list[str] | None = None,
    output_refs: list[str] | None = None,
    issues_found: list[str] | None = None,
    patches_applied: list[str] | None = None,
    revalidation_status: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stage_id": stage_id,
        "status": status,
        "details": details,
        "role": role,
        "input_refs": input_refs or [],
        "output_refs": output_refs or [],
        "issues_found": issues_found or [],
        "patches_applied": patches_applied or [],
    }
    if revalidation_status is not None:
        payload["revalidation_status"] = revalidation_status
    return payload


def build_retry_budget_report(
    run_id: str,
    structural_attempts: list[dict[str, Any]],
    semantic_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    attempts = structural_attempts + semantic_attempts
    budget_stop_reason = "budget_available"
    if len(attempts) >= TOTAL_BUDGET:
        budget_stop_reason = "total_budget_exhausted"
    return {
        "run_id": run_id,
        "workflow_key": WORKFLOW_KEY,
        "structural_fix_budget": STRUCTURAL_BUDGET,
        "semantic_fix_budget": SEMANTIC_BUDGET,
        "total_repair_budget": TOTAL_BUDGET,
        "structural_attempts_used": len(structural_attempts),
        "semantic_attempts_used": len(semantic_attempts),
        "total_attempts_used": len(attempts),
        "attempts": attempts,
        "budget_stop_reason": budget_stop_reason,
    }


def build_handoff_proposal(
    run_id: str,
    action: str,
    target_skill: str,
    candidate_path: Path,
    artifacts_dir: Path,
) -> dict[str, Any] | None:
    if action == "blocked":
        return None
    expected_output = "epic" if action == "next_skill" else "raw_to_src_resolution"
    return {
        "handoff_id": f"handoff-{run_id}",
        "from_skill": SKILL_ID,
        "to_skill": target_skill,
        "source_run_id": run_id,
        "primary_artifact_ref": str(candidate_path),
        "supporting_artifact_refs": [
            str(artifacts_dir / "source-semantic-findings.json"),
            str(artifacts_dir / "acceptance-report.json"),
            str(artifacts_dir / "defect-list.json"),
            str(artifacts_dir / "result-summary.json"),
        ],
        "gate_result_ref": None,
        "evidence_bundle_refs": [
            str(artifacts_dir / "execution-evidence.json"),
            str(artifacts_dir / "supervision-evidence.json"),
            str(artifacts_dir / "retry-budget-report.json"),
            str(artifacts_dir / "patch-lineage.json"),
        ],
        "required_context": [
            "candidate markdown",
            "semantic findings",
            "retry budget report",
        ],
        "expected_output_type": expected_output,
        "created_at": iso_now(),
    }


def build_job_proposal(
    run_id: str,
    action: str,
    target_skill: str,
    queue_path: str,
    handoff_ref: str | None,
    candidate_path: Path,
    retry_budget: int = 0,
) -> dict[str, Any]:
    consumer_type = "human_loop" if action == "human_handoff" else "skill_loop"
    return {
        "job_id": f"job-{run_id}-{action}",
        "job_type": action,
        "from_skill": SKILL_ID,
        "target_skill": target_skill,
        "handoff_ref": handoff_ref,
        "source_run_id": run_id,
        "source_artifacts": [str(candidate_path)],
        "gate_decision_ref": None,
        "reason": f"raw-to-src recommended {action}",
        "priority": "normal",
        "status": "proposed",
        "created_at": iso_now(),
        "queue_path": queue_path,
        "consumer_type": consumer_type,
        "retry_count": 0,
        "retry_budget": retry_budget,
    }


def build_proposed_actions(run_id: str, status: str, action: str, target_skill: str, queue_path: str) -> dict[str, Any]:
    handoff_action = {
        "next_skill": "materialize_handoff",
        "retry": "materialize_retry_handoff",
        "human_handoff": "materialize_human_handoff",
        "blocked": "no_handoff",
    }[action]
    return {
        "workflow_key": WORKFLOW_KEY,
        "run_id": run_id,
        "current_result_state": status,
        "recommended_action": action,
        "recommended_target_skill": target_skill,
        "recommended_queue_path": queue_path,
        "recommended_handoff_action": handoff_action,
        "recommend_freeze": action == "next_skill",
        "reasons": [f"raw-to-src proposed {action}"],
    }


def build_result_summary(
    run_id: str,
    status: str,
    action: str,
    target_skill: str,
    queue_path: str,
    candidate_path: Path,
    artifacts_dir: Path,
    handoff_ref: str | None,
    stage_state: str,
    gate_ready_package_ref: str | None = None,
    authoritative_handoff_ref: str | None = None,
    gate_pending_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "workflow_key": WORKFLOW_KEY,
        "run_id": run_id,
        "status": status,
        "primary_artifact_ref": str(candidate_path),
        "artifacts_dir": str(artifacts_dir),
        "recommended_action": action,
        "recommended_target_skill": target_skill,
        "recommended_queue_path": queue_path,
        "recommended_handoff_ref": handoff_ref,
        "stage_state": stage_state,
        "freeze_readiness": "freeze_ready" if action == "next_skill" else "not_ready",
        "gate_ready_package_ref": gate_ready_package_ref or "",
        "authoritative_handoff_ref": authoritative_handoff_ref or "",
        "gate_pending_ref": gate_pending_ref or "",
    }


def build_run_state(run_id: str, current_state: str, action: str, stage_results: list[dict[str, Any]]) -> dict[str, Any]:
    state_history = [
        {
            "state": item["status"],
            "stage_id": item["stage_id"],
            "role": item["role"],
        }
        for item in stage_results
    ]
    return {
        "run_id": run_id,
        "workflow_key": WORKFLOW_KEY,
        "current_state": current_state,
        "recommended_action": action,
        "state_history": state_history,
    }


def build_patch_lineage(run_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "workflow_key": WORKFLOW_KEY,
        "events": events,
    }


def build_package_manifest(
    artifacts_dir: Path,
    candidate_path: Path,
    status: str,
    action: str,
    handoff_ref: str | None,
    gate_ready_package_ref: str | None = None,
    authoritative_handoff_ref: str | None = None,
    gate_pending_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "artifacts_dir": str(artifacts_dir),
        "primary_artifact_ref": str(candidate_path),
        "result_summary_ref": str(artifacts_dir / "result-summary.json"),
        "proposed_actions_ref": str(artifacts_dir / "proposed-next-actions.json"),
        "handoff_proposal_ref": handoff_ref,
        "job_proposal_ref": str(artifacts_dir / "job-proposal.json"),
        "run_state_ref": str(artifacts_dir / "run-state.json"),
        "patch_lineage_ref": str(artifacts_dir / "patch-lineage.json"),
        "source_semantic_findings_ref": str(artifacts_dir / "source-semantic-findings.json"),
        "acceptance_report_ref": str(artifacts_dir / "acceptance-report.json"),
        "execution_evidence_ref": str(artifacts_dir / "execution-evidence.json"),
        "supervision_evidence_ref": str(artifacts_dir / "supervision-evidence.json"),
        "recommended_action": action,
        "status": status,
        "gate_ready_package_ref": gate_ready_package_ref or "",
        "authoritative_handoff_ref": authoritative_handoff_ref or "",
        "gate_pending_ref": gate_pending_ref or "",
    }


def build_execution_evidence(
    run_id: str,
    input_path: Path,
    outputs: list[Path],
    stage_results: list[dict[str, Any]],
    structural_results: dict[str, Any],
    decisions: list[str],
    uncertainties: list[str],
) -> dict[str, Any]:
    return {
        "skill_id": SKILL_ID,
        "run_id": run_id,
        "role": "executor",
        "input_path": str(input_path),
        "outputs": [str(path) for path in outputs],
        "stage_results": stage_results,
        "commands_run": ["python scripts/raw_to_src.py run --input <path>"],
        "structural_results": structural_results,
        "key_decisions": decisions,
        "uncertainties": uncertainties,
        "created_artifacts": [str(path) for path in outputs],
    }


def build_supervision_evidence(
    run_id: str,
    input_path: Path,
    candidate_path: Path,
    acceptance_report: dict[str, Any],
    semantic_findings: list[dict[str, Any]],
    action: str,
) -> dict[str, Any]:
    reason = "Candidate is freeze-ready for external gate." if action == "next_skill" else "External gate materialization is required before downstream flow."
    return {
        "skill_id": SKILL_ID,
        "run_id": run_id,
        "role": "supervisor",
        "reviewed_inputs": [str(input_path)],
        "reviewed_outputs": [str(candidate_path)],
        "acceptance_dimensions": acceptance_report["dimensions"],
        "semantic_findings": semantic_findings,
        "decision": "pass" if action == "next_skill" else "revise",
        "reason": reason,
        "readiness_recommendation": action,
        "ownership_scope": "read_only_review",
    }
