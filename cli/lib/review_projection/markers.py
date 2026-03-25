"""Derived-only marker injection for review projections."""

from __future__ import annotations

from typing import Any

from cli.lib.review_projection.traceability import bind_block_trace_refs, bind_snapshot_field_refs, flatten_trace_refs


class ProjectionMarkerError(RuntimeError):
    """Raised when projection markers cannot satisfy the frozen contract."""


def attach_projection_markers(
    ssot_ref: str,
    template_version: str,
    projection_ref: str,
    block_sources: dict[str, list[str]],
    snapshot_field_paths: dict[str, str],
    prompt_trace_refs: list[str],
) -> dict[str, Any]:
    markers = {
        "derived_only": True,
        "non_authoritative": True,
        "non_inheritable": True,
        "template_version": template_version,
        "source_ssot_ref": ssot_ref,
        "projection_ref": projection_ref,
    }
    if not all(markers[name] for name in ("derived_only", "non_authoritative", "non_inheritable")):
        raise ProjectionMarkerError("marker_missing")
    block_traceability = bind_block_trace_refs(ssot_ref, block_sources)
    snapshot_traceability = _normalize_snapshot_traceability(ssot_ref, snapshot_field_paths)
    trace_refs = flatten_trace_refs(
        block_traceability["trace_refs"],
        snapshot_traceability["field_refs"],
        prompt_trace_refs,
    )
    status = "review_visible"
    if block_traceability["status"] != "traceable_to_ssot" or snapshot_traceability["status"] != "traceable_to_ssot":
        status = "traceability_pending"
    return {
        "derived_markers": markers,
        "trace_refs": trace_refs,
        "block_trace_refs": block_traceability["trace_refs"],
        "snapshot_field_refs": snapshot_traceability["field_refs"],
        "status": status,
        "traceability_notes": {
            "missing_blocks": block_traceability["missing_blocks"],
            "missing_snapshot_fields": snapshot_traceability["missing_fields"],
        },
    }


def _normalize_snapshot_traceability(ssot_ref: str, snapshot_field_paths: dict[str, str]) -> dict[str, Any]:
    if any("#" in value for value in snapshot_field_paths.values() if value):
        field_refs = {field_name: value for field_name, value in snapshot_field_paths.items() if value}
        missing_fields = [field_name for field_name, value in snapshot_field_paths.items() if not value]
        return {
            "field_refs": field_refs,
            "status": "traceable_to_ssot" if not missing_fields else "snapshot_trace_pending",
            "missing_fields": missing_fields,
        }
    return bind_snapshot_field_refs(ssot_ref, snapshot_field_paths)
