#!/usr/bin/env python3
"""
Input resolution and validation helpers for feat-to-tech.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from feat_to_tech_common import (
    REQUIRED_INPUT_FILES,
    ensure_list,
    load_json,
    normalize_semantic_lock,
    parse_markdown_frontmatter,
    semantic_lock_errors,
)
from feat_to_tech_integration_context import (
    INTEGRATION_CONTEXT_FILENAME,
    integration_context_errors,
    integration_context_ref,
    load_integration_context,
)


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
    admission = validate_admission(repo_root, consumer_ref="dev.feat-to-tech", requested_ref=requested_ref)
    record = resolve_registry_record(repo_root, requested_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    if not source_package_ref:
        raise ValueError("formal feat record is missing metadata.source_package_ref")
    artifacts_dir = canonical_to_path(source_package_ref, repo_root)
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        raise FileNotFoundError(f"resolved feat package directory not found: {artifacts_dir}")
    return artifacts_dir.resolve(), {
        "input_mode": "formal_admission",
        "requested_ref": requested_ref,
        "resolved_formal_ref": admission["resolved_formal_ref"],
        "managed_artifact_ref": record.get("managed_artifact_ref", ""),
        "resolved_feat_ref": str(metadata.get("feat_ref") or metadata.get("assigned_id") or "").strip(),
    }


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
    integration_context: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(self.feat_json.get("workflow_run_id") or self.manifest.get("run_id") or self.artifacts_dir.name)


def load_feat_package(artifacts_dir: Path) -> FeatPackage:
    feat_json = load_json(artifacts_dir / "feat-freeze-bundle.json")
    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    return FeatPackage(
        artifacts_dir=artifacts_dir,
        manifest=load_json(artifacts_dir / "package-manifest.json"),
        feat_json=feat_json,
        feat_frontmatter=frontmatter,
        feat_markdown_body=body,
        review_report=load_json(artifacts_dir / "feat-review-report.json"),
        acceptance_report=load_json(artifacts_dir / "feat-acceptance-report.json"),
        defect_list=load_json(artifacts_dir / "feat-defect-list.json"),
        execution_evidence=load_json(artifacts_dir / "execution-evidence.json"),
        supervision_evidence=load_json(artifacts_dir / "supervision-evidence.json"),
        gate=load_json(artifacts_dir / "feat-freeze-gate.json"),
        handoff=load_json(artifacts_dir / "handoff-to-feat-downstreams.json"),
        semantic_lock=normalize_semantic_lock(feat_json.get("semantic_lock")),
        integration_context=load_integration_context(artifacts_dir, load_json, feat_json),
    )


def find_feature(package: FeatPackage, feat_ref: str) -> dict[str, Any] | None:
    target = feat_ref.strip()
    for feature in package.feat_json.get("features") or []:
        if isinstance(feature, dict) and str(feature.get("feat_ref") or "").strip() == target:
            return feature
    return None


def validate_input_package(input_value: str | Path, feat_ref: str, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    artifacts_dir, input_resolution = resolve_input_artifacts_dir(input_value, repo_root)
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    required_files = list(REQUIRED_INPUT_FILES)
    if INTEGRATION_CONTEXT_FILENAME not in required_files:
        required_files.append(INTEGRATION_CONTEXT_FILENAME)
    for required_file in required_files:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")

    effective_feat_ref = feat_ref.strip() or str(input_resolution.get("resolved_feat_ref") or "").strip()
    if not effective_feat_ref:
        errors.append("feat_ref is required.")
    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_feat_package(artifacts_dir)
    errors.extend(semantic_lock_errors(package.feat_json.get("semantic_lock")))
    errors.extend(integration_context_errors(package.integration_context))

    artifact_type = str(package.feat_json.get("artifact_type") or "")
    if artifact_type != "feat_freeze_package":
        errors.append(f"feat-freeze-bundle.json artifact_type must be feat_freeze_package, got: {artifact_type or '<missing>'}")
    workflow_key = str(package.feat_json.get("workflow_key") or package.gate.get("workflow_key") or "")
    if workflow_key != "product.epic-to-feat":
        errors.append(f"Upstream workflow must be product.epic-to-feat, got: {workflow_key or '<missing>'}")
    status = str(package.feat_json.get("status") or package.manifest.get("status") or "")
    if status not in {"accepted", "frozen"}:
        errors.append(f"feat-freeze status must be accepted or frozen, got: {status or '<missing>'}")
    if package.gate.get("freeze_ready") is not True:
        errors.append("feat-freeze-gate.json must mark the package as freeze_ready.")

    feature = find_feature(package, effective_feat_ref)
    if feature is None:
        errors.append(f"Selected feat_ref not found in feat-freeze-bundle.json: {effective_feat_ref}")
    else:
        for field in ["feat_ref", "title", "goal", "scope", "constraints", "acceptance_checks", "source_refs"]:
            if feature.get(field) in (None, "", []):
                errors.append(f"Selected feature is missing required field: {field}")
        if len(feature.get("acceptance_checks") or []) < 3:
            errors.append(f"{effective_feat_ref} must include at least three acceptance checks.")

    source_refs = ensure_list(package.feat_json.get("source_refs"))
    if not any(ref.startswith("EPIC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include EPIC-*.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include SRC-*.")
    derivable_children = ensure_list(package.handoff.get("derivable_children"))
    if "TECH" not in derivable_children:
        errors.append("handoff-to-feat-downstreams.json must include TECH in derivable_children.")

    return errors, {
        "valid": not errors,
        "run_id": package.run_id,
        "workflow_key": workflow_key,
        "status": status,
        "input_mode": input_resolution.get("input_mode", "package_dir"),
        "feat_ref": effective_feat_ref,
        "feat_title": str((feature or {}).get("title") or ""),
        "epic_freeze_ref": package.feat_json.get("epic_freeze_ref"),
        "src_root_id": package.feat_json.get("src_root_id"),
        "source_refs": source_refs,
        "integration_context_ref": integration_context_ref(package.integration_context),
        "integration_context_present": bool(package.integration_context),
    }
