"""Authoritative field selection for review projections."""

from __future__ import annotations

from typing import Any


_FIELD_ALIASES = {
    "completed_state": (
        "completed_state",
        "done_definition",
        "ready_state",
        "review_completed_state",
        "product_behavior_slices.completed_state",
        "epic_success_criteria",
        "success_metrics",
    ),
    "authoritative_output": (
        "authoritative_output",
        "deliverables.primary",
        "primary_deliverable",
        "output",
        "epic_freeze_ref",
        "title",
        "artifact_type",
    ),
    "frozen_downstream_boundary": (
        "frozen_downstream_boundary",
        "downstream_boundary",
        "boundary",
        "frozen_boundary",
        "upstream_and_downstream",
        "decomposition_rules",
        "constraints_and_dependencies",
    ),
    "open_technical_decisions": (
        "open_technical_decisions",
        "technical_decisions.open",
        "open_questions",
        "known_unknowns",
        "constraints_and_dependencies",
        "constraint_groups.items",
    ),
}


def select_authoritative_fields(ssot_payload: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    field_paths: dict[str, str] = {}
    missing_fields: list[str] = []
    for field_name, candidates in _FIELD_ALIASES.items():
        value, resolved_path = _resolve_alias(ssot_payload, candidates)
        if resolved_path:
            fields[field_name] = value
            field_paths[field_name] = resolved_path
        else:
            missing_fields.append(field_name)
    return {"fields": fields, "field_paths": field_paths, "missing_fields": missing_fields}


def resolve_field_value(ssot_payload: dict[str, Any], candidates: tuple[str, ...]) -> tuple[Any, str]:
    for candidate in candidates:
        value = lookup_path(ssot_payload, candidate)
        if has_value(value):
            return value, candidate
    return None, ""


def authoritative_field_candidates(field_name: str) -> tuple[str, ...]:
    return _FIELD_ALIASES[field_name]


def lookup_path(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
            continue
        if isinstance(current, list):
            collected: list[Any] = []
            for item in current:
                if isinstance(item, dict) and part in item:
                    value = item[part]
                    if isinstance(value, list):
                        collected.extend(value)
                    else:
                        collected.append(value)
            if not collected:
                return None
            current = collected
            continue
        return None
    return current


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _resolve_alias(ssot_payload: dict[str, Any], candidates: tuple[str, ...]) -> tuple[Any, str]:
    return resolve_field_value(ssot_payload, candidates)
