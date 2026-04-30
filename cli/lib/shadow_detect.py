"""Shadow fix detection: detect when files are modified but bugs are still open.

Truth source: ADR-055 §2.8 Shadow Fix Detection.
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lib.bug_registry import load_or_create_registry


def _timestamp() -> str:
    """Return current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scan_git_diff(
    workspace_root: Path,
    since_commit: str | None = None,
) -> list[str]:
    """Scan git diff and return list of modified files.

    Args:
        workspace_root: Root of the workspace (git repo)
        since_commit: Optional commit hash to diff from

    Returns:
        List of modified file paths (relative to repo root)
    """
    try:
        cmd = ["git", "diff", "--name-only"]
        if since_commit:
            cmd.append(since_commit)

        result = subprocess.run(
            cmd,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=True,
        )

        files = result.stdout.strip().split("\n")
        return [f for f in files if f.strip()]
    except Exception:
        return []


def check_shadow_fixes(
    workspace_root: Path,
    feat_ref: str,
    since_commit: str | None = None,
) -> dict[str, Any]:
    """Check for shadow fixes: files modified but bugs still open.

    Args:
        workspace_root: Root of the workspace
        feat_ref: Feature reference to check
        since_commit: Optional commit hash to diff from

    Returns:
        Dict with shadow_fixes list, warnings list, summary
    """
    # Get modified files
    modified_files = scan_git_diff(workspace_root, since_commit)
    if not modified_files:
        return {
            "shadow_fixes": [],
            "warnings": [],
            "summary": "No modified files detected",
            "modified_count": 0,
        }

    # Load registry and get open bugs
    registry = load_or_create_registry(workspace_root, feat_ref)
    open_bugs = [b for b in registry["bugs"] if b["status"] in {"open"}]

    if not open_bugs:
        return {
            "shadow_fixes": [],
            "warnings": [],
            "summary": "No open bugs to check",
            "modified_count": len(modified_files),
        }

    # Check each open bug against modified files
    shadow_fixes = []
    for bug in open_bugs:
        bug_cov_id = bug.get("coverage_id", bug.get("case_id", ""))
        bug_id = bug.get("bug_id", "unknown")
        fix_hypothesis = bug.get("fix_hypothesis", {})
        affected_files = fix_hypothesis.get("affected_files", []) if fix_hypothesis else []

        # If bug doesn't have affected_files, skip (can't detect)
        if not affected_files:
            continue

        # Check for overlap
        overlap = set(affected_files) & set(modified_files)
        if overlap:
            shadow_fixes.append({
                "bug_id": bug_id,
                "coverage_id": bug_cov_id,
                "bug_title": bug.get("title", ""),
                "modified_files": list(overlap),
                "all_affected_files": affected_files,
                "status": bug["status"],
            })

    # Create warnings
    warnings = []
    for sf in shadow_fixes:
        warnings.append(
            f"⚠️ Shadow Fix Detected: Bug {sf['bug_id']} ('{sf['bug_title']}') "
            f"has modified files: {', '.join(sf['modified_files'])} "
            f"but is still in {sf['status']} status. "
            f"Consider running ll-bug-remediate to track the fix properly."
        )

    summary = (
        f"Found {len(shadow_fixes)} potential shadow fixes "
        f"among {len(open_bugs)} open bugs "
        f"with {len(modified_files)} modified files"
    )

    return {
        "shadow_fixes": shadow_fixes,
        "warnings": warnings,
        "summary": summary,
        "modified_count": len(modified_files),
        "open_bug_count": len(open_bugs),
        "shadow_fix_count": len(shadow_fixes),
    }
