#!/usr/bin/env python3
"""
CLI-backed materialization helpers for epic-to-feat.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from epic_to_feat_common import dump_json, load_json, parse_markdown_frontmatter, render_markdown


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _commit_markdown(repo_root: Path, artifacts_dir: Path, run_id: str, markdown_text: str, request_suffix: str) -> dict[str, Any]:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.ll import main as cli_main

    staging_path = repo_root / ".workflow" / "runs" / run_id / "generated" / "epic-to-feat" / f"{request_suffix}.md"
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path.write_text(markdown_text, encoding="utf-8")

    request_path = artifacts_dir / "_cli" / f"{request_suffix}.request.json"
    response_path = artifacts_dir / "_cli" / f"{request_suffix}.response.json"
    payload = {
        "api_version": "v1",
        "command": "artifact.commit",
        "request_id": f"req-epic-to-feat-{run_id}-{request_suffix}",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-product-epic-to-feat",
        "trace": {"run_ref": run_id, "workflow_key": "product.epic-to-feat"},
        "payload": {
            "artifact_ref": f"epic-to-feat.{run_id}.feat-freeze-bundle",
            "workspace_path": f"artifacts/epic-to-feat/{run_id}/feat-freeze-bundle.md",
            "requested_mode": "commit",
            "content_ref": staging_path.relative_to(repo_root).as_posix(),
        },
    }
    _write_json(request_path, payload)
    exit_code = cli_main(["artifact", "commit", "--request", str(request_path), "--response-out", str(response_path)])
    response = load_json(response_path)
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"epic-to-feat bundle commit failed: {response.get('status_code')} {response.get('message')}")
    return {"request_path": request_path, "response_path": response_path, "response": response}


def write_executor_outputs(output_dir: Path, repo_root: Path, package: Any, generated: Any, command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = output_dir.name
    revision_context = generated.json_payload.get("revision_context") if isinstance(generated.json_payload.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or "").strip()
    markdown_text = render_markdown(generated.frontmatter, generated.markdown_body)
    cli_commit = _commit_markdown(repo_root, output_dir, run_id, markdown_text, "feat-freeze-executor-commit")
    dump_json(output_dir / "feat-freeze-bundle.json", generated.json_payload)
    dump_json(output_dir / "feat-review-report.json", generated.review_report)
    dump_json(output_dir / "feat-acceptance-report.json", generated.acceptance_report)
    dump_json(output_dir / "feat-defect-list.json", generated.defect_list)
    dump_json(output_dir / "handoff-to-feat-downstreams.json", generated.handoff)
    dump_json(output_dir / "semantic-drift-check.json", generated.semantic_drift_check)
    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": package.run_id,
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "primary_artifact_ref": str(output_dir / "feat-freeze-bundle.md"),
            "result_summary_ref": str(output_dir / "feat-freeze-gate.json"),
            "review_report_ref": str(output_dir / "feat-review-report.json"),
            "acceptance_report_ref": str(output_dir / "feat-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "feat-defect-list.json"),
            "handoff_ref": str(output_dir / "handoff-to-feat-downstreams.json"),
            "semantic_drift_check_ref": str(output_dir / "semantic-drift-check.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
            "status": generated.json_payload["status"],
            "cli_executor_commit_ref": str(cli_commit["response_path"]),
            **({"revision_request_ref": revision_request_ref} if revision_request_ref else {}),
        },
    )
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-product-epic-to-feat",
            "run_id": package.run_id,
            "role": "executor",
            "input_path": str(package.artifacts_dir),
            "inputs": [str(package.artifacts_dir)],
            "outputs": [str(output_dir / "feat-freeze-bundle.md"), str(output_dir / "feat-freeze-bundle.json")],
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "draft_output_files": [
                    "feat-freeze-bundle.md",
                    "feat-freeze-bundle.json",
                    "feat-review-report.json",
                    "feat-acceptance-report.json",
                    "feat-defect-list.json",
                    "handoff-to-feat-downstreams.json",
                    "semantic-drift-check.json",
                ],
                "cli_executor_commit_ref": str(cli_commit["response_path"]),
                "cli_executor_receipt_ref": cli_commit["response"]["data"].get("receipt_ref", ""),
                "cli_executor_registry_record_ref": cli_commit["response"]["data"].get("registry_record_ref", ""),
            },
            "key_decisions": [
                f"Preserved epic_freeze_ref as {generated.frontmatter['epic_freeze_ref']}.",
                f"Preserved src_root_id as {generated.frontmatter['src_root_id']}.",
                f"Generated {len(generated.frontmatter['feat_refs'])} FEAT refs for downstream governed TECH and TESTSET workflows.",
            ],
            "uncertainties": [],
            **({"revision_request_ref": revision_request_ref} if revision_request_ref else {}),
        },
    )


def build_supervision_evidence(artifacts_dir: Path, generated: Any) -> dict[str, Any]:
    decision = "pass" if not generated.defect_list else "revise"
    revision_context = generated.json_payload.get("revision_context") if isinstance(generated.json_payload.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or "").strip()
    revision_summary = str(revision_context.get("summary") or "").strip()
    findings = [
        {
            "title": "FEAT boundary preserved" if decision == "pass" else "FEAT boundary needs revision",
            "detail": "The generated FEAT bundle remains suitable for downstream derivation." if decision == "pass" else "The generated FEAT bundle requires revision before freeze.",
        }
    ]
    findings.extend({"title": defect["title"], "detail": defect["detail"]} for defect in generated.defect_list)
    if revision_summary:
        findings.append({"title": "Revision context absorbed", "detail": revision_summary})
    return {
        "skill_id": "ll-product-epic-to-feat",
        "run_id": generated.frontmatter["workflow_run_id"],
        "role": "supervisor",
        "reviewed_inputs": [str(artifacts_dir / "feat-freeze-bundle.md"), str(artifacts_dir / "feat-freeze-bundle.json")],
        "reviewed_outputs": [str(artifacts_dir / "feat-freeze-bundle.md"), str(artifacts_dir / "feat-freeze-bundle.json")],
        "semantic_findings": findings,
        "decision": decision,
        "reason": (
            "FEAT bundle passed semantic review."
            if decision == "pass"
            else "FEAT bundle needs revision before freeze."
        )
        + (f" Revision context: {revision_summary}" if revision_summary else ""),
        "created_at": generated.acceptance_report["created_at"],
        **({"revision_request_ref": revision_request_ref} if revision_request_ref else {}),
    }


def build_gate_result(generated: Any, supervision_evidence: dict[str, Any]) -> dict[str, Any]:
    pass_gate = supervision_evidence["decision"] == "pass" and not generated.defect_list
    revision_context = generated.json_payload.get("revision_context") if isinstance(generated.json_payload.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or supervision_evidence.get("revision_request_ref") or "").strip()
    return {
        "workflow_key": "product.epic-to-feat",
        "decision": "pass" if pass_gate else "revise",
        "freeze_ready": pass_gate,
        "epic_freeze_ref": generated.frontmatter["epic_freeze_ref"],
        "src_root_id": generated.frontmatter["src_root_id"],
        "feat_refs": generated.frontmatter["feat_refs"],
        **({"revision_request_ref": revision_request_ref} if revision_request_ref else {}),
        "checks": {
            "execution_evidence_present": True,
            "supervision_evidence_present": True,
            "feat_refs_present": bool(generated.frontmatter["feat_refs"]),
            "downstream_handoff_present": True,
            "structured_acceptance_checks_complete": not generated.defect_list,
            "feat_count_valid": len(generated.frontmatter["feat_refs"]) >= 2,
            "semantic_lock_preserved": generated.semantic_drift_check.get("semantic_lock_preserved", True),
            **({"revision_request_present": True} if revision_request_ref else {}),
        },
        "created_at": generated.acceptance_report["created_at"],
    }


def update_supervisor_outputs(artifacts_dir: Path, repo_root: Path, generated: Any, supervision: dict[str, Any], gate: dict[str, Any]) -> None:
    run_id = artifacts_dir.name
    bundle_json = load_json(artifacts_dir / "feat-freeze-bundle.json")
    updated_json = dict(bundle_json)
    updated_json["status"] = "accepted" if supervision["decision"] == "pass" else "revised"
    revision_context = updated_json.get("revision_context") if isinstance(updated_json.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or gate.get("revision_request_ref") or supervision.get("revision_request_ref") or "").strip()
    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    frontmatter["status"] = updated_json["status"]
    cli_commit = _commit_markdown(repo_root, artifacts_dir, run_id, render_markdown(frontmatter, body), "feat-freeze-supervisor-commit")
    dump_json(artifacts_dir / "feat-freeze-bundle.json", updated_json)
    dump_json(artifacts_dir / "feat-review-report.json", generated.review_report)
    dump_json(artifacts_dir / "feat-acceptance-report.json", generated.acceptance_report)
    dump_json(artifacts_dir / "feat-defect-list.json", generated.defect_list)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "feat-freeze-gate.json", gate)
    manifest = load_json(artifacts_dir / "package-manifest.json")
    manifest["cli_supervisor_commit_ref"] = str(cli_commit["response_path"])
    if revision_request_ref:
        manifest["revision_request_ref"] = revision_request_ref
    dump_json(artifacts_dir / "package-manifest.json", manifest)


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    revision_request_ref = str(execution.get("revision_request_ref") or supervision.get("revision_request_ref") or gate.get("revision_request_ref") or "").strip()
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-product-epic-to-feat Review Report",
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
