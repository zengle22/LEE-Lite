#!/usr/bin/env python3
"""
Shared helpers for the lite-native feat-to-tech runtime.
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
    "feat-freeze-bundle.md",
    "feat-freeze-bundle.json",
    "feat-review-report.json",
    "feat-acceptance-report.json",
    "feat-defect-list.json",
    "feat-freeze-gate.json",
    "handoff-to-feat-downstreams.json",
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
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized or "unspecified"


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


def guess_repo_root_from_input(input_path: Path) -> Path:
    parts = list(input_path.parts)
    for index, part in enumerate(parts):
        if part.lower() == "artifacts" and index > 0:
            return Path(*parts[:index])
    return input_path.parent


@dataclass
class FeatPackage:
    artifacts_dir: Path
    manifest: dict[str, Any]
    feat_json: dict[str, Any]
    feat_frontmatter: dict[str, Any]
    feat_markdown_body: str
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
        return str(
            self.feat_json.get("workflow_run_id")
            or self.manifest.get("run_id")
            or self.artifacts_dir.name
        )


def load_feat_package(artifacts_dir: Path) -> FeatPackage:
    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    return FeatPackage(
        artifacts_dir=artifacts_dir,
        manifest=load_json(artifacts_dir / "package-manifest.json"),
        feat_json=load_json(artifacts_dir / "feat-freeze-bundle.json"),
        feat_frontmatter=frontmatter,
        feat_markdown_body=body,
        review_report=load_json(artifacts_dir / "feat-review-report.json"),
        acceptance_report=load_json(artifacts_dir / "feat-acceptance-report.json"),
        defect_list=load_json(artifacts_dir / "feat-defect-list.json"),
        execution_evidence=load_json(artifacts_dir / "execution-evidence.json"),
        supervision_evidence=load_json(artifacts_dir / "supervision-evidence.json"),
        gate=load_json(artifacts_dir / "feat-freeze-gate.json"),
        handoff=load_json(artifacts_dir / "handoff-to-feat-downstreams.json"),
        semantic_lock=normalize_semantic_lock(load_json(artifacts_dir / "feat-freeze-bundle.json").get("semantic_lock")),
    )


def find_feature(package: FeatPackage, feat_ref: str) -> dict[str, Any] | None:
    target = feat_ref.strip()
    for feature in package.feat_json.get("features") or []:
        if isinstance(feature, dict) and str(feature.get("feat_ref") or "").strip() == target:
            return feature
    return None


def validate_input_package(artifacts_dir: Path, feat_ref: str) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_INPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")

    if not feat_ref.strip():
        errors.append("feat_ref is required.")

    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_feat_package(artifacts_dir)
    errors.extend(semantic_lock_errors(package.feat_json.get("semantic_lock")))

    artifact_type = str(package.feat_json.get("artifact_type") or "")
    if artifact_type != "feat_freeze_package":
        errors.append(
            f"feat-freeze-bundle.json artifact_type must be feat_freeze_package, got: {artifact_type or '<missing>'}"
        )

    workflow_key = str(package.feat_json.get("workflow_key") or package.gate.get("workflow_key") or "")
    if workflow_key != "product.epic-to-feat":
        errors.append(f"Upstream workflow must be product.epic-to-feat, got: {workflow_key or '<missing>'}")

    status = str(package.feat_json.get("status") or package.manifest.get("status") or "")
    if status not in {"accepted", "frozen"}:
        errors.append(f"feat-freeze status must be accepted or frozen, got: {status or '<missing>'}")

    if package.gate.get("freeze_ready") is not True:
        errors.append("feat-freeze-gate.json must mark the package as freeze_ready.")

    feature = find_feature(package, feat_ref)
    if feature is None:
        errors.append(f"Selected feat_ref not found in feat-freeze-bundle.json: {feat_ref}")
    else:
        for field in ["feat_ref", "title", "goal", "scope", "constraints", "acceptance_checks", "source_refs"]:
            if feature.get(field) in (None, "", []):
                errors.append(f"Selected feature is missing required field: {field}")
        if len(feature.get("acceptance_checks") or []) < 3:
            errors.append(f"{feat_ref} must include at least three acceptance checks.")

    source_refs = ensure_list(package.feat_json.get("source_refs"))
    if not any(ref.startswith("EPIC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include EPIC-*.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include SRC-*.")
    derivable_children = ensure_list(package.handoff.get("derivable_children"))
    if "TECH" not in derivable_children:
        errors.append("handoff-to-feat-downstreams.json must include TECH in derivable_children.")

    result = {
        "valid": not errors,
        "run_id": package.run_id,
        "workflow_key": workflow_key,
        "status": status,
        "feat_ref": feat_ref,
        "feat_title": str((feature or {}).get("title") or ""),
        "epic_freeze_ref": package.feat_json.get("epic_freeze_ref"),
        "src_root_id": package.feat_json.get("src_root_id"),
        "source_refs": source_refs,
        "semantic_lock": package.semantic_lock,
    }
    return errors, result
