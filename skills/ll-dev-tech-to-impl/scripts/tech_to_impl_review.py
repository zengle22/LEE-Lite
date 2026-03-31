#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section
from tech_to_impl_builder import DOWNSTREAM_TEMPLATE_ID, DOWNSTREAM_TEMPLATE_PATH
from tech_to_impl_common import dump_json, ensure_list, load_json, parse_markdown_frontmatter, render_markdown
from tech_to_impl_derivation import workstream_required_inputs
from tech_to_impl_review_support import REQUIRED_OUTPUT_FILES


def write_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(frontmatter, body), encoding="utf-8")


def _revision_metadata(generated: dict[str, Any]) -> dict[str, Any]:
    bundle_json = generated.get("bundle_json") if isinstance(generated.get("bundle_json"), dict) else {}
    revision_context = bundle_json.get("revision_context") if isinstance(bundle_json, dict) else {}
    if not isinstance(revision_context, dict):
        revision_context = {}
    revision_request_ref = str(
        generated.get("revision_request_ref")
        or revision_context.get("revision_request_ref")
        or ""
    ).strip()
    revision_round = int(generated.get("revision_round") or revision_context.get("revision_round") or 0)
    revision_summary = str(
        generated.get("revision_summary")
        or revision_context.get("summary")
        or ""
    ).strip()
    payload = {
        "revision_request_ref": revision_request_ref,
        "revision_round": revision_round,
        "revision_summary": revision_summary,
    }
    return {key: value for key, value in payload.items() if value not in {"", 0}}


def _build_document_test_report(generated: dict[str, Any]) -> dict[str, Any]:
    consistency = generated["consistency"]
    semantic_drift = generated["semantic_drift_check"]
    blocking_found = (not consistency["passed"]) or semantic_drift.get("verdict") == "reject"
    revision_context = generated["bundle_json"].get("revision_context") if isinstance(generated["bundle_json"].get("revision_context"), dict) else {}
    report = build_document_test_report(
        workflow_key="dev.tech-to-impl",
        run_id=generated["bundle_json"]["workflow_run_id"],
        tested_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        defect_list=[{"severity": "P1", "title": item} for item in consistency["issues"]] if blocking_found else [],
        revision_request_ref=str(revision_context.get("revision_request_ref") or ""),
        structural={"package_integrity": True, "traceability_integrity": bool(generated["bundle_json"].get("source_refs")), "blocking": False},
        logic_consistency={"checked_topics": ["workstreams", "handoff", "evidence_plan", "canonical_boundary"], "conflicts_found": list(consistency["issues"]), "severity": "blocking" if blocking_found else "none", "blocking": blocking_found},
        downstream_readiness={"downstream_target": "template.dev.feature_delivery_l2", "consumption_contract_ref": "skills/ll-dev-tech-to-impl/ll.contract.yaml#validation.document_test.downstream_consumption_contract", "ready_for_gate_review": not blocking_found, "blocking_gaps": list(consistency["issues"]), "missing_contracts": [], "assumption_leaks": []},
        semantic_drift={"revision_context_present": bool(revision_context), "drift_detected": semantic_drift.get("verdict") == "reject", "drift_items": list(semantic_drift.get("forbidden_axis_detected") or []), "semantic_lock_preserved": semantic_drift.get("semantic_lock_preserved", True)},
        fixability=build_fixability_section(recommended_next_action="workflow_rebuild" if blocking_found else "submit_to_external_gate", recommended_actor="workflow_rebuild" if blocking_found else "external_gate_review", rebuild_required=1 if blocking_found else 0),
    )
    report["sections"].update({
        "canonical_package": {"status": "pass", "summary": "Package semantics are projected as canonical execution package only."},
        "freshness": {"status": "pass", "summary": "Package marked fresh_on_generation at creation time."},
        "discrepancy": {"status": "pass", "summary": "Repo discrepancy policy requires explicit handling before truth changes."},
        "self_contained_boundary": {"status": "pass", "summary": "Package projects minimum sufficient information, not upstream mirroring."},
    })
    return report


def _updated_document_test_sections(
    document_test_report: dict[str, Any],
    *,
    passed: bool,
    blocking: list[dict[str, Any]],
) -> dict[str, Any]:
    sections = document_test_report.get("sections") if isinstance(document_test_report.get("sections"), dict) else {}
    downstream = dict(sections.get("downstream_readiness") or {})
    downstream.update(
        {
            "downstream_target": str(downstream.get("downstream_target") or "template.dev.feature_delivery_l2"),
            "consumption_contract_ref": str(
                downstream.get("consumption_contract_ref")
                or "skills/ll-dev-tech-to-impl/ll.contract.yaml#validation.document_test.downstream_consumption_contract"
            ),
            "ready_for_gate_review": passed,
            "blocking_gaps": [str(item.get("title") or "") for item in blocking if str(item.get("title") or "").strip()],
            "missing_contracts": list(downstream.get("missing_contracts") or []),
            "assumption_leaks": list(downstream.get("assumption_leaks") or []),
        }
    )
    fixability = build_fixability_section(
        recommended_next_action="external_gate_review" if passed else "workflow_rebuild",
        recommended_actor="external_gate_review" if passed else "workflow_rebuild",
        mechanical_fixable=0 if passed else int((sections.get("fixability") or {}).get("mechanical_fixable") or 0),
        local_semantic_fixable=0 if passed else int((sections.get("fixability") or {}).get("local_semantic_fixable") or 0),
        rebuild_required=0 if passed else max(1, len(blocking)),
        human_judgement_required=int((sections.get("fixability") or {}).get("human_judgement_required") or 0),
    )
    return {
        **sections,
        "downstream_readiness": downstream,
        "fixability": fixability,
    }


