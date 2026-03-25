"""Review focus extraction for review projections."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from cli.lib.fs import write_json
from cli.lib.registry_store import slugify
from cli.lib.review_projection.field_selector import authoritative_field_candidates, resolve_field_value
from cli.lib.review_projection.risk_analyzer import analyze_risk_signals


class ReviewFocusError(RuntimeError):
    """Raised when focus extraction lacks enough context."""


def build_review_focus(
    workspace_root: Path,
    ssot_ref: str,
    projection_ref: str,
    ssot_payload: dict[str, Any],
    base_blocks: list[dict[str, Any]],
    field_trace_refs: dict[str, str],
) -> dict[str, Any]:
    context = _load_review_context(ssot_payload, base_blocks, field_trace_refs)
    if not context["anchors"]:
        raise ReviewFocusError("insufficient_context")
    focus_ref = _focus_ref(ssot_ref, projection_ref)
    focus_items = _extract_focus_items(context)
    risk_items, ambiguity_items = analyze_risk_signals(context)
    result = {
        "focus_ref": focus_ref,
        "ssot_ref": ssot_ref,
        "projection_ref": projection_ref,
        "focus_items": focus_items,
        "risk_items": risk_items,
        "ambiguity_items": ambiguity_items,
        "trace_refs": _collect_trace_refs(focus_items, risk_items, ambiguity_items),
        "status": "review_guidance_visible",
    }
    write_json(workspace_root / focus_ref, result)
    return result


def build_review_focus_or_empty(
    workspace_root: Path,
    ssot_ref: str,
    projection_ref: str,
    ssot_payload: dict[str, Any],
    base_blocks: list[dict[str, Any]],
    field_trace_refs: dict[str, str],
) -> dict[str, Any]:
    try:
        return build_review_focus(workspace_root, ssot_ref, projection_ref, ssot_payload, base_blocks, field_trace_refs)
    except ReviewFocusError:
        focus_ref = _focus_ref(ssot_ref, projection_ref)
        result = {
            "focus_ref": focus_ref,
            "ssot_ref": ssot_ref,
            "projection_ref": projection_ref,
            "focus_items": [],
            "risk_items": [],
            "ambiguity_items": [],
            "trace_refs": [],
            "status": "insufficient_context",
            "reason": "insufficient_context",
        }
        write_json(workspace_root / focus_ref, result)
        return result


def _load_review_context(
    ssot_payload: dict[str, Any],
    base_blocks: list[dict[str, Any]],
    field_trace_refs: dict[str, str],
) -> dict[str, Any]:
    block_map = {block["id"]: block for block in base_blocks}
    boundary_value, _ = resolve_field_value(ssot_payload, authoritative_field_candidates("frozen_downstream_boundary"))
    open_decision_value, _ = resolve_field_value(ssot_payload, authoritative_field_candidates("open_technical_decisions"))
    return {
        "anchors": [block["id"] for block in base_blocks if block["status"] == "complete"],
        "product_summary": block_map.get("product_summary", {}).get("content", []),
        "roles": block_map.get("roles", {}).get("content", []),
        "main_flow": block_map.get("main_flow", {}).get("content", []),
        "deliverables": block_map.get("deliverables", {}).get("content", []),
        "boundary": boundary_value,
        "open_technical_decisions": open_decision_value,
        "field_trace_refs": field_trace_refs,
    }


def _extract_focus_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    focus_items = [
        _focus_item(
            "product_shape",
            "Confirm the product shape in the summary matches the intended review scope.",
            context["field_trace_refs"].get("completed_state", ""),
        ),
        _focus_item(
            "boundary_completeness",
            "Check the frozen downstream boundary and make sure no out-of-scope work leaked into this round.",
            context["field_trace_refs"].get("frozen_downstream_boundary", ""),
        ),
        _focus_item(
            "authoritative_deliverable",
            "Verify there is one authoritative deliverable and downstream inheritance still points back to Machine SSOT.",
            context["field_trace_refs"].get("authoritative_output", ""),
        ),
        _focus_item(
            "responsibility_placement",
            "Check role ownership and responsibility placement before approving the projection.",
            context["field_trace_refs"].get("open_technical_decisions", ""),
        ),
    ]
    return [item for item in focus_items if item["source_trace_refs"]]


def _focus_item(item_id: str, prompt: str, trace_ref: str) -> dict[str, Any]:
    return {
        "focus_item_ref": item_id,
        "review_prompt": prompt,
        "source_trace_refs": [trace_ref] if trace_ref else [],
    }


def _collect_trace_refs(*groups: list[dict[str, Any]]) -> list[str]:
    trace_refs: list[str] = []
    for group in groups:
        for item in group:
            for trace_ref in item["source_trace_refs"]:
                if trace_ref not in trace_refs:
                    trace_refs.append(trace_ref)
    return trace_refs


def _focus_ref(ssot_ref: str, projection_ref: str) -> str:
    key = f"{ssot_ref}|{projection_ref}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"artifacts/active/gates/projections/focus/{slugify(ssot_ref)}-{digest}.json"
