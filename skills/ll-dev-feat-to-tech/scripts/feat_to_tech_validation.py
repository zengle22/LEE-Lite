#!/usr/bin/env python3
"""
Validation helpers for feat-to-tech output packages.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cli.lib.workflow_document_test import validate_document_test_report
from feat_to_tech_common import ensure_list, load_json, parse_markdown_frontmatter
from feat_to_tech_package_builder import build_semantic_drift_check

REQUIRED_OUTPUT_FILES = [
    "tech-design-bundle.md",
    "tech-design-bundle.json",
    "tech-spec.md",
    "integration-context.json",
    "tech-review-report.json",
    "tech-acceptance-report.json",
    "tech-defect-list.json",
    "document-test-report.json",
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
    "### State Machine",
    "### Module Plan",
    "### Implementation Strategy",
    "### Implementation Unit Mapping",
    "### Interface Contracts",
    "### Main Sequence",
    "### Exception and Compensation",
    "### Integration Points",
    "### Algorithm Constraints",
    "### Input / Output Matrix and Side Effects",
    "### Technical Glossary and Canonical Ownership",
    "### Migration Constraints",
    "### Minimal Code Skeleton",
]
PRODUCT_AXIS_IDS = {
    "minimal-onboarding-flow",
    "first-ai-advice-release",
    "extended-profile-progressive-completion",
    "device-connect-deferred-entry",
    "state-and-profile-boundary-alignment",
}
REQUIRED_API_HEADINGS = [
    "## Contract Scope",
    "## Response Envelope",
    "## Command Contracts",
    "## Compatibility and Versioning",
]
DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"

SEMANTIC_GATE_KEYS = {
    "verdict",
    "semantic_lock_present",
    "semantic_lock_preserved",
    "topic_alignment_ok",
    "lock_gate_ok",
    "review_gate_ok",
    "axis_conflicts",
    "carrier_topic_issues",
}


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
    errors.extend(validate_document_test_report(load_json(artifacts_dir / "document-test-report.json")))
    validate_adr007_adoption(errors, bundle_json)
    validate_explicit_product_axis_resolution(errors, bundle_json)
    return errors, {
        "valid": not errors,
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "arch_required": arch_required,
        "api_required": api_required,
        "semantic_lock_preserved": load_json(artifacts_dir / "semantic-drift-check.json").get("semantic_lock_preserved", True),
    }


def _markdown_body(path: Path) -> str:
    if not path.exists():
        return ""
    _, body = parse_markdown_frontmatter(path.read_text(encoding="utf-8"))
    return body


def recompute_semantic_gate(bundle_json: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    tech_design = bundle_json.get("tech_design") or {}
    feature = dict(bundle_json.get("selected_feat") or {})
    if "semantic_lock" not in feature:
        feature["semantic_lock"] = bundle_json.get("semantic_lock") or {}
    if "feat_ref" not in feature:
        feature["feat_ref"] = bundle_json.get("feat_ref")
    generated_text_parts = [
        feature.get("resolved_axis") or "",
        " ".join(ensure_list(tech_design.get("design_focus"))),
        " ".join(ensure_list(tech_design.get("implementation_rules"))),
        " ".join(ensure_list(tech_design.get("non_functional_requirements"))),
        " ".join(ensure_list(tech_design.get("implementation_architecture"))),
        " ".join(ensure_list(tech_design.get("state_model"))),
        " ".join(ensure_list(tech_design.get("state_machine"))),
        " ".join(ensure_list(tech_design.get("module_plan"))),
        " ".join(ensure_list(tech_design.get("implementation_strategy"))),
        " ".join(ensure_list(tech_design.get("implementation_unit_mapping"))),
        " ".join(ensure_list(tech_design.get("interface_contracts"))),
        " ".join(ensure_list(tech_design.get("main_sequence"))),
        " ".join(ensure_list(tech_design.get("exception_and_compensation"))),
        " ".join(ensure_list(tech_design.get("integration_points"))),
        " ".join(ensure_list(tech_design.get("algorithm_constraints"))),
        " ".join(ensure_list(tech_design.get("io_matrix_and_side_effects"))),
        " ".join(ensure_list(tech_design.get("technical_glossary_and_canonical_ownership"))),
        " ".join(ensure_list(tech_design.get("migration_constraints"))),
        " ".join(ensure_list(tech_design.get("minimal_code_skeleton"))),
        json.dumps(tech_design.get("implementation_carrier_view") or {}, ensure_ascii=False),
        _markdown_body(artifacts_dir / "tech-spec.md"),
    ]
    return build_semantic_drift_check(feature, generated_text_parts)


def _recompute_semantic_gate(bundle_json: dict[str, Any], artifacts_dir: Path) -> dict[str, Any]:
    return recompute_semantic_gate(bundle_json, artifacts_dir)


def _semantic_gate_projection(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload.get(key) for key in SEMANTIC_GATE_KEYS}


def _validate_semantic_gate_projection(
    errors: list[str],
    name: str,
    payload: dict[str, Any] | None,
    recomputed_gate: dict[str, Any],
) -> None:
    if not isinstance(payload, dict):
        errors.append(f"{name} must include semantic_gate.")
        return
    if _semantic_gate_projection(payload) != _semantic_gate_projection(recomputed_gate):
        errors.append(f"{name} semantic_gate must match the current artifact content.")


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
    unexpected = [key for key in artifact_refs if key not in {"tech_spec", "integration_context", "arch_spec", "api_spec"}]
    if unexpected:
        errors.append(
            "artifact_refs may only contain tech_spec/integration_context/arch_spec/api_spec; unexpected keys: " + ", ".join(sorted(unexpected))
        )
    if artifact_refs.get("integration_context") != "integration-context.json":
        errors.append("artifact_refs.integration_context must point to integration-context.json.")


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
    integration_sufficiency = bundle_json.get("integration_sufficiency_check")
    if not isinstance(consistency, dict):
        errors.append("tech-design-bundle.json must include design_consistency_check.")
    else:
        required_keys = {"passed", "structural_passed", "semantic_passed", "checks", "issues", "minor_open_items"}
        if not required_keys.issubset(set(consistency.keys())):
            errors.append("design_consistency_check must include passed/structural_passed/semantic_passed/checks/issues/minor_open_items.")
    if not isinstance(integration_sufficiency, dict):
        errors.append("tech-design-bundle.json must include integration_sufficiency_check.")
    else:
        required_keys = {"passed", "checks", "issues", "summary"}
        if not required_keys.issubset(set(integration_sufficiency.keys())):
            errors.append("integration_sufficiency_check must include passed/checks/issues/summary.")
    need_assessment = bundle_json.get("need_assessment") or {}
    for field in ["integration_context_sufficient", "stateful_design_present"]:
        if field not in need_assessment:
            errors.append(f"need_assessment must include {field}.")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    recomputed_gate = _recompute_semantic_gate(bundle_json, artifacts_dir)
    if bundle_json.get("semantic_lock") and semantic_drift_check.get("semantic_lock_preserved") is not True:
        errors.append("semantic-drift-check.json must preserve semantic_lock when semantic_lock is present.")
    if semantic_drift_check.get("verdict") != "pass":
        errors.append("semantic-drift-check.json must report verdict=pass for freeze-ready TECH output.")
    required_drift_keys = {"matched_allowed_capabilities", "axis_conflicts", "carrier_topic_issues", "topic_alignment_ok", "lock_gate_ok", "review_gate_ok"}
    missing = required_drift_keys.difference(set(semantic_drift_check.keys()))
    if missing:
        errors.append("semantic-drift-check.json is missing required review keys: " + ", ".join(sorted(missing)))
    if _semantic_gate_projection(semantic_drift_check) != _semantic_gate_projection(recomputed_gate):
        errors.append("semantic-drift-check.json must match the current TECH/ARCH/API artifact content.")
    review_report = load_json(artifacts_dir / "tech-review-report.json")
    _validate_semantic_gate_projection(errors, "tech-review-report.json", review_report.get("semantic_gate"), recomputed_gate)
    if review_report.get("decision") == "pass" and recomputed_gate.get("review_gate_ok") is not True:
        errors.append("tech-review-report.json cannot report pass when the recomputed semantic gate fails.")
    acceptance_report = load_json(artifacts_dir / "tech-acceptance-report.json")
    _validate_semantic_gate_projection(errors, "tech-acceptance-report.json", acceptance_report.get("semantic_gate"), recomputed_gate)
    if acceptance_report.get("decision") == "approve" and recomputed_gate.get("review_gate_ok") is not True:
        errors.append("tech-acceptance-report.json cannot approve when the recomputed semantic gate fails.")
    freeze_gate = load_json(artifacts_dir / "tech-freeze-gate.json")
    checks = freeze_gate.get("checks") or {}
    for key in ["topic_alignment_ok", "lock_gate_ok", "review_gate_ok"]:
        if key not in checks:
            errors.append(f"tech-freeze-gate.json checks must include {key}.")
        elif checks.get(key) != recomputed_gate.get(key):
            errors.append(f"tech-freeze-gate.json checks.{key} must match the recomputed semantic gate.")
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
    tech_design = bundle_json.get("tech_design") or {}
    for key in ["state_machine", "algorithm_constraints", "io_matrix_and_side_effects", "technical_glossary_and_canonical_ownership", "migration_constraints"]:
        if not ensure_list(tech_design.get(key)):
            errors.append(f"tech_design.{key} must be non-empty.")


def validate_handoff(errors, artifacts_dir):
    handoff = load_json(artifacts_dir / "handoff-to-tech-impl.json")
    if handoff.get("target_workflow") != DOWNSTREAM_WORKFLOW:
        errors.append(f"handoff-to-tech-impl.json must target {DOWNSTREAM_WORKFLOW}.")
    for key in ["integration_context_ref", "canonical_owner_refs", "state_machine_ref", "nfr_constraints_ref", "migration_constraints_ref", "algorithm_constraint_refs"]:
        if handoff.get(key) in (None, "", []):
            errors.append(f"handoff-to-tech-impl.json must include {key}.")


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


def validate_explicit_product_axis_resolution(errors, bundle_json):
    selected_feat = bundle_json.get("selected_feat") or {}
    axis_id = str(selected_feat.get("axis_id") or "").strip().lower()
    resolved_axis = str(selected_feat.get("resolved_axis") or "").strip().lower()
    if axis_id in PRODUCT_AXIS_IDS and resolved_axis == "generic":
        errors.append(f"selected_feat.axis_id={axis_id} must not resolve to generic TECH output.")
