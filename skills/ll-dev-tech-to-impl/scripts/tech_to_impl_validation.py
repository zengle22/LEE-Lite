#!/usr/bin/env python3
"""
Input validation helpers for tech-to-impl.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tech_to_impl_common import ensure_list, load_tech_package, resolve_input_artifacts_dir, semantic_lock_errors


def validate_input_package(input_value: str | Path, feat_ref: str, tech_ref: str, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    artifacts_dir, input_resolution = resolve_input_artifacts_dir(input_value, repo_root)
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    errors.extend(check_required_files(artifacts_dir))
    effective_feat_ref = feat_ref.strip() or str(input_resolution.get("resolved_feat_ref") or "").strip()
    effective_tech_ref = tech_ref.strip() or str(input_resolution.get("resolved_tech_ref") or "").strip()
    if not effective_feat_ref:
        errors.append("feat_ref is required.")
    if not effective_tech_ref:
        errors.append("tech_ref is required.")
    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_tech_package(artifacts_dir)
    bundle = package.tech_json
    errors.extend(semantic_lock_errors(bundle.get("semantic_lock")))
    selected_feat = package.selected_feat

    errors.extend(check_bundle_identity(bundle))
    errors.extend(check_selected_refs(package, selected_feat, effective_feat_ref, effective_tech_ref))
    errors.extend(check_selected_feat_fields(selected_feat))
    errors.extend(check_provisional_inputs(selected_feat))
    errors.extend(check_source_refs(bundle, package, effective_tech_ref))
    errors.extend(check_optional_refs(bundle, package))
    errors.extend(check_handoff_lineage(package))
    errors.extend(check_adr007_family_markers(bundle, selected_feat, package, effective_feat_ref))

    result = {
        "valid": not errors,
        "run_id": package.run_id,
        "workflow_key": str(bundle.get("workflow_key") or package.gate.get("workflow_key") or ""),
        "status": str(bundle.get("status") or package.manifest.get("status") or ""),
        "feat_ref": effective_feat_ref,
        "tech_ref": effective_tech_ref,
        "arch_ref": package.arch_ref,
        "api_ref": package.api_ref,
        "feat_title": str(selected_feat.get("title") or ""),
        "source_refs": ensure_list(bundle.get("source_refs")),
        "semantic_lock": package.semantic_lock,
        "input_mode": input_resolution.get("input_mode", "package_dir"),
    }
    return errors, result


def check_required_files(artifacts_dir: Path) -> list[str]:
    from tech_to_impl_common import REQUIRED_INPUT_FILES

    errors: list[str] = []
    for required_file in REQUIRED_INPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")
    return errors


def check_bundle_identity(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if str(bundle.get("artifact_type") or "") != "tech_design_package":
        errors.append(
            f"tech-design-bundle.json artifact_type must be tech_design_package, got: {str(bundle.get('artifact_type') or '<missing>')}"
        )
    if str(bundle.get("workflow_key") or "") != "dev.feat-to-tech":
        errors.append(
            f"Upstream workflow must be dev.feat-to-tech, got: {str(bundle.get('workflow_key') or '<missing>')}"
        )
    return errors


def check_selected_refs(package: Any, selected_feat: dict[str, Any], effective_feat_ref: str, effective_tech_ref: str) -> list[str]:
    errors: list[str] = []
    if package.feat_ref != effective_feat_ref:
        errors.append(f"Selected feat_ref does not match tech-design-bundle.json: {effective_feat_ref}")
    if package.tech_ref != effective_tech_ref:
        errors.append(f"Selected tech_ref does not match tech-design-bundle.json: {effective_tech_ref}")
    selected_feat_ref = str(selected_feat.get("feat_ref") or "").strip()
    if selected_feat_ref and selected_feat_ref != effective_feat_ref:
        errors.append("selected_feat.feat_ref must match the selected feat_ref.")
    return errors


def check_selected_feat_fields(selected_feat: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["title", "goal", "scope", "constraints"]:
        if selected_feat.get(field) in (None, "", []):
            errors.append(f"selected_feat is missing required field: {field}")
    return errors


def check_provisional_inputs(selected_feat: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    raw_provisional_refs = selected_feat.get("provisional_refs")
    provisional_refs = raw_provisional_refs if isinstance(raw_provisional_refs, list) else ensure_list(raw_provisional_refs)
    for item in provisional_refs:
        if isinstance(item, dict):
            if not str(item.get("ref") or "").strip():
                errors.append("selected_feat provisional_refs entries must include ref.")
            if not str(item.get("follow_up_action") or "").strip():
                errors.append("selected_feat provisional_refs entries must include follow_up_action.")
        elif not str(item).strip():
            errors.append("selected_feat provisional_refs entries must be non-empty.")
    return errors


def check_source_refs(bundle: dict[str, Any], package: Any, effective_tech_ref: str) -> list[str]:
    errors: list[str] = []
    source_refs = ensure_list(bundle.get("source_refs"))
    for prefix in ["FEAT-", "EPIC-", "SRC-"]:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"tech-design-bundle.json source_refs must include {prefix}.")
    if effective_tech_ref not in source_refs and package.tech_ref not in source_refs:
        errors.append("tech-design-bundle.json source_refs must retain the selected TECH ref.")
    return errors


def check_optional_refs(bundle: dict[str, Any], package: Any) -> list[str]:
    errors: list[str] = []
    if bool(bundle.get("arch_required")):
        if not package.arch_ref:
            errors.append("arch_required is true but arch_ref is missing.")
    if bool(bundle.get("api_required")):
        if not package.api_ref:
            errors.append("api_required is true but api_ref is missing.")
    return errors


def check_handoff_lineage(package: Any) -> list[str]:
    if str(package.handoff.get("target_workflow") or "") != "workflow.dev.tech_to_impl":
        return ["handoff-to-tech-impl.json must preserve workflow.dev.tech_to_impl lineage."]
    return []


def check_adr007_family_markers(
    bundle: dict[str, Any],
    selected_feat: dict[str, Any],
    package: Any,
    effective_feat_ref: str,
) -> list[str]:
    source_refs = ensure_list(bundle.get("source_refs"))
    axis_markers = [
        str(selected_feat.get("resolved_axis") or "").strip().lower(),
        str(selected_feat.get("axis_id") or "").strip().lower(),
        str(selected_feat.get("track") or "").strip().lower(),
    ]
    is_adr007_adoption = "ADR-007" in source_refs and any(marker in {"adoption_e2e", "skill-adoption-e2e"} for marker in axis_markers if marker)
    if not is_adr007_adoption:
        return []

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
        return [
            "ADR-007 adoption_e2e TECH must preserve the full test execution family markers: "
            + ", ".join(missing_family_markers)
        ]
    return []
