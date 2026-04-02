#!/usr/bin/env python3
"""
Package assembly helpers for feat-to-tech runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.workflow_revision import normalize_revision_context
from feat_to_tech_common import (
    derive_semantic_lock,
    enrich_feature_execution_metadata,
    ensure_list,
    normalize_semantic_lock,
    unique_strings,
)
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
from feat_to_tech_documents import build_api_docs, build_arch_docs, build_markdown_body, build_tech_docs

DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"

TOPIC_FAMILIES = {
    "first_ai_advice": {
        "markers": [
            "generatefirstadvice",
            "evaluatefirstadviceriskgate",
            "training_advice_level",
            "first_week_action",
            "needs_more_info_prompt",
            "device_connect_prompt",
            "firstadvicepanel",
            "advice_visible",
        ],
        "min_hits": 2,
    },
    "extended_profile_completion": {
        "markers": [
            "saveextendedprofilepatch",
            "getprofilecompletiontasks",
            "profile_extension_in_progress",
            "profile_extension_done",
            "incrementalsave",
            "taskcard",
            "completionupdater",
        ],
        "min_hits": 2,
    },
    "device_deferred_entry": {
        "markers": [
            "startdeferreddeviceconnection",
            "finalizedeviceconnection",
            "device_connection_offered",
            "device_failed_nonblocking",
            "device_skipped",
            "deferreddeviceentry",
            "homepage_entered",
        ],
        "min_hits": 2,
    },
    "state_profile_boundary": {
        "markers": [
            "writeprimarystate",
            "writecapabilityflags",
            "writephysicalprofilecanonical",
            "readunifiedonboardingstate",
            "primary_state",
            "capability_flags",
            "canonical_profile_boundary",
            "conflict_blocked",
            "user_physical_profile",
        ],
        "min_hits": 2,
    },
    "minimal_onboarding": {
        "markers": [
            "submitminimalprofile",
            "profile_minimal_done",
            "homepageentryguard",
            "minimalprofilepage",
            "device_connection_deferred",
            "homepageentryallowed",
            "post/v1/onboarding/minimal-profile",
        ],
        "min_hits": 2,
    },
    "adoption_e2e": {
        "markers": [
            "onboardingdirective",
            "pilotevidencesubmission",
            "llrolloutonboard-skill",
            "pilotchain",
            "cutover",
            "compat_mode",
            "rolloutstate",
            "fallback_triggered",
        ],
        "min_hits": 2,
    },
    "formalization": {
        "markers": [
            "gatedecision",
            "gatebriefrecord",
            "llgateevaluate",
            "llgatedispatch",
            "decision_target",
            "pendinghumandecision",
            "formalpublication",
        ],
        "min_hits": 2,
    },
    "collaboration": {
        "markers": [
            "handoffenvelope",
            "decisionreturnenvelope",
            "gatependingref",
            "authoritativehandoff",
        ],
        "min_hits": 2,
    },
    "layering": {
        "markers": [
            "admissionrequest",
            "lineageresolverequest",
            "formalrefs",
            "candidatepackage",
            "authoritativeformalref",
        ],
        "min_hits": 2,
    },
    "io_governance": {
        "markers": [
            "gatewaywriterequest",
            "policyverdict",
            "managedref",
            "registryrecordref",
            "logicalpath",
        ],
        "min_hits": 2,
    },
}

PRODUCT_AXIS_IDS = {
    "minimal-onboarding-flow",
    "first-ai-advice-release",
    "extended-profile-progressive-completion",
    "device-connect-deferred-entry",
    "state-and-profile-boundary-alignment",
}


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
    revision_context: dict[str, Any] | None


def build_semantic_drift_check(feature: dict[str, Any], generated_text_parts: list[str]) -> dict[str, Any]:
    lock = normalize_semantic_lock(feature.get("semantic_lock"))
    axis = feature_axis(feature)
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    generated_text = compact_text(" ".join(part for part in generated_text_parts if str(part).strip()))
    forbidden_hits = [item for item in lock.get("forbidden_capabilities", []) if compact_text(str(item)) in generated_text]
    anchor_matches = collect_anchor_matches(feature, lock, generated_text)
    matched_allowed_capabilities = [
        item for item in ensure_list(lock.get("allowed_capabilities")) if compact_text(str(item)) in generated_text
    ]
    family_hits = topic_family_hits(generated_text)
    axis_conflicts = collect_axis_conflicts(axis, family_hits)
    carrier_topic_issues = collect_carrier_topic_issues(feature, axis, family_hits, axis_conflicts, matched_allowed_capabilities)
    if axis == "generic" and axis_id in PRODUCT_AXIS_IDS:
        carrier_topic_issues.append(f"explicit product axis `{axis_id}` resolved to generic TECH output")
    topic_alignment_ok = not axis_conflicts and not carrier_topic_issues
    implementation_readiness_signature = False
    if str(lock.get("domain_type") or "").strip().lower() == "implementation_readiness_rule":
        implementation_readiness_signature = any(
            token in generated_text
            for token in [
                "implementationreadiness",
                "implreadiness",
                "qaimplspectest",
            ]
        )
        if implementation_readiness_signature and "implementation_readiness_signature" not in anchor_matches:
            anchor_matches.append("implementation_readiness_signature")
    lock_gate_ok = True if not lock else (len(anchor_matches) >= 1 or len(matched_allowed_capabilities) >= 2 or implementation_readiness_signature)
    preserved = not forbidden_hits and topic_alignment_ok and lock_gate_ok
    return {
        "verdict": "pass" if preserved else "reject",
        "semantic_lock_present": bool(lock),
        "semantic_lock_preserved": preserved,
        "topic_alignment_ok": topic_alignment_ok,
        "lock_gate_ok": lock_gate_ok,
        "review_gate_ok": preserved,
        "domain_type": lock.get("domain_type"),
        "one_sentence_truth": lock.get("one_sentence_truth"),
        "matched_allowed_capabilities": matched_allowed_capabilities,
        "forbidden_axis_detected": forbidden_hits,
        "axis_conflicts": axis_conflicts,
        "carrier_topic_issues": carrier_topic_issues,
        "anchor_matches": anchor_matches,
        "summary": (
            "semantic_lock preserved."
            if lock and preserved
            else "topic alignment preserved."
            if preserved
            else "semantic_lock drift detected."
        ),
    }


def compact_text(text: str) -> str:
    return "".join(str(text).lower().split())


def topic_family_hits(generated_text: str) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for axis, family in TOPIC_FAMILIES.items():
        axis_hits = [marker for marker in family["markers"] if marker in generated_text]
        if axis_hits:
            hits[axis] = axis_hits
    return hits


def collect_axis_conflicts(axis: str, family_hits: dict[str, list[str]]) -> list[str]:
    conflicts: list[str] = []
    selected_family = TOPIC_FAMILIES.get(axis)
    selected_hits = family_hits.get(axis, [])
    if not selected_family:
        return conflicts
    if len(selected_hits) >= selected_family["min_hits"]:
        return conflicts
    for foreign_axis, foreign_hits in family_hits.items():
        if foreign_axis == axis:
            continue
        if len(foreign_hits) >= 2:
            conflicts.append(f"{foreign_axis}: " + ", ".join(foreign_hits[:4]))
    return conflicts


def collect_carrier_topic_issues(
    feature: dict[str, Any],
    axis: str,
    family_hits: dict[str, list[str]],
    axis_conflicts: list[str],
    matched_allowed_capabilities: list[str],
) -> list[str]:
    issues: list[str] = []
    selected_family = TOPIC_FAMILIES.get(axis)
    selected_hits = family_hits.get(axis, [])
    if selected_family and len(selected_hits) < selected_family["min_hits"]:
        issues.append(
            f"{axis} TECH did not preserve enough topic markers: "
            + (", ".join(selected_hits[:4]) if selected_hits else "none")
        )
    if axis_conflicts:
        issues.append("Resolved axis conflicts with foreign topic family: " + "; ".join(axis_conflicts))
    if axis == "minimal_onboarding" and matched_allowed_capabilities and len(matched_allowed_capabilities) < 2:
        issues.append("minimal_onboarding TECH did not preserve enough minimal-profile/homepage-entry capability markers.")
    identity = feature.get("identity_and_scenario") if isinstance(feature.get("identity_and_scenario"), dict) else {}
    completed_state = str(identity.get("completed_state") or "").strip().lower()
    if axis == "minimal_onboarding" and completed_state:
        if "首页" in completed_state and "homepage" not in compact_text(completed_state) and "homepage" not in "".join(selected_hits):
            issues.append("minimal_onboarding completed_state mentions homepage entry, but generated TECH does not mention homepage entry.")
        if ("设备" in completed_state or "device" in completed_state) and "device" not in "".join(selected_hits):
            issues.append("minimal_onboarding completed_state mentions deferred device connection, but generated TECH does not mention device handling.")
    return issues


def collect_anchor_matches(feature: dict[str, Any], lock: dict[str, Any], generated_text: str) -> list[str]:
    matches: list[str] = []
    token_groups = {
        "domain_type": [compact_text(str(lock.get("domain_type") or ""))],
        "primary_object": [compact_text(str(lock.get("primary_object") or ""))],
        "lifecycle_stage": [compact_text(str(lock.get("lifecycle_stage") or ""))],
    }
    for label, tokens in token_groups.items():
        tokens = [token for token in tokens if token]
        if tokens and all(token in generated_text for token in tokens):
            matches.append(label)
    if str(lock.get("domain_type") or "").strip().lower() == "review_projection_rule":
        if explicit_axis(feature) in {"projection_generation", "authoritative_snapshot", "review_focus_risk", "feedback_writeback"}:
            matches.append("review_projection_axis")
        if all(token in generated_text for token in ["projection", "gate", "ssot"]):
            matches.append("review_projection_signature")
    if str(lock.get("domain_type") or "").strip().lower() == "execution_runner_rule":
        axis = explicit_axis(feature)
        execution_runner_signatures = {
            "runner_ready_job": ["ready", "job", "runner"],
            "runner_operator_entry": ["runner", "operator"],
            "runner_control_surface": ["runner", "control"],
            "runner_intake": ["runner", "claim"],
            "runner_dispatch": ["next", "skill", "dispatch"],
            "runner_feedback": ["execution", "retry"],
            "runner_observability": ["runner", "observability"],
        }
        if axis in execution_runner_signatures:
            matches.append("execution_runner_axis")
            if all(token in generated_text for token in execution_runner_signatures[axis]):
                matches.append("execution_runner_signature")
    return matches


def _build_revision_context(revision_request: dict[str, Any] | None) -> dict[str, Any] | None:
    context = normalize_revision_context(revision_request, ensure_list=ensure_list)
    return context or None


def build_tech_package(
    package: Any,
    feature: dict[str, Any],
    feat_ref: str,
    run_id: str,
    utc_now_fn,
    revision_request: dict[str, Any] | None = None,
) -> GeneratedTechPackage:
    repo_root = package.artifacts_dir.parents[2]
    feature = enrich_feature_execution_metadata(repo_root, dict(feature))
    feature["semantic_lock"] = derive_semantic_lock(feature, package.semantic_lock)
    refs = build_refs(feature, package)
    assessment = assess_optional_artifacts(feature, package)
    revision_context = _build_revision_context(revision_request)
    context = build_design_context(package, feature, refs, assessment, revision_context)
    source_refs = build_source_refs(package, refs, feature)
    semantic_drift_check = build_semantic_drift_check(
        feature,
        [
            str(feature.get("title") or ""),
            str(feature.get("goal") or ""),
            feature_axis(feature),
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
    json_payload = build_json_payload(
        run_id,
        feature,
        refs,
        source_refs,
        assessment,
        context,
        handoff,
        semantic_drift_check,
        artifact_refs,
        revision_context,
    )
    frontmatter = build_frontmatter(run_id, refs, assessment, source_refs, feature, json_payload["status"], revision_context)
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
    if revision_context:
        for block in [frontmatter, tech_frontmatter, arch_frontmatter, api_frontmatter]:
            if block is None:
                continue
            block["revision_request_ref"] = revision_context["revision_request_ref"]
            block["revision_summary"] = revision_context["summary"]
    review_report = build_review_report(run_id, refs, defects, context["consistency"], semantic_drift_check, utc_now_fn)
    acceptance_report = build_acceptance_report(defects, context["consistency"], semantic_drift_check, utc_now_fn)
    execution_decisions = build_execution_decisions(package, refs, assessment, revision_context)
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
        revision_context=revision_context,
    )


def build_design_context(package, feature, refs, assessment, revision_context=None):
    rules = implementation_rules(feature)
    if revision_context and revision_context.get("summary"):
        rules = unique_strings(rules + [f"Revision constraint: {revision_context['summary']}"])
    return {
        "focus": ensure_list(design_focus(feature)),
        "rules": rules,
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
    focus_items = [str(item).strip() for item in focus if str(item).strip()]
    if not focus_items:
        defects.append({"severity": "P1", "title": "TECH design focus is too thin", "detail": "The selected FEAT does not expose enough scope or constraint detail to support a robust TECH design."})
    if not consistency["passed"]:
        defects.append({"severity": "P1", "title": "Cross-artifact consistency failed", "detail": "; ".join(consistency["issues"])})
    if semantic_drift_check["verdict"] == "reject":
        defects.append({"severity": "P1", "title": "semantic_lock drift detected", "detail": semantic_drift_check["summary"]})
    for issue in semantic_drift_check.get("carrier_topic_issues") or []:
        defects.append({"severity": "P1", "title": "TECH carrier drifted away from FEAT topic", "detail": issue})
    axis_conflicts = semantic_drift_check.get("axis_conflicts") or []
    if axis_conflicts:
        defects.append({
            "severity": "P1",
            "title": "Resolved axis conflicts with generated TECH keyword family",
            "detail": "Conflicting markers: " + ", ".join(str(item) for item in axis_conflicts),
        })
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


def build_json_payload(run_id, feature, refs, source_refs, assessment, context, handoff, semantic_drift_check, artifact_refs, revision_context=None):
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
        "selected_feat": {**selected_feat_snapshot(feature), "resolved_axis": feature_axis(feature)},
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


def build_frontmatter(run_id, refs, assessment, source_refs, feature, status, revision_context=None):
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
        **(
            {
                "revision_request_ref": revision_context["revision_request_ref"],
                "revision_summary": revision_context["summary"],
            }
            if revision_context
            else {}
        ),
    }


def build_review_report(run_id, refs, defects, consistency, semantic_drift_check, utc_now_fn):
    passed = not defects and consistency["passed"] and semantic_drift_check.get("review_gate_ok", True)
    return {
        "review_id": f"tech-review-{run_id}",
        "review_type": "tech_design_review",
        "subject_refs": [refs["feat_ref"], refs["tech_ref"]],
        "summary": "TECH package preserves FEAT traceability and downstream implementation readiness." if passed else "TECH package needs revision before it can be treated as aligned to the selected FEAT.",
        "findings": [
            "TECH is present and aligned to the selected FEAT." if passed else "TECH / FEAT semantic alignment is not yet credible.",
            "Optional companions were emitted only when need assessment required them.",
            "A final cross-artifact consistency check was recorded before freeze.",
        ],
        "decision": "pass" if passed else "revise",
        "risks": [defect["detail"] for defect in defects],
        "semantic_gate": semantic_drift_check,
        "created_at": utc_now_fn(),
    }


def build_acceptance_report(defects, consistency, semantic_drift_check, utc_now_fn):
    passed = not defects and consistency["passed"] and semantic_drift_check.get("review_gate_ok", True)
    return {
        "stage_id": "tech_acceptance_review",
        "created_by_role": "supervisor",
        "decision": "approve" if passed else "revise",
        "dimensions": {
            "tech_presence": {"status": "pass", "note": "TECH is mandatory and present."},
            "optional_outputs_match_assessment": {
                "status": "pass" if passed else "fail",
                "note": "Optional ARCH/API outputs align with the need assessment." if passed else "Optional outputs need revision.",
            },
            "cross_artifact_consistency": {
                "status": "pass" if consistency["passed"] else "fail",
                "note": "ARCH, TECH, and API remain aligned." if consistency["passed"] else "Consistency issues remain open.",
            },
            "semantic_alignment": {
                "status": "pass" if semantic_drift_check.get("review_gate_ok", True) else "fail",
                "note": (
                    "TECH carrier, state, and interface topics remain aligned to the selected FEAT."
                    if semantic_drift_check.get("review_gate_ok", True)
                    else "TECH semantic gate detected topic drift or semantic_lock mismatch."
                ),
            },
            "downstream_readiness": {
                "status": "pass" if passed else "fail",
                "note": "Output remains actionable for workflow.dev.tech_to_impl." if passed else "Output is not freeze-ready for downstream implementation planning.",
            },
        },
        "summary": "TECH acceptance review passed." if passed else "TECH acceptance review requires revision.",
        "acceptance_findings": defects,
        "semantic_gate": semantic_drift_check,
        "created_at": utc_now_fn(),
    }


def build_execution_decisions(package, refs, assessment, revision_context=None):
    decisions = [
        f"Selected FEAT {refs['feat_ref']} from upstream run {package.run_id}.",
        f"ARCH required: {assessment['arch_required']}.",
        f"API required: {assessment['api_required']}.",
        f"Prepared downstream handoff to {DOWNSTREAM_WORKFLOW}.",
    ]
    if revision_context and revision_context.get("summary"):
        decisions.append(f"Applied revision context: {revision_context['summary']}")
    return decisions
