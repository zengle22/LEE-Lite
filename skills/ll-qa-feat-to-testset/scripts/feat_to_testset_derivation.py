#!/usr/bin/env python3
"""Deterministic derivation helpers for feat-to-testset."""

from __future__ import annotations

import re
from typing import Any

from feat_to_testset_common import (
    derive_test_set_id,
    derive_test_set_ref,
    ensure_list,
    normalize_semantic_lock,
    slugify,
    unique_strings,
)
from feat_to_testset_environment import derive_required_environment_inputs as derive_required_environment_inputs_impl
from feat_to_testset_profiles import (
    derive_feature_owned_code_paths,
    derive_priority,
    derive_recommended_coverage_scope_name,
    derive_test_layers,
    feature_profile,
    is_explicit_web_feature,
)
from feat_to_testset_support import (
    derive_coverage_exclusions as derive_coverage_exclusions_impl,
    derive_environment_assumptions as derive_environment_assumptions_impl,
    derive_risk_focus as derive_risk_focus_impl,
    supporting_contract_refs as supporting_contract_refs_impl,
)
from feat_to_testset_units import (
    derive_acceptance_traceability as derive_acceptance_traceability_impl,
    derive_test_units as derive_test_units_impl,
)


def governing_adrs(feature: dict[str, Any], package_json: dict[str, Any]) -> list[str]:
    refs = ensure_list(feature.get("source_refs")) + ensure_list(package_json.get("source_refs"))
    return unique_strings([ref for ref in refs if ref.startswith("ADR-")])



def supporting_contract_refs(feature: dict[str, Any]) -> list[str]:
    return supporting_contract_refs_impl(feature_profile(feature), ensure_list(feature.get("source_refs")))


def derive_environment_assumptions(feature: dict[str, Any], layers: list[str]) -> list[str]:
    profile = feature_profile(feature)
    return derive_environment_assumptions_impl(feature, layers, profile, derive_downstream_target_skill(feature, layers))


def derive_required_environment_inputs(feature: dict[str, Any], layers: list[str]) -> dict[str, list[str]]:
    profile = feature_profile(feature)
    return derive_required_environment_inputs_impl(feature, layers, profile, derive_downstream_target_skill(feature, layers))


def derive_coverage_exclusions(feature: dict[str, Any]) -> list[str]:
    return derive_coverage_exclusions_impl(feature)


def derive_test_units(feature: dict[str, Any]) -> list[dict[str, Any]]:
    layers = derive_test_layers(feature)
    profile = feature_profile(feature)
    return derive_test_units_impl(feature, layers, profile, derive_priority(feature), supporting_contract_refs(feature))


def derive_acceptance_traceability(feature: dict[str, Any], units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return derive_acceptance_traceability_impl(feature, units, feature_profile(feature))


def derive_risk_focus(feature: dict[str, Any]) -> list[str]:
    return derive_risk_focus_impl(feature, feature_profile(feature))


def derive_coverage_goal(feature: dict[str, Any]) -> dict[str, Any]:
    if not derive_feature_owned_code_paths(feature):
        return {}
    goal: dict[str, Any] = {"line_rate_percent": 80}
    if feature_profile(feature) in {"runner_observability", "runner_dispatch", "pilot"}:
        goal["branch_rate_percent"] = 70
    return goal


def derive_branch_families(feature: dict[str, Any]) -> list[str]:
    if not derive_feature_owned_code_paths(feature):
        return []
    profile = feature_profile(feature)
    families = [profile]
    extras = {
        "runner_operator_entry": ["entry-mode-start", "entry-mode-resume", "context-lineage"],
        "runner_ready_job": ["approve-vs-non-approve", "progression-mode", "ready-vs-hold"],
        "runner_control_surface": ["claim-run-complete-fail", "ownership-guard", "state-transition"],
        "runner_intake": ["ready-scan", "claim-conflict", "lease-recovery"],
        "runner_dispatch": ["target-skill-routing", "authoritative-input-lineage", "dispatch-fail-closed"],
        "runner_feedback": ["done-vs-failed-vs-retry", "failure-evidence", "retry-reentry"],
        "runner_observability": ["status-buckets", "snapshot-traceability", "read-only-monitoring"],
        "pilot": ["pilot-chain", "fallback-path", "rollout-audit"],
    }
    families.extend(extras.get(profile, []))
    return unique_strings(families)


def derive_expansion_hints(feature: dict[str, Any], units: list[dict[str, Any]]) -> list[str]:
    if not derive_feature_owned_code_paths(feature):
        return []
    hints: list[str] = []
    for unit in units[:5]:
        hints.extend(
            [
                str(unit.get("unit_ref") or "").strip(),
                str(unit.get("acceptance_ref") or "").strip(),
                str(unit.get("title") or "").strip(),
            ]
        )
    return unique_strings([item for item in hints if item])


def derive_qualification_expectation(feature: dict[str, Any]) -> str:
    if not derive_feature_owned_code_paths(feature):
        return ""
    return "required" if derive_priority(feature) == "P1" else "recommended"


def derive_qualification_budget(feature: dict[str, Any], units: list[dict[str, Any]]) -> int | None:
    if not derive_feature_owned_code_paths(feature):
        return None
    return max(len(units) + 2, 6)


def derive_max_expansion_rounds(feature: dict[str, Any]) -> int | None:
    if not derive_feature_owned_code_paths(feature):
        return None
    return 2


def derive_preconditions(feature: dict[str, Any]) -> list[str]:
    preconditions = ensure_list(feature.get("dependencies"))[:3]
    if not preconditions:
        preconditions = ["selected FEAT 及其上游 source refs 可被稳定解析。"]
    profile = feature_profile(feature)
    extras = {
        "minimal_onboarding": ["登录/注册后最小建档主链可被执行。", "minimal profile state 与 homepage entry guard 可被解析。"],
        "first_ai_advice": ["minimal profile 已完成且可触发首轮建议生成。", "risk gate evaluator 可读取 running_level 与 recent_injury_status。"],
        "extended_profile_completion": ["homepage task card 已可见。", "扩展画像 patch 保存与 completion updater 可被解析。"],
        "device_deferred_entry": ["homepage 已可进入。", "deferred device entry 与 callback finalize surface 可被解析。"],
        "state_profile_boundary": ["primary_state / capability_flags 状态边界已存在。", "canonical profile store 与 unified reader 可被解析。"],
        "runner_ready_job": ["approve decision 已存在且 dispatchable。", "ready queue writer 可写入 artifacts/jobs/ready。"],
        "runner_operator_entry": ["Claude/Codex CLI 可调用 runner skill entry。", "runner context bootstrapper 可创建或恢复 run context。"],
        "runner_control_surface": ["runner control surface 已暴露 lifecycle commands。", "runner context 与 ownership record 可被解析。"],
        "runner_intake": ["ready execution job 已进入 artifacts/jobs/ready。", "single-owner claim guard 可输出 authoritative verdict。"],
        "runner_dispatch": ["claimed execution job 已形成 running ownership。", "target skill ref 与 authoritative input 可被解析。"],
        "runner_feedback": ["execution attempt record 已存在。", "downstream skill result 与 failure evidence 可回链到 runner。"],
        "runner_observability": ["ready queue、running ownership 与 outcome records 可被读取。", "status projector 可聚合 runner state。"],
        "projection_generation": ["Machine SSOT 已 freeze-ready。", "Projection template 已发布且可解析。"],
        "authoritative_snapshot": ["SSOT authoritative fields 已冻结。", "Snapshot extractor 可读取对应 source refs。"],
        "review_focus_risk": ["Projection 已渲染。", "review focus / risk analyzer 可读取 SSOT 与 projection context。"],
        "feedback_writeback": ["reviewer comment 已被捕获。", "SSOT writeback channel 可创建 revision request。"],
        "formal": ["approve decision object 已存在。", "formal publication / admission contract 可被解析。"],
        "io": ["Gateway / Path Policy / Registry 已接入主链。", "managed write/read preflight 可独立输出 verdict。"],
        "pilot": ["foundation FEAT 对应主链已可执行。", "至少一个真实 pilot scope 已被选定。"],
    }
    return unique_strings(preconditions + extras.get(profile, []))


def derive_pass_criteria(feature: dict[str, Any]) -> list[str]:
    criteria = [
        "每条 acceptance check 都有至少一个可执行测试单元映射。",
        "TESTSET 不越界覆盖相邻 FEAT 或新需求。",
        "candidate package 在外置 approval 前保持 machine-readable traceability 与 gate subject identity。",
    ]
    profile = feature_profile(feature)
    if derive_priority(feature) == "P1":
        criteria.append("高风险或 adoption/E2E 路径需要明确的环境、数据与 pilot execution 前提。")
    extras = {
        "minimal_onboarding": [
            "required fields invalid 时必须阻止 homepage entry，并留下字段级错误 evidence。",
            "device connection 只能作为 deferred follow-up entry，不得重新阻塞首进链路。",
        ],
        "first_ai_advice": [
            "risk gate 缺字段或高风险时必须阻止正常 advice branch，并返回补充提示路径。",
            "training_advice_level / first_week_action / needs_more_info_prompt / device_connect_prompt 必须齐全可追溯。",
        ],
        "extended_profile_completion": [
            "任务卡分步补全与增量保存必须可执行，且 completion percent / next task cards 会刷新。",
            "patch save failure 不得撤销 homepage_entered，必须保留 retry entry。",
        ],
        "device_deferred_entry": [
            "设备连接只能在首页后以 deferred entry 方式出现，并允许 skip。",
            "device_failed_nonblocking / device_skipped 结果不得阻塞首页或首轮建议。",
        ],
        "state_profile_boundary": [
            "primary_state / capability_flags 语义必须显式区分，不能混写。",
            "cross-boundary 冲突必须 fail closed，且 user_physical_profile 保持唯一事实源。",
        ],
        "runner_ready_job": [
            "approve 后必须产出 ready execution job，并保留 approve-to-job lineage。",
            "non-approve 路径不得生成 ready queue item。",
        ],
        "runner_operator_entry": [
            "runner skill entry 必须是显式的 Claude/Codex CLI 用户入口。",
            "start / resume 必须保留 authoritative run context，不得退化成 manual relay。",
        ],
        "runner_control_surface": [
            "runner CLI control surface 必须统一暴露 claim/run/complete/fail 等控制语义。",
            "control plane 不得越权改写 dispatch 或 outcome 业务边界。",
        ],
        "runner_intake": [
            "ready queue consumption 必须保持 single-owner claim 语义。",
            "claim conflict、job_not_ready 等失败路径必须可追溯且 fail closed。",
        ],
        "runner_dispatch": [
            "claimed job 必须派发到声明的 target skill，并保留 authoritative input lineage。",
            "dispatch 不得退化成第三会话人工接力。",
        ],
        "runner_feedback": [
            "done / failed / retry-reentry 必须形成单一 authoritative outcome。",
            "failure evidence 与 retry-reentry directive 必须可追溯。",
        ],
        "runner_observability": [
            "监控面必须覆盖 ready backlog、running、failed、deadletters、waiting-human 状态。",
            "监控面只能读取 authoritative runner records，不得扫目录猜状态。",
        ],
        "projection_generation": [
            "Projection blocks 必须从 Machine SSOT 派生，且保留 derived-only / traceability 标记。",
            "Projection 不得被下游继承为 authoritative source。",
        ],
        "authoritative_snapshot": [
            "Snapshot 只包含 completed state / authoritative output / frozen boundary / open technical decisions。",
            "缺少 authoritative field 时必须显式 fail closed。",
        ],
        "review_focus_risk": [
            "Review Focus / Risks / Ambiguities 只服务 reviewer 决策，不引入新的 authority object。",
            "不可回链的 risk signal 不得出现在最终 projection 中。",
        ],
        "feedback_writeback": [
            "review comment 必须映射为 SSOT revision request，而不是直接修改 projection。",
            "Projection regeneration 必须由 updated SSOT 触发并保留 provenance。",
        ],
        "formal": [
            "formal_ref / lineage / admission verdict 必须形成单一 authoritative consumption path。",
            "lineage_missing 或 layer_violation 必须 fail closed。",
        ],
        "io": [
            "commit-governed / read-governed 成功路径必须返回 receipt_ref、registry_record_ref、managed_artifact_ref。",
            "policy_deny / registry_prerequisite_failed / receipt_pending 必须留下可追溯结果且不得 fallback。",
        ],
        "pilot": [
            "至少一条 producer -> gate -> formal -> consumer -> audit 真实 pilot 主链被验证。",
            "pilot evidence 缺失时 rollout 必须 fail closed，fallback / wave state 必须可追溯。",
        ],
        "gate": [
            "gate decision path 必须唯一，decision object 不得并行分叉。",
            "formal publication 只由 approve decision object 触发。",
        ],
    }
    return unique_strings(criteria + extras.get(profile, []))


def derive_evidence_required(feature: dict[str, Any], layers: list[str]) -> list[str]:
    evidence = [
        "analysis 与 strategy 形成过程的 execution evidence",
        "supervisor 对 TESTSET 与 traceability 的 review evidence",
        "candidate package 的 machine-readable gate subject records",
    ]
    if "e2e" in layers:
        evidence.append("若进入 e2e 层，需补充 pilot 链路或 UI/integration context 的执行前提证据")
    extras = {
        "minimal_onboarding": ["minimal profile submission evidence", "homepage entry decision evidence", "deferred device entry evidence"],
        "first_ai_advice": ["first advice payload evidence", "risk gate verdict evidence", "fallback / completion prompt evidence"],
        "extended_profile_completion": ["task-card rendering evidence", "patch save evidence", "completion percent update evidence"],
        "device_deferred_entry": ["deferred device connection evidence", "skip / non-blocking failure evidence", "homepage preservation evidence"],
        "state_profile_boundary": ["primary_state write evidence", "canonical ownership / conflict_blocked evidence", "unified-reader judgment evidence"],
        "runner_ready_job": ["ready execution job evidence", "approve-to-job lineage evidence", "ready queue receipt"],
        "runner_operator_entry": ["runner invocation receipt", "runner context bootstrap evidence", "runner skill entry trace"],
        "runner_control_surface": ["runner control action record", "job ownership evidence", "control-plane state transition evidence"],
        "runner_intake": ["ready queue scan evidence", "claim receipt", "running ownership record"],
        "runner_dispatch": ["next-skill invocation evidence", "execution attempt record", "dispatch lineage trace"],
        "runner_feedback": ["execution outcome evidence", "retry-reentry directive evidence", "failure evidence binding"],
        "runner_observability": ["runner observability snapshot", "backlog / running / failed status evidence", "waiting-human / deadletter view evidence"],
        "projection_generation": ["projection render evidence", "derived-only marker evidence", "projection trace refs"],
        "authoritative_snapshot": ["authoritative snapshot evidence", "authoritative field trace evidence"],
        "review_focus_risk": ["review focus extraction evidence", "risk / ambiguity trace evidence"],
        "feedback_writeback": ["projection comment evidence", "revision request evidence", "projection regeneration evidence"],
        "formal": ["formal_ref resolution evidence", "lineage build / lineage_missing evidence", "admission verdict evidence"],
        "io": ["receipt_ref", "registry_record_ref", "managed_artifact_ref", "policy_deny / registry_prerequisite_failed / receipt_pending evidence"],
        "pilot": ["pilot evidence package", "wave state / cutover_guard_ref evidence", "fallback / rollback evidence"],
        "gate": ["decision object evidence", "approve / revise / retry / handoff / reject routing evidence"],
    }
    return unique_strings(evidence + extras.get(feature_profile(feature), []))


def derive_downstream_target_skill(feature: dict[str, Any], layers: list[str]) -> str:
    del layers
    return "skill.qa.test_exec_web_e2e" if is_explicit_web_feature(feature) else "skill.qa.test_exec_cli"


def derive_analysis_markdown(feature: dict[str, Any], package_json: dict[str, Any], derived_slug: str) -> str:
    source_refs = unique_strings(ensure_list(feature.get("source_refs")) + ensure_list(package_json.get("source_refs")))
    governing = governing_adrs(feature, package_json)
    return "\n\n".join(
        [
            f"# Requirement Analysis for {feature.get('feat_ref')}",
            "## Selected FEAT\n\n"
            + "\n".join(
                [
                    f"- feat_ref: `{feature.get('feat_ref')}`",
                    f"- title: {feature.get('title')}",
                    f"- derived_slug: `{derived_slug}`",
                    f"- epic_ref: `{feature.get('epic_ref') or package_json.get('epic_freeze_ref')}`",
                    f"- src_ref: `{package_json.get('src_root_id')}`",
                    f"- profile: `{feature_profile(feature)}`",
                ]
            ),
            "## Boundary Analysis\n\n"
            + "\n".join([f"- {item}" for item in ensure_list(feature.get("scope"))])
            + "\n\n## Non-Goals\n\n"
            + "\n".join([f"- {item}" for item in ensure_list(feature.get("non_goals")) or ["- 未声明额外 non-goals，按 FEAT 现有边界执行。"]]),
            "## Constraint and Risk Intake\n\n" + "\n".join([f"- {item}" for item in derive_risk_focus(feature)]),
            "## Governing References\n\n"
            + "\n".join([f"- {item}" for item in governing] or ["- No explicit ADR refs inherited."])
            + "\n\n## Source Refs\n\n"
            + "\n".join([f"- {item}" for item in source_refs]),
        ]
    )


def derive_strategy_yaml(feature: dict[str, Any], package_json: dict[str, Any]) -> dict[str, Any]:
    layers = derive_test_layers(feature)
    units = derive_test_units(feature)
    return {
        "strategy_id": f"strategy-{slugify(str(feature.get('feat_ref') or 'feat'))}",
        "selected_feat_ref": feature.get("feat_ref"),
        "profile": feature_profile(feature),
        "priority": derive_priority(feature),
        "test_layers": layers,
        "risk_focus": derive_risk_focus(feature),
        "environment_assumptions": derive_environment_assumptions(feature, layers),
        "coverage_exclusions": derive_coverage_exclusions(feature),
        "test_units": units,
        "acceptance_traceability": derive_acceptance_traceability(feature, units),
        "governing_adrs": governing_adrs(feature, package_json),
        "semantic_lock": normalize_semantic_lock(feature.get("semantic_lock")),
        "coverage_goal": derive_coverage_goal(feature),
        "branch_families": derive_branch_families(feature),
        "expansion_hints": derive_expansion_hints(feature, units),
        "qualification_expectation": derive_qualification_expectation(feature),
        "qualification_budget": derive_qualification_budget(feature, units),
        "max_expansion_rounds": derive_max_expansion_rounds(feature),
    }


def build_gate_subjects(run_id: str, feat_ref: str) -> dict[str, dict[str, Any]]:
    return {
        "analysis_review": {
            "subject_id": f"gate-subject-{run_id}-analysis",
            "gate_type": "analysis_review",
            "subject_kind": "gate_subject",
            "workflow_key": "qa.feat-to-testset",
            "workflow_run_id": run_id,
            "feat_ref": feat_ref,
            "artifact_ref": "analysis.md",
            "related_refs": ["test-set.yaml", "test-set-bundle.json"],
        },
        "strategy_review": {
            "subject_id": f"gate-subject-{run_id}-strategy",
            "gate_type": "strategy_review",
            "subject_kind": "gate_subject",
            "workflow_key": "qa.feat-to-testset",
            "workflow_run_id": run_id,
            "feat_ref": feat_ref,
            "artifact_ref": "strategy-draft.yaml",
            "related_refs": ["test-set.yaml", "test-set-bundle.json"],
        },
        "test_set_approval": {
            "subject_id": f"gate-subject-{run_id}-approval",
            "gate_type": "test_set_approval",
            "subject_kind": "gate_subject",
            "workflow_key": "qa.feat-to-testset",
            "workflow_run_id": run_id,
            "feat_ref": feat_ref,
            "artifact_ref": "test-set.yaml",
            "related_refs": ["test-set-review-report.json", "test-set-acceptance-report.json", "test-set-bundle.json"],
        },
    }


def build_test_set_yaml(feature: dict[str, Any], package_json: dict[str, Any]) -> dict[str, Any]:
    feat_ref = str(feature.get("feat_ref") or "")
    layers = derive_test_layers(feature)
    units = derive_test_units(feature)
    test_set_yaml = {
        "id": derive_test_set_ref(feat_ref),
        "ssot_type": "TESTSET",
        "workflow_key": "qa.feat-to-testset",
        "template_id": "template.qa.test_set_production",
        "template_workflow_key": "workflow.qa.test_set_production_l3",
        "test_set_id": derive_test_set_id(feat_ref),
        "feat_ref": feat_ref,
        "epic_ref": str(feature.get("epic_ref") or package_json.get("epic_freeze_ref") or ""),
        "src_ref": str(package_json.get("src_root_id") or ""),
        "title": f"{feature.get('title')} Test Set",
        "description": f"{feature.get('title')} governed QA candidate package",
        "derived_slug": slugify(str(feature.get("title") or feat_ref)),
        "coverage_scope": ensure_list(feature.get("scope")),
        "recommended_coverage_scope_name": derive_recommended_coverage_scope_name(feature),
        "feature_owned_code_paths": derive_feature_owned_code_paths(feature),
        "coverage_goal": derive_coverage_goal(feature),
        "branch_families": derive_branch_families(feature),
        "expansion_hints": derive_expansion_hints(feature, units),
        "qualification_expectation": derive_qualification_expectation(feature),
        "risk_focus": derive_risk_focus(feature),
        "preconditions": derive_preconditions(feature),
        "environment_assumptions": derive_environment_assumptions(feature, layers),
        "required_environment_inputs": derive_required_environment_inputs(feature, layers),
        "test_layers": layers,
        "test_units": units,
        "coverage_exclusions": derive_coverage_exclusions(feature),
        "pass_criteria": derive_pass_criteria(feature),
        "evidence_required": derive_evidence_required(feature, layers),
        "acceptance_traceability": derive_acceptance_traceability(feature, units),
        "source_refs": unique_strings(
            [f"product.epic-to-feat::{package_json.get('workflow_run_id')}", feat_ref]
            + ensure_list(feature.get("source_refs"))
            + ensure_list(package_json.get("source_refs"))
        ),
        "governing_adrs": governing_adrs(feature, package_json),
        "semantic_lock": normalize_semantic_lock(feature.get("semantic_lock")),
        "status": "draft",
    }
    qualification_budget = derive_qualification_budget(feature, units)
    if qualification_budget is not None:
        test_set_yaml["qualification_budget"] = qualification_budget
    max_expansion_rounds = derive_max_expansion_rounds(feature)
    if max_expansion_rounds is not None:
        test_set_yaml["max_expansion_rounds"] = max_expansion_rounds
    return test_set_yaml

