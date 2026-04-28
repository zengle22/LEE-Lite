#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tech_to_impl_contract_projection import build_contract_projection, resolve_selected_upstream_refs
from tech_to_impl_common import ensure_list, guess_repo_root_from_input, normalize_semantic_lock, unique_strings
from tech_to_impl_derivation import (
    acceptance_checkpoints,
    assess_workstreams,
    backend_workstream_items,
    build_refs,
    consistency_check,
    deliverable_files,
    evidence_rows,
    execution_contract_snapshot,
    filtered_implementation_rules,
    frontend_workstream_items,
    implementation_units,
    implementation_scope,
    implementation_steps,
    integration_plan_items,
    migration_plan_items,
    risk_items,
    tech_list,
    workstream_required_inputs,
)
from tech_to_impl_package_documents import _build_text_sections

DOWNSTREAM_TEMPLATE_ID = "template.dev.feature_delivery_l2"
DOWNSTREAM_TEMPLATE_PATH = "E:\\ai\\LEE-Lite-skill-first\\skills\\ll-dev-tech-to-impl\\output\\template.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _md_frontmatter(artifact_type: str, refs: dict[str, str | None], source_refs: list[str]) -> dict[str, Any]:
    payload = {
        "artifact_type": artifact_type,
        "status": "draft",
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "source_refs": source_refs,
    }
    if refs.get("arch_ref"):
        payload["arch_ref"] = refs["arch_ref"]
    if refs.get("api_ref"):
        payload["api_ref"] = refs["api_ref"]
    return payload


def _non_empty_phase_input_names(handoff: dict[str, Any]) -> list[str]:
    phase_inputs = handoff.get("phase_inputs") or {}
    if not isinstance(phase_inputs, dict):
        return []
    return [name for name, items in phase_inputs.items() if ensure_list(items)]


def build_semantic_drift_check(feature: dict[str, Any], bundle_json: dict[str, Any], upstream_design_refs: dict[str, Any]) -> dict[str, Any]:
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

    generated_text = " ".join(
        [
            str(bundle_json.get("title") or ""),
            str(feature.get("title") or ""),
            str(feature.get("goal") or ""),
            " ".join(ensure_list((bundle_json.get("selected_scope") or {}).get("scope"))),
            " ".join(ensure_list((upstream_design_refs.get("frozen_decisions") or {}).get("implementation_rules"))),
            " ".join(ensure_list((upstream_design_refs.get("frozen_decisions") or {}).get("state_model"))),
            " ".join(ensure_list((upstream_design_refs.get("frozen_decisions") or {}).get("main_sequence"))),
            " ".join(ensure_list((upstream_design_refs.get("frozen_decisions") or {}).get("implementation_unit_mapping"))),
            " ".join(ensure_list((upstream_design_refs.get("frozen_decisions") or {}).get("interface_contracts"))),
            " ".join(ensure_list((upstream_design_refs.get("frozen_decisions") or {}).get("integration_points"))),
        ]
    ).lower()
    forbidden_hits = [item for item in lock.get("forbidden_capabilities", []) if str(item).strip().lower() in generated_text]
    anchor_matches: list[str] = []
    token_groups = {
        "domain_type": [str(lock.get("domain_type") or "").replace("_", " ").lower()],
        "primary_object": [token for token in str(lock.get("primary_object") or "").replace("_", " ").lower().split() if token],
        "lifecycle_stage": [token for token in str(lock.get("lifecycle_stage") or "").replace("_", " ").lower().split() if token],
    }
    for label, tokens in token_groups.items():
        if tokens and all(token in generated_text for token in tokens):
            anchor_matches.append(label)
    allowed_capability_tokens = [
        [token for token in str(item).replace("_", " ").lower().split() if token]
        for item in ensure_list(lock.get("allowed_capabilities"))
    ]
    if any(tokens and all(token in generated_text for token in tokens) for tokens in allowed_capability_tokens):
        anchor_matches.append("allowed_capability_signature")
    implementation_readiness_signature = False
    if str(lock.get("domain_type") or "").strip().lower() == "review_projection_rule":
        review_projection_tokens = ["projection", "ssot"]
        if all(token in generated_text for token in review_projection_tokens):
            anchor_matches.append("review_projection_signature")
    if str(lock.get("domain_type") or "").strip().lower() == "implementation_readiness_rule":
        selected_scope = bundle_json.get("selected_scope") or {}
        implementation_steps = bundle_json.get("implementation_steps") or []
        artifact_refs = bundle_json.get("artifact_refs") or {}
        downstream_handoff = bundle_json.get("downstream_handoff") or {}
        implementation_readiness_signature = bool(selected_scope) and bool(implementation_steps) and bool(artifact_refs) and bool(downstream_handoff)
        if implementation_readiness_signature:
            anchor_matches.append("implementation_readiness_signature")
    preserved = not forbidden_hits and (len(anchor_matches) >= 1 or implementation_readiness_signature)
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


