from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from cli.ll import build_parser

from .common import (
    ROOT,
    Violation,
    build_report,
    changed_with_prefix,
    dump_json,
    find_skill_roots,
    load_json,
    load_yaml,
    match_any,
    read_text,
    run_pytest,
)


def extract_runtime_paths(command: str) -> list[str]:
    return re.findall(r"[\w./-]+\.(?:py|sh|json|yaml|yml|md)", command)


def build_cli_surface() -> dict[str, Any]:
    parser = build_parser()
    groups: dict[str, Any] = {}
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        for group_name, group_parser in action.choices.items():
            group_entry: dict[str, Any] = {"actions": {}}
            for sub_action in group_parser._actions:
                if not isinstance(sub_action, argparse._SubParsersAction):
                    continue
                for action_name, action_parser in sub_action.choices.items():
                    args_shape = []
                    for child in action_parser._actions:
                        if child.dest == "help":
                            continue
                        args_shape.append(
                            {
                                "dest": child.dest,
                                "required": bool(getattr(child, "required", False)),
                                "option_strings": list(child.option_strings),
                            }
                        )
                    group_entry["actions"][action_name] = {"args": args_shape}
            groups[group_name] = group_entry
    return groups


def check_skill_governance(changed_files: list[str], output_dir: Path, run_tests_flag: bool, manifest_path: Path) -> int:
    skill_roots = find_skill_roots(changed_files)
    violations: list[Violation] = []
    impacted_tests: set[str] = set()
    manifest = load_json(manifest_path)
    required_files = manifest["required_skill_files"]

    for skill_root in skill_roots:
        rel_root = skill_root.relative_to(ROOT).as_posix()
        for relative in required_files:
            if not (skill_root / relative).exists():
                violations.append(Violation("skill-governance", "bundle_file_missing", rel_root, f"Missing required file: {relative}"))
        contract_path = skill_root / "ll.contract.yaml"
        lifecycle_path = skill_root / "ll.lifecycle.yaml"
        skill_md = skill_root / "SKILL.md"
        if not contract_path.exists() or not lifecycle_path.exists() or not skill_md.exists():
            continue
        try:
            contract = load_yaml(contract_path)
            load_yaml(lifecycle_path)
        except Exception as exc:
            violations.append(Violation("skill-governance", "contract_parse_error", rel_root, f"YAML parse failed: {exc}"))
            continue
        try:
            load_json(skill_root / "input" / "schema.json")
            load_json(skill_root / "output" / "schema.json")
        except Exception as exc:
            violations.append(Violation("skill-governance", "contract_parse_error", rel_root, f"JSON schema parse failed: {exc}"))
        declared_paths = []
        for section in ("input", "output", "evidence"):
            block = contract.get(section, {}) if isinstance(contract, dict) else {}
            if isinstance(block, dict):
                for value in block.values():
                    if isinstance(value, str) and "/" in value:
                        declared_paths.append(value)
        runtime = contract.get("runtime", {}) if isinstance(contract, dict) else {}
        if isinstance(runtime, dict):
            for key in ("command", "executor_command", "supervisor_command"):
                value = runtime.get(key)
                if isinstance(value, str):
                    declared_paths.extend(extract_runtime_paths(value))
        for declared in sorted(set(declared_paths)):
            if declared.startswith("<"):
                continue
            if not (skill_root / declared).exists():
                violations.append(Violation("skill-governance", "broken_declared_path", rel_root, f"Declared path does not exist: {declared}"))
        agent_configs = sorted((skill_root / "agents").glob("*.yaml"))
        if agent_configs:
            for config in agent_configs:
                try:
                    load_yaml(config)
                except Exception as exc:
                    violations.append(Violation("skill-governance", "adapter_config_missing_or_invalid", rel_root, f"Invalid adapter config {config.name}: {exc}"))
        if isinstance(contract, dict):
            skill_text = read_text(skill_md)
            frontmatter = {}
            match = re.match(r"^---\n(.*?)\n---", skill_text, re.DOTALL)
            if match:
                try:
                    import yaml

                    frontmatter = yaml.safe_load(match.group(1)) or {}
                except Exception:
                    frontmatter = {}
            frontmatter_name = frontmatter.get("name") if isinstance(frontmatter, dict) else None
            if isinstance(frontmatter_name, str) and frontmatter_name.strip() != skill_root.name:
                violations.append(
                    Violation("skill-governance", "bundle_contract_mismatch", rel_root, f"SKILL.md frontmatter name does not match bundle directory: {frontmatter_name}")
                )
        impacted_tests.update(manifest["skill_test_map"].get(skill_root.name, []))

    report = build_report("skill-governance", violations, {"impacted_skills": [path.name for path in skill_roots], "tests_run": []})
    if run_tests_flag and impacted_tests:
        exit_code, payload = run_pytest(sorted(impacted_tests), output_dir / "skill-governance-pytest-report.json")
        report["tests_run"] = payload["tests"]
        if exit_code != 0:
            violations.append(Violation("skill-governance", "runtime_entry_smoke_failed", "skills", "Impacted skill tests failed."))
            report = build_report("skill-governance", violations, {"impacted_skills": [path.name for path in skill_roots], "tests_run": payload["tests"]})
    dump_json(output_dir / "skill-governance-report.json", report)
    return 1 if violations else 0


