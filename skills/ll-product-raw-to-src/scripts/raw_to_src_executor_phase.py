#!/usr/bin/env python3
"""
Executor phase for raw-to-src.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def executor_run(input_path: Path, repo_root: Path, run_id: str) -> dict[str, Any]:
    artifacts_dir = ensure_dir(repo_root / "artifacts" / "raw-to-src" / run_id)
    ensure_dir(repo_root / "ssot" / "src")

    document = load_raw_input(input_path)
    document["workflow_run_id"] = run_id

    initial_input_issues, initial_input_validation = validate_input_document(document)
    input_patchable, input_blocking = split_patchable_issues(initial_input_issues, {"missing_title", "missing_body"})
    input_patches: list[dict[str, Any]] = []
    structural_attempts: list[dict[str, Any]] = []
    decisions: list[str] = []

    if input_patchable:
        document, input_patches = apply_input_patch(document, input_patchable)
        structural_attempts.append(
            {
                "loop": "structural",
                "attempt_number": 1,
                "reason": input_patchable[0]["code"],
                "outcome": "input_patch_applied",
            }
        )
    input_revalidation_issues, input_validation = validate_input_document(document)

    stage_results = [
        stage(
            "input_validation",
            "passed" if initial_input_validation["valid"] else "failed",
            "Input validation completed.",
            "executor",
            input_refs=[str(input_path)],
            output_refs=[str(artifacts_dir / "input-validation.json")],
            issues_found=[item["code"] for item in initial_input_issues],
        ),
        stage(
            "input_fix_assessment",
            "blocked" if input_blocking else ("revise" if input_patchable else "passed"),
            "Input patchability assessment completed.",
            "executor",
            issues_found=[item["code"] for item in initial_input_issues],
        ),
        stage(
            "input_minimal_patch",
            "completed" if input_patches else "skipped",
            f"{len(input_patches)} input patches applied.",
            "executor",
            patches_applied=[item["code"] for item in input_patches],
        ),
        stage(
            "input_revalidation",
            "passed" if input_validation["valid"] else "failed",
            "Input revalidation completed.",
            "executor",
            issues_found=[item["code"] for item in input_revalidation_issues],
            revalidation_status="passed" if input_validation["valid"] else "failed",
        ),
    ]
    patch_events: list[dict[str, Any]] = [
        {
            "patch_id": f"patch-{run_id}-input-{index}",
            "stage_id": "input_minimal_patch",
            "actor_role": "executor",
            "patch_scope": "structural",
            "patch_mode": "minimal_patch",
            "issue_code": patch["code"],
            "target_fields": patch["target_fields"],
            "action": patch["action"],
            "outcome": "applied",
        }
        for index, patch in enumerate(input_patches, start=1)
    ]

    intake_issues, intake_validation = validate_intake_document(document)
    intake_patchable, intake_blocking = split_patchable_issues(
        intake_issues,
        {"missing_title", "missing_source_refs", "missing_problem_statement"},
    )
    intake_patches: list[dict[str, Any]] = []
    stage_results.extend(
        [
            stage(
                "raw_input_intake",
                "passed",
                "Raw input captured.",
                "executor",
                input_refs=[str(input_path)],
                output_refs=[str(artifacts_dir / "normalized-input.json")],
            ),
            stage(
                "intake_validation",
                "passed" if intake_validation["valid"] else "failed",
                "Intake validation completed.",
                "executor",
                issues_found=[item["code"] for item in intake_issues],
            ),
            stage(
                "intake_fix_assessment",
                "blocked" if intake_blocking else ("revise" if intake_patchable else "passed"),
                "Intake patchability assessment completed.",
                "executor",
                issues_found=[item["code"] for item in intake_issues],
            ),
        ]
    )
    if intake_patchable:
        document, intake_patches = apply_intake_patch(document, intake_patchable)
        structural_attempts.append(
            {
                "loop": "structural",
                "attempt_number": len(structural_attempts) + 1,
                "reason": intake_patchable[0]["code"],
                "outcome": "intake_patch_applied",
            }
        )
        intake_issues, intake_validation = validate_intake_document(document)
    stage_results.extend(
        [
            stage(
                "intake_minimal_patch",
                "completed" if intake_patches else "skipped",
                f"{len(intake_patches)} intake patches applied.",
                "executor",
                patches_applied=[item["code"] for item in intake_patches],
            ),
            stage(
                "intake_revalidation",
                "passed" if intake_validation["valid"] else "failed",
                "Intake revalidation completed.",
                "executor",
                issues_found=[item["code"] for item in intake_issues],
                revalidation_status="passed" if intake_validation["valid"] else "failed",
            ),
        ]
    )
    patch_events.extend(
        {
            "patch_id": f"patch-{run_id}-intake-{index}",
            "stage_id": "intake_minimal_patch",
            "actor_role": "executor",
            "patch_scope": "structural",
            "patch_mode": "minimal_patch",
            "issue_code": patch["code"],
            "target_fields": patch["target_fields"],
            "action": patch["action"],
            "outcome": "applied",
        }
        for index, patch in enumerate(intake_patches, start=1)
    )

    candidate = normalize_candidate(document)
    candidate["workflow_run_id"] = run_id
    stage_results.append(
        stage(
            "source_normalization",
            "passed",
            "SRC candidate normalized.",
            "executor",
            input_refs=[str(artifacts_dir / "normalized-input.json")],
            output_refs=[str(artifacts_dir / "src-candidate.json")],
        )
    )

    structural_issues = structural_check(candidate)
    stage_results.append(
        stage(
            "structural_acceptance_check",
            "passed" if not structural_issues else "revise",
            "Structural check completed.",
            "executor",
            input_refs=[str(artifacts_dir / "src-candidate.json")],
            issues_found=[item["code"] for item in structural_issues],
        )
    )
    applied_fixes: list[dict[str, Any]] = []
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
        patch_events.extend(
            {
                "patch_id": f"patch-{run_id}-structural-{index}",
                "stage_id": "structural_fix_loop",
                "actor_role": "executor",
                "patch_scope": "structural",
                "patch_mode": "minimal_patch",
                "issue_code": patch["code"],
                "target_fields": patch["target_fields"],
                "action": patch["action"],
                "outcome": "applied",
            }
            for index, patch in enumerate(applied_fixes, start=1)
        )
        structural_issues = structural_check(candidate)
    stage_results.extend(
        [
            stage(
                "structural_fix_loop",
                "completed",
                f"{len(applied_fixes)} deterministic fixes applied.",
                "executor",
                patches_applied=[item["code"] for item in applied_fixes],
            ),
            stage(
                "structural_recheck",
                "passed" if not structural_issues else "failed",
                "Structural recheck completed.",
                "executor",
                issues_found=[item["code"] for item in structural_issues],
                revalidation_status="passed" if not structural_issues else "failed",
            ),
        ]
    )

    candidate_path = artifacts_dir / "src-candidate.md"
    candidate_json_path = artifacts_dir / "src-candidate.json"
    candidate_path.write_text(render_candidate_markdown(candidate), encoding="utf-8")
    write_json(candidate_json_path, candidate)
    write_json(
        artifacts_dir / "normalized-input.json",
        {
            "document": document,
            "intake_validation": intake_validation,
            "applied_patches": intake_patches,
        },
    )
    write_json(
        artifacts_dir / "input-validation.json",
        {
            "initial_validation": initial_input_validation,
            "patch_assessment": {
                "patchable_issue_codes": [item["code"] for item in input_patchable],
                "blocking_issue_codes": [item["code"] for item in input_blocking],
            },
            "applied_patches": input_patches,
            "revalidation": input_validation,
        },
    )
    write_json(
        artifacts_dir / "structural-report.json",
        {
            "issues": structural_issues,
            "applied_fixes": applied_fixes,
            "stages": [item for item in stage_results if item["role"] == "executor"],
            "structural_attempts": structural_attempts,
            "input_valid": input_validation["valid"],
            "intake_valid": intake_validation["valid"],
        },
    )
    write_json(artifacts_dir / "patch-lineage.json", build_patch_lineage(run_id, patch_events))
    execution = build_execution_evidence(
        run_id,
        input_path,
        [candidate_path],
        stage_results,
        {
            "input_validation": input_validation,
            "intake_validation": intake_validation,
            "structural_issues": structural_issues,
        },
        decisions,
        candidate["uncertainties"],
    )
    write_json(artifacts_dir / "execution-evidence.json", execution)

    return {
        "ok": True,
        "run_id": run_id,
        "artifacts_dir": str(artifacts_dir),
        "candidate_path": str(candidate_path),
        "structural_issues": structural_issues,
        "input_valid": input_validation["valid"],
        "intake_valid": intake_validation["valid"],
    }