def _build_upstream_design_refs(package: Any, feature: dict[str, Any], refs: dict[str, str | None], source_refs: list[str], run_id: str, selected_upstream_refs: dict[str, Any]) -> dict[str, Any]:
    implementation_units_payload = implementation_units(package)
    return {
        "artifact_type": "UPSTREAM_DESIGN_REFS",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "surface_map_ref": refs.get("surface_map_ref"),
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "upstream_workflow_key": str(package.tech_json.get("workflow_key") or ""),
        "upstream_run_id": package.run_id,
        "primary_artifacts": {
            "tech_design_bundle": "tech-design-bundle.json",
            "tech_spec": "tech-spec.md",
            "surface_map_package": "surface-map-bundle.json" if refs.get("surface_map_ref") else None,
            "arch_design": "arch-design.md" if refs["arch_ref"] else None,
            "api_contract": "api-contract.md" if refs["api_ref"] else None,
        },
        "selected_upstream_refs": selected_upstream_refs,
        "frozen_source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
        "frozen_decisions": {
            "design_focus": ensure_list((package.tech_json.get("tech_design") or {}).get("design_focus")),
            "implementation_rules": filtered_implementation_rules(package),
            "state_model": tech_list(package, "state_model"),
            "main_sequence": tech_list(package, "main_sequence"),
            "integration_points": tech_list(package, "integration_points"),
            "implementation_unit_mapping": [f"{unit['path']} ({unit['mode']}): {unit['detail']}" for unit in implementation_units_payload],
            "interface_contracts": tech_list(package, "interface_contracts"),
            "consistency_passed": bool((package.tech_json.get("design_consistency_check") or {}).get("passed")),
        },
    }


def _build_handoff(
    run_id: str,
    refs: dict[str, str | None],
    assessment: dict[str, Any],
    deliverables: list[str],
    acceptance_refs: list[str],
) -> dict[str, Any]:
    return {
        "handoff_id": f"handoff-{run_id}-to-feature-delivery",
        "from_skill": "ll-dev-tech-to-impl",
        "source_run_id": run_id,
        "target_template_id": DOWNSTREAM_TEMPLATE_ID,
        "target_template_path": DOWNSTREAM_TEMPLATE_PATH,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "surface_map_ref": refs.get("surface_map_ref"),
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "primary_artifact_ref": "impl-bundle.json",
        "phase_inputs": {
            "implementation_task": ["impl-task.md"],
            "frontend": ["frontend-workstream.md"] if assessment["frontend_required"] else [],
            "backend": ["backend-workstream.md"] if assessment["backend_required"] else [],
            "migration": ["migration-cutover-plan.md"] if assessment["migration_required"] else [],
            "integration": ["integration-plan.md"],
            "evidence": ["dev-evidence-plan.json", "smoke-gate-subject.json"],
            "upstream_design": ["upstream-design-refs.json"],
        },
        "deliverables": deliverables,
        "acceptance_refs": acceptance_refs,
        "supporting_artifact_refs": deliverables,
        "created_at": utc_now(),
    }


def _normalized_source_refs(
    refs: dict[str, str | None],
    selected_upstream_refs: dict[str, Any],
    upstream_source_refs: list[str],
    *,
    upstream_run_id: str,
) -> list[str]:
    selected_optional_refs = {
        "ARCH-": str(refs.get("arch_ref") or "").strip() or None,
        "API-": str(refs.get("api_ref") or "").strip() or None,
        "UI-": str(selected_upstream_refs.get("ui_ref") or "").strip() or None,
        "SURFACE-": str(selected_upstream_refs.get("surface_map_ref") or "").strip() or None,
        "TESTSET-": str(selected_upstream_refs.get("testset_ref") or "").strip() or None,
    }
    normalized: list[str] = []

    # Core upstream traceability chain (per D-16)
    core_refs = [
        f"dev.feat-to-tech::{upstream_run_id}",
        refs["feat_ref"],
        refs["tech_ref"],
    ]

    # Add optional SSOT refs with type tagging (per D-17)
    if refs.get("arch_ref"):
        core_refs.append(f"ARCH:{refs['arch_ref']}")
    if refs.get("api_ref"):
        core_refs.append(f"API:{refs['api_ref']}")
    if refs.get("epic_ref"):
        core_refs.append(f"EPIC:{refs['epic_ref']}")
    if refs.get("src_ref"):
        core_refs.append(f"SRC:{refs['src_ref']}")
    if refs.get("surface_map_ref"):
        core_refs.append(f"SURFACE:{refs['surface_map_ref']}")

    seed_refs = unique_strings(
        core_refs
        + upstream_source_refs
        + ensure_list(selected_upstream_refs.get("adr_refs"))
        + [value for value in selected_optional_refs.values() if value]
    )

    for ref in seed_refs:
        optional_prefix = next((prefix for prefix in selected_optional_refs if ref.startswith(prefix)), None)
        if optional_prefix:
            selected_value = selected_optional_refs[optional_prefix]
            if selected_value and ref == selected_value:
                normalized.append(ref)
            continue
        normalized.append(ref)
    return unique_strings(normalized)