def write_executor_outputs(output_dir: Path, package: Any, generated: dict[str, Any], command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    revision_metadata = _revision_metadata(generated)
    write_markdown(output_dir / "impl-bundle.md", generated["bundle_frontmatter"], generated["bundle_body"])
    dump_json(output_dir / "impl-bundle.json", generated["bundle_json"])
    write_markdown(output_dir / "impl-task.md", generated["impl_task_frontmatter"], generated["impl_task_body"])
    dump_json(output_dir / "upstream-design-refs.json", generated["upstream_design_refs"])
    write_markdown(output_dir / "integration-plan.md", generated["integration_frontmatter"], generated["integration_body"])
    dump_json(output_dir / "dev-evidence-plan.json", generated["evidence_plan"])
    dump_json(output_dir / "smoke-gate-subject.json", generated["smoke_gate_subject"])
    dump_json(output_dir / "impl-review-report.json", generated["review_report"])
    dump_json(output_dir / "document-test-report.json", _build_document_test_report(generated))
    dump_json(output_dir / "impl-acceptance-report.json", generated["acceptance_report"])
    dump_json(output_dir / "impl-defect-list.json", generated["defect_list"])
    dump_json(output_dir / "handoff-to-feature-delivery.json", generated["handoff"])
    dump_json(output_dir / "semantic-drift-check.json", generated["semantic_drift_check"])
    if revision_metadata:
        dump_json(output_dir / "revision-request.json", generated["revision_request"])

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
    if revision_metadata:
        outputs.append(str(output_dir / "revision-request.json"))

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
            "document_test_report_ref": str(output_dir / "document-test-report.json"),
            "acceptance_report_ref": str(output_dir / "impl-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "impl-defect-list.json"),
            "smoke_gate_subject_ref": str(output_dir / "smoke-gate-subject.json"),
            "handoff_ref": str(output_dir / "handoff-to-feature-delivery.json"),
            "semantic_drift_check_ref": str(output_dir / "semantic-drift-check.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
            **revision_metadata,
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
            **revision_metadata,
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
            **revision_metadata,
        },
    )


def build_supervision_evidence(artifacts_dir: Path) -> dict[str, Any]:
    bundle_json = load_json(artifacts_dir / "impl-bundle.json")
    handoff = load_json(artifacts_dir / "handoff-to-feature-delivery.json")
    upstream_refs = load_json(artifacts_dir / "upstream-design-refs.json")
    evidence_plan = load_json(artifacts_dir / "dev-evidence-plan.json")
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    findings: list[dict[str, Any]] = []
    package_semantics = bundle_json.get("package_semantics") or {}
    selected_upstream_refs = bundle_json.get("selected_upstream_refs") or {}

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
    if package_semantics.get("canonical_package") is not True or package_semantics.get("execution_time_single_entrypoint") is not True:
        findings.append({"severity": "P1", "title": "Missing canonical package semantics", "detail": "impl-bundle.json must mark canonical execution package semantics."})
    if str(selected_upstream_refs.get("feat_ref") or "") != str(bundle_json.get("feat_ref") or ""):
        findings.append({"severity": "P1", "title": "Missing selected upstream FEAT", "detail": "selected_upstream_refs must retain the selected feat_ref."})
    if bundle_json.get("freshness_status") not in {"fresh_on_generation", "needs_review", "stale"}:
        findings.append({"severity": "P1", "title": "Invalid freshness status", "detail": "freshness_status must be explicit and valid."})
    if str((bundle_json.get("repo_discrepancy_status") or {}).get("policy") or "") != "do_not_promote_repo_to_truth":
        findings.append({"severity": "P1", "title": "Missing discrepancy policy", "detail": "repo discrepancy policy must prevent repo-as-truth fallback."})
    if not ensure_list(handoff.get("deliverables")):
        findings.append({"severity": "P1", "title": "Missing handoff deliverables", "detail": "handoff-to-feature-delivery.json must freeze downstream deliverables."})
    if not ensure_list(handoff.get("acceptance_refs")):
        findings.append({"severity": "P1", "title": "Missing handoff acceptance refs", "detail": "handoff-to-feature-delivery.json must carry acceptance_refs for downstream execution."})
    evidence_rows = evidence_plan.get("rows")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        findings.append({"severity": "P1", "title": "Evidence plan is empty", "detail": "dev-evidence-plan.json must define at least one evidence row before the package can become execution-ready."})
    if semantic_drift_check.get("semantic_lock_present") and semantic_drift_check.get("semantic_lock_preserved") is not True:
        findings.append({"severity": "P1", "title": "semantic_lock drift detected", "detail": str(semantic_drift_check.get("summary") or "semantic_lock drift detected.")})

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
    document_test_report = load_json(artifacts_dir / "document-test-report.json")
    acceptance_report = load_json(artifacts_dir / "impl-acceptance-report.json")
    smoke_gate_subject = load_json(artifacts_dir / "smoke-gate-subject.json")
    evidence_plan = load_json(artifacts_dir / "dev-evidence-plan.json")
    revision_metadata = _revision_metadata({"bundle_json": bundle_json, **supervision})

    blocking = [item for item in supervision.get("semantic_findings") or [] if str(item.get("severity") or "") in {"P0", "P1"}]
    passed = supervision.get("decision") == "pass"
    bundle_status = "execution_ready" if passed else "blocked"

    bundle_json["status"] = bundle_status
    bundle_json["status_model"] = {"package": bundle_status, "smoke_gate": "pending_execution" if passed else "blocked"}
    manifest["status"] = bundle_status
    if revision_metadata:
        bundle_json["revision_context"] = bundle_json.get("revision_context") or {}
        bundle_json["revision_context"].update(revision_metadata)
        manifest.update(revision_metadata)

    review_report.update(
        {
            "status": "completed",
            "decision": "pass" if passed else "revise",
            "summary": "Implementation task review passed." if passed else "Implementation task review requires revision.",
            "findings": supervision.get("semantic_findings") or [],
            **revision_metadata,
        }
    )
    document_test_report.update(
        {
            "tested_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "test_outcome": "no_blocking_defect_found" if passed else "blocking_defect_found",
            "defect_counts": {"blocking": len(blocking), "non_blocking": 0},
            "recommended_next_action": "external_gate_review" if passed else "workflow_rebuild",
            "recommended_actor": "external_gate_review" if passed else "workflow_rebuild",
            "sections": _updated_document_test_sections(document_test_report, passed=passed, blocking=blocking),
            **revision_metadata,
        }
    )
    acceptance_report.update(
        {
            "status": "completed",
            "decision": "approve" if passed else "revise",
            "summary": "Candidate package satisfies downstream execution entry conditions." if passed else "Candidate package does not yet satisfy downstream execution entry conditions.",
            "acceptance_findings": blocking,
            **revision_metadata,
        }
    )
    smoke_gate_subject.update(
        {
            "status": "pending_execution" if passed else "blocked",
            "decision": "ready" if passed else "revise",
            "ready_for_execution": passed,
            **revision_metadata,
        }
    )
    evidence_plan["status"] = bundle_status
    if revision_metadata:
        evidence_plan.update(revision_metadata)

    frontmatter, body = parse_markdown_frontmatter((artifacts_dir / "impl-bundle.md").read_text(encoding="utf-8"))
    frontmatter["status"] = bundle_status
    if revision_metadata:
        frontmatter.update(revision_metadata)
    (artifacts_dir / "impl-bundle.md").write_text(render_markdown(frontmatter, body), encoding="utf-8")
    for name in [
        "impl-task.md",
        "integration-plan.md",
        "frontend-workstream.md",
        "backend-workstream.md",
        "migration-cutover-plan.md",
    ]:
        path = artifacts_dir / name
        if not path.exists():
            continue
        frontmatter, body = parse_markdown_frontmatter(path.read_text(encoding="utf-8"))
        frontmatter["status"] = bundle_status
        if revision_metadata:
            frontmatter.update(revision_metadata)
        path.write_text(render_markdown(frontmatter, body), encoding="utf-8")

    dump_json(artifacts_dir / "impl-bundle.json", bundle_json)
    dump_json(artifacts_dir / "impl-review-report.json", review_report)
    dump_json(artifacts_dir / "document-test-report.json", document_test_report)
    dump_json(artifacts_dir / "impl-acceptance-report.json", acceptance_report)
    dump_json(artifacts_dir / "impl-defect-list.json", supervision.get("semantic_findings") or [])
    dump_json(artifacts_dir / "dev-evidence-plan.json", evidence_plan)
    dump_json(artifacts_dir / "smoke-gate-subject.json", smoke_gate_subject)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "package-manifest.json", manifest)


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    from tech_to_impl_review_support import validate_output_package as _validate_output_package

    return _validate_output_package(artifacts_dir)


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    from tech_to_impl_review_support import validate_package_readiness as _validate_package_readiness

    return _validate_package_readiness(artifacts_dir)


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
                f"- revision_request_ref: {execution.get('revision_request_ref') or supervision.get('revision_request_ref') or ''}",
                f"- revision_round: {execution.get('revision_round') or supervision.get('revision_round') or ''}",
                f"- revision_summary: {execution.get('revision_summary') or supervision.get('revision_summary') or ''}",
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

