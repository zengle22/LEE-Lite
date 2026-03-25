"""Authoritative snapshot rendering for review projections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.fs import write_json
from cli.lib.registry_store import slugify
from cli.lib.review_projection.field_selector import select_authoritative_fields
from cli.lib.review_projection.traceability import bind_snapshot_field_refs


class SnapshotError(RuntimeError):
    """Raised when authoritative snapshot extraction cannot satisfy required fields."""


def build_authoritative_snapshot(
    workspace_root: Path,
    ssot_ref: str,
    projection_ref: str | None,
    ssot_payload: dict[str, Any],
) -> dict[str, Any]:
    selection = select_authoritative_fields(ssot_payload)
    if selection["missing_fields"]:
        raise SnapshotError("authoritative_field_missing")
    snapshot_ref = _snapshot_ref(ssot_ref)
    traceability = bind_snapshot_field_refs(ssot_ref, selection["field_paths"])
    result = {
        "snapshot_ref": snapshot_ref,
        "projection_ref": projection_ref or "",
        "completed_state": _as_lines(selection["fields"]["completed_state"]),
        "authoritative_output": _as_lines(selection["fields"]["authoritative_output"]),
        "frozen_downstream_boundary": _as_lines(selection["fields"]["frozen_downstream_boundary"]),
        "open_technical_decisions": _as_lines(selection["fields"]["open_technical_decisions"]),
        "field_refs": traceability["field_refs"],
        "traceability_status": traceability["status"],
        "block": _snapshot_block(selection["fields"], traceability["field_refs"], "complete"),
    }
    write_json(workspace_root / snapshot_ref, result)
    return result


def build_authoritative_snapshot_or_flag(
    workspace_root: Path,
    ssot_ref: str,
    projection_ref: str | None,
    ssot_payload: dict[str, Any],
) -> dict[str, Any]:
    selection = select_authoritative_fields(ssot_payload)
    if selection["missing_fields"]:
        snapshot_ref = _snapshot_ref(ssot_ref)
        result = {
            "snapshot_ref": snapshot_ref,
            "projection_ref": projection_ref or "",
            "completed_state": [],
            "authoritative_output": [],
            "frozen_downstream_boundary": [],
            "open_technical_decisions": [],
            "field_refs": {},
            "missing_fields": selection["missing_fields"],
            "traceability_status": "snapshot_trace_pending",
            "block": {
                "id": "authoritative_snapshot",
                "title": "Authoritative Snapshot",
                "content": [
                    "Authoritative constraints are incomplete; inspect Machine SSOT directly before approving.",
                    f"Missing fields: {', '.join(selection['missing_fields'])}",
                ],
                "status": "constraints_missing",
                "source_trace_refs": [],
            },
        }
        write_json(workspace_root / snapshot_ref, result)
        return result
    return build_authoritative_snapshot(workspace_root, ssot_ref, projection_ref, ssot_payload)


def _snapshot_ref(ssot_ref: str) -> str:
    return f"artifacts/active/gates/projections/snapshots/{slugify(ssot_ref)}.json"


def _snapshot_block(fields: dict[str, Any], field_refs: dict[str, str], status: str) -> dict[str, Any]:
    content = [
        f"Completed state: {_line(fields['completed_state'])}",
        f"Authoritative output: {_line(fields['authoritative_output'])}",
        f"Frozen downstream boundary: {_line(fields['frozen_downstream_boundary'])}",
        f"Open technical decisions: {_line(fields['open_technical_decisions'])}",
    ]
    return {
        "id": "authoritative_snapshot",
        "title": "Authoritative Snapshot",
        "content": content,
        "status": status,
        "source_trace_refs": [ref for ref in field_refs.values() if ref],
    }


def _line(value: Any) -> str:
    lines = _as_lines(value)
    return "; ".join(lines) if lines else "not available"


def _as_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, dict):
        return [f"{key}: {item}" for key, item in value.items()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []
