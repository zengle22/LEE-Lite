"""Auto-registration of experience patches from git-detected changes (ADR-049).

Detects uncommitted changes via git diff, maps them to FEAT directories,
drafts patch YAML, and writes to ssot/experience-patches.

Does NOT auto-commit or auto-finalize patches (ADR-049 section 12.2
requires user confirmation).
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from .patch_schema import ChangeClass, PatchStatus


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_changes(
    workspace_root: str | Path,
    *,
    feat_ref: str | None = None,
) -> list[dict[str, Any]]:
    """Detect uncommitted changes using ``git diff --name-status``.

    Args:
        workspace_root: Root of the project workspace (must be inside a
                        git repository).
        feat_ref: Optional feature reference to filter results to a
                  specific FEAT directory.

    Returns:
        List of dicts with keys: ``status`` (A/M/D), ``path`` (relative
        file path), ``feat_dir`` (mapped FEAT directory or None).
    """
    workspace_root = Path(workspace_root)
    raw = _run_git_diff(workspace_root)
    changes = _parse_name_status(raw)

    if feat_ref:
        changes = [c for c in changes if feat_ref in (c["path"] or "")]

    return changes


def draft_patch_yaml(
    changes: list[dict[str, Any]],
    workspace_root: str | Path,
) -> dict[str, Any]:
    """Pre-fill a Patch YAML draft from detected changes.

    Auto-suggests values for all fields. The draft has ``status=draft``
    and requires user review before finalization.

    Args:
        changes: Output of :func:`detect_changes`.
        workspace_root: Project workspace root.

    Returns:
        Dict with all patch fields pre-populated.
    """
    timestamp = int(time.time())
    changed_files = [c["path"] for c in changes if c["path"]]
    paths = changed_files

    # Auto-suggest change_class from file patterns
    change_class = _suggest_change_class(paths)

    # Derive scope from common path prefix
    scope = _derive_scope(paths)

    # test_impact is required but left as a prompt for the user
    test_impact = "TODO: describe which tests are affected or need updating"

    patch: dict[str, Any] = {
        "id": f"UXPATCH-{timestamp}",
        "title": "Auto-detected patch — please review and edit",
        "change_class": change_class.value,
        "scope": scope,
        "changed_files": changed_files,
        "test_impact": test_impact,
        "backwrite_targets": [],
        "status": PatchStatus.draft.value,
    }
    return patch


def register_patch(
    patch: dict[str, Any],
    output_dir: str | Path,
) -> Path:
    """Validate and write a patch to the experience-patches directory.

    Args:
        patch: Patch dict (typically from :func:`draft_patch_yaml`).
        output_dir: Directory to write the YAML file into.
                    Usually ``ssot/experience-patches/{feat_ref}/``.

    Returns:
        Path to the written YAML file.

    Raises:
        ValueError: If required fields are missing.
    """
    _validate_patch(patch)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    patch_id = patch["id"]
    yaml_path = output_dir / f"{patch_id}.yaml"

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(patch, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return yaml_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_git_diff(workspace_root: Path) -> str:
    """Run ``git diff --name-status`` and return raw output."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", "--cached", "--", "."],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Also check unstaged changes
        result_unstaged = subprocess.run(
            ["git", "diff", "--name-status", "--", "."],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        combined = result.stdout + result_unstaged.stdout
        return combined
    except (subprocess.TimeoutExpired, OSError):
        return ""


def _parse_name_status(raw: str) -> list[dict[str, Any]]:
    """Parse ``git diff --name-status`` output into structured dicts."""
    changes: list[dict[str, Any]] = []
    for line in raw.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0].strip()
        path = parts[1].strip()
        # Map to FEAT directory if the path lives under ssot/experience-patches
        feat_dir = None
        if "ssot/experience-patches/" in path:
            segments = path.split("/")
            for i, seg in enumerate(segments):
                if seg == "experience-patches" and i + 1 < len(segments):
                    feat_dir = segments[i + 1]
                    break
        changes.append({"status": status, "path": path, "feat_dir": feat_dir})
    return changes


def _suggest_change_class(paths: list[str]) -> ChangeClass:
    """Suggest a ChangeClass based on file path patterns."""
    ui_patterns = (".html", ".jsx", ".tsx", ".vue", ".svelte", "ui/", "components/", "templates/")
    validation_patterns = ("validator", "validation", "schema", "constraint")
    nav_patterns = ("nav", "route", "router", "link", "breadcrumb")
    layout_patterns = ("layout", "grid", "flex", "style", ".css")
    error_patterns = ("error", "exception", "fallback", "boundary")

    joined = " ".join(paths).lower()

    if any(p in joined for p in ui_patterns):
        return ChangeClass.ui_flow
    if any(p in joined for p in validation_patterns):
        return ChangeClass.validation
    if any(p in joined for p in nav_patterns):
        return ChangeClass.navigation
    if any(p in joined for p in layout_patterns):
        return ChangeClass.layout
    if any(p in joined for p in error_patterns):
        return ChangeClass.error_handling

    return ChangeClass.other


def _derive_scope(paths: list[str]) -> str:
    """Derive a scope string from the common path prefix."""
    if not paths:
        return ""

    # Use the most common top-level directory as scope
    top_dirs: dict[str, int] = {}
    for p in paths:
        parts = p.split("/")
        if len(parts) > 1:
            top = parts[0]
            top_dirs[top] = top_dirs.get(top, 0) + 1

    if top_dirs:
        return max(top_dirs, key=top_dirs.get)
    return paths[0].split("/")[0] if paths else ""


def _validate_patch(patch: dict[str, Any]) -> None:
    """Validate required fields before writing.

    Required fields: id, title, change_class, scope, changed_files,
    test_impact, backwrite_targets, status.
    """
    required = ["id", "title", "change_class", "scope", "changed_files",
                "test_impact", "backwrite_targets", "status"]
    missing = [f for f in required if f not in patch or patch[f] is None]
    if missing:
        raise ValueError(f"Missing required patch fields: {', '.join(missing)}")

    if not patch.get("changed_files"):
        raise ValueError("changed_files must not be empty")

    # test_impact must be filled (not the TODO placeholder)
    test_impact = str(patch.get("test_impact", "")).strip()
    if not test_impact or test_impact.startswith("TODO"):
        raise ValueError("test_impact is required and must describe actual test impact")
