#!/usr/bin/env python3
"""
Validate that a workflow skill follows the LEE Lite governed skill shape.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "context",
    "agent",
}

REQUIRED_FILES = [
    "SKILL.md",
    "ll.contract.yaml",
    "ll.lifecycle.yaml",
    "input/contract.yaml",
    "input/schema.json",
    "input/semantic-checklist.md",
    "output/contract.yaml",
    "output/schema.json",
    "output/template.md",
    "output/semantic-checklist.md",
    "evidence/execution-evidence.schema.json",
    "evidence/supervision-evidence.schema.json",
    "evidence/report.template.md",
    "agents/executor.md",
    "agents/supervisor.md",
    "agents/openai.yaml",
    "resources/glossary.md",
    "resources/examples/input.example.md",
    "resources/examples/output.example.md",
    "resources/checklists/authoring-checklist.md",
    "resources/checklists/review-checklist.md",
    "scripts/validate_input.sh",
    "scripts/validate_output.sh",
    "scripts/collect_evidence.sh",
    "scripts/freeze_guard.sh",
]

REQUIRED_LIFECYCLE_STATES = {
    "drafted",
    "structurally_validated",
    "semantically_reviewed",
    "revised",
    "accepted",
    "frozen",
    "rejected",
}

REQUIRED_FREEZE_GATES = {
    "input_structural_pass",
    "input_semantic_pass",
    "output_structural_pass",
    "output_semantic_pass",
    "execution_evidence_present",
    "supervision_evidence_present",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_frontmatter(skill_md: Path, errors: list[str]) -> None:
    content = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        errors.append("SKILL.md is missing YAML frontmatter.")
        return
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"SKILL.md frontmatter is invalid YAML: {exc}")
        return
    if not isinstance(frontmatter, dict):
        errors.append("SKILL.md frontmatter must be a YAML mapping.")
        return
    unexpected = sorted(set(frontmatter) - ALLOWED_FRONTMATTER_KEYS)
    if unexpected:
        errors.append(f"SKILL.md has unexpected frontmatter keys: {', '.join(unexpected)}")
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+", name.strip()):
        errors.append("SKILL.md frontmatter name must be hyphen-case.")
    if not isinstance(description, str) or not description.strip():
        errors.append("SKILL.md frontmatter description is required.")


def validate_required_files(skill_dir: Path, errors: list[str]) -> None:
    for relative_path in REQUIRED_FILES:
        if not (skill_dir / relative_path).exists():
            errors.append(f"Missing required file: {relative_path}")


def validate_contract(skill_dir: Path, errors: list[str]) -> None:
    contract = load_yaml(skill_dir / "ll.contract.yaml")
    if not isinstance(contract, dict):
        errors.append("ll.contract.yaml must be a YAML mapping.")
        return

    for key in ["skill_id", "skill_type", "version", "roles", "runtime", "input", "output", "validation", "evidence", "lifecycle", "gate"]:
        if key not in contract:
            errors.append(f"ll.contract.yaml is missing '{key}'.")

    roles = contract.get("roles", {})
    for role_name in ["executor", "supervisor"]:
        role = roles.get(role_name)
        if not isinstance(role, dict):
            errors.append(f"ll.contract.yaml roles.{role_name} must be a mapping.")
            continue
        if role.get("required") is not True:
            errors.append(f"ll.contract.yaml roles.{role_name}.required must be true.")
        if role.get("evidence_required") is not True:
            errors.append(f"ll.contract.yaml roles.{role_name}.evidence_required must be true.")

    for side in ["input", "output"]:
        block = contract.get(side, {})
        if not isinstance(block, dict):
            errors.append(f"ll.contract.yaml {side} must be a mapping.")
            continue
        contract_file = block.get("contract_file")
        if not isinstance(contract_file, str):
            errors.append(f"ll.contract.yaml {side}.contract_file must be present.")
        elif not (skill_dir / contract_file).exists():
            errors.append(f"{side}.contract_file points to a missing path: {contract_file}")

    validation = contract.get("validation", {})
    structural = validation.get("structural", []) if isinstance(validation, dict) else []
    semantic = validation.get("semantic", {}) if isinstance(validation, dict) else {}
    if not isinstance(structural, list) or len(structural) < 2:
        errors.append("ll.contract.yaml validation.structural should list multiple checks.")
    if not isinstance(semantic, dict):
        errors.append("ll.contract.yaml validation.semantic must be a mapping.")
    else:
        for checklist_key in ["input_checklist", "output_checklist"]:
            checklist_path = semantic.get(checklist_key)
            if not isinstance(checklist_path, str):
                errors.append(f"ll.contract.yaml validation.semantic.{checklist_key} is required.")
            elif not (skill_dir / checklist_path).exists():
                errors.append(f"Semantic checklist path is missing: {checklist_path}")

    runtime = contract.get("runtime", {})
    if not isinstance(runtime, dict):
        errors.append("ll.contract.yaml runtime must be a mapping.")
    else:
        mode = runtime.get("mode")
        command = runtime.get("command")
        entry_script = runtime.get("entry_script")
        if mode not in {"lite_native", "legacy_lee"}:
            errors.append("ll.contract.yaml runtime.mode must be lite_native or legacy_lee.")
        if not isinstance(command, str) or not command.strip():
            errors.append("ll.contract.yaml runtime.command is required.")
        if isinstance(command, str) and "lee " in command and mode != "legacy_lee":
            errors.append("runtime.command references lee but runtime.mode is not legacy_lee.")
        if mode == "lite_native":
            if not isinstance(entry_script, str) or not entry_script.strip():
                errors.append("lite_native workflows must declare runtime.entry_script.")
            elif not (skill_dir / entry_script).exists():
                errors.append(f"runtime.entry_script points to a missing path: {entry_script}")
            if isinstance(command, str) and not command.strip().startswith("python "):
                errors.append("lite_native runtime.command should invoke a local python entrypoint.")
            if isinstance(structural, list):
                legacy_checks = [item for item in structural if isinstance(item, str) and "lee " in item]
                if legacy_checks:
                    errors.append("lite_native validation.structural must not reference legacy lee commands.")

    evidence = contract.get("evidence", {})
    if isinstance(evidence, dict):
        for evidence_key in ["execution_schema", "supervision_schema"]:
            evidence_path = evidence.get(evidence_key)
            if not isinstance(evidence_path, str):
                errors.append(f"ll.contract.yaml evidence.{evidence_key} is required.")
            elif not (skill_dir / evidence_path).exists():
                errors.append(f"Evidence schema path is missing: {evidence_path}")
    else:
        errors.append("ll.contract.yaml evidence must be a mapping.")

    lifecycle = contract.get("lifecycle", {})
    definition_file = lifecycle.get("definition_file") if isinstance(lifecycle, dict) else None
    if not isinstance(definition_file, str):
        errors.append("ll.contract.yaml lifecycle.definition_file is required.")
    elif not (skill_dir / definition_file).exists():
        errors.append(f"Lifecycle definition path is missing: {definition_file}")

    gate = contract.get("gate", {})
    freeze_requires = gate.get("freeze_requires") if isinstance(gate, dict) else None
    if not isinstance(freeze_requires, list):
        errors.append("ll.contract.yaml gate.freeze_requires must be a list.")
    else:
        missing = REQUIRED_FREEZE_GATES - set(freeze_requires)
        if missing:
            errors.append(
                "ll.contract.yaml gate.freeze_requires is missing: "
                + ", ".join(sorted(missing))
            )


def validate_lifecycle(skill_dir: Path, errors: list[str]) -> None:
    lifecycle = load_yaml(skill_dir / "ll.lifecycle.yaml")
    if not isinstance(lifecycle, dict):
        errors.append("ll.lifecycle.yaml must be a YAML mapping.")
        return
    states = lifecycle.get("states")
    if not isinstance(states, list):
        errors.append("ll.lifecycle.yaml states must be a list.")
        return
    missing = REQUIRED_LIFECYCLE_STATES - set(states)
    if missing:
        errors.append("ll.lifecycle.yaml is missing states: " + ", ".join(sorted(missing)))


def validate_json_files(skill_dir: Path, errors: list[str]) -> None:
    for relative_path in [
        "input/schema.json",
        "output/schema.json",
        "evidence/execution-evidence.schema.json",
        "evidence/supervision-evidence.schema.json",
    ]:
        try:
            load_json(skill_dir / relative_path)
        except Exception as exc:
            errors.append(f"{relative_path} is not valid JSON: {exc}")


def validate_openai_yaml(skill_dir: Path, errors: list[str]) -> None:
    openai_yaml = load_yaml(skill_dir / "agents" / "openai.yaml")
    if not isinstance(openai_yaml, dict):
        errors.append("agents/openai.yaml must be a YAML mapping.")
        return
    interface = openai_yaml.get("interface")
    if not isinstance(interface, dict):
        errors.append("agents/openai.yaml must define interface.")
        return
    for key in ["display_name", "short_description", "default_prompt"]:
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"agents/openai.yaml interface.{key} is required.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a governed LEE Lite workflow skill.")
    parser.add_argument("skill_path", help="Path to the skill directory")
    args = parser.parse_args()

    skill_dir = Path(args.skill_path).resolve()
    errors: list[str] = []

    if not skill_dir.exists() or not skill_dir.is_dir():
        print(f"[ERROR] Skill directory not found: {skill_dir}")
        return 1

    validate_required_files(skill_dir, errors)

    if not errors:
        validate_frontmatter(skill_dir / "SKILL.md", errors)
        validate_contract(skill_dir, errors)
        validate_lifecycle(skill_dir, errors)
        validate_json_files(skill_dir, errors)
        validate_openai_yaml(skill_dir, errors)

    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1

    print("[OK] Governed workflow skill is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
