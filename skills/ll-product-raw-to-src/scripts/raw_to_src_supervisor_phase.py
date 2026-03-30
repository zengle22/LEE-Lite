#!/usr/bin/env python3
"""
Supervisor phase for raw-to-src.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from raw_to_src_bridge import acceptance_review, semantic_review
from raw_to_src_common import WORKFLOW_KEY, find_duplicate_src, render_candidate_markdown
from raw_to_src_gate_integration import create_gate_ready_package, submit_gate_pending
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


def _semantic_patch_events(run_id: str, patches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "patch_id": f"patch-{run_id}-semantic-{index}",
            "stage_id": "semantic_fix_loop",
            "actor_role": "supervisor",
            "patch_scope": "semantic",
            "patch_mode": "targeted_repair",
            "issue_code": patch["code"],
            "target_fields": patch["target_fields"],
            "action": patch["action"],
            "outcome": "applied",
        }
        for index, patch in enumerate(patches, start=1)
    ]


def _append_unique(items: list[str], additions: list[str]) -> list[str]:
    seen = {str(item).strip() for item in items if str(item).strip()}
    merged = list(items)
    for item in additions:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        merged.append(text)
    return merged


def _apply_revision_request(
    candidate: dict[str, Any],
    revision_request: dict[str, Any],
    *,
    revision_request_ref: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    working = json.loads(json.dumps(candidate, ensure_ascii=False))
    applied: list[dict[str, Any]] = []
    decision_reason = str(revision_request.get("decision_reason") or "").strip()
    if not decision_reason:
        return working, applied

    lower_reason = decision_reason.lower()
    key_constraints = list(working.get("key_constraints", []))
    business_drivers = list(working.get("business_drivers", []))
    in_scope = list(working.get("in_scope", []))
    source_refs = list(working.get("source_refs", []))
    semantic_inventory = working.setdefault("semantic_inventory", {})
    semantic_constraints = list(semantic_inventory.get("constraints", []))

    source_ref_updates = [revision_request_ref, str(revision_request.get("source_gate_decision_ref") or "").strip()]
    updated_source_refs = _append_unique(source_refs, source_ref_updates)
    if updated_source_refs != source_refs:
        working["source_refs"] = updated_source_refs
        applied.append(
            {
                "code": "revision_source_refs",
                "action": "Appended gate revision references into source_refs for traceability.",
                "target_fields": ["source_refs"],
            }
        )

    if any(token in lower_reason for token in ("running_level", "starter", "can_run_5k", "race_finisher", "训练基础轴")):
        additions = [
            "最小分层字段 `running_level` 必须收敛为单一训练基础轴，不得混合训练阶段、当前能力与历史赛事经历三种口径。",
            "正式比赛经历不属于最小建档必填项，应下沉到扩展画像中补充。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_running_level_axis",
                    "action": "Normalized running_level constraints into a single training-base axis.",
                    "target_fields": ["key_constraints", "semantic_inventory.constraints"],
                }
            )
            key_constraints = updated_constraints
            semantic_constraints = updated_semantic_constraints

    if any(token in lower_reason for token in ("recent_injury_status", "伤病", "疼痛", "无伤优先")):
        additions = [
            "最小建档必填字段至少包括 `gender / birthday / height_cm / weight_kg / running_level / recent_injury_status`，用于支撑首轮建议的安全门槛。",
            "AI 首轮建议必须以“无伤优先”为前置约束；若存在明显疼痛或恢复中状态，不得直接进入强度课建议。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_drivers = _append_unique(business_drivers, ["首轮建议必须先拿到最小风险输入，再决定训练强度与恢复建议。"])
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_drivers != business_drivers or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            working["business_drivers"] = updated_drivers
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_minimal_risk_input",
                    "action": "Added recent_injury_status and injury-first recommendation guardrails into the SRC constraints.",
                    "target_fields": ["key_constraints", "business_drivers", "semantic_inventory.constraints"],
                }
            )
            key_constraints = updated_constraints
            business_drivers = updated_drivers
            semantic_constraints = updated_semantic_constraints

    if any(token in lower_reason for token in ("extended_profile_completed", "device_connected", "initial_plan_ready", "组合化", "capability flags")):
        additions = [
            "状态模型应区分主阶段状态与独立 capability flags；`extended_profile_completed`、`device_connected`、`initial_plan_ready` 不得被建模为严格串行阶段。",
            "设备连接、扩展画像补全与初始计划准备应允许独立完成，避免把非阻塞能力错误建模成单线状态流。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_state_capabilities",
                    "action": "Reframed state semantics into stage state plus independent capability flags.",
                    "target_fields": ["key_constraints", "semantic_inventory.constraints"],
                }
            )
            key_constraints = updated_constraints
            semantic_constraints = updated_semantic_constraints

    hard_constraint_markers = (
        "一个提交动作",
        "首页任务卡",
        "增量更新",
        "最低输出目标",
        "第一周行动建议",
        "连接设备",
    )
    if any(marker in decision_reason for marker in hard_constraint_markers):
        additions = [
            "最小建档页不得拆成多页向导；用户填写后应一次提交并直接进入首页。",
            "首页任务卡只用于增强，不得阻塞首次 AI 可用体验。",
            "扩展画像应支持增量更新，不要求用户一次性完成全量补充。",
            "AI 首轮建议至少应包含当前训练建议级别、第一周行动建议、是否提示补充更多信息、是否提示连接设备。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_scope = _append_unique(
            in_scope,
            [
                "定义最小建档单次提交边界、首页任务卡非阻塞边界，以及首轮建议的最低输出要求。",
            ],
        )
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_scope != in_scope or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            working["in_scope"] = updated_scope
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_non_blocking_onboarding",
                    "action": "Added non-blocking onboarding and minimum first-recommendation constraints from the gate revise request.",
                    "target_fields": ["key_constraints", "in_scope", "semantic_inventory.constraints"],
                }
            )

    return working, applied


def _apply_semantic_patch(
    candidate: dict[str, Any],
    findings: list[dict[str, Any]],
    *,
    duplicate_path: Path | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    working = json.loads(json.dumps(candidate, ensure_ascii=False))
    applied: list[dict[str, Any]] = []
    finding_types = {str(item.get("type") or "") for item in findings}

    if "duplicate_title" in finding_types and duplicate_path is not None:
        base_title = str(working.get("title") or "").strip()
        if base_title and not base_title.endswith("修订版"):
            working["title"] = f"{base_title} 修订版"
            applied.append(
                {
                    "code": "duplicate_title",
                    "action": f"Adjusted SRC title to avoid duplicate slug with {duplicate_path}.",
                    "target_fields": ["title"],
                }
            )

    if "layer_boundary" in finding_types:
        working["problem_statement"] = (
            "当前已落地的治理语义仍分散在 skill、runtime、contract 与测试中；"
            "如果不把这些约束收敛成统一的 SRC 继承源，下游会继续各自重写输入边界、冻结条件与交接规则。"
        )
        applied.append(
            {
                "code": "layer_boundary",
                "action": "Rewrote problem statement to stay at SRC governance boundary and avoid downstream artifact layers.",
                "target_fields": ["problem_statement"],
            }
        )

    return working, applied


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    normalized_input = read_json(artifacts_dir / "normalized-input.json")
    document = normalized_input["document"]
    candidate = read_json(artifacts_dir / "src-candidate.json")
    candidate_path = artifacts_dir / "src-candidate.md"
    structural_report = read_json(artifacts_dir / "structural-report.json")
    execution = read_json(artifacts_dir / "execution-evidence.json")
    revision_request_path = artifacts_dir / "revision-request.json"
    revision_request_ref = str(revision_request_path) if revision_request_path.exists() else ""
    revision_request = read_json(revision_request_path) if revision_request_ref else {}

    revision_patch_codes: list[str] = []
    if allow_update and revision_request:
        revised_candidate, revision_patches = _apply_revision_request(
            candidate,
            revision_request,
            revision_request_ref=revision_request_ref,
        )
        if revision_patches:
            candidate = revised_candidate
            write_json(artifacts_dir / "src-candidate.json", candidate)
            candidate_path.write_text(render_candidate_markdown(candidate), encoding="utf-8")
            revision_patch_codes = [item["code"] for item in revision_patches]
            patch_lineage = read_json(artifacts_dir / "patch-lineage.json")
            patch_lineage["events"] = list(patch_lineage.get("events", [])) + _semantic_patch_events(run_id, revision_patches)
            write_json(artifacts_dir / "patch-lineage.json", patch_lineage)

    duplicate_path = find_duplicate_src(repo_root, candidate["title"])
    review, semantic_findings = semantic_review(
        candidate,
        duplicate_path,
        document=document,
    )
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

    semantic_attempts: list[dict[str, Any]] = []
    semantic_patch_events: list[dict[str, Any]] = []
    semantic_patch_codes: list[str] = list(revision_patch_codes)
    if annotated_semantic_findings:
        semantic_attempts.append(
            {
                "loop": "semantic",
                "attempt_number": 1,
                "reason": annotated_semantic_findings[0]["type"],
                "outcome": "retry_recommended",
            }
        )

    if allow_update and annotated_semantic_findings:
        patched_candidate, applied_patches = _apply_semantic_patch(
            candidate,
            annotated_semantic_findings,
            duplicate_path=duplicate_path,
        )
        if applied_patches:
            candidate = patched_candidate
            write_json(artifacts_dir / "src-candidate.json", candidate)
            candidate_path.write_text(render_candidate_markdown(candidate), encoding="utf-8")
            semantic_patch_events = _semantic_patch_events(run_id, applied_patches)
            semantic_patch_codes.extend(item["code"] for item in applied_patches)
            semantic_attempts[-1]["outcome"] = "semantic_patch_applied"
            patch_lineage = read_json(artifacts_dir / "patch-lineage.json")
            patch_lineage["events"] = list(patch_lineage.get("events", [])) + semantic_patch_events
            write_json(artifacts_dir / "patch-lineage.json", patch_lineage)
            review, semantic_findings = semantic_review(candidate, None, document=document)
            annotated_semantic_findings = [
                {
                    "finding_id": f"semantic-{run_id}-{index}",
                    "source_stage": "semantic_recheck",
                    "created_by_role": "supervisor",
                    **finding,
                }
                for index, finding in enumerate(semantic_findings, start=1)
            ]
            if annotated_semantic_findings:
                semantic_attempts[-1]["outcome"] = "retry_recommended"

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
                "completed" if semantic_patch_codes else "skipped",
                "Semantic targeted repair executed." if semantic_patch_codes else "No semantic auto-rewrite performed.",
                "supervisor",
                patches_applied=semantic_patch_codes,
            ),
            stage(
                "semantic_recheck",
                "passed" if not defects else "failed",
                "Semantic recheck completed.",
                "supervisor",
                issues_found=[item["type"] for item in defects],
                patches_applied=semantic_patch_codes,
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
    handoff_submission_ref = None
    if handoff is not None:
        handoff_ref = str(artifacts_dir / "handoff-proposal.json")
        write_json(artifacts_dir / "handoff-proposal.json", handoff)
        handoff_submission_ref = str((artifacts_dir / "handoff-proposal.json").resolve().relative_to(repo_root.resolve()).as_posix())

    gate_ready_package_ref = None
    authoritative_handoff_ref = None
    gate_pending_ref = None
    if action == "next_skill" and handoff_ref is not None:
        registry_record_ref = str(structural_report.get("cli_candidate_registry_record_ref", "")).strip()
        candidate_ref = f"raw-to-src.{run_id}.src-candidate"
        if registry_record_ref:
            registry_record = read_json(repo_root / registry_record_ref)
            candidate_ref = str(registry_record.get("artifact_ref", candidate_ref))
        gate_ready_package = create_gate_ready_package(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=run_id,
            candidate_ref=candidate_ref,
            machine_ssot_ref=str((artifacts_dir / "src-candidate.json").resolve().relative_to(repo_root.resolve()).as_posix()),
            acceptance_ref=str((artifacts_dir / "acceptance-report.json").resolve().relative_to(repo_root.resolve()).as_posix()),
            evidence_bundle_ref=str((artifacts_dir / "supervision-evidence.json").resolve().relative_to(repo_root.resolve()).as_posix()),
        )
        gate_ready_package_ref = str(gate_ready_package.resolve().relative_to(repo_root.resolve()).as_posix())
        gate_submit = submit_gate_pending(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=run_id,
            proposal_ref=handoff_submission_ref,
            payload_path=gate_ready_package,
            trace_context_ref=str((artifacts_dir / "supervision-evidence.json").resolve().relative_to(repo_root.resolve()).as_posix()),
        )
        gate_submit_data = gate_submit["response"]["data"]
        authoritative_handoff_ref = str(gate_submit_data.get("handoff_ref", ""))
        gate_pending_ref = str(gate_submit_data.get("gate_pending_ref", ""))
        supervisor_stages.append(
            stage(
                "gate_pending_submission",
                "submitted",
                "Authoritative handoff submitted to gate pending queue.",
                "supervisor",
                input_refs=[handoff_ref, gate_ready_package_ref],
                output_refs=[authoritative_handoff_ref, gate_pending_ref, str(gate_submit["response_path"])],
            )
        )

    retry_budget = 0
    if action == "retry":
        retry_budget = STRUCTURAL_BUDGET if structural_report["issues"] else SEMANTIC_BUDGET
    job = build_job_proposal(run_id, action, target_skill, queue_path, handoff_ref, candidate_path, retry_budget)
    actions = build_proposed_actions(run_id, status, action, target_skill, queue_path)
    summary = build_result_summary(
        run_id,
        status,
        action,
        target_skill,
        queue_path,
        candidate_path,
        artifacts_dir,
        handoff_ref,
        stage_state,
        gate_ready_package_ref=gate_ready_package_ref,
        authoritative_handoff_ref=authoritative_handoff_ref,
        gate_pending_ref=gate_pending_ref,
        revision_request_ref=revision_request_ref,
    )
    combined_stages = execution["stage_results"] + supervisor_stages
    run_state = build_run_state(run_id, stage_state, action, combined_stages, revision_request_ref=revision_request_ref)
    supervision = build_supervision_evidence(
        run_id,
        Path(document["path"]),
        candidate_path,
        acceptance_report,
        annotated_semantic_findings,
        action,
        revision_request_ref=revision_request_ref,
    )
    write_json(artifacts_dir / "supervision-evidence.json", supervision)
    manifest = build_package_manifest(
        artifacts_dir,
        candidate_path,
        status,
        action,
        handoff_ref,
        gate_ready_package_ref=gate_ready_package_ref,
        authoritative_handoff_ref=authoritative_handoff_ref,
        gate_pending_ref=gate_pending_ref,
        revision_request_ref=revision_request_ref,
    )

    write_json(artifacts_dir / "job-proposal.json", job)
    write_json(artifacts_dir / "proposed-next-actions.json", actions)
    write_json(artifacts_dir / "result-summary.json", summary)
    write_json(artifacts_dir / "run-state.json", run_state)
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
        "gate_ready_package_ref": gate_ready_package_ref,
        "authoritative_handoff_ref": authoritative_handoff_ref,
        "gate_pending_ref": gate_pending_ref,
        "revision_request_ref": revision_request_ref,
        "input_issues": execution["structural_results"]["input_validation"]["issues"],
    }
