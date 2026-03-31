"""Shared helpers for formal materialization flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.formalization_snapshot import (
    assigned_id_from_path,
    candidate_source_path,
    compliant_src_path,
    default_formal_ref,
    formal_src_output_path,
    next_src_id,
)
from cli.lib.fs import load_json, to_canonical_path, write_json
from cli.lib.registry_store import bind_record, record_path, slugify


def existing_formal_record(workspace_root: Path, formal_ref: str) -> dict[str, Any] | None:
    target = record_path(workspace_root, formal_ref)
    if not target.exists():
        return None
    return load_json(target)


def materialize_handoff(workspace_root: Path, trace: dict[str, Any], candidate: dict[str, Any]) -> dict[str, str]:
    source_path = candidate_source_path(workspace_root, candidate)
    published_ref = to_canonical_path(source_path, workspace_root)
    materialized_ssot_ref = "artifacts/active/ssot/materialized-handoff.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(candidate['artifact_ref'])}",
            "ssot_type": "HANDOFF",
            "candidate_ref": candidate["artifact_ref"],
            "published_ref": published_ref,
            "managed_artifact_ref": candidate["managed_artifact_ref"],
        },
    )
    bind_record(
        workspace_root,
        default_formal_ref("handoff"),
        published_ref,
        "materialized",
        trace,
        metadata={"candidate_ref": candidate["artifact_ref"], "materialized_ssot_ref": materialized_ssot_ref},
        lineage=[candidate["artifact_ref"]],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": "",
        "gateway_receipt_ref": "",
    }


def materialize_generic(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, str]:
    published_ref = to_canonical_path(source_path, workspace_root)
    materialized_ssot_ref = f"artifacts/active/ssot/materialized-{slugify(formal_ref)}.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(formal_ref)}",
            "ssot_type": "GENERIC",
            "formal_ref": formal_ref,
            "published_ref": published_ref,
            "materialized_by": materialized_by,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata={"target_kind": "generic", "published_ref": published_ref},
        lineage=[candidate["artifact_ref"]],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": "",
        "gateway_receipt_ref": to_canonical_path(workspace_root / materialized_ssot_ref, workspace_root),
    }


def resolve_src_target_path(workspace_root: Path, formal_ref: str, title: str) -> tuple[str, Path]:
    existing = existing_formal_record(workspace_root, formal_ref)
    if existing:
        existing_path = Path(workspace_root / str(existing.get("managed_artifact_ref", "")))
        if existing_path.exists() and compliant_src_path(existing_path, workspace_root):
            return assigned_id_from_path(existing_path) or next_src_id(workspace_root), existing_path
    assigned_id = next_src_id(workspace_root)
    return assigned_id, formal_src_output_path(workspace_root, assigned_id, title)


def ensure_publication_title(title: str, target_kind: str, ref_value: str) -> str:
    normalized = str(title or "").strip()
    ensure(normalized, "PRECONDITION_FAILED", f"{target_kind} formalization requires non-empty title: {ref_value}")
    return normalized
