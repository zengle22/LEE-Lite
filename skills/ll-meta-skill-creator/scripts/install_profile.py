#!/usr/bin/env python3
"""
Compatibility wrapper for installing ll-meta-skill-creator.

- `--profile codex` delegates to ll-skill-install so Codex gets a workspace-bound adapter.
- `--profile claude` delegates to ll-skill-install so Claude Code gets a workspace-bound adapter.
- `--profile standard` performs a plain copy of the canonical skill for non-adapter use.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_NAME = "ll-meta-skill-creator"
SUPPORTED_PROFILES = {"standard", "codex", "claude"}
IGNORE_NAMES = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def default_skills_dir(profile: str) -> Path:
    if profile == "claude":
        claude_home = os.environ.get("CLAUDE_HOME")
        if claude_home:
            return Path(claude_home).expanduser() / "skills"
        return Path.home() / ".claude" / "skills"

    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def source_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def workspace_root() -> Path:
    return source_dir().parent.parent


def install_adapter_script() -> Path:
    return workspace_root() / "skills" / "ll-skill-install" / "scripts" / "install_adapter.py"


def install_standard(dest_root: Path, replace: bool) -> Path:
    src = source_dir()
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_dir = dest_root / SKILL_NAME
    if dest_dir.exists():
        if not replace:
            raise FileExistsError(f"Destination already exists: {dest_dir}")
        shutil.rmtree(dest_dir)
    shutil.copytree(src, dest_dir, ignore=IGNORE_NAMES)
    return dest_dir


def install_adapter_profile(dest_root: Path, replace: bool, runtime_name: str) -> Path:
    script_path = install_adapter_script()
    if not script_path.exists():
        raise FileNotFoundError(
            f"Required installer not found: {script_path}. Install or restore ll-skill-install first."
        )

    command = [
        sys.executable,
        str(script_path),
        "--source",
        str(source_dir()),
        "--dest-root",
        str(dest_root),
        "--workspace-root",
        str(workspace_root()),
    ]
    if replace:
        command.append("--replace")

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or "unknown error"
        raise RuntimeError(detail)
    if result.stdout.strip():
        print(result.stdout.strip())
    print(f"[OK] Delegated adapter installation for {runtime_name}.")
    return dest_root / SKILL_NAME


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install ll-meta-skill-creator with a standard copy or Codex/Claude adapter profile."
    )
    parser.add_argument("--profile", choices=sorted(SUPPORTED_PROFILES), default="standard")
    parser.add_argument(
        "--dest",
        help="Destination skills root; defaults to ~/.claude/skills for profile=claude, otherwise $CODEX_HOME/skills or ~/.codex/skills",
    )
    parser.add_argument("--replace", action="store_true", help="Replace an existing installed copy")
    args = parser.parse_args()

    dest_root = Path(args.dest).expanduser() if args.dest else default_skills_dir(args.profile)

    try:
        if args.profile == "standard":
            dest_dir = install_standard(dest_root, args.replace)
        elif args.profile == "codex":
            dest_dir = install_adapter_profile(dest_root, args.replace, "Codex")
        else:
            dest_dir = install_adapter_profile(dest_root, args.replace, "Claude Code")
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] Installed {SKILL_NAME} to {dest_dir}")
    print(f"[OK] Applied runtime profile: {args.profile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
