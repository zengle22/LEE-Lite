#!/usr/bin/env python3
"""
Rendering helpers for feat-to-tech package documents.
"""

from __future__ import annotations

from feat_to_tech_common import ensure_list, unique_strings
from feat_to_tech_derivation import (
    api_compatibility_rules,
    api_surfaces,
    architecture_topics,
    feature_axis,
    is_engineering_baseline_feature,
    responsibility_splits,
)

DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"


def display_list(values: list[str]) -> str:
    items = [str(item).strip() for item in values if str(item).strip()]
    return ", ".join(items) if items else "None"


def build_markdown_body(json_payload, feature, refs, assessment, focus, rules, nfrs, implementation_arch, runtime_view, states, state_machine, modules, strategy, unit_mapping, contracts, sequence_steps, main_flow_diagram, exception_rules, integrations, algorithm_constraints, io_matrix, glossary, migration_constraints, skeleton, api_specs, consistency, traceability):
    return "\n\n".join(
        [
            build_selected_feat_section(feature, refs),
            build_need_assessment_section(assessment),
            build_tech_design_section(focus, rules, nfrs, implementation_arch, runtime_view, states, state_machine, modules, strategy, unit_mapping, contracts, sequence_steps, main_flow_diagram, exception_rules, integrations, algorithm_constraints, io_matrix, glossary, migration_constraints, skeleton),
            build_optional_arch_section(feature, refs, assessment),
            build_optional_api_section(feature, refs, assessment, api_specs),
            build_consistency_section(consistency),
            build_handoff_section(refs, assessment),
            build_traceability_section(traceability),
        ]
    ).replace("# ", f"# {json_payload['title']}\n\n", 1)


def build_selected_feat_section(feature, refs):
    return "# \n## Selected FEAT\n\n" + "\n".join([
        f"- feat_ref: `{refs['feat_ref']}`",
        f"- title: {feature.get('title')}",
        f"- axis_id: {feature.get('axis_id')}",
        f"- resolved_axis: {feature_axis(feature)}",
        f"- epic_freeze_ref: `{refs['epic_ref']}`",
        f"- src_root_id: `{refs['src_ref']}`",
        f"- goal: {feature.get('goal')}",
        f"- authoritative_artifact: {feature.get('authoritative_artifact')}",
        f"- upstream_feat: {display_list(ensure_list(feature.get('upstream_feat')))}",
        f"- downstream_feat: {display_list(ensure_list(feature.get('downstream_feat')))}",
        f"- gate_decision_dependency_feat_refs: {display_list(ensure_list(feature.get('gate_decision_dependency_feat_refs')))}",
        f"- admission_dependency_feat_refs: {display_list(ensure_list(feature.get('admission_dependency_feat_refs')))}",
    ])


def build_need_assessment_section(assessment):
    return "## Need Assessment\n\n" + "\n".join([
        f"- arch_required: {assessment['arch_required']}",
        *[f"  - {item}" for item in assessment["arch_rationale"]],
        f"- api_required: {assessment['api_required']}",
        *[f"  - {item}" for item in assessment["api_rationale"]],
        f"- integration_context_sufficient: {assessment['integration_context_sufficient']}",
        *[f"  - {item}" for item in assessment["integration_context_rationale"]],
        f"- stateful_design_present: {assessment['stateful_design_present']}",
        *[f"  - {item}" for item in assessment["stateful_design_rationale"]],
    ])


def build_tech_design_section(focus, rules, nfrs, implementation_arch, runtime_view, states, state_machine, modules, strategy, unit_mapping, contracts, sequence_steps, main_flow_diagram, exception_rules, integrations, algorithm_constraints, io_matrix, glossary, migration_constraints, skeleton):
    return "## TECH Design\n\n" + "\n".join([
        "- Design focus:", *[f"  - {item}" for item in focus],
        "- Implementation rules:", *[f"  - {item}" for item in rules],
        "- Non-functional requirements:", *[f"  - {item}" for item in nfrs],
        "", "### Implementation Carrier View", *[f"- {item}" for item in implementation_arch], "",
        runtime_view, "", "### State Model", *[f"- {item}" for item in states], "",
        "### State Machine", *[f"- {item}" for item in state_machine], "",
        "### Module Plan", *[f"- {item}" for item in modules], "",
        "### Implementation Strategy", *[f"- {item}" for item in strategy], "",
        "### Implementation Unit Mapping", *[f"- {item}" for item in unit_mapping], "",
        "### Interface Contracts", *[f"- {item}" for item in contracts], "",
        "### Main Sequence", *[f"- {item}" for item in sequence_steps], "",
        main_flow_diagram, "", "### Exception and Compensation", *[f"- {item}" for item in exception_rules], "",
        "### Integration Points", *[f"- {item}" for item in integrations], "",
        "### Algorithm Constraints", *[f"- {item}" for item in algorithm_constraints], "",
        "### Input / Output Matrix and Side Effects", *[f"- {item}" for item in io_matrix], "",
        "### Technical Glossary and Canonical Ownership", *[f"- {item}" for item in glossary], "",
        "### Migration Constraints", *[f"- {item}" for item in migration_constraints], "",
        "### Minimal Code Skeleton", "- Happy path:", skeleton["happy_path"], "", "- Failure path:", skeleton["failure_path"],
    ])


