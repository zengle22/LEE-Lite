#!/usr/bin/env python3
"""Shared helpers for ll-gate-human-orchestrator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GateReadyPackage:
    artifacts_dir: Path
    package_path: Path
    payload: dict[str, Any]
    trace: dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        chars.append(char if char.isalnum() else "-")
    return "".join(chars).strip("-") or "gate"


def guess_repo_root_from_input(input_path: Path) -> Path:
    current = input_path.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "cli").exists() or (candidate / "skills").exists():
            return candidate
    return input_path.resolve().parents[-1]


def package_file_from_input(input_path: Path) -> Path:
    resolved = input_path.resolve()
    if resolved.is_dir():
        return resolved / "gate-ready-package.json"
    return resolved


def load_gate_ready_package(input_path: Path) -> GateReadyPackage:
    package_path = package_file_from_input(input_path)
    payload = load_json(package_path)
    body = payload.get("payload", {})
    if not isinstance(body, dict):
        body = {}
    trace = payload.get("trace", {})
    if not isinstance(trace, dict):
        trace = {}
    return GateReadyPackage(
        artifacts_dir=package_path.parent,
        package_path=package_path,
        payload=body,
        trace=trace,
    )


def validate_input_package(input_path: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    package_path = package_file_from_input(input_path)
    if not package_path.exists():
        return [f"gate-ready-package not found: {package_path}"], {"input_path": str(input_path), "package_path": str(package_path)}

    package = load_gate_ready_package(input_path)
    for field in ("candidate_ref", "machine_ssot_ref", "acceptance_ref", "evidence_bundle_ref"):
        if not str(package.payload.get(field, "")).strip():
            errors.append(f"missing payload field: {field}")

    result = {
        "input_path": str(input_path.resolve()),
        "package_path": str(package.package_path),
        "artifacts_dir": str(package.artifacts_dir),
        "candidate_ref": str(package.payload.get("candidate_ref", "")),
        "machine_ssot_ref": str(package.payload.get("machine_ssot_ref", "")),
        "acceptance_ref": str(package.payload.get("acceptance_ref", "")),
        "evidence_bundle_ref": str(package.payload.get("evidence_bundle_ref", "")),
    }
    return errors, result


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"{key}: {value}")
    lines.extend(["---", "", body.rstrip(), ""])
    return "\n".join(lines)
