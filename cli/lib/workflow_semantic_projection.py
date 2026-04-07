"""Projection helpers for ADR-043 Narrative / Checklist / Diff views."""

from __future__ import annotations

from typing import Any


def checklist_view_from_coverage(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "status": item["status"],
            "required": item["required"],
            "review_anchor": item["review_anchor"],
            "evidence_refs": list(item.get("evidence_refs") or []),
        }
        for item in (coverage.get("dimensions") or [])
    ]


def build_review_views(
    *,
    narrative: list[str],
    coverage: dict[str, Any],
    diff: dict[str, Any],
) -> dict[str, Any]:
    return {
        "narrative": [str(item).strip() for item in narrative if str(item).strip()],
        "checklist": checklist_view_from_coverage(coverage),
        "diff": diff,
    }