def _build_bundle_json(
    run_id: str,
    refs: dict[str, str | None],
    feature: dict[str, Any],
    assessment: dict[str, Any],
    consistency: dict[str, Any],
    upstream_design_refs: dict[str, Any],
    handoff: dict[str, Any],
    source_refs: list[str],
    steps: list[dict[str, str]],
    scope: list[str],
) -> dict[str, Any]:
    return {
        "artifact_type": "feature_impl_candidate_package",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "title": f"{feature.get('title') or refs['feat_ref']} Implementation Task Package",
        "status": "in_progress",
        "package_role": "candidate",
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
        "selected_scope": {
            "title": feature.get("title"),
            "goal": feature.get("goal"),
            "scope": ensure_list(feature.get("scope")),
            "constraints": ensure_list(feature.get("constraints")),
            "dependencies": ensure_list(feature.get("dependencies")),
        },
        "workstream_assessment": assessment,
        "status_model": {
            "package": "in_progress",
            "smoke_gate": "pending_review",
        },
        "artifact_refs": {
            "bundle_markdown": "impl-bundle.md",
            "bundle_json": "impl-bundle.json",
            "impl_task": "impl-task.md",
            "upstream_design_refs": "upstream-design-refs.json",
            "frontend_workstream": "frontend-workstream.md" if assessment["frontend_required"] else None,
            "backend_workstream": "backend-workstream.md" if assessment["backend_required"] else None,
            "migration_cutover_plan": "migration-cutover-plan.md" if assessment["migration_required"] else None,
            "integration_plan": "integration-plan.md",
            "dev_evidence_plan": "dev-evidence-plan.json",
            "smoke_gate_subject": "smoke-gate-subject.json",
            "review_report": "impl-review-report.json",
            "acceptance_report": "impl-acceptance-report.json",
            "defect_list": "impl-defect-list.json",
            "handoff": "handoff-to-feature-delivery.json",
        },
        "upstream_design_refs": upstream_design_refs,
        "consistency_check": consistency,
        "downstream_handoff": handoff,
        "implementation_steps": steps,
    }


