#!/usr/bin/env python3
"""
Content builders for feat-to-tech package assembly.
"""

from __future__ import annotations

from feat_to_tech_common import ensure_list, unique_strings
from feat_to_tech_derivation import (
    api_command_specs,
    api_compatibility_rules,
    api_surfaces,
    architecture_diagram,
    architecture_topics,
    design_focus,
    exception_compensation,
    feature_axis,
    flow_diagram,
    implementation_architecture,
    implementation_modules,
    implementation_rules,
    implementation_strategy,
    implementation_unit_mapping,
    integration_points,
    interface_contracts,
    main_sequence,
    minimal_code_skeleton,
    non_functional_requirements,
    selected_feat_snapshot,
    state_model,
    tech_runtime_view,
    traceability_rows,
)
from feat_to_tech_governance import (
    algorithm_constraints,
    consistency_check,
    evaluate_stateful_design_present,
    io_matrix_and_side_effects,
    migration_constraints,
    state_machine,
    technical_glossary_and_canonical_ownership,
)
from feat_to_tech_integration_context import integration_sufficiency_check


DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"


def build_design_context(package, feature, refs, assessment, revision_context=None):
    rules = implementation_rules(feature)
    if revision_context and revision_context.get("summary"):
        rules = unique_strings(rules + [f"Revision constraint: {revision_context['summary']}"])
    integration_gate = integration_sufficiency_check(package.integration_context)
    assessment["integration_context_sufficient"] = integration_gate["passed"]
    assessment["integration_context_rationale"] = [integration_gate["summary"], *integration_gate["issues"]]
    state_machine_lines = state_machine(feature)
    io_matrix_lines = io_matrix_and_side_effects(feature)
    glossary_lines = technical_glossary_and_canonical_ownership(feature, package.integration_context)
    stateful_design_present, stateful_rationale = evaluate_stateful_design_present(state_machine_lines, io_matrix_lines, glossary_lines)
    assessment["stateful_design_present"] = stateful_design_present
    assessment["stateful_design_rationale"] = stateful_rationale
    context = {
        "focus": ensure_list(design_focus(feature)),
        "rules": rules,
        "nfrs": non_functional_requirements(feature, package),
        "implementation_arch": implementation_architecture(feature),
        "modules": implementation_modules(feature),
        "states": state_model(feature),
        "state_machine": state_machine_lines,
        "strategy": implementation_strategy(feature),
        "arch_diagram": architecture_diagram(feature),
        "runtime_view": tech_runtime_view(feature),
        "main_flow_diagram": flow_diagram(feature),
        "unit_mapping": implementation_unit_mapping(feature),
        "contracts": interface_contracts(feature),
        "sequence_steps": main_sequence(feature),
        "exception_rules": exception_compensation(feature),
        "integrations": integration_points(feature),
        "integration_context": package.integration_context,
        "integration_sufficiency": integration_gate,
        "algorithm_constraints": algorithm_constraints(feature, package.integration_context),
        "io_matrix": io_matrix_lines,
        "glossary_and_ownership": glossary_lines,
        "migration_constraints": migration_constraints(package.integration_context),
        "skeleton": minimal_code_skeleton(feature),
        "api_specs": api_command_specs(feature),
        "traceability": traceability_rows(feature, package, refs),
    }
    context["consistency"] = consistency_check(feature, assessment, context)
    return context


def build_source_refs(package, refs, feature, context):
    return unique_strings(
        [
            f"product.epic-to-feat::{package.run_id}",
            refs["feat_ref"],
            refs["tech_ref"],
            refs["epic_ref"],
            refs["src_ref"],
            str(feature.get("surface_map_ref") or ""),
        ]
        + ensure_list(feature.get("source_refs"))
        + ensure_list(package.feat_json.get("source_refs"))
        + ensure_list(context["integration_context"].get("source_refs"))
    )


