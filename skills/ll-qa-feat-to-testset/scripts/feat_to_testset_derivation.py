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


def feature_profile(feature: dict[str, Any]) -> str:
    lock = normalize_semantic_lock(feature.get("semantic_lock"))
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    if axis_id == "projection-generation":
        return "projection_generation"
    if axis_id == "authoritative-snapshot":
        return "authoritative_snapshot"
    if axis_id == "review-focus-risk":
        return "review_focus_risk"
    if axis_id == "feedback-writeback":
        return "feedback_writeback"
    if str(lock.get("domain_type") or "").strip().lower() == "review_projection_rule":
        title = str(feature.get("title") or "").lower()
        if "snapshot" in title:
            return "authoritative_snapshot"
        if "review focus" in title or "风险" in title or "ambigu" in title:
            return "review_focus_risk"
        if "writeback" in title or "回写" in title or "批注" in title:
            return "feedback_writeback"
        return "projection_generation"
    title_text = " ".join(
        [
            str(feature.get("title") or ""),
            str(feature.get("authoritative_artifact") or ""),
            str(feature.get("axis_id") or ""),
            str(feature.get("derived_axis") or ""),
        ]
    ).lower()
    related_text = " ".join(ensure_list(feature.get("consumes")) + ensure_list(feature.get("produces"))).lower()
    fallback_text = " ".join(
        ensure_list(feature.get("scope"))
        + ensure_list(feature.get("constraints"))
        + ensure_list(feature.get("dependencies"))
        + [str(feature.get("gate_decision_dependency") or ""), str(feature.get("admission_dependency") or "")]
    ).lower()
    buckets = [
        ("io", ["governed write-read receipt", "managed ref", "receipt", "registry", "artifact-io-governance", "governed io", "落盘与读取流"]),
        ("formal", ["formal publication", "formal ref", "lineage", "admission", "formal object", "formal 发布", "准入流"]),
        ("gate", ["gate", "decision object", "gate-decision", "handoff-formalization", "审核与裁决流"]),
        ("collaboration", ["candidate", "handoff submission", "collaboration-loop", "候选提交与交接流"]),
        ("pilot", ["pilot", "onboarding", "cutover", "fallback", "wave", "compat mode", "skill-adoption-e2e", "接入与 pilot 验证流"]),
    ]
    for text in (title_text, related_text, f"{title_text} {related_text} {fallback_text}"):
        for profile, markers in buckets:
            if any(marker in text for marker in markers):
                return profile
    return "default"


def derive_priority(feature: dict[str, Any]) -> str:
    track = str(feature.get("track") or "").lower()
    profile = feature_profile(feature)
    text = " ".join(ensure_list(feature.get("scope")) + ensure_list(feature.get("constraints")) + [str(feature.get("title") or "")]).lower()
    if profile == "pilot" or "adoption" in track or "e2e" in track or "pilot" in text:
        return "P1"
    return "P0"


def derive_test_layers(feature: dict[str, Any]) -> list[str]:
    layers = ["integration"]
    joined_text = " ".join(ensure_list(feature.get("scope")) + [str(feature.get("axis_id") or ""), str(feature.get("track") or ""), feature_profile(feature)]).lower()
    if any(marker in joined_text for marker in ["e2e", "pilot", "ui", "cross skill", "cross-skill"]):
        layers.append("e2e")
    return layers


def derive_recommended_coverage_scope_name(feature: dict[str, Any]) -> list[str]:
    profile = feature_profile(feature)
    title = str(feature.get("title") or "").strip()
    mapping = {
        "collaboration": "mainline collaboration feature",
        "gate": "gate decision feature",
        "formal": "formal publication feature",
        "io": "governed io feature",
        "pilot": "pilot rollout feature",
    }
    return [mapping.get(profile, f"{title or 'feature'} coverage")]


def derive_feature_owned_code_paths(feature: dict[str, Any]) -> list[str]:
    mapping = {
        "collaboration": [
            "cli/lib/mainline_runtime.py",
            "cli/lib/reentry.py",
            "cli/lib/gate_collaboration_actions.py",
        ],
        "gate": ["cli/commands/gate/command.py"],
        "formal": [
            "cli/lib/formalization.py",
            "cli/lib/lineage.py",
            "cli/lib/admission.py",
            "cli/commands/registry/command.py",
        ],
        "io": [
            "cli/lib/managed_gateway.py",
            "cli/commands/artifact/command.py",
        ],
        "pilot": [
            "cli/lib/rollout_state.py",
            "cli/lib/pilot_chain.py",
            "cli/commands/rollout/command.py",
            "cli/commands/audit/command.py",
        ],
    }
    return mapping.get(feature_profile(feature), [])


def is_explicit_web_feature(feature: dict[str, Any]) -> bool:
    text_parts = [
        str(feature.get("title") or ""),
        str(feature.get("goal") or ""),
        str(feature.get("axis_id") or ""),
        str(feature.get("track") or ""),
    ]
    for key in ["scope", "constraints", "dependencies", "non_goals", "source_refs", "consumes", "produces"]:
        text_parts.extend(str(item) for item in ensure_list(feature.get(key)))
    for check in ensure_list(feature.get("acceptance_checks")):
        if isinstance(check, dict):
            text_parts.extend([str(check.get("scenario") or ""), str(check.get("given") or ""), str(check.get("when") or ""), str(check.get("then") or "")])
    joined = " ".join(text_parts).lower()
    latin_web_markers = ["web", "browser", "playwright", "page", "dom", "locator", "selector", "base_url", "base url", "frontend", "screen", "route", "url", "click", "form", "input field"]
    chinese_web_markers = ["页面", "浏览器", "定位器", "选择器", "前端", "路由", "按钮", "输入框", "表单", "页面跳转", "截图"]
    if any(re.search(rf"\b{re.escape(marker)}\b", joined) for marker in latin_web_markers):
        return True
    return any(marker in joined for marker in chinese_web_markers)


def derive_downstream_target_skill(feature: dict[str, Any], layers: list[str] | None = None) -> str:
    resolved_layers = layers or derive_test_layers(feature)
    if is_explicit_web_feature(feature):
        return "skill.qa.test_exec_web_e2e"
    e2e_context = " ".join([str(feature.get("title") or ""), str(feature.get("goal") or ""), " ".join(str(item) for item in ensure_list(feature.get("scope")))]).lower()
    if "e2e" in resolved_layers and any(marker in e2e_context for marker in ["browser", "playwright", "page", "dom", "locator", "selector", "ui", "页面", "浏览器", "定位器"]):
        return "skill.qa.test_exec_web_e2e"
    return "skill.qa.test_exec_cli"


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


def derive_preconditions(feature: dict[str, Any]) -> list[str]:
    preconditions = ensure_list(feature.get("dependencies"))[:3]
    if not preconditions:
        preconditions = ["selected FEAT 及其上游 source refs 可被稳定解析。"]
    profile = feature_profile(feature)
    extras = {
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
    return {
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
