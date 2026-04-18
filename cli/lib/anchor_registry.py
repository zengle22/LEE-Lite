"""Anchor ID registry — register, resolve, and list anchor references.

Truth source: Plan 07-02 (FRZ-03, EXTR-03).
Anchor IDs (PREFIX-NNN format) are registered with an FRZ reference and
projection path, enabling projection-invariant traceability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import CommandError
from cli.lib.fs import ensure_parent


ANCHOR_ID_PATTERN = re.compile(r"^[A-Z]{2,5}-\d{3,}$")
VALID_PROJECTION_PATHS = {"SRC", "EPIC", "FEAT", "TECH", "UI", "TEST", "IMPL"}


@dataclass(frozen=True)
class AnchorEntry:
    """Frozen record representing a registered anchor."""

    anchor_id: str
    frz_ref: str
    projection_path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str | None = None


class AnchorRegistry:
    """YAML-backed anchor ID registry.

    Args:
        workspace_root: Root directory of the workspace. Registry file is
            stored at ssot/registry/anchor_registry.yaml.
    """

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.registry_path = (
            workspace_root / "ssot" / "registry" / "anchor_registry.yaml"
        )

    # ------------------------------------------------------------------
    # Internal persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> list[dict[str, Any]]:
        """Read YAML file and return list of anchor records.

        Returns an empty list if the file does not exist.
        """
        if not self.registry_path.exists():
            return []
        text = self.registry_path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            return []
        return data.get("anchor_registry", [])

    def _save(self, records: list[dict[str, Any]]) -> None:
        """Write records to YAML under key 'anchor_registry'."""
        ensure_parent(self.registry_path)
        content = yaml.dump(
            {"anchor_registry": records},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        self.registry_path.write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        anchor_id: str,
        frz_ref: str,
        projection_path: str,
        metadata: dict[str, Any] | None = None,
    ) -> AnchorEntry:
        """Register a new anchor ID.

        Args:
            anchor_id: Must match ANCHOR_ID_PATTERN (e.g., JRN-001).
            frz_ref: FRZ reference string (e.g., FRZ-001).
            projection_path: One of VALID_PROJECTION_PATHS (SRC, EPIC, FEAT,
                TECH, UI, TEST, IMPL).
            metadata: Optional key-value metadata dict.

        Returns:
            The created AnchorEntry.

        Raises:
            CommandError: INVALID_REQUEST on bad format, bad projection,
                or duplicate anchor_id+projection_path combination.
        """
        if not ANCHOR_ID_PATTERN.match(anchor_id):
            raise CommandError(
                "INVALID_REQUEST", f"Invalid anchor ID format: {anchor_id}"
            )
        if projection_path not in VALID_PROJECTION_PATHS:
            raise CommandError(
                "INVALID_REQUEST",
                f"Invalid projection path: {projection_path}. Must be one of: {', '.join(sorted(VALID_PROJECTION_PATHS))}",
            )

        records = self._load()
        for rec in records:
            if rec["anchor_id"] == anchor_id and rec["projection_path"] == projection_path:
                raise CommandError(
                    "INVALID_REQUEST",
                    f"Anchor {anchor_id} already registered for {projection_path}",
                )

        now = datetime.now(timezone.utc).isoformat()
        record = {
            "anchor_id": anchor_id,
            "frz_ref": frz_ref,
            "projection_path": projection_path,
            "metadata": metadata or {},
            "registered_at": now,
        }
        records.append(record)
        self._save(records)
        return _dict_to_entry(record)

    def resolve(self, anchor_id: str, projection_path: str | None = None) -> AnchorEntry | list[AnchorEntry] | None:
        """Look up an anchor by ID.

        Args:
            anchor_id: Anchor identifier to look up.
            projection_path: If provided, return the single AnchorEntry
                matching both anchor_id and projection_path. If None,
                return a list of all AnchorEntries for that anchor_id.

        Returns:
            Single AnchorEntry (when projection_path given), list of
            AnchorEntries (when projection_path is None), or None.
        """
        records = self._load()
        matches = [
            rec for rec in records
            if rec["anchor_id"] == anchor_id
        ]

        if projection_path is not None:
            for rec in matches:
                if rec["projection_path"] == projection_path:
                    return _dict_to_entry(rec)
            return None

        if not matches:
            return None
        return [_dict_to_entry(rec) for rec in matches]

    def register_projection(
        self,
        anchor_id: str,
        frz_ref: str,
        projection_path: str,
        metadata: dict[str, Any] | None = None,
    ) -> AnchorEntry:
        """Register a new projection_path for an existing anchor, or create it.

        Allows the same anchor_id to be registered with different projection_path
        values (e.g., JRN-001@SRC, JRN-001@EPIC, JRN-001@FEAT).

        Args:
            anchor_id: Must match ANCHOR_ID_PATTERN.
            frz_ref: FRZ reference string.
            projection_path: One of VALID_PROJECTION_PATHS.
            metadata: Optional metadata for this projection entry.

        Returns:
            The created or updated AnchorEntry.
        """
        if not ANCHOR_ID_PATTERN.match(anchor_id):
            raise CommandError(
                "INVALID_REQUEST", f"Invalid anchor ID format: {anchor_id}"
            )
        if projection_path not in VALID_PROJECTION_PATHS:
            raise CommandError(
                "INVALID_REQUEST",
                f"Invalid projection path: {projection_path}. Must be one of: {', '.join(sorted(VALID_PROJECTION_PATHS))}",
            )

        records = self._load()

        # Check for duplicate anchor_id + projection_path combo
        for rec in records:
            if rec["anchor_id"] == anchor_id and rec["projection_path"] == projection_path:
                raise CommandError(
                    "INVALID_REQUEST",
                    f"Anchor {anchor_id} already registered for {projection_path}",
                )

        now = datetime.now(timezone.utc).isoformat()
        record = {
            "anchor_id": anchor_id,
            "frz_ref": frz_ref,
            "projection_path": projection_path,
            "metadata": metadata or {},
            "registered_at": now,
        }
        records.append(record)
        self._save(records)
        return _dict_to_entry(record)

    def list_by_frz(self, frz_ref: str) -> list[AnchorEntry]:
        """Return all anchors referencing a given FRZ."""
        records = self._load()
        return [
            _dict_to_entry(rec) for rec in records if rec["frz_ref"] == frz_ref
        ]

    def list_all(self) -> list[AnchorEntry]:
        """Return all registered anchors."""
        records = self._load()
        return [_dict_to_entry(rec) for rec in records]

    def count(self) -> int:
        """Return the number of registered anchors."""
        return len(self._load())


def _dict_to_entry(record: dict[str, Any]) -> AnchorEntry:
    """Convert a registry record dict to an AnchorEntry dataclass."""
    return AnchorEntry(
        anchor_id=record["anchor_id"],
        frz_ref=record["frz_ref"],
        projection_path=record["projection_path"],
        metadata=record.get("metadata", {}),
        registered_at=record.get("registered_at"),
    )