def check_cli_governance(changed_files: list[str], output_dir: Path, snapshot_path: Path, run_tests_flag: bool, manifest_path: Path) -> int:
    changed_cli = changed_with_prefix(changed_files, "cli")
    violations: list[Violation] = []
    current_surface = build_cli_surface()
    snapshot = load_json(snapshot_path)
    diff = {
        "added_groups": sorted(set(current_surface) - set(snapshot)),
        "removed_groups": sorted(set(snapshot) - set(current_surface)),
        "changed_groups": [],
    }
    for group in sorted(set(current_surface) & set(snapshot)):
        if current_surface[group] != snapshot[group]:
            diff["changed_groups"].append(group)
    if diff["added_groups"] or diff["removed_groups"] or diff["changed_groups"]:
        violations.append(Violation("cli-governance", "cli_surface_drift", "cli/ll.py", "CLI surface differs from the committed snapshot."))
    tests = load_json(manifest_path)["cli_tests"]
    report = build_report("cli-governance", violations, {"changed_files": changed_cli, "tests_run": []})
    if run_tests_flag and changed_cli:
        exit_code, payload = run_pytest(tests, output_dir / "cli-governance-pytest-report.json")
        report["tests_run"] = payload["tests"]
        if exit_code != 0:
            violations.append(Violation("cli-governance", "targeted_test_failure", "cli", "CLI governance tests failed."))
            report = build_report("cli-governance", violations, {"changed_files": changed_cli, "tests_run": payload["tests"]})
    dump_json(output_dir / "cli-surface-snapshot.json", current_surface)
    dump_json(output_dir / "cli-surface-diff.json", diff)
    dump_json(output_dir / "cli-governance-report.json", report)
    return 1 if violations else 0


def check_cross_domain_compat(changed_files: list[str], output_dir: Path, manifest_path: Path, run_tests_flag: bool) -> int:
    manifest = load_json(manifest_path)
    violations: list[Violation] = []
    matched_rules: list[dict[str, Any]] = []
    impacted_tests: set[str] = set()
    governed_prefixes = tuple(manifest["governed_prefixes"])
    for rule in manifest["rules"]:
        matched = [path for path in changed_files if match_any(path, rule["patterns"])]
        if matched:
            matched_rules.append({"name": rule["name"], "matched_files": matched, "tests": rule["tests"]})
            impacted_tests.update(rule["tests"])
    unmatched_governed = [
        path for path in changed_files
        if path.startswith(governed_prefixes) and not any(path in item["matched_files"] for item in matched_rules)
    ]
    if unmatched_governed:
        for rel_path in unmatched_governed:
            violations.append(Violation("cross-domain-compat", "dependency_mapping_resolution_error", rel_path, "Governed path was not covered by dependency rules."))
    impacted_payload = {
        "changed_files": changed_files,
        "matched_rules": matched_rules,
        "impacted_tests": sorted(impacted_tests),
        "unmatched_governed_files": unmatched_governed,
    }
    dump_json(output_dir / "impacted-dependency-chain.json", impacted_payload)
    report = build_report("cross-domain-compat", violations, {"tests_run": []})
    if run_tests_flag and impacted_tests and not violations:
        exit_code, payload = run_pytest(sorted(impacted_tests), output_dir / "cross-domain-pytest-report.json")
        report["tests_run"] = payload["tests"]
        if exit_code != 0:
            violations.append(Violation("cross-domain-compat", "cross_domain_smoke_failed", "tests", "Cross-domain compatibility smoke tests failed."))
            report = build_report("cross-domain-compat", violations, {"tests_run": payload["tests"]})
    dump_json(output_dir / "cross-domain-compat-report.json", report)
    return 1 if violations else 0
