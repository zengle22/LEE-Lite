#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from tech_to_impl_builder import DOWNSTREAM_TEMPLATE_ID, DOWNSTREAM_TEMPLATE_PATH
from tech_to_impl_common import dump_json, ensure_list, load_json, parse_markdown_frontmatter, render_markdown
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


def write_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(frontmatter, body), encoding="utf-8")


def write_executor_outputs(output_dir: Path, package: Any, generated: dict[str, Any], command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_markdown(output_dir / "impl-bundle.md", generated["bundle_frontmatter"], generated["bundle_body"])
    dump_json(output_dir / "impl-bundle.json", generated["bundle_json"])
    write_markdown(output_dir / "impl-task.md", generated["impl_task_frontmatter"], generated["impl_task_body"])
    dump_json(output_dir / "upstream-design-refs.json", generated["upstream_design_refs"])
    write_markdown(output_dir / "integration-plan.md", generated["integration_frontmatter"], generated["integration_body"])
    dump_json(output_dir / "dev-evidence-plan.json", generated["evidence_plan"])
    dump_json(output_dir / "smoke-gate-subject.json", generated["smoke_gate_subject"])
    dump_json(output_dir / "impl-review-report.json", generated["review_report"])
    dump_json(output_dir / "impl-acceptance-report.json", generated["acceptance_report"])
    dump_json(output_dir / "impl-defect-list.json", generated["defect_list"])
    dump_json(output_dir / "handoff-to-feature-delivery.json", generated["handoff"])
    dump_json(output_dir / "semantic-drift-check.json", generated["semantic_drift_check"])

    optional_markdown = [
        ("frontend-workstream.md", generated["frontend_frontmatter"], generated["frontend_body"]),
        ("backend-workstream.md", generated["backend_frontmatter"], generated["backend_body"]),
        ("migration-cutover-plan.md", generated["migration_frontmatter"], generated["migration_body"]),
    ]
    for name, frontmatter, body in optional_markdown:
        path = output_dir / name
        if frontmatter and body:
            write_markdown(path, frontmatter, body)
        elif path.exists():
            path.unlink()

    outputs = [str(output_dir / name) for name in REQUIRED_OUTPUT_FILES if name != "supervision-evidence.json"]
    for name, frontmatter, _ in optional_markdown:
        if frontmatter:
            outputs.append(str(output_dir / name))

    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": generated["bundle_json"]["workflow_run_id"],
            "workflow_key": "dev.tech-to-impl",
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "feat_ref": generated["bundle_json"]["feat_ref"],
            "tech_ref": generated["bundle_json"]["tech_ref"],
            "impl_ref": generated["bundle_json"]["impl_ref"],
            "status": generated["bundle_json"]["status"],
            "primary_artifact_ref": str(output_dir / "impl-bundle.json"),
            "review_report_ref": str(output_dir / "impl-review-report.json"),
            "acceptance_report_ref": str(output_dir / "impl-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "impl-defect-list.json"),
            "smoke_gate_subject_ref": str(output_dir / "smoke-gate-subject.json"),
            "handoff_ref": str(output_dir / "handoff-to-feature-delivery.json"),
            "semantic_drift_check_ref": str(output_dir / "semantic-drift-check.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
        },
    )
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-dev-tech-to-impl",
            "run_id": generated["bundle_json"]["workflow_run_id"],
            "role": "executor",
            "inputs": [str(package.artifacts_dir), generated["bundle_json"]["feat_ref"], generated["bundle_json"]["tech_ref"]],
            "outputs": outputs,
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "impl_task_present": True,
                "upstream_design_refs_present": True,
                "frontend_required": generated["assessment"]["frontend_required"],
                "backend_required": generated["assessment"]["backend_required"],
                "migration_required": generated["assessment"]["migration_required"],
                "consistency_passed": generated["consistency"]["passed"],
                "semantic_lock_present": bool(generated["bundle_json"].get("semantic_lock")),
                "semantic_lock_preserved": generated["semantic_drift_check"].get("semantic_lock_preserved", True),
            },
            "key_decisions": generated["execution_decisions"],
            "uncertainties": generated["execution_uncertainties"],
        },
    )
    dump_json(
        output_dir / "supervision-evidence.json",
        {
            "skill_id": "ll-dev-tech-to-impl",
            "run_id": generated["bundle_json"]["workflow_run_id"],
            "role": "supervisor",
            "reviewed_inputs": [str(output_dir / "impl-bundle.md"), str(output_dir / "impl-bundle.json")],
            "reviewed_outputs": [str(output_dir / "impl-task.md"), str(output_dir / "integration-plan.md")],
            "semantic_findings": [],
            "decision": "revise",
            "reason": "Pending supervisor review.",
        },
    )


def build_supervision_evidence(artifacts_dir: Path) -> dict[str, Any]:
    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    handoff = load_json(artifacts_dir / "handoff-to-feature-delivery.json")
    upstream_refs = load_json(artifacts_dir / "upstream-design-refs.json")
    evidence_plan = load_json(artifacts_dir / "dev-evidence-plan.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    findings: list[dict[str, Any]] = []

    assessment = bundle_json.get("workstream_assessment") or {}
    frontend_required = bool(assessment.get("frontend_required"))
    backend_required = bool(assessment.get("backend_required"))
    migration_required = bool(assessment.get("migration_required"))

    if handoff.get("target_template_id") != DOWNSTREAM_TEMPLATE_ID:
        findings.append({"severity": "P1", "title": "Wrong downstream template target", "detail": f"Handoff must target {DOWNSTREAM_TEMPLATE_ID}."})
    if handoff.get("target_template_path") != DOWNSTREAM_TEMPLATE_PATH:
        findings.append({"severity": "P1", "title": "Wrong downstream template path", "detail": "Handoff target_template_path is inconsistent."})
    if not (frontend_required or backend_required):
        findings.append({"severity": "P1", "title": "No execution surface selected", "detail": "At least one frontend or backend workstream must be present."})
    if frontend_required and not (artifacts_dir / "frontend-workstream.md").exists():
        findings.append({"severity": "P1", "title": "Missing frontend workstream", "detail": "frontend_required is true but frontend-workstream.md is missing."})
    if backend_required and not (artifacts_dir / "backend-workstream.md").exists():
        findings.append({"severity": "P1", "title": "Missing backend workstream", "detail": "backend_required is true but backend-workstream.md is missing."})
    if migration_required and not (artifacts_dir / "migration-cutover-plan.md").exists():
        findings.append({"severity": "P1", "title": "Missing migration plan", "detail": "migration_required is true but migration-cutover-plan.md is missing."})
    if str(upstream_refs.get("feat_ref") or "") != str(bundle_json.get("feat_ref") or ""):
        findings.append({"severity": "P1", "title": "Upstream FEAT mismatch", "detail": "upstream-design-refs.json must retain the selected feat_ref."})
    if str(upstream_refs.get("tech_ref") or "") != str(bundle_json.get("tech_ref") or ""):
        findings.append({"severity": "P1", "title": "Upstream TECH mismatch", "detail": "upstream-design-refs.json must retain the selected tech_ref."})
    if not ensure_list(handoff.get("deliverables")):
        findings.append({"severity": "P1", "title": "Missing handoff deliverables", "detail": "handoff-to-feature-delivery.json must freeze downstream deliverables."})
    if not ensure_list(handoff.get("acceptance_refs")):
        findings.append({"severity": "P1", "title": "Missing handoff acceptance refs", "detail": "handoff-to-feature-delivery.json must carry acceptance_refs for downstream execution."})
    evidence_rows = evidence_plan.get("rows")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        findings.append({"severity": "P1", "title": "Evidence plan is empty", "detail": "dev-evidence-plan.json must define at least one evidence row before the package can become execution-ready."})

    expected_inputs = workstream_required_inputs(assessment)
    actual_inputs = ensure_list(smoke_gate.get("required_inputs"))
    missing_inputs = [item for item in expected_inputs if item not in actual_inputs]
    if missing_inputs:
        findings.append(
            {
                "severity": "P1",
                "title": "Smoke gate missing workstream inputs",
                "detail": f"smoke-gate-subject.json required_inputs is missing: {', '.join(missing_inputs)}.",
            }
        )

    blocking = [item for item in findings if str(item.get("severity") or "") in {"P0", "P1"}]
    passed = not blocking
    return {
        "skill_id": "ll-dev-tech-to-impl",
        "run_id": str(bundle_json.get("workflow_run_id") or artifacts_dir.name),
        "role": "supervisor",
        "reviewed_inputs": [
            str(artifacts_dir / "impl-bundle.md"),
            str(artifacts_dir / "impl-bundle.json"),
            str(artifacts_dir / "upstream-design-refs.json"),
        ],
        "reviewed_outputs": [
            str(artifacts_dir / "impl-task.md"),
            str(artifacts_dir / "integration-plan.md"),
            str(artifacts_dir / "handoff-to-feature-delivery.json"),
        ],
        "semantic_findings": findings,
        "decision": "pass" if passed else "revise",
        "reason": "Implementation task package is ready for downstream execution." if passed else "Implementation task package requires revision before downstream execution.",
    }


def update_supervisor_outputs(artifacts_dir: Path, supervision: dict[str, Any]) -> None:
    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    review_report = load_json(artifacts_dir / "impl-review-report.json")
    acceptance_report = load_json(artifacts_dir / "impl-acceptance-report.json")
    smoke_gate_subject = load_json(artifacts_dir / "smoke-gate-subject.json")

    blocking = [item for item in supervision.get("semantic_findings") or [] if str(item.get("severity") or "") in {"P0", "P1"}]
    passed = supervision.get("decision") == "pass"
    bundle_status = "execution_ready" if passed else "blocked"

    bundle_json["status"] = bundle_status
    bundle_json["status_model"] = {"package": bundle_status, "smoke_gate": "pending_execution" if passed else "blocked"}
    manifest["status"] = bundle_status

    review_report.update(
        {
            "status": "completed",
            "decision": "pass" if passed else "revise",
            "summary": "Implementation task review passed." if passed else "Implementation task review requires revision.",
            "findings": supervision.get("semantic_findings") or [],
        }
    )
    acceptance_report.update(
        {
            "status": "completed",
            "decision": "approve" if passed else "revise",
            "summary": "Candidate package satisfies downstream execution entry conditions." if passed else "Candidate package does not yet satisfy downstream execution entry conditions.",
            "acceptance_findings": blocking,
        }
    )
    smoke_gate_subject.update(
        {
            "status": "pending_execution" if passed else "blocked",
            "decision": "ready" if passed else "revise",
            "ready_for_execution": passed,
        }
    )

    frontmatter, body = parse_markdown_frontmatter((artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8"))
    frontmatter["status"] = bundle_status
    (artifacts_dir / "impl-bundle.md").write_text(render_markdown(frontmatter, body), encoding="utf-8")

    dump_json(artifacts_dir / "impl-bundle.json", bundle_json)
    dump_json(artifacts_dir / "impl-review-report.json", review_report)
    dump_json(artifacts_dir / "impl-acceptance-report.json", acceptance_report)
    dump_json(artifacts_dir / "impl-defect-list.json", supervision.get("semantic_findings") or [])
    dump_json(artifacts_dir / "smoke-gate-subject.json", smoke_gate_subject)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "package-manifest.json", manifest)


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

    if bundle_json.get("artifact_type") != "feature_impl_candidate_package":
        errors.append("impl-bundle.json artifact_type must be feature_impl_candidate_package.")
    if bundle_json.get("workflow_key") != "dev.tech-to-impl":
        errors.append("impl-bundle.json workflow_key must be dev.tech-to-impl.")
    if bundle_json.get("package_role") != "candidate":
        errors.append("impl-bundle.json package_role must be candidate.")

    source_refs = ensure_list(bundle_json.get("source_refs"))
    for prefix in ["dev.feat-to-tech::", "FEAT-", "TECH-", "EPIC-", "SRC-"]:
        if not any(ref.startswith(prefix) for ref in source_refs):
            errors.append(f"impl-bundle.json source_refs must include {prefix}.")

    _, bundle_body = parse_markdown_frontmatter((artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_BUNDLE_HEADINGS:
        if f"## {heading}" not in bundle_body:
            errors.append(f"impl-bundle.md is missing section: {heading}")

    _, impl_task_body = parse_markdown_frontmatter((artifacts_dir / "impl-task.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_IMPL_TASK_HEADINGS:
        if heading not in impl_task_body:
            errors.append(f"impl-task.md is missing section: {heading}")

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

    if str(upstream_refs.get("feat_ref") or "") != str(bundle_json.get("feat_ref") or ""):
        errors.append("upstream-design-refs.json feat_ref must match impl-bundle.json.")
    if str(upstream_refs.get("tech_ref") or "") != str(bundle_json.get("tech_ref") or ""):
        errors.append("upstream-design-refs.json tech_ref must match impl-bundle.json.")

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
            errors.append(
                "dev-evidence-plan.json must cover all acceptance_refs: " + ", ".join(missing_evidence_refs) + "."
            )

    expected_inputs = workstream_required_inputs(assessment)
    actual_inputs = ensure_list(smoke_gate.get("required_inputs"))
    missing_inputs = [item for item in expected_inputs if item not in actual_inputs]
    if missing_inputs:
        errors.append(f"smoke-gate-subject.json required_inputs is missing: {', '.join(missing_inputs)}.")

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

    return errors, {
        "valid": not errors,
        "feat_ref": bundle_json.get("feat_ref"),
        "tech_ref": bundle_json.get("tech_ref"),
        "impl_ref": bundle_json.get("impl_ref"),
        "manifest_status": manifest_status,
        "smoke_gate_status": smoke_status,
    }


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


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-dev-tech-to-impl Evidence Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- inputs: {', '.join(str(item) for item in execution.get('inputs', []))}",
                f"- output_dir: {artifacts_dir}",
                "",
                "## Execution Evidence",
                "",
                f"- commands: {', '.join(execution.get('commands_run', []))}",
                f"- decisions: {', '.join(execution.get('key_decisions', []))}",
                "",
                "## Supervision Evidence",
                "",
                f"- decision: {supervision.get('decision')}",
                f"- reason: {supervision.get('reason')}",
                "",
                "## Smoke Gate Subject",
                "",
                f"- status: {smoke_gate.get('status')}",
                f"- ready_for_execution: {smoke_gate.get('ready_for_execution')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path

