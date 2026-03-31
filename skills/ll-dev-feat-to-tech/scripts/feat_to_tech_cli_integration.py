#!/usr/bin/env python3
"""
Materialization helpers for feat-to-tech.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section
from feat_to_tech_common import dump_json, load_json, parse_markdown_frontmatter, render_markdown


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _commit_markdown(repo_root: Path, artifacts_dir: Path, run_id: str, markdown_text: str, request_suffix: str) -> dict[str, Any]:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.ll import main as cli_main

    staging_path = repo_root / ".workflow" / "runs" / run_id / "generated" / "feat-to-tech" / f"{request_suffix}.md"
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path.write_text(markdown_text, encoding="utf-8")

    request_path = artifacts_dir / "_cli" / f"{request_suffix}.request.json"
    response_path = artifacts_dir / "_cli" / f"{request_suffix}.response.json"
    payload = {
        "api_version": "v1",
        "command": "artifact.commit",
        "request_id": f"req-feat-to-tech-{run_id}-{request_suffix}",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-dev-feat-to-tech",
        "trace": {"run_ref": run_id, "workflow_key": "dev.feat-to-tech"},
        "payload": {
            "artifact_ref": f"feat-to-tech.{run_id}.tech-design-bundle",
            "workspace_path": f"artifacts/feat-to-tech/{run_id}/tech-design-bundle.md",
            "requested_mode": "commit",
            "content_ref": staging_path.relative_to(repo_root).as_posix(),
        },
    }
    _write_json(request_path, payload)
    exit_code = cli_main(["artifact", "commit", "--request", str(request_path), "--response-out", str(response_path)])
    response = load_json(response_path)
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"feat-to-tech bundle commit failed: {response.get('status_code')} {response.get('message')}")
    return {"request_path": request_path, "response_path": response_path, "response": response}


def write_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(frontmatter, body), encoding="utf-8")


def _document_test_report(generated: Any) -> dict[str, Any]:
    defects = list(generated.defect_list)
    revision_context = generated.json_payload.get("revision_context") or {}
    issues = [str(item.get("title") or "").strip() for item in defects if str(item.get("title") or "").strip()]
    missing_contracts = [name for name, required in {"arch_design": generated.json_payload["arch_required"], "api_contract": generated.json_payload["api_required"]}.items() if required and not generated.json_payload["artifact_refs"].get("arch_spec" if name == "arch_design" else "api_spec")]
    fixability = build_fixability_section(
        recommended_next_action="workflow_rebuild" if defects else "submit_to_external_gate",
        recommended_actor="workflow_rebuild" if defects else "external_gate_review",
        rebuild_required=len(defects),
    )
    return build_document_test_report(
        workflow_key="dev.feat-to-tech",
        run_id=generated.run_id,
        tested_at=str(generated.acceptance_report["created_at"]),
        defect_list=defects,
        revision_request_ref=str(revision_context.get("revision_request_ref") or ""),
        structural={"package_integrity": True, "traceability_integrity": bool(generated.json_payload.get("source_refs")), "blocking": False},
        logic_consistency={"checked_topics": ["design_focus", "consistency", "artifact_projection", "downstream_handoff"], "conflicts_found": issues, "severity": "blocking" if defects else "none", "blocking": bool(defects)},
        downstream_readiness={
            "downstream_target": "dev.tech-to-impl",
            "consumption_contract_ref": "skills/ll-dev-feat-to-tech/ll.contract.yaml#validation.document_test.downstream_consumption_contract",
            "ready_for_gate_review": not defects,
            "blocking_gaps": issues,
            "missing_contracts": missing_contracts,
            "assumption_leaks": [str(item) for item in generated.json_payload["design_consistency_check"].get("minor_open_items") or [] if str(item).strip()],
        },
        semantic_drift={
            "revision_context_present": bool(revision_context),
            "drift_detected": generated.semantic_drift_check.get("verdict") != "pass",
            "drift_items": list(generated.semantic_drift_check.get("axis_conflicts") or []) + list(generated.semantic_drift_check.get("carrier_topic_issues") or []),
            "semantic_lock_preserved": generated.semantic_drift_check.get("semantic_lock_preserved", True),
        },
        fixability=fixability,
    )


def write_executor_outputs(output_dir: Path, repo_root: Path, package: Any, generated: Any, command_name: str) -> None:
    revision_context = generated.json_payload.get("revision_context") or {}
    document_test_report = _document_test_report(generated)
    output_dir.mkdir(parents=True, exist_ok=True)
    arch_path = output_dir / "arch-design.md"
    api_path = output_dir / "api-contract.md"
    run_id = output_dir.name
    markdown_text = render_markdown(generated.frontmatter, generated.markdown_body)
    cli_commit = _commit_markdown(repo_root, output_dir, run_id, markdown_text, "tech-design-bundle-executor-commit")
    write_markdown(output_dir / "tech-spec.md", generated.tech_frontmatter, generated.tech_body)
    if generated.arch_frontmatter:
        write_markdown(arch_path, generated.arch_frontmatter, generated.arch_body)
    elif arch_path.exists():
        arch_path.unlink()
    if generated.api_frontmatter:
        write_markdown(api_path, generated.api_frontmatter, generated.api_body)
    elif api_path.exists():
        api_path.unlink()

    dump_json(output_dir / "tech-design-bundle.json", generated.json_payload)
    dump_json(output_dir / "tech-review-report.json", generated.review_report)
    dump_json(output_dir / "tech-acceptance-report.json", generated.acceptance_report)
    dump_json(output_dir / "tech-defect-list.json", generated.defect_list)
    dump_json(output_dir / "document-test-report.json", document_test_report)
    dump_json(output_dir / "handoff-to-tech-impl.json", generated.handoff)
    dump_json(output_dir / "semantic-drift-check.json", generated.semantic_drift_check)
    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": generated.run_id,
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "feat_ref": generated.json_payload["feat_ref"],
            "primary_artifact_ref": str(output_dir / "tech-design-bundle.md"),
            "tech_spec_ref": str(output_dir / "tech-spec.md"),
            "result_summary_ref": str(output_dir / "tech-freeze-gate.json"),
            "review_report_ref": str(output_dir / "tech-review-report.json"),
            "acceptance_report_ref": str(output_dir / "tech-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "tech-defect-list.json"),
            "document_test_report_ref": str(output_dir / "document-test-report.json"),
            "handoff_ref": str(output_dir / "handoff-to-tech-impl.json"),
            "semantic_drift_check_ref": str(output_dir / "semantic-drift-check.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
            "status": generated.json_payload["status"],
            "cli_executor_commit_ref": str(cli_commit["response_path"]),
            **(
                {
                    "revision_request_ref": revision_context.get("revision_request_ref", ""),
                    "revision_summary": revision_context.get("summary", ""),
                }
                if revision_context
                else {}
            ),
        },
    )
    outputs = [
        str(output_dir / "tech-design-bundle.md"),
        str(output_dir / "tech-design-bundle.json"),
        str(output_dir / "tech-spec.md"),
    ]
    if generated.arch_frontmatter:
        outputs.append(str(output_dir / "arch-design.md"))
    if generated.api_frontmatter:
        outputs.append(str(output_dir / "api-contract.md"))
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-dev-feat-to-tech",
            "run_id": generated.run_id,
            "role": "executor",
            "inputs": [str(package.artifacts_dir), generated.json_payload["feat_ref"]],
            "outputs": outputs,
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "semantic_lock_present": bool(generated.json_payload.get("semantic_lock")),
                "semantic_lock_preserved": generated.semantic_drift_check.get("semantic_lock_preserved", True),
                "tech_present": True,
                "arch_required": generated.json_payload["arch_required"],
                "api_required": generated.json_payload["api_required"],
                "design_consistency_passed": generated.json_payload["design_consistency_check"]["passed"],
                "cli_executor_commit_ref": str(cli_commit["response_path"]),
                "cli_executor_receipt_ref": cli_commit["response"]["data"].get("receipt_ref", ""),
                "cli_executor_registry_record_ref": cli_commit["response"]["data"].get("registry_record_ref", ""),
                "document_test_outcome": document_test_report["test_outcome"],
            },
            "key_decisions": generated.execution_decisions,
            "uncertainties": generated.execution_uncertainties,
            **({"revision_context": revision_context} if revision_context else {}),
        },
    )


def build_supervision_evidence(artifacts_dir: Path, generated: Any) -> dict[str, Any]:
    decision = "pass" if not generated.defect_list else "revise"
    revision_context = generated.json_payload.get("revision_context") or {}
    document_test_report = _document_test_report(generated)
    findings = [
        {
            "title": "TECH package aligned to selected FEAT" if decision == "pass" else "TECH package requires revision",
            "detail": "The package remains suitable for downstream IMPL task planning." if decision == "pass" else "The package needs revision before freeze.",
        }
    ]
    findings.extend({"title": defect["title"], "detail": defect["detail"]} for defect in generated.defect_list)
    return {
        "skill_id": "ll-dev-feat-to-tech",
        "run_id": generated.run_id,
        "role": "supervisor",
        "reviewed_inputs": [str(artifacts_dir / "tech-design-bundle.md"), str(artifacts_dir / "tech-design-bundle.json")],
        "reviewed_outputs": [str(artifacts_dir / "tech-spec.md")],
        "semantic_findings": findings,
        "decision": decision,
        "reason": "TECH package passed semantic review." if decision == "pass" else "TECH package needs revision before freeze.",
        "document_test_report_ref": str(artifacts_dir / "document-test-report.json"),
        "document_test_outcome": document_test_report["test_outcome"],
        **({"revision_context": revision_context} if revision_context else {}),
    }


def build_gate_result(generated: Any, supervision_evidence: dict[str, Any]) -> dict[str, Any]:
    consistency = generated.json_payload["design_consistency_check"]
    revision_context = generated.json_payload.get("revision_context") or {}
    document_test_report = _document_test_report(generated)
    document_test_non_blocking = document_test_report["test_outcome"] == "no_blocking_defect_found"
    checks = {
        "execution_evidence_present": True,
        "supervision_evidence_present": True,
        "tech_present": True,
        "optional_outputs_match_assessment": True,
        "cross_artifact_consistency_passed": consistency["passed"],
        "downstream_handoff_present": True,
        "semantic_lock_preserved": generated.semantic_drift_check.get("semantic_lock_preserved", True),
        "document_test_report_present": document_test_report["test_outcome"] in {"no_blocking_defect_found", "blocking_defect_found", "inconclusive", "not_applicable"},
        "document_test_non_blocking": document_test_non_blocking,
    }
    freeze_ready = supervision_evidence["decision"] == "pass" and all(checks.values())
    return {
        "workflow_key": "dev.feat-to-tech",
        "decision": "pass" if freeze_ready else "revise",
        "freeze_ready": freeze_ready,
        "feat_ref": generated.json_payload["feat_ref"],
        "tech_ref": generated.json_payload["tech_ref"],
        "arch_required": generated.json_payload["arch_required"],
        "api_required": generated.json_payload["api_required"],
        "checks": checks,
        **({"revision_context": revision_context} if revision_context else {}),
    }


def update_supervisor_outputs(
    artifacts_dir: Path,
    repo_root: Path,
    generated: Any,
    supervision: dict[str, Any],
    gate: dict[str, Any],
) -> None:
    bundle_json = load_json(artifacts_dir / "tech-design-bundle.json")
    document_test_report = _document_test_report(generated)
    updated_json = dict(bundle_json)
    updated_json["status"] = "accepted" if supervision["decision"] == "pass" else "revised"
    revision_context = updated_json.get("revision_context") or {}
    markdown_text = (artifacts_dir / "tech-design-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    frontmatter["status"] = updated_json["status"]
    run_id = artifacts_dir.name
    cli_commit = _commit_markdown(
        repo_root,
        artifacts_dir,
        run_id,
        render_markdown(frontmatter, body),
        "tech-design-bundle-supervisor-commit",
    )
    dump_json(artifacts_dir / "tech-design-bundle.json", updated_json)
    dump_json(artifacts_dir / "tech-review-report.json", generated.review_report)
    dump_json(artifacts_dir / "tech-acceptance-report.json", generated.acceptance_report)
    dump_json(artifacts_dir / "tech-defect-list.json", generated.defect_list)
    dump_json(artifacts_dir / "document-test-report.json", document_test_report)
    dump_json(artifacts_dir / "semantic-drift-check.json", generated.semantic_drift_check)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "tech-freeze-gate.json", gate)
    manifest = load_json(artifacts_dir / "package-manifest.json")
    manifest["status"] = updated_json["status"]
    manifest["cli_supervisor_commit_ref"] = str(cli_commit["response_path"])
    manifest["document_test_report_ref"] = str(artifacts_dir / "document-test-report.json")
    if revision_context:
        manifest["revision_request_ref"] = revision_context.get("revision_request_ref", "")
        manifest["revision_summary"] = revision_context.get("summary", "")
    dump_json(artifacts_dir / "package-manifest.json", manifest)
    for doc_name in ["tech-spec.md", "arch-design.md", "api-contract.md"]:
        doc_path = artifacts_dir / doc_name
        if not doc_path.exists():
            continue
        doc_frontmatter, doc_body = parse_markdown_frontmatter(doc_path.read_text(encoding="utf-8"))
        doc_frontmatter["status"] = updated_json["status"]
        doc_path.write_text(render_markdown(doc_frontmatter, doc_body), encoding="utf-8")


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "tech-freeze-gate.json")
    bundle = load_json(artifacts_dir / "tech-design-bundle.json")
    document_test = load_json(artifacts_dir / "document-test-report.json")
    revision_context = bundle.get("revision_context") or {}
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-dev-feat-to-tech Review Report",
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
                f"- commands: {', '.join(execution.get('commands_run', []))}",
                f"- decisions: {', '.join(execution.get('key_decisions', []))}",
                "",
                "## Supervision Evidence",
                "",
                f"- decision: {supervision.get('decision')}",
                f"- reason: {supervision.get('reason')}",
                "",
                "## Freeze Gate",
                "",
                f"- decision: {gate.get('decision')}",
                f"- freeze_ready: {gate.get('freeze_ready')}",
                "",
                "## Document Test",
                "",
                f"- test_outcome: {document_test.get('test_outcome')}",
                f"- recommended_next_action: {document_test.get('recommended_next_action')}",
                f"- recommended_actor: {document_test.get('recommended_actor')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path
