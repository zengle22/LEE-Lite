#!/usr/bin/env python3
"""
Deterministic derivation helpers for feat-to-testset.
"""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import (
    derive_test_set_id,
    derive_test_set_ref,
    ensure_list,
    slugify,
    unique_strings,
)


def governing_adrs(feature: dict[str, Any], package_json: dict[str, Any]) -> list[str]:
    refs = ensure_list(feature.get("source_refs")) + ensure_list(package_json.get("source_refs"))
    return unique_strings([ref for ref in refs if ref.startswith("ADR-")])


def derive_priority(feature: dict[str, Any]) -> str:
    track = str(feature.get("track") or "").lower()
    text = " ".join(
        ensure_list(feature.get("scope"))
        + ensure_list(feature.get("constraints"))
        + [str(feature.get("title") or "")]
    ).lower()
    if "adoption" in track or "e2e" in track or "pilot" in text:
        return "P1"
    return "P0"


def derive_test_layers(feature: dict[str, Any]) -> list[str]:
    layers = ["integration"]
    track = str(feature.get("track") or "").lower()
    axis = str(feature.get("axis_id") or "").lower()
    joined_text = " ".join(ensure_list(feature.get("scope")) + [axis, track]).lower()
    if any(marker in joined_text for marker in ["e2e", "pilot", "ui", "cross skill", "cross-skill"]):
        layers.append("e2e")
    return layers


def derive_environment_assumptions(feature: dict[str, Any], layers: list[str]) -> list[str]:
    assumptions = [
        "需要可解析 selected FEAT 所依赖的集成环境与上游 artifact lineage。",
        "需要能读取并追踪 FEAT、EPIC、SRC 与 governing ADR 引用。",
        "需要保留 execution evidence 与 supervision evidence 所要求的最小审计链。",
    ]
    if "e2e" in layers:
        assumptions.append("若启用 e2e 层，必须具备可重复执行的 UI 或跨服务集成上下文。")
    if ensure_list(feature.get("dependencies")):
        assumptions.append("依赖服务或上游能力应以可观测、可判定的方式处于可用状态。")
    return assumptions


def derive_required_environment_inputs(feature: dict[str, Any], layers: list[str]) -> dict[str, list[str]]:
    scope_text = " ".join(ensure_list(feature.get("scope"))).lower()
    return {
        "environment": unique_strings(
            [
                "可运行所选 FEAT 的集成环境",
                "可解析 source_refs 的受治理 workspace 上下文",
            ]
            + (["可重复的端到端验证环境"] if "e2e" in layers else [])
        ),
        "data": [
            "覆盖 FEAT acceptance checks 所需的最小测试数据或 fixtures",
            "可重建 analysis/strategy trace 的输入样本",
        ],
        "services": unique_strings(
            [
                "selected FEAT 所依赖的集成服务或协作 consumer",
            ]
            + (["跨 skill pilot 链路涉及的 producer / consumer / gate consumer"] if "pilot" in scope_text or "cross skill" in scope_text else [])
        ),
        "access": [
            "读取 FEAT candidate / freeze lineage 所需权限",
            "执行 QA evidence 采集与落盘所需权限",
        ],
        "feature_flags": [
            "selected FEAT 涉及的 gated rollout、cutover 或 guarded branch 开关",
        ],
        "ui_or_integration_context": [
            "驱动 FEAT acceptance checks 的 UI 路径或 integration context",
        ],
    }


def derive_coverage_exclusions(feature: dict[str, Any]) -> list[str]:
    exclusions = ensure_list(feature.get("non_goals"))[:3]
    if not exclusions:
        exclusions = [
            "不覆盖 selected FEAT 之外的相邻 FEAT 语义。",
            "不把本 TESTSET 扩展为 TASK、TECH 或 runner-level 实现细节。",
        ]
    return exclusions


