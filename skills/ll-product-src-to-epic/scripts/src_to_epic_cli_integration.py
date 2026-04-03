#!/usr/bin/env python3
"""
CLI-backed materialization helpers for src-to-epic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from src_to_epic_common import dump_json, load_json, parse_markdown_frontmatter, render_markdown
from src_to_epic_review_phase1 import build_src_to_epic_document_test_report, validate_review_phase1_fields


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _commit_markdown(repo_root: Path, artifacts_dir: Path, run_id: str, markdown_text: str, request_suffix: str) -> dict[str, Any]:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.ll import main as cli_main

    staging_path = repo_root / ".workflow" / "runs" / run_id / "generated" / "src-to-epic" / f"{request_suffix}.md"
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path.write_text(markdown_text, encoding="utf-8")

    request_path = artifacts_dir / "_cli" / f"{request_suffix}.request.json"
    response_path = artifacts_dir / "_cli" / f"{request_suffix}.response.json"
    payload = {
        "api_version": "v1",
        "command": "artifact.commit",
        "request_id": f"req-src-to-epic-{run_id}-{request_suffix}",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-product-src-to-epic",
        "trace": {"run_ref": run_id, "workflow_key": "product.src-to-epic"},
        "payload": {
            "artifact_ref": f"src-to-epic.{run_id}.epic-freeze",
            "workspace_path": f"artifacts/src-to-epic/{run_id}/epic-freeze.md",
            "requested_mode": "commit",
            "content_ref": staging_path.relative_to(repo_root).as_posix(),
        },
    }
    _write_json(request_path, payload)
    exit_code = cli_main(["artifact", "commit", "--request", str(request_path), "--response-out", str(response_path)])
    response = load_json(response_path)
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"src-to-epic epic commit failed: {response.get('status_code')} {response.get('message')}")
    return {"request_path": request_path, "response_path": response_path, "response": response}


def write_executor_outputs(output_dir: Path, repo_root: Path, package: Any, generated: Any, command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = output_dir.name
    revision_request_ref = str(generated.json_payload.get("revision_request_ref") or "").strip()
    document_test_report = build_src_to_epic_document_test_report(generated)
    markdown_text = render_markdown(generated.frontmatter, generated.markdown_body)
    cli_commit = _commit_markdown(repo_root, output_dir, run_id, markdown_text, "epic-freeze-executor-commit")
    dump_json(output_dir / "epic-freeze.json", generated.json_payload)
    dump_json(output_dir / "epic-review-report.json", generated.review_report)
    dump_json(output_dir / "epic-acceptance-report.json", generated.acceptance_report)
    dump_json(output_dir / "epic-defect-list.json", generated.defect_list)
    dump_json(output_dir / "document-test-report.json", document_test_report)
    dump_json(output_dir / "handoff-to-epic-to-feat.json", generated.handoff)
    dump_json(output_dir / "semantic-drift-check.json", generated.semantic_drift_check)
    dump_json(
        output_dir / "package-manifest.json",
        {
            "artifacts_dir": str(output_dir),
            "primary_artifact_ref": str(output_dir / "epic-freeze.md"),
            "result_summary_ref": str(output_dir / "epic-freeze-gate.json"),
            "review_report_ref": str(output_dir / "epic-review-report.json"),
            "acceptance_report_ref": str(output_dir / "epic-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "epic-defect-list.json"),
            "document_test_report_ref": str(output_dir / "document-test-report.json"),
            "handoff_ref": str(output_dir / "handoff-to-epic-to-feat.json"),
            "semantic_drift_check_ref": str(output_dir / "semantic-drift-check.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
            "status": generated.json_payload["status"],
            "cli_executor_commit_ref": str(cli_commit["response_path"]),
        },
    )
    if revision_request_ref:
        package_manifest = load_json(output_dir / "package-manifest.json")
        package_manifest["revision_request_ref"] = revision_request_ref
        dump_json(output_dir / "package-manifest.json", package_manifest)
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-product-src-to-epic",
            "run_id": package.run_id,
            "role": "executor",
            "inputs": [str(package.artifacts_dir)],
            "outputs": [str(output_dir / "epic-freeze.md"), str(output_dir / "epic-freeze.json")],
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "draft_output_files": [
                    "epic-freeze.md",
                    "epic-freeze.json",
                    "epic-review-report.json",
                    "epic-acceptance-report.json",
                    "epic-defect-list.json",
                    "document-test-report.json",
                    "handoff-to-epic-to-feat.json",
                    "semantic-drift-check.json",
                ],
                "cli_executor_commit_ref": str(cli_commit["response_path"]),
                "cli_executor_receipt_ref": cli_commit["response"]["data"].get("receipt_ref", ""),
                "cli_executor_registry_record_ref": cli_commit["response"]["data"].get("registry_record_ref", ""),
            },
            "key_decisions": [
                f"Preserved src_root_id as {generated.frontmatter['src_root_id']}.",
                f"Bound downstream handoff to {generated.frontmatter['downstream_workflow']}.",
                "Kept the artifact at EPIC layer and deferred FEAT decomposition to the next workflow.",
                "When rollout is required, encoded adoption/E2E decomposition requirements inside the primary EPIC instead of emitting a second EPIC.",
            ],
            "uncertainties": [],
        },
    )
    if revision_request_ref:
        execution_evidence = load_json(output_dir / "execution-evidence.json")
        execution_evidence["revision_request_ref"] = revision_request_ref
        dump_json(output_dir / "execution-evidence.json", execution_evidence)


def build_supervision_evidence(package: Any, output_dir: Path, generated: Any) -> dict[str, Any]:
    decision = "pass" if not generated.defect_list else "revise"
    revision_request_ref = str(generated.json_payload.get("revision_request_ref") or "").strip()
    document_test_report = build_src_to_epic_document_test_report(generated)
    findings = [
        {
            "title": "Multi-FEAT boundary preserved" if decision == "pass" else "Multi-FEAT boundary weak",
            "detail": "The EPIC remains a downstream decomposition boundary." if decision == "pass" else "The current EPIC may need demotion or additional scope clarification.",
        }
    ]
    findings.extend({"title": defect["title"], "detail": defect["detail"]} for defect in generated.defect_list)
    result = {
        "skill_id": "ll-product-src-to-epic",
        "run_id": package.run_id,
        "role": "supervisor",
        "reviewed_inputs": [str(package.artifacts_dir)],
        "reviewed_outputs": [str(output_dir / "epic-freeze.md"), str(output_dir / "epic-freeze.json")],
        "semantic_findings": findings,
        "decision": decision,
        "reason": "EPIC package passed semantic review." if decision == "pass" else "EPIC package needs revision before freeze.",
        "created_at": generated.acceptance_report["created_at"],
        "document_test_report_ref": str(output_dir / "document-test-report.json"),
        "document_test_outcome": document_test_report["test_outcome"],
    }
    if revision_request_ref:
        result["revision_request_ref"] = revision_request_ref
    return result


def build_gate_result(generated: Any, supervision_evidence: dict[str, Any]) -> dict[str, Any]:
    document_test_report = build_src_to_epic_document_test_report(generated)
    review_phase1_ready = not validate_review_phase1_fields(document_test_report)
    document_test_non_blocking = document_test_report["test_outcome"] == "no_blocking_defect_found"
    pass_gate = supervision_evidence["decision"] == "pass" and not generated.defect_list and document_test_non_blocking and review_phase1_ready
    return {
        "workflow_key": "product.src-to-epic",
        "decision": "pass" if pass_gate else "revise",
        "freeze_ready": pass_gate,
        "epic_freeze_ref": generated.frontmatter["epic_freeze_ref"],
        "src_root_id": generated.frontmatter["src_root_id"],
        **({"revision_request_ref": str(generated.json_payload.get("revision_request_ref") or "").strip()} if str(generated.json_payload.get("revision_request_ref") or "").strip() else {}),
        "checks": {
            "execution_evidence_present": True,
            "supervision_evidence_present": True,
            "epic_freeze_ref_presence": True,
            "downstream_handoff_presence": True,
            "adr025_acceptance_complete": generated.acceptance_report["decision"] == "approve",
            "multi_feat_boundary_preserved": not generated.defect_list,
            "rollout_plan_present_when_required": (not generated.json_payload["rollout_requirement"]["required"]) or bool(generated.json_payload.get("rollout_plan", {}).get("required_feat_families")),
            "semantic_lock_preserved": generated.semantic_drift_check.get("semantic_lock_preserved", True),
            "document_test_report_present": document_test_report["test_outcome"] in {"no_blocking_defect_found", "blocking_defect_found", "inconclusive", "not_applicable"},
            "document_test_non_blocking": document_test_non_blocking,
            "review_phase1_ready": review_phase1_ready,
        },
        "created_at": generated.acceptance_report["created_at"],
    }


def update_supervisor_outputs(artifacts_dir: Path, repo_root: Path, package: Any, generated: Any, supervision: dict[str, Any], gate: dict[str, Any]) -> None:
    run_id = artifacts_dir.name
    document_test_report = build_src_to_epic_document_test_report(generated)
    epic_json = load_json(artifacts_dir / "epic-freeze.json")
    updated_json = dict(epic_json)
    updated_json["status"] = "accepted" if supervision["decision"] == "pass" else "revised"
    revision_request_ref = str(generated.json_payload.get("revision_request_ref") or "").strip()
    if revision_request_ref:
        updated_json["revision_request_ref"] = revision_request_ref
    markdown_text = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    frontmatter["status"] = updated_json["status"]
    if revision_request_ref:
        frontmatter["revision_request_ref"] = revision_request_ref
    cli_commit = _commit_markdown(repo_root, artifacts_dir, run_id, render_markdown(frontmatter, body), "epic-freeze-supervisor-commit")
    dump_json(artifacts_dir / "epic-freeze.json", updated_json)
    dump_json(artifacts_dir / "epic-review-report.json", generated.review_report)
    dump_json(artifacts_dir / "epic-acceptance-report.json", generated.acceptance_report)
    dump_json(artifacts_dir / "epic-defect-list.json", generated.defect_list)
    dump_json(artifacts_dir / "document-test-report.json", document_test_report)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "epic-freeze-gate.json", gate)
    manifest = load_json(artifacts_dir / "package-manifest.json")
    manifest["cli_supervisor_commit_ref"] = str(cli_commit["response_path"])
    manifest["document_test_report_ref"] = str(artifacts_dir / "document-test-report.json")
    if revision_request_ref:
        manifest["revision_request_ref"] = revision_request_ref
    dump_json(artifacts_dir / "package-manifest.json", manifest)


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "epic-freeze-gate.json")
    document_test = load_json(artifacts_dir / "document-test-report.json")
    report_path = artifacts_dir / "evidence-report.md"
    revision_request_ref = str(execution.get("revision_request_ref") or supervision.get("revision_request_ref") or gate.get("revision_request_ref") or "").strip()
    report_path.write_text(
        "\n".join(
            [
                "# ll-product-src-to-epic Review Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- output_dir: {artifacts_dir}",
                *([f"- revision_request_ref: {revision_request_ref}"] if revision_request_ref else []),
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
                "## Document Test",
                "",
                f"- test_outcome: {document_test.get('test_outcome')}",
                f"- recommended_next_action: {document_test.get('recommended_next_action')}",
                f"- recommended_actor: {document_test.get('recommended_actor')}",
                "",
                "## Freeze Gate",
                "",
                f"- decision: {gate.get('decision')}",
                f"- freeze_ready: {gate.get('freeze_ready')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path