def build_optional_arch_section(feature, refs, assessment):
    if not assessment["arch_required"]:
        return "## Optional ARCH\n\n- ARCH not required for this FEAT."
    return "## Optional ARCH\n\n" + "\n".join(
        [f"- arch_ref: `{refs['arch_ref']}`", "- summary_topics:", *[f"  - {item}" for item in architecture_topics(feature)], "- see: `arch-design.md`"]
    )


def build_optional_api_section(feature, refs, assessment, api_specs):
    if not assessment["api_required"]:
        return "## Optional API\n\n- API not required for this FEAT."
    return "## Optional API\n\n" + "\n".join(
        [f"- api_ref: `{refs['api_ref']}`", "- contract_surfaces:", *[f"  - {item}" for item in api_surfaces(feature)], "- command_refs:", *[f"  - `{spec['command']}`" for spec in api_specs], "- response_envelope:", "  - success: `{ ok: true, command_ref, trace_ref, result }`", "  - error: `{ ok: false, command_ref, trace_ref, error }`", "- see: `api-contract.md`"]
    )


def build_consistency_section(consistency):
    return "## Cross-Artifact Consistency\n\n" + "\n".join([
        f"- passed: {consistency['passed']}",
        f"- structural_passed: {consistency['structural_passed']}",
        f"- semantic_passed: {consistency['semantic_passed']}",
        "- checks:",
        *[f"  - [{item['category']}] {item['name']}: {item['passed']} ({item['detail']})" for item in consistency["checks"]],
        "- issues:",
        *([f"  - {item}" for item in consistency["issues"]] or ["  - None"]),
        "- minor_open_items:",
        *([f"  - {item}" for item in consistency["minor_open_items"]] or ["  - None"]),
    ])


def build_handoff_section(refs, assessment):
    return "## Downstream Handoff\n\n" + "\n".join([
        f"- target_workflow: {DOWNSTREAM_WORKFLOW}",
        f"- tech_ref: `{refs['tech_ref']}`",
        f"- arch_ref: `{refs['arch_ref']}`" if assessment["arch_required"] else "- arch_ref: not emitted",
        f"- api_ref: `{refs['api_ref']}`" if assessment["api_required"] else "- api_ref: not emitted",
        "- integration_context_ref: `integration-context.json`",
        "- state_machine_ref: `tech-design-bundle.json#/tech_design/state_machine`",
        "- canonical_owner_refs: `tech-design-bundle.json#/tech_design/technical_glossary_and_canonical_ownership`",
        "- migration_constraints_ref: `tech-design-bundle.json#/tech_design/migration_constraints`",
        "- algorithm_constraint_refs: `tech-design-bundle.json#/tech_design/algorithm_constraints`",
    ])


def build_traceability_section(traceability):
    return "## Traceability\n\n" + "\n".join(
        f"- {item['design_section']}: {', '.join(item['feat_fields'])} <- {', '.join(item['source_refs'])}"
        for item in traceability
    )


