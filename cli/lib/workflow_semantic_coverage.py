"""Coverage builders for ADR-043 semantic contracts."""

from __future__ import annotations

from typing import Any


FAIL_STATUSES = {"missing", "placeholder", "conflict", "partial"}


def build_dimension_result(
    *,
    dimension: dict[str, Any],
    status: str,
    evidence_refs: list[str] | None = None,
    notes: list[str] | None = None,
    l3_judgment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "id": str(dimension["id"]),
        "required": bool(dimension.get("required")),
        "status": status,
        "review_anchor": str(dimension.get("review_question") or ""),
        "evidence_refs": [str(item).strip() for item in (evidence_refs or []) if str(item).strip()],
        "notes": [str(item).strip() for item in (notes or []) if str(item).strip()],
    }
    if l3_judgment:
        payload["l3_judgment"] = l3_judgment
    return payload


def build_semantic_coverage(
    dimensions: dict[str, Any],
    statuses: dict[str, str],
    *,
    evidence: dict[str, list[str]] | None = None,
    notes: dict[str, list[str]] | None = None,
    l3_judgments: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    open_gaps: list[str] = []
    semantic_pass = True
    for dimension in list(dimensions["core_dimensions"]) + list(dimensions["auxiliary_dimensions"]):
        dimension_id = str(dimension["id"])
        result = build_dimension_result(
            dimension=dimension,
            status=str(statuses.get(dimension_id) or "missing"),
            evidence_refs=(evidence or {}).get(dimension_id),
            notes=(notes or {}).get(dimension_id),
            l3_judgment=(l3_judgments or {}).get(dimension_id),
        )
        items.append(result)
        if result["required"] and result["status"] in FAIL_STATUSES:
            semantic_pass = False
            open_gaps.append(dimension_id)
    return {
        "artifact_type": str(dimensions["artifact_type"]),
        "schema_version": str(dimensions["schema_version"]),
        "dimensions": items,
        "semantic_pass": semantic_pass,
        "open_semantic_gaps": open_gaps,
    }
