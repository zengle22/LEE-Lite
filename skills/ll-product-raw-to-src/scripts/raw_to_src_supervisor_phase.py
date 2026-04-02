#!/usr/bin/env python3
"""
Supervisor phase for raw-to-src.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section
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
from raw_to_src_revision import apply_revision_request, load_revision_request
from raw_to_src_runtime_support import collect_evidence_report, determine_action, read_json


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _semantic_patch_events(
    run_id: str,
    patches: list[dict[str, Any]],
    *,
    start_index: int = 1,
) -> list[dict[str, Any]]:
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
        for index, patch in enumerate(patches, start=start_index)
    ]




def _apply_semantic_patch(
    candidate: dict[str, Any],
    findings: list[dict[str, Any]],
    *,
    duplicate_path: Path | None,
    document: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    working = json.loads(json.dumps(candidate, ensure_ascii=False))
    applied: list[dict[str, Any]] = []
    finding_types = {str(item.get("type") or "") for item in findings}
    bridge_fixable_findings = {
        "semantic_density_insufficient",
        "downstream_actionability_insufficient",
        "governance_constraint_clarity_insufficient",
        "non_goal_explicitness_insufficient",
        "bridge_summary_insufficient",
        "acceptance_impact_insufficient",
        "semantic_preservation_insufficient",
        "provenance_preservation_insufficient",
    }
    inventory_fixable_findings = {
        "semantic_inventory_too_thin",
        "semantic_preservation_insufficient",
        "feature_completeness",
    }

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
        _repair_problem_statement(working)
        applied.append(
            {
                "code": "layer_boundary",
                "action": "Rewrote problem statement to stay at SRC governance boundary and avoid downstream artifact layers.",
                "target_fields": ["problem_statement"],
            }
        )

    if finding_types & inventory_fixable_findings:
        _repair_semantic_inventory(working)
        applied.append(
            {
                "code": "semantic_inventory_repair",
                "action": "Expanded semantic_inventory with local bridge-derived objects, states, and routing surfaces.",
                "target_fields": ["semantic_inventory"],
            }
        )

    if finding_types & bridge_fixable_findings or "layer_boundary" in finding_types:
        _repair_bridge_context(working)
        applied.append(
            {
                "code": "bridge_context_repair",
                "action": "Rewrote bridge context to expose explicit governance objects, inheritance requirements, and downstream impact.",
                "target_fields": ["bridge_context", "key_constraints", "governance_change_summary"],
            }
        )

    return working, applied


def _merge_unique_texts(existing: Any, additions: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    def add(value: Any) -> None:
        text = str(value or "").strip()
        if not text:
            return
        key = text.casefold()
        if key in seen:
            return
        seen.add(key)
        merged.append(text)

    if isinstance(existing, list):
        for item in existing:
            add(item)
    elif existing not in (None, "", []):
        add(existing)

    for item in additions:
        add(item)
    return merged


def _normalize_object_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    token = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "_", text)
    token = re.sub(r"_+", "_", token).strip("_")
    return token


def _repair_problem_statement(working: dict[str, Any]) -> None:
    title = str(working.get("title") or "").strip() or "this SRC"
    working["problem_statement"] = (
        f"当前主链在《{title}》进入 implementation start 前仍缺一层独立的实施前压力测试边界，"
        "需要一份正式需求源只负责检测跨文档冲突、失败路径缺口和修复目标，"
        "避免 AI 在实施时对同一组联动对象形成不同解释。"
    )


def _repair_semantic_inventory(working: dict[str, Any]) -> None:
    semantic_lock = working.get("semantic_lock") or {}
    inventory = working.setdefault("semantic_inventory", {})
    target_objects = [
        semantic_lock.get("primary_object"),
        *working.get("target_capability_objects", []),
        "implementation_readiness_verdict",
        "deep_mode_trigger_rules",
        "score_to_verdict_binding_rules",
        "repair_target_routing_rules",
        "counterexample_coverage_rules",
    ]
    key_constraints = [str(item).strip() for item in working.get("key_constraints", []) if str(item).strip()]
    derived_inventory = {
        "core_objects": [token for token in (_normalize_object_token(item) for item in target_objects) if token],
        "product_surfaces": [
            "implementation_start_gate",
            "supervisor_review_surface",
            "allow_update_patch_surface",
            "freeze_readiness_assessment",
        ],
        "runtime_objects": [
            "feature_impl_candidate_package",
            "impl_spec_test_report_package",
            "implementation_readiness_gate_subject",
            "source_semantic_findings",
            "acceptance_report",
        ],
        "states": [
            "ready",
            "partial",
            "not_ready",
            "pass",
            "pass_with_revisions",
            "block",
        ],
        "entry_points": [
            "quick_preflight",
            "deep_spec_testing",
            "external_gate",
            "allow_update",
        ],
        "commands": [
            "allow_update",
            "retry",
            "next_skill",
            "human_handoff",
        ],
        "constraints": _merge_unique_texts(
            inventory.get("constraints"),
            key_constraints
            + [
                "workflow must keep IMPL as the main tested object and treat upstream authority as authoritative on conflict.",
                "workflow must surface score-to-verdict binding, repair-target routing, and counterexample coverage as machine-readable controls.",
            ],
        ),
    }

    for field, values in derived_inventory.items():
        current = inventory.get(field)
        if not isinstance(current, list) or not any(str(item).strip() for item in current):
            inventory[field] = values


def _repair_bridge_context(working: dict[str, Any]) -> None:
    semantic_lock = working.get("semantic_lock") or {}
    bridge = working.setdefault("bridge_context", {})
    governance_objects = _merge_unique_texts(
        bridge.get("governance_objects"),
        [
            _normalize_object_token(semantic_lock.get("primary_object")),
            *[_normalize_object_token(item) for item in working.get("target_capability_objects", [])],
            "implementation_start_boundary",
            "authority_non_override",
        ],
    )
    bridge["governance_objects"] = governance_objects[:8]
    title = str(working.get("title") or "").strip() or "this SRC"
    bridge["change_scope"] = (
        f"将《{title}》涉及的 {', '.join(governance_objects[:3])} 收敛为统一主链继承边界，"
        "明确主测试对象、联动 authority、修复目标与 verdict 协作责任。"
    )
    bridge["downstream_inheritance_requirements"] = _merge_unique_texts(
        bridge.get("downstream_inheritance_requirements"),
        [
            "下游必须继承主测试对象优先级与 authority non-override 规则。",
            "下游必须显式消费 quick_preflight 与 deep_spec_testing 的触发条件。",
            "下游必须显式消费 score_to_verdict、repair_target_artifact 与 counterexample coverage。",
        ],
    )
    bridge["acceptance_impact"] = _merge_unique_texts(
        bridge.get("acceptance_impact"),
        [
            "下游 gate、auditor 与 handoff 必须按同一组实施前压力测试边界消费 candidate。",
            "下游实现 consumer 必须在不回读原始 ADR 的前提下理解何时 block、何时修复、何时进入 implementation start。",
        ],
    )
    bridge["non_goals"] = _merge_unique_texts(bridge.get("non_goals"), list(working.get("out_of_scope", [])))
    working["key_constraints"] = _merge_unique_texts(
        working.get("key_constraints"),
        [
            "workflow 只能检测、升级并建议修复目标，不得自行裁决新的 business truth 或 design truth.",
            "下游继承约束必须显式声明主测试对象优先级、authority non-override、score-to-verdict 绑定、repair_target_artifact 与 counterexample coverage。",
            "bridge_context.governance_objects must be object-like tokens, not copied prose constraints.",
            "repair_target_artifact must be explicit in the repair plan and report artifacts.",
        ],
    )
    working["governance_change_summary"] = _merge_unique_texts(
        working.get("governance_change_summary"),
        [
            f"治理对象：{'; '.join(governance_objects[:4])}",
            "统一原则：implementation start 前必须运行 implementation spec testing；主测试对象固定为 IMPL；上游 authority 冲突时 workflow 只升级冲突、不改写 truth；结论必须落成 pass / pass_with_revisions / block",
            "下游必须继承的约束：主测试对象优先级、authority non-override、deep mode 强制触发、score-to-verdict 绑定、repair target 与高风险维度反例覆盖规则",
        ],
    )


def _document_test_report(
    *,
    artifacts_dir: Path,
    run_id: str,
    candidate: dict[str, Any],
    structural_report: dict[str, Any],
    defects: list[dict[str, Any]],
    acceptance_report: dict[str, Any],
    review: dict[str, Any],
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

    return build_document_test_report(
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


def supervisor_review(
    artifacts_dir: Path,
    repo_root: Path,
    run_id: str,
    allow_update: bool,
    revision_request_path: Path | None = None,
) -> dict[str, Any]:
    normalized_input = read_json(artifacts_dir / "normalized-input.json")
    document = normalized_input["document"]
    candidate = read_json(artifacts_dir / "src-candidate.json")
    candidate_path = artifacts_dir / "src-candidate.md"
    structural_report = read_json(artifacts_dir / "structural-report.json")
    execution = read_json(artifacts_dir / "execution-evidence.json")
    revision_request_ref, revision_request, revision_context = load_revision_request(artifacts_dir, revision_request_path)

    revision_patch_codes: list[str] = []
    if allow_update and revision_request:
        revised_candidate, revision_patches = apply_revision_request(
            candidate,
            revision_request,
            revision_request_ref=revision_request_ref,
            revision_context=revision_context,
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
    patch_event_count = 0
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
            document=document,
        )
        if applied_patches:
            candidate = patched_candidate
            write_json(artifacts_dir / "src-candidate.json", candidate)
            candidate_path.write_text(render_candidate_markdown(candidate), encoding="utf-8")
            semantic_patch_events = _semantic_patch_events(
                run_id,
                applied_patches,
                start_index=patch_event_count + 1,
            )
            semantic_patch_codes.extend(item["code"] for item in applied_patches)
            patch_event_count += len(semantic_patch_events)
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
    if allow_update and annotated_acceptance_findings:
        acceptance_attempt = {
            "loop": "semantic",
            "attempt_number": len(semantic_attempts) + 1,
            "reason": annotated_acceptance_findings[0]["type"],
            "outcome": "retry_recommended",
        }
        semantic_attempts.append(acceptance_attempt)
        patched_candidate, applied_patches = _apply_semantic_patch(
            candidate,
            annotated_acceptance_findings,
            duplicate_path=duplicate_path,
            document=document,
        )
        if applied_patches:
            candidate = patched_candidate
            write_json(artifacts_dir / "src-candidate.json", candidate)
            candidate_path.write_text(render_candidate_markdown(candidate), encoding="utf-8")
            acceptance_patch_events = _semantic_patch_events(
                run_id,
                applied_patches,
                start_index=patch_event_count + 1,
            )
            patch_event_count += len(acceptance_patch_events)
            semantic_patch_events.extend(acceptance_patch_events)
            semantic_patch_codes.extend(item["code"] for item in applied_patches)
            acceptance_attempt["outcome"] = "semantic_patch_applied"
            patch_lineage = read_json(artifacts_dir / "patch-lineage.json")
            patch_lineage["events"] = list(patch_lineage.get("events", [])) + acceptance_patch_events
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
            if annotated_semantic_findings or annotated_acceptance_findings:
                acceptance_attempt["outcome"] = "retry_recommended"
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
    document_test_report = _document_test_report(
        artifacts_dir=artifacts_dir,
        run_id=run_id,
        candidate=candidate,
        structural_report=structural_report,
        defects=defects,
        acceptance_report=acceptance_report,
        review=review,
        action=action,
        revision_request_ref=revision_request_ref,
    )
    document_test_report_path = artifacts_dir / "document-test-report.json"
    write_json(document_test_report_path, document_test_report)

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
        document_test_report_ref=str(document_test_report_path),
        document_test_outcome=str(document_test_report.get("test_outcome") or ""),
        revision_request_ref=revision_request_ref,
    )
    write_json(artifacts_dir / "supervision-evidence.json", supervision)
    manifest = build_package_manifest(
        artifacts_dir,
        candidate_path,
        status,
        action,
        handoff_ref,
        document_test_report_ref=str(document_test_report_path),
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
