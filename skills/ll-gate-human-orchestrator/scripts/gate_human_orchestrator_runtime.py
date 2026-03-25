#!/usr/bin/env python3
"""Lite-native runtime support for ll-gate-human-orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from gate_human_orchestrator_common import (
    dump_json,
    guess_repo_root_from_input,
    load_gate_ready_package,
    load_json,
    render_markdown,
    repo_relative,
    slugify,
    validate_input_package,
)
from gate_human_orchestrator_projection import (
    bundle_markdown,
    capture_projection_comment,
    dispatch_handoff,
    human_projection_findings,
    projection_bundle_fields,
    regenerate_projection_bundle,
    write_bundle_files,
    write_evidence_report,
)


def _cli_main():
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.ll import main

    return main


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "gate-human-orchestrator" / run_id


def default_run_id(package_path: Path) -> str:
    return slugify(package_path.parent.name or package_path.stem)


def _write_request(path: Path, payload: dict[str, Any]) -> None:
    dump_json(path, payload)


def _default_audit_refs(repo_root: Path) -> list[str]:
    default_ref = repo_root / "artifacts" / "active" / "audit" / "finding-bundle.json"
    if default_ref.exists():
        return [repo_relative(repo_root, default_ref)]
    return []


def _run_gate_command(group_action: list[str], request_path: Path, response_path: Path) -> dict[str, Any]:
    cli_main = _cli_main()
    exit_code = cli_main([*group_action, "--request", str(request_path), "--response-out", str(response_path)])
    response = load_json(response_path)
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"{' '.join(group_action)} failed: {response.get('status_code')} {response.get('message')}")
    return response


def executor_run(
    input_path: Path,
    repo_root: Path,
    run_id: str,
    decision: str = "",
    decision_reason: str = "",
    decision_target: str = "",
    audit_finding_refs: list[str] | None = None,
    allow_update: bool = False,
) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path)
    if errors:
        raise ValueError("; ".join(errors))

    package = load_gate_ready_package(input_path)
    effective_run_id = run_id or default_run_id(package.package_path)
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_cli").mkdir(parents=True, exist_ok=True)

    audit_refs = audit_finding_refs or _default_audit_refs(repo_root)
    resolved_target = decision_target or str(package.payload.get("candidate_ref", ""))
    trace = {
        "run_ref": effective_run_id,
        "workflow_key": "governance.gate-human-orchestrator",
    }

    evaluate_request_path = output_dir / "_cli" / "gate-evaluate.request.json"
    evaluate_response_path = output_dir / "_cli" / "gate-evaluate.response.json"
    evaluate_request = {
        "api_version": "v1",
        "command": "gate.evaluate",
        "request_id": f"req-gate-evaluate-{effective_run_id}",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-gate-human-orchestrator",
        "trace": trace,
        "payload": {
            "gate_ready_package_ref": repo_relative(repo_root, package.package_path),
            "audit_finding_refs": audit_refs,
            "target_matrix": {"allowed_targets": ["materialized_handoff", "materialized_job", "run_closure"]},
            "decision_target": resolved_target,
            "machine_ssot_ref": str(package.payload.get("machine_ssot_ref", "")),
            "decision_reason": decision_reason or "issued through governed human gate orchestrator",
            "evidence_refs": [str(package.payload.get("evidence_bundle_ref", ""))],
        },
    }
    if decision:
        evaluate_request["payload"]["decision"] = decision
    _write_request(evaluate_request_path, evaluate_request)
    evaluate = _run_gate_command(["gate", "evaluate"], evaluate_request_path, evaluate_response_path)
    result = evaluate["data"]

    dispatch_request_path = output_dir / "_cli" / "gate-dispatch.request.json"
    dispatch_response_path = output_dir / "_cli" / "gate-dispatch.response.json"
    dispatch_request = {
        "api_version": "v1",
        "command": "gate.dispatch",
        "request_id": f"req-gate-dispatch-{effective_run_id}",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-gate-human-orchestrator",
        "trace": trace,
        "payload": {
            "gate_decision_ref": result["gate_decision_ref"],
        },
    }
    _write_request(dispatch_request_path, dispatch_request)
    dispatch = _run_gate_command(["gate", "dispatch"], dispatch_request_path, dispatch_response_path)
    dispatch_result = dispatch["data"]
    projection_fields = projection_bundle_fields(
        repo_root,
        result["brief_record_ref"],
        str(package.payload.get("machine_ssot_ref", "")),
    )

    bundle_json = {
        "artifact_type": "gate_decision_package",
        "workflow_key": "governance.gate-human-orchestrator",
        "workflow_run_id": effective_run_id,
        "title": f"Gate Decision Package {effective_run_id}",
        "status": "drafted",
        "schema_version": "1.0.0",
        "input_ref": repo_relative(repo_root, package.package_path),
        **projection_fields,
        "decision_ref": result["decision_ref"],
        "decision": result["decision"],
        "decision_target": result["decision_target"],
        "decision_basis_refs": result["decision_basis_refs"],
        "dispatch_target": result["dispatch_target"],
        "materialized_handoff_ref": dispatch_result.get("materialized_handoff_ref", result.get("materialized_handoff_ref", "")),
        "materialized_job_ref": dispatch_result.get("materialized_job_ref", ""),
        "source_refs": [
            repo_relative(repo_root, package.package_path),
            result["decision_ref"],
            result["brief_record_ref"],
            result["pending_human_decision_ref"],
            *[ref for ref in (projection_fields["human_projection_ref"], projection_fields["snapshot_ref"], projection_fields["focus_ref"]) if ref],
        ],
        "runtime_refs": {
            "brief_record_ref": result["brief_record_ref"],
            "pending_human_decision_ref": result["pending_human_decision_ref"],
            "dispatch_receipt_ref": dispatch_result["dispatch_receipt_ref"],
            "materialized_handoff_ref": dispatch_result.get("materialized_handoff_ref", result.get("materialized_handoff_ref", "")),
            "materialized_job_ref": dispatch_result.get("materialized_job_ref", ""),
            "human_projection_ref": projection_fields["human_projection_ref"],
            "snapshot_ref": projection_fields["snapshot_ref"],
            "focus_ref": projection_fields["focus_ref"],
        },
    }
    write_bundle_files(output_dir, bundle_json)
    dump_json(
        output_dir / "runtime-artifact-refs.json",
        {
            "evaluate_request_ref": str(evaluate_request_path),
            "evaluate_response_ref": str(evaluate_response_path),
            "dispatch_request_ref": str(dispatch_request_path),
            "dispatch_response_ref": str(dispatch_response_path),
            **bundle_json["runtime_refs"],
        },
    )
    dump_json(
        output_dir / "gate-review-report.json",
        {
            "decision": "pass",
            "summary": "executor produced gate runtime outputs",
            "decision_action": bundle_json["decision"],
            "projection_status": bundle_json["projection_status"],
            "human_projection_ref": bundle_json["human_projection_ref"],
        },
    )
    dump_json(
        output_dir / "gate-acceptance-report.json",
        {"decision": "pending_supervisor", "summary": "awaiting supervisor review"},
    )
    dump_json(output_dir / "gate-defect-list.json", [])
    dump_json(output_dir / "handoff-to-gate-downstreams.json", dispatch_handoff(bundle_json))
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-gate-human-orchestrator",
            "run_id": effective_run_id,
            "role": "executor",
            "inputs": [str(package.package_path)],
            "outputs": [str(output_dir / "gate-decision-bundle.md"), str(output_dir / "gate-decision-bundle.json")],
            "commands_run": [
                f"python scripts/gate_human_orchestrator.py executor-run --input {input_path}",
                "ll gate evaluate",
                "ll gate dispatch",
            ],
            "structural_results": {
                "input_validation": "pass",
                "decision_ref_present": True,
                "decision_target_present": bool(bundle_json["decision_target"]),
                "decision_basis_refs_present": bool(bundle_json["decision_basis_refs"]),
                "dispatch_receipt_present": True,
                "approve_materialized": bundle_json["decision"] != "approve" or bool(bundle_json["materialized_handoff_ref"]),
                "human_projection_present": bool(bundle_json["human_projection_ref"]),
                "projection_review_visible": bundle_json["projection_status"] == "review_visible",
                "projection_markers_valid": all(
                    bundle_json["projection_markers"].get(key) is True
                    for key in ("derived_only", "non_authoritative", "non_inheritable")
                ),
            },
        },
    )
    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": effective_run_id,
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "primary_artifact_ref": str(output_dir / "gate-decision-bundle.md"),
            "bundle_ref": str(output_dir / "gate-decision-bundle.json"),
            "runtime_refs_ref": str(output_dir / "runtime-artifact-refs.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
            "status": "drafted",
        },
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "decision_ref": bundle_json["decision_ref"],
        "decision": bundle_json["decision"],
        "bundle_ref": str(output_dir / "gate-decision-bundle.json"),
        "human_projection_ref": bundle_json["human_projection_ref"],
    }


def _semantic_findings(bundle: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not bundle.get("decision_target"):
        findings.append({"title": "Missing decision target", "detail": "decision_target must be explicit."})
    if not bundle.get("decision_basis_refs"):
        findings.append({"title": "Missing basis refs", "detail": "decision_basis_refs must not be empty."})
    if bundle.get("decision") == "approve" and not bundle.get("materialized_handoff_ref"):
        findings.append({"title": "Approve without materialization", "detail": "approve must produce materialization evidence."})
    if bundle.get("decision") != "approve" and bundle.get("materialized_handoff_ref"):
        findings.append({"title": "Unexpected materialization", "detail": "non-approve decision should not carry formal handoff success."})
    return findings + human_projection_findings(bundle)


def build_supervision_evidence(artifacts_dir: Path) -> dict[str, Any]:
    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    findings = _semantic_findings(bundle)
    return {
        "skill_id": "ll-gate-human-orchestrator",
        "run_id": bundle["workflow_run_id"],
        "role": "supervisor",
        "reviewed_inputs": [str(artifacts_dir / "gate-decision-bundle.md"), str(artifacts_dir / "gate-decision-bundle.json")],
        "reviewed_outputs": [str(artifacts_dir / "runtime-artifact-refs.json")],
        "semantic_findings": findings or [{"title": "Gate package accepted", "detail": "The gate decision package is semantically coherent."}],
        "decision": "pass" if not findings else "revise",
    }


def update_supervisor_outputs(artifacts_dir: Path, supervision: dict[str, Any]) -> None:
    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    bundle["status"] = "accepted" if supervision["decision"] == "pass" else "revised"
    write_bundle_files(artifacts_dir, bundle)
    defects = [] if supervision["decision"] == "pass" else supervision["semantic_findings"]
    dump_json(artifacts_dir / "gate-defect-list.json", defects)
    dump_json(
        artifacts_dir / "gate-acceptance-report.json",
        {
            "decision": "approve" if supervision["decision"] == "pass" else "revise",
            "summary": "gate decision package passed supervisor review" if supervision["decision"] == "pass" else "gate decision package requires revision",
        },
    )
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(
        artifacts_dir / "gate-freeze-gate.json",
        {
            "workflow_key": "governance.gate-human-orchestrator",
            "decision": "pass" if supervision["decision"] == "pass" else "revise",
            "freeze_ready": supervision["decision"] == "pass",
        },
    )
    manifest = load_json(artifacts_dir / "package-manifest.json")
    manifest["status"] = bundle["status"]
    dump_json(artifacts_dir / "package-manifest.json", manifest)


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    required = [
        "package-manifest.json",
        "gate-decision-bundle.md",
        "gate-decision-bundle.json",
        "runtime-artifact-refs.json",
        "gate-review-report.json",
        "gate-acceptance-report.json",
        "gate-defect-list.json",
        "gate-freeze-gate.json",
        "handoff-to-gate-downstreams.json",
        "execution-evidence.json",
        "supervision-evidence.json",
    ]
    for name in required:
        if not (artifacts_dir / name).exists():
            errors.append(f"missing output artifact: {name}")
    bundle = load_json(artifacts_dir / "gate-decision-bundle.json") if (artifacts_dir / "gate-decision-bundle.json").exists() else {}
    for field in (
        "decision_ref",
        "decision",
        "decision_target",
        "decision_basis_refs",
        "dispatch_target",
        "machine_ssot_ref",
        "human_projection_ref",
        "projection_status",
    ):
        if not bundle.get(field):
            errors.append(f"missing bundle field: {field}")
    if bundle.get("decision") == "approve" and not bundle.get("materialized_handoff_ref"):
        errors.append("approve requires materialized_handoff_ref")
    if bundle.get("projection_status") != "review_visible":
        errors.append("human projection must be review_visible")
    if not bundle.get("snapshot_ref"):
        errors.append("missing bundle field: snapshot_ref")
    if not bundle.get("focus_ref"):
        errors.append("missing bundle field: focus_ref")
    for key in ("derived_only", "non_authoritative", "non_inheritable"):
        if bundle.get("projection_markers", {}).get(key) is not True:
            errors.append(f"projection marker must be true: {key}")
    return errors, {
        "artifacts_dir": str(artifacts_dir),
        "decision": bundle.get("decision", ""),
        "dispatch_target": bundle.get("dispatch_target", ""),
        "projection_status": bundle.get("projection_status", ""),
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if not (artifacts_dir / "gate-freeze-gate.json").exists():
        errors.append("missing gate-freeze-gate.json")
        return False, errors
    gate = load_json(artifacts_dir / "gate-freeze-gate.json")
    if gate.get("freeze_ready") is not True:
        errors.append("freeze gate is not ready")
    return not errors, errors


def collect_evidence_report(artifacts_dir: Path) -> Path:
    return write_evidence_report(artifacts_dir)


def projection_comment(
    artifacts_dir: Path,
    repo_root: Path,
    comment_ref: str,
    comment_text: str,
    comment_author: str,
    target_block: str = "",
) -> dict[str, Any]:
    return capture_projection_comment(artifacts_dir, repo_root, comment_ref, comment_text, comment_author, target_block)


def regenerate_projection(
    artifacts_dir: Path,
    repo_root: Path,
    updated_ssot_ref: str,
    revision_request_ref: str = "",
) -> dict[str, Any]:
    return regenerate_projection_bundle(artifacts_dir, repo_root, updated_ssot_ref, revision_request_ref)


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del repo_root, run_id, allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")
    supervision = build_supervision_evidence(artifacts_dir)
    update_supervisor_outputs(artifacts_dir, supervision)
    return {
        "ok": True,
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "freeze_ready": supervision["decision"] == "pass",
    }


def run_workflow(
    input_path: Path,
    repo_root: Path,
    run_id: str,
    decision: str = "",
    decision_reason: str = "",
    decision_target: str = "",
    audit_finding_refs: list[str] | None = None,
    allow_update: bool = False,
) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        repo_root=repo_root,
        run_id=run_id,
        decision=decision,
        decision_reason=decision_reason,
        decision_target=decision_target,
        audit_finding_refs=audit_finding_refs,
        allow_update=allow_update,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(artifacts_dir, repo_root, run_id or executor_result["run_id"], allow_update=True)
    output_errors, output_result = validate_output_package(artifacts_dir)
    if output_errors:
        raise ValueError("; ".join(output_errors))
    readiness_ok, readiness_errors = validate_package_readiness(artifacts_dir)
    report_path = collect_evidence_report(artifacts_dir)
    return {
        "ok": readiness_ok,
        "run_id": executor_result["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "decision": executor_result["decision"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }
