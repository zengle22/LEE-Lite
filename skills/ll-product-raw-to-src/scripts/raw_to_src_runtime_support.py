#!/usr/bin/env python3
"""
Support helpers for raw-to-src runtime validation and decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from raw_to_src_common import WORKFLOW_KEY, read_text, validate_candidate_markdown
from raw_to_src_records import SEMANTIC_BUDGET, STRUCTURAL_BUDGET, TOTAL_BUDGET


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = read_json(artifacts_dir / "execution-evidence.json")
    summary = read_json(artifacts_dir / "result-summary.json")
    actions = read_json(artifacts_dir / "proposed-next-actions.json")
    lines = [
        "# Raw To SRC Review Report",
        "",
        "## Run Summary",
        "",
        f"- run_id: {execution['run_id']}",
        f"- workflow: {WORKFLOW_KEY}",
        f"- input_ref: {execution['input_path']}",
        f"- primary_artifact_ref: {summary['primary_artifact_ref']}",
        "",
        "## Stage Results",
        "",
    ]
    lines.extend(f"- {item['stage_id']}: {item['status']}" for item in execution["stage_results"])
    lines.extend(["", "## Proposed Action", "", f"- action: {actions['recommended_action']}", f"- target_skill: {actions['recommended_target_skill']}"])
    if (artifacts_dir / "run-state.json").exists():
        run_state = read_json(artifacts_dir / "run-state.json")
        lines.extend(["", "## Run State", "", f"- current_state: {run_state['current_state']}"])
    report_path = artifacts_dir / "review-report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    required = [
        "package-manifest.json",
        "result-summary.json",
        "run-state.json",
        "patch-lineage.json",
        "src-candidate.json",
        "src-candidate.md",
        "semantic-inventory.json",
        "source-provenance-map.json",
        "contradiction-register.json",
        "normalization-decisions.json",
        "omission-and-compression-report.json",
        "source-semantic-findings.json",
        "acceptance-report.json",
        "defect-list.json",
        "retry-budget-report.json",
        "execution-evidence.json",
        "supervision-evidence.json",
        "proposed-next-actions.json",
    ]
    missing = [name for name in required if not (artifacts_dir / name).exists()]
    errors.extend(f"Missing artifact: {name}" for name in missing)
    candidate_errors, candidate_result = ([], {})
    if (artifacts_dir / "src-candidate.md").exists():
        candidate_errors, candidate_result = validate_candidate_markdown(artifacts_dir / "src-candidate.md")
        errors.extend(candidate_errors)
    if (artifacts_dir / "source-semantic-findings.json").exists() and (artifacts_dir / "acceptance-report.json").exists():
        semantic_findings = read_json(artifacts_dir / "source-semantic-findings.json")
        acceptance_report = read_json(artifacts_dir / "acceptance-report.json")
        if "findings" not in semantic_findings:
            errors.append("source-semantic-findings.json must contain findings.")
        if "acceptance_findings" not in acceptance_report:
            errors.append("acceptance-report.json must contain acceptance_findings.")
    if (artifacts_dir / "proposed-next-actions.json").exists():
        actions = read_json(artifacts_dir / "proposed-next-actions.json")
        if actions["recommended_action"] != "blocked" and not (artifacts_dir / "handoff-proposal.json").exists():
            errors.append("Missing handoff-proposal.json for non-blocked action.")
        if not (artifacts_dir / "job-proposal.json").exists():
            errors.append("Missing job-proposal.json.")
    result = {
        "valid": not errors,
        "artifacts_dir": str(artifacts_dir),
        "candidate": candidate_result,
        "errors": errors,
    }
    return errors, result


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    return not errors, errors


def freeze_guard(artifacts_dir: Path) -> tuple[bool, list[str]]:
    return validate_package_readiness(artifacts_dir)


def loop_budget_available(
    structural_attempts: list[dict[str, Any]],
    semantic_attempts: list[dict[str, Any]],
    loop_name: str,
) -> bool:
    total_attempts = len(structural_attempts) + len(semantic_attempts)
    if total_attempts >= TOTAL_BUDGET:
        return False
    if loop_name == "structural":
        return len(structural_attempts) < STRUCTURAL_BUDGET
    return len(semantic_attempts) < SEMANTIC_BUDGET


def determine_action(
    input_valid: bool,
    structural_issues: list[dict[str, Any]],
    semantic_defects: list[dict[str, Any]],
    structural_attempts: list[dict[str, Any]],
    semantic_attempts: list[dict[str, Any]],
    allow_update: bool,
) -> tuple[str, str, str, str]:
    if not input_valid:
        return "blocked", "blocked", "human.review.raw-to-src", "artifacts/jobs/failed/"
    defect_types = {item["type"] for item in semantic_defects}
    if "duplicate_title" in defect_types and not allow_update:
        return "blocked", "blocked", "human.review.raw-to-src", "artifacts/jobs/failed/"
    if structural_issues:
        if loop_budget_available(structural_attempts, semantic_attempts, "structural"):
            return "retry_proposed", "retry", "product.raw-to-src", "artifacts/jobs/ready/"
        return "blocked", "blocked", "human.review.raw-to-src", "artifacts/jobs/failed/"
    if semantic_defects:
        if loop_budget_available(structural_attempts, semantic_attempts, "semantic"):
            return "retry_proposed", "retry", "product.raw-to-src", "artifacts/jobs/ready/"
        return "human_handoff_proposed", "human_handoff", "human.review.raw-to-src", "artifacts/human-queue/waiting-human/"
    return "freeze_ready", "next_skill", "product.src-to-epic", "artifacts/jobs/ready/"
