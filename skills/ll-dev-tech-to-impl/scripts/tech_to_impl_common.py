#!/usr/bin/env python3
"""
Shared helpers for the lite-native tech-to-impl runtime.
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
    "tech-design-bundle.md",
    "tech-design-bundle.json",
    "tech-spec.md",
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


def validate_input_package(artifacts_dir: Path, feat_ref: str, tech_ref: str) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_INPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")

    if not feat_ref.strip():
        errors.append("feat_ref is required.")
    if not tech_ref.strip():
        errors.append("tech_ref is required.")
    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_tech_package(artifacts_dir)
    bundle = package.tech_json
    errors.extend(semantic_lock_errors(bundle.get("semantic_lock")))
    selected_feat = package.selected_feat

    artifact_type = str(bundle.get("artifact_type") or "")
    if artifact_type != "tech_design_package":
        errors.append(f"tech-design-bundle.json artifact_type must be tech_design_package, got: {artifact_type or '<missing>'}")

    workflow_key = str(bundle.get("workflow_key") or package.gate.get("workflow_key") or "")
    if workflow_key != "dev.feat-to-tech":
        errors.append(f"Upstream workflow must be dev.feat-to-tech, got: {workflow_key or '<missing>'}")

    status = str(bundle.get("status") or package.manifest.get("status") or "")
    if status not in {"accepted", "frozen"}:
        errors.append(f"tech-design status must be accepted or frozen, got: {status or '<missing>'}")

    if package.gate.get("freeze_ready") is not True:
        errors.append("tech-freeze-gate.json must mark the package as freeze_ready.")

    if package.feat_ref != feat_ref.strip():
        errors.append(f"Selected feat_ref does not match tech-design-bundle.json: {feat_ref}")
    if package.tech_ref != tech_ref.strip():
        errors.append(f"Selected tech_ref does not match tech-design-bundle.json: {tech_ref}")

    selected_feat_ref = str(selected_feat.get("feat_ref") or "").strip()
    if selected_feat_ref and selected_feat_ref != feat_ref.strip():
        errors.append("selected_feat.feat_ref must match the selected feat_ref.")
    for field in ["title", "goal", "scope", "constraints"]:
        if selected_feat.get(field) in (None, "", []):
            errors.append(f"selected_feat is missing required field: {field}")

    source_refs = ensure_list(bundle.get("source_refs"))
    for prefix in ["FEAT-", "EPIC-", "SRC-"]:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"tech-design-bundle.json source_refs must include {prefix}.")
    if tech_ref.strip() not in source_refs and package.tech_ref not in source_refs:
        errors.append("tech-design-bundle.json source_refs must retain the selected TECH ref.")

    if bool(bundle.get("arch_required")):
        if not package.arch_ref:
            errors.append("arch_required is true but arch_ref is missing.")
        if not (artifacts_dir / "arch-design.md").exists():
            errors.append("arch_required is true but arch-design.md is missing.")
    if bool(bundle.get("api_required")):
        if not package.api_ref:
            errors.append("api_required is true but api_ref is missing.")
        if not (artifacts_dir / "api-contract.md").exists():
            errors.append("api_required is true but api-contract.md is missing.")

    if str(package.handoff.get("target_workflow") or "") != "workflow.dev.tech_to_impl":
        errors.append("handoff-to-tech-impl.json must preserve workflow.dev.tech_to_impl lineage.")

    axis_markers = [
        str(selected_feat.get("resolved_axis") or "").strip().lower(),
        str(selected_feat.get("axis_id") or "").strip().lower(),
        str(selected_feat.get("track") or "").strip().lower(),
    ]
    is_adr007_adoption = "ADR-007" in source_refs and any(
        marker in {"adoption_e2e", "skill-adoption-e2e"} for marker in axis_markers if marker
    )
    if is_adr007_adoption:
        tech_design = bundle.get("tech_design") or {}
        implementation_rules = ensure_list(tech_design.get("implementation_rules")) if isinstance(tech_design, dict) else []
        inherited_text = "\n".join(implementation_rules + ensure_list(selected_feat.get("constraints")))
        required_family_markers = [
            "skill.qa.test_exec_web_e2e",
            "skill.qa.test_exec_cli",
            "skill.runner.test_e2e",
            "skill.runner.test_cli",
        ]
        missing_family_markers = [marker for marker in required_family_markers if marker not in inherited_text]
        if missing_family_markers:
            errors.append(
                "ADR-007 adoption_e2e TECH must preserve the full test execution family markers: "
                + ", ".join(missing_family_markers)
            )

    result = {
        "valid": not errors,
        "run_id": package.run_id,
        "workflow_key": workflow_key,
        "status": status,
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "arch_ref": package.arch_ref,
        "api_ref": package.api_ref,
        "feat_title": str(selected_feat.get("title") or ""),
        "source_refs": source_refs,
        "semantic_lock": package.semantic_lock,
    }
    return errors, result

