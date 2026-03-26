from __future__ import annotations

from typing import Any

from src_to_epic_behavior_execution import derive_execution_runner_behavior_slices
from src_to_epic_behavior_governance import derive_governance_bridge_behavior_slices
from src_to_epic_behavior_review import derive_review_projection_behavior_slices
from src_to_epic_identity import derive_capability_axes, is_execution_runner_package, is_governance_bridge_package, is_review_projection_package


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
    if is_governance_bridge_package(package):
        return derive_governance_bridge_behavior_slices(package, rollout_requirement)
    return _default_behavior_slices(package, rollout_requirement)
