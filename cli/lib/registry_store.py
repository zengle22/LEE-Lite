"""File-backed registry and object helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, load_json, read_text, to_canonical_path, write_json


FORMAL_STATUSES = {"committed", "promoted", "materialized"}


def slugify(value: str) -> str:
    chars = []
    for char in value.lower():
        chars.append(char if char.isalnum() else "-")
    return "".join(chars).strip("-") or "artifact"


def registry_dir(workspace_root: Path) -> Path:
    return workspace_root / "artifacts" / "registry"


def record_path(workspace_root: Path, artifact_ref: str) -> Path:
    return registry_dir(workspace_root) / f"{slugify(artifact_ref)}.json"


def save_registry_record(workspace_root: Path, record: dict[str, Any]) -> str:
    artifact_ref = str(record["artifact_ref"])
    target = record_path(workspace_root, artifact_ref)
    write_json(target, record)
    return to_canonical_path(target, workspace_root)


def load_registry_record(workspace_root: Path, artifact_ref: str) -> dict[str, Any]:
    target = record_path(workspace_root, artifact_ref)
    if not target.exists():
        raise CommandError("REGISTRY_MISS", f"registry record not found for {artifact_ref}")
    return load_json(target)


def bind_record(
    workspace_root: Path,
    artifact_ref: str,
    managed_artifact_ref: str,
    status: str,
    trace: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    lineage: list[str] | None = None,
) -> tuple[dict[str, Any], str]:
    record = {
        "artifact_ref": artifact_ref,
        "managed_artifact_ref": managed_artifact_ref,
        "status": status,
        "trace": trace,
        "metadata": metadata or {},
        "lineage": lineage or [],
    }
    record_ref = save_registry_record(workspace_root, record)
    return record, record_ref


def verify_eligibility(workspace_root: Path, artifact_ref: str, lineage_expectation: str | None = None) -> dict[str, Any]:
    record = load_registry_record(workspace_root, artifact_ref)
    if record.get("status") not in FORMAL_STATUSES:
        raise CommandError("ELIGIBILITY_DENIED", "artifact is not in a formal status", [record.get("status", "unknown")])
    if lineage_expectation and lineage_expectation not in record.get("lineage", []):
        raise CommandError("ELIGIBILITY_DENIED", "lineage expectation not satisfied", [lineage_expectation])
    return record


def resolve_content_ref(workspace_root: Path, ref: str) -> str:
    return read_text(canonical_to_path(ref, workspace_root))

