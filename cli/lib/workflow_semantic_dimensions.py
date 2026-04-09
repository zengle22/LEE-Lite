"""Shared helpers for ADR-043 semantic dimension contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_semantic_dimensions(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_semantic_dimensions(payload)
    return payload


def validate_semantic_dimensions(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("semantic dimensions payload must be an object")
    for key in ("artifact_type", "schema_version", "core_dimensions", "auxiliary_dimensions"):
        if key not in payload:
            raise ValueError(f"semantic dimensions missing `{key}`")
    core_dimensions = payload.get("core_dimensions")
    auxiliary_dimensions = payload.get("auxiliary_dimensions")
    if not isinstance(core_dimensions, list) or not core_dimensions:
        raise ValueError("semantic dimensions must include a non-empty core_dimensions list")
    if not isinstance(auxiliary_dimensions, list):
        raise ValueError("semantic dimensions must include auxiliary_dimensions list")
    for dimension in core_dimensions + auxiliary_dimensions:
        if not isinstance(dimension, dict):
            raise ValueError("each semantic dimension must be an object")
        for key in ("id", "required", "review_question"):
            if key not in dimension:
                raise ValueError(f"semantic dimension missing `{key}`")


def dimension_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_semantic_dimensions(payload)
    dimensions = list(payload["core_dimensions"]) + list(payload["auxiliary_dimensions"])
    return {str(item["id"]): item for item in dimensions}


def render_semantic_checklist_markdown(
    payload: dict[str, Any],
    *,
    heading: str = "# Output Semantic Checklist",
    intro: str | None = None,
) -> str:
    validate_semantic_dimensions(payload)
    lines = [heading, ""]
    if intro:
        lines.extend([intro, ""])
    for dimension in list(payload["core_dimensions"]) + list(payload["auxiliary_dimensions"]):
        prefix = "[required] " if bool(dimension.get("required")) else "[aux] "
        lines.append(f"- {prefix}{dimension['review_question']}")
        evidence_targets = [str(item).strip() for item in (dimension.get("evidence_targets") or []) if str(item).strip()]
        if evidence_targets:
            lines.append(f"  Evidence: {', '.join(evidence_targets)}")
    return "\n".join(lines) + "\n"
