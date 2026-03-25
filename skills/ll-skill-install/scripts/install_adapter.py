#!/usr/bin/env python3
"""
Install a canonical workflow skill into Codex as a workspace-bound adapter.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

import yaml


IGNORE_NAMES = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def default_skills_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_yaml(path: Path):
    return yaml.safe_load(read_text(path))


def dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=False)


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def parse_frontmatter(skill_md_path: Path) -> dict:
    content = read_text(skill_md_path)
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        raise ValueError(f"SKILL.md is missing YAML frontmatter: {skill_md_path}")
    frontmatter = yaml.safe_load(match.group(1))
    if not isinstance(frontmatter, dict):
        raise ValueError(f"SKILL.md frontmatter must be a mapping: {skill_md_path}")
    return frontmatter


def infer_workspace_root(source_skill_dir: Path) -> Path:
    parent = source_skill_dir.parent
    if parent.name == "skills":
        return parent.parent
    for candidate in source_skill_dir.parents:
        if candidate.name == "skills":
            return candidate.parent
    return source_skill_dir.parent


def title_case(skill_name: str) -> str:
    words = []
    for word in skill_name.split("-"):
        if word in {"ll", "lee"}:
            words.append(word.upper())
        else:
            words.append(word.capitalize())
    return " ".join(words)


def load_contract(source_skill_dir: Path) -> dict:
    contract_path = source_skill_dir / "ll.contract.yaml"
    if not contract_path.exists():
        return {}
    contract = load_yaml(contract_path)
    if not isinstance(contract, dict):
        raise ValueError(f"ll.contract.yaml must be a mapping: {contract_path}")
    return contract


def load_openai_interface(source_skill_dir: Path) -> dict:
    openai_path = source_skill_dir / "agents" / "openai.yaml"
    if not openai_path.exists():
        return {}
    data = load_yaml(openai_path)
    if not isinstance(data, dict):
        return {}
    interface = data.get("interface")
    return interface if isinstance(interface, dict) else {}


def display_name(skill_name: str, interface: dict) -> str:
    value = interface.get("display_name")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return title_case(skill_name)


def adapter_description(workspace_root: Path, frontmatter: dict, contract: dict, source_skill_name: str) -> str:
    if contract:
        workflow_key = contract.get("workflow_key", source_skill_name.replace("-", "."))
        input_type = contract.get("input", {}).get("artifact_type", "input artifact")
        output_type = contract.get("output", {}).get("artifact_type", "output artifact")
        downstream = contract.get("authority", {}).get("downstream_workflow")
        if downstream:
            tail = f" before {downstream}."
        else:
            tail = "."
        return (
            f"Workspace-bound adapter for the canonical {workflow_key} governed workflow in "
            f"{workspace_root}. Use when a {input_type} needs to be transformed into a "
            f"{output_type}{tail}"
        )

    source_description = frontmatter.get("description")
    if isinstance(source_description, str) and source_description.strip():
        return (
            f"Workspace-bound adapter for the canonical {source_skill_name} skill in "
            f"{workspace_root}. {source_description.strip()}"
        )
    return (
        f"Workspace-bound adapter for the canonical {source_skill_name} skill in "
        f"{workspace_root}."
    )


def adapter_body(
    source_skill_dir: Path,
    workspace_root: Path,
    dest_root: Path,
    skill_name: str,
    frontmatter: dict,
    contract: dict,
    interface: dict,
) -> str:
    workflow_key = contract.get("workflow_key", skill_name.replace("-", "."))
    authority = contract.get("authority", {}) if isinstance(contract.get("authority"), dict) else {}
    runtime = contract.get("runtime", {}) if isinstance(contract.get("runtime"), dict) else {}
    input_type = contract.get("input", {}).get("artifact_type", "input artifact")
    output_type = contract.get("output", {}).get("artifact_type", "output artifact")
    upstream = authority.get("upstream_skill")
    downstream = authority.get("downstream_workflow", "unspecified")
    template = authority.get("canonical_template")

    upstream_line = ""
    if upstream:
        upstream_installed = dest_root / upstream
        if upstream_installed.exists():
            upstream_line = f"- Upstream governed skill: `{upstream_installed}`\n"
        else:
            upstream_line = f"- Upstream governed skill: `{upstream}`\n"

    read_lines = [
        f"1. Read `{source_skill_dir / 'SKILL.md'}`.",
    ]
    for relative in ["ll.contract.yaml", "input/contract.yaml", "output/contract.yaml"]:
        target = source_skill_dir / relative
        if target.exists():
            read_lines.append(f"{len(read_lines) + 1}. Read `{target}`.")
    read_lines.append(
        f"{len(read_lines) + 1}. Read the semantic checklists and role prompts under "
        f"`{source_skill_dir}` only as needed."
    )

    runtime_lines = []
    command = runtime.get("command")
    if command:
        runtime_lines.append("- Canonical workflow command:")
        runtime_lines.append(f"  - `{command}`")
    helper_lines = []
    for helper in ["validate_input.sh", "validate_output.sh", "freeze_guard.sh"]:
        helper_path = source_skill_dir / "scripts" / helper
        if helper_path.exists():
            arg = "<artifact-dir>"
            if helper == "validate_input.sh":
                arg = "<input-artifact-dir>"
            elif helper == "validate_output.sh":
                arg = "<output-artifact-dir>"
            runtime_lines.append("- Canonical validation helpers:") if not helper_lines else None
            helper_lines.append(f"  - `bash {helper_path} {arg}`")
    runtime_lines.extend(helper_lines)
    if not contract:
        script_paths = sorted((source_skill_dir / "scripts").glob("*.py"))
        if script_paths:
            runtime_lines.append("- Canonical bundled scripts:")
            for script_path in script_paths:
                runtime_lines.append(f"  - `python {script_path} --help`")
    if not runtime_lines:
        runtime_lines.append("- No explicit runtime command was found in the canonical contract.")

    frontmatter_block = dump_yaml(
        {
            "name": skill_name,
            "description": adapter_description(workspace_root, frontmatter, contract, skill_name),
        }
    ).strip()

    body = [
        "---",
        frontmatter_block,
        "---",
        "",
        f"# {display_name(skill_name, interface)}",
        "",
        "This installed skill is an adapter to the canonical implementation in the current workspace:",
        "",
        f"- Skill root: `{source_skill_dir}`",
    ]
    if template:
        body.append(f"- Workflow template authority: `{template}`")
    if contract and workflow_key:
        body.append(f"- Workflow key: `{workflow_key}`")
    elif not contract:
        body.append(f"- Skill name: `{skill_name}`")
    if upstream_line:
        body.append(upstream_line.rstrip())
    body.extend(
        [
            "",
            f"Use this skill only when operating inside `{workspace_root}` or an equivalent checkout "
            "with the same canonical paths.",
            "",
            "## Required Read Order",
            "",
            *read_lines,
            "",
            "## Runtime Entry Points",
            "",
            *runtime_lines,
        ]
    )
    if contract:
        body.extend(
            [
                "",
                "## Workflow Boundary",
                "",
                f"- Input boundary: one `{input_type}` from the canonical workflow boundary",
                f"- Output boundary: one `{output_type}` under the canonical workspace skill/runtime expectations",
                f"- Downstream handoff: `{downstream}`",
                "- Out of scope: bypassing the canonical workflow template, hand-editing installed metadata in place, and inventing alternate canonical paths",
                "",
                "## Guardrails",
                "",
                "- Treat the workspace skill as the canonical source of truth.",
                "- Prefer the canonical workflow command over manually drafting workflow outputs.",
                "- Preserve provenance, source refs, and freeze refs when the canonical contract requires them.",
                "- Refresh the installed copy from the canonical source instead of making drift-only edits in the installed adapter.",
            ]
        )
    else:
        body.extend(
            [
                "",
                "## Adapter Boundary",
                "",
                "- Purpose: expose the canonical skill through an installed workspace-bound entry in Codex.",
                "- Source of truth: the canonical skill directory in the current workspace.",
                "- Out of scope: maintaining a divergent installed copy by hand.",
                "",
                "## Guardrails",
                "",
                "- Treat the workspace skill as the canonical source of truth.",
                "- Run the canonical bundled scripts from the workspace copy when the task depends on current logic.",
                "- Refresh the installed copy from the canonical source instead of making drift-only edits in the installed adapter.",
            ]
        )
    return "\n".join(body) + "\n"


def adapter_openai_yaml(skill_name: str, contract: dict, interface: dict) -> str:
    workflow_key = contract.get("workflow_key", skill_name.replace("-", "."))
    target_label = workflow_key if contract else skill_name
    short_description = f"Workspace adapter for {target_label}"
    short_description = short_description[:64]
    display = display_name(skill_name, interface)
    if contract:
        default_prompt = (
            f"Use ${skill_name} to route into the canonical workspace "
            f"{workflow_key} governed workflow."
        )
    else:
        default_prompt = (
            f"Use ${skill_name} to route into the canonical workspace "
            f"{skill_name} skill."
        )
    return "\n".join(
        [
            "interface:",
            f"  display_name: {quote_yaml(display)}",
            f"  short_description: {quote_yaml(short_description)}",
            f"  default_prompt: {quote_yaml(default_prompt)}",
            "",
        ]
    )


def install_adapter(
    source_skill_dir: Path,
    dest_root: Path,
    workspace_root: Path | None,
    replace: bool,
) -> Path:
    source_skill_dir = source_skill_dir.resolve()
    if not source_skill_dir.exists():
        raise FileNotFoundError(f"Source skill directory not found: {source_skill_dir}")
    if not (source_skill_dir / "SKILL.md").exists():
        raise FileNotFoundError(f"Source SKILL.md not found: {source_skill_dir / 'SKILL.md'}")

    workspace_root = workspace_root.resolve() if workspace_root else infer_workspace_root(source_skill_dir)
    frontmatter = parse_frontmatter(source_skill_dir / "SKILL.md")
    skill_name = frontmatter.get("name")
    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("Source SKILL.md is missing a valid name.")

    contract = load_contract(source_skill_dir)
    interface = load_openai_interface(source_skill_dir)
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_dir = dest_root / skill_name

    if dest_dir.exists():
        if not replace:
            raise FileExistsError(f"Destination already exists: {dest_dir}")
        shutil.rmtree(dest_dir)

    shutil.copytree(source_skill_dir, dest_dir, ignore=IGNORE_NAMES)

    write_text(
        dest_dir / "SKILL.md",
        adapter_body(source_skill_dir, workspace_root, dest_root, skill_name, frontmatter, contract, interface),
    )
    write_text(dest_dir / "agents" / "openai.yaml", adapter_openai_yaml(skill_name, contract, interface))
    return dest_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install a canonical workflow skill into Codex as a workspace-bound adapter."
    )
    parser.add_argument("--source", required=True, help="Canonical source skill directory")
    parser.add_argument("--dest-root", help="Destination skills root, defaults to $CODEX_HOME/skills")
    parser.add_argument(
        "--workspace-root",
        help="Workspace root to reference in the generated adapter; inferred from the source path by default",
    )
    parser.add_argument("--replace", action="store_true", help="Replace an existing installed copy")
    args = parser.parse_args()

    source_skill_dir = Path(args.source).expanduser()
    dest_root = Path(args.dest_root).expanduser() if args.dest_root else default_skills_dir()
    workspace_root = Path(args.workspace_root).expanduser() if args.workspace_root else None

    try:
        dest_dir = install_adapter(source_skill_dir, dest_root, workspace_root, args.replace)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] Installed adapter to {dest_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
