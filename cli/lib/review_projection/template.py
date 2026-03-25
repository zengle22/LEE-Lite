"""Stable review template blocks for human review projections."""

from __future__ import annotations

from typing import Any

from cli.lib.review_projection.field_selector import lookup_path


DEFAULT_TEMPLATE_VERSION = "v1"

_BLOCK_SPECS = (
    {
        "id": "product_summary",
        "title": "Product Summary",
        "bindings": (
            "product_summary",
            "summary",
            "overview",
            "product_shape",
            "problem_statement",
            "epic_intent",
            "business_goal",
            "product_positioning",
        ),
        "fallback": "Product summary is not yet frozen in Machine SSOT.",
    },
    {
        "id": "roles",
        "title": "Roles",
        "bindings": (
            "roles",
            "actors",
            "personas",
            "stakeholders",
            "participants",
            "actors_and_roles.role",
            "actors_and_roles",
        ),
        "fallback": "Roles are not yet frozen in Machine SSOT.",
    },
    {
        "id": "main_flow",
        "title": "Main Flow",
        "bindings": (
            "main_flow",
            "user_flow",
            "flow",
            "journey",
            "review_flow",
            "product_behavior_slices.product_surface",
            "product_behavior_slices.goal",
            "feat_axis_mapping.product_behavior_slice",
        ),
        "fallback": "Main flow is not yet frozen in Machine SSOT.",
    },
    {
        "id": "deliverables",
        "title": "Deliverables",
        "bindings": (
            "deliverables",
            "key_deliverables",
            "outputs",
            "authoritative_output",
            "product_behavior_slices.business_deliverable",
            "product_behavior_slices.name",
        ),
        "fallback": "Deliverables are not yet frozen in Machine SSOT.",
    },
)


def load_projection_template(template_version: str | None) -> dict[str, Any] | None:
    version = str(template_version or DEFAULT_TEMPLATE_VERSION).strip() or DEFAULT_TEMPLATE_VERSION
    if version != DEFAULT_TEMPLATE_VERSION:
        return None
    return {"version": version, "blocks": [dict(spec) for spec in _BLOCK_SPECS]}


def build_review_blocks(ssot_payload: dict[str, Any], template: dict[str, Any]) -> list[dict[str, Any]]:
    return [_build_block(ssot_payload, spec) for spec in template["blocks"]]


def _build_block(ssot_payload: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    content, source_field = _resolve_block_content(ssot_payload, spec["bindings"])
    complete = bool(source_field)
    return {
        "id": spec["id"],
        "title": spec["title"],
        "content": content or [str(spec["fallback"])],
        "status": "complete" if complete else "missing_source",
        "source_fields": [source_field] if complete else [],
    }


def _resolve_block_content(ssot_payload: dict[str, Any], bindings: tuple[str, ...]) -> tuple[list[str], str]:
    for binding in bindings:
        value = lookup_path(ssot_payload, binding)
        content = _normalize_content(value)
        if content:
            return content, binding
    return [], ""


def _normalize_content(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(_normalize_content(item))
        return items
    if isinstance(value, dict):
        if "role" in value and "responsibility" in value:
            role = str(value["role"]).strip()
            responsibility = str(value["responsibility"]).strip()
            if role and responsibility:
                return [f"{role}: {responsibility}"]
        items: list[str] = []
        for key, item in value.items():
            normalized = _normalize_content(item)
            if normalized:
                if len(normalized) == 1:
                    items.append(f"{key}: {normalized[0]}")
                else:
                    items.append(f"{key}:")
                    items.extend(f"- {entry}" for entry in normalized)
        return items
    return [str(value)]
