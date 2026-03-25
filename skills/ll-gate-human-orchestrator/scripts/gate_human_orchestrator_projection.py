#!/usr/bin/env python3
"""Projection helpers for ll-gate-human-orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from gate_human_orchestrator_common import dump_json, load_json, render_markdown, repo_relative, slugify


def dispatch_handoff(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_runtime_action": result["dispatch_target"],
        "decision_ref": result["decision_ref"],
        "materialized_handoff_ref": result.get("materialized_handoff_ref", ""),
        "materialized_job_ref": result.get("materialized_job_ref", ""),
    }


def projection_bundle_fields(repo_root: Path, brief_record_ref: str, machine_ssot_ref: str) -> dict[str, Any]:
    brief = load_json(_path_from_ref(repo_root, brief_record_ref))
    projection = brief.get("human_projection", {})
    if not isinstance(projection, dict):
        projection = {}
    return {
        "machine_ssot_ref": str(projection.get("ssot_ref") or machine_ssot_ref),
        "human_projection_ref": str(projection.get("projection_ref", "")),
        "projection_status": str(projection.get("status", "")),
        "projection_trace_refs": list(projection.get("trace_refs", [])),
        "projection_markers": dict(projection.get("derived_markers", {})),
        "snapshot_ref": str(projection.get("snapshot_ref", "")),
        "focus_ref": str(projection.get("focus_ref", "")),
        "human_projection": projection,
    }


def bundle_markdown(bundle: dict[str, Any]) -> str:
    refs = bundle["runtime_refs"]
    lines = [
        f"# {bundle['title']}",
        "",
        "## Input Package",
        "",
        f"- input_ref: {bundle['input_ref']}",
        f"- machine_ssot_ref: {bundle.get('machine_ssot_ref', '')}",
        "",
        "## Brief Record",
        "",
        f"- brief_record_ref: {refs['brief_record_ref']}",
        "",
        "## Human Review Projection",
        "",
        f"- human_projection_ref: {bundle.get('human_projection_ref', '')}",
        f"- projection_status: {bundle.get('projection_status', '')}",
        f"- snapshot_ref: {bundle.get('snapshot_ref', '')}",
        f"- focus_ref: {bundle.get('focus_ref', '')}",
    ]
    for block in bundle.get("human_projection", {}).get("review_blocks", []):
        lines.extend(
            [
                "",
                f"### {block.get('title', block.get('id', 'Projection Block'))}",
                "",
                f"- status: {block.get('status', '')}",
                *[f"- {item}" for item in block.get("content", [])],
            ]
        )
    lines.extend(
        [
            "",
            "## Pending Human Decision",
            "",
            f"- pending_human_decision_ref: {refs['pending_human_decision_ref']}",
            "",
            "## Decision Result",
            "",
            f"- decision_ref: {bundle['decision_ref']}",
            f"- decision: {bundle['decision']}",
            f"- decision_target: {bundle['decision_target']}",
            "",
            "## Dispatch Result",
            "",
            f"- dispatch_receipt_ref: {refs['dispatch_receipt_ref']}",
            f"- dispatch_target: {bundle['dispatch_target']}",
            "",
            "## Materialization",
            "",
            f"- materialized_handoff_ref: {bundle['materialized_handoff_ref']}",
            f"- materialized_job_ref: {bundle['materialized_job_ref']}",
            "",
            "## Traceability",
            "",
            *[f"- {item}" for item in bundle["source_refs"]],
        ]
    )
    return "\n".join(lines)


def write_bundle_files(artifacts_dir: Path, bundle: dict[str, Any]) -> None:
    frontmatter = {
        "artifact_type": bundle["artifact_type"],
        "workflow_key": bundle["workflow_key"],
        "workflow_run_id": bundle["workflow_run_id"],
        "status": bundle["status"],
        "schema_version": bundle["schema_version"],
        "decision_ref": bundle["decision_ref"],
    }
    (artifacts_dir / "gate-decision-bundle.md").write_text(
        render_markdown(frontmatter, bundle_markdown(bundle)),
        encoding="utf-8",
    )
    dump_json(artifacts_dir / "gate-decision-bundle.json", bundle)


def human_projection_findings(bundle: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not bundle.get("machine_ssot_ref"):
        findings.append({"title": "Missing Machine SSOT ref", "detail": "machine_ssot_ref must be explicit in the gate package."})
    if not bundle.get("human_projection_ref"):
        findings.append({"title": "Missing human projection ref", "detail": "gate bundle must expose the rendered projection ref."})
    if bundle.get("projection_status") != "review_visible":
        findings.append(
            {
                "title": "Projection not reviewer-ready",
                "detail": f"projection_status must be review_visible, got {bundle.get('projection_status', 'missing')}.",
            }
        )
    markers = bundle.get("projection_markers", {})
    for key in ("derived_only", "non_authoritative", "non_inheritable"):
        if markers.get(key) is not True:
            findings.append({"title": f"Missing projection marker: {key}", "detail": "projection markers must remain explicit and true."})
    if not bundle.get("snapshot_ref"):
        findings.append({"title": "Missing snapshot ref", "detail": "review bundle must expose snapshot_ref for authoritative constraints."})
    if not bundle.get("focus_ref"):
        findings.append({"title": "Missing focus ref", "detail": "review bundle must expose focus_ref for reviewer guidance."})
    return findings


def capture_projection_comment(
    artifacts_dir: Path,
    repo_root: Path,
    comment_ref: str,
    comment_text: str,
    comment_author: str,
    target_block: str = "",
) -> dict[str, Any]:
    _ensure_implementation_root()
    from cli.lib.review_projection.writeback import writeback_projection_comment

    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    projection_ref = str(bundle.get("human_projection_ref", ""))
    if not projection_ref:
        raise ValueError("gate decision bundle does not contain human_projection_ref")
    result = writeback_projection_comment(
        workspace_root=repo_root,
        projection_ref=projection_ref,
        comment_ref=comment_ref,
        comment_text=comment_text,
        comment_author=comment_author,
        target_block=target_block or None,
    )
    record_ref = artifacts_dir / f"projection-comment-{slugify(comment_ref)}.json"
    dump_json(record_ref, result)
    runtime_refs = load_json(artifacts_dir / "runtime-artifact-refs.json")
    runtime_refs["latest_projection_comment_ref"] = repo_relative(repo_root, record_ref)
    runtime_refs["latest_revision_request_ref"] = result["revision_request_ref"]
    dump_json(artifacts_dir / "runtime-artifact-refs.json", runtime_refs)
    return {
        "comment_record_ref": repo_relative(repo_root, record_ref),
        **result,
    }


def regenerate_projection_bundle(
    artifacts_dir: Path,
    repo_root: Path,
    updated_ssot_ref: str,
    revision_request_ref: str = "",
) -> dict[str, Any]:
    _ensure_implementation_root()
    from cli.lib.review_projection.regeneration import request_projection_regeneration

    runtime_refs = load_json(artifacts_dir / "runtime-artifact-refs.json")
    effective_revision_ref = revision_request_ref or str(runtime_refs.get("latest_revision_request_ref", ""))
    if not effective_revision_ref:
        raise ValueError("revision_request_ref is required")
    result = request_projection_regeneration(
        workspace_root=repo_root,
        revision_request_ref=effective_revision_ref,
        updated_ssot_ref=updated_ssot_ref,
    )
    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    projection = load_json(_path_from_ref(repo_root, result["regenerated_projection_ref"]))
    bundle.update(
        {
            "machine_ssot_ref": updated_ssot_ref,
            "human_projection_ref": result["regenerated_projection_ref"],
            "projection_status": projection.get("status", ""),
            "projection_trace_refs": projection.get("trace_refs", []),
            "projection_markers": projection.get("derived_markers", {}),
            "snapshot_ref": projection.get("snapshot_ref", ""),
            "focus_ref": projection.get("focus_ref", ""),
            "human_projection": projection,
        }
    )
    for ref_value in (result["regenerated_projection_ref"], projection.get("snapshot_ref", ""), projection.get("focus_ref", ""), effective_revision_ref):
        if ref_value and ref_value not in bundle["source_refs"]:
            bundle["source_refs"].append(ref_value)
    write_bundle_files(artifacts_dir, bundle)
    runtime_refs["human_projection_ref"] = result["regenerated_projection_ref"]
    runtime_refs["snapshot_ref"] = projection.get("snapshot_ref", "")
    runtime_refs["focus_ref"] = projection.get("focus_ref", "")
    runtime_refs["latest_revision_request_ref"] = effective_revision_ref
    dump_json(artifacts_dir / "runtime-artifact-refs.json", runtime_refs)
    record_ref = artifacts_dir / "projection-regeneration.json"
    dump_json(record_ref, result)
    return {
        "regeneration_record_ref": repo_relative(repo_root, record_ref),
        **result,
    }


def write_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "gate-freeze-gate.json")
    bundle = load_json(artifacts_dir / "gate-decision-bundle.json")
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-gate-human-orchestrator Review Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- decision: {bundle.get('decision')}",
                f"- projection_status: {bundle.get('projection_status', '')}",
                "",
                "## Execution Evidence",
                "",
                f"- commands: {', '.join(execution.get('commands_run', []))}",
                "",
                "## Supervision Evidence",
                "",
                f"- supervisor_decision: {supervision.get('decision')}",
                "",
                "## Freeze Gate",
                "",
                f"- freeze_ready: {gate.get('freeze_ready')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def _path_from_ref(repo_root: Path, ref_value: str) -> Path:
    path = Path(ref_value)
    return path if path.is_absolute() else (repo_root / path)


def _ensure_implementation_root() -> None:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
