#!/usr/bin/env python3
"""
Shared helpers for the lite-native tech-to-impl runtime.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_INPUT_FILES = [
    "package-manifest.json",
    "tech-design-bundle.md",
    "tech-design-bundle.json",
    "tech-spec.md",
    "integration-context.json",
    "tech-review-report.json",
    "tech-acceptance-report.json",
    "tech-defect-list.json",
    "tech-freeze-gate.json",
    "handoff-to-tech-impl.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_semantic_lock(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    lock = {
        "domain_type": str(payload.get("domain_type") or "").strip(),
        "one_sentence_truth": str(payload.get("one_sentence_truth") or "").strip(),
        "primary_object": str(payload.get("primary_object") or "").strip(),
        "lifecycle_stage": str(payload.get("lifecycle_stage") or "").strip(),
        "allowed_capabilities": ensure_list(payload.get("allowed_capabilities")),
        "forbidden_capabilities": ensure_list(payload.get("forbidden_capabilities")),
        "inheritance_rule": str(payload.get("inheritance_rule") or "").strip(),
    }
    return {key: value for key, value in lock.items() if value not in ("", [], None)}


def semantic_lock_errors(payload: Any) -> list[str]:
    lock = normalize_semantic_lock(payload)
    if not lock:
        return []
    required_fields = [
        "domain_type",
        "one_sentence_truth",
        "primary_object",
        "lifecycle_stage",
        "inheritance_rule",
    ]
    errors = [field for field in required_fields if not str(lock.get(field) or "").strip()]
    if not ensure_list(lock.get("allowed_capabilities")):
        errors.append("allowed_capabilities")
    if not ensure_list(lock.get("forbidden_capabilities")):
        errors.append("forbidden_capabilities")
    return [f"semantic_lock missing required field: {field}" for field in errors]


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized or "unspecified"


def guess_repo_root_from_input(input_path: Path) -> Path:
    parts = list(input_path.parts)
    for index, part in enumerate(parts):
        if part.lower() == "artifacts" and index > 0:
            return Path(*parts[:index])
    return input_path.parent


def resolve_input_artifacts_dir(input_value: str | Path, repo_root: Path) -> tuple[Path, dict[str, Any]]:
    candidate_path = Path(str(input_value))
    if candidate_path.exists() and candidate_path.is_dir():
        return candidate_path.resolve(), {"input_mode": "package_dir", "requested_ref": str(candidate_path.resolve())}

    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.lib.admission import validate_admission
    from cli.lib.fs import canonical_to_path
    from cli.lib.registry_store import resolve_registry_record

    requested_ref = str(input_value)
    admission = validate_admission(
        repo_root,
        consumer_ref="dev.tech-to-impl",
        requested_ref=requested_ref,
    )
    record = resolve_registry_record(repo_root, requested_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    if not source_package_ref:
        raise ValueError("formal tech record is missing metadata.source_package_ref")
    artifacts_dir = canonical_to_path(source_package_ref, repo_root)
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        raise FileNotFoundError(f"resolved tech package directory not found: {artifacts_dir}")
    return artifacts_dir.resolve(), {
        "input_mode": "formal_admission",
        "requested_ref": requested_ref,
        "resolved_formal_ref": admission["resolved_formal_ref"],
        "managed_artifact_ref": record.get("managed_artifact_ref", ""),
        "resolved_feat_ref": str(metadata.get("feat_ref") or "").strip(),
        "resolved_tech_ref": str(metadata.get("tech_ref") or metadata.get("assigned_id") or "").strip(),
    }


@dataclass
class TechPackage:
    artifacts_dir: Path
    manifest: dict[str, Any]
    tech_json: dict[str, Any]
    tech_frontmatter: dict[str, Any]
    tech_markdown_body: str
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    execution_evidence: dict[str, Any]
    supervision_evidence: dict[str, Any]
    gate: dict[str, Any]
    handoff: dict[str, Any]
    semantic_lock: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(self.tech_json.get("workflow_run_id") or self.manifest.get("run_id") or self.artifacts_dir.name)

    @property
    def feat_ref(self) -> str:
        return str(self.tech_json.get("feat_ref") or "").strip()

    @property
    def tech_ref(self) -> str:
        return str(self.tech_json.get("tech_ref") or "").strip()

    @property
    def arch_ref(self) -> str | None:
        value = str(self.tech_json.get("arch_ref") or "").strip()
        return value or None

    @property
    def api_ref(self) -> str | None:
        value = str(self.tech_json.get("api_ref") or "").strip()
        return value or None

    @property
    def selected_feat(self) -> dict[str, Any]:
        selected = self.tech_json.get("selected_feat") or {}
        return selected if isinstance(selected, dict) else {}

    @property
    def integration_context(self) -> dict[str, Any]:
        payload = self.tech_json.get("integration_context") or {}
        return payload if isinstance(payload, dict) else {}


def load_tech_package(artifacts_dir: Path) -> TechPackage:
    markdown_text = (artifacts_dir / "tech-design-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    return TechPackage(
        artifacts_dir=artifacts_dir,
        manifest=load_json(artifacts_dir / "package-manifest.json"),
        tech_json=load_json(artifacts_dir / "tech-design-bundle.json"),
        tech_frontmatter=frontmatter,
        tech_markdown_body=body,
        review_report=load_json(artifacts_dir / "tech-review-report.json"),
        acceptance_report=load_json(artifacts_dir / "tech-acceptance-report.json"),
        defect_list=load_json(artifacts_dir / "tech-defect-list.json"),
        execution_evidence=load_json(artifacts_dir / "execution-evidence.json"),
        supervision_evidence=load_json(artifacts_dir / "supervision-evidence.json"),
        gate=load_json(artifacts_dir / "tech-freeze-gate.json"),
        handoff=load_json(artifacts_dir / "handoff-to-tech-impl.json"),
        semantic_lock=normalize_semantic_lock(load_json(artifacts_dir / "tech-design-bundle.json").get("semantic_lock")),
    )


def validate_input_package(input_value: str | Path, feat_ref: str, tech_ref: str, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    from tech_to_impl_validation import validate_input_package as _validate_input_package

    return _validate_input_package(input_value, feat_ref, tech_ref, repo_root)