def derive_test_units(feature: dict[str, Any]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    test_set_id = derive_test_set_id(feat_ref)
    priority = derive_priority(feature)
    units: list[dict[str, Any]] = []
    for index, check in enumerate(feature.get("acceptance_checks") or [], start=1):
        check_id = str(check.get("id") or f"{feat_ref}-AC-{index:02d}")
        scenario = str(check.get("scenario") or f"Acceptance check {index}")
        units.append(
            {
                "unit_ref": f"{test_set_id}-U{index:02d}",
                "acceptance_ref": check_id,
                "title": scenario,
                "priority": priority,
                "focus": unique_strings(
                    [
                        scenario,
                        str(check.get("then") or "").strip(),
                    ]
                ),
                "suggested_layers": derive_test_layers(feature),
                "evidence_expectations": [
                    "保留与 acceptance 对应的执行结果证据。",
                    "失败时提供最小可审计上下文。",
                ],
            }
        )
    return units


def derive_acceptance_traceability(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "acceptance_ref": unit["acceptance_ref"],
            "unit_refs": [unit["unit_ref"]],
        }
        for unit in units
    ]


def derive_risk_focus(feature: dict[str, Any]) -> list[str]:
    focus = ensure_list(feature.get("constraints"))[:3] + ensure_list(feature.get("dependencies"))[:2]
    if not focus:
        focus = ["保持 FEAT acceptance、traceability 与 evidence closure 一致。"]
    return unique_strings(focus)


def derive_preconditions(feature: dict[str, Any]) -> list[str]:
    preconditions = ensure_list(feature.get("dependencies"))[:3]
    if not preconditions:
        preconditions = ["selected FEAT 及其上游 source refs 可被稳定解析。"]
    return unique_strings(preconditions)


def derive_pass_criteria(feature: dict[str, Any]) -> list[str]:
    criteria = [
        "每条 acceptance check 都有至少一个可执行测试单元映射。",
        "TESTSET 不越界覆盖相邻 FEAT 或新需求。",
        "candidate package 在外置 approval 前保持 machine-readable traceability 与 gate subject identity。",
    ]
    if derive_priority(feature) == "P1":
        criteria.append("高风险或 adoption/E2E 路径需要明确的环境、数据与 pilot execution 前提。")
    return criteria


def derive_evidence_required(feature: dict[str, Any], layers: list[str]) -> list[str]:
    evidence = [
        "analysis 与 strategy 形成过程的 execution evidence",
        "supervisor 对 TESTSET 与 traceability 的 review evidence",
        "candidate package 的 machine-readable gate subject records",
    ]
    if "e2e" in layers:
        evidence.append("若进入 e2e 层，需补充 pilot 链路或 UI/integration context 的执行前提证据")
    return evidence


def derive_analysis_markdown(
    feature: dict[str, Any],
    package_json: dict[str, Any],
    derived_slug: str,
) -> str:
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
                ]
            ),
            "## Boundary Analysis\n\n"
            + "\n".join([f"- {item}" for item in ensure_list(feature.get("scope"))])
            + "\n\n## Non-Goals\n\n"
            + "\n".join([f"- {item}" for item in ensure_list(feature.get("non_goals")) or ["- 未声明额外 non-goals，按 FEAT 现有边界执行。"]]),
            "## Constraint and Risk Intake\n\n"
            + "\n".join([f"- {item}" for item in derive_risk_focus(feature)]),
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
        "priority": derive_priority(feature),
        "test_layers": layers,
        "risk_focus": derive_risk_focus(feature),
        "environment_assumptions": derive_environment_assumptions(feature, layers),
        "coverage_exclusions": derive_coverage_exclusions(feature),
        "test_units": units,
        "acceptance_traceability": derive_acceptance_traceability(units),
        "governing_adrs": governing_adrs(feature, package_json),
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
            "related_refs": [
                "test-set-review-report.json",
                "test-set-acceptance-report.json",
                "test-set-bundle.json",
            ],
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
        "risk_focus": derive_risk_focus(feature),
        "preconditions": derive_preconditions(feature),
        "environment_assumptions": derive_environment_assumptions(feature, layers),
        "test_layers": layers,
        "test_units": units,
        "coverage_exclusions": derive_coverage_exclusions(feature),
        "pass_criteria": derive_pass_criteria(feature),
        "evidence_required": derive_evidence_required(feature, layers),
        "acceptance_traceability": derive_acceptance_traceability(units),
        "source_refs": unique_strings(
            [f"product.epic-to-feat::{package_json.get('workflow_run_id')}", feat_ref]
            + ensure_list(feature.get("source_refs"))
            + ensure_list(package_json.get("source_refs"))
        ),
        "governing_adrs": governing_adrs(feature, package_json),
        "status": "draft",
    }
