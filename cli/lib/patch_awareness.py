"""Patch-aware context schema definitions for AI awareness injection.

Separate from cli.lib.patch_schema (experience patch schemas) to avoid
import coupling between the two distinct domains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PatchAwarenessStatus(str, Enum):
    """Lifecycle status of a patch relative to AI awareness injection."""

    PENDING = "pending"
    APPLIED = "applied"
    SUPERSEDED = "superseded"
    REVERTED = "reverted"


@dataclass(frozen=True)
class PatchContext:
    """Minimal patch context for AI awareness injection."""

    patches_found: list[dict[str, Any]] = field(default_factory=list)
    none_found: bool = False
    scan_path: str = ""
    scan_ref: str = ""
    total_count: int = 0
    summary_budget: int = 5

    def to_dict(self) -> dict[str, Any]:
        """Convert to a serializable dict for YAML recording."""
        return {
            "patches_found": self.patches_found,
            "none_found": self.none_found,
            "scan_path": self.scan_path,
            "scan_ref": self.scan_ref,
            "total_count": self.total_count,
            "summary_budget": self.summary_budget,
        }
