#!/usr/bin/env python3
"""
Lite-native runtime support for feat-to-testset.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from feat_to_testset_common import (
    dump_json,
    dump_yaml,
    ensure_list,
    find_feature,
    guess_repo_root_from_input,
    load_feat_package,
    load_json,
    normalize_semantic_lock,
    parse_markdown_frontmatter,
    render_markdown,
    slugify,
    unique_strings,
    validate_input_package,
)
from feat_to_testset_derivation import (
    build_gate_subjects,
    build_test_set_yaml,
    derive_analysis_markdown,
    derive_downstream_target_skill,
    derive_required_environment_inputs,
    derive_strategy_yaml,
)


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
REQUIRED_MARKDOWN_HEADINGS = [
    "Selected FEAT",
    "Requirement Analysis",
    "Strategy Draft",
    "TESTSET",
    "Gate Subjects",
    "Downstream Handoff",
    "Traceability",
]
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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "feat-to-testset" / run_id


def yaml_load(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


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


def build_semantic_drift_check(feature: dict[str, Any], bundle_json: dict[str, Any], test_set_yaml: dict[str, Any]) -> dict[str, Any]:
    lock = normalize_semantic_lock(feature.get("semantic_lock"))
    if not lock:
        return {
            "verdict": "not_applicable",
            "semantic_lock_present": False,
            "semantic_lock_preserved": True,
            "forbidden_axis_detected": [],
            "anchor_matches": [],
            "summary": "No semantic_lock present.",
        }

    generated_text = " ".join(
        [
            str(bundle_json.get("title") or ""),
            str(feature.get("title") or ""),
            " ".join(ensure_list(test_set_yaml.get("coverage_scope"))),
            " ".join(ensure_list(test_set_yaml.get("risk_focus"))),
            " ".join(ensure_list(test_set_yaml.get("pass_criteria"))),
            " ".join(str(unit.get("title") or "") for unit in ensure_list(test_set_yaml.get("test_units")) if isinstance(unit, dict)),
        ]
    ).lower()
    forbidden_hits = [item for item in lock.get("forbidden_capabilities", []) if str(item).strip().lower() in generated_text]
    anchor_matches: list[str] = []
    token_groups = {
        "domain_type": [str(lock.get("domain_type") or "").replace("_", " ").lower()],
        "primary_object": [token for token in str(lock.get("primary_object") or "").replace("_", " ").lower().split() if token],
        "lifecycle_stage": [token for token in str(lock.get("lifecycle_stage") or "").replace("_", " ").lower().split() if token],
    }
    for label, tokens in token_groups.items():
        if tokens and all(token in generated_text for token in tokens):
            anchor_matches.append(label)
    if str(lock.get("domain_type") or "").strip().lower() == "review_projection_rule":
        axis_id = str(feature.get("axis_id") or "").strip().lower()
        if axis_id in {"projection-generation", "authoritative-snapshot", "review-focus-risk", "feedback-writeback"}:
            anchor_matches.append("review_projection_axis")
        review_projection_tokens = ["projection", "gate", "ssot"]
        if all(token in generated_text for token in review_projection_tokens):
            anchor_matches.append("review_projection_signature")
    preserved = not forbidden_hits and len(anchor_matches) >= 1
    return {
        "verdict": "pass" if preserved else "reject",
        "semantic_lock_present": True,
        "semantic_lock_preserved": preserved,
        "domain_type": lock.get("domain_type"),
        "one_sentence_truth": lock.get("one_sentence_truth"),
        "forbidden_axis_detected": forbidden_hits,
        "anchor_matches": anchor_matches,
        "summary": "semantic_lock preserved." if preserved else "semantic_lock drift detected.",
    }


def build_candidate_package(package: Any, feature: dict[str, Any], feat_ref: str, run_id: str) -> GeneratedCandidatePackage:
    del feat_ref
    feature = dict(feature)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)
    derived_slug = slugify(str(feature.get("title") or feature.get("feat_ref") or run_id))
    test_set_yaml = build_test_set_yaml(feature, package.feat_json)
    strategy_yaml = derive_strategy_yaml(feature, package.feat_json)
    analysis_markdown = derive_analysis_markdown(feature, package.feat_json, derived_slug)
    gate_subjects = build_gate_subjects(run_id, str(feature.get("feat_ref") or ""))
    for subject in gate_subjects.values():
        subject["candidate_package_ref"] = "test-set-bundle.json"

    source_refs = unique_strings(
        [f"product.epic-to-feat::{package.run_id}", str(feature.get("feat_ref") or "")]
        + ensure_list(feature.get("source_refs"))
        + ensure_list(package.feat_json.get("source_refs"))
    )
    test_layers = ensure_list(test_set_yaml.get("test_layers"))
    downstream_skill = derive_downstream_target_skill(feature, test_layers)
    required_environment_inputs = derive_required_environment_inputs(feature, test_layers)
    test_set_ref = str(test_set_yaml.get("id") or "")
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
    gate_subject_refs = {
        gate_type: SUBJECT_FILE_NAMES[gate_type] for gate_type in SUBJECT_FILE_NAMES
    }

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
        "created_at": utc_now(),
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
        "created_at": utc_now(),
    }
    defect_list: list[dict[str, Any]] = []
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
        "created_at": utc_now(),
    }

    handoff = {
        "handoff_id": f"handoff-{run_id}-to-test-execution",
        "from_skill": "ll-qa-feat-to-testset",
        "source_run_id": run_id,
        "target_skill": downstream_skill,
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
        "required_environment_inputs": required_environment_inputs,
        "created_at": utc_now(),
    }

    bundle_json = {
        "artifact_type": "test_set_candidate_package",
        "workflow_key": "qa.feat-to-testset",
        "workflow_run_id": run_id,
        "title": f"{feature.get('title')} TESTSET Candidate Package",
        "status": "in_progress",
        "schema_version": "1.0.0",
        "package_role": "candidate",
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "derived_slug": derived_slug,
        "epic_ref": test_set_yaml.get("epic_ref"),
        "src_ref": test_set_yaml.get("src_ref"),
        "source_refs": source_refs,
        "semantic_lock": feature["semantic_lock"],
        "artifact_refs": artifact_refs,
        "gate_subject_refs": gate_subject_refs,
        "downstream_target": downstream_skill,
    }
    bundle_frontmatter = {
        "artifact_type": bundle_json["artifact_type"],
        "workflow_key": bundle_json["workflow_key"],
        "workflow_run_id": bundle_json["workflow_run_id"],
        "status": bundle_json["status"],
        "package_role": bundle_json["package_role"],
        "schema_version": bundle_json["schema_version"],
        "feat_ref": bundle_json["feat_ref"],
        "test_set_ref": bundle_json["test_set_ref"],
        "derived_slug": bundle_json["derived_slug"],
        "source_refs": bundle_json["source_refs"],
        "semantic_lock": bundle_json["semantic_lock"],
    }
    test_units = [
        unit for unit in (test_set_yaml.get("test_units") or []) if isinstance(unit, dict)
    ]
    traceability_rows = [
        row for row in (test_set_yaml.get("acceptance_traceability") or []) if isinstance(row, dict)
    ]
    traceability_lines = [
        f"- acceptance `{row.get('acceptance_ref')}` `{row.get('acceptance_scenario')}` -> {', '.join(ensure_list(row.get('unit_refs')))}"
        for row in traceability_rows
    ]
    gate_subject_lines = [
        f"- `{subject['gate_type']}`: `{subject['subject_id']}` -> `{SUBJECT_FILE_NAMES[subject['gate_type']]}`"
        for subject in gate_subjects.values()
    ]
    bundle_body = "\n\n".join(
        [
            f"# {bundle_json['title']}",
            "## Selected FEAT\n\n"
            + "\n".join(
                [
                    f"- feat_ref: `{feature.get('feat_ref')}`",
                    f"- title: {feature.get('title')}",
                    f"- goal: {feature.get('goal')}",
                    f"- epic_ref: `{test_set_yaml.get('epic_ref')}`",
                    f"- src_ref: `{test_set_yaml.get('src_ref')}`",
                ]
            ),
            "## Requirement Analysis\n\n"
            + "\n".join(
                _format_field_list("coverage_scope", ensure_list(test_set_yaml.get("coverage_scope")))
                + _format_field_list("risk_focus", ensure_list(test_set_yaml.get("risk_focus")))
                + _format_field_list("preconditions", ensure_list(test_set_yaml.get("preconditions")))
                + _format_field_list("coverage_exclusions", ensure_list(test_set_yaml.get("coverage_exclusions")))
            ),
            "## Strategy Draft\n\n"
            + "\n".join(
                [f"- priority: {strategy_yaml.get('priority')}"]
                + _format_field_list("test_layers", ensure_list(strategy_yaml.get("test_layers")))
                + _format_test_units(test_units)
            ),
            "## TESTSET\n\n"
            + "\n".join(
                [
                    f"- main_object: `{test_set_ref}`",
                    f"- file: `{artifact_refs['test_set']}`",
                    f"- status: `{test_set_yaml.get('status')}`",
                    f"- environment_assumptions_count: {len(ensure_list(test_set_yaml.get('environment_assumptions')))}",
                    f"- pass_criteria_count: {len(ensure_list(test_set_yaml.get('pass_criteria')))}",
                    f"- evidence_required_count: {len(ensure_list(test_set_yaml.get('evidence_required')))}",
                    "- only `test-set.yaml` is the formal main object; companion artifacts remain subordinate evidence.",
                    "- main_object_fields:",
                    "  - coverage_scope",
                    "  - risk_focus",
                    "  - preconditions",
                    "  - environment_assumptions",
                    "  - test_layers",
                    "  - test_units",
                    "  - coverage_exclusions",
                    "  - pass_criteria",
                    "  - evidence_required",
                    "  - acceptance_traceability",
                    "  - source_refs",
                    "  - governing_adrs",
                    "  - status",
                    "- environment_assumptions:",
                    *[f"  - {item}" for item in ensure_list(test_set_yaml.get("environment_assumptions"))],
                    "- pass_criteria:",
                    *[f"  - {item}" for item in ensure_list(test_set_yaml.get("pass_criteria"))],
                    "- evidence_required:",
                    *[f"  - {item}" for item in ensure_list(test_set_yaml.get("evidence_required"))],
                ]
            ),
            "## Gate Subjects\n\n" + "\n".join(gate_subject_lines),
            "## Downstream Handoff\n\n"
            + "\n".join(
                [
                    f"- target_skill: `{downstream_skill}`",
                    f"- package_ref: `{handoff['package_ref']}`",
                    "- required_environment_inputs:",
                    *[
                        f"  - {category}: {', '.join(ensure_list(values))}"
                        for category, values in required_environment_inputs.items()
                    ],
                ]
            ),
            "## Traceability\n\n"
            + "\n".join(traceability_lines + _format_acceptance_traceability(traceability_rows)),
        ]
    )
    gate_subject_index = {
        "workflow_key": "qa.feat-to-testset",
        "workflow_run_id": run_id,
        "feat_ref": feature.get("feat_ref"),
        "test_set_ref": test_set_ref,
        "subjects": {
            gate_type: {
                "subject_id": gate_subjects[gate_type]["subject_id"],
                "artifact_ref": gate_subjects[gate_type]["artifact_ref"],
                "subject_file": gate_subject_refs[gate_type],
            }
            for gate_type in gate_subject_refs
        },
    }
    semantic_drift_check = build_semantic_drift_check(feature, bundle_json, test_set_yaml)
    if semantic_drift_check["verdict"] == "reject":
        defect_list.append(
            {
                "severity": "P1",
                "title": "semantic_lock drift detected",
                "detail": semantic_drift_check["summary"],
            }
        )

    execution_decisions = [
        f"Selected FEAT {feature.get('feat_ref')} from upstream run {package.run_id}.",
        f"Derived TESTSET main object {test_set_ref}.",
        "Kept analysis and strategy as companion artifacts, not parallel SSOT objects.",
        f"Prepared downstream handoff to {downstream_skill}.",
    ]
    execution_uncertainties = []
    if not ensure_list(test_set_yaml.get("governing_adrs")):
        execution_uncertainties.append("No governing ADR refs were inherited into the TESTSET candidate package.")

    return GeneratedCandidatePackage(
        run_id=run_id,
        bundle_frontmatter=bundle_frontmatter,
        bundle_body=bundle_body,
        bundle_json=bundle_json,
        test_set_yaml=test_set_yaml,
        analysis_markdown=analysis_markdown,
        strategy_yaml=strategy_yaml,
        review_report=review_report,
        acceptance_report=acceptance_report,
        defect_list=defect_list,
        freeze_gate=freeze_gate,
        gate_subject_index=gate_subject_index,
        gate_subjects=gate_subjects,
        handoff=handoff,
        semantic_drift_check=semantic_drift_check,
        execution_decisions=execution_decisions,
        execution_uncertainties=execution_uncertainties,
    )


def write_executor_outputs(output_dir: Path, package: Any, generated: GeneratedCandidatePackage, command_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "test-set-bundle.md").write_text(
        render_markdown(generated.bundle_frontmatter, generated.bundle_body),
        encoding="utf-8",
    )
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
            },
            "key_decisions": generated.execution_decisions,
            "uncertainties": generated.execution_uncertainties,
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
        },
    )


def _build_findings(test_set_yaml: dict[str, Any], handoff: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not ensure_list(test_set_yaml.get("governing_adrs")):
        findings.append(
            {
                "severity": "P2",
                "title": "No governing ADR refs were inherited",
                "detail": "The candidate package is usable, but governing ADR lineage should be made explicit when available.",
            }
        )
    required_inputs = handoff.get("required_environment_inputs") or {}
    for category in ENVIRONMENT_INPUT_CATEGORIES:
        if not ensure_list(required_inputs.get(category)):
            findings.append(
                {
                    "severity": "P1",
                    "title": f"Missing required environment input category: {category}",
                    "detail": "Downstream execution handoff must cover all required environment input categories.",
                }
            )
    return findings


def build_supervision_evidence(artifacts_dir: Path) -> dict[str, Any]:
    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    handoff = load_json(artifacts_dir / "handoff-to-test-execution.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    findings = _build_findings(test_set_yaml, handoff)
    if semantic_drift_check.get("semantic_lock_present") and semantic_drift_check.get("semantic_lock_preserved") is not True:
        findings.append(
            {
                "severity": "P1",
                "title": "semantic_lock drift detected",
                "detail": str(semantic_drift_check.get("summary") or "semantic_lock drift detected."),
            }
        )
    blocking = [item for item in findings if str(item.get("severity") or "") in {"P0", "P1"}]
    decision = "pass" if not blocking else "revise"
    return {
        "skill_id": "ll-qa-feat-to-testset",
        "run_id": str(bundle_json.get("workflow_run_id") or artifacts_dir.name),
        "role": "supervisor",
        "reviewed_inputs": [str(artifacts_dir / "analysis.md"), str(artifacts_dir / "strategy-draft.yaml")],
        "reviewed_outputs": [
            str(artifacts_dir / "test-set.yaml"),
            str(artifacts_dir / "test-set-bundle.json"),
            str(artifacts_dir / "handoff-to-test-execution.json"),
        ],
        "semantic_findings": findings,
        "decision": decision,
        "reason": (
            "TESTSET candidate package is ready for external approval handoff."
            if decision == "pass"
            else "TESTSET candidate package requires revision before external approval."
        ),
    }


def update_supervisor_outputs(artifacts_dir: Path, supervision: dict[str, Any]) -> None:
    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    review_report = load_json(artifacts_dir / "test-set-review-report.json")
    acceptance_report = load_json(artifacts_dir / "test-set-acceptance-report.json")
    freeze_gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    blocking = [item for item in supervision.get("semantic_findings") or [] if str(item.get("severity") or "") in {"P0", "P1"}]
    passed = supervision.get("decision") == "pass"

    manifest_status = "approval_pending" if passed else "review_pending"
    test_set_status = "approved" if passed else "review_ready"
    gate_status = "pending" if passed else "failed"
    gate_decision = "pending" if passed else "revise"

    bundle_json["status"] = manifest_status
    manifest["status"] = manifest_status
    test_set_yaml["status"] = test_set_status

    review_report.update(
        {
            "status": "completed",
            "decision": "pass" if passed else "revise",
            "summary": (
                "Analysis and strategy review passed."
                if passed
                else "Analysis and strategy review requires revision."
            ),
            "findings": supervision.get("semantic_findings") or [],
            "updated_at": utc_now(),
        }
    )
    acceptance_report.update(
        {
            "status": "completed",
            "decision": "approve" if passed else "revise",
            "summary": (
                "TESTSET content satisfies external approval entry conditions."
                if passed
                else "TESTSET content does not yet satisfy external approval entry conditions."
            ),
            "acceptance_findings": blocking,
            "updated_at": utc_now(),
        }
    )
    freeze_gate.update(
        {
            "status": gate_status,
            "decision": gate_decision,
            "freeze_ready": False,
            "ready_for_external_approval": passed,
            "checks": {
                "test_set_present": True,
                "analysis_present": True,
                "strategy_present": True,
                "gate_subjects_present": True,
                "handoff_present": True,
                "required_environment_inputs_present": not blocking,
                "semantic_lock_preserved": semantic_drift_check.get("semantic_lock_preserved", True),
            },
            "updated_at": utc_now(),
        }
    )

    markdown_text = (artifacts_dir / "test-set-bundle.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    frontmatter["status"] = manifest_status
    (artifacts_dir / "test-set-bundle.md").write_text(render_markdown(frontmatter, body), encoding="utf-8")

    dump_json(artifacts_dir / "test-set-bundle.json", bundle_json)
    dump_yaml(artifacts_dir / "test-set.yaml", test_set_yaml)
    dump_json(artifacts_dir / "test-set-review-report.json", review_report)
    dump_json(artifacts_dir / "test-set-acceptance-report.json", acceptance_report)
    dump_json(artifacts_dir / "test-set-defect-list.json", supervision.get("semantic_findings") or [])
    dump_json(artifacts_dir / "test-set-freeze-gate.json", freeze_gate)
    dump_json(artifacts_dir / "supervision-evidence.json", supervision)
    dump_json(artifacts_dir / "package-manifest.json", manifest)


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_OUTPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required output artifact: {required_file}")
    if errors:
        return errors, {"valid": False}

    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    freeze_gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    handoff = load_json(artifacts_dir / "handoff-to-test-execution.json")
    semantic_drift_check = load_json(artifacts_dir / "semantic-drift-check.json")

    if bundle_json.get("artifact_type") != "test_set_candidate_package":
        errors.append("test-set-bundle.json artifact_type must be test_set_candidate_package.")
    if bundle_json.get("workflow_key") != "qa.feat-to-testset":
        errors.append("test-set-bundle.json workflow_key must be qa.feat-to-testset.")
    if bundle_json.get("package_role") != "candidate":
        errors.append("test-set-bundle.json package_role must be candidate.")

    source_refs = ensure_list(bundle_json.get("source_refs"))
    if not any(ref.startswith("product.epic-to-feat::") for ref in source_refs):
        errors.append("test-set-bundle.json source_refs must include product.epic-to-feat::<run_id>.")
    if not any(ref.startswith("FEAT-") for ref in source_refs):
        errors.append("test-set-bundle.json source_refs must include FEAT-*.")
    if not any(ref.startswith("EPIC-") for ref in source_refs):
        errors.append("test-set-bundle.json source_refs must include EPIC-*.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("test-set-bundle.json source_refs must include SRC-*.")

    if test_set_yaml.get("ssot_type") != "TESTSET":
        errors.append("test-set.yaml ssot_type must be TESTSET.")
    if test_set_yaml.get("workflow_key") != "qa.feat-to-testset":
        errors.append("test-set.yaml workflow_key must be qa.feat-to-testset.")
    test_units = test_set_yaml.get("test_units") or []
    acceptance_traceability = test_set_yaml.get("acceptance_traceability") or []
    if not isinstance(test_units, list) or not test_units:
        errors.append("test-set.yaml must contain non-empty test_units.")
    else:
        required_unit_fields = {
            "unit_ref",
            "title",
            "priority",
            "input_preconditions",
            "trigger_action",
            "observation_points",
            "pass_conditions",
            "fail_conditions",
            "required_evidence",
        }
        for index, unit in enumerate(test_units, start=1):
            if not isinstance(unit, dict):
                errors.append(f"test_units[{index}] must be an object.")
                continue
            missing = sorted(field for field in required_unit_fields if unit.get(field) in (None, "", []))
            if missing:
                errors.append(f"test_units[{index}] is missing required fields: {', '.join(missing)}.")
            if unit.get("acceptance_ref") in (None, "", []):
                if not ensure_list(unit.get("derivation_basis")):
                    errors.append(
                        f"test_units[{index}] must include acceptance_ref or a non-empty derivation_basis."
                    )
    if not isinstance(acceptance_traceability, list) or not acceptance_traceability:
        errors.append("test-set.yaml must contain non-empty acceptance_traceability.")
    else:
        for index, row in enumerate(acceptance_traceability, start=1):
            if not isinstance(row, dict):
                errors.append(f"acceptance_traceability[{index}] must be an object.")
                continue
            missing = sorted(
                field
                for field in ["acceptance_ref", "acceptance_scenario", "given", "when", "then", "unit_refs", "coverage_status"]
                if row.get(field) in (None, "", [])
            )
            if missing:
                errors.append(
                    f"acceptance_traceability[{index}] is missing required fields: {', '.join(missing)}."
                )
        traceability_acceptance_refs = {
            str(row.get("acceptance_ref")) for row in acceptance_traceability if isinstance(row, dict)
        }
        unit_acceptance_refs = {
            str(unit.get("acceptance_ref"))
            for unit in test_units
            if isinstance(unit, dict) and unit.get("acceptance_ref") not in (None, "", [])
        }
        if traceability_acceptance_refs != unit_acceptance_refs:
            errors.append("acceptance_traceability must explicitly cover every acceptance_ref present in test_units.")

    bundle_markdown = (artifacts_dir / "test-set-bundle.md").read_text(encoding="utf-8")
    _, bundle_body = parse_markdown_frontmatter(bundle_markdown)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if f"## {heading}" not in bundle_body:
            errors.append(f"test-set-bundle.md is missing section: {heading}")

    gate_subject_index = load_json(artifacts_dir / "gate-subject-index.json")
    subjects = gate_subject_index.get("subjects")
    if not isinstance(subjects, dict):
        errors.append("gate-subject-index.json must contain subjects.")
    for gate_type, filename in SUBJECT_FILE_NAMES.items():
        subject = load_json(artifacts_dir / filename)
        if subject.get("gate_type") != gate_type:
            errors.append(f"{filename} gate_type must be {gate_type}.")
        if subject.get("candidate_package_ref") != "test-set-bundle.json":
            errors.append(f"{filename} candidate_package_ref must be test-set-bundle.json.")

    target_skill = str(handoff.get("target_skill") or "")
    bundle_target = str(bundle_json.get("downstream_target") or "")
    if target_skill not in SUPPORTED_DOWNSTREAM_SKILLS:
        errors.append("handoff-to-test-execution.json target_skill must be a supported test execution sibling.")
    if bundle_target not in SUPPORTED_DOWNSTREAM_SKILLS:
        errors.append("test-set-bundle.json downstream_target must be a supported test execution sibling.")
    if target_skill and bundle_target and target_skill != bundle_target:
        errors.append("handoff-to-test-execution.json target_skill must match test-set-bundle.json downstream_target.")
    required_inputs = handoff.get("required_environment_inputs") or {}
    for category in ENVIRONMENT_INPUT_CATEGORIES:
        if not ensure_list(required_inputs.get(category)):
            errors.append(f"required_environment_inputs.{category} must be populated.")
    execution_context = " ".join(ensure_list(required_inputs.get("ui_or_integration_context"))).lower()
    if target_skill == "skill.qa.test_exec_cli" and not any(
        marker in execution_context for marker in ["cli", "command", "integration", "api", "调用", "命令"]
    ):
        errors.append("CLI downstream handoff must describe CLI, command, API, or integration execution context.")
    if target_skill == "skill.qa.test_exec_web_e2e" and not any(
        marker in execution_context for marker in ["browser", "page", "locator", "selector", "ui", "浏览器", "页面", "定位器"]
    ):
        errors.append("Web downstream handoff must describe browser, page, locator, or UI execution context.")

    test_set_status = str(test_set_yaml.get("status") or "")
    manifest_status = str(manifest.get("status") or "")
    bundle_status = str(bundle_json.get("status") or "")
    gate_status = str(freeze_gate.get("status") or "")
    allowed_test_set = {"draft", "review_ready", "approved", "frozen"}
    allowed_manifest = {"in_progress", "review_pending", "approval_pending", "frozen", "rejected"}
    allowed_gate = {"pending", "passed", "failed"}
    if test_set_status not in allowed_test_set:
        errors.append(f"test-set.yaml.status must be one of {sorted(allowed_test_set)}.")
    if manifest_status not in allowed_manifest:
        errors.append(f"package-manifest.json.status must be one of {sorted(allowed_manifest)}.")
    if bundle_status not in allowed_manifest:
        errors.append(f"test-set-bundle.json.status must be one of {sorted(allowed_manifest)}.")
    if gate_status not in allowed_gate:
        errors.append(f"test-set-freeze-gate.json.status must be one of {sorted(allowed_gate)}.")

    ready_for_external_approval = freeze_gate.get("ready_for_external_approval") is True
    if bundle_json.get("semantic_lock") and semantic_drift_check.get("semantic_lock_preserved") is not True:
        errors.append("semantic-drift-check.json must preserve semantic_lock when semantic_lock is present.")
    if manifest_status != bundle_status:
        errors.append("package-manifest.json.status must match test-set-bundle.json.status.")
    if manifest_status == "in_progress":
        if test_set_status != "draft" or gate_status != "pending":
            errors.append("in_progress packages must keep test-set draft and freeze gate pending.")
    elif manifest_status == "review_pending":
        if test_set_status != "review_ready" or gate_status != "failed" or ready_for_external_approval:
            errors.append("review_pending packages must map to test-set review_ready and failed freeze gate.")
    elif manifest_status == "approval_pending":
        if test_set_status != "approved" or gate_status != "pending" or not ready_for_external_approval:
            errors.append("approval_pending packages must map to test-set approved and pending freeze gate.")
    elif manifest_status == "frozen":
        if test_set_status != "frozen" or gate_status != "passed":
            errors.append("frozen packages must map to test-set frozen and passed freeze gate.")
    elif manifest_status == "rejected":
        if gate_status != "failed":
            errors.append("rejected packages must carry failed freeze gate.")

    return errors, {
        "valid": not errors,
        "feat_ref": bundle_json.get("feat_ref"),
        "test_set_ref": bundle_json.get("test_set_ref"),
        "manifest_status": manifest_status,
        "test_set_status": test_set_status,
        "freeze_gate_status": gate_status,
        "semantic_lock_preserved": semantic_drift_check.get("semantic_lock_preserved", True),
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors

    bundle_json = load_json(artifacts_dir / "test-set-bundle.json")
    manifest = load_json(artifacts_dir / "package-manifest.json")
    test_set_yaml = yaml_load(artifacts_dir / "test-set.yaml")
    freeze_gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    review_report = load_json(artifacts_dir / "test-set-review-report.json")
    acceptance_report = load_json(artifacts_dir / "test-set-acceptance-report.json")

    readiness_errors: list[str] = []
    if bundle_json.get("status") != "approval_pending":
        readiness_errors.append("Candidate package status must be approval_pending.")
    if manifest.get("status") != "approval_pending":
        readiness_errors.append("Package manifest status must be approval_pending.")
    if test_set_yaml.get("status") != "approved":
        readiness_errors.append("test-set.yaml status must be approved.")
    if freeze_gate.get("status") != "pending":
        readiness_errors.append("test-set-freeze-gate.json status must be pending.")
    if freeze_gate.get("ready_for_external_approval") is not True:
        readiness_errors.append("test-set-freeze-gate.json must mark ready_for_external_approval true.")
    if review_report.get("decision") != "pass":
        readiness_errors.append("test-set-review-report.json decision must be pass.")
    if acceptance_report.get("decision") != "approve":
        readiness_errors.append("test-set-acceptance-report.json decision must be approve.")
    return not readiness_errors, readiness_errors


def collect_evidence_report(artifacts_dir: Path) -> Path:
    execution = load_json(artifacts_dir / "execution-evidence.json")
    supervision = load_json(artifacts_dir / "supervision-evidence.json")
    gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    report_path = artifacts_dir / "evidence-report.md"
    report_path.write_text(
        "\n".join(
            [
                "# ll-qa-feat-to-testset Evidence Report",
                "",
                "## Run Summary",
                "",
                f"- run_id: {execution.get('run_id')}",
                f"- feat_ref: {execution.get('inputs', ['', ''])[-1]}",
                f"- output_dir: {artifacts_dir}",
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
                f"- status: {gate.get('status')}",
                f"- decision: {gate.get('decision')}",
                f"- ready_for_external_approval: {gate.get('ready_for_external_approval')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def executor_run(input_path: Path, feat_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, feat_ref)
    if errors:
        raise ValueError("; ".join(errors))

    package = load_feat_package(input_path)
    feature = find_feature(package, feat_ref)
    if feature is None:
        raise ValueError(f"Selected feat_ref not found: {feat_ref}")
    feature = dict(feature)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)

    effective_run_id = run_id or f"{package.run_id}--{feat_ref.lower()}"
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    generated = build_candidate_package(package, feature, feat_ref, effective_run_id)
    write_executor_outputs(
        output_dir,
        package,
        generated,
        f"python scripts/feat_to_testset.py executor-run --input {input_path} --feat-ref {feat_ref}",
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "feat_ref": feat_ref,
        "test_set_ref": generated.bundle_json["test_set_ref"],
    }


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del repo_root
    del run_id
    del allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")
    supervision = build_supervision_evidence(artifacts_dir)
    update_supervisor_outputs(artifacts_dir, supervision)
    freeze_gate = load_json(artifacts_dir / "test-set-freeze-gate.json")
    return {
        "ok": True,
        "run_id": supervision["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "freeze_ready": freeze_gate.get("ready_for_external_approval") is True,
    }


def run_workflow(input_path: Path, feat_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        feat_ref=feat_ref,
        repo_root=repo_root,
        run_id=run_id,
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
        "feat_ref": feat_ref,
        "test_set_ref": executor_result["test_set_ref"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }
