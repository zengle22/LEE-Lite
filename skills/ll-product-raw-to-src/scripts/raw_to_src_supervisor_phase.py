#!/usr/bin/env python3
"""
Supervisor phase for raw-to-src.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from raw_to_src_bridge import acceptance_review, semantic_review
from raw_to_src_common import WORKFLOW_KEY, find_duplicate_src
from raw_to_src_records import (
    SEMANTIC_BUDGET,
    STRUCTURAL_BUDGET,
    build_handoff_proposal,
    build_job_proposal,
    build_package_manifest,
    build_proposed_actions,
    build_result_summary,
    build_retry_budget_report,
    build_run_state,
    build_supervision_evidence,
    stage,
)
from raw_to_src_runtime_support import collect_evidence_report, determine_action, read_json


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    normalized_input = read_json(artifacts_dir / "normalized-input.json")
    document = normalized_input["document"]
    candidate = read_json(artifacts_dir / "src-candidate.json")
    candidate_path = artifacts_dir / "src-candidate.md"
    structural_report = read_json(artifacts_dir / "structural-report.json")
    execution = read_json(artifacts_dir / "execution-evidence.json")

    duplicate_path = find_duplicate_src(repo_root, candidate["title"])
    review, semantic_findings = semantic_review(candidate, duplicate_path if not allow_update else None)
    annotated_semantic_findings = [
        {
            "finding_id": f"semantic-{run_id}-{index}",
            "source_stage": "source_semantic_review",
            "created_by_role": "supervisor",
            **finding,
        }
        for index, finding in enumerate(semantic_findings, start=1)
    ]
    supervisor_stages = [
        stage(
            "source_semantic_review",
            "passed" if review["decision"] == "pass" else "revise",
            review["summary"],
            "supervisor",
            input_refs=[str(artifacts_dir / "src-candidate.json")],
            output_refs=[str(artifacts_dir / "source-semantic-findings.json")],
            issues_found=[item["type"] for item in annotated_semantic_findings],
        )
    ]

    acceptance_report, acceptance_findings = acceptance_review(candidate, review)
    annotated_acceptance_findings = [
        {
            "finding_id": f"acceptance-{run_id}-{index}",
            "source_stage": "semantic_acceptance_review",
            "created_by_role": "supervisor",
            **finding,
        }
        for index, finding in enumerate(acceptance_findings, start=1)
    ]
    defects = annotated_semantic_findings + annotated_acceptance_findings
    semantic_attempts: list[dict[str, Any]] = []
    if defects:
        semantic_attempts.append(
            {
                "loop": "semantic",
                "attempt_number": 1,
                "reason": defects[0]["type"],
                "outcome": "retry_recommended",
            }
        )
    supervisor_stages.extend(
        [
            stage(
                "semantic_acceptance_review",
                acceptance_report["decision"],
                acceptance_report["summary"],
                "supervisor",
                input_refs=[str(artifacts_dir / "source-semantic-findings.json")],
                output_refs=[str(artifacts_dir / "acceptance-report.json")],
                issues_found=[item["type"] for item in annotated_acceptance_findings],
            ),
            stage(
                "semantic_fix_loop",
                "completed",
                "No semantic auto-rewrite performed.",
                "executor",
            ),
            stage(
                "semantic_recheck",
                "passed" if not defects else "failed",
                "Semantic recheck completed.",
                "supervisor",
                issues_found=[item["type"] for item in defects],
                revalidation_status="passed" if not defects else "failed",
            ),
        ]
    )

    status, action, target_skill, queue_path = determine_action(
        structural_report["input_valid"] and structural_report["intake_valid"],
        structural_report["issues"],
        defects,
        structural_report["structural_attempts"],
        semantic_attempts,
        allow_update,
    )
    stage_state = {
        "freeze_ready": "freeze_ready",
        "retry_proposed": "retry_recommended",
        "human_handoff_proposed": "handed_off",
        "blocked": "blocked",
    }[status]
    supervisor_stages.append(
        stage(
            "freeze_readiness_assessment",
            status,
            f"Recommended action: {action}",
            "supervisor",
            output_refs=[str(artifacts_dir / "result-summary.json")],
        )
    )

    write_json(
        artifacts_dir / "source-semantic-findings.json",
        {
            "run_id": run_id,
            "workflow_key": WORKFLOW_KEY,
            "stage_id": "source_semantic_review",
            "reviewed_artifact_ref": str(artifacts_dir / "src-candidate.json"),
            "decision": review["decision"],
            "summary": review["summary"],
            "created_by_role": "supervisor",
            "findings": annotated_semantic_findings,
        },
    )
    write_json(
        artifacts_dir / "acceptance-report.json",
        {
            "stage_id": "semantic_acceptance_review",
            "source_semantic_findings_ref": str(artifacts_dir / "source-semantic-findings.json"),
            "created_by_role": "supervisor",
            **acceptance_report,
        },
    )
    write_json(artifacts_dir / "defect-list.json", defects)
    budget_report = build_retry_budget_report(run_id, structural_report["structural_attempts"], semantic_attempts)
    write_json(artifacts_dir / "retry-budget-report.json", budget_report)

    handoff = build_handoff_proposal(run_id, action, target_skill, candidate_path, artifacts_dir)
    handoff_ref = None
    if handoff is not None:
        handoff_ref = str(artifacts_dir / "handoff-proposal.json")
        write_json(artifacts_dir / "handoff-proposal.json", handoff)

    retry_budget = 0
    if action == "retry":
        retry_budget = STRUCTURAL_BUDGET if structural_report["issues"] else SEMANTIC_BUDGET
    job = build_job_proposal(run_id, action, target_skill, queue_path, handoff_ref, candidate_path, retry_budget)
    actions = build_proposed_actions(run_id, status, action, target_skill, queue_path)
    summary = build_result_summary(run_id, status, action, target_skill, queue_path, candidate_path, artifacts_dir, handoff_ref, stage_state)
    combined_stages = execution["stage_results"] + supervisor_stages
    run_state = build_run_state(run_id, stage_state, action, combined_stages)
    supervision = build_supervision_evidence(
        run_id,
        Path(document["path"]),
        candidate_path,
        acceptance_report,
        annotated_semantic_findings,
        action,
    )
    manifest = build_package_manifest(artifacts_dir, candidate_path, status, action, handoff_ref)

    write_json(artifacts_dir / "job-proposal.json", job)
    write_json(artifacts_dir / "proposed-next-actions.json", actions)
    write_json(artifacts_dir / "result-summary.json", summary)
    write_json(artifacts_dir / "run-state.json", run_state)
    write_json(artifacts_dir / "supervision-evidence.json", supervision)
    write_json(artifacts_dir / "package-manifest.json", manifest)
    report_path = collect_evidence_report(artifacts_dir)

    return {
        "ok": True,
        "run_id": run_id,
        "status": status,
        "recommended_action": action,
        "candidate_path": str(candidate_path),
        "artifacts_dir": str(artifacts_dir),
        "package_manifest_path": str(artifacts_dir / "package-manifest.json"),
        "handoff_proposal_path": handoff_ref,
        "job_proposal_path": str(artifacts_dir / "job-proposal.json"),
        "review_report_path": str(report_path),
        "input_issues": execution["structural_results"]["input_validation"]["issues"],
    }
