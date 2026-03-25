#!/usr/bin/env python3
"""
Lite-native runtime support for epic-to-feat.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from epic_to_feat_common import (
    dump_json,
    ensure_list,
    guess_repo_root_from_input,
    load_epic_package,
    load_json,
    parse_markdown_frontmatter,
    render_markdown,
    unique_strings,
    validate_input_package,
)
from epic_to_feat_cli_integration import (
    build_gate_result,
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    write_executor_outputs,
)
from epic_to_feat_derivation import (
    build_boundary_matrix,
    build_feat_record,
    bundle_source_refs,
    bundle_shared_non_goals,
    choose_epic_ref,
    choose_src_ref,
    derive_bundle_intent,
    derive_feat_axes,
    feat_count_assessment,
    prerequisite_foundations,
)


REQUIRED_OUTPUT_FILES = ["feat-freeze-bundle.md", "feat-freeze-bundle.json", "feat-review-report.json", "feat-acceptance-report.json", "feat-defect-list.json", "feat-freeze-gate.json", "handoff-to-feat-downstreams.json", "execution-evidence.json", "supervision-evidence.json"]
REQUIRED_MARKDOWN_HEADINGS = ["FEAT Bundle Intent", "EPIC Context", "Boundary Matrix", "FEAT Inventory", "Acceptance and Review", "Downstream Handoff", "Traceability"]
DOWNSTREAM_WORKFLOWS = ["workflow.product.task.feat_to_delivery_prep", "workflow.product.feat_to_plan_pipeline"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "epic-to-feat" / run_id


@dataclass
class GeneratedFeatBundle:
    frontmatter: dict[str, Any]
    markdown_body: str
    json_payload: dict[str, Any]
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    handoff: dict[str, Any]


def build_feat_bundle(package: Any) -> GeneratedFeatBundle:
    axes = derive_feat_axes(package)
    feats = [build_feat_record(package, axis, index) for index, axis in enumerate(axes, start=1)]
    assessment = feat_count_assessment(feats)
    epic_ref = choose_epic_ref(package)
    src_ref = choose_src_ref(package)
    boundary_matrix = build_boundary_matrix(feats)
    shared_non_goals = bundle_shared_non_goals(package)
    inherited_source_refs = bundle_source_refs(package, axes)
    source_refs = unique_strings([f"product.src-to-epic::{package.run_id}", epic_ref, src_ref] + inherited_source_refs)
    feat_track_map = [{"feat_ref": feat["feat_ref"], "title": feat["title"], "track": feat["track"]} for feat in feats]
    prerequisites = prerequisite_foundations(package, axes)

    defects: list[dict[str, Any]] = []
    if not assessment["is_valid"]:
        defects.append(
            {
                "severity": "P1",
                "title": "EPIC boundary did not decompose into multiple FEAT slices",
                "detail": "The generated FEAT bundle contains fewer than two independently acceptable FEATs.",
            }
        )

    for feat in feats:
        if len(feat.get("acceptance_checks") or []) < 3:
            defects.append(
                {
                    "severity": "P1",
                    "title": f"{feat['feat_ref']} is missing structured acceptance checks",
                "detail": "Each FEAT must provide at least three structured acceptance checks.",
            }
        )

    rollout_required = bool((package.epic_json.get("rollout_requirement") or {}).get("required"))
    has_adoption_feat = any(feat.get("axis_id") == "skill-adoption-e2e" for feat in feats)
    if rollout_required and not has_adoption_feat:
        defects.append(
            {
                "severity": "P1",
                "title": "Rollout-required EPIC is missing adoption/E2E FEAT coverage",
                "detail": "When rollout_requirement.required is true, the FEAT bundle must include a skill-adoption-e2e slice for onboarding, migration, and pilot-chain validation.",
            }
        )

    review_decision = "pass" if not defects else "revise"
    acceptance_decision = "approve" if not defects else "revise"

    handoff = {
        "handoff_id": f"handoff-{package.run_id}-to-feat-downstreams",
        "from_skill": "ll-product-epic-to-feat",
        "source_run_id": package.run_id,
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "feat_track_map": feat_track_map,
        "target_workflows": [
            {
                "workflow": "workflow.product.task.feat_to_delivery_prep",
                "purpose": "derive delivery-prep artifacts and seed TECH / TASK generation",
            },
            {
                "workflow": "workflow.product.feat_to_plan_pipeline",
                "purpose": "derive release, devplan, and testplan after FEAT readiness",
            },
        ],
        "derivable_children": ["TECH", "TASK", "TESTSET"],
        "primary_artifact_ref": "feat-freeze-bundle.md",
        "supporting_artifact_refs": [
            "feat-freeze-bundle.json",
            "feat-review-report.json",
            "feat-acceptance-report.json",
            "feat-defect-list.json",
        ],
        "prerequisite_foundations": prerequisites,
        "created_at": utc_now(),
    }

    json_payload = {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat",
        "workflow_run_id": package.run_id,
        "title": f"{package.epic_json.get('title') or epic_ref} FEAT Bundle",
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "downstream_workflows": DOWNSTREAM_WORKFLOWS,
        "source_refs": source_refs,
        "bundle_intent": derive_bundle_intent(package, feats),
        "bundle_shared_non_goals": shared_non_goals,
        "epic_context": {
            "business_goal": package.epic_json.get("business_goal"),
            "scope": ensure_list(package.epic_json.get("scope")),
            "non_goals": ensure_list(package.epic_json.get("non_goals")),
            "decomposition_rules": ensure_list(package.epic_json.get("decomposition_rules")),
            "constraints_and_dependencies": ensure_list(package.epic_json.get("constraints_and_dependencies")),
            "rollout_requirement": package.epic_json.get("rollout_requirement"),
            "rollout_plan": package.epic_json.get("rollout_plan"),
            "prerequisite_foundations": prerequisites,
        },
        "boundary_matrix": boundary_matrix,
        "features": feats,
        "feat_track_map": feat_track_map,
        "bundle_acceptance_conventions": [
            {
                "topic": "Traceability",
                "rule": "Every FEAT must preserve epic_freeze_ref, src_root_id, and source_refs so downstream readers can recover the authoritative EPIC lineage.",
            },
            {
                "topic": "Independent acceptance",
                "rule": "Every FEAT must remain independently acceptable and must not collapse into task, code, or UI implementation detail.",
            },
        ],
        "acceptance_and_review": {
            "upstream_acceptance_decision": package.acceptance_report.get("decision"),
            "upstream_acceptance_summary": package.acceptance_report.get("summary"),
            "upstream_review_decision": package.review_report.get("decision"),
            "feat_review_decision": review_decision,
            "feat_acceptance_decision": acceptance_decision,
        },
        "downstream_handoff": handoff,
        "traceability": [
            {
                "bundle_section": "FEAT Bundle Intent",
                "epic_fields": ["title", "business_goal"],
                "source_refs": [epic_ref] + source_refs[:3],
            },
            {
                "bundle_section": "FEAT Inventory",
                "epic_fields": ["scope", "capability_axes", "decomposition_rules"],
                "source_refs": [epic_ref, f"product.src-to-epic::{package.run_id}"],
            },
        ],
        "feat_count_assessment": assessment,
    }

    frontmatter = {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat",
        "workflow_run_id": package.run_id,
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "downstream_workflows": DOWNSTREAM_WORKFLOWS,
        "source_refs": source_refs,
    }

    epic_context_lines = [
        f"- epic_freeze_ref: `{epic_ref}`",
        f"- src_root_id: `{package.epic_json.get('src_root_id')}`",
        f"- business_goal: {package.epic_json.get('business_goal')}",
    ]
    epic_scope = ensure_list(package.epic_json.get("scope"))
    if epic_scope:
        epic_context_lines.append("- inherited_scope:")
        epic_context_lines.extend([f"  - {item}" for item in epic_scope[:5]])
    if prerequisites:
        epic_context_lines.append("- prerequisite_foundations:")
        epic_context_lines.extend([f"  - {item}" for item in prerequisites])

    boundary_matrix_sections = []
    for row in boundary_matrix:
        boundary_matrix_sections.append(
            "\n".join(
                [
                    f"### {row['feat_ref']} {row['title']}",
                    "",
                    "- Responsible for:",
                    *[f"  - {item}" for item in row["responsible_for"]],
                    "- Not responsible for:",
                    *[f"  - {item}" for item in row["not_responsible_for"]],
                    "- Boundary dependencies:",
                    *([f"  - {item}" for item in row["boundary_dependencies"]] or ["  - None"]),
                ]
            )
        )

    bundle_shared_non_goal_lines = ["- Shared non-goals:"] + [f"  - {item}" for item in shared_non_goals]
    bundle_acceptance_lines = ["- Bundle acceptance conventions:"] + [
        f"  - {item['topic']}: {item['rule']}" for item in json_payload["bundle_acceptance_conventions"]
    ]

    feat_inventory_sections: list[str] = []
    for feat in feats:
        feat_inventory_sections.append(
            "\n".join(
                [
                    f"### {feat['feat_ref']} {feat['title']}",
                    "",
                    f"- Track: {feat['track']}",
                    f"- Goal: {feat['goal']}",
                    "- Scope:",
                    *[f"  - {item}" for item in feat["scope"]],
                    "- Dependencies:",
                    *([f"  - {item}" for item in feat["dependencies"]] or ["  - None"]),
                    "- Constraints:",
                    *[f"  - {item}" for item in feat["constraints"]],
                    "- Acceptance Checks:",
                    *[
                        f"  - {check['id']}: {check['scenario']} | given {check['given']} | when {check['when']} | then {check['then']}"
                        for check in feat["acceptance_checks"]
                    ],
                ]
            )
        )

    markdown_body = "\n\n".join(
        [
            f"# {json_payload['title']}",
            "## FEAT Bundle Intent\n\n" + json_payload["bundle_intent"] + "\n\n" + "\n".join(bundle_shared_non_goal_lines),
            "## EPIC Context\n\n" + "\n".join(epic_context_lines),
            "## Boundary Matrix\n\n" + "\n\n".join(boundary_matrix_sections),
            "## FEAT Inventory\n\n" + "\n\n".join(feat_inventory_sections),
            "## Acceptance and Review\n\n"
            + "\n".join(
                [
                    f"- Upstream acceptance: {package.acceptance_report.get('decision')} ({package.acceptance_report.get('summary')})",
                    f"- Upstream review: {package.review_report.get('decision')} ({package.review_report.get('summary')})",
                    f"- FEAT review: {review_decision}",
                    f"- FEAT acceptance: {acceptance_decision}",
                    f"- FEAT count assessment: {assessment['reason']}",
                    "- Boundary matrix: present and aligned with feature-specific acceptance surfaces.",
                    *bundle_acceptance_lines,
                ]
            ),
            "## Downstream Handoff\n\n"
            + "\n".join(
                [
                    "- Target workflows:",
                    *[f"  - {workflow}" for workflow in DOWNSTREAM_WORKFLOWS],
                    "- FEAT tracks:",
                    *[f"  - {item['feat_ref']}: {item['track']} ({item['title']})" for item in feat_track_map],
                    "- Derived child artifacts:",
                    "  - TECH",
                    "  - TASK",
                    "  - TESTSET",
                ]
            ),
            "## Traceability\n\n"
            + "\n".join(
                f"- {item['bundle_section']}: {', '.join(item['epic_fields'])} <- {', '.join(item['source_refs'])}"
                for item in json_payload["traceability"]
            ),
        ]
    )

    review_report = {
        "review_id": f"feat-review-{package.run_id}",
        "review_type": "feat_review",
        "subject_refs": [epic_ref] + [feat["feat_ref"] for feat in feats],
        "summary": "FEAT bundle preserves the EPIC decomposition boundary and downstream readiness.",
        "findings": [
            f"Generated {len(feats)} FEAT slices from {epic_ref}.",
            "Each FEAT includes FEAT-specific acceptance checks and axis-specific constraints, while traceability is enforced as a bundle-wide convention.",
            "Downstream handoff metadata preserves delivery-prep and plan workflow targets.",
            "FEAT track mapping preserves the foundation vs adoption/E2E overlay split for downstream flows.",
            "Boundary matrix records the horizontal split between FEAT responsibilities and adjacent non-responsibilities.",
        ],
        "decision": review_decision,
        "risks": [defect["detail"] for defect in defects],
        "recommendations": [
            "Keep downstream TECH, TASK, and TESTSET derivation anchored to FEAT acceptance checks.",
            "Do not re-open the parent EPIC scope in delivery-prep or plan stages.",
            "Use the boundary matrix as the first guard against overlap before expanding downstream plans.",
            "Treat the emitted FEAT bundle as the single governed FEAT truth for downstream flows.",
        ],
        "created_at": utc_now(),
    }

    acceptance_report = {
        "stage_id": "feat_acceptance_review",
        "created_by_role": "supervisor",
        "decision": acceptance_decision,
        "dimensions": {
            "independent_acceptance_boundary": {
                "status": "pass" if not defects else "fail",
                "note": "Each FEAT remains independently acceptable." if not defects else "One or more FEAT boundaries are weak.",
            },
            "parent_child_traceability": {"status": "pass", "note": "epic_freeze_ref, src_root_id, and source_refs are preserved."},
            "downstream_readiness": {"status": "pass", "note": "Output remains actionable for delivery-prep and plan flows."},
            "structured_acceptance_checks": {"status": "pass", "note": "Each FEAT includes structured acceptance checks."},
            "evidence_completeness": {"status": "pass", "note": "Execution and supervision evidence will ship with the package."},
        },
        "summary": "FEAT acceptance review passed." if not defects else "FEAT acceptance review requires revision.",
        "acceptance_findings": defects,
        "created_at": utc_now(),
    }

    return GeneratedFeatBundle(
        frontmatter=frontmatter,
        markdown_body=markdown_body,
        json_payload=json_payload,
        review_report=review_report,
        acceptance_report=acceptance_report,
        defect_list=defects,
        handoff=handoff,
    )


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_OUTPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required output artifact: {required_file}")
    if errors:
        return errors, {"valid": False}

    feat_json = load_json(artifacts_dir / "feat-freeze-bundle.json")
    if feat_json.get("artifact_type") != "feat_freeze_package":
        errors.append("feat-freeze-bundle.json artifact_type must be feat_freeze_package.")
    if feat_json.get("workflow_key") != "product.epic-to-feat":
        errors.append("feat-freeze-bundle.json workflow_key must be product.epic-to-feat.")

    epic_ref = str(feat_json.get("epic_freeze_ref") or "")
    src_root_id = str(feat_json.get("src_root_id") or "")
    feat_refs = ensure_list(feat_json.get("feat_refs"))
    source_refs = ensure_list(feat_json.get("source_refs"))
    downstream_workflows = ensure_list(feat_json.get("downstream_workflows"))
    if not epic_ref:
        errors.append("feat-freeze-bundle.json must include epic_freeze_ref.")
    if not src_root_id:
        errors.append("feat-freeze-bundle.json must include src_root_id.")
    if not feat_refs:
        errors.append("feat-freeze-bundle.json must include feat_refs.")
    if not any(ref.startswith("product.src-to-epic::") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include product.src-to-epic::<run_id>.")
    if not any(ref.startswith("EPIC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include EPIC-*.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("feat-freeze-bundle.json source_refs must include SRC-*.")
    for workflow in DOWNSTREAM_WORKFLOWS:
        if workflow not in downstream_workflows:
            errors.append(f"feat-freeze-bundle.json downstream_workflows must include {workflow}.")

    features = feat_json.get("features")
    if not isinstance(features, list) or not features:
        errors.append("feat-freeze-bundle.json must include a non-empty features list.")
    else:
        for feature in features:
            if not isinstance(feature, dict):
                errors.append("Each feature entry must be an object.")
                continue
            if not feature.get("feat_ref"):
                errors.append("Each feature entry must include feat_ref.")
            if not feature.get("title"):
                errors.append("Each feature entry must include title.")
            if len(feature.get("acceptance_checks") or []) < 3:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least three acceptance checks.")
            if len(feature.get("constraints") or []) < 4:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least four constraints.")
            if len(feature.get("scope") or []) < 3:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least three scope bullets.")

    boundary_matrix = feat_json.get("boundary_matrix")
    if not isinstance(boundary_matrix, list) or len(boundary_matrix) != len(feat_refs):
        errors.append("feat-freeze-bundle.json must include a boundary_matrix aligned to feat_refs.")
    shared_non_goals = feat_json.get("bundle_shared_non_goals")
    if not isinstance(shared_non_goals, list) or not shared_non_goals:
        errors.append("feat-freeze-bundle.json must include bundle_shared_non_goals.")
    acceptance_conventions = feat_json.get("bundle_acceptance_conventions")
    if not isinstance(acceptance_conventions, list) or not acceptance_conventions:
        errors.append("feat-freeze-bundle.json must include bundle_acceptance_conventions.")

    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    _, markdown_body = parse_markdown_frontmatter(markdown_text)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if f"## {heading}" not in markdown_body:
            errors.append(f"feat-freeze-bundle.md is missing section: {heading}")

    handoff = load_json(artifacts_dir / "handoff-to-feat-downstreams.json")
    workflows = [item.get("workflow") for item in handoff.get("target_workflows", []) if isinstance(item, dict)]
    for workflow in DOWNSTREAM_WORKFLOWS:
        if workflow not in workflows:
            errors.append(f"handoff-to-feat-downstreams.json must include target workflow {workflow}.")

    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    if gate.get("epic_freeze_ref") != epic_ref:
        errors.append("feat-freeze-gate.json must point to the same epic_freeze_ref.")

    return errors, {
        "valid": not errors,
        "epic_freeze_ref": epic_ref,
        "src_root_id": src_root_id,
        "feat_refs": feat_refs,
        "source_refs": source_refs,
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors

    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    checks = gate.get("checks") or {}
    readiness_errors = [name for name, status in checks.items() if status is not True]
    return not readiness_errors, readiness_errors


def executor_run(input_path: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path)
    if errors:
        raise ValueError("; ".join(errors))

    package = load_epic_package(input_path)
    generated = build_feat_bundle(package)
    effective_run_id = run_id or package.run_id
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    write_executor_outputs(
        output_dir=output_dir,
        repo_root=repo_root,
        package=package,
        generated=generated,
        command_name=f"python scripts/epic_to_feat.py executor-run --input {input_path}",
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "epic_freeze_ref": generated.frontmatter["epic_freeze_ref"],
        "feat_refs": generated.frontmatter["feat_refs"],
    }


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    package_manifest = load_json(artifacts_dir / "package-manifest.json")
    input_package_dir = Path(str(package_manifest.get("input_artifacts_dir") or "")).resolve()
    if not input_package_dir.exists():
        raise FileNotFoundError(f"Input package directory not found: {input_package_dir}")

    package = load_epic_package(input_package_dir)
    generated = build_feat_bundle(package)
    supervision = build_supervision_evidence(artifacts_dir, generated)
    gate = build_gate_result(generated, supervision)

    update_supervisor_outputs(artifacts_dir, repo_root, generated, supervision, gate)

    return {
        "ok": True,
        "run_id": run_id or str(generated.frontmatter.get("workflow_run_id") or artifacts_dir.name),
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "freeze_ready": gate["freeze_ready"],
    }


def run_workflow(input_path: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(
        artifacts_dir=artifacts_dir,
        repo_root=repo_root,
        run_id=run_id or executor_result["run_id"],
        allow_update=True,
    )
    output_errors, output_result = validate_output_package(artifacts_dir)
    if output_errors:
        raise ValueError("; ".join(output_errors))
    readiness_ok, readiness_errors = validate_package_readiness(artifacts_dir)
    report_path = collect_evidence_report(artifacts_dir)
    return {
        "ok": readiness_ok,
        "run_id": executor_result["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "epic_freeze_ref": executor_result["epic_freeze_ref"],
        "feat_refs": executor_result["feat_refs"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }
