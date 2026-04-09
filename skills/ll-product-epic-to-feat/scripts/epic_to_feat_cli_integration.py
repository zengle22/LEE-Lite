#!/usr/bin/env python3
"""
CLI-backed materialization helpers for epic-to-feat.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from cli.lib.feat_semantic_phase1 import build_feat_semantic_artifacts
from epic_to_feat_common import dump_json, load_json, parse_markdown_frontmatter, render_markdown
from epic_to_feat_review_phase1 import build_epic_to_feat_document_test_report, validate_review_phase1_fields


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _surface_map_summary_md(bundle: dict[str, Any]) -> str:
    selected = bundle.get("selected_feat") if isinstance(bundle.get("selected_feat"), dict) else {}
    surface_map = bundle.get("surface_map") if isinstance(bundle.get("surface_map"), dict) else {}
    design_surfaces = surface_map.get("design_surfaces") if isinstance(surface_map.get("design_surfaces"), dict) else {}
    lines: list[str] = [
        f"# Surface Map Bundle ({bundle.get('surface_map_ref') or 'SURFACE-MAP'})",
        "",
        "## Selected FEAT",
        "",
        f"- feat_ref: {selected.get('feat_ref') or bundle.get('feat_ref') or ''}",
        f"- title: {selected.get('title') or ''}",
        f"- goal: {selected.get('goal') or ''}",
        "",
        "## Design Impact",
        "",
        f"- design_impact_required: {str(bool(bundle.get('design_impact_required'))).lower()}",
        f"- owner_binding_status: {surface_map.get('owner_binding_status') or ''}",
        f"- bypass_rationale: {surface_map.get('bypass_rationale') or ''}",
        "",
        "## Surface Map",
        "",
    ]
    for surface_name in ("architecture", "api", "ui", "prototype", "tech"):
        entries = design_surfaces.get(surface_name) or []
        lines.append(f"### {surface_name.title()}")
        if not isinstance(entries, list) or not entries:
            lines.append("[none]")
            lines.append("")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            owner = str(entry.get("owner") or "").strip()
            action = str(entry.get("action") or "").strip()
            scope = entry.get("scope") if isinstance(entry.get("scope"), list) else []
            reason = str(entry.get("reason") or "").strip()
            lines.append(f"- {owner} ({action})")
            if scope:
                lines.append(f"  - scope: {', '.join(str(item) for item in scope if str(item).strip())}")
            if reason:
                lines.append(f"  - reason: {reason}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _maybe_write_surface_map_artifacts(output_dir: Path, repo_root: Path, generated: Any) -> dict[str, Any]:
    json_payload = generated.json_payload if isinstance(getattr(generated, "json_payload", None), dict) else {}
    feats = json_payload.get("features")
    if not isinstance(feats, list) or not feats:
        return {}

    design_impact_feats = [item for item in feats if isinstance(item, dict) and bool(item.get("design_impact_required"))]
    if not design_impact_feats:
        return {}

    # repo_root can point to a *target* workspace (often a temp repo in unit tests).
    # The surface-map helper modules live alongside this implementation repo, so
    # we must import them from the implementation root, not the target repo_root.
    implementation_root = Path(__file__).resolve().parents[3]
    surface_map_scripts_dir = implementation_root / "skills" / "ll-dev-feat-to-surface-map" / "scripts"
    if str(surface_map_scripts_dir) not in sys.path:
        sys.path.insert(0, str(surface_map_scripts_dir))
    from feat_to_surface_map_common import build_freeze_gate, build_package_payload, build_review_report  # type: ignore
    from feat_to_surface_map_validation import validate_bundle_payload  # type: ignore

    run_id = output_dir.name
    feat_refs = [str(item.get("feat_ref") or "").strip() for item in feats if isinstance(item, dict) and str(item.get("feat_ref") or "").strip()]

    index_entries: list[dict[str, str]] = []
    canonical_surface_map_ref = ""
    canonical_written = False

    for feature in design_impact_feats:
        feat_ref = str(feature.get("feat_ref") or "").strip()
        if not feat_ref:
            continue

        context = {
            "bundle": json_payload,
            "feature": feature,
            "selected_feat_ref": feat_ref,
            "feat_ref": feat_ref,
        }
        bundle = build_package_payload(context, run_id)
        bundle["related_feat_refs"] = [ref for ref in feat_refs if ref and ref != feat_ref]

        validation_errors: list[str] = []
        validate_bundle_payload(validation_errors, bundle)
        review_report = build_review_report(run_id, feat_ref, validation_errors)
        gate = build_freeze_gate(review_report, validation_errors)
        defects = [{"severity": "P1", "title": error, "type": "validation"} for error in validation_errors]

        surface_map_ref = str(bundle.get("surface_map_ref") or "").strip() or "SURFACE-MAP"
        if not canonical_surface_map_ref:
            canonical_surface_map_ref = surface_map_ref

        # Keep a canonical set of surface-map artifacts for debugging and for the
        # package-manifest references (first design-impact feature wins).
        if not canonical_written:
            fixed_files = {
                "surface-map-bundle.json": bundle,
                "surface-map-bundle.md": _surface_map_summary_md(bundle),
                "surface-map-review-report.json": review_report,
                "surface-map-defect-list.json": defects,
                "surface-map-freeze-gate.json": gate,
            }
            for filename, payload in fixed_files.items():
                if filename.endswith(".md"):
                    (output_dir / filename).write_text(str(payload), encoding="utf-8")
                else:
                    dump_json(output_dir / filename, payload)
            canonical_written = True

        id_bundle_json = f"surface-map-bundle__{feat_ref}.json"
        id_bundle_md = f"surface-map-bundle__{feat_ref}.md"
        id_gate_json = f"surface-map-freeze-gate__{feat_ref}.json"
        dump_json(output_dir / id_bundle_json, bundle)
        (output_dir / id_bundle_md).write_text(_surface_map_summary_md(bundle), encoding="utf-8")
        dump_json(output_dir / id_gate_json, gate)

        index_entries.append(
            {
                "feat_ref": feat_ref,
                "surface_map_ref": surface_map_ref,
                "bundle_ref": id_bundle_json,
            }
        )

    if not index_entries:
        return {}

    dump_json(
        output_dir / "surface-map-index.json",
        {
            "artifact_type": "surface_map_index",
            "schema_version": "1.0.0",
            "surface_map_ref": canonical_surface_map_ref,
            "entries": index_entries,
        },
    )

    return {
        "surface_map_ref": canonical_surface_map_ref,
        "surface_map_index_ref": str(output_dir / "surface-map-index.json"),
        "surface_map_bundle_ref": str(output_dir / "surface-map-bundle.json"),
        "surface_map_bundle_md_ref": str(output_dir / "surface-map-bundle.md"),
        "surface_map_review_report_ref": str(output_dir / "surface-map-review-report.json"),
        "surface_map_defect_list_ref": str(output_dir / "surface-map-defect-list.json"),
        "surface_map_freeze_gate_ref": str(output_dir / "surface-map-freeze-gate.json"),
    }


def _canonical_ref(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


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


def _load_l3_review(artifacts_dir: Path) -> tuple[dict[str, Any], Path]:
    path = artifacts_dir / "l3-review.json"
    payload = load_json(path) if path.exists() else {}
    return payload if isinstance(payload, dict) else {}, path


def _persist_l3_review(artifacts_dir: Path, l3_review: dict[str, Any]) -> Path | None:
    if not isinstance(l3_review, dict) or not l3_review:
        return None
    path = artifacts_dir / "l3-review.json"
    dump_json(path, l3_review)
    return path


def write_executor_outputs(output_dir: Path, repo_root: Path, package: Any, generated: Any, command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = output_dir.name
    revision_context = generated.json_payload.get("revision_context") if isinstance(generated.json_payload.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or "").strip()
    document_test_report = build_epic_to_feat_document_test_report(generated)
    semantic = build_feat_semantic_artifacts(
        str(Path(__file__).resolve().parents[1] / "resources" / "semantic-dimensions.json"),
        generated.json_payload,
        list(generated.defect_list),
        dict(generated.handoff),
        dict(generated.semantic_drift_check),
    )
    for key in ("semantic_dimensions_ref", "semantic_coverage", "semantic_pass", "review_views", "l3_review"):
        generated.json_payload[key] = semantic[key]
        if isinstance(generated.review_report, dict):
            generated.review_report[key] = semantic[key]
        if isinstance(generated.acceptance_report, dict):
            generated.acceptance_report[key] = semantic[key]
    if isinstance(generated.handoff, dict):
        generated.handoff.update(semantic.get("handoff_updates") or {})
    markdown_text = render_markdown(generated.frontmatter, generated.markdown_body)
    cli_commit = _commit_markdown(repo_root, output_dir, run_id, markdown_text, "feat-freeze-executor-commit")
    dump_json(output_dir / "feat-freeze-bundle.json", generated.json_payload)
    dump_json(output_dir / "integration-context.json", generated.json_payload["integration_context"])
    dump_json(output_dir / "feat-review-report.json", generated.review_report)
    dump_json(output_dir / "feat-acceptance-report.json", generated.acceptance_report)
    dump_json(output_dir / "feat-defect-list.json", generated.defect_list)
    dump_json(output_dir / "document-test-report.json", document_test_report)
    dump_json(output_dir / "handoff-to-feat-downstreams.json", generated.handoff)
    dump_json(output_dir / "semantic-drift-check.json", generated.semantic_drift_check)
    surface_map_manifest = _maybe_write_surface_map_artifacts(output_dir, repo_root, generated)
    if not surface_map_manifest:
        dump_json(
            output_dir / "surface-map-index.json",
            {
                "artifact_type": "surface_map_index",
                "schema_version": "1.0.0",
                "surface_map_ref": "",
                "entries": [],
            },
        )
        surface_map_manifest = {"surface_map_index_ref": str(output_dir / "surface-map-index.json")}
    spec_findings_path = output_dir / "spec-findings.json"
    dump_json(
        spec_findings_path,
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "product.epic-to-feat", "run_ref": package.run_id},
            "lineage": [],
            "findings": [],
        },
    )
    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": package.run_id,
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "primary_artifact_ref": str(output_dir / "feat-freeze-bundle.md"),
            "integration_context_ref": str(output_dir / "integration-context.json"),
            "result_summary_ref": str(output_dir / "feat-freeze-gate.json"),
            "review_report_ref": str(output_dir / "feat-review-report.json"),
            "acceptance_report_ref": str(output_dir / "feat-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "feat-defect-list.json"),
            "document_test_report_ref": str(output_dir / "document-test-report.json"),
            "handoff_ref": str(output_dir / "handoff-to-feat-downstreams.json"),
            "semantic_drift_check_ref": str(output_dir / "semantic-drift-check.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
            "status": generated.json_payload["status"],
            "cli_executor_commit_ref": str(cli_commit["response_path"]),
            "spec_findings_ref": _canonical_ref(spec_findings_path, repo_root),
            **surface_map_manifest,
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
            "outputs": [str(output_dir / "feat-freeze-bundle.md"), str(output_dir / "feat-freeze-bundle.json"), str(output_dir / "integration-context.json")],
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "draft_output_files": [
                    "feat-freeze-bundle.md",
                    "feat-freeze-bundle.json",
                    "integration-context.json",
                    "feat-review-report.json",
                    "feat-acceptance-report.json",
                    "feat-defect-list.json",
                    "document-test-report.json",
                    "surface-map-index.json",
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

    if surface_map_manifest:
        execution = load_json(output_dir / "execution-evidence.json")
        structural = execution.get("structural_results") if isinstance(execution.get("structural_results"), dict) else {}
        draft_files = structural.get("draft_output_files") if isinstance(structural.get("draft_output_files"), list) else []
        for name in [
            "surface-map-bundle.json",
            "surface-map-bundle.md",
            "surface-map-review-report.json",
            "surface-map-defect-list.json",
            "surface-map-freeze-gate.json",
            "surface-map-index.json",
        ]:
            if name not in draft_files:
                draft_files.append(name)
        structural["draft_output_files"] = draft_files
        execution["structural_results"] = structural
        dump_json(output_dir / "execution-evidence.json", execution)


def build_supervision_evidence(artifacts_dir: Path, generated: Any) -> dict[str, Any]:
    decision = "pass" if not generated.defect_list else "revise"
    document_test_report = build_epic_to_feat_document_test_report(generated)
    revision_context = generated.json_payload.get("revision_context") if isinstance(generated.json_payload.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or "").strip()
    revision_summary = str(revision_context.get("summary") or "").strip()
    current_bundle = load_json(artifacts_dir / "feat-freeze-bundle.json")
    findings = [
        {
            "title": "FEAT boundary preserved" if decision == "pass" else "FEAT boundary needs revision",
            "detail": "The generated FEAT bundle remains suitable for downstream derivation." if decision == "pass" else "The generated FEAT bundle requires revision before freeze.",
        }
    ]
    findings.extend({"title": defect["title"], "detail": defect["detail"]} for defect in generated.defect_list)
    if revision_summary:
        findings.append({"title": "Revision context absorbed", "detail": revision_summary})
    l3_review, l3_review_path = _load_l3_review(artifacts_dir)
    return {
        "skill_id": "ll-product-epic-to-feat",
        "run_id": generated.frontmatter["workflow_run_id"],
        "role": "supervisor",
        "semantic_pass": bool(current_bundle.get("semantic_pass", False)),
        "open_semantic_gaps": list((current_bundle.get("semantic_coverage") or {}).get("open_semantic_gaps") or []),
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
        "document_test_report_ref": str(artifacts_dir / "document-test-report.json"),
        "document_test_outcome": document_test_report["test_outcome"],
        **({"l3_review": l3_review} if isinstance(l3_review, dict) and l3_review else {}),
        **({"l3_review_artifact_ref": str(l3_review_path)} if isinstance(l3_review, dict) and l3_review else {}),
        **({"revision_request_ref": revision_request_ref} if revision_request_ref else {}),
    }


def build_gate_result(generated: Any, supervision_evidence: dict[str, Any]) -> dict[str, Any]:
    document_test_report = build_epic_to_feat_document_test_report(generated)
    review_phase1_ready = not validate_review_phase1_fields(document_test_report)
    document_test_non_blocking = document_test_report["test_outcome"] == "no_blocking_defect_found"
    semantic_pass = bool(supervision_evidence.get("semantic_pass", generated.json_payload.get("semantic_pass", False)))
    l3_review = supervision_evidence.get("l3_review") if isinstance(supervision_evidence.get("l3_review"), dict) else {}
    l3_decision = str(l3_review.get("decision") or "").strip().lower()
    l3_review_present = l3_decision in {"pass", "revise", "reject"}
    l3_review_pass = l3_decision == "pass"
    pass_gate = (
        supervision_evidence["decision"] == "pass"
        and not generated.defect_list
        and document_test_non_blocking
        and review_phase1_ready
        and semantic_pass
    )
    revision_context = generated.json_payload.get("revision_context") if isinstance(generated.json_payload.get("revision_context"), dict) else {}
    revision_request_ref = str(revision_context.get("revision_request_ref") or supervision_evidence.get("revision_request_ref") or "").strip()
    return {
        "workflow_key": "product.epic-to-feat",
        "decision": "pass" if pass_gate else "revise",
        "freeze_ready": pass_gate,
        "semantic_pass": semantic_pass,
        "open_semantic_gaps": list(supervision_evidence.get("open_semantic_gaps") or (generated.json_payload.get("semantic_coverage") or {}).get("open_semantic_gaps") or []),
        "l3_review_present": l3_review_present,
        "l3_review_pass": l3_review_pass,
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
            "document_test_report_present": document_test_report["test_outcome"] in {"no_blocking_defect_found", "blocking_defect_found", "inconclusive", "not_applicable"},
            "document_test_non_blocking": document_test_non_blocking,
            "review_phase1_ready": review_phase1_ready,
            "semantic_pass": semantic_pass,
            **({"revision_request_present": True} if revision_request_ref else {}),
        },
        "created_at": generated.acceptance_report["created_at"],
    }


def update_supervisor_outputs(artifacts_dir: Path, repo_root: Path, generated: Any, supervision: dict[str, Any], gate: dict[str, Any]) -> None:
    run_id = artifacts_dir.name
    document_test_report = build_epic_to_feat_document_test_report(generated)
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
    dump_json(artifacts_dir / "document-test-report.json", document_test_report)
    _persist_l3_review(artifacts_dir, supervision.get("l3_review") if isinstance(supervision, dict) else {})
    handoff_path = artifacts_dir / "handoff-to-feat-downstreams.json"
    if handoff_path.exists():
        handoff_payload = load_json(handoff_path)
        if isinstance(handoff_payload, dict):
            semantic_pass = bool(updated_json.get("semantic_pass", False))
            # The external human gate runs after this freeze gate and may later attach L3 evidence.
            handoff_payload["semantic_ready"] = bool(semantic_pass)
            handoff_payload["open_semantic_gaps"] = list((updated_json.get("semantic_coverage") or {}).get("open_semantic_gaps") or [])
            dump_json(handoff_path, handoff_payload)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "feat-freeze-gate.json", gate)
    manifest = load_json(artifacts_dir / "package-manifest.json")
    manifest["cli_supervisor_commit_ref"] = str(cli_commit["response_path"])
    manifest["document_test_report_ref"] = str(artifacts_dir / "document-test-report.json")
    if revision_request_ref:
        manifest["revision_request_ref"] = revision_request_ref
    dump_json(artifacts_dir / "package-manifest.json", manifest)


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    document_test = load_json(artifacts_dir / "document-test-report.json")
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
