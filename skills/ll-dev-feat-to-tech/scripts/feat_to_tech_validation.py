#!/usr/bin/env python3
"""
Validation helpers for feat-to-tech output packages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from feat_to_tech_common import ensure_list, load_json, parse_markdown_frontmatter

REQUIRED_OUTPUT_FILES = [
    "tech-design-bundle.md",
    "tech-design-bundle.json",
    "tech-spec.md",
    "tech-review-report.json",
    "tech-acceptance-report.json",
    "tech-defect-list.json",
    "tech-freeze-gate.json",
    "handoff-to-tech-impl.json",
    "semantic-drift-check.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
REQUIRED_MARKDOWN_HEADINGS = [
    "Selected FEAT",
    "Need Assessment",
    "TECH Design",
    "Optional ARCH",
    "Optional API",
    "Cross-Artifact Consistency",
    "Downstream Handoff",
    "Traceability",
]
REQUIRED_TECH_SUBHEADINGS = [
    "### Implementation Carrier View",
    "### State Model",
    "### Module Plan",
    "### Implementation Strategy",
    "### Implementation Unit Mapping",
    "### Interface Contracts",
    "### Main Sequence",
    "### Exception and Compensation",
    "### Integration Points",
    "### Minimal Code Skeleton",
]
REQUIRED_API_HEADINGS = [
    "## Contract Scope",
    "## Response Envelope",
    "## Command Contracts",
    "## Compatibility and Versioning",
]
DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_OUTPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required output artifact: {required_file}")
    if errors:
        return errors, {"valid": False}

    bundle_json = load_json(artifacts_dir / "tech-design-bundle.json")
    validate_bundle_identity(errors, bundle_json)
    feat_ref = str(bundle_json.get("feat_ref") or "")
    tech_ref = str(bundle_json.get("tech_ref") or "")
    validate_source_refs(errors, bundle_json)
    validate_artifact_refs(errors, bundle_json)
    arch_required = bool(bundle_json.get("arch_required"))
    api_required = bool(bundle_json.get("api_required"))
    validate_optional_outputs(errors, artifacts_dir, arch_required, api_required)
    validate_consistency_sections(errors, artifacts_dir, bundle_json)
    validate_handoff(errors, artifacts_dir)
    validate_adr007_adoption(errors, bundle_json)
    return errors, {
        "valid": not errors,
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "arch_required": arch_required,
        "api_required": api_required,
        "semantic_lock_preserved": load_json(artifacts_dir / "semantic-drift-check.json").get("semantic_lock_preserved", True),
    }


def validate_bundle_identity(errors, bundle_json):
    if bundle_json.get("artifact_type") != "tech_design_package":
        errors.append("tech-design-bundle.json artifact_type must be tech_design_package.")
    if bundle_json.get("workflow_key") != "dev.feat-to-tech":
        errors.append("tech-design-bundle.json workflow_key must be dev.feat-to-tech.")
    if not str(bundle_json.get("feat_ref") or ""):
        errors.append("tech-design-bundle.json must include feat_ref.")
    if not str(bundle_json.get("tech_ref") or ""):
        errors.append("tech-design-bundle.json must include tech_ref.")


def validate_source_refs(errors, bundle_json):
    source_refs = ensure_list(bundle_json.get("source_refs"))
    expected_prefixes = ["product.epic-to-feat::", "FEAT-", "TECH-", "EPIC-", "SRC-"]
    messages = {
        "product.epic-to-feat::": "product.epic-to-feat::<run_id>",
        "FEAT-": "FEAT-*",
        "TECH-": "TECH-*",
        "EPIC-": "EPIC-*",
        "SRC-": "SRC-*",
    }
    for prefix in expected_prefixes:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"tech-design-bundle.json source_refs must include {messages[prefix]}.")


def validate_artifact_refs(errors, bundle_json):
    artifact_refs = bundle_json.get("artifact_refs") or {}
    if artifact_refs.get("tech_spec") != "tech-spec.md":
        errors.append("artifact_refs.tech_spec must point to tech-spec.md.")
    unexpected = [key for key in artifact_refs if key not in {"tech_spec", "arch_spec", "api_spec"}]
    if unexpected:
        errors.append(
            "artifact_refs may only contain tech_spec/arch_spec/api_spec; unexpected keys: " + ", ".join(sorted(unexpected))
        )


def validate_optional_outputs(errors, artifacts_dir, arch_required, api_required):
    arch_path = artifacts_dir / "arch-design.md"
    api_path = artifacts_dir / "api-contract.md"
    if arch_required and not arch_path.exists():
        errors.append("arch-design.md must exist when arch_required is true.")
    if not arch_required and arch_path.exists():
        errors.append("arch-design.md must not exist when arch_required is false.")
    if api_required and not api_path.exists():
        errors.append("api-contract.md must exist when api_required is true.")
    if not api_required and api_path.exists():
        errors.append("api-contract.md must not exist when api_required is false.")
    if api_required:
        api_body = api_path.read_text(encoding="utf-8")
        for heading in REQUIRED_API_HEADINGS:
            if heading not in api_body:
                errors.append(f"api-contract.md must contain heading: {heading}")


def validate_consistency_sections(errors, artifacts_dir, bundle_json):
    consistency = bundle_json.get("design_consistency_check")
    if not isinstance(consistency, dict):
        errors.append("tech-design-bundle.json must include design_consistency_check.")
    else:
        required_keys = {"passed", "structural_passed", "semantic_passed", "checks", "issues", "minor_open_items"}
        if not required_keys.issubset(set(consistency.keys())):
            errors.append("design_consistency_check must include passed/structural_passed/semantic_passed/checks/issues/minor_open_items.")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    if bundle_json.get("semantic_lock") and semantic_drift_check.get("semantic_lock_preserved") is not True:
        errors.append("semantic-drift-check.json must preserve semantic_lock when semantic_lock is present.")
    markdown_text = (artifacts_dir / "tech-design-bundle.md").read_text(encoding="utf-8")
    _, markdown_body = parse_markdown_frontmatter(markdown_text)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if f"## {heading}" not in markdown_body:
            errors.append(f"tech-design-bundle.md is missing section: {heading}")
    for subheading in REQUIRED_TECH_SUBHEADINGS:
        if subheading not in markdown_body:
            errors.append(f"tech-design-bundle.md is missing TECH subsection: {subheading.replace('### ', '')}")
    if markdown_body.count("```text") < 2:
        errors.append("tech-design-bundle.md must include at least two ASCII diagrams for architecture and flow.")


def validate_handoff(errors, artifacts_dir):
    handoff = load_json(artifacts_dir / "handoff-to-tech-impl.json")
    if handoff.get("target_workflow") != DOWNSTREAM_WORKFLOW:
        errors.append(f"handoff-to-tech-impl.json must target {DOWNSTREAM_WORKFLOW}.")


def validate_adr007_adoption(errors, bundle_json):
    selected_feat = bundle_json.get("selected_feat") or {}
    selected_source_refs = ensure_list(selected_feat.get("source_refs"))
    selected_axis_markers = {
        str(selected_feat.get("resolved_axis") or "").strip().lower(),
        str(selected_feat.get("axis_id") or "").strip().lower(),
        str(selected_feat.get("track") or "").strip().lower(),
    }
    if "ADR-007" in selected_source_refs and any(marker in {"adoption_e2e", "skill-adoption-e2e"} for marker in selected_axis_markers if marker):
        implementation_rules = ensure_list((bundle_json.get("tech_design") or {}).get("implementation_rules"))
        joined_rules = "\n".join(implementation_rules)
        for marker in [
            "skill.qa.test_exec_web_e2e",
            "skill.qa.test_exec_cli",
            "skill.runner.test_e2e",
            "skill.runner.test_cli",
        ]:
            if marker not in joined_rules:
                errors.append("ADR-007 adoption_e2e TECH must preserve inherited family marker: " + marker)
