#!/usr/bin/env python3
"""
Install the canonical LL meta skill creator with a lightweight runtime profile.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

import yaml


SKILL_NAME = "ll-meta-skill-creator"
SUPPORTED_PROFILES = {"standard", "codex"}
IGNORE_NAMES = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def default_skills_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def update_frontmatter_description(skill_md: str, description: str) -> str:
    pattern = r"^---\n(.*?)\n---"
    match = re.match(pattern, skill_md, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md is missing YAML frontmatter.")
    frontmatter = yaml.safe_load(match.group(1))
    if not isinstance(frontmatter, dict):
        raise ValueError("SKILL.md frontmatter must be a mapping.")
    frontmatter["description"] = description
    rendered = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=False).strip()
    return re.sub(pattern, f"---\n{rendered}\n---", skill_md, count=1, flags=re.DOTALL)


def ensure_codex_runtime_note(skill_md: str) -> str:
    note = (
        "## Runtime Profile\n\n"
        "This installed copy targets Codex. Prefer repository-local paths, direct workspace edits, "
        "and explicit validation before reporting completion.\n"
    )
    if "## Runtime Profile" in skill_md:
        return skill_md
    marker = "## Non-Negotiable Rules"
    if marker in skill_md:
        return skill_md.replace(marker, note + "\n" + marker, 1)
    return skill_md.rstrip() + "\n\n" + note


def apply_profile(skill_dir: Path, profile: str) -> None:
    skill_md_path = skill_dir / "SKILL.md"
    openai_yaml_path = skill_dir / "agents" / "openai.yaml"

    skill_md = read_text(skill_md_path)
    openai_yaml = yaml.safe_load(read_text(openai_yaml_path))
    if not isinstance(openai_yaml, dict):
        raise ValueError("agents/openai.yaml must be a mapping.")

    base_description = (
        "Create or update LEE Lite workflow skills that keep a standard agent-skill shell while "
        "adding LEE governance files for contracts, structural and semantic validation, execution "
        "and supervision evidence, revision limits, and freeze gates. "
    )

    if profile == "codex":
        description = (
            base_description
            + "Use when Codex needs to scaffold or revise a governed workflow skill in the current "
            + "workspace, especially for requests mentioning Codex skills, LEE workflow skills, "
            + "ll.contract.yaml, ll.lifecycle.yaml, contract/evidence/supervisor/freeze, or "
            + "workflows such as src-to-epic and epic-to-feat."
        )
        skill_md = update_frontmatter_description(skill_md, description)
        skill_md = ensure_codex_runtime_note(skill_md)
        interface = openai_yaml.setdefault("interface", {})
        interface["default_prompt"] = (
            "Use $ll-meta-skill-creator to scaffold a governed LEE workflow skill for Codex."
        )
    else:
        description = (
            base_description
            + "Use when an agent needs to scaffold or revise a governed workflow skill, especially "
            + "for requests mentioning LEE workflow skills, ll.contract.yaml, ll.lifecycle.yaml, "
            + "contract/evidence/supervisor/freeze, or workflows such as src-to-epic and epic-to-feat."
        )
        skill_md = update_frontmatter_description(skill_md, description)

    write_text(skill_md_path, skill_md)
    write_text(openai_yaml_path, yaml.safe_dump(openai_yaml, sort_keys=False, allow_unicode=False))


def install_skill(source_dir: Path, dest_root: Path, profile: str, replace: bool) -> Path:
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_dir = dest_root / SKILL_NAME
    if dest_dir.exists():
        if not replace:
            raise FileExistsError(f"Destination already exists: {dest_dir}")
        shutil.rmtree(dest_dir)
    shutil.copytree(source_dir, dest_dir, ignore=IGNORE_NAMES)
    apply_profile(dest_dir, profile)
    return dest_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Install LL meta skill creator with a runtime profile.")
    parser.add_argument("--profile", choices=sorted(SUPPORTED_PROFILES), default="standard")
    parser.add_argument("--dest", help="Destination skills root; defaults to $CODEX_HOME/skills or ~/.codex/skills")
    parser.add_argument("--replace", action="store_true", help="Replace an existing installed copy")
    args = parser.parse_args()

    source_dir = Path(__file__).resolve().parent.parent
    dest_root = Path(args.dest).expanduser() if args.dest else default_skills_dir()

    try:
        dest_dir = install_skill(source_dir, dest_root, args.profile, args.replace)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] Installed {SKILL_NAME} to {dest_dir}")
    print(f"[OK] Applied runtime profile: {args.profile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