def _build_document_payloads(
    feature: dict[str, Any],
    refs: dict[str, str | None],
    assessment: dict[str, Any],
    steps: list[dict[str, str]],
    risks: list[str],
    deliverables: list[str],
    checkpoints: list[dict[str, str]],
    integration_items: list[str],
    evidence_plan_rows: list[dict[str, Any]],
    handoff: dict[str, Any],
    source_refs: list[str],
    bundle_json: dict[str, Any],
    scope: list[str],
    contract_projection: dict[str, Any],
    frontend_items: list[str],
    backend_items: list[str],
    migration_items: list[str],
) -> dict[str, Any]:
    texts = _build_text_sections(feature, refs, assessment, steps, risks, deliverables, checkpoints, integration_items, evidence_plan_rows, handoff, source_refs, bundle_json, scope, contract_projection)
    payload: dict[str, Any] = {
        "bundle_frontmatter": {
            "artifact_type": bundle_json["artifact_type"],
            "workflow_key": bundle_json["workflow_key"],
            "workflow_run_id": bundle_json["workflow_run_id"],
            "status": bundle_json["status"],
            "package_role": bundle_json["package_role"],
            "schema_version": bundle_json["schema_version"],
            "feat_ref": bundle_json["feat_ref"],
            "impl_ref": bundle_json["impl_ref"],
            "tech_ref": bundle_json["tech_ref"],
            "source_refs": bundle_json["source_refs"],
            "semantic_lock": bundle_json["semantic_lock"],
        },
        "bundle_body": texts["bundle_body"],
        "impl_task_frontmatter": _md_frontmatter("IMPL_TASK", refs, source_refs),
        "impl_task_body": texts["impl_task_body"],
        "integration_frontmatter": _md_frontmatter("INTEGRATION_PLAN", refs, source_refs),
        "integration_body": "\n\n".join(
            [
                f"# INTEGRATION-{refs['impl_ref']}",
                "## Integration Sequence\n\n" + "\n".join(f"- {item}" for item in integration_items),
                "## Blocking Conditions\n\n"
                + "\n".join(
                    [
                        "- Upstream refs must remain resolvable.",
                        "- Optional workstreams can only enter execution if their applicability assessment is true.",
                        "- Smoke review is blocked until evidence plan artifacts are available.",
                    ]
                ),
            ]
        ),
    }
    if assessment["frontend_required"]:
        payload.update(
            {
                "frontend_frontmatter": _md_frontmatter("FRONTEND_WORKSTREAM", refs, source_refs),
                "frontend_body": "\n\n".join(
                    [
                        f"# FRONTEND-{refs['impl_ref']}",
                        "## Frontend Surface\n\n" + "\n".join(f"- {item}" for item in frontend_items),
                        "## Done Criteria\n\n- Frontend implementation stays inside the selected IMPL boundary and traceability chain.",
                    ]
                ),
            }
        )
    else:
        payload.update({"frontend_frontmatter": None, "frontend_body": None})
    if assessment["backend_required"]:
        payload.update(
            {
                "backend_frontmatter": _md_frontmatter("BACKEND_WORKSTREAM", refs, source_refs),
                "backend_body": "\n\n".join(
                    [
                        f"# BACKEND-{refs['impl_ref']}",
                        "## Backend Surface\n\n" + "\n".join(f"- {item}" for item in backend_items),
                        "## Done Criteria\n\n- Backend changes satisfy frozen TECH/ARCH/API decisions without introducing new design truth.",
                    ]
                ),
            }
        )
    else:
        payload.update({"backend_frontmatter": None, "backend_body": None})
    if assessment["migration_required"]:
        payload.update(
            {
                "migration_frontmatter": _md_frontmatter("MIGRATION_CUTOVER_PLAN", refs, source_refs),
                "migration_body": "\n\n".join(
                    [
                        f"# MIGRATION-{refs['impl_ref']}",
                        "## Migration and Cutover\n\n" + "\n".join(f"- {item}" for item in migration_items),
                        "## Done Criteria\n\n- Rollout and rollback expectations are explicit enough for downstream execution.",
                    ]
                ),
            }
        )
    else:
        payload.update({"migration_frontmatter": None, "migration_body": None})
    return payload


def _build_review_payloads(
    run_id: str,
    refs: dict[str, str | None],
    feature: dict[str, Any],
    assessment: dict[str, Any],
    consistency: dict[str, Any],
    bundle_json: dict[str, Any],
    upstream_design_refs: dict[str, Any],
    smoke_required_inputs: list[str],
    checkpoints: list[dict[str, str]],
    evidence_plan_rows: list[dict[str, Any]],
    semantic_drift_check: dict[str, Any],
) -> dict[str, Any]:
    defects: list[dict[str, Any]] = []
    if not consistency["passed"]:
        defects.append({"severity": "P1", "title": "No implementation surface selected", "detail": "; ".join(consistency["issues"])})
    if semantic_drift_check["verdict"] == "reject":
        defects.append({"severity": "P1", "title": "semantic_lock drift detected", "detail": semantic_drift_check["summary"]})
    return {
        "evidence_plan": {
            "artifact_type": "DEV_EVIDENCE_PLAN",
            "workflow_key": "dev.tech-to-impl",
            "workflow_run_id": run_id,
            "feat_ref": refs["feat_ref"],
            "impl_ref": refs["impl_ref"],
            "rows": evidence_plan_rows,
            "status": "draft",
        },
        "smoke_gate_subject": {
            "artifact_type": "SMOKE_GATE_SUBJECT",
            "workflow_key": "dev.tech-to-impl",
            "workflow_run_id": run_id,
            "gate_ref": f"SMOKE-GATE-{refs['impl_ref']}",
            "feat_ref": refs["feat_ref"],
            "impl_ref": refs["impl_ref"],
            "tech_ref": refs["tech_ref"],
            "status": "pending_review",
            "decision": "pending",
            "ready_for_execution": False,
            "required_inputs": smoke_required_inputs,
            "required_workstreams": smoke_required_inputs,
            "acceptance_refs": [item["ref"] for item in checkpoints],
            "created_at": utc_now(),
        },
        "review_report": {
            "report_id": f"impl-review-{run_id}",
            "report_type": "feature_impl_review",
            "workflow_key": "dev.tech-to-impl",
            "workflow_run_id": run_id,
            "feat_ref": refs["feat_ref"],
            "impl_ref": refs["impl_ref"],
            "status": "pending",
            "decision": "pending",
            "summary": "Pending supervisor review.",
            "findings": [],
            "created_at": utc_now(),
        },
        "acceptance_report": {
            "report_id": f"impl-acceptance-{run_id}",
            "report_type": "feature_impl_acceptance",
            "workflow_key": "dev.tech-to-impl",
            "workflow_run_id": run_id,
            "feat_ref": refs["feat_ref"],
            "impl_ref": refs["impl_ref"],
            "status": "pending",
            "decision": "pending",
            "summary": "Pending supervisor review.",
            "acceptance_findings": [],
            "created_at": utc_now(),
        },
        "defect_list": defects,
        "semantic_drift_check": semantic_drift_check,
        "execution_decisions": [
            f"Selected TECH package {refs['tech_ref']} from upstream run {bundle_json['workflow_run_id']}.",
            f"frontend_required={assessment['frontend_required']}, backend_required={assessment['backend_required']}, migration_required={assessment['migration_required']}.",
            f"Prepared downstream handoff to {DOWNSTREAM_TEMPLATE_ID}.",
        ],
        "execution_uncertainties": consistency["issues"][:],
    }


