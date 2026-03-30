#!/usr/bin/env python3
"""
Executor phase for raw-to-src.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from raw_to_src_cli_integration import commit_candidate_markdown
from raw_to_src_common import (
    apply_structural_patch,
    load_raw_input,
    normalize_candidate,
    render_candidate_markdown,
    structural_check,
    validate_input_document,
)
from raw_to_src_loop_helpers import (
    apply_input_patch,
    apply_intake_patch,
    split_patchable_issues,
    validate_intake_document,
)
from raw_to_src_records import build_execution_evidence, build_patch_lineage, stage


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_patch_events(run_id: str, stage_id: str, event_prefix: str, patches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "patch_id": f"patch-{run_id}-{event_prefix}-{index}",
            "stage_id": stage_id,
            "actor_role": "executor",
            "patch_scope": "structural",
            "patch_mode": "minimal_patch",
            "issue_code": patch["code"],
            "target_fields": patch["target_fields"],
            "action": patch["action"],
            "outcome": "applied",
        }
        for index, patch in enumerate(patches, start=1)
    ]


def _materialize_revision_request(
    artifacts_dir: Path,
    revision_request_path: Path | None,
) -> tuple[str, dict[str, Any] | None, list[dict[str, Any]]]:
    destination = artifacts_dir / "revision-request.json"
    source_path = revision_request_path or (destination if destination.exists() else None)
    if source_path is None or not source_path.exists():
        return "", None, []
    revision_request = json.loads(source_path.read_text(encoding="utf-8"))
    if source_path.resolve() != destination.resolve():
        write_json(destination, revision_request)
    event = {
        "patch_id": f"patch-{revision_request.get('run_id') or revision_request.get('source_run_id') or 'revision'}-revision-request",
        "stage_id": "revision_request",
        "actor_role": "executor",
        "patch_scope": "external_revision",
        "patch_mode": "gate_revise_rerun",
        "issue_code": str(revision_request.get("decision_type") or "revise"),
        "target_fields": ["revision-request.json"],
        "action": "Accepted external revision request as rerun context.",
        "outcome": "applied",
    }
    return str(destination), deepcopy(revision_request), [event]


def _run_input_flow(document: dict[str, Any], input_path: Path, artifacts_dir: Path, run_id: str) -> tuple[
    dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]
]:
    initial_issues, initial_validation = validate_input_document(document)
    patchable, blocking = split_patchable_issues(initial_issues, {"missing_title", "missing_body"})
    input_patches: list[dict[str, Any]] = []
    structural_attempts: list[dict[str, Any]] = []
    if patchable:
        document, input_patches = apply_input_patch(document, patchable)
        structural_attempts.append(
            {
                "loop": "structural",
                "attempt_number": 1,
                "reason": patchable[0]["code"],
                "outcome": "input_patch_applied",
            }
        )
    revalidation_issues, input_validation = validate_input_document(document)
    stages = [
        stage("input_validation", "passed" if initial_validation["valid"] else "failed", "Input validation completed.", "executor", input_refs=[str(input_path)], output_refs=[str(artifacts_dir / "input-validation.json")], issues_found=[item["code"] for item in initial_issues]),
        stage("input_fix_assessment", "blocked" if blocking else ("revise" if patchable else "passed"), "Input patchability assessment completed.", "executor", issues_found=[item["code"] for item in initial_issues]),
        stage("input_minimal_patch", "completed" if input_patches else "skipped", f"{len(input_patches)} input patches applied.", "executor", patches_applied=[item["code"] for item in input_patches]),
        stage("input_revalidation", "passed" if input_validation["valid"] else "failed", "Input revalidation completed.", "executor", issues_found=[item["code"] for item in revalidation_issues], revalidation_status="passed" if input_validation["valid"] else "failed"),
    ]
    report = {
        "initial_validation": initial_validation,
        "patch_assessment": {
            "patchable_issue_codes": [item["code"] for item in patchable],
            "blocking_issue_codes": [item["code"] for item in blocking],
        },
        "applied_patches": input_patches,
        "revalidation": input_validation,
    }
    return document, input_validation, stages, _build_patch_events(run_id, "input_minimal_patch", "input", input_patches), structural_attempts, report


def _run_intake_flow(
    document: dict[str, Any],
    input_path: Path,
    artifacts_dir: Path,
    run_id: str,
    structural_attempts: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    intake_issues, intake_validation = validate_intake_document(document)
    patchable, blocking = split_patchable_issues(intake_issues, {"missing_title", "missing_source_refs", "missing_problem_statement"})
    intake_patches: list[dict[str, Any]] = []
    if patchable:
        document, intake_patches = apply_intake_patch(document, patchable)
        structural_attempts.append(
            {
                "loop": "structural",
                "attempt_number": len(structural_attempts) + 1,
                "reason": patchable[0]["code"],
                "outcome": "intake_patch_applied",
            }
        )
        intake_issues, intake_validation = validate_intake_document(document)
    stages = [
        stage("raw_input_intake", "passed", "Raw input captured.", "executor", input_refs=[str(input_path)], output_refs=[str(artifacts_dir / "normalized-input.json")]),
        stage("intake_validation", "passed" if intake_validation["valid"] else "failed", "Intake validation completed.", "executor", issues_found=[item["code"] for item in intake_issues]),
        stage("intake_fix_assessment", "blocked" if blocking else ("revise" if patchable else "passed"), "Intake patchability assessment completed.", "executor", issues_found=[item["code"] for item in intake_issues]),
        stage("intake_minimal_patch", "completed" if intake_patches else "skipped", f"{len(intake_patches)} intake patches applied.", "executor", patches_applied=[item["code"] for item in intake_patches]),
        stage("intake_revalidation", "passed" if intake_validation["valid"] else "failed", "Intake revalidation completed.", "executor", issues_found=[item["code"] for item in intake_issues], revalidation_status="passed" if intake_validation["valid"] else "failed"),
    ]
    report = {
        "document": document,
        "intake_validation": intake_validation,
        "applied_patches": intake_patches,
    }
    return document, intake_validation, stages, _build_patch_events(run_id, "intake_minimal_patch", "intake", intake_patches), report


def _run_structural_flow(document: dict[str, Any], run_id: str, structural_attempts: list[dict[str, Any]]) -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str], list[dict[str, Any]]
]:
    candidate = normalize_candidate(document)
    candidate["workflow_run_id"] = run_id
    structural_issues = structural_check(candidate)
    applied_fixes: list[dict[str, Any]] = []
    decisions: list[str] = []
    if structural_issues:
        structural_attempts.append(
            {
                "loop": "structural",
                "attempt_number": len(structural_attempts) + 1,
                "reason": structural_issues[0]["code"],
                "outcome": "patch_applied",
            }
        )
        candidate, applied_fixes = apply_structural_patch(candidate, structural_issues)
        decisions.extend(item["action"] for item in applied_fixes)
        structural_issues = structural_check(candidate)
    stages = [
        stage("structural_fix_loop", "completed", f"{len(applied_fixes)} deterministic fixes applied.", "executor", patches_applied=[item["code"] for item in applied_fixes]),
        stage("structural_recheck", "passed" if not structural_issues else "failed", "Structural recheck completed.", "executor", issues_found=[item["code"] for item in structural_issues], revalidation_status="passed" if not structural_issues else "failed"),
    ]
    return candidate, structural_issues, stages, _build_patch_events(run_id, "structural_fix_loop", "structural", applied_fixes), decisions, applied_fixes


def _persist_outputs(
    repo_root: Path,
    artifacts_dir: Path,
    run_id: str,
    candidate: dict[str, Any],
    stage_results: list[dict[str, Any]],
    document: dict[str, Any],
    input_validation: dict[str, Any],
    intake_validation: dict[str, Any],
    intake_patches: list[dict[str, Any]],
    input_validation_report: dict[str, Any],
    structural_issues: list[dict[str, Any]],
    applied_fixes: list[dict[str, Any]],
    structural_attempts: list[dict[str, Any]],
    patch_events: list[dict[str, Any]],
) -> Path:
    candidate_path = artifacts_dir / "src-candidate.md"
    candidate_json_path = artifacts_dir / "src-candidate.json"
    cli_commit = commit_candidate_markdown(repo_root, artifacts_dir, run_id, render_candidate_markdown(candidate))
    write_json(candidate_json_path, candidate)
    write_json(artifacts_dir / "semantic-inventory.json", candidate.get("semantic_inventory", {}))
    write_json(artifacts_dir / "source-provenance-map.json", candidate.get("source_provenance_map", []))
    write_json(artifacts_dir / "contradiction-register.json", candidate.get("contradiction_register", []))
    write_json(artifacts_dir / "normalization-decisions.json", candidate.get("normalization_decisions", []))
    write_json(artifacts_dir / "omission-and-compression-report.json", candidate.get("omission_and_compression_report", {}))
    stage_results.extend(
        [
            stage("source_normalization", "passed", "SRC candidate normalized and committed via CLI artifact runtime.", "executor", input_refs=[str(artifacts_dir / "normalized-input.json")], output_refs=[str(candidate_path), str(candidate_json_path), str(cli_commit["response_path"])]),
            stage("structural_acceptance_check", "passed" if not structural_issues else "revise", "Structural check completed.", "executor", input_refs=[str(candidate_json_path)], issues_found=[item["code"] for item in structural_issues]),
        ]
    )
    write_json(artifacts_dir / "normalized-input.json", {"document": document, "intake_validation": intake_validation, "applied_patches": intake_patches, "cli_candidate_commit_ref": str(cli_commit["response_path"])})
    write_json(artifacts_dir / "input-validation.json", input_validation_report)
    write_json(
        artifacts_dir / "structural-report.json",
        {
            "issues": structural_issues,
            "applied_fixes": applied_fixes,
            "stages": [item for item in stage_results if item["role"] == "executor"],
            "structural_attempts": structural_attempts,
            "input_valid": input_validation["valid"],
            "intake_valid": intake_validation["valid"],
            "cli_candidate_commit_ref": str(cli_commit["response_path"]),
            "cli_candidate_receipt_ref": cli_commit["response"]["data"].get("receipt_ref", ""),
            "cli_candidate_registry_record_ref": cli_commit["response"]["data"].get("registry_record_ref", ""),
        },
    )
    write_json(artifacts_dir / "patch-lineage.json", build_patch_lineage(run_id, patch_events))
    return candidate_path


def executor_run(input_path: Path, repo_root: Path, run_id: str, revision_request_path: Path | None = None) -> dict[str, Any]:
    artifacts_dir = ensure_dir(repo_root / "artifacts" / "raw-to-src" / run_id)
    ensure_dir(repo_root / "ssot" / "src")
    document = load_raw_input(input_path)
    document["workflow_run_id"] = run_id
    revision_request_ref, revision_request, revision_events = _materialize_revision_request(artifacts_dir, revision_request_path)

    document, input_validation, stage_results, patch_events, structural_attempts, input_validation_report = _run_input_flow(document, input_path, artifacts_dir, run_id)
    document, intake_validation, intake_stages, intake_events, intake_report = _run_intake_flow(document, input_path, artifacts_dir, run_id, structural_attempts)
    candidate, structural_issues, structural_stages, structural_events, decisions, applied_fixes = _run_structural_flow(document, run_id, structural_attempts)

    stage_results.extend(intake_stages)
    stage_results.extend(structural_stages)
    patch_events.extend(revision_events)
    patch_events.extend(intake_events)
    patch_events.extend(structural_events)
    candidate_path = _persist_outputs(
        repo_root,
        artifacts_dir,
        run_id,
        candidate,
        stage_results,
        document,
        input_validation,
        intake_validation,
        intake_report["applied_patches"],
        input_validation_report,
        structural_issues,
        applied_fixes,
        structural_attempts,
        patch_events,
    )
    execution = build_execution_evidence(
        run_id,
        input_path,
        [candidate_path],
        stage_results,
        {"input_validation": input_validation, "intake_validation": intake_validation, "structural_issues": structural_issues},
        decisions,
        candidate["uncertainties"],
        revision_request_ref=revision_request_ref,
    )
    if revision_request is not None:
        execution["revision_request"] = revision_request
    write_json(artifacts_dir / "execution-evidence.json", execution)
    return {
        "ok": True,
        "run_id": run_id,
        "artifacts_dir": str(artifacts_dir),
        "candidate_path": str(candidate_path),
        "structural_issues": structural_issues,
        "input_valid": input_validation["valid"],
        "intake_valid": intake_validation["valid"],
        "revision_request_ref": revision_request_ref,
    }
