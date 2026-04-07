"""Diff view helpers for ADR-043 semantic review."""

from __future__ import annotations

from typing import Any


def build_diff_view(
    *,
    upstream_refs: list[str] | None = None,
    previous_owner_ref: str = "",
    added: list[str] | None = None,
    changed: list[str] | None = None,
    preserved: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "upstream_refs": [str(item).strip() for item in (upstream_refs or []) if str(item).strip()],
        "previous_owner_ref": str(previous_owner_ref or "").strip(),
        "added": [str(item).strip() for item in (added or []) if str(item).strip()],
        "changed": [str(item).strip() for item in (changed or []) if str(item).strip()],
        "preserved": [str(item).strip() for item in (preserved or []) if str(item).strip()],
    }