def build_tech_docs(refs, source_refs, feature, focus, rules, nfrs, implementation_arch, runtime_view, states, state_machine, modules, strategy, unit_mapping, contracts, sequence_steps, main_flow_diagram, exception_rules, integrations, algorithm_constraints, io_matrix, glossary, migration_constraints, skeleton, traceability, json_payload):
    frontmatter = {
        "artifact_type": "TECH",
        "status": json_payload["status"],
        "schema_version": "1.0.0",
        "tech_ref": refs["tech_ref"],
        "feat_ref": refs["feat_ref"],
        "source_refs": source_refs,
    }

    is_engineering = is_engineering_baseline_feature(feature)

    # Build sections conditionally based on FEAT type
    sections = [
        f"# {refs['tech_ref']}",
        "## Overview\n\n" + str(feature.get("goal") or ""),
        "## Design Focus\n\n" + "\n".join(f"- {item}" for item in focus),
        "## Implementation Rules\n\n" + "\n".join(f"- {item}" for item in rules),
    ]

    # Add NFRs if they exist
    if nfrs:
        sections.append("## Non-Functional Requirements\n\n" + "\n".join(f"- {item}" for item in nfrs))

    # Add implementation carrier view
    sections.append("## Implementation Carrier View\n\n" + "\n".join(f"- {item}" for item in implementation_arch) + "\n\n" + runtime_view)

    # Add state model only if it's meaningful (not just the generic default)
    if states and not (len(states) == 1 and "prepared -> executed -> recorded" in states[0]):
        sections.append("## State Model\n\n" + "\n".join(f"- {item}" for item in states))

    # Add state machine only if meaningful
    if state_machine:
        sections.append("## State Machine\n\n" + "\n".join(f"- {item}" for item in state_machine))

    # Add module plan
    if modules:
        sections.append("## Module Plan\n\n" + "\n".join(f"- {item}" for item in modules))

    # Add implementation strategy
    if strategy:
        sections.append("## Implementation Strategy\n\n" + "\n".join(f"- {item}" for item in strategy))

    # Add implementation unit mapping (always include - this is core)
    if unit_mapping:
        sections.append("## Implementation Unit Mapping\n\n" + "\n".join(f"- {item}" for item in unit_mapping))

    # Add interface contracts
    if contracts:
        sections.append("## Interface Contracts\n\n" + "\n".join(f"- {item}" for item in contracts))

    # Add main sequence
    if sequence_steps:
        sections.append("## Main Sequence\n\n" + "\n".join(f"- {item}" for item in sequence_steps))
        if main_flow_diagram:
            sections[-1] = sections[-1] + "\n\n" + main_flow_diagram

    # Add exception and compensation
    if exception_rules:
        sections.append("## Exception and Compensation\n\n" + "\n".join(f"- {item}" for item in exception_rules))

    # Add integration points
    if integrations:
        sections.append("## Integration Points\n\n" + "\n".join(f"- {item}" for item in integrations))

    # Add algorithm constraints only if meaningful
    if algorithm_constraints:
        sections.append("## Algorithm Constraints\n\n" + "\n".join(f"- {item}" for item in algorithm_constraints))

    # Add IO matrix only if meaningful
    if io_matrix:
        sections.append("## Input / Output Matrix and Side Effects\n\n" + "\n".join(f"- {item}" for item in io_matrix))

    # Add technical glossary only if meaningful
    if glossary:
        sections.append("## Technical Glossary and Canonical Ownership\n\n" + "\n".join(f"- {item}" for item in glossary))

    # Add migration constraints only if meaningful
    if migration_constraints:
        sections.append("## Migration Constraints\n\n" + "\n".join(f"- {item}" for item in migration_constraints))

    # For engineering baseline FEATs, skip the generic minimal code skeleton
    # since unit mapping already provides the specific skeleton
    if not is_engineering and skeleton["happy_path"] and skeleton["failure_path"]:
        sections.append("## Minimal Code Skeleton\n\n- Happy path:\n\n" + skeleton["happy_path"] + "\n\n- Failure path:\n\n" + skeleton["failure_path"])

    # Always add traceability
    if traceability:
        sections.append("## Traceability\n\n" + "\n".join(f"- {item['design_section']}: {', '.join(item['source_refs'])}" for item in traceability))

    body = "\n\n".join(sections)
    return frontmatter, body


