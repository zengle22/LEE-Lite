"""FRZ registry helpers — register, list, get, and update FRZ package records.

Truth source: Plan 07-02 (FRZ-03, EXTR-03).
Provides YAML-backed persistence for FRZ lifecycle records with revision
chain tracking and MSC validation status.
"""

from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import CommandError
from cli.lib.fs import ensure_parent, read_text, write_text


FRZ_ID_PATTERN = re.compile(r"^FRZ-\d{3,}$")


def registry_path(workspace_root: Path) -> Path:
    """Return the path to the FRZ registry YAML file."""
    return workspace_root / "ssot" / "registry" / "frz-registry.yaml"


def _load_registry(path: Path) -> list[dict[str, Any]]:
    """Read YAML file and return list of FRZ records.

    Returns an empty list if the file does not exist or contains no data.
    """
    if not path.exists():
        return []
    text = read_text(path)
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return []
    return data.get("frz_registry", [])


def _save_registry(path: Path, records: list[dict[str, Any]]) -> None:
    """Write records to YAML using atomic write (temp file + os.replace)."""
    ensure_parent(path)
    content = yaml.dump(
        {"frz_registry": records},
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    dir_name = path.parent
    fd, temp_path = tempfile.mkstemp(dir=str(dir_name), suffix=".yaml.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_path, str(path))
    except BaseException:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def register_frz(
    workspace_root: Path,
    frz_id: str,
    msc_report: dict[str, Any],
    package_ref: str,
    metadata: dict[str, Any] | None = None,
    previous_frz: str | None = None,
    revision_type: str = "new",
    reason: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Register a new FRZ package in the registry.

    Args:
        workspace_root: Root directory of the workspace.
        frz_id: FRZ identifier (must match FRZ-xxx pattern).
        msc_report: MSC validation report containing at least 'msc_valid'.
        package_ref: Reference to the FRZ package location.
        metadata: Optional key-value metadata dict.
        previous_frz: Previous FRZ ID for revision chains (optional).
        revision_type: Type of revision ("new", "revise", etc.).
        reason: Reason for revision (required when revising).

    Returns:
        Tuple of (record dict, frz_id).

    Raises:
        CommandError: INVALID_REQUEST on bad format or duplicate ID.
    """
    if not FRZ_ID_PATTERN.match(frz_id):
        raise CommandError(
            "INVALID_REQUEST",
            f"Invalid FRZ ID format: {frz_id}. Must match FRZ-xxx",
        )

    path = registry_path(workspace_root)
    records = _load_registry(path)

    for rec in records:
        if rec["frz_id"] == frz_id:
            raise CommandError(
                "INVALID_REQUEST", f"FRZ ID already registered: {frz_id}"
            )

    record: dict[str, Any] = {
        "frz_id": frz_id,
        "status": "frozen",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_ref": package_ref,
        "msc_valid": msc_report.get("msc_valid", False),
        "version": "1.0",
        "revision_type": revision_type,
        "metadata": metadata or {},
    }

    if previous_frz is not None:
        record["previous_frz_ref"] = previous_frz
    if reason is not None:
        record["revision_reason"] = reason

    records.append(record)
    _save_registry(path, records)
    return record, frz_id


def list_frz(
    workspace_root: Path, status: str | None = None
) -> list[dict[str, Any]]:
    """List FRZ records, optionally filtered by status.

    Args:
        workspace_root: Root directory of the workspace.
        status: Filter by exact status match (None = all).

    Returns:
        List of matching FRZ record dicts.
    """
    path = registry_path(workspace_root)
    records = _load_registry(path)
    if status is None:
        return records
    return [rec for rec in records if rec.get("status") == status]


def get_frz(workspace_root: Path, frz_id: str) -> dict[str, Any] | None:
    """Get a single FRZ record by ID.

    Args:
        workspace_root: Root directory of the workspace.
        frz_id: FRZ identifier to look up.

    Returns:
        The record dict if found, None otherwise.
    """
    path = registry_path(workspace_root)
    records = _load_registry(path)
    for rec in records:
        if rec["frz_id"] == frz_id:
            return rec
    return None


def update_frz_status(
    workspace_root: Path, frz_id: str, new_status: str
) -> dict[str, Any]:
    """Update the status of an existing FRZ record.

    Args:
        workspace_root: Root directory of the workspace.
        frz_id: FRZ identifier to update.
        new_status: New status value.

    Returns:
        The updated record dict.

    Raises:
        CommandError: REGISTRY_MISS if FRZ not found.
    """
    path = registry_path(workspace_root)
    records = _load_registry(path)

    for i, rec in enumerate(records):
        if rec["frz_id"] == frz_id:
            records[i]["status"] = new_status
            _save_registry(path, records)
            return records[i]

    raise CommandError(
        "REGISTRY_MISS", f"FRZ not found: {frz_id}"
    )