def build_defects(focus, consistency, semantic_drift_check, assessment=None):
    assessment = assessment or {
        "integration_context_sufficient": True,
        "integration_context_rationale": [],
        "stateful_design_present": True,
        "stateful_design_rationale": [],
    }
    defects: list[dict[str, str]] = []
    if not [str(item).strip() for item in focus if str(item).strip()]:
        defects.append({"severity": "P1", "title": "TECH design focus is too thin", "detail": "The selected FEAT does not expose enough scope or constraint detail to support a robust TECH design."})
    if not assessment["integration_context_sufficient"]:
        defects.append({"severity": "P1", "title": "integration_context is insufficient", "detail": "; ".join(assessment["integration_context_rationale"])})
    if not assessment["stateful_design_present"]:
        defects.append({"severity": "P1", "title": "Stateful design facts are missing", "detail": "; ".join(assessment["stateful_design_rationale"])})
    if not consistency["passed"]:
        defects.append({"severity": "P1", "title": "Cross-artifact consistency failed", "detail": "; ".join(consistency["issues"])})
    if semantic_drift_check["verdict"] == "reject":
        defects.append({"severity": "P1", "title": "semantic_lock drift detected", "detail": semantic_drift_check["summary"]})
    if semantic_drift_check.get("axis_conflicts"):
        defects.append(
            {
                "severity": "P1",
                "title": "Resolved axis conflicts with generated TECH keyword family",
                "detail": "; ".join(semantic_drift_check["axis_conflicts"]),
            }
        )
    for issue in semantic_drift_check.get("carrier_topic_issues") or []:
        defects.append({"severity": "P1", "title": "TECH carrier drifted away from FEAT topic", "detail": issue})
    return defects


def build_artifact_refs(assessment):
    return {
        "tech_spec": "tech-spec.md",
        "integration_context": "integration-context.json",
        "arch_spec": "arch-design.md" if assessment["arch_required"] else None,
        "api_spec": "api-contract.md" if assessment["api_required"] else None,
    }


def build_handoff(run_id, refs, assessment, utc_now_fn):
    return {
        "handoff_id": f"handoff-{run_id}-to-tech-impl",
        "from_skill": "ll-dev-feat-to-tech",
        "source_run_id": run_id,
        "target_workflow": DOWNSTREAM_WORKFLOW,
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "surface_map_ref": refs.get("surface_map_ref"),
        "arch_ref": refs["arch_ref"] if assessment["arch_required"] else None,
        "api_ref": refs["api_ref"] if assessment["api_required"] else None,
        "primary_artifact_ref": "tech-design-bundle.md",
        "supporting_artifact_refs": ["tech-design-bundle.json", "tech-spec.md", "integration-context.json", *(["arch-design.md"] if assessment["arch_required"] else []), *(["api-contract.md"] if assessment["api_required"] else []), "tech-review-report.json", "tech-acceptance-report.json", "tech-defect-list.json"],
        "integration_context_ref": "integration-context.json",
        "canonical_owner_refs": ["tech-design-bundle.json#/tech_design/technical_glossary_and_canonical_ownership"],
        "state_machine_ref": "tech-design-bundle.json#/tech_design/state_machine",
        "nfr_constraints_ref": "tech-design-bundle.json#/tech_design/non_functional_requirements",
        "migration_constraints_ref": "tech-design-bundle.json#/tech_design/migration_constraints",
        "algorithm_constraint_refs": ["tech-design-bundle.json#/tech_design/algorithm_constraints"],
        "created_at": utc_now_fn(),
    }


