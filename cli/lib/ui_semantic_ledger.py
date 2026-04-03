"""Semantic source ledger helpers for UI spec derivation."""

from __future__ import annotations

from typing import Any


HIGH_RISK_AREAS = {
    "canonical_data_source",
    "state_semantics",
    "api_mapping",
    "error_mapping",
    "completion_semantics",
    "blocker_behavior",
    "non_blocker_behavior",
}


def build_ui_semantic_ledger(
    *,
    from_prototype: list[dict[str, Any]],
    from_feat: list[dict[str, Any]],
    from_other_authority: list[dict[str, Any]] | None = None,
    inferred_by_ai: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "ui_spec_semantic_sources": {
            "from_prototype": from_prototype,
            "from_feat": from_feat,
            "from_other_authority": from_other_authority or [],
            "inferred_by_ai": inferred_by_ai or [],
        }
    }


def validate_ui_semantic_ledger(ledger: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    root = ledger.get("ui_spec_semantic_sources")
    if not isinstance(root, dict):
        return ["ui semantic source ledger must include ui_spec_semantic_sources"]
    for key in ["from_prototype", "from_feat", "from_other_authority", "inferred_by_ai"]:
        if key not in root or not isinstance(root.get(key), list):
            errors.append(f"ui semantic source ledger missing list: {key}")
    for entry in root.get("inferred_by_ai", []):
        area = str(entry.get("semantic_area") or "").strip()
        if not area:
            errors.append("inferred_by_ai entry missing semantic_area")
        if not str(entry.get("rationale") or "").strip():
            errors.append(f"inferred_by_ai entry missing rationale: {area or 'unknown'}")
        if entry.get("confidence") not in {"low", "medium", "high"}:
            errors.append(f"inferred_by_ai entry has invalid confidence: {area or 'unknown'}")
        if "requires_explicit_review" not in entry:
            errors.append(f"inferred_by_ai entry missing requires_explicit_review: {area or 'unknown'}")
        if area in HIGH_RISK_AREAS and not entry.get("requires_explicit_review"):
            errors.append(f"high-risk inferred_by_ai entry must require explicit review: {area}")
    return errors
