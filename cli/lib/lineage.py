"""Lineage resolution for candidate and formal objects."""

from __future__ import annotations

from typing import Any

from cli.lib.registry_store import artifact_layer, list_registry_records, resolve_registry_record


def resolve_lineage(workspace_root, ref_value: str) -> dict[str, Any]:
    record = resolve_registry_record(workspace_root, ref_value)
    downstream: list[str] = []
    for item in list_registry_records(workspace_root):
        if record["artifact_ref"] in item.get("lineage", []):
            downstream.append(str(item["artifact_ref"]))
    return {
        "authoritative_ref": record["artifact_ref"],
        "resolved_formal_ref": record["artifact_ref"] if artifact_layer(record) == "formal" else "",
        "layer": artifact_layer(record),
        "upstream_refs": list(record.get("lineage", [])),
        "downstream_refs": downstream,
        "managed_artifact_ref": record["managed_artifact_ref"],
    }
