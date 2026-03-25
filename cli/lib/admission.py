"""Admission checks for downstream consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError
from cli.lib.lineage import resolve_formal_ref


def validate_admission(
    workspace_root: Path,
    artifact_ref: str,
    consumer_ref: str,
    lineage_expectation: str | None = None,
) -> dict[str, Any]:
    record = resolve_formal_ref(workspace_root, artifact_ref, lineage_expectation)
    return {
        "consumer_ref": consumer_ref,
        "artifact_ref": artifact_ref,
        "managed_artifact_ref": record["managed_artifact_ref"],
        "lineage_summary": record.get("lineage", []),
        "admission_result": "allow",
    }