def build_json_payload(run_id, feature, refs, source_refs, assessment, context, handoff, semantic_drift_check, artifact_refs, revision_context=None):
    return {
        "artifact_type": "tech_design_package",
        "workflow_key": "dev.feat-to-tech",
        "workflow_run_id": run_id,
        "title": f"{feature.get('title') or refs['feat_ref']} Technical Design Package",
        "status": build_status(context, semantic_drift_check, assessment),
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "surface_map_ref": str(feature.get("surface_map_ref") or ""),
        "owner_binding_status": str(feature.get("owner_binding_status") or ("bound" if str(feature.get("surface_map_ref") or "").strip() else "not_selected")),
        "arch_ref": refs["arch_ref"] if assessment["arch_required"] else None,
        "api_ref": refs["api_ref"] if assessment["api_required"] else None,
        "epic_freeze_ref": refs["epic_ref"],
        "src_root_id": refs["src_ref"],
        "source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
        "arch_required": assessment["arch_required"],
        "api_required": assessment["api_required"],
        "need_assessment": assessment,
        "selected_feat": {**selected_feat_snapshot(feature), "resolved_axis": feature_axis(feature)},
        "integration_context": context["integration_context"],
        "integration_sufficiency_check": context["integration_sufficiency"],
        "tech_design": build_tech_design_block(context),
        "optional_arch": build_optional_arch_block(feature, refs, assessment),
        "optional_api": build_optional_api_block(feature, refs, assessment, context["api_specs"]),
        "artifact_refs": artifact_refs,
        "design_consistency_check": context["consistency"],
        "downstream_handoff": handoff,
        "traceability": context["traceability"],
        "semantic_drift_check": semantic_drift_check,
        "revision_context": revision_context,
    }


def build_status(context, semantic_drift_check, assessment):
    if context["consistency"]["issues"] or semantic_drift_check["verdict"] == "reject" or len(context["focus"]) < 3 or not assessment["integration_context_sufficient"] or not assessment["stateful_design_present"]:
        return "revised"
    return "accepted"


def build_tech_design_block(context):
    return {
        "design_focus": context["focus"],
        "implementation_rules": context["rules"],
        "non_functional_requirements": context["nfrs"],
        "implementation_carrier_view": {"summary": context["implementation_arch"], "diagram": context["runtime_view"]},
        "implementation_architecture": context["implementation_arch"],
        "state_model": context["states"],
        "state_machine": context["state_machine"],
        "module_plan": context["modules"],
        "implementation_strategy": context["strategy"],
        "implementation_unit_mapping": context["unit_mapping"],
        "interface_contracts": context["contracts"],
        "main_sequence": context["sequence_steps"],
        "flow_diagram": context["main_flow_diagram"],
        "exception_and_compensation": context["exception_rules"],
        "integration_points": context["integrations"],
        "algorithm_constraints": context["algorithm_constraints"],
        "io_matrix_and_side_effects": context["io_matrix"],
        "technical_glossary_and_canonical_ownership": context["glossary_and_ownership"],
        "migration_constraints": context["migration_constraints"],
        "minimal_code_skeleton": context["skeleton"],
    }


def build_optional_arch_block(feature, refs, assessment):
    if not assessment["arch_required"]:
        return None
    return {"arch_ref": refs["arch_ref"], "topics": architecture_topics(feature), "rationale": assessment["arch_rationale"]}


def build_optional_api_block(feature, refs, assessment, api_specs):
    if not assessment["api_required"]:
        return None
    return {"api_ref": refs["api_ref"], "surfaces": api_surfaces(feature), "command_refs": [spec["command"] for spec in api_specs], "response_envelope": {"success": "{ ok: true, command_ref, trace_ref, result }", "error": "{ ok: false, command_ref, trace_ref, error }"}, "compatibility_rules": api_compatibility_rules(feature), "rationale": assessment["api_rationale"]}


def build_frontmatter(run_id, refs, assessment, source_refs, feature, status, revision_context=None):
    return {
        "artifact_type": "tech_design_package",
        "workflow_key": "dev.feat-to-tech",
        "workflow_run_id": run_id,
        "status": status,
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "surface_map_ref": str(feature.get("surface_map_ref") or ""),
        "arch_required": assessment["arch_required"],
        "api_required": assessment["api_required"],
        "integration_context_sufficient": assessment["integration_context_sufficient"],
        "stateful_design_present": assessment["stateful_design_present"],
        "source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
        **({"revision_request_ref": revision_context["revision_request_ref"], "revision_summary": revision_context["summary"]} if revision_context else {}),
    }