def build_candidate_package(package: Any, run_id: str) -> dict[str, Any]:
    feature = dict(package.selected_feat)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)
    refs = build_refs(package)
    if package.surface_map_ref and not refs.get("surface_map_ref"):
        refs["surface_map_ref"] = package.surface_map_ref
    assessment = assess_workstreams(feature, package)
    consistency = consistency_check(assessment)
    checkpoints = acceptance_checkpoints(feature, package, assessment)
    scope = implementation_scope(feature, package)
    steps = implementation_steps(feature, assessment, package, checkpoints)
    risks = risk_items(feature, assessment, package)
    deliverables = deliverable_files(assessment)
    smoke_required_inputs = workstream_required_inputs(assessment)
    integration_items = integration_plan_items(feature, assessment, package)
    evidence_plan_rows = evidence_rows(feature, assessment, checkpoints)
    frontend_items = frontend_workstream_items(feature)
    backend_items = backend_workstream_items(feature, package)
    migration_items = migration_plan_items(feature, package)
    repo_root = guess_repo_root_from_input(package.artifacts_dir.resolve())
    selected_upstream_refs = resolve_selected_upstream_refs(feature, refs, ensure_list(package.tech_json.get("source_refs")), repo_root)

    source_refs = _normalized_source_refs(
        refs,
        selected_upstream_refs,
        ensure_list(package.tech_json.get("source_refs")),
        upstream_run_id=package.run_id,
    )
    contract_projection = build_contract_projection(
        package,
        feature,
        refs,
        source_refs,
        assessment,
        steps,
        checkpoints,
        evidence_plan_rows,
        deliverables,
        execution_contract_snapshot(feature, assessment, package),
    )
    upstream_design_refs = _build_upstream_design_refs(package, feature, refs, source_refs, run_id, contract_projection["selected_upstream_refs"])
    handoff = _build_handoff(run_id, refs, assessment, deliverables, [item["ref"] for item in checkpoints])
    bundle_json = _build_bundle_json(run_id, refs, feature, assessment, consistency, upstream_design_refs, handoff, source_refs, steps, scope)
    bundle_json.update(contract_projection)
    semantic_drift_check = build_semantic_drift_check(feature, bundle_json, upstream_design_refs)
    doc_payloads = _build_document_payloads(
        feature,
        refs,
        assessment,
        steps,
        risks,
        deliverables,
        checkpoints,
        integration_items,
        evidence_plan_rows,
        handoff,
        source_refs,
        bundle_json,
        scope,
        contract_projection,
        frontend_items,
        backend_items,
        migration_items,
    )
    review_payloads = _build_review_payloads(run_id, refs, feature, assessment, consistency, bundle_json, upstream_design_refs, smoke_required_inputs, checkpoints, evidence_plan_rows, semantic_drift_check)
    return {
        "refs": refs,
        "assessment": assessment,
        "consistency": consistency,
        **doc_payloads,
        "bundle_json": bundle_json,
        "impl_task_frontmatter": _md_frontmatter("IMPL_TASK", refs, source_refs),
        "upstream_design_refs": upstream_design_refs,
        **review_payloads,
        "handoff": handoff,
    }
