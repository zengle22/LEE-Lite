"""Patch context injection for AI session awareness (ADR-049).

Scans experience-patches for non-terminal patches relevant to a target
file and formats them as context-friendly text, respecting the context
budget of 3000 tokens / 10 patches (ADR-049 section 12.1).

BOUNDARY: This module handles CONSUMER-SIDE injection — it matches patches
by target file and returns markdown for AI consumption during code edits.
It is NOT the same as patch_aware_context.py, which handles FULL-SCAN
recording by feat-ref for evidence capture (that script was removed as a
skill; its function remains in cli/lib/patch_context_injector.py).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .patch_schema import ChangeClass, PatchStatus, derive_grade


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ADR-049 section 12.1 budget constraints
MAX_CONTEXT_TOKENS = 3000
MAX_PATCH_COUNT = 10
# Rough token estimate: 1 token ~ 4 chars for English text
TOKENS_PER_CHAR = 0.25

TERMINAL_STATUSES = {
    PatchStatus.applied,
    PatchStatus.rejected,
    PatchStatus.superseded,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_related_patches(
    workspace_root: str | Path,
    target_file: str,
    *,
    feat_ref: str | None = None,
) -> list[dict[str, Any]]:
    """Scan experience-patches for non-terminal patches matching *target_file*.

    Args:
        workspace_root: Root of the project workspace.
        target_file: Relative path of the file being worked on.
        feat_ref: Optional feature reference to narrow the search
                  to a specific FEAT directory.

    Returns:
        List of patch dicts (parsed YAML) whose ``changed_files`` include
        *target_file* and whose status is not terminal.
    """
    workspace_root = Path(workspace_root)
    patch_dirs = _discover_patch_dirs(workspace_root, feat_ref=feat_ref)
    results: list[dict[str, Any]] = []

    for patch_dir in patch_dirs:
        for yaml_file in sorted(patch_dir.glob("*.yaml")):
            patch = _load_patch_yaml(yaml_file)
            if patch is None:
                continue
            if _is_terminal(patch):
                continue
            changed_files = patch.get("changed_files", [])
            if target_file in changed_files:
                patch["_source_file"] = str(yaml_file)
                results.append(patch)

    return results


def summarize_patch_for_context(
    patch: dict[str, Any],
    *,
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> str:
    """Format a single patch as context-friendly text.

    Respects the token budget by truncating the YAML summary section
    if it exceeds *max_tokens*.

    Args:
        patch: Patch dict (parsed YAML).
        max_tokens: Maximum token budget for this patch summary.

    Returns:
        Markdown-formatted context string for the patch.
    """
    max_chars = int(max_tokens / TOKENS_PER_CHAR)

    lines: list[str] = []
    lines.append(f"### Patch: {patch.get('id', 'unknown')}")
    lines.append(f"- **title**: {patch.get('title', '')}")
    lines.append(f"- **change_class**: {patch.get('change_class', '')}")
    change_class = patch.get("change_class", "")
    grade_level = patch.get("grade_level", derive_grade(change_class).value)
    lines.append(f"- **grade_level**: {grade_level}")

    # Highlight Major patches with a warning
    if grade_level == "major":
        lines.append(f"\n> [!WARNING] MAJOR change — requires FRZ re-freeze via `ll frz-manage freeze --type revise`")

    lines.append(f"- **scope**: {patch.get('scope', '')}")
    lines.append(f"- **status**: {patch.get('status', '')}")
    lines.append(f"- **changed_files**:")
    for fpath in patch.get("changed_files", []):
        lines.append(f"  - `{fpath}`")

    test_impact = patch.get("test_impact", "")
    if test_impact:
        lines.append(f"- **test_impact**: {test_impact}")

    patch_yaml = patch.get("patch_yaml", "")
    if patch_yaml:
        lines.append("- **patch_yaml**:")
        yaml_text = yaml.dump(patch_yaml, default_flow_style=False, allow_unicode=True) if isinstance(patch_yaml, dict) else str(patch_yaml)
        lines.append(f"```yaml\n{yaml_text}```")

    summary = "\n".join(lines)
    if len(summary) * TOKENS_PER_CHAR > max_chars:
        summary = summary[:max_chars] + "\n... [truncated to fit token budget]"
    return summary


def inject_context(
    workspace_root: str | Path,
    target_files: list[str],
    *,
    feat_ref: str | None = None,
    max_tokens: int = MAX_CONTEXT_TOKENS,
    max_patches: int = MAX_PATCH_COUNT,
) -> str:
    """Convenience: find patches for each file, format as markdown context.

    Args:
        workspace_root: Root of the project workspace.
        target_files: List of relative file paths to search patches for.
        feat_ref: Optional feature reference to narrow the search.
        max_tokens: Global token budget across all patches.
        max_patches: Maximum number of patches to include.

    Returns:
        Combined markdown context string with all relevant patches.
    """
    workspace_root = Path(workspace_root)
    all_patches: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for target_file in target_files:
        patches = find_related_patches(workspace_root, target_file, feat_ref=feat_ref)
        for p in patches:
            pid = p.get("id", "")
            if pid not in seen_ids:
                seen_ids.add(pid)
                all_patches.append(p)

    # Enforce global budget
    all_patches = all_patches[:max_patches]

    sections: list[str] = []
    sections.append("## Experience Patch Context (Change Grading)\n")
    sections.append(
        f"> Context budget: {max_tokens} tokens, "
        f"max {max_patches} patches. "
        f"Found {len(all_patches)} relevant patch(es).\n"
        f"> Patches graded: Minor = code-level settle, Major = FRZ re-freeze required.\n"
    )

    remaining_tokens = max_tokens
    for patch in all_patches:
        patch_tokens = min(max_tokens, remaining_tokens)
        if patch_tokens <= 0:
            break
        section = summarize_patch_for_context(patch, max_tokens=patch_tokens)
        estimated_tokens = int(len(section) * TOKENS_PER_CHAR)
        remaining_tokens -= estimated_tokens
        sections.append(section)
        sections.append("")

    if not all_patches:
        sections.append("No relevant experience patches found.\n")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _discover_patch_dirs(
    workspace_root: Path,
    *,
    feat_ref: str | None = None,
) -> list[Path]:
    """Locate experience-patch directories under ssot/experience-patches."""
    base = workspace_root / "ssot" / "experience-patches"
    if not base.is_dir():
        return []

    if feat_ref:
        feat_dir = base / feat_ref
        return [feat_dir] if feat_dir.is_dir() else []

    # Collect all FEAT subdirectories
    dirs = [d for d in base.iterdir() if d.is_dir() and d.name.startswith("FEAT")]
    return sorted(dirs)


def _load_patch_yaml(path: Path) -> dict[str, Any] | None:
    """Load and return a patch YAML file, or None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None
        # Derive grade_level if not present, using derive_grade from patch_schema
        if "grade_level" not in data and "change_class" in data:
            data["grade_level"] = derive_grade(data["change_class"]).value
            data["grade_derived_from"] = "patch_schema.derive_grade"
        return data
    except (OSError, yaml.YAMLError):
        return None


def _is_terminal(patch: dict[str, Any]) -> bool:
    """Return True if the patch status is terminal (not actionable)."""
    status_str = str(patch.get("status", "")).strip().lower()
    for ts in TERMINAL_STATUSES:
        if status_str == ts.value.lower():
            return True
    return False