def build_review_report(run_id, refs, defects, consistency, semantic_drift_check, assessment, utc_now_fn):
    passed = not defects and consistency["passed"] and semantic_drift_check.get("review_gate_ok", True) and assessment["integration_context_sufficient"] and assessment["stateful_design_present"]
    return {"review_id": f"tech-review-{run_id}", "review_type": "tech_design_review", "subject_refs": [refs["feat_ref"], refs["tech_ref"]], "summary": "TECH package preserves FEAT traceability and downstream implementation readiness." if passed else "TECH package needs revision before it can be treated as aligned to the selected FEAT.", "findings": ["TECH is present and aligned to the selected FEAT." if passed else "TECH / FEAT semantic alignment is not yet credible.", "Optional companions were emitted only when need assessment required them.", "Integration sufficiency and stateful design checks were recorded before freeze.", "A final cross-artifact consistency check was recorded before freeze."], "decision": "pass" if passed else "revise", "risks": [defect["detail"] for defect in defects], "semantic_gate": semantic_drift_check, "created_at": utc_now_fn()}


def build_acceptance_report(defects, consistency, semantic_drift_check, assessment, utc_now_fn):
    passed = not defects and consistency["passed"] and semantic_drift_check.get("review_gate_ok", True) and assessment["integration_context_sufficient"] and assessment["stateful_design_present"]
    return {"stage_id": "tech_acceptance_review", "created_by_role": "supervisor", "decision": "approve" if passed else "revise", "dimensions": {"tech_presence": {"status": "pass", "note": "TECH is mandatory and present."}, "optional_outputs_match_assessment": {"status": "pass" if passed else "fail", "note": "Optional ARCH/API outputs align with the need assessment." if passed else "Optional outputs need revision."}, "integration_sufficiency": {"status": "pass" if assessment["integration_context_sufficient"] else "fail", "note": assessment["integration_context_rationale"][0] if assessment["integration_context_rationale"] else "integration context checked"}, "stateful_design": {"status": "pass" if assessment["stateful_design_present"] else "fail", "note": "; ".join(assessment["stateful_design_rationale"])}, "cross_artifact_consistency": {"status": "pass" if consistency["passed"] else "fail", "note": "ARCH, TECH, and API remain aligned." if consistency["passed"] else "Consistency issues remain open."}, "semantic_alignment": {"status": "pass" if semantic_drift_check.get("review_gate_ok", True) else "fail", "note": "TECH carrier, state, and interface topics remain aligned to the selected FEAT." if semantic_drift_check.get("review_gate_ok", True) else "TECH semantic gate detected topic drift or semantic_lock mismatch."}, "downstream_readiness": {"status": "pass" if passed else "fail", "note": "Output remains actionable for workflow.dev.tech_to_impl." if passed else "Output is not freeze-ready for downstream implementation planning."}}, "summary": "TECH acceptance review passed." if passed else "TECH acceptance review requires revision.", "acceptance_findings": defects, "semantic_gate": semantic_drift_check, "created_at": utc_now_fn()}


def build_execution_decisions(package, refs, assessment, revision_context=None):
    decisions = [f"Selected FEAT {refs['feat_ref']} from upstream run {package.run_id}.", f"ARCH required: {assessment['arch_required']}.", f"API required: {assessment['api_required']}.", f"Integration context sufficient: {assessment['integration_context_sufficient']}.", f"Stateful design present: {assessment['stateful_design_present']}.", f"Prepared downstream handoff to {DOWNSTREAM_WORKFLOW}."]
    if revision_context and revision_context.get("summary"):
        decisions.append(f"Applied revision context: {revision_context['summary']}")
    return decisions
