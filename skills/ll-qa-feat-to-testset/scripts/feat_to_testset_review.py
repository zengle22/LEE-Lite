#!/usr/bin/env python3
"""Review, supervision, validation, and reporting helpers for feat-to-testset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from feat_to_testset_common import dump_json, dump_yaml, ensure_list, load_json, parse_markdown_frontmatter, render_markdown
from feat_to_testset_cli_integration import refresh_supervisor_bundle
from feat_to_testset_document_test import build_document_test
from cli.lib.workflow_document_test import validate_document_test_report

ENVIRONMENT_INPUT_CATEGORIES = [
    "environment",
    "data",
    "services",
    "access",
    "feature_flags",
    "ui_or_integration_context",
]
REQUIRED_OUTPUT_FILES = [
    "package-manifest.json",
    "test-set-bundle.md",
    "test-set-bundle.json",
    "test-set.yaml",
    "analysis.md",
    "strategy-draft.yaml",
    "test-set-review-report.json",
    "test-set-acceptance-report.json",
    "test-set-defect-list.json",
    "document-test-report.json",
    "test-set-freeze-gate.json",
    "gate-subject-index.json",
    "analysis-review-subject.json",
    "strategy-review-subject.json",
    "test-set-approval-subject.json",
    "handoff-to-test-execution.json",
    "semantic-drift-check.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
REQUIRED_MARKDOWN_HEADINGS = [
    "Selected FEAT",
    "Requirement Analysis",
    "Strategy Draft",
    "TESTSET",
    "Gate Subjects",
    "Downstream Handoff",
    "Traceability",
]
SUBJECT_FILE_NAMES = {
    "analysis_review": "analysis-review-subject.json",
    "strategy_review": "strategy-review-subject.json",
    "test_set_approval": "test-set-approval-subject.json",
}
SUPPORTED_DOWNSTREAM_SKILLS = {
    "skill.qa.test_exec_cli",
    "skill.qa.test_exec_web_e2e",
}


def yaml_load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _build_findings(test_set_yaml: dict[str, Any], handoff: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not ensure_list(test_set_yaml.get("governing_adrs")):
        findings.append(
            {
                "severity": "P2",
                "title": "No governing ADR refs were inherited",
                "detail": "The candidate package is usable, but governing ADR lineage should be made explicit when available.",
            }
        )
    required_inputs = handoff.get("required_environment_inputs") or {}
    for category in ENVIRONMENT_INPUT_CATEGORIES:
        if not ensure_list(required_inputs.get(category)):
            findings.append(
                {
                    "severity": "P1",
                    "title": f"Missing required environment input category: {category}",
                    "detail": "Downstream execution handoff must cover all required environment input categories.",
                }
            )
    return findings


def build_supervision_evidence(artifacts_dir: Path) -> dict[str, Any]:
    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    handoff = load_json(artifacts_dir / "handoff-to-test-execution.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    revision_context = bundle_json.get("revision_context") or {}
    findings = _build_findings(test_set_yaml, handoff)
    if semantic_drift_check.get("semantic_lock_present") and semantic_drift_check.get("semantic_lock_preserved") is not True:
        findings.append(
            {
                "severity": "P1",
                "title": "semantic_lock drift detected",
                "detail": str(semantic_drift_check.get("summary") or "semantic_lock drift detected."),
            }
        )
    blocking = [item for item in findings if str(item.get("severity") or "") in {"P0", "P1"}]
    decision = "pass" if not blocking else "revise"
    return {
        "skill_id": "ll-qa-feat-to-testset",
        "run_id": str(bundle_json.get("workflow_run_id") or artifacts_dir.name),
        "role": "supervisor",
        "reviewed_inputs": [str(artifacts_dir / "analysis.md"), str(artifacts_dir / "strategy-draft.yaml")],
        "reviewed_outputs": [
            str(artifacts_dir / "test-set.yaml"),
            str(artifacts_dir / "test-set-bundle.json"),
            str(artifacts_dir / "handoff-to-test-execution.json"),
        ],
        "semantic_findings": findings,
        "decision": decision,
        "reason": (
            "TESTSET candidate package is ready for external approval handoff."
            if decision == "pass"
            else "TESTSET candidate package requires revision before external approval."
        ),
        "document_test_report_ref": str(artifacts_dir / "document-test-report.json"),
        "document_test_outcome": "no_blocking_defect_found" if decision == "pass" else "blocking_defect_found",
        **({"revision_context": revision_context} if revision_context else {}),
    }


def update_supervisor_outputs(artifacts_dir: Path, repo_root: Path, supervision: dict[str, Any]) -> dict[str, Any]:
    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    review_report = load_json(artifacts_dir / "test-set-review-report.json")
    acceptance_report = load_json(artifacts_dir / "test-set-acceptance-report.json")
    freeze_gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    blocking = [item for item in supervision.get("semantic_findings") or [] if str(item.get("severity") or "") in {"P0", "P1"}]
    passed = supervision.get("decision") == "pass"
    manifest_status = "approval_pending" if passed else "review_pending"
    test_set_status = "approved" if passed else "review_ready"
    gate_status = "pending" if passed else "failed"
    gate_decision = "pending" if passed else "revise"

    bundle_json["status"] = manifest_status
    manifest["status"] = manifest_status
    test_set_yaml["status"] = test_set_status
    review_report.update(
        {
            "status": "completed",
            "decision": "pass" if passed else "revise",
            "summary": "Analysis and strategy review passed." if passed else "Analysis and strategy review requires revision.",
            "findings": supervision.get("semantic_findings") or [],
            "updated_at": _utc_now(),
        }
    )
    acceptance_report.update(
        {
            "status": "completed",
            "decision": "approve" if passed else "revise",
            "summary": (
                "TESTSET content satisfies external approval entry conditions."
                if passed
                else "TESTSET content does not yet satisfy external approval entry conditions."
            ),
            "acceptance_findings": blocking,
            "updated_at": _utc_now(),
        }
    )
    document_test_report = build_document_test(
        run_id=str(bundle_json.get("workflow_run_id") or artifacts_dir.name),
        tested_at=_utc_now(),
        bundle_json=bundle_json,
        semantic_drift_check=semantic_drift_check,
        defects=supervision.get("semantic_findings") or [],
        downstream_target=str(bundle_json.get("downstream_target") or ""),
        required_environment_inputs=load_json(artifacts_dir / "handoff-to-test-execution.json").get("required_environment_inputs"),
        revision_context=revision_context or None,
        ready_for_gate_review=passed,
    )
    freeze_gate.update(
        {
            "status": gate_status,
            "decision": gate_decision,
            "freeze_ready": False,
            "ready_for_external_approval": passed,
            "checks": {
                "test_set_present": True,
                "analysis_present": True,
                "strategy_present": True,
                "gate_subjects_present": True,
                "handoff_present": True,
                "required_environment_inputs_present": not blocking,
                "semantic_lock_preserved": semantic_drift_check.get("semantic_lock_preserved", True),
                "document_test_report_present": document_test_report.get("test_outcome") in {"no_blocking_defect_found", "blocking_defect_found", "inconclusive", "not_applicable"},
                "document_test_non_blocking": passed,
            },
            "updated_at": _utc_now(),
        }
    )
    cli_commit = refresh_supervisor_bundle(repo_root, artifacts_dir, manifest_status)
    dump_json(artifacts_dir / "test-set-bundle.json", bundle_json)
    dump_yaml(artifacts_dir / "test-set.yaml", test_set_yaml)
    dump_json(artifacts_dir / "test-set-review-report.json", review_report)
    dump_json(artifacts_dir / "test-set-acceptance-report.json", acceptance_report)
    dump_json(artifacts_dir / "test-set-defect-list.json", supervision.get("semantic_findings") or [])
    dump_json(artifacts_dir / "document-test-report.json", document_test_report)
    dump_json(artifacts_dir / "test-set-freeze-gate.json", freeze_gate)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    manifest["cli_supervisor_commit_ref"] = str(cli_commit["response_path"])
    manifest["document_test_report_ref"] = str(artifacts_dir / "document-test-report.json")
    dump_json(artifacts_dir / "package-manifest.json", manifest)
    return cli_commit


def _validate_identity(bundle_json: dict[str, Any], errors: list[str]) -> None:
    if bundle_json.get("artifact_type") != "test_set_candidate_package":
        errors.append("test-set-bundle.json artifact_type must be test_set_candidate_package.")
    if bundle_json.get("workflow_key") != "qa.feat-to-testset":
        errors.append("test-set-bundle.json workflow_key must be qa.feat-to-testset.")
    if bundle_json.get("package_role") != "candidate":
        errors.append("test-set-bundle.json package_role must be candidate.")


def _validate_source_refs(bundle_json: dict[str, Any], errors: list[str]) -> None:
    source_refs = ensure_list(bundle_json.get("source_refs"))
    for prefix, message in [
        ("product.epic-to-feat::", "product.epic-to-feat::<run_id>"),
        ("FEAT-", "FEAT-*"),
        ("EPIC-", "EPIC-*"),
        ("SRC-", "SRC-*"),
    ]:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"test-set-bundle.json source_refs must include {message}.")


def _validate_test_set_yaml(test_set_yaml: dict[str, Any], errors: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if test_set_yaml.get("ssot_type") != "TESTSET":
        errors.append("test-set.yaml ssot_type must be TESTSET.")
    if test_set_yaml.get("workflow_key") != "qa.feat-to-testset":
        errors.append("test-set.yaml workflow_key must be qa.feat-to-testset.")
    test_units = test_set_yaml.get("test_units") or []
    acceptance_traceability = test_set_yaml.get("acceptance_traceability") or []
    if not isinstance(test_units, list) or not test_units:
        errors.append("test-set.yaml must contain non-empty test_units.")
    else:
        required_unit_fields = {
            "unit_ref",
            "title",
            "priority",
            "input_preconditions",
            "trigger_action",
            "observation_points",
            "pass_conditions",
            "fail_conditions",
            "required_evidence",
        }
        for index, unit in enumerate(test_units, start=1):
            if not isinstance(unit, dict):
                errors.append(f"test_units[{index}] must be an object.")
                continue
            missing = sorted(field for field in required_unit_fields if unit.get(field) in (None, "", []))
            if missing:
                errors.append(f"test_units[{index}] is missing required fields: {', '.join(missing)}.")
            if unit.get("acceptance_ref") in (None, "", []):
                if not ensure_list(unit.get("derivation_basis")):
                    errors.append(f"test_units[{index}] must include acceptance_ref or a non-empty derivation_basis.")
    if not isinstance(acceptance_traceability, list) or not acceptance_traceability:
        errors.append("test-set.yaml must contain non-empty acceptance_traceability.")
    else:
        for index, row in enumerate(acceptance_traceability, start=1):
            if not isinstance(row, dict):
                errors.append(f"acceptance_traceability[{index}] must be an object.")
                continue
            missing = sorted(
                field
                for field in ["acceptance_ref", "acceptance_scenario", "given", "when", "then", "unit_refs", "coverage_status"]
                if row.get(field) in (None, "", [])
            )
            if missing:
                errors.append(f"acceptance_traceability[{index}] is missing required fields: {', '.join(missing)}.")
        traceability_acceptance_refs = {str(row.get("acceptance_ref")) for row in acceptance_traceability if isinstance(row, dict)}
        unit_acceptance_refs = {str(unit.get("acceptance_ref")) for unit in test_units if isinstance(unit, dict) and unit.get("acceptance_ref") not in (None, "", [])}
        if traceability_acceptance_refs != unit_acceptance_refs:
            errors.append("acceptance_traceability must explicitly cover every acceptance_ref present in test_units.")
    return test_units, acceptance_traceability


def _validate_gate_subjects(artifacts_dir: Path, errors: list[str]) -> None:
    gate_subject_index = load_json(artifacts_dir / "gate-subject-index.json")
    subjects = gate_subject_index.get("subjects")
    if not isinstance(subjects, dict):
        errors.append("gate-subject-index.json must contain subjects.")
    for gate_type, filename in SUBJECT_FILE_NAMES.items():
        subject = load_json(artifacts_dir / filename)
        if subject.get("gate_type") != gate_type:
            errors.append(f"{filename} gate_type must be {gate_type}.")
        if subject.get("candidate_package_ref") != "test-set-bundle.json":
            errors.append(f"{filename} candidate_package_ref must be test-set-bundle.json.")


def _validate_handoff(bundle_json: dict[str, Any], handoff: dict[str, Any], errors: list[str]) -> None:
    target_skill = str(handoff.get("target_skill") or "")
    bundle_target = str(bundle_json.get("downstream_target") or "")
    if target_skill not in SUPPORTED_DOWNSTREAM_SKILLS:
        errors.append("handoff-to-test-execution.json target_skill must be a supported test execution sibling.")
    if bundle_target not in SUPPORTED_DOWNSTREAM_SKILLS:
        errors.append("test-set-bundle.json downstream_target must be a supported test execution sibling.")
    if target_skill and bundle_target and target_skill != bundle_target:
        errors.append("handoff-to-test-execution.json target_skill must match test-set-bundle.json downstream_target.")
    required_inputs = handoff.get("required_environment_inputs") or {}
    for category in ENVIRONMENT_INPUT_CATEGORIES:
        if not ensure_list(required_inputs.get(category)):
            errors.append(f"required_environment_inputs.{category} must be populated.")
    execution_context = " ".join(ensure_list(required_inputs.get("ui_or_integration_context"))).lower()
    if target_skill == "skill.qa.test_exec_cli" and not any(marker in execution_context for marker in ["cli", "command", "integration", "api", "调用", "命令"]):
        errors.append("CLI downstream handoff must describe CLI, command, API, or integration execution context.")
    if target_skill == "skill.qa.test_exec_web_e2e" and not any(marker in execution_context for marker in ["browser", "page", "locator", "selector", "ui", "浏览器", "页面", "定位器"]):
        errors.append("Web downstream handoff must describe browser, page, locator, or UI execution context.")


def _validate_statuses(bundle_json: dict[str, Any], test_set_yaml: dict[str, Any], freeze_gate: dict[str, Any], manifest: dict[str, Any], errors: list[str]) -> None:
    test_set_status = str(test_set_yaml.get("status") or "")
    manifest_status = str(manifest.get("status") or "")
    bundle_status = str(bundle_json.get("status") or "")
    gate_status = str(freeze_gate.get("status") or "")
    allowed_test_set = {"draft", "review_ready", "approved", "frozen"}
    allowed_manifest = {"in_progress", "review_pending", "approval_pending", "frozen", "rejected"}
    allowed_gate = {"pending", "passed", "failed"}
    if test_set_status not in allowed_test_set:
        errors.append(f"test-set.yaml.status must be one of {sorted(allowed_test_set)}.")
    if manifest_status not in allowed_manifest:
        errors.append(f"package-manifest.json.status must be one of {sorted(allowed_manifest)}.")
    if bundle_status not in allowed_manifest:
        errors.append(f"test-set-bundle.json.status must be one of {sorted(allowed_manifest)}.")
    if gate_status not in allowed_gate:
        errors.append(f"test-set-freeze-gate.json.status must be one of {sorted(allowed_gate)}.")


def _validate_state_relationships(bundle_json: dict[str, Any], test_set_yaml: dict[str, Any], freeze_gate: dict[str, Any], manifest: dict[str, Any], semantic_drift_check: dict[str, Any], errors: list[str]) -> None:
    manifest_status = str(manifest.get("status") or "")
    test_set_status = str(test_set_yaml.get("status") or "")
    gate_status = str(freeze_gate.get("status") or "")
    ready_for_external_approval = freeze_gate.get("ready_for_external_approval") is True
    if bundle_json.get("semantic_lock") and semantic_drift_check.get("semantic_lock_preserved") is not True:
        errors.append("semantic-drift-check.json must preserve semantic_lock when semantic_lock is present.")
    if manifest_status != str(bundle_json.get("status") or ""):
        errors.append("package-manifest.json.status must match test-set-bundle.json.status.")
    if manifest_status == "in_progress":
        if test_set_status != "draft" or gate_status != "pending":
            errors.append("in_progress packages must keep test-set draft and freeze gate pending.")
    elif manifest_status == "review_pending":
        if test_set_status != "review_ready" or gate_status != "failed" or ready_for_external_approval:
            errors.append("review_pending packages must map to test-set review_ready and failed freeze gate.")
    elif manifest_status == "approval_pending":
        if test_set_status != "approved" or gate_status != "pending" or not ready_for_external_approval:
            errors.append("approval_pending packages must map to test-set approved and pending freeze gate.")
    elif manifest_status == "frozen":
        if test_set_status != "frozen" or gate_status != "passed":
            errors.append("frozen packages must map to test-set frozen and passed freeze gate.")
    elif manifest_status == "rejected":
        if gate_status != "failed":
            errors.append("rejected packages must carry failed freeze gate.")


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}
    for required_file in REQUIRED_OUTPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required output artifact: {required_file}")
    if errors:
        return errors, {"valid": False}

    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    freeze_gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    handoff = load_json(artifacts_dir / "handoff-to-test-execution.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    errors.extend(validate_document_test_report(load_json(artifacts_dir / "document-test-report.json")))

    _validate_identity(bundle_json, errors)
    _validate_source_refs(bundle_json, errors)
    test_units, acceptance_traceability = _validate_test_set_yaml(test_set_yaml, errors)
    _validate_gate_subjects(artifacts_dir, errors)
    _validate_handoff(bundle_json, handoff, errors)
    _validate_statuses(bundle_json, test_set_yaml, freeze_gate, manifest, errors)
    _validate_state_relationships(bundle_json, test_set_yaml, freeze_gate, manifest, semantic_drift_check, errors)

    bundle_markdown = (artifacts_dir / "test-set-bundle.md").read_text(encoding="utf-8")
    _, bundle_body = parse_markdown_frontmatter(bundle_markdown)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if f"## {heading}" not in bundle_body:
            errors.append(f"test-set-bundle.md is missing section: {heading}")

    return errors, {
        "valid": not errors,
        "feat_ref": bundle_json.get("feat_ref"),
        "test_set_ref": bundle_json.get("test_set_ref"),
        "manifest_status": str(manifest.get("status") or ""),
        "test_set_status": str(test_set_yaml.get("status") or ""),
        "freeze_gate_status": str(freeze_gate.get("status") or ""),
        "semantic_lock_preserved": semantic_drift_check.get("semantic_lock_preserved", True),
        "test_units_count": len(test_units),
        "acceptance_traceability_count": len(acceptance_traceability),
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors
    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    freeze_gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    review_report = load_json(artifacts_dir / "test-set-review-report.json")
    acceptance_report = load_json(artifacts_dir / "test-set-acceptance-report.json")
    document_test_report = load_json(artifacts_dir / "document-test-report.json")
    readiness_errors: list[str] = []
    if bundle_json.get("status") != "approval_pending":
        readiness_errors.append("Candidate package status must be approval_pending.")
    if manifest.get("status") != "approval_pending":
        readiness_errors.append("Package manifest status must be approval_pending.")
    if test_set_yaml.get("status") != "approved":
        readiness_errors.append("test-set.yaml status must be approved.")
    if freeze_gate.get("status") != "pending":
        readiness_errors.append("test-set-freeze-gate.json status must be pending.")
    if freeze_gate.get("ready_for_external_approval") is not True:
        readiness_errors.append("test-set-freeze-gate.json must mark ready_for_external_approval true.")
    if review_report.get("decision") != "pass":
        readiness_errors.append("test-set-review-report.json decision must be pass.")
    if acceptance_report.get("decision") != "approve":
        readiness_errors.append("test-set-acceptance-report.json decision must be approve.")
    if document_test_report.get("test_outcome") != "no_blocking_defect_found":
        readiness_errors.append("document_test_non_blocking")
    return not readiness_errors, readiness_errors


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    bundle = load_json(artifacts_dir / "test-set-bundle.json")
    document_test = load_json(artifacts_dir / "document-test-report.json")
    revision_context = bundle.get("revision_context") or {}
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-qa-feat-to-testset Evidence Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- feat_ref: {execution.get('inputs', ['', ''])[-1]}",
                f"- output_dir: {artifacts_dir}",
                f"- revision_request_ref: {revision_context.get('revision_request_ref', '') or 'None'}",
                "",
                "## Execution Evidence",
                "",
                f"- decision: {execution.get('structural_results', {}).get('semantic_lock_preserved')}",
                f"- commands_run: {', '.join(ensure_list(execution.get('commands_run')))}",
                "",
                "## Supervision Evidence",
                "",
                f"- decision: {supervision.get('decision')}",
                f"- reason: {supervision.get('reason')}",
                "",
                "## Freeze Gate",
                "",
                f"- status: {gate.get('status')}",
                f"- ready_for_external_approval: {gate.get('ready_for_external_approval')}",
                "",
                "## Document Test",
                "",
                f"- test_outcome: {document_test.get('test_outcome')}",
                f"- recommended_next_action: {document_test.get('recommended_next_action')}",
                f"- recommended_actor: {document_test.get('recommended_actor')}",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
