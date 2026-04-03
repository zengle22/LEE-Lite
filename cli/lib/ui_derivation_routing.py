"""Routing helpers for FEAT -> Prototype/UI derivation."""

from __future__ import annotations

from typing import Any


LOW = "low"
MEDIUM = "medium"
HIGH = "high"

DIRECT_UI_ALLOWED = "direct_ui_allowed"
PROTOTYPE_OPTIONAL = "prototype_optional"
PROTOTYPE_REQUIRED = "prototype_required"


def _tokens(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(str(item).lower() for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {value}" for key, value in value.items()).lower()
    return str(value or "").lower()


def _has_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def evaluate_dimensions(feature: dict[str, Any]) -> dict[str, bool]:
    text = " ".join(
        [
            _tokens(feature.get("title")),
            _tokens(feature.get("goal")),
            _tokens(feature.get("scope")),
            _tokens(feature.get("constraints")),
            _tokens(feature.get("acceptance_checks")),
            _tokens(feature.get("ui_units")),
            _tokens(feature.get("ui_api_touchpoints")),
        ]
    )
    page_count = len(feature.get("ui_units") or [])
    return {
        "multi_step_flow": page_count > 1 or _has_any(text, ["step", "多步", "journey", "wizard", "流程"]),
        "workflow_branching": _has_any(text, ["branch", "retry", "skip", "回退", "重试", "分支", "fallback"]),
        "async_or_stateful_behavior": _has_any(
            text,
            ["loading", "error", "success", "async", "状态", "state", "poll", "submit", "连接", "sync"],
        ),
        "user_decision_sensitivity": _has_any(
            text,
            ["recommend", "decision", "choice", "approval", "confirm", "建议", "确认", "选择"],
        ),
        "cta_or_information_hierarchy_risk": _has_any(
            text,
            ["cta", "priority", "hierarchy", "banner", "card", "主按钮", "优先级", "信息层级"],
        ),
    }


def route_ui_derivation(feature: dict[str, Any]) -> dict[str, Any]:
    explicit = str(feature.get("ui_complexity") or "").strip().lower()
    dimensions = evaluate_dimensions(feature)
    score = sum(1 for value in dimensions.values() if value)
    if explicit in {LOW, MEDIUM, HIGH}:
        level = explicit
    elif (
        dimensions["multi_step_flow"]
        and dimensions["workflow_branching"]
        and dimensions["async_or_stateful_behavior"]
    ):
        level = HIGH
    elif score >= 4:
        level = HIGH
    elif score >= 2:
        level = MEDIUM
    else:
        level = LOW
    route = {
        LOW: DIRECT_UI_ALLOWED,
        MEDIUM: PROTOTYPE_OPTIONAL,
        HIGH: PROTOTYPE_REQUIRED,
    }[level]
    reasons = [name for name, value in dimensions.items() if value] or ["simple_single_surface_change"]
    return {
        "ui_complexity_level": level,
        "route_decision": route,
        "routing_rationale": ", ".join(reasons),
        "evaluated_dimensions": dimensions,
        "prototype_bypass_rationale": None,
    }


def validate_route_decision(route: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if route.get("ui_complexity_level") not in {LOW, MEDIUM, HIGH}:
        errors.append("ui_complexity_level must be low, medium, or high")
    if route.get("route_decision") not in {DIRECT_UI_ALLOWED, PROTOTYPE_OPTIONAL, PROTOTYPE_REQUIRED}:
        errors.append("route_decision must be direct_ui_allowed, prototype_optional, or prototype_required")
    dims = route.get("evaluated_dimensions")
    if not isinstance(dims, dict):
        errors.append("evaluated_dimensions must be an object")
    else:
        for key in [
            "multi_step_flow",
            "workflow_branching",
            "async_or_stateful_behavior",
            "user_decision_sensitivity",
            "cta_or_information_hierarchy_risk",
        ]:
            if key not in dims:
                errors.append(f"evaluated_dimensions missing key: {key}")
    return errors
