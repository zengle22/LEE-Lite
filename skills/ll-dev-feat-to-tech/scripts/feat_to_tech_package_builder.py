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
from feat_to_tech_common import derive_semantic_lock, enrich_feature_execution_metadata, ensure_list, normalize_semantic_lock
from feat_to_tech_derivation import build_refs, explicit_axis, feature_axis
from feat_to_tech_documents import build_api_docs, build_arch_docs, build_markdown_body, build_tech_docs
from feat_to_tech_governance import assess_optional_artifacts
from feat_to_tech_package_content import (
    build_acceptance_report,
    build_artifact_refs,
    build_defects,
    build_design_context,
    build_execution_decisions,
    build_frontmatter,
    build_handoff,
    build_json_payload,
    build_review_report,
    build_source_refs,
)

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
    assessment = assess_optional_artifacts(feature, package.integration_context)
    revision_context = _build_revision_context(revision_request)
    context = build_design_context(package, feature, refs, assessment, revision_context)
    source_refs = build_source_refs(package, refs, feature, context)
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
    defects = build_defects(context["focus"], context["consistency"], semantic_drift_check, assessment)
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
        context["state_machine"],
        context["modules"],
        context["strategy"],
        context["unit_mapping"],
        context["contracts"],
        context["sequence_steps"],
        context["main_flow_diagram"],
        context["exception_rules"],
        context["integrations"],
        context["algorithm_constraints"],
        context["io_matrix"],
        context["glossary_and_ownership"],
        context["migration_constraints"],
        context["skeleton"],
        context["api_specs"],
        context["consistency"],
        context["traceability"],
    )
    tech_frontmatter, tech_body = build_tech_docs(refs, source_refs, feature, context["focus"], context["rules"], context["nfrs"], context["implementation_arch"], context["runtime_view"], context["states"], context["state_machine"], context["modules"], context["strategy"], context["unit_mapping"], context["contracts"], context["sequence_steps"], context["main_flow_diagram"], context["exception_rules"], context["integrations"], context["algorithm_constraints"], context["io_matrix"], context["glossary_and_ownership"], context["migration_constraints"], context["skeleton"], context["traceability"], json_payload)
    arch_frontmatter, arch_body = build_arch_docs(feature, refs, source_refs, assessment, context["arch_diagram"], json_payload)
    api_frontmatter, api_body = build_api_docs(refs, source_refs, assessment, feature, context["api_specs"], json_payload)
    if revision_context:
        for block in [frontmatter, tech_frontmatter, arch_frontmatter, api_frontmatter]:
            if block is None:
                continue
            block["revision_request_ref"] = revision_context["revision_request_ref"]
            block["revision_summary"] = revision_context["summary"]
    review_report = build_review_report(run_id, refs, defects, context["consistency"], semantic_drift_check, assessment, utc_now_fn)
    acceptance_report = build_acceptance_report(defects, context["consistency"], semantic_drift_check, assessment, utc_now_fn)
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
