#!/usr/bin/env python3
"""
Lite-native runtime support for feat-to-tech.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feat_to_tech_cli_integration import (
    build_gate_result,
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    write_executor_outputs,
)
from feat_to_tech_common import (
    ensure_list,
    find_feature,
    guess_repo_root_from_input,
    load_feat_package,
    load_json,
    parse_markdown_frontmatter,
    unique_strings,
    validate_input_package,
)
from feat_to_tech_derivation import (
    api_cli_commands,
    api_compatibility_rules,
    api_error_and_idempotency,
    api_request_response_contracts,
    api_surfaces,
    architecture_topics,
    architecture_diagram,
    assess_optional_artifacts,
    build_refs,
    consistency_check,
    design_focus,
    explicit_axis,
    exception_compensation,
    flow_diagram,
    implementation_unit_mapping,
    integration_points,
    interface_contracts,
    implementation_architecture,
    implementation_modules,
    implementation_strategy,
    implementation_rules,
    main_sequence,
    minimal_code_skeleton,
    non_functional_requirements,
    responsibility_splits,
    selected_feat_snapshot,
    state_model,
    traceability_rows,
)
REQUIRED_OUTPUT_FILES = [
    "tech-design-bundle.md",
    "tech-design-bundle.json",
    "tech-spec.md",
    "tech-impl.md",
    "tech-review-report.json",
    "tech-acceptance-report.json",
    "tech-defect-list.json",
    "tech-freeze-gate.json",
    "handoff-to-tech-impl.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
REQUIRED_MARKDOWN_HEADINGS = [
    "Selected FEAT",
    "Need Assessment",
    "TECH Design",
    "TECH-IMPL Design",
    "Optional ARCH",
    "Optional API",
    "Cross-Artifact Consistency",
    "Downstream Handoff",
    "Traceability",
]
REQUIRED_TECH_SUBHEADINGS = [
    "### Implementation Unit Mapping",
    "### Interface Contracts",
    "### Main Sequence",
    "### Exception and Compensation",
    "### Integration Points",
    "### Minimal Code Skeleton",
]
REQUIRED_TECH_IMPL_HEADINGS = [
    "## ASCII Architecture View",
    "## Implementation Unit Mapping",
    "## Interface Contracts",
    "## Main Sequence",
    "## Exception and Compensation",
    "## Integration Points",
    "## Minimal Code Skeleton",
]
REQUIRED_API_HEADINGS = [
    "## CLI Command Surface",
    "## Request and Response Contracts",
    "## Error Codes and Idempotency",
    "## Compatibility and Versioning",
]
DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()

def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "feat-to-tech" / run_id


def display_list(values: list[str]) -> str:
    items = [str(item).strip() for item in values if str(item).strip()]
    return ", ".join(items) if items else "None"


@dataclass
class GeneratedTechPackage:
    run_id: str
    frontmatter: dict[str, Any]
    markdown_body: str
    json_payload: dict[str, Any]
    tech_frontmatter: dict[str, Any]
    tech_body: str
    tech_impl_frontmatter: dict[str, Any]
    tech_impl_body: str
    arch_frontmatter: dict[str, Any] | None
    arch_body: str | None
    api_frontmatter: dict[str, Any] | None
    api_body: str | None
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    handoff: dict[str, Any]
    execution_decisions: list[str]
    execution_uncertainties: list[str]

def build_tech_package(package: Any, feature: dict[str, Any], feat_ref: str, run_id: str) -> GeneratedTechPackage:
    refs = build_refs(feature, package)
    assessment = assess_optional_artifacts(feature, package)
    focus = design_focus(feature)
    rules = implementation_rules(feature)
    nfrs = non_functional_requirements(feature, package)
    implementation_arch = implementation_architecture(feature)
    modules = implementation_modules(feature)
    states = state_model(feature)
    strategy = implementation_strategy(feature)
    arch_diagram = architecture_diagram(feature)
    main_flow_diagram = flow_diagram(feature)
    unit_mapping = implementation_unit_mapping(feature)
    contracts = interface_contracts(feature)
    sequence_steps = main_sequence(feature)
    exception_rules = exception_compensation(feature)
    integrations = integration_points(feature)
    skeleton = minimal_code_skeleton(feature)
    traceability = traceability_rows(feature, package, refs)
    consistency = consistency_check(feature, assessment)
    source_refs = unique_strings(
        [f"product.epic-to-feat::{package.run_id}", refs["feat_ref"], refs["epic_ref"], refs["src_ref"]]
        + ensure_list(feature.get("source_refs"))
        + ensure_list(package.feat_json.get("source_refs"))
    )

    artifact_refs = {
        "tech_spec": "tech-spec.md",
        "tech_impl": "tech-impl.md",
        "arch_spec": "arch-design.md" if assessment["arch_required"] else None,
        "api_spec": "api-contract.md" if assessment["api_required"] else None,
    }

    defects: list[dict[str, Any]] = []
    if len(focus) < 3:
        defects.append(
            {
                "severity": "P1",
                "title": "TECH design focus is too thin",
                "detail": "The selected FEAT does not expose enough scope or constraint detail to support a robust TECH design.",
            }
        )
    if not consistency["passed"]:
        defects.append(
            {
                "severity": "P1",
                "title": "Cross-artifact consistency failed",
                "detail": "; ".join(consistency["issues"]),
            }
        )

    review_decision = "pass" if not defects else "revise"
    acceptance_decision = "approve" if not defects else "revise"

    handoff = {
        "handoff_id": f"handoff-{run_id}-to-tech-impl",
        "from_skill": "ll-dev-feat-to-tech",
        "source_run_id": run_id,
        "target_workflow": DOWNSTREAM_WORKFLOW,
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"] if assessment["arch_required"] else None,
        "api_ref": refs["api_ref"] if assessment["api_required"] else None,
        "primary_artifact_ref": "tech-design-bundle.md",
        "supporting_artifact_refs": [
            "tech-design-bundle.json",
            "tech-spec.md",
            "tech-impl.md",
            *(['arch-design.md'] if assessment["arch_required"] else []),
            *(['api-contract.md'] if assessment["api_required"] else []),
            "tech-review-report.json",
            "tech-acceptance-report.json",
            "tech-defect-list.json",
        ],
        "created_at": utc_now(),
    }

    json_payload = {
        "artifact_type": "tech_design_package",
        "workflow_key": "dev.feat-to-tech",
        "workflow_run_id": run_id,
        "title": f"{feature.get('title') or feat_ref} Technical Design Package",
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"] if assessment["arch_required"] else None,
        "api_ref": refs["api_ref"] if assessment["api_required"] else None,
        "epic_freeze_ref": refs["epic_ref"],
        "src_root_id": refs["src_ref"],
        "source_refs": source_refs,
        "arch_required": assessment["arch_required"],
        "api_required": assessment["api_required"],
        "need_assessment": assessment,
        "selected_feat": {
            **selected_feat_snapshot(feature),
            "resolved_axis": explicit_axis(feature) or "derived",
        },
        "tech_design": {
            "design_focus": focus,
            "implementation_rules": rules,
            "non_functional_requirements": nfrs,
        },
        "tech_impl_design": {
            "implementation_architecture": implementation_arch,
            "architecture_diagram": arch_diagram,
            "state_model": states,
            "module_plan": modules,
            "implementation_strategy": strategy,
            "implementation_unit_mapping": unit_mapping,
            "interface_contracts": contracts,
            "main_sequence": sequence_steps,
            "flow_diagram": main_flow_diagram,
            "exception_and_compensation": exception_rules,
            "integration_points": integrations,
            "minimal_code_skeleton": skeleton,
        },
        "optional_arch": {
            "topics": architecture_topics(feature),
            "rationale": assessment["arch_rationale"],
        }
        if assessment["arch_required"]
        else None,
        "optional_api": {
            "surfaces": api_surfaces(feature),
            "cli_commands": api_cli_commands(feature),
            "request_response_contracts": api_request_response_contracts(feature),
            "error_and_idempotency": api_error_and_idempotency(feature),
            "compatibility_rules": api_compatibility_rules(feature),
            "rationale": assessment["api_rationale"],
        }
        if assessment["api_required"]
        else None,
        "artifact_refs": artifact_refs,
        "design_consistency_check": consistency,
        "downstream_handoff": handoff,
        "traceability": traceability,
    }

    frontmatter = {
        "artifact_type": "tech_design_package",
        "workflow_key": "dev.feat-to-tech",
        "workflow_run_id": run_id,
        "status": json_payload["status"],
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_required": assessment["arch_required"],
        "api_required": assessment["api_required"],
        "source_refs": source_refs,
    }

    markdown_body = "\n\n".join(
        [
            f"# {json_payload['title']}",
            "## Selected FEAT\n\n"
            + "\n".join(
                [
                    f"- feat_ref: `{refs['feat_ref']}`",
                    f"- title: {feature.get('title')}",
                    f"- axis_id: {feature.get('axis_id')}",
                    f"- resolved_axis: {explicit_axis(feature) or 'derived'}",
                    f"- epic_freeze_ref: `{refs['epic_ref']}`",
                    f"- src_root_id: `{refs['src_ref']}`",
                    f"- goal: {feature.get('goal')}",
                    f"- authoritative_artifact: {feature.get('authoritative_artifact')}",
                    f"- upstream_feat: {display_list(ensure_list(feature.get('upstream_feat')))}",
                    f"- downstream_feat: {display_list(ensure_list(feature.get('downstream_feat')))}",
                    f"- gate_decision_dependency_feat_refs: {display_list(ensure_list(feature.get('gate_decision_dependency_feat_refs')))}",
                    f"- admission_dependency_feat_refs: {display_list(ensure_list(feature.get('admission_dependency_feat_refs')))}",
                ]
            ),
            "## Need Assessment\n\n"
            + "\n".join(
                [
                    f"- arch_required: {assessment['arch_required']}",
                    *[f"  - {item}" for item in assessment["arch_rationale"]],
                    f"- api_required: {assessment['api_required']}",
                    *[f"  - {item}" for item in assessment["api_rationale"]],
                ]
            ),
            "## TECH Design\n\n"
            + "\n".join(
                [
                    "- Design focus:",
                    *[f"  - {item}" for item in focus],
                    "- Implementation rules:",
                    *[f"  - {item}" for item in rules],
                    "- Non-functional requirements:",
                    *[f"  - {item}" for item in nfrs],
                ]
            ),
            "## TECH-IMPL Design\n\n"
            + "\n".join(
                [
                    "### ASCII Architecture View",
                    *[f"- {item}" for item in implementation_arch],
                    "",
                    arch_diagram,
                    "",
                    "### Implementation Unit Mapping",
                    *[f"- {item}" for item in unit_mapping],
                    "",
                    "### Interface Contracts",
                    *[f"- {item}" for item in contracts],
                    "",
                    "### Main Sequence",
                    *[f"- {item}" for item in sequence_steps],
                    "",
                    main_flow_diagram,
                    "",
                    "### Exception and Compensation",
                    *[f"- {item}" for item in exception_rules],
                    "",
                    "### Integration Points",
                    *[f"- {item}" for item in integrations],
                    "",
                    "### Minimal Code Skeleton",
                    "- Happy path:",
                    skeleton["happy_path"],
                    "",
                    "- Failure path:",
                    skeleton["failure_path"],
                ]
            ),
            "## Optional ARCH\n\n"
            + (
                "\n".join(["- ARCH emitted with topics:", *[f"  - {item}" for item in architecture_topics(feature)]])
                if assessment["arch_required"]
                else "- ARCH not required for this FEAT."
            ),
            "## Optional API\n\n"
            + (
                "\n".join(["- API emitted with contract surfaces:", *[f"  - {item}" for item in api_surfaces(feature)]])
                if assessment["api_required"]
                else "- API not required for this FEAT."
            ),
            "## Cross-Artifact Consistency\n\n"
            + "\n".join(
                [
                    f"- passed: {consistency['passed']}",
                    "- checks:",
                    *[f"  - {item['name']}: {item['passed']} ({item['detail']})" for item in consistency["checks"]],
                    "- issues:",
                    *([f"  - {item}" for item in consistency["issues"]] or ["  - None"]),
                ]
            ),
            "## Downstream Handoff\n\n"
            + "\n".join(
                [
                    f"- target_workflow: {DOWNSTREAM_WORKFLOW}",
                    f"- tech_ref: `{refs['tech_ref']}`",
                    f"- arch_ref: `{refs['arch_ref']}`" if assessment["arch_required"] else "- arch_ref: not emitted",
                    f"- api_ref: `{refs['api_ref']}`" if assessment["api_required"] else "- api_ref: not emitted",
                ]
            ),
            "## Traceability\n\n"
            + "\n".join(
                f"- {item['design_section']}: {', '.join(item['feat_fields'])} <- {', '.join(item['source_refs'])}"
                for item in traceability
            ),
        ]
    )

    tech_frontmatter = {
        "artifact_type": "TECH",
        "status": json_payload["status"],
        "schema_version": "1.0.0",
        "tech_ref": refs["tech_ref"],
        "feat_ref": refs["feat_ref"],
        "source_refs": source_refs,
    }
    tech_body = "\n\n".join(
        [
            f"# {refs['tech_ref']}",
            "## Overview\n\n" + str(feature.get("goal") or ""),
            "## Design Focus\n\n" + "\n".join(f"- {item}" for item in focus),
            "## Implementation Rules\n\n" + "\n".join(f"- {item}" for item in rules),
            "## Non-Functional Requirements\n\n" + "\n".join(f"- {item}" for item in nfrs),
            "## Traceability\n\n" + "\n".join(f"- {item['design_section']}: {', '.join(item['source_refs'])}" for item in traceability),
        ]
    )

    tech_impl_frontmatter = {
        "artifact_type": "TECH_IMPL",
        "status": json_payload["status"],
        "schema_version": "1.0.0",
        "tech_ref": refs["tech_ref"],
        "feat_ref": refs["feat_ref"],
        "source_refs": source_refs,
    }
    tech_impl_body = "\n\n".join(
        [
            f"# TECH-IMPL-{refs['feat_ref']}",
            "## ASCII Architecture View\n\n" + "\n".join(f"- {item}" for item in implementation_arch) + "\n\n" + arch_diagram,
            "## State Model\n\n" + "\n".join(f"- {item}" for item in states),
            "## Module Plan\n\n" + "\n".join(f"- {item}" for item in modules),
            "## Implementation Strategy\n\n" + "\n".join(f"- {item}" for item in strategy),
            "## Implementation Unit Mapping\n\n" + "\n".join(f"- {item}" for item in unit_mapping),
            "## Interface Contracts\n\n" + "\n".join(f"- {item}" for item in contracts),
            "## Main Sequence\n\n" + "\n".join(f"- {item}" for item in sequence_steps) + "\n\n" + main_flow_diagram,
            "## Exception and Compensation\n\n" + "\n".join(f"- {item}" for item in exception_rules),
            "## Integration Points\n\n" + "\n".join(f"- {item}" for item in integrations),
            "## Minimal Code Skeleton\n\n- Happy path:\n\n" + skeleton["happy_path"] + "\n\n- Failure path:\n\n" + skeleton["failure_path"],
            "## Traceability\n\n" + "\n".join(f"- {item['design_section']}: {', '.join(item['source_refs'])}" for item in traceability),
        ]
    )

    arch_frontmatter = None
    arch_body = None
    if assessment["arch_required"]:
        arch_frontmatter = {
            "artifact_type": "ARCH",
            "status": json_payload["status"],
            "schema_version": "1.0.0",
            "arch_ref": refs["arch_ref"],
            "feat_ref": refs["feat_ref"],
            "source_refs": source_refs,
        }
        arch_body = "\n\n".join(
            [
                f"# {refs['arch_ref']}",
                "## Boundary Placement\n\n" + "\n".join(f"- {item}" for item in architecture_topics(feature)),
                "## Boundary Diagram\n\n" + arch_diagram,
                "## Responsibility Split\n\n" + "\n".join(f"- {item}" for item in responsibility_splits(feature)),
                "## Architecture Decisions\n\n" + "\n".join(f"- {item}" for item in assessment["arch_rationale"]),
            ]
        )

    api_frontmatter = None
    api_body = None
    if assessment["api_required"]:
        api_frontmatter = {
            "artifact_type": "API",
            "status": json_payload["status"],
            "schema_version": "1.0.0",
            "api_ref": refs["api_ref"],
            "feat_ref": refs["feat_ref"],
            "source_refs": source_refs,
        }
        api_body = "\n\n".join(
            [
                f"# {refs['api_ref']}",
                "## CLI Command Surface\n\n" + "\n".join(f"- {item}" for item in api_cli_commands(feature)),
                "## Request and Response Contracts\n\n" + "\n".join(f"- {item}" for item in api_request_response_contracts(feature)),
                "## Error Codes and Idempotency\n\n" + "\n".join(f"- {item}" for item in api_error_and_idempotency(feature)),
                "## Compatibility and Versioning\n\n"
                + "\n".join(
                    [f"- {item}" for item in api_compatibility_rules(feature)]
                ),
            ]
        )

    review_report = {
        "review_id": f"tech-review-{run_id}",
        "review_type": "tech_design_review",
        "subject_refs": [refs["feat_ref"], refs["tech_ref"]],
        "summary": "TECH package preserves FEAT traceability and downstream implementation readiness.",
        "findings": [
            "TECH is present and aligned to the selected FEAT.",
            "Optional companions were emitted only when need assessment required them.",
            "A final cross-artifact consistency check was recorded before freeze.",
        ],
        "decision": review_decision,
        "risks": [defect["detail"] for defect in defects],
        "created_at": utc_now(),
    }

    acceptance_report = {
        "stage_id": "tech_acceptance_review",
        "created_by_role": "supervisor",
        "decision": acceptance_decision,
        "dimensions": {
            "tech_presence": {"status": "pass", "note": "TECH is mandatory and present."},
            "optional_outputs_match_assessment": {
                "status": "pass" if not defects else "fail",
                "note": "Optional ARCH/API outputs align with the need assessment." if not defects else "Optional outputs need revision.",
            },
            "cross_artifact_consistency": {
                "status": "pass" if consistency["passed"] else "fail",
                "note": "ARCH, TECH, and API remain aligned." if consistency["passed"] else "Consistency issues remain open.",
            },
            "downstream_readiness": {
                "status": "pass" if not defects else "fail",
                "note": "Output remains actionable for workflow.dev.tech_to_impl." if not defects else "Output is not freeze-ready for tech-impl.",
            },
        },
        "summary": "TECH acceptance review passed." if not defects else "TECH acceptance review requires revision.",
        "acceptance_findings": defects,
        "created_at": utc_now(),
    }

    execution_decisions = [
        f"Selected FEAT {refs['feat_ref']} from upstream run {package.run_id}.",
        f"ARCH required: {assessment['arch_required']}.",
        f"API required: {assessment['api_required']}.",
        f"Prepared downstream handoff to {DOWNSTREAM_WORKFLOW}.",
    ]
    execution_uncertainties = consistency["issues"][:]

    return GeneratedTechPackage(
        run_id=run_id,
        frontmatter=frontmatter,
        markdown_body=markdown_body,
        json_payload=json_payload,
        tech_frontmatter=tech_frontmatter,
        tech_body=tech_body,
        tech_impl_frontmatter=tech_impl_frontmatter,
        tech_impl_body=tech_impl_body,
        arch_frontmatter=arch_frontmatter,
        arch_body=arch_body,
        api_frontmatter=api_frontmatter,
        api_body=api_body,
        review_report=review_report,
        acceptance_report=acceptance_report,
        defect_list=defects,
        handoff=handoff,
        execution_decisions=execution_decisions,
        execution_uncertainties=execution_uncertainties,
    )

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
    if bundle_json.get("artifact_type") != "tech_design_package":
        errors.append("tech-design-bundle.json artifact_type must be tech_design_package.")
    if bundle_json.get("workflow_key") != "dev.feat-to-tech":
        errors.append("tech-design-bundle.json workflow_key must be dev.feat-to-tech.")

    feat_ref = str(bundle_json.get("feat_ref") or "")
    tech_ref = str(bundle_json.get("tech_ref") or "")
    source_refs = ensure_list(bundle_json.get("source_refs"))
    if not feat_ref:
        errors.append("tech-design-bundle.json must include feat_ref.")
    if not tech_ref:
        errors.append("tech-design-bundle.json must include tech_ref.")
    if not any(ref.startswith("product.epic-to-feat::") for ref in source_refs):
        errors.append("tech-design-bundle.json source_refs must include product.epic-to-feat::<run_id>.")
    if not any(ref.startswith("FEAT-") for ref in source_refs):
        errors.append("tech-design-bundle.json source_refs must include FEAT-*.")
    if not any(ref.startswith("EPIC-") for ref in source_refs):
        errors.append("tech-design-bundle.json source_refs must include EPIC-*.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("tech-design-bundle.json source_refs must include SRC-*.")

    artifact_refs = bundle_json.get("artifact_refs") or {}
    if artifact_refs.get("tech_spec") != "tech-spec.md":
        errors.append("artifact_refs.tech_spec must point to tech-spec.md.")

    arch_required = bool(bundle_json.get("arch_required"))
    api_required = bool(bundle_json.get("api_required"))
    if arch_required and not (artifacts_dir / "arch-design.md").exists():
        errors.append("arch-design.md must exist when arch_required is true.")
    if not arch_required and (artifacts_dir / "arch-design.md").exists():
        errors.append("arch-design.md must not exist when arch_required is false.")
    if api_required and not (artifacts_dir / "api-contract.md").exists():
        errors.append("api-contract.md must exist when api_required is true.")
    if not api_required and (artifacts_dir / "api-contract.md").exists():
        errors.append("api-contract.md must not exist when api_required is false.")
    if api_required:
        api_body = (artifacts_dir / "api-contract.md").read_text(encoding="utf-8")
        for heading in REQUIRED_API_HEADINGS:
            if heading not in api_body:
                errors.append(f"api-contract.md must contain heading: {heading}")

    consistency = bundle_json.get("design_consistency_check")
    if not isinstance(consistency, dict):
        errors.append("tech-design-bundle.json must include design_consistency_check.")
    else:
        if "passed" not in consistency or "checks" not in consistency or "issues" not in consistency:
            errors.append("design_consistency_check must include passed/checks/issues.")

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

    tech_impl_text = (artifacts_dir / "tech-impl.md").read_text(encoding="utf-8")
    _, tech_impl_body = parse_markdown_frontmatter(tech_impl_text)
    for heading in REQUIRED_TECH_IMPL_HEADINGS:
        if heading not in tech_impl_body:
            errors.append(f"tech-impl.md is missing section: {heading.replace('## ', '')}")
    if tech_impl_body.count("```text") < 2:
        errors.append("tech-impl.md must include at least two ASCII diagrams for architecture and flow.")

    handoff = load_json(artifacts_dir / "handoff-to-tech-impl.json")
    if handoff.get("target_workflow") != DOWNSTREAM_WORKFLOW:
        errors.append(f"handoff-to-tech-impl.json must target {DOWNSTREAM_WORKFLOW}.")

    return errors, {
        "valid": not errors,
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "arch_required": arch_required,
        "api_required": api_required,
    }

def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors
    gate = load_json(artifacts_dir / "tech-freeze-gate.json")
    checks = gate.get("checks") or {}
    readiness_errors = [name for name, status in checks.items() if status is not True]
    return not readiness_errors, readiness_errors

def executor_run(input_path: Path, feat_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, feat_ref)
    if errors:
        raise ValueError("; ".join(errors))

    package = load_feat_package(input_path)
    feature = find_feature(package, feat_ref)
    if feature is None:
        raise ValueError(f"Selected feat_ref not found: {feat_ref}")

    effective_run_id = run_id or f"{package.run_id}--{feat_ref.lower()}"
    generated = build_tech_package(package, feature, feat_ref, effective_run_id)
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    write_executor_outputs(output_dir, repo_root, package, generated, f"python scripts/feat_to_tech.py executor-run --input {input_path} --feat-ref {feat_ref}")
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "feat_ref": feat_ref,
        "tech_ref": generated.json_payload["tech_ref"],
    }

def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    package_manifest = load_json(artifacts_dir / "package-manifest.json")
    input_package_dir = Path(str(package_manifest.get("input_artifacts_dir") or "")).resolve()
    feat_ref = str(package_manifest.get("feat_ref") or "").strip()
    if not input_package_dir.exists():
        raise FileNotFoundError(f"Input package directory not found: {input_package_dir}")
    if not feat_ref:
        raise ValueError("package-manifest.json is missing feat_ref.")

    package = load_feat_package(input_package_dir)
    feature = find_feature(package, feat_ref)
    if feature is None:
        raise ValueError(f"Selected feat_ref not found: {feat_ref}")
    effective_run_id = run_id or artifacts_dir.name
    generated = build_tech_package(package, feature, feat_ref, effective_run_id)
    supervision = build_supervision_evidence(artifacts_dir, generated)
    gate = build_gate_result(generated, supervision)
    update_supervisor_outputs(artifacts_dir, repo_root, generated, supervision, gate)

    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "freeze_ready": gate["freeze_ready"],
    }

def run_workflow(input_path: Path, feat_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        feat_ref=feat_ref,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(artifacts_dir, repo_root, run_id or executor_result["run_id"], allow_update=True)
    output_errors, output_result = validate_output_package(artifacts_dir)
    if output_errors:
        raise ValueError("; ".join(output_errors))
    readiness_ok, readiness_errors = validate_package_readiness(artifacts_dir)
    report_path = collect_evidence_report(artifacts_dir)
    return {
        "ok": readiness_ok,
        "run_id": executor_result["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "feat_ref": feat_ref,
        "tech_ref": executor_result["tech_ref"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }
