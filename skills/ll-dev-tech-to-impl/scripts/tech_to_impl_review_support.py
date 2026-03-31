#!/usr/bin/env python3
"""
Validation helpers for tech-to-impl review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.workflow_revision import build_revision_summary, normalize_revision_context
from cli.lib.workflow_document_test import validate_document_test_report
from tech_to_impl_common import ensure_list, load_json, load_tech_package, parse_markdown_frontmatter, render_markdown, unique_strings
from tech_to_impl_builder import DOWNSTREAM_TEMPLATE_ID, DOWNSTREAM_TEMPLATE_PATH, build_candidate_package
from tech_to_impl_derivation import workstream_required_inputs

REQUIRED_OUTPUT_FILES = [
    "package-manifest.json",
    "impl-bundle.md",
    "impl-bundle.json",
    "impl-task.md",
    "upstream-design-refs.json",
    "integration-plan.md",
    "dev-evidence-plan.json",
    "smoke-gate-subject.json",
    "impl-review-report.json",
    "document-test-report.json",
    "impl-acceptance-report.json",
    "impl-defect-list.json",
    "handoff-to-feature-delivery.json",
    "semantic-drift-check.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
REQUIRED_BUNDLE_HEADINGS = [
    "Selected Upstream",
    "Package Semantics",
    "Applicability Assessment",
    "Implementation Task",
    "Integration Plan",
    "Evidence Plan",
    "Smoke Gate Subject",
    "Delivery Handoff",
    "Traceability",
]
REQUIRED_IMPL_TASK_HEADINGS = [
    "## 1. 任务标识",
    "## 2. 本次目标",
    "## 3. 范围与非目标",
    "## 4. 上游收敛结果",
    "## 5. 规范性约束",
    "## 6. 实施要求",
    "## 7. 交付物要求",
    "## 8. 验收标准与 TESTSET 映射",
    "## 9. 执行顺序建议",
    "## 10. 风险与注意事项",
]


def _revision_summary(revision_request: dict[str, Any]) -> str:
    return build_revision_summary(revision_request, reason_limit=180, output_limit=220, prefix="Gate revise")


def _apply_revision_request(generated: dict[str, Any], revision_request_ref: str, revision_request: dict[str, Any]) -> None:
    if not revision_request:
        return
    revision_context = normalize_revision_context(
        revision_request,
        revision_request_ref=revision_request_ref,
        ensure_list=lambda values: unique_strings([str(item).strip() for item in (values or []) if str(item).strip()]),
        reason_limit=180,
        output_limit=220,
    )
    revision_summary = str(revision_context["summary"]).strip()
    generated["revision_request_ref"] = revision_request_ref
    generated["revision_request"] = revision_request
    generated["revision_summary"] = revision_summary
    bundle_json = generated.get("bundle_json")
    if isinstance(bundle_json, dict):
        bundle_json["revision_context"] = revision_context
        selected_scope = bundle_json.get("selected_scope")
        if isinstance(selected_scope, dict):
            selected_scope["constraints"] = unique_strings(
                [str(item).strip() for item in selected_scope.get("constraints") or [] if str(item).strip()] + [revision_summary]
            )
    upstream_design_refs = generated.get("upstream_design_refs")
    if isinstance(upstream_design_refs, dict):
        upstream_design_refs["revision_context"] = revision_context
        frozen_decisions = upstream_design_refs.get("frozen_decisions")
        if isinstance(frozen_decisions, dict):
            frozen_decisions["implementation_rules"] = unique_strings(
                [str(item).strip() for item in frozen_decisions.get("implementation_rules") or [] if str(item).strip()] + [revision_summary]
            )
    for key in [
        "bundle_frontmatter",
        "impl_task_frontmatter",
        "integration_frontmatter",
        "frontend_frontmatter",
        "backend_frontmatter",
        "migration_frontmatter",
    ]:
        frontmatter = generated.get(key)
        if isinstance(frontmatter, dict):
            frontmatter["revision_request_ref"] = revision_request_ref
            frontmatter["revision_round"] = revision_context["revision_round"]
    for key in ["review_report", "acceptance_report", "smoke_gate_subject", "handoff"]:
        payload = generated.get(key)
        if isinstance(payload, dict):
            payload["revision_request_ref"] = revision_request_ref
            payload["revision_summary"] = revision_summary
    evidence_plan = generated.get("evidence_plan")
    if isinstance(evidence_plan, dict):
        evidence_plan["revision_request_ref"] = revision_request_ref
        evidence_plan["revision_summary"] = revision_summary
    semantic_drift_check = generated.get("semantic_drift_check")
    if isinstance(semantic_drift_check, dict):
        semantic_drift_check["revision_request_ref"] = revision_request_ref
        semantic_drift_check["revision_summary"] = revision_summary


def _status_normalized_markdown(markdown_text: str) -> str:
    normalized = markdown_text.replace("status: execution_ready", "status: <status>")
    normalized = normalized.replace("status: blocked", "status: <status>")
    normalized = normalized.replace("status: in_progress", "status: <status>")
    normalized = normalized.replace("status: draft", "status: <status>")
    normalized = normalized.replace("- status: `execution_ready`", "- status: `<status>`")
    normalized = normalized.replace("- status: `blocked`", "- status: `<status>`")
    normalized = normalized.replace("- status: `in_progress`", "- status: `<status>`")
    normalized = normalized.replace("- status: `draft`", "- status: `<status>`")
    return normalized


def _frontmatter_without_dynamic_keys(frontmatter: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in frontmatter.items()
        if key not in {"status", "revision_request_ref", "revision_round", "revision_summary"}
    }


def _recompute_current_artifact_gate(artifacts_dir: Path) -> tuple[dict[str, Any], list[str]]:
    manifest = load_json(artifacts_dir / "package-manifest.json")
    input_artifacts_dir = Path(str(manifest.get("input_artifacts_dir") or "")).resolve()
    if not input_artifacts_dir.exists():
        return {
            "review_gate_ok": False,
            "stale_documents": [],
            "semantic_gate_matches": False,
            "summary": "Current implementation artifacts cannot be recomputed because the upstream TECH package is missing.",
        }, [f"input_artifacts_dir does not exist: {input_artifacts_dir}"]
    package = load_tech_package(input_artifacts_dir)
    run_id = str(manifest.get("run_id") or artifacts_dir.name)
    generated = build_candidate_package(package, run_id)
    revision_request_path = artifacts_dir / "revision-request.json"
    if revision_request_path.exists():
        _apply_revision_request(generated, "revision-request.json", load_json(revision_request_path))
    stale_documents: list[str] = []
    expected_markdowns = {
        "impl-bundle.md": render_markdown(generated["bundle_frontmatter"], generated["bundle_body"]),
        "impl-task.md": render_markdown(generated["impl_task_frontmatter"], generated["impl_task_body"]),
        "integration-plan.md": render_markdown(generated["integration_frontmatter"], generated["integration_body"]),
    }
    optional_docs = [
        ("frontend-workstream.md", generated.get("frontend_frontmatter"), generated.get("frontend_body")),
        ("backend-workstream.md", generated.get("backend_frontmatter"), generated.get("backend_body")),
        ("migration-cutover-plan.md", generated.get("migration_frontmatter"), generated.get("migration_body")),
    ]
    for name, frontmatter, body in optional_docs:
        path = artifacts_dir / name
        if frontmatter and body:
            expected_markdowns[name] = render_markdown(frontmatter, body)
        elif path.exists():
            stale_documents.append(name)
    for name, expected_markdown in expected_markdowns.items():
        path = artifacts_dir / name
        if not path.exists():
            stale_documents.append(name)
            continue
        current_frontmatter, current_body = parse_markdown_frontmatter(path.read_text(encoding="utf-8"))
        expected_frontmatter, expected_body = parse_markdown_frontmatter(expected_markdown)
        if _frontmatter_without_dynamic_keys(current_frontmatter) != _frontmatter_without_dynamic_keys(expected_frontmatter):
            stale_documents.append(name)
            continue
        if _status_normalized_markdown(current_body) != _status_normalized_markdown(expected_body):
            stale_documents.append(name)
    stored_semantic = load_json(artifacts_dir / "semantic-drift-check.json")
    expected_semantic = generated["semantic_drift_check"]
    semantic_gate_matches = all(
        stored_semantic.get(key) == expected_semantic.get(key)
        for key in ["verdict", "semantic_lock_present", "semantic_lock_preserved", "forbidden_axis_detected", "anchor_matches"]
    )
    review_gate_ok = not stale_documents and semantic_gate_matches
    return {
        "review_gate_ok": review_gate_ok,
        "stale_documents": stale_documents,
        "semantic_gate_matches": semantic_gate_matches,
        "summary": "Current implementation artifacts match the canonical upstream projection." if review_gate_ok else "Current implementation artifacts drift from the canonical upstream projection.",
        "expected_supervision_decision": "pass" if review_gate_ok else "revise",
    }, []


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_OUTPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required output artifact: {required_file}")
    if errors:
        return errors, {"valid": False}

    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    handoff = load_json(artifacts_dir / "handoff-to-feature-delivery.json")
    upstream_refs = load_json(artifacts_dir / "upstream-design-refs.json")
    evidence_plan = load_json(artifacts_dir / "dev-evidence-plan.json")
    document_test = load_json(artifacts_dir / "document-test-report.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    review_report = load_json(artifacts_dir / "impl-review-report.json")
    acceptance_report = load_json(artifacts_dir / "impl-acceptance-report.json")
    review_gate, recompute_errors = _recompute_current_artifact_gate(artifacts_dir)

    errors.extend(validate_document_test_report(document_test))
    errors.extend(check_bundle_identity(bundle_json))
    errors.extend(check_source_refs(bundle_json))
    errors.extend(check_markdown_sections(artifacts_dir))
    errors.extend(check_workstream_presence(artifacts_dir, bundle_json))
    errors.extend(check_contract_projection(bundle_json, handoff, evidence_plan, document_test))
    errors.extend(check_handoff_and_evidence(handoff, upstream_refs, bundle_json, evidence_plan, smoke_gate))
    errors.extend(check_status_model(manifest, bundle_json, smoke_gate))
    errors.extend(recompute_errors)
    if not review_gate.get("review_gate_ok", False):
        errors.append("Current implementation artifacts must match the canonical upstream projection.")
    if review_report.get("decision") != review_gate.get("expected_supervision_decision"):
        errors.append("impl-review-report.json decision must match the recomputed current-artifact review gate.")
    expected_acceptance_decision = "approve" if review_gate.get("expected_supervision_decision") == "pass" else "revise"
    if acceptance_report.get("decision") != expected_acceptance_decision:
        errors.append("impl-acceptance-report.json decision must match the recomputed current-artifact review gate.")
    if bool(smoke_gate.get("ready_for_execution")) != bool(review_gate.get("review_gate_ok")):
        errors.append("smoke-gate-subject.json ready_for_execution must match the recomputed current-artifact review gate.")
    expected_document_test_outcome = "no_blocking_defect_found" if review_gate.get("review_gate_ok") else "blocking_defect_found"
    if document_test.get("test_outcome") != expected_document_test_outcome:
        errors.append("document-test-report.json test_outcome must match the recomputed current-artifact review gate.")

    return errors, {
        "valid": not errors,
        "feat_ref": bundle_json.get("feat_ref"),
        "tech_ref": bundle_json.get("tech_ref"),
        "impl_ref": bundle_json.get("impl_ref"),
        "manifest_status": str(manifest.get("status") or ""),
        "smoke_gate_status": str(smoke_gate.get("status") or ""),
        "semantic_lock_preserved": semantic_drift_check.get("semantic_lock_preserved", True),
        "review_gate": review_gate,
    }


def check_bundle_identity(bundle_json: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if bundle_json.get("artifact_type") != "feature_impl_candidate_package":
        errors.append("impl-bundle.json artifact_type must be feature_impl_candidate_package.")
    if bundle_json.get("workflow_key") != "dev.tech-to-impl":
        errors.append("impl-bundle.json workflow_key must be dev.tech-to-impl.")
    if bundle_json.get("package_role") != "candidate":
        errors.append("impl-bundle.json package_role must be candidate.")
    return errors


def check_source_refs(bundle_json: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_refs = ensure_list(bundle_json.get("source_refs"))
    for prefix in ["dev.feat-to-tech::", "FEAT-", "TECH-", "EPIC-", "SRC-"]:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"impl-bundle.json source_refs must include {prefix}.")
    return errors


def check_markdown_sections(artifacts_dir: Path) -> list[str]:
    errors: list[str] = []
    _, bundle_body = parse_markdown_frontmatter((artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_BUNDLE_HEADINGS:
        if f"## {heading}" not in bundle_body:
            errors.append(f"impl-bundle.md is missing section: {heading}")
    if "execution input of SSOT" in bundle_body or "execution-entry truth" in bundle_body:
        errors.append("impl-bundle.md must use canonical execution package wording instead of truth/SSOT wording.")
    _, impl_task_body = parse_markdown_frontmatter((artifacts_dir / "impl-task.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_IMPL_TASK_HEADINGS:
        if heading not in impl_task_body:
            errors.append(f"impl-task.md is missing section: {heading}")
    for marker in [
        "### In Scope",
        "### Out of Scope",
        "### Normative / MUST",
        "### Informative / Context Only",
        "### Touch Set / Module Plan",
        "### Allowed",
        "### Forbidden",
        "### Acceptance Trace",
        "### Required",
        "### Suggested",
    ]:
        if marker not in impl_task_body:
            errors.append(f"impl-task.md is missing marker: {marker}")
    return errors


def check_contract_projection(
    bundle_json: dict[str, Any],
    handoff: dict[str, Any],
    evidence_plan: dict[str, Any],
    document_test: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    required_fields = [
        "package_semantics",
        "authority_scope",
        "selected_upstream_refs",
        "provisional_refs",
        "scope_boundary",
        "upstream_impacts",
        "normative_items",
        "informative_items",
        "change_controls",
        "required_steps",
        "suggested_steps",
        "acceptance_trace",
        "testset_mapping",
        "handoff_artifacts",
        "conflict_policy",
        "freshness_status",
        "rederive_triggers",
        "self_contained_policy",
        "repo_discrepancy_status",
    ]
    for field in required_fields:
        if field not in bundle_json:
            errors.append(f"impl-bundle.json must include {field}.")
    semantics = bundle_json.get("package_semantics") or {}
    if semantics.get("canonical_package") is not True or semantics.get("execution_time_single_entrypoint") is not True:
        errors.append("impl-bundle.json package_semantics must mark the package as canonical execution package.")
    if semantics.get("domain_truth_source") is not False or semantics.get("design_truth_source") is not False or semantics.get("test_truth_source") is not False:
        errors.append("impl-bundle.json package_semantics must keep domain/design/test truth source flags false.")
    selected_refs = bundle_json.get("selected_upstream_refs") or {}
    if str(selected_refs.get("feat_ref") or "") != str(bundle_json.get("feat_ref") or ""):
        errors.append("selected_upstream_refs.feat_ref must match impl-bundle.json feat_ref.")
    if str(selected_refs.get("tech_ref") or "") != str(bundle_json.get("tech_ref") or ""):
        errors.append("selected_upstream_refs.tech_ref must match impl-bundle.json tech_ref.")
    if not ensure_list(bundle_json.get("normative_items")):
        errors.append("impl-bundle.json normative_items must be non-empty.")
    if not isinstance(bundle_json.get("informative_items"), list):
        errors.append("impl-bundle.json informative_items must be present as a list.")
    scope_boundary = bundle_json.get("scope_boundary") or {}
    if not ensure_list(scope_boundary.get("in_scope")):
        errors.append("impl-bundle.json scope_boundary.in_scope must be non-empty.")
    if not ensure_list(scope_boundary.get("out_of_scope")):
        errors.append("impl-bundle.json scope_boundary.out_of_scope must be non-empty.")
    upstream_impacts = bundle_json.get("upstream_impacts") or {}
    for key in ["adr", "src_epic_feat", "tech", "arch", "api", "ui", "testset"]:
        if key not in upstream_impacts:
            errors.append(f"impl-bundle.json upstream_impacts must include {key}.")
    if not ensure_list(bundle_json.get("required_steps")):
        errors.append("impl-bundle.json required_steps must be non-empty.")
    if not isinstance(bundle_json.get("suggested_steps"), list):
        errors.append("impl-bundle.json suggested_steps must be present as a list.")
    change_controls = bundle_json.get("change_controls") or {}
    if not ensure_list(change_controls.get("touch_set")):
        errors.append("impl-bundle.json change_controls.touch_set must be non-empty.")
    for key in ["allowed_changes", "forbidden_changes"]:
        if not ensure_list(change_controls.get(key)):
            errors.append(f"impl-bundle.json change_controls.{key} must be non-empty.")
    if not ensure_list(bundle_json.get("acceptance_trace")):
        errors.append("impl-bundle.json acceptance_trace must be non-empty.")
    testset_mapping = bundle_json.get("testset_mapping") or {}
    if not isinstance(testset_mapping.get("mappings"), list) or not testset_mapping.get("mappings"):
        errors.append("impl-bundle.json testset_mapping.mappings must be non-empty.")
    if str(testset_mapping.get("mapping_policy") or "") != "TESTSET_over_IMPL_when_present":
        errors.append("impl-bundle.json testset_mapping.mapping_policy must be TESTSET_over_IMPL_when_present.")
    if set(ensure_list(bundle_json.get("handoff_artifacts"))) != set(ensure_list(handoff.get("deliverables"))):
        errors.append("impl-bundle.json handoff_artifacts must match handoff deliverables.")
    if bundle_json.get("freshness_status") not in {"fresh_on_generation", "needs_review", "stale"}:
        errors.append("impl-bundle.json freshness_status is invalid.")
    if not ensure_list(bundle_json.get("rederive_triggers")):
        errors.append("impl-bundle.json rederive_triggers must be non-empty.")
    if str((bundle_json.get("conflict_policy") or {}).get("repo_discrepancy_policy") or "") != "explicit_discrepancy_handling_required":
        errors.append("impl-bundle.json conflict_policy must require explicit discrepancy handling.")
    provisional_refs = bundle_json.get("provisional_refs")
    if not isinstance(provisional_refs, list):
        errors.append("impl-bundle.json provisional_refs must be present as a list.")
    else:
        for item in provisional_refs:
            if not isinstance(item, dict) or not all(str(item.get(key) or "").strip() for key in ["ref", "status", "impact_scope", "follow_up_action"]):
                errors.append("Each provisional_refs item must include ref, status, impact_scope, and follow_up_action.")
                break
    if "rows" not in evidence_plan:
        errors.append("dev-evidence-plan.json must retain rows for acceptance mapping completeness.")
    for key in ["workflow_key", "run_id", "tested_at", "test_outcome", "defect_counts", "recommended_next_action", "recommended_actor", "sections"]:
        if key not in document_test:
            errors.append(f"document-test-report.json must include {key}.")
    sections = document_test.get("sections") or {}
    for key in ["structural", "logic_consistency", "downstream_readiness", "semantic_drift", "fixability", "canonical_package", "freshness", "discrepancy", "self_contained_boundary"]:
        if key not in sections:
            errors.append(f"document-test-report.json sections must include {key}.")
    return errors


def check_workstream_presence(artifacts_dir: Path, bundle_json: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    assessment = bundle_json.get("workstream_assessment") or {}
    frontend_required = bool(assessment.get("frontend_required"))
    backend_required = bool(assessment.get("backend_required"))
    migration_required = bool(assessment.get("migration_required"))
    if frontend_required and not (artifacts_dir / "frontend-workstream.md").exists():
        errors.append("frontend-workstream.md must exist when frontend_required is true.")
    if not frontend_required and (artifacts_dir / "frontend-workstream.md").exists():
        errors.append("frontend-workstream.md must not exist when frontend_required is false.")
    if backend_required and not (artifacts_dir / "backend-workstream.md").exists():
        errors.append("backend-workstream.md must exist when backend_required is true.")
    if not backend_required and (artifacts_dir / "backend-workstream.md").exists():
        errors.append("backend-workstream.md must not exist when backend_required is false.")
    if migration_required and not (artifacts_dir / "migration-cutover-plan.md").exists():
        errors.append("migration-cutover-plan.md must exist when migration_required is true.")
    if not migration_required and (artifacts_dir / "migration-cutover-plan.md").exists():
        errors.append("migration-cutover-plan.md must not exist when migration_required is false.")
    return errors


def check_handoff_and_evidence(
    handoff: dict[str, Any],
    upstream_refs: dict[str, Any],
    bundle_json: dict[str, Any],
    evidence_plan: dict[str, Any],
    smoke_gate: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if handoff.get("target_template_id") != DOWNSTREAM_TEMPLATE_ID:
        errors.append(f"handoff-to-feature-delivery.json must target {DOWNSTREAM_TEMPLATE_ID}.")
    if handoff.get("target_template_path") != DOWNSTREAM_TEMPLATE_PATH:
        errors.append("handoff-to-feature-delivery.json target_template_path is incorrect.")
    for field in ["feat_ref", "impl_ref", "tech_ref"]:
        if str(handoff.get(field) or "") != str(bundle_json.get(field) or ""):
            errors.append(f"handoff-to-feature-delivery.json {field} must match impl-bundle.json.")
    if not ensure_list(handoff.get("deliverables")):
        errors.append("handoff-to-feature-delivery.json must include deliverables.")
    if not ensure_list(handoff.get("acceptance_refs")):
        errors.append("handoff-to-feature-delivery.json must include acceptance_refs.")
    evidence_rows = evidence_plan.get("rows")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        errors.append("dev-evidence-plan.json must include at least one evidence row.")
    else:
        evidence_acceptance_refs = {
            str(item.get("acceptance_ref") or "").strip()
            for item in evidence_rows
            if isinstance(item, dict) and str(item.get("acceptance_ref") or "").strip()
        }
        handoff_acceptance_refs = set(ensure_list(handoff.get("acceptance_refs")))
        missing_evidence_refs = [item for item in sorted(handoff_acceptance_refs) if item not in evidence_acceptance_refs]
        if missing_evidence_refs:
            errors.append("dev-evidence-plan.json must cover all acceptance_refs: " + ", ".join(missing_evidence_refs) + ".")
    expected_inputs = workstream_required_inputs(bundle_json.get("workstream_assessment") or {})
    actual_inputs = ensure_list(smoke_gate.get("required_inputs"))
    missing_inputs = [item for item in expected_inputs if item not in actual_inputs]
    if missing_inputs:
        errors.append(f"smoke-gate-subject.json required_inputs is missing: {', '.join(missing_inputs)}.")
    if str(upstream_refs.get("feat_ref") or "") != str(bundle_json.get("feat_ref") or ""):
        errors.append("upstream-design-refs.json feat_ref must match impl-bundle.json.")
    if str(upstream_refs.get("tech_ref") or "") != str(bundle_json.get("tech_ref") or ""):
        errors.append("upstream-design-refs.json tech_ref must match impl-bundle.json.")
    return errors


def check_status_model(manifest: dict[str, Any], bundle_json: dict[str, Any], smoke_gate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    manifest_status = str(manifest.get("status") or "")
    bundle_status = str(bundle_json.get("status") or "")
    smoke_status = str(smoke_gate.get("status") or "")
    if manifest_status not in {"in_progress", "execution_ready", "blocked"}:
        errors.append("package-manifest.json.status is invalid.")
    if bundle_status not in {"in_progress", "execution_ready", "blocked"}:
        errors.append("impl-bundle.json.status is invalid.")
    if smoke_status not in {"pending_review", "pending_execution", "blocked"}:
        errors.append("smoke-gate-subject.json.status is invalid.")
    if manifest_status != bundle_status:
        errors.append("package-manifest.json.status must match impl-bundle.json.status.")
    if bundle_status == "execution_ready" and (smoke_status != "pending_execution" or smoke_gate.get("ready_for_execution") is not True):
        errors.append("execution_ready packages must have ready_for_execution true and pending_execution smoke status.")
    if bundle_status == "blocked" and smoke_status != "blocked":
        errors.append("blocked packages must have blocked smoke gate subject.")
    if bundle_status == "in_progress" and smoke_gate.get("ready_for_execution") is True:
        errors.append("in_progress packages must not already be ready_for_execution.")
    return errors


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors

    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    review_report = load_json(artifacts_dir / "impl-review-report.json")
    acceptance_report = load_json(artifacts_dir / "impl-acceptance-report.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    evidence_plan = load_json(artifacts_dir / "dev-evidence-plan.json")

    readiness_errors: list[str] = []
    if bundle_json.get("status") != "execution_ready":
        readiness_errors.append("impl-bundle.json status must be execution_ready.")
    if manifest.get("status") != "execution_ready":
        readiness_errors.append("package-manifest.json status must be execution_ready.")
    if review_report.get("decision") != "pass":
        readiness_errors.append("impl-review-report.json decision must be pass.")
    if acceptance_report.get("decision") != "approve":
        readiness_errors.append("impl-acceptance-report.json decision must be approve.")
    if smoke_gate.get("ready_for_execution") is not True:
        readiness_errors.append("smoke-gate-subject.json must mark ready_for_execution true.")
    if load_json(artifacts_dir / "document-test-report.json").get("test_outcome") != "no_blocking_defect_found":
        readiness_errors.append("document_test_non_blocking")
    if not isinstance(evidence_plan.get("rows"), list) or not evidence_plan.get("rows"):
        readiness_errors.append("dev-evidence-plan.json rows must be non-empty.")
    return not readiness_errors, readiness_errors
