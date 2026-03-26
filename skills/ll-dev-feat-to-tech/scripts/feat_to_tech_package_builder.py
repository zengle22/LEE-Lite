#!/usr/bin/env python3
"""
Package assembly helpers for feat-to-tech runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from feat_to_tech_common import ensure_list, normalize_semantic_lock, unique_strings
from feat_to_tech_derivation import (
    api_command_specs,
    api_compatibility_rules,
    api_surfaces,
    architecture_diagram,
    architecture_topics,
    assess_optional_artifacts,
    build_refs,
    consistency_check,
    design_focus,
    exception_compensation,
    explicit_axis,
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
from feat_to_tech_documents import build_api_docs, build_arch_docs, build_markdown_body, build_tech_docs

DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"


@dataclass
class GeneratedTechPackage:
    run_id: str
    frontmatter: dict[str, Any]
    markdown_body: str
    json_payload: dict[str, Any]
    tech_frontmatter: dict[str, Any]
    tech_body: str
    arch_frontmatter: dict[str, Any] | None
    arch_body: str | None
    api_frontmatter: dict[str, Any] | None
    api_body: str | None
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    handoff: dict[str, Any]
    semantic_drift_check: dict[str, Any]
    execution_decisions: list[str]
    execution_uncertainties: list[str]


def build_semantic_drift_check(feature: dict[str, Any], generated_text_parts: list[str]) -> dict[str, Any]:
    lock = normalize_semantic_lock(feature.get("semantic_lock"))
    if not lock:
        return {
            "verdict": "not_applicable",
            "semantic_lock_present": False,
            "semantic_lock_preserved": True,
            "forbidden_axis_detected": [],
            "anchor_matches": [],
            "summary": "No semantic_lock present.",
        }

    generated_text = " ".join(part for part in generated_text_parts if str(part).strip()).lower()
    forbidden_hits = [item for item in lock.get("forbidden_capabilities", []) if str(item).strip().lower() in generated_text]
    anchor_matches = collect_anchor_matches(feature, lock, generated_text)
    preserved = not forbidden_hits and len(anchor_matches) >= 1
    return {
        "verdict": "pass" if preserved else "reject",
        "semantic_lock_present": True,
        "semantic_lock_preserved": preserved,
        "domain_type": lock.get("domain_type"),
        "one_sentence_truth": lock.get("one_sentence_truth"),
        "forbidden_axis_detected": forbidden_hits,
        "anchor_matches": anchor_matches,
        "summary": "semantic_lock preserved." if preserved else "semantic_lock drift detected.",
    }


def collect_anchor_matches(feature: dict[str, Any], lock: dict[str, Any], generated_text: str) -> list[str]:
    matches: list[str] = []
    token_groups = {
        "domain_type": [str(lock.get("domain_type") or "").replace("_", " ").lower()],
        "primary_object": [token for token in str(lock.get("primary_object") or "").replace("_", " ").lower().split() if token],
        "lifecycle_stage": [token for token in str(lock.get("lifecycle_stage") or "").replace("_", " ").lower().split() if token],
    }
    for label, tokens in token_groups.items():
        if tokens and all(token in generated_text for token in tokens):
            matches.append(label)
    if str(lock.get("domain_type") or "").strip().lower() == "review_projection_rule":
        if explicit_axis(feature) in {"projection_generation", "authoritative_snapshot", "review_focus_risk", "feedback_writeback"}:
            matches.append("review_projection_axis")
        if all(token in generated_text for token in ["projection", "gate", "ssot"]):
            matches.append("review_projection_signature")
    return matches


def build_tech_package(package: Any, feature: dict[str, Any], feat_ref: str, run_id: str, utc_now_fn) -> GeneratedTechPackage:
    feature = dict(feature)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)
    refs = build_refs(feature, package)
    assessment = assess_optional_artifacts(feature, package)
    context = build_design_context(package, feature, refs, assessment)
    source_refs = build_source_refs(package, refs, feature)
    semantic_drift_check = build_semantic_drift_check(
        feature,
        [
            str(feature.get("title") or ""),
            str(feature.get("goal") or ""),
            explicit_axis(feature) or "",
            " ".join(context["focus"]),
            " ".join(context["rules"]),
            " ".join(context["implementation_arch"]),
            " ".join(context["modules"]),
            " ".join(context["contracts"]),
            " ".join(context["integrations"]),
        ],
    )
    defects = build_defects(context["focus"], context["consistency"], semantic_drift_check)
    artifact_refs = build_artifact_refs(assessment)
    handoff = build_handoff(run_id, refs, assessment, utc_now_fn)
    json_payload = build_json_payload(run_id, feature, refs, source_refs, assessment, context, handoff, semantic_drift_check, artifact_refs)
    frontmatter = build_frontmatter(run_id, refs, assessment, source_refs, feature, json_payload["status"])
    markdown_body = build_markdown_body(
        json_payload,
        feature,
        refs,
        assessment,
        context["focus"],
        context["rules"],
        context["nfrs"],
        context["implementation_arch"],
        context["runtime_view"],
        context["states"],
        context["modules"],
        context["strategy"],
        context["unit_mapping"],
        context["contracts"],
        context["sequence_steps"],
        context["main_flow_diagram"],
        context["exception_rules"],
        context["integrations"],
        context["skeleton"],
        context["api_specs"],
        context["consistency"],
        context["traceability"],
    )
    tech_frontmatter, tech_body = build_tech_docs(refs, source_refs, feature, context["focus"], context["rules"], context["nfrs"], context["implementation_arch"], context["runtime_view"], context["states"], context["modules"], context["strategy"], context["unit_mapping"], context["contracts"], context["sequence_steps"], context["main_flow_diagram"], context["exception_rules"], context["integrations"], context["skeleton"], context["traceability"], json_payload)
    arch_frontmatter, arch_body = build_arch_docs(feature, refs, source_refs, assessment, context["arch_diagram"], json_payload)
    api_frontmatter, api_body = build_api_docs(refs, source_refs, assessment, feature, context["api_specs"], json_payload)
    review_report = build_review_report(run_id, refs, defects, utc_now_fn)
    acceptance_report = build_acceptance_report(defects, context["consistency"], utc_now_fn)
    execution_decisions = build_execution_decisions(package, refs, assessment)
    return GeneratedTechPackage(
        run_id=run_id,
        frontmatter=frontmatter,
        markdown_body=markdown_body,
        json_payload=json_payload,
        tech_frontmatter=tech_frontmatter,
        tech_body=tech_body,
        arch_frontmatter=arch_frontmatter,
        arch_body=arch_body,
        api_frontmatter=api_frontmatter,
        api_body=api_body,
        review_report=review_report,
        acceptance_report=acceptance_report,
        defect_list=defects,
        handoff=handoff,
        semantic_drift_check=semantic_drift_check,
        execution_decisions=execution_decisions,
        execution_uncertainties=context["consistency"]["issues"][:],
    )


def build_design_context(package, feature, refs, assessment):
    return {
        "focus": design_focus(feature),
        "rules": implementation_rules(feature),
        "nfrs": non_functional_requirements(feature, package),
        "implementation_arch": implementation_architecture(feature),
        "modules": implementation_modules(feature),
        "states": state_model(feature),
        "strategy": implementation_strategy(feature),
        "arch_diagram": architecture_diagram(feature),
        "runtime_view": tech_runtime_view(feature),
        "main_flow_diagram": flow_diagram(feature),
        "unit_mapping": implementation_unit_mapping(feature),
        "contracts": interface_contracts(feature),
        "sequence_steps": main_sequence(feature),
        "exception_rules": exception_compensation(feature),
        "integrations": integration_points(feature),
        "skeleton": minimal_code_skeleton(feature),
        "api_specs": api_command_specs(feature),
        "traceability": traceability_rows(feature, package, refs),
        "consistency": consistency_check(feature, assessment),
    }


def build_source_refs(package, refs, feature):
    return unique_strings(
        [f"product.epic-to-feat::{package.run_id}", refs["feat_ref"], refs["tech_ref"], refs["epic_ref"], refs["src_ref"]]
        + ensure_list(feature.get("source_refs"))
        + ensure_list(package.feat_json.get("source_refs"))
    )


def build_defects(focus, consistency, semantic_drift_check):
    defects: list[dict[str, Any]] = []
    if len(focus) < 3:
        defects.append({"severity": "P1", "title": "TECH design focus is too thin", "detail": "The selected FEAT does not expose enough scope or constraint detail to support a robust TECH design."})
    if not consistency["passed"]:
        defects.append({"severity": "P1", "title": "Cross-artifact consistency failed", "detail": "; ".join(consistency["issues"])})
    if semantic_drift_check["verdict"] == "reject":
        defects.append({"severity": "P1", "title": "semantic_lock drift detected", "detail": semantic_drift_check["summary"]})
    return defects


def build_artifact_refs(assessment):
    return {
        "tech_spec": "tech-spec.md",
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
        "arch_ref": refs["arch_ref"] if assessment["arch_required"] else None,
        "api_ref": refs["api_ref"] if assessment["api_required"] else None,
        "primary_artifact_ref": "tech-design-bundle.md",
        "supporting_artifact_refs": [
            "tech-design-bundle.json",
            "tech-spec.md",
            *(["arch-design.md"] if assessment["arch_required"] else []),
            *(["api-contract.md"] if assessment["api_required"] else []),
            "tech-review-report.json",
            "tech-acceptance-report.json",
            "tech-defect-list.json",
        ],
        "created_at": utc_now_fn(),
    }


def build_json_payload(run_id, feature, refs, source_refs, assessment, context, handoff, semantic_drift_check, artifact_refs):
    return {
        "artifact_type": "tech_design_package",
        "workflow_key": "dev.feat-to-tech",
        "workflow_run_id": run_id,
        "title": f"{feature.get('title') or refs['feat_ref']} Technical Design Package",
        "status": build_status(context, semantic_drift_check),
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"] if assessment["arch_required"] else None,
        "api_ref": refs["api_ref"] if assessment["api_required"] else None,
        "epic_freeze_ref": refs["epic_ref"],
        "src_root_id": refs["src_ref"],
        "source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
        "arch_required": assessment["arch_required"],
        "api_required": assessment["api_required"],
        "need_assessment": assessment,
        "selected_feat": {**selected_feat_snapshot(feature), "resolved_axis": explicit_axis(feature) or "derived"},
        "tech_design": build_tech_design_block(context),
        "optional_arch": build_optional_arch_block(feature, refs, assessment),
        "optional_api": build_optional_api_block(feature, refs, assessment, context["api_specs"]),
        "artifact_refs": artifact_refs,
        "design_consistency_check": context["consistency"],
        "downstream_handoff": handoff,
        "traceability": context["traceability"],
        "semantic_drift_check": semantic_drift_check,
    }


def build_status(context, semantic_drift_check):
    if context["consistency"]["issues"] or semantic_drift_check["verdict"] == "reject" or len(context["focus"]) < 3:
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
        "module_plan": context["modules"],
        "implementation_strategy": context["strategy"],
        "implementation_unit_mapping": context["unit_mapping"],
        "interface_contracts": context["contracts"],
        "main_sequence": context["sequence_steps"],
        "flow_diagram": context["main_flow_diagram"],
        "exception_and_compensation": context["exception_rules"],
        "integration_points": context["integrations"],
        "minimal_code_skeleton": context["skeleton"],
    }


def build_optional_arch_block(feature, refs, assessment):
    if not assessment["arch_required"]:
        return None
    return {"arch_ref": refs["arch_ref"], "topics": architecture_topics(feature), "rationale": assessment["arch_rationale"]}


def build_optional_api_block(feature, refs, assessment, api_specs):
    if not assessment["api_required"]:
        return None
    return {
        "api_ref": refs["api_ref"],
        "surfaces": api_surfaces(feature),
        "command_refs": [spec["command"] for spec in api_specs],
        "response_envelope": {
            "success": "{ ok: true, command_ref, trace_ref, result }",
            "error": "{ ok: false, command_ref, trace_ref, error }",
        },
        "compatibility_rules": api_compatibility_rules(feature),
        "rationale": assessment["api_rationale"],
    }


def build_frontmatter(run_id, refs, assessment, source_refs, feature, status):
    return {
        "artifact_type": "tech_design_package",
        "workflow_key": "dev.feat-to-tech",
        "workflow_run_id": run_id,
        "status": status,
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_required": assessment["arch_required"],
        "api_required": assessment["api_required"],
        "source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
    }


def build_review_report(run_id, refs, defects, utc_now_fn):
    return {
        "review_id": f"tech-review-{run_id}",
        "review_type": "tech_design_review",
        "subject_refs": [refs["feat_ref"], refs["tech_ref"]],
        "summary": "TECH package preserves FEAT traceability and downstream implementation readiness.",
        "findings": [
            "TECH is present and aligned to the selected FEAT.",
            "Optional companions were emitted only when need assessment required them.",
            "A final cross-artifact consistency check was recorded before freeze.",
        ],
        "decision": "pass" if not defects else "revise",
        "risks": [defect["detail"] for defect in defects],
        "created_at": utc_now_fn(),
    }


def build_acceptance_report(defects, consistency, utc_now_fn):
    return {
        "stage_id": "tech_acceptance_review",
        "created_by_role": "supervisor",
        "decision": "approve" if not defects else "revise",
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
                "note": "Output remains actionable for workflow.dev.tech_to_impl." if not defects else "Output is not freeze-ready for downstream implementation planning.",
            },
        },
        "summary": "TECH acceptance review passed." if not defects else "TECH acceptance review requires revision.",
        "acceptance_findings": defects,
        "created_at": utc_now_fn(),
    }


def build_execution_decisions(package, refs, assessment):
    return [
        f"Selected FEAT {refs['feat_ref']} from upstream run {package.run_id}.",
        f"ARCH required: {assessment['arch_required']}.",
        f"API required: {assessment['api_required']}.",
        f"Prepared downstream handoff to {DOWNSTREAM_WORKFLOW}.",
    ]
