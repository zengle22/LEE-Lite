"""Helpers for resolving governed skill runtime source directories."""

from __future__ import annotations

from pathlib import Path


def canonical_cli_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_skill_scripts_dir(workspace_root: Path, scripts_subdir: str) -> Path:
    workspace_dir = workspace_root / "skills" / scripts_subdir / "scripts"
    if workspace_dir.exists():
        return workspace_dir
    return canonical_cli_root() / "skills" / scripts_subdir / "scripts"
