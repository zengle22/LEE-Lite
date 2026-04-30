"""Gate remediation module for automatic bug promotion and consistency checks.

Truth source: ADR-055 §2.4 Gate remediation, §2.8A detected→open promotion.
Provides detected→open promotion, gap_list consistency checks, and audit logging.
"""
from __future__ import annotations

import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.bug_registry import (
    _save_registry,
    _timestamp,
    load_or_create_registry,
    registry_path,
    transition_bug_status_with_audit,
)
from cli.lib.errors import CommandError
from cli.lib.fs import ensure_parent, read_text


def _get_coverage_ids_from_gap_list(gap_list: list[dict]) -> set[str]:
    """Extract coverage_id from each gap_list item."""
    return {gap.get("coverage_id", gap.get("case_id", "")) for gap in gap_list}


def promote_detected_to_open(
    workspace_root: Path,
    feat_ref: str,
    gap_list: list[dict],
    run_id: str,
    actor: str = "system:gate-remediation",
) -> dict[str, Any]:
    """Promote detected bugs to open when they appear in gap_list.

    Returns summary: promoted_count, already_open_count, archived_count.
    """
    coverage_ids = _get_coverage_ids_from_gap_list(gap_list)
    registry = load_or_create_registry(workspace_root, feat_ref)
    path = registry_path(workspace_root, feat_ref)

    promoted_count = 0
    already_open_count = 0

    new_bugs = []
    for bug in registry["bugs"]:
        bug_coverage_id = bug.get("coverage_id", bug.get("case_id", ""))

        if bug["status"] == "open":
            already_open_count += 1
            new_bugs.append(bug)
        elif bug["status"] == "detected" and bug_coverage_id in coverage_ids:
            # Promote to open with audit
            new_bug = transition_bug_status_with_audit(
                workspace_root,
                feat_ref,
                bug,
                "open",
                reason="gate FAIL verdict",
                actor=actor,
                run_id=run_id,
            )
            new_bugs.append(new_bug)
            promoted_count += 1
        else:
            new_bugs.append(bug)

    # Update registry
    registry["bugs"] = new_bugs
    registry["version"] = str(uuid.uuid4())
    registry["last_synced_at"] = _timestamp()
    _save_registry(path, registry)

    return {
        "promoted_count": promoted_count,
        "already_open_count": already_open_count,
        "archived_count": 0,  # Handled separately
        "feat_ref": feat_ref,
        "run_id": run_id,
    }


def archive_detected_not_in_gap_list(
    workspace_root: Path,
    feat_ref: str,
    gap_list: list[dict],
    run_id: str,
    actor: str = "system:gate-remediation",
) -> dict[str, Any]:
    """Archive detected bugs NOT in gap_list (settlement says they're not real issues).

    Returns summary: archived_count, preserved_count.
    """
    coverage_ids = _get_coverage_ids_from_gap_list(gap_list)
    registry = load_or_create_registry(workspace_root, feat_ref)
    path = registry_path(workspace_root, feat_ref)

    archived_count = 0

    new_bugs = []
    for bug in registry["bugs"]:
        bug_coverage_id = bug.get("coverage_id", bug.get("case_id", ""))

        if bug["status"] == "detected" and bug_coverage_id not in coverage_ids:
            # Archive this bug with audit
            new_bug = transition_bug_status_with_audit(
                workspace_root,
                feat_ref,
                bug,
                "archived",
                reason="not in settlement gap_list",
                actor=actor,
                run_id=run_id,
            )
            new_bugs.append(new_bug)
            archived_count += 1
        else:
            new_bugs.append(bug)

    # Update registry
    registry["bugs"] = new_bugs
    registry["version"] = str(uuid.uuid4())
    registry["last_synced_at"] = _timestamp()
    _save_registry(path, registry)

    return {
        "archived_count": archived_count,
        "preserved_count": len(new_bugs) - archived_count,
        "feat_ref": feat_ref,
        "run_id": run_id,
    }
