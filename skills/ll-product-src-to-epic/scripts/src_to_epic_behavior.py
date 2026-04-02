from __future__ import annotations

from typing import Any

from src_to_epic_behavior_execution import derive_execution_runner_behavior_slices
from src_to_epic_behavior_governance import derive_governance_bridge_behavior_slices
from src_to_epic_behavior_review import derive_review_projection_behavior_slices
from src_to_epic_identity import (
    derive_capability_axes,
    is_execution_runner_package,
    is_governance_bridge_package,
    is_implementation_readiness_package,
    is_review_projection_package,
)


def _implementation_readiness_behavior_slices() -> list[dict[str, Any]]:
    return [
        {
            "id": "impl_readiness_intake",
            "name": "IMPL 主测试对象 intake 与 authority 绑定流",
            "track": "foundation",
            "goal": "冻结 IMPL 进入 implementation start 前如何作为主测试对象被 intake，并与 FEAT / TECH / ARCH / API / UI / TESTSET authority 绑定。",
            "scope": "主测试对象选择、authority ref 绑定、execution mode 选择、self-contained readiness 判定入口。",
            "product_surface": "impl readiness intake surface",
            "completed_state": "reviewer 能明确知道当前测试对象、authority refs 和执行模式。",
            "business_deliverable": "implementation readiness intake result",
            "capability_axes": ["main_test_object_priority", "authority_binding"],
            "overlay_families": [],
        },
        {
            "id": "cross_artifact_consistency_review",
            "name": "跨文档一致性与产品行为边界评审流",
            "track": "foundation",
            "goal": "冻结 IMPL 与联动 authority 之间的功能逻辑、状态、API、UI、旅程和测试可观测性检查。",
            "scope": "functional logic、state/data、user journey、UI、API、testability、migration compatibility 多维一致性评审。",
            "product_surface": "cross-artifact review report",
            "completed_state": "关键跨文档冲突、越权点和空洞被显式列为 issue，不再依赖 coder 自行推断。",
            "business_deliverable": "cross-artifact issue inventory",
            "capability_axes": ["conflict_detection", "product_behavior_boundary"],
            "overlay_families": [],
        },
        {
            "id": "counterexample_and_failure_path_simulation",
            "name": "失败路径与反例推演流",
            "track": "foundation",
            "goal": "冻结 deep mode 下的失败路径推演、counterexample 覆盖和恢复动作校验。",
            "scope": "非法输入、部分失败、恢复动作、迁移兼容、counterexample family coverage。",
            "product_surface": "failure-path simulation summary",
            "completed_state": "高风险维度至少命中一个反例场景，且恢复动作或阻断理由明确。",
            "business_deliverable": "counterexample coverage result",
            "capability_axes": ["failure_path_simulation", "counterexample_coverage"],
            "overlay_families": [],
        },
        {
            "id": "readiness_verdict_and_repair_routing",
            "name": "实施 readiness verdict 与修复路由流",
            "track": "foundation",
            "goal": "冻结 score-to-verdict、blocking/high-priority issue 和 repair_target_artifact 的输出语义。",
            "scope": "dimension score、pass/pass_with_revisions/block verdict、repair target、missing information、repair plan。",
            "product_surface": "implementation readiness report",
            "completed_state": "implementation consumer 无需回读 ADR 即可知道能否开工、哪里要修、由谁修。",
            "business_deliverable": "implementation-readiness verdict package",
            "capability_axes": ["score_to_verdict", "repair_target_routing"],
            "overlay_families": [],
        },
    ]


def _default_behavior_slices(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    axes = derive_capability_axes(package, rollout_requirement)
    derived: list[dict[str, Any]] = []
    for axis in axes:
        derived.append(
            {
                "id": str(axis.get("id") or ""),
                "name": str(axis.get("feat_axis") or axis.get("name") or ""),
                "track": "foundation",
                "goal": f"冻结 {axis.get('feat_axis') or axis.get('name')} 这一产品行为切片。",
                "scope": str(axis.get("scope") or axis.get("feat_axis") or axis.get("name") or ""),
                "product_surface": str(axis.get("feat_axis") or axis.get("name") or "产品切片"),
                "completed_state": "该切片对应的产品行为已形成可验收、可交接的业务结果。",
                "business_deliverable": str(axis.get("feat_axis") or axis.get("name") or "产品交付物"),
                "capability_axes": [str(axis.get("name") or axis.get("feat_axis") or "")],
                "overlay_families": [],
            }
        )
    return derived


def derive_product_behavior_slices(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if is_review_projection_package(package):
        return derive_review_projection_behavior_slices()
    if is_execution_runner_package(package):
        return derive_execution_runner_behavior_slices(package)
    if is_implementation_readiness_package(package):
        return _implementation_readiness_behavior_slices()
    if is_governance_bridge_package(package):
        return derive_governance_bridge_behavior_slices(package, rollout_requirement)
    return _default_behavior_slices(package, rollout_requirement)
