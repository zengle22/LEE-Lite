"""Traceability helpers for review projections."""

from __future__ import annotations


def bind_block_trace_refs(ssot_ref: str, block_sources: dict[str, list[str]]) -> dict[str, object]:
    trace_map: dict[str, list[str]] = {}
    missing_blocks: list[str] = []
    for block_id, fields in block_sources.items():
        refs = [_field_trace_ref(ssot_ref, field) for field in fields if field]
        if refs:
            trace_map[block_id] = refs
        else:
            missing_blocks.append(block_id)
    return {
        "trace_refs": trace_map,
        "status": "traceable_to_ssot" if not missing_blocks else "traceability_pending",
        "missing_blocks": missing_blocks,
    }


def bind_snapshot_field_refs(ssot_ref: str, field_paths: dict[str, str]) -> dict[str, object]:
    refs = {field_name: _field_trace_ref(ssot_ref, field_path) for field_name, field_path in field_paths.items() if field_path}
    missing_fields = [field_name for field_name, field_path in field_paths.items() if not field_path]
    return {
        "field_refs": refs,
        "status": "traceable_to_ssot" if not missing_fields else "snapshot_trace_pending",
        "missing_fields": missing_fields,
    }


def flatten_trace_refs(*groups: object) -> list[str]:
    flattened: list[str] = []
    for group in groups:
        if isinstance(group, dict):
            for value in group.values():
                if isinstance(value, list):
                    for item in value:
                        if item and item not in flattened:
                            flattened.append(item)
                elif isinstance(value, str) and value and value not in flattened:
                    flattened.append(value)
        elif isinstance(group, list):
            for item in group:
                if isinstance(item, str) and item and item not in flattened:
                    flattened.append(item)
    return flattened


def _field_trace_ref(ssot_ref: str, field_path: str) -> str:
    return f"{ssot_ref}#{field_path}"
