#!/usr/bin/env python3
"""
Shared helpers for the lite-native src-to-epic runtime.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_INPUT_FILES = [
    "package-manifest.json",
    "src-candidate.md",
    "src-candidate.json",
    "structural-report.json",
    "source-semantic-findings.json",
    "acceptance-report.json",
    "result-summary.json",
    "proposed-next-actions.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_markdown_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    if not markdown_text.startswith("---\n"):
        return {}, markdown_text
    end_marker = "\n---\n"
    end_index = markdown_text.find(end_marker, 4)
    if end_index == -1:
        return {}, markdown_text
    frontmatter_text = markdown_text[4:end_index]
    body = markdown_text[end_index + len(end_marker) :]
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        return {}, body
    return data, body


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized or "UNSPECIFIED"


def shorten_identifier(value: str, limit: int = 48) -> str:
    slug = slugify(value)
    if len(slug) <= limit:
        return slug
    head = slug[: limit - 9].rstrip("-")
    tail = slug[-8:]
    return f"{head}-{tail}"


def summarize_text(value: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def guess_repo_root_from_input(input_path: Path) -> Path:
    parts = list(input_path.parts)
    for index, part in enumerate(parts):
        if part.lower() == "artifacts" and index > 0:
            return Path(*parts[:index])
    return input_path.parent


@dataclass
class SrcPackage:
    artifacts_dir: Path
    manifest: dict[str, Any]
    result_summary: dict[str, Any]
    src_candidate: dict[str, Any]
    src_frontmatter: dict[str, Any]
    src_markdown_body: str
    source_semantic_findings: dict[str, Any]
    acceptance_report: dict[str, Any]
    execution_evidence: dict[str, Any]
    supervision_evidence: dict[str, Any]
    proposed_next_actions: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(
            self.manifest.get("run_id")
            or self.src_candidate.get("workflow_run_id")
            or self.result_summary.get("run_id")
            or self.artifacts_dir.name
        )


def load_src_package(artifacts_dir: Path) -> SrcPackage:
    markdown_text = (artifacts_dir / "src-candidate.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    return SrcPackage(
        artifacts_dir=artifacts_dir,
        manifest=load_json(artifacts_dir / "package-manifest.json"),
        result_summary=load_json(artifacts_dir / "result-summary.json"),
        src_candidate=load_json(artifacts_dir / "src-candidate.json"),
        src_frontmatter=frontmatter,
        src_markdown_body=body,
        source_semantic_findings=load_json(artifacts_dir / "source-semantic-findings.json"),
        acceptance_report=load_json(artifacts_dir / "acceptance-report.json"),
        execution_evidence=load_json(artifacts_dir / "execution-evidence.json"),
        supervision_evidence=load_json(artifacts_dir / "supervision-evidence.json"),
        proposed_next_actions=load_json(artifacts_dir / "proposed-next-actions.json"),
    )


def validate_input_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_INPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")

    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_src_package(artifacts_dir)

    manifest_status = str(package.manifest.get("status", "")).strip()
    if manifest_status != "freeze_ready":
        errors.append(f"package-manifest.json status must be freeze_ready, got: {manifest_status or '<missing>'}")

    workflow_key = str(package.result_summary.get("workflow_key") or package.src_candidate.get("workflow_key") or "")
    if workflow_key != "product.raw-to-src":
        errors.append(f"Upstream workflow must be product.raw-to-src, got: {workflow_key or '<missing>'}")

    recommended_target = str(package.result_summary.get("recommended_target_skill") or "")
    if recommended_target and recommended_target != "product.src-to-epic":
        errors.append(f"recommended_target_skill must be product.src-to-epic when present, got: {recommended_target}")

    source_refs = ensure_list(package.src_candidate.get("source_refs"))
    if not source_refs:
        errors.append("src-candidate.json must include source_refs.")

    required_fields = [
        "artifact_type",
        "workflow_key",
        "workflow_run_id",
        "title",
        "status",
        "source_kind",
        "source_refs",
        "problem_statement",
        "target_users",
        "trigger_scenarios",
        "business_drivers",
        "key_constraints",
        "in_scope",
        "out_of_scope",
    ]
    for field in required_fields:
        if package.src_candidate.get(field) in (None, "", []):
            errors.append(f"src-candidate.json is missing required field: {field}")

    result = {
        "valid": not errors,
        "manifest_status": manifest_status,
        "workflow_key": workflow_key,
        "run_id": package.run_id,
        "source_refs": source_refs,
        "recommended_target_skill": recommended_target,
    }
    return errors, result
