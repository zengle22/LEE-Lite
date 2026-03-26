#!/usr/bin/env python3
"""
Validation helpers for tech-to-impl review.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tech_to_impl_common import ensure_list, load_json, parse_markdown_frontmatter
from tech_to_impl_builder import DOWNSTREAM_TEMPLATE_ID, DOWNSTREAM_TEMPLATE_PATH
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
    "impl-acceptance-report.json",
    "impl-defect-list.json",
    "handoff-to-feature-delivery.json",
    "semantic-drift-check.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
REQUIRED_BUNDLE_HEADINGS = [
    "Selected Upstream",
    "Applicability Assessment",
    "Implementation Task",
    "Integration Plan",
    "Evidence Plan",
    "Smoke Gate Subject",
    "Delivery Handoff",
    "Traceability",
]
REQUIRED_IMPL_TASK_HEADINGS = [
    "## 1. 目标",
    "## 2. 上游依赖",
    "## 3. 实施范围",
    "## 4. 实施步骤",
    "## 5. 风险与阻塞",
    "## 6. 交付物",
    "## 7. 验收检查点",
]


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
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")

    errors.extend(check_bundle_identity(bundle_json))
    errors.extend(check_source_refs(bundle_json))
    errors.extend(check_markdown_sections(artifacts_dir))
    errors.extend(check_workstream_presence(artifacts_dir, bundle_json))
    errors.extend(check_handoff_and_evidence(handoff, upstream_refs, bundle_json, evidence_plan, smoke_gate))
    errors.extend(check_status_model(manifest, bundle_json, smoke_gate))

    return errors, {
        "valid": not errors,
        "feat_ref": bundle_json.get("feat_ref"),
        "tech_ref": bundle_json.get("tech_ref"),
        "impl_ref": bundle_json.get("impl_ref"),
        "manifest_status": str(manifest.get("status") or ""),
        "smoke_gate_status": str(smoke_gate.get("status") or ""),
        "semantic_lock_preserved": semantic_drift_check.get("semantic_lock_preserved", True),
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
    _, impl_task_body = parse_markdown_frontmatter((artifacts_dir / "impl-task.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_IMPL_TASK_HEADINGS:
        if heading not in impl_task_body:
            errors.append(f"impl-task.md is missing section: {heading}")
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
    if not isinstance(evidence_plan.get("rows"), list) or not evidence_plan.get("rows"):
        readiness_errors.append("dev-evidence-plan.json rows must be non-empty.")
    return not readiness_errors, readiness_errors
