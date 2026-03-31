#!/usr/bin/env python3
"""Candidate package assembly for feat-to-testset."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.workflow_revision import normalize_revision_context
from feat_to_testset_common import (
    dump_json,
    dump_yaml,
    ensure_list,
    normalize_semantic_lock,
    render_markdown,
    slugify,
    unique_strings,
)
from feat_to_testset_cli_integration import commit_bundle_markdown
from feat_to_testset_derivation import (
    build_gate_subjects,
    build_test_set_yaml,
    derive_analysis_markdown,
    derive_downstream_target_skill,
    derive_required_environment_inputs,
    derive_strategy_yaml,
)
from feat_to_testset_profiles import derive_semantic_lock
from feat_to_testset_semantics import build_semantic_drift_check

SUBJECT_FILE_NAMES = {
    "analysis_review": "analysis-review-subject.json",
    "strategy_review": "strategy-review-subject.json",
    "test_set_approval": "test-set-approval-subject.json",
}
ENVIRONMENT_INPUT_CATEGORIES = [
    "environment",
    "data",
    "services",
    "access",
    "feature_flags",
    "ui_or_integration_context",
]
SUPPORTED_DOWNSTREAM_SKILLS = {
    "skill.qa.test_exec_cli",
    "skill.qa.test_exec_web_e2e",
}
REQUIRED_OUTPUT_FILES = [
    "package-manifest.json",
    "test-set-bundle.md",
    "test-set-bundle.json",
    "test-set.yaml",
    "analysis.md",
    "strategy-draft.yaml",
    "test-set-review-report.json",
    "test-set-acceptance-report.json",
    "test-set-defect-list.json",
    "test-set-freeze-gate.json",
    "gate-subject-index.json",
    "analysis-review-subject.json",
    "strategy-review-subject.json",
    "test-set-approval-subject.json",
    "handoff-to-test-execution.json",
    "semantic-drift-check.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]


@dataclass
class GeneratedCandidatePackage:
    run_id: str
    bundle_frontmatter: dict[str, Any]
    bundle_body: str
    bundle_json: dict[str, Any]
    test_set_yaml: dict[str, Any]
    analysis_markdown: str
    strategy_yaml: dict[str, Any]
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    freeze_gate: dict[str, Any]
    gate_subject_index: dict[str, Any]
    gate_subjects: dict[str, dict[str, Any]]
    handoff: dict[str, Any]
    semantic_drift_check: dict[str, Any]
    execution_decisions: list[str]
    execution_uncertainties: list[str]
    revision_context: dict[str, Any] | None


def _format_field_list(label: str, values: list[str]) -> list[str]:
    return [f"- {label}:"] + [f"  - {item}" for item in values]


def _format_test_units(units: list[dict[str, Any]]) -> list[str]:
    lines = ["- test_units:"]
    for unit in units:
        acceptance_label = unit.get("acceptance_ref") or "(supplemental)"
        lines.extend(
            [
                f"  - `{unit.get('unit_ref')}` {unit.get('title')}",
                f"    acceptance_ref: `{acceptance_label}`",
                f"    priority: `{unit.get('priority')}`",
                f"    input_preconditions: {'; '.join(ensure_list(unit.get('input_preconditions')))}",
                f"    trigger_action: {unit.get('trigger_action')}",
                f"    observation_points: {'; '.join(ensure_list(unit.get('observation_points')))}",
                f"    pass_conditions: {'; '.join(ensure_list(unit.get('pass_conditions')))}",
                f"    required_evidence: {'; '.join(ensure_list(unit.get('required_evidence')))}",
            ]
        )
        if ensure_list(unit.get("derivation_basis")):
            lines.append(f"    derivation_basis: {'; '.join(ensure_list(unit.get('derivation_basis')))}")
    return lines


def _format_acceptance_traceability(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["- acceptance_traceability:"]
    for row in rows:
        lines.extend(
            [
                f"  - `{row.get('acceptance_ref')}` {row.get('acceptance_scenario')}",
                f"    unit_refs: {', '.join(ensure_list(row.get('unit_refs')))}",
                f"    given: {row.get('given')}",
                f"    when: {row.get('when')}",
                f"    then: {row.get('then')}",
                f"    coverage_status: {row.get('coverage_status')}",
            ]
        )
    return lines


def _format_qualification_fields(strategy_yaml: dict[str, Any]) -> list[str]:
    lines = ["- qualification:"]
    coverage_goal = strategy_yaml.get("coverage_goal") or {}
    if coverage_goal:
        lines.append("  - coverage_goal:")
        for key, value in coverage_goal.items():
            lines.append(f"    - {key}: {value}")
    lines.extend(
        [
            f"  - qualification_expectation: {strategy_yaml.get('qualification_expectation', '')}",
            f"  - qualification_budget: {strategy_yaml.get('qualification_budget')}",
            f"  - max_expansion_rounds: {strategy_yaml.get('max_expansion_rounds')}",
        ]
    )
    lines.extend(_format_field_list("branch_families", ensure_list(strategy_yaml.get("branch_families"))))
    lines.extend(_format_field_list("expansion_hints", ensure_list(strategy_yaml.get("expansion_hints"))))
    return lines


def _build_revision_context(revision_request: dict[str, Any] | None) -> dict[str, Any] | None:
    context = normalize_revision_context(revision_request)
    return context or None


def _build_candidate_context(package: Any, feature: dict[str, Any], run_id: str, revision_context: dict[str, Any] | None = None) -> dict[str, Any]:
    feature = dict(feature)
    feature["semantic_lock"] = derive_semantic_lock({**feature, "semantic_lock": feature.get("semantic_lock") or package.semantic_lock})
    test_set_yaml = build_test_set_yaml(feature, package.feat_json)
    if revision_context and revision_context.get("summary"):
        test_set_yaml["preconditions"] = unique_strings(ensure_list(test_set_yaml.get("preconditions")) + [f"Revision constraint: {revision_context['summary']}"])
    strategy_yaml = derive_strategy_yaml(feature, package.feat_json)
    analysis_markdown = derive_analysis_markdown(feature, package.feat_json, slugify(str(feature.get("title") or feature.get("feat_ref") or run_id)))
    gate_subjects = build_gate_subjects(run_id, str(feature.get("feat_ref") or ""))
    for subject in gate_subjects.values():
        subject["candidate_package_ref"] = "test-set-bundle.json"
    test_layers = ensure_list(test_set_yaml.get("test_layers"))
    required_environment_inputs = derive_required_environment_inputs(feature, test_layers)
    artifact_refs = {
        "test_set": "test-set.yaml",
        "analysis": "analysis.md",
        "strategy": "strategy-draft.yaml",
        "review_report": "test-set-review-report.json",
        "acceptance_report": "test-set-acceptance-report.json",
        "freeze_gate": "test-set-freeze-gate.json",
        "handoff": "handoff-to-test-execution.json",
        "bundle_markdown": "test-set-bundle.md",
        "bundle_json": "test-set-bundle.json",
        "gate_subject_index": "gate-subject-index.json",
        "defect_list": "test-set-defect-list.json",
    }
    gate_subject_refs = {gate_type: SUBJECT_FILE_NAMES[gate_type] for gate_type in SUBJECT_FILE_NAMES}
    return {
        "feature": feature,
        "test_set_yaml": test_set_yaml,
        "strategy_yaml": strategy_yaml,
        "analysis_markdown": analysis_markdown,
        "gate_subjects": gate_subjects,
        "test_layers": test_layers,
        "required_environment_inputs": required_environment_inputs,
        "artifact_refs": artifact_refs,
        "gate_subject_refs": gate_subject_refs,
        "source_refs": unique_strings(
            [f"product.epic-to-feat::{package.run_id}", str(feature.get("feat_ref") or "")] + ensure_list(feature.get("source_refs")) + ensure_list(package.feat_json.get("source_refs"))
        ),
        "downstream_skill": derive_downstream_target_skill(feature, test_layers),
        "test_set_ref": str(test_set_yaml.get("id") or ""),
        "revision_context": revision_context,
        "package": package,
    }


def _build_candidate_documents(run_id: str, context: dict[str, Any], revision_context: dict[str, Any] | None = None) -> dict[str, Any]:
    feature = context["feature"]
    test_set_yaml = context["test_set_yaml"]
    test_set_ref = context["test_set_ref"]
    review_report = {
        "report_id": f"test-set-review-{run_id}",
        "report_type": "test_set_review",
        "workflow_key": "qa.feat-to-testset",
        "workflow_run_id": run_id,
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "status": "pending",
        "decision": "pending",
        "summary": "Pending supervisor review for analysis and strategy quality.",
        "findings": [],
        "created_at": derive_now(),
        **({"revision_context": revision_context} if revision_context else {}),
    }
    acceptance_report = {
        "report_id": f"test-set-acceptance-{run_id}",
        "report_type": "test_set_acceptance_review",
        "workflow_key": "qa.feat-to-testset",
        "workflow_run_id": run_id,
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "status": "pending",
        "decision": "pending",
        "summary": "Pending supervisor acceptance review.",
        "acceptance_findings": [],
        "created_at": derive_now(),
        **({"revision_context": revision_context} if revision_context else {}),
    }
    freeze_gate = {
        "gate_id": f"test-set-freeze-gate-{run_id}",
        "workflow_key": "qa.feat-to-testset",
        "workflow_run_id": run_id,
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "status": "pending",
        "decision": "pending",
        "freeze_ready": False,
        "ready_for_external_approval": False,
        "checks": {
            "test_set_present": True,
            "analysis_present": True,
            "strategy_present": True,
            "gate_subjects_present": True,
            "handoff_present": True,
            "required_environment_inputs_present": True,
        },
        "created_at": derive_now(),
        **({"revision_context": revision_context} if revision_context else {}),
    }
    gate_subjects = context["gate_subjects"]
    handoff = {
        "handoff_id": f"handoff-{run_id}-to-test-execution",
        "from_skill": "ll-qa-feat-to-testset",
        "source_run_id": run_id,
        "target_skill": context["downstream_skill"],
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "package_ref": "test-set-bundle.json",
        "primary_artifact_ref": "test-set.yaml",
        "supporting_artifact_refs": [
            "analysis.md",
            "strategy-draft.yaml",
            "test-set-review-report.json",
            "test-set-acceptance-report.json",
            "test-set-freeze-gate.json",
            "test-set-bundle.md",
            "test-set-bundle.json",
        ],
        "required_environment_inputs": context["required_environment_inputs"],
        "created_at": derive_now(),
        **({"revision_context": revision_context} if revision_context else {}),
    }
    return {
        "review_report": review_report,
        "acceptance_report": acceptance_report,
        "freeze_gate": freeze_gate,
        "handoff": handoff,
        "gate_subjects": gate_subjects,
    }


def _build_candidate_package_body(context: dict[str, Any], documents: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    feature = context["feature"]
    test_set_yaml = context["test_set_yaml"]
    strategy_yaml = context["strategy_yaml"]
    test_set_ref = context["test_set_ref"]
    downstream_skill = context["downstream_skill"]
    artifact_refs = context["artifact_refs"]
    gate_subject_refs = context["gate_subject_refs"]
    gate_subjects = documents["gate_subjects"]
    handoff = documents["handoff"]
    review_report = documents["review_report"]
    acceptance_report = documents["acceptance_report"]
    freeze_gate = documents["freeze_gate"]
    source_refs = context["source_refs"]
    test_units = [unit for unit in (test_set_yaml.get("test_units") or []) if isinstance(unit, dict)]
    traceability_rows = [row for row in (test_set_yaml.get("acceptance_traceability") or []) if isinstance(row, dict)]
    traceability_lines = [f"- acceptance `{row.get('acceptance_ref')}` `{row.get('acceptance_scenario')}` -> {', '.join(ensure_list(row.get('unit_refs')))}" for row in traceability_rows]
    gate_subject_lines = [f"- `{subject['gate_type']}`: `{subject['subject_id']}` -> `{SUBJECT_FILE_NAMES[subject['gate_type']]}`" for subject in gate_subjects.values()]
    bundle_json = {
        "artifact_type": "test_set_candidate_package",
        "workflow_key": "qa.feat-to-testset",
        "workflow_run_id": context["package"].run_id,
        "title": f"{feature.get('title')} TESTSET Candidate Package",
        "status": "in_progress",
        "schema_version": "1.0.0",
        "package_role": "candidate",
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "derived_slug": slugify(str(feature.get("title") or feature.get("feat_ref") or context["package"].run_id)),
        "epic_ref": test_set_yaml.get("epic_ref"),
        "src_ref": test_set_yaml.get("src_ref"),
        "source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
        "coverage_goal": test_set_yaml.get("coverage_goal", {}),
        "branch_families": test_set_yaml.get("branch_families", []),
        "expansion_hints": test_set_yaml.get("expansion_hints", []),
        "qualification_expectation": test_set_yaml.get("qualification_expectation", ""),
        "qualification_budget": test_set_yaml.get("qualification_budget"),
        "max_expansion_rounds": test_set_yaml.get("max_expansion_rounds"),
        "artifact_refs": artifact_refs,
        "gate_subject_refs": gate_subject_refs,
        "downstream_target": downstream_skill,
        **({"revision_context": context["revision_context"]} if context.get("revision_context") else {}),
    }
    bundle_frontmatter = {
        key: bundle_json[key]
        for key in [
            "artifact_type",
            "workflow_key",
            "workflow_run_id",
            "status",
            "package_role",
            "schema_version",
            "feat_ref",
            "test_set_ref",
            "derived_slug",
            "source_refs",
            "semantic_lock",
        ]
    }
    if context.get("revision_context"):
        bundle_frontmatter["revision_request_ref"] = context["revision_context"].get("revision_request_ref", "")
        bundle_frontmatter["revision_summary"] = context["revision_context"].get("summary", "")
    bundle_body = "\n\n".join(
        [
            f"# {bundle_json['title']}",
            "## Selected FEAT\n\n" + "\n".join([f"- feat_ref: `{feature.get('feat_ref')}`", f"- title: {feature.get('title')}", f"- goal: {feature.get('goal')}", f"- epic_ref: `{test_set_yaml.get('epic_ref')}`", f"- src_ref: `{test_set_yaml.get('src_ref')}`"]),
            "## Requirement Analysis\n\n" + "\n".join(_format_field_list("coverage_scope", ensure_list(test_set_yaml.get("coverage_scope"))) + _format_field_list("risk_focus", ensure_list(test_set_yaml.get("risk_focus"))) + _format_field_list("preconditions", ensure_list(test_set_yaml.get("preconditions"))) + _format_field_list("coverage_exclusions", ensure_list(test_set_yaml.get("coverage_exclusions")))),
            "## Strategy Draft\n\n" + "\n".join(
                [f"- priority: {strategy_yaml.get('priority')}"]
                + _format_field_list("test_layers", ensure_list(strategy_yaml.get("test_layers")))
                + _format_qualification_fields(strategy_yaml)
                + _format_test_units(test_units)
            ),
            "## TESTSET\n\n" + "\n".join([f"- main_object: `{test_set_ref}`", f"- file: `{artifact_refs['test_set']}`", f"- status: `{test_set_yaml.get('status')}`", f"- environment_assumptions_count: {len(ensure_list(test_set_yaml.get('environment_assumptions')))}", f"- pass_criteria_count: {len(ensure_list(test_set_yaml.get('pass_criteria')))}", f"- evidence_required_count: {len(ensure_list(test_set_yaml.get('evidence_required')))}", "- only `test-set.yaml` is the formal main object; companion artifacts remain subordinate evidence.", "- main_object_fields:", "  - coverage_scope", "  - risk_focus", "  - preconditions", "  - environment_assumptions", "  - test_layers", "  - test_units", "  - coverage_exclusions", "  - pass_criteria", "  - evidence_required", "  - acceptance_traceability", "  - source_refs", "  - governing_adrs", "  - status", "- environment_assumptions:", *[f"  - {item}" for item in ensure_list(test_set_yaml.get("environment_assumptions"))], "- pass_criteria:", *[f"  - {item}" for item in ensure_list(test_set_yaml.get("pass_criteria"))], "- evidence_required:", *[f"  - {item}" for item in ensure_list(test_set_yaml.get("evidence_required"))]]),
            "## Gate Subjects\n\n" + "\n".join(gate_subject_lines),
            "## Downstream Handoff\n\n" + "\n".join([f"- target_skill: `{downstream_skill}`", f"- package_ref: `{handoff['package_ref']}`", "- required_environment_inputs:", *[f"  - {category}: {', '.join(ensure_list(values))}" for category, values in context["required_environment_inputs"].items()]]),
            "## Traceability\n\n" + "\n".join(traceability_lines + _format_acceptance_traceability(traceability_rows)),
        ]
    )
    gate_subject_index = {
        "workflow_key": "qa.feat-to-testset",
        "workflow_run_id": context["package"].run_id,
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "subjects": {gate_type: {"subject_id": gate_subjects[gate_type]["subject_id"], "artifact_ref": gate_subjects[gate_type]["artifact_ref"], "subject_file": gate_subject_refs[gate_type]} for gate_type in gate_subject_refs},
    }
    semantic_drift_check = build_semantic_drift_check(feature, bundle_json, test_set_yaml)
    return bundle_json, bundle_frontmatter, bundle_body, {
        "review_report": review_report,
        "acceptance_report": acceptance_report,
        "freeze_gate": freeze_gate,
        "handoff": handoff,
        "gate_subject_index": gate_subject_index,
        "semantic_drift_check": semantic_drift_check,
        "gate_subjects": gate_subjects,
    }


def build_candidate_package(
    package: Any,
    feature: dict[str, Any],
    feat_ref: str,
    run_id: str,
    revision_request: dict[str, Any] | None = None,
) -> GeneratedCandidatePackage:
    del feat_ref
    revision_context = _build_revision_context(revision_request)
    context = _build_candidate_context(package, feature, run_id, revision_context)
    documents = _build_candidate_documents(run_id, context, revision_context)
    bundle_json, bundle_frontmatter, bundle_body, payload = _build_candidate_package_body(context, documents)
    defect_list: list[dict[str, Any]] = []
    if payload["semantic_drift_check"]["verdict"] == "reject":
        defect_list.append({"severity": "P1", "title": "semantic_lock drift detected", "detail": payload["semantic_drift_check"]["summary"]})
    execution_decisions = [
        f"Selected FEAT {context['feature'].get('feat_ref')} from upstream run {package.run_id}.",
        f"Derived TESTSET main object {context['test_set_ref']}.",
        "Kept analysis and strategy as companion artifacts, not parallel SSOT objects.",
        f"Prepared downstream handoff to {context['downstream_skill']}.",
    ]
    if revision_context and revision_context.get("summary"):
        execution_decisions.append(f"Applied revision context: {revision_context['summary']}")
    execution_uncertainties = []
    if not ensure_list(context["test_set_yaml"].get("governing_adrs")):
        execution_uncertainties.append("No governing ADR refs were inherited into the TESTSET candidate package.")
    return GeneratedCandidatePackage(
        run_id=run_id,
        bundle_frontmatter=bundle_frontmatter,
        bundle_body=bundle_body,
        bundle_json=bundle_json,
        test_set_yaml=context["test_set_yaml"],
        analysis_markdown=context["analysis_markdown"],
        strategy_yaml=context["strategy_yaml"],
        review_report=documents["review_report"],
        acceptance_report=documents["acceptance_report"],
        defect_list=defect_list,
        freeze_gate=documents["freeze_gate"],
        gate_subject_index=payload["gate_subject_index"],
        gate_subjects=payload["gate_subjects"],
        handoff=documents["handoff"],
        semantic_drift_check=payload["semantic_drift_check"],
        execution_decisions=execution_decisions,
        execution_uncertainties=execution_uncertainties,
        revision_context=revision_context,
    )


def write_executor_outputs(output_dir, repo_root, package, generated: GeneratedCandidatePackage, command_name: str) -> None:
    revision_context = generated.revision_context or generated.bundle_json.get("revision_context") or {}
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_markdown = render_markdown(generated.bundle_frontmatter, generated.bundle_body)
    (output_dir / "test-set-bundle.md").write_text(bundle_markdown, encoding="utf-8")
    cli_commit = commit_bundle_markdown(repo_root, output_dir, generated.run_id, bundle_markdown, "test-set-bundle-executor-commit")
    dump_json(output_dir / "test-set-bundle.json", generated.bundle_json)
    dump_yaml(output_dir / "test-set.yaml", generated.test_set_yaml)
    (output_dir / "analysis.md").write_text(generated.analysis_markdown.strip() + "\n", encoding="utf-8")
    dump_yaml(output_dir / "strategy-draft.yaml", generated.strategy_yaml)
    dump_json(output_dir / "test-set-review-report.json", generated.review_report)
    dump_json(output_dir / "test-set-acceptance-report.json", generated.acceptance_report)
    dump_json(output_dir / "test-set-defect-list.json", generated.defect_list)
    dump_json(output_dir / "test-set-freeze-gate.json", generated.freeze_gate)
    dump_json(output_dir / "gate-subject-index.json", generated.gate_subject_index)
    dump_json(output_dir / "semantic-drift-check.json", generated.semantic_drift_check)
    for gate_type, payload in generated.gate_subjects.items():
        dump_json(output_dir / SUBJECT_FILE_NAMES[gate_type], payload)
    dump_json(output_dir / "handoff-to-test-execution.json", generated.handoff)
    dump_json(
        output_dir / "package-manifest.json",
        {
            "run_id": generated.run_id,
            "workflow_key": "qa.feat-to-testset",
            "artifacts_dir": str(output_dir),
            "input_artifacts_dir": str(package.artifacts_dir),
            "feat_ref": generated.bundle_json["feat_ref"],
            "test_set_ref": generated.bundle_json["test_set_ref"],
            "status": generated.bundle_json["status"],
            "primary_artifact_ref": str(output_dir / "test-set.yaml"),
            "candidate_package_ref": str(output_dir / "test-set-bundle.json"),
            "review_report_ref": str(output_dir / "test-set-review-report.json"),
            "acceptance_report_ref": str(output_dir / "test-set-acceptance-report.json"),
            "defect_list_ref": str(output_dir / "test-set-defect-list.json"),
            "freeze_gate_ref": str(output_dir / "test-set-freeze-gate.json"),
            "handoff_ref": str(output_dir / "handoff-to-test-execution.json"),
            "semantic_drift_check_ref": str(output_dir / "semantic-drift-check.json"),
            "execution_evidence_ref": str(output_dir / "execution-evidence.json"),
            "supervision_evidence_ref": str(output_dir / "supervision-evidence.json"),
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
    dump_json(
        output_dir / "execution-evidence.json",
        {
            "skill_id": "ll-qa-feat-to-testset",
            "run_id": generated.run_id,
            "role": "executor",
            "inputs": [str(package.artifacts_dir), generated.bundle_json["feat_ref"]],
            "outputs": [str(output_dir / name) for name in REQUIRED_OUTPUT_FILES if name != "supervision-evidence.json"],
            "commands_run": [command_name],
            "structural_results": {
                "input_validation": "pass",
                "candidate_package_emitted": True,
                "test_set_present": True,
                "gate_subjects_present": True,
                "required_environment_inputs_present": True,
                "semantic_lock_present": bool(generated.bundle_json.get("semantic_lock")),
                "semantic_lock_preserved": generated.semantic_drift_check.get("semantic_lock_preserved", True),
                "cli_executor_commit_ref": str(cli_commit["response_path"]),
                "cli_executor_receipt_ref": cli_commit["response"]["data"].get("receipt_ref", ""),
                "cli_executor_registry_record_ref": cli_commit["response"]["data"].get("registry_record_ref", ""),
            },
            "key_decisions": generated.execution_decisions,
            "uncertainties": generated.execution_uncertainties,
            **({"revision_context": revision_context} if revision_context else {}),
        },
    )
    dump_json(
        output_dir / "supervision-evidence.json",
        {
            "skill_id": "ll-qa-feat-to-testset",
            "run_id": generated.run_id,
            "role": "supervisor",
            "reviewed_inputs": [str(output_dir / "test-set-bundle.md"), str(output_dir / "test-set-bundle.json")],
            "reviewed_outputs": [str(output_dir / "test-set.yaml")],
            "semantic_findings": [],
            "decision": "revise",
            "reason": "Pending supervisor review.",
            **({"revision_context": revision_context} if revision_context else {}),
        },
    )


def derive_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
