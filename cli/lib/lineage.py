"""Lineage and authoritative formal reference helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError
from cli.lib.registry_store import load_registry_record, verify_eligibility


def resolve_formal_ref(workspace_root: Path, artifact_ref: str, lineage_expectation: str | None = None) -> dict[str, Any]:
    record = verify_eligibility(workspace_root, artifact_ref, lineage_expectation)
    if record.get("status") not in {"materialized", "promoted"}:
        raise CommandError("ELIGIBILITY_DENIED", "record is not published on the formal layer")
    metadata = record.get("metadata", {})
    if metadata.get("layer") not in {"formal", "materialized"}:
        raise CommandError("ELIGIBILITY_DENIED", "record is not formal")
    return record


def build_lineage_summary(workspace_root: Path, artifact_ref: str) -> list[str]:
    record = load_registry_record(workspace_root, artifact_ref)
    return [str(item) for item in record.get("lineage", []) if str(item)]