def build_arch_docs(feature, refs, source_refs, assessment, arch_diagram, json_payload):
    if not assessment["arch_required"]:
        return None, None
    arch_out_of_scope = ensure_list(feature.get("non_goals"))
    arch_out_of_scope.extend(
        item for item in ensure_list(feature.get("constraints")) if any(marker in item.lower() for marker in ["不得", "不", "only", "must not", "do not", "not "])
    )
    acceptance = feature.get("acceptance_and_testability") or {}
    if isinstance(acceptance, dict):
        arch_out_of_scope.extend(ensure_list(acceptance.get("out_of_scope")))
    if not arch_out_of_scope:
        axis = feature_axis(feature)
        defaults = {
            "collaboration": ["Do not define decision vocabulary or final formalization semantics here.", "Do not publish formal objects or downstream admission results here."],
            "formalization": ["Do not redefine authoritative submission or pending visibility here.", "Do not decide downstream consumer admission policy here."],
            "layering": ["Do not redefine handoff submission or materialization dispatch here.", "Do not rewrite path / mode governance here."],
            "io_governance": ["Do not redefine object layering or admission semantics here.", "Do not carry approve / reject business semantics here."],
            "first_ai_advice": ["Do not redefine homepage shell ownership here.", "Do not require expanded profile or device data before minimum first-advice release."],
            "extended_profile_completion": ["Do not move extended profile completion back into first-day blocking onboarding here.", "Do not treat partial-save failure as homepage access revocation."],
            "device_deferred_entry": ["Do not reintroduce device connection as a homepage or first-advice prerequisite here.", "Do not let device sync ownership overwrite canonical onboarding/profile facts here."],
            "state_profile_boundary": ["Do not blur page-flow state and business completion state here.", "Do not let non-canonical profile stores win body-field conflicts here."],
            "minimal_onboarding": ["Do not rewrite login/registration ownership here.", "Do not reintroduce device connection as a blocking prerequisite before homepage entry."],
            "adoption_e2e": ["Do not rewrite foundation FEAT internal semantics here.", "Do not create a parallel gate or audit decision model here."],
        }
        arch_out_of_scope.extend(defaults.get(axis, []))
    frontmatter = {
        "artifact_type": "ARCH",
        "status": json_payload["status"],
        "schema_version": "1.0.0",
        "arch_ref": refs["arch_ref"],
        "feat_ref": refs["feat_ref"],
        "source_refs": source_refs,
    }
    body = "\n\n".join(
        [
            f"# {refs['arch_ref']}",
            "## Boundary Placement\n\n" + "\n".join(f"- {item}" for item in architecture_topics(feature)),
            "## System Topology\n\n" + arch_diagram,
            "## Responsibility Split\n\n" + "\n".join(f"- {item}" for item in responsibility_splits(feature)),
            "## Dedicated Runtime Placement\n\n" + "\n".join(f"- {item}" for item in assessment["arch_rationale"]),
            "## Out of Scope\n\n" + "\n".join(f"- {item}" for item in unique_strings(arch_out_of_scope)[:4]),
        ]
    )
    return frontmatter, body


def build_api_docs(refs, source_refs, assessment, feature, api_specs, json_payload):
    if not assessment["api_required"]:
        return None, None
    frontmatter = {
        "artifact_type": "API",
        "status": json_payload["status"],
        "schema_version": "1.0.0",
        "api_ref": refs["api_ref"],
        "feat_ref": refs["feat_ref"],
        "source_refs": source_refs,
    }
    body = "\n\n".join(
        [
            f"# {refs['api_ref']}",
            "## Contract Scope\n\n" + "\n".join(f"- {item}" for item in api_surfaces(feature)),
            "## Response Envelope\n\n- Success envelope: `{ ok: true, command_ref, trace_ref, result }`\n- Error envelope: `{ ok: false, command_ref, trace_ref, error }`",
            "## Command Contracts\n\n" + "\n\n".join(
                "\n".join(
                    [
                        f"### `{spec['command']}`",
                        f"- Surface: {spec['surface']}",
                        "- Request schema:",
                        *[f"  - {item}" for item in spec["request_schema"]],
                        "- Response schema:",
                        *[f"  - {item}" for item in spec["response_schema"]],
                        "- Field semantics:",
                        *[f"  - {item}" for item in spec["field_semantics"]],
                        "- Enum / domain:",
                        *([f"  - {item}" for item in spec["enum_domain"]] or ["  - None"]),
                        "- Invariants:",
                        *[f"  - {item}" for item in spec["invariants"]],
                        "- Canonical refs:",
                        *[f"  - {item}" for item in spec["canonical_refs"]],
                        "- Errors:",
                        *[f"  - {item}" for item in spec["errors"]],
                        f"- Idempotency key: {spec['idempotency']}",
                        "- Preconditions:",
                        *[f"  - {item}" for item in spec["preconditions"]],
                    ]
                )
                for spec in api_specs
            ),
            "## Compatibility and Versioning\n\n" + "\n".join([f"- {item}" for item in api_compatibility_rules(feature)]),
        ]
    )
    return frontmatter, body
