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
    load_optional_json,
    normalize_semantic_lock,
    parse_markdown_frontmatter,
    render_markdown,
    summarize_text,
    unique_strings,
    resolve_input_artifacts_dir,
    validate_input_package,
)
from epic_to_feat_cli_integration import (
    build_gate_result,
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    write_executor_outputs,
)
from epic_to_feat_gate_integration import (
    create_gate_ready_package,
    create_handoff_proposal,
    submit_gate_pending,
)
from epic_to_feat_derivation import (
    apply_feature_relationships,
    build_boundary_matrix,
    build_feat_record,
    bundle_source_refs,
    bundle_shared_non_goals,
    canonical_glossary,
    choose_epic_ref,
    choose_src_ref,
    derive_bundle_intent,
    derive_feat_axes,
    feat_count_assessment,
    prerequisite_foundations,
    prohibited_inference_rules,
)


REQUIRED_OUTPUT_FILES = ["feat-freeze-bundle.md", "feat-freeze-bundle.json", "feat-review-report.json", "feat-acceptance-report.json", "feat-defect-list.json", "feat-freeze-gate.json", "handoff-to-feat-downstreams.json", "semantic-drift-check.json", "execution-evidence.json", "supervision-evidence.json"]
REQUIRED_MARKDOWN_HEADINGS = ["FEAT Bundle Intent", "EPIC Context", "Canonical Glossary", "Boundary Matrix", "FEAT Inventory", "Prohibited Inference Rules", "Acceptance and Review", "Downstream Handoff", "Traceability"]
REQUIRED_FEAT_SUBHEADINGS = [
    "#### Identity and Scenario",
    "#### Business Flow",
    "#### Product Objects and Deliverables",
    "#### Collaboration and Timeline",
    "#### Acceptance and Testability",
    "#### Frozen Downstream Boundary",
]
DOWNSTREAM_WORKFLOWS = ["workflow.dev.feat_to_tech", "workflow.qa.feat_to_testset"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from(repo_root: str | None, input_path: str | Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        candidate = Path(str(input_path))
        if candidate.exists():
            return guess_repo_root_from_input(candidate.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "epic-to-feat" / run_id


def _revision_request_target_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / "revision-request.json"


def _materialize_revision_request(
    artifacts_dir: Path,
    revision_request_path: str | Path | None,
) -> tuple[str, dict[str, Any]]:
    target_path = _revision_request_target_path(artifacts_dir)
    source_path = Path(revision_request_path).resolve() if revision_request_path else target_path
    if not source_path.exists():
        if revision_request_path:
            raise FileNotFoundError(f"Revision request not found: {source_path}")
        return "", {}

    revision_request = load_optional_json(source_path)
    revision_round = int(revision_request.get("revision_round") or 1)
    if target_path.exists():
        previous_revision = load_json(target_path)
        revision_round = int(previous_revision.get("revision_round") or 0) + 1
    revision_request["revision_round"] = revision_round
    dump_json(target_path, revision_request)
    return str(target_path), revision_request


def _load_revision_request(
    artifacts_dir: Path,
    revision_request_path: str | Path | None,
) -> tuple[str, dict[str, Any]]:
    target_path = _revision_request_target_path(artifacts_dir)
    if target_path.exists():
        return str(target_path), load_optional_json(target_path)
    if not revision_request_path:
        return "", {}
    source_path = Path(revision_request_path).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Revision request not found: {source_path}")
    revision_request = load_optional_json(source_path)
    dump_json(target_path, revision_request)
    return str(target_path), revision_request


def _revision_summary(revision_request: dict[str, Any]) -> str:
    decision_target = str(revision_request.get("decision_target") or "").strip()
    decision_reason = str(revision_request.get("decision_reason") or revision_request.get("reason") or "").strip()
    revision_round = str(revision_request.get("revision_round") or "").strip()
    pieces: list[str] = []
    if revision_round:
        pieces.append(f"round {revision_round}")
    if decision_target:
        pieces.append(decision_target)
    if decision_reason:
        pieces.append(summarize_text(decision_reason, limit=180))
    summary = " | ".join(pieces)
    if not summary:
        summary = "gate revise request"
    return summarize_text(f"Gate revise: {summary}", limit=220)


def _apply_revision_request(
    package: Any,
    revision_request_ref: str,
    revision_request: dict[str, Any],
) -> str:
    if not revision_request:
        return ""

    revision_summary = _revision_summary(revision_request)
    revision_context = {
        "revision_request_ref": revision_request_ref,
        "workflow_key": str(revision_request.get("workflow_key") or "").strip(),
        "run_id": str(revision_request.get("run_id") or "").strip(),
        "source_run_id": str(revision_request.get("source_run_id") or "").strip(),
        "decision_type": str(revision_request.get("decision_type") or "").strip(),
        "decision_target": str(revision_request.get("decision_target") or "").strip(),
        "decision_reason": str(revision_request.get("decision_reason") or revision_request.get("reason") or "").strip(),
        "revision_round": revision_request.get("revision_round"),
        "basis_refs": ensure_list(revision_request.get("basis_refs")),
        "source_gate_decision_ref": str(revision_request.get("source_gate_decision_ref") or "").strip(),
        "source_return_job_ref": str(revision_request.get("source_return_job_ref") or "").strip(),
        "authoritative_input_ref": str(revision_request.get("authoritative_input_ref") or "").strip(),
        "candidate_ref": str(revision_request.get("candidate_ref") or "").strip(),
        "original_input_path": str(revision_request.get("original_input_path") or "").strip(),
        "triggered_by_request_id": str(revision_request.get("triggered_by_request_id") or "").strip(),
        "trace": revision_request.get("trace") if isinstance(revision_request.get("trace"), dict) else {},
        "summary": revision_summary,
    }
    package.epic_json["revision_context"] = revision_context
    package.epic_frontmatter["revision_context"] = revision_context
    package.manifest["revision_request_ref"] = revision_request_ref
    return revision_summary


@dataclass
class GeneratedFeatBundle:
    frontmatter: dict[str, Any]
    markdown_body: str
    json_payload: dict[str, Any]
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    handoff: dict[str, Any]
    semantic_drift_check: dict[str, Any]


def build_semantic_drift_check(package: Any, feats: list[dict[str, Any]]) -> dict[str, Any]:
    lock = normalize_semantic_lock(package.epic_json.get("semantic_lock") or package.epic_frontmatter.get("semantic_lock"))
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
            str(package.epic_json.get("title") or ""),
            str(package.epic_json.get("business_goal") or ""),
            " ".join(str(feat.get("title") or "") for feat in feats),
            " ".join(str(feat.get("goal") or "") for feat in feats),
            " ".join(str(feat.get("identity_and_scenario", {}).get("product_interface") or "") for feat in feats),
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
        review_projection_tokens = ["projection", "gate", "ssot"]
        if all(token in generated_text for token in review_projection_tokens):
            anchor_matches.append("review_projection_signature")
    domain_type = str(lock.get("domain_type") or "").strip().lower()
    if domain_type == "execution_runner_rule":
        runner_signatures = [
            ("runner_ready_queue_signature", ["ready", "job", "runner"]),
            ("approve_next_skill_signature", ["approve", "next", "skill"]),
        ]
        for label, tokens in runner_signatures:
            if all(token in generated_text for token in tokens):
                anchor_matches.append(label)
        preserved = not forbidden_hits and "runner_ready_queue_signature" in anchor_matches and "approve_next_skill_signature" in anchor_matches
    else:
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


def build_feat_bundle(
    package: Any,
    workflow_run_id: str | None = None,
    revision_request_ref: str = "",
    revision_request: dict[str, Any] | None = None,
) -> GeneratedFeatBundle:
    active_run_id = workflow_run_id or package.run_id
    revision_request = revision_request or {}
    axes = derive_feat_axes(package)
    feats = apply_feature_relationships([build_feat_record(package, axis, index) for index, axis in enumerate(axes, start=1)])
    assessment = feat_count_assessment(feats)
    epic_ref = choose_epic_ref(package)
    src_ref = choose_src_ref(package)
    boundary_matrix = build_boundary_matrix(feats)
    shared_non_goals = bundle_shared_non_goals(package)
    glossary = canonical_glossary(feats)
    inference_rules = prohibited_inference_rules()
    inherited_source_refs = bundle_source_refs(package, axes)
    source_refs = unique_strings([f"product.src-to-epic::{package.run_id}", epic_ref, src_ref] + inherited_source_refs)
    feat_track_map = [{"feat_ref": feat["feat_ref"], "title": feat["title"], "track": feat["track"]} for feat in feats]
    prerequisites = prerequisite_foundations(package, axes)
    semantic_drift_check = build_semantic_drift_check(package, feats)
    revision_summary = _apply_revision_request(package, revision_request_ref, revision_request)

    defects: list[dict[str, Any]] = []
    if semantic_drift_check["verdict"] == "reject":
        defects.append(
            {
                "severity": "P1",
                "title": "semantic_lock drift detected",
                "detail": semantic_drift_check["summary"],
            }
        )
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
    if revision_summary:
        review_report_findings = [
            f"Revision context absorbed: {revision_summary}.",
        ]
    else:
        review_report_findings = []

    review_decision = "pass" if not defects else "revise"
    acceptance_decision = "approve" if not defects else "revise"

    handoff = {
        "handoff_id": f"handoff-{active_run_id}-to-feat-downstreams",
        "from_skill": "ll-product-epic-to-feat",
        "source_run_id": active_run_id,
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "feat_track_map": feat_track_map,
        "authoritative_artifact_map": [
            {
                "feat_ref": feat["feat_ref"],
                "title": feat["title"],
                "authoritative_artifact": feat["authoritative_artifact"],
            }
            for feat in feats
        ],
        "feature_dependency_map": [
            {
                "feat_ref": feat["feat_ref"],
                "upstream_feat": feat["upstream_feat"],
                "downstream_feat": feat["downstream_feat"],
                "gate_decision_dependency_feat_refs": feat["gate_decision_dependency_feat_refs"],
                "admission_dependency_feat_refs": feat["admission_dependency_feat_refs"],
            }
            for feat in feats
        ],
        "glossary": glossary,
        "prohibited_inference_rules": inference_rules,
        "target_workflows": [
            {
                "workflow": "workflow.dev.feat_to_tech",
                "purpose": "derive the governed TECH package, with conditional ARCH / API companions, from the frozen FEAT slice",
            },
            {
                "workflow": "workflow.qa.feat_to_testset",
                "purpose": "derive the governed TESTSET package from the same frozen FEAT acceptance boundary",
            },
        ],
        "derivable_children": ["TECH", "TESTSET"],
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
        "workflow_run_id": active_run_id,
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
            "business_value_problem": ensure_list(package.epic_json.get("business_value_problem")),
            "product_positioning": package.epic_json.get("product_positioning"),
            "actors_and_roles": package.epic_json.get("actors_and_roles"),
            "scope": ensure_list(package.epic_json.get("scope")),
            "upstream_and_downstream": ensure_list(package.epic_json.get("upstream_and_downstream")),
            "epic_success_criteria": ensure_list(package.epic_json.get("epic_success_criteria") or package.epic_json.get("success_metrics")),
            "non_goals": ensure_list(package.epic_json.get("non_goals")),
            "decomposition_rules": ensure_list(package.epic_json.get("decomposition_rules")),
            "product_behavior_slices": package.epic_json.get("product_behavior_slices") or [],
            "constraints_and_dependencies": ensure_list(package.epic_json.get("constraints_and_dependencies")),
            "rollout_requirement": package.epic_json.get("rollout_requirement"),
            "rollout_plan": package.epic_json.get("rollout_plan"),
            "prerequisite_foundations": prerequisites,
        },
        "glossary": glossary,
        "boundary_matrix": boundary_matrix,
        "features": feats,
        "feat_track_map": feat_track_map,
        "prohibited_inference_rules": inference_rules,
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
                "epic_fields": ["scope", "product_behavior_slices", "decomposition_rules"],
                "source_refs": [epic_ref, f"product.src-to-epic::{package.run_id}"],
            },
        ],
        "feat_count_assessment": assessment,
        "semantic_lock": normalize_semantic_lock(package.epic_json.get("semantic_lock") or package.epic_frontmatter.get("semantic_lock")),
        "semantic_drift_check": semantic_drift_check,
    }
    if revision_summary:
        json_payload["revision_context"] = package.epic_json.get("revision_context") or {
            "revision_request_ref": revision_request_ref,
            "workflow_key": str(revision_request.get("workflow_key") or "").strip(),
            "run_id": str(revision_request.get("run_id") or "").strip(),
            "source_run_id": str(revision_request.get("source_run_id") or "").strip(),
            "decision_type": str(revision_request.get("decision_type") or "").strip(),
            "decision_target": str(revision_request.get("decision_target") or "").strip(),
            "decision_reason": str(revision_request.get("decision_reason") or revision_request.get("reason") or "").strip(),
            "revision_round": revision_request.get("revision_round"),
            "basis_refs": ensure_list(revision_request.get("basis_refs")),
            "source_gate_decision_ref": str(revision_request.get("source_gate_decision_ref") or "").strip(),
            "source_return_job_ref": str(revision_request.get("source_return_job_ref") or "").strip(),
            "authoritative_input_ref": str(revision_request.get("authoritative_input_ref") or "").strip(),
            "candidate_ref": str(revision_request.get("candidate_ref") or "").strip(),
            "original_input_path": str(revision_request.get("original_input_path") or "").strip(),
            "triggered_by_request_id": str(revision_request.get("triggered_by_request_id") or "").strip(),
            "trace": revision_request.get("trace") if isinstance(revision_request.get("trace"), dict) else {},
            "summary": revision_summary,
        }

    frontmatter = {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat",
        "workflow_run_id": active_run_id,
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_ref,
        "src_root_id": package.epic_json.get("src_root_id"),
        "feat_refs": [feat["feat_ref"] for feat in feats],
        "downstream_workflows": DOWNSTREAM_WORKFLOWS,
        "source_refs": source_refs,
        "semantic_lock": normalize_semantic_lock(package.epic_json.get("semantic_lock") or package.epic_frontmatter.get("semantic_lock")),
    }
    if revision_summary:
        frontmatter["revision_context"] = json_payload["revision_context"]

    epic_context_lines = [
        f"- epic_freeze_ref: `{epic_ref}`",
        f"- src_root_id: `{package.epic_json.get('src_root_id')}`",
        f"- business_goal: {package.epic_json.get('business_goal')}",
        f"- product_positioning: {package.epic_json.get('product_positioning')}",
    ]
    business_value_problem = ensure_list(package.epic_json.get("business_value_problem"))
    if business_value_problem:
        epic_context_lines.append("- business_value_problem:")
        epic_context_lines.extend([f"  - {item}" for item in business_value_problem[:4]])
    actors = package.epic_json.get("actors_and_roles") or []
    if isinstance(actors, list) and actors:
        epic_context_lines.append("- actors_and_roles:")
        for actor in actors[:5]:
            if isinstance(actor, dict):
                epic_context_lines.append(f"  - {actor.get('role')}: {actor.get('responsibility')}")
    epic_scope = ensure_list(package.epic_json.get("scope"))
    if epic_scope:
        epic_context_lines.append("- inherited_scope:")
        epic_context_lines.extend([f"  - {item}" for item in epic_scope[:5]])
    upstream_downstream = ensure_list(package.epic_json.get("upstream_and_downstream"))
    if upstream_downstream:
        epic_context_lines.append("- upstream_and_downstream:")
        epic_context_lines.extend([f"  - {item}" for item in upstream_downstream[:4]])
    if prerequisites:
        epic_context_lines.append("- prerequisite_foundations:")
        epic_context_lines.extend([f"  - {item}" for item in prerequisites])
    product_behavior_slices = package.epic_json.get("product_behavior_slices") or []
    if isinstance(product_behavior_slices, list) and product_behavior_slices:
        epic_context_lines.append("- product_behavior_slices:")
        for item in product_behavior_slices[:6]:
            if isinstance(item, dict):
                epic_context_lines.append(
                    f"  - {item.get('name')}: {item.get('product_surface')} | completed_state={item.get('completed_state')}"
                )
    if revision_summary:
        epic_context_lines.append(f"- revision_context: {revision_summary}")

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

    glossary_lines = []
    for item in glossary:
        glossary_lines.extend(
            [
                f"### {item['term']}",
                "",
                f"- Canonical meaning: {item['canonical_meaning']}",
                f"- Owned by FEAT: {item['owned_by_feat'] or 'bundle'}",
                f"- Must not be confused with: {item['must_not_be_confused_with']}",
                "",
            ]
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
                    f"- Business value: {feat['business_value']}",
                    "- Upstream FEATs:",
                    *([f"  - {item}" for item in feat["upstream_feat"]] or ["  - None"]),
                    "- Downstream FEATs:",
                    *([f"  - {item}" for item in feat["downstream_feat"]] or ["  - None"]),
                    "- Consumes:",
                    *([f"  - {item}" for item in feat["consumes"]] or ["  - None"]),
                    "- Produces:",
                    *([f"  - {item}" for item in feat["produces"]] or ["  - None"]),
                    f"- Authoritative artifact: {feat['authoritative_artifact']}",
                    "- Gate decision dependency FEAT refs:",
                    *([f"  - {item}" for item in feat["gate_decision_dependency_feat_refs"]] or ["  - None"]),
                    f"- Gate decision dependency: {feat['gate_decision_dependency']}",
                    "- Admission dependency FEAT refs:",
                    *([f"  - {item}" for item in feat["admission_dependency_feat_refs"]] or ["  - None"]),
                    f"- Admission dependency: {feat['admission_dependency']}",
                    "",
                    "#### Identity and Scenario",
                    f"- Product interface: {feat['identity_and_scenario']['product_interface']}",
                    f"- Completed state: {feat['identity_and_scenario']['completed_state']}",
                    f"- Primary actor: {feat['identity_and_scenario']['primary_actor']}",
                    "- Secondary actors:",
                    *[f"  - {item}" for item in feat["identity_and_scenario"]["secondary_actors"]],
                    f"- User story: {feat['identity_and_scenario']['user_story']}",
                    f"- Trigger: {feat['identity_and_scenario']['trigger']}",
                    "- Preconditions:",
                    *[f"  - {item}" for item in feat["identity_and_scenario"]["preconditions"]],
                    "- Postconditions:",
                    *[f"  - {item}" for item in feat["identity_and_scenario"]["postconditions"]],
                    "",
                    "#### Business Flow",
                    "- Main flow:",
                    *[f"  - {item}" for item in feat["business_flow"]["main_flow"]],
                    "- Alternate flows:",
                    *([f"  - {item}" for item in feat["business_flow"]["alternate_flows"]] or ["  - None"]),
                    "- Exception / reject / retry flows:",
                    *([f"  - {item}" for item in feat["business_flow"]["exception_flows"]] or ["  - None"]),
                    "- Business rules:",
                    *[f"  - {item}" for item in feat["business_flow"]["business_rules"]],
                    "- Business state transitions:",
                    *[f"  - {item}" for item in feat["business_flow"]["business_state_transitions"]],
                    "",
                    "#### Product Objects and Deliverables",
                    "- Input objects:",
                    *[f"  - {item}" for item in feat["product_objects_and_deliverables"]["input_objects"]],
                    "- Output objects:",
                    *[f"  - {item}" for item in feat["product_objects_and_deliverables"]["output_objects"]],
                    "- Required deliverables:",
                    *[f"  - {item}" for item in feat["product_objects_and_deliverables"]["required_deliverables"]],
                    f"- Authoritative output: {feat['product_objects_and_deliverables']['authoritative_output']}",
                    f"- Business deliverable: {feat['product_objects_and_deliverables']['business_deliverable']}",
                    "- Governance intermediates:",
                    *([f"  - {item}" for item in feat["product_objects_and_deliverables"]["governance_intermediates"]] or ["  - None"]),
                    "- Evidence / audit trail:",
                    *[f"  - {item}" for item in feat["product_objects_and_deliverables"]["evidence_audit_trail"]],
                    "",
                    "#### Collaboration and Timeline",
                    "- Role responsibility split:",
                    *[f"  - {item}" for item in feat["collaboration_and_timeline"]["role_responsibility_split"]],
                    "- Handoff points:",
                    *[f"  - {item}" for item in feat["collaboration_and_timeline"]["handoff_points"]],
                    "- Interaction timeline:",
                    *[f"  - {item}" for item in feat["collaboration_and_timeline"]["interaction_timeline"]],
                    "- Business sequence:",
                    feat["collaboration_and_timeline"]["business_sequence"],
                    "- Loop / gate / human involvement points:",
                    *([f"  - {item}" for item in feat["collaboration_and_timeline"]["loop_gate_human_involvement"]] or ["  - None"]),
                    "- Cross-cutting capability axes:",
                    *([f"  - {item}" for item in feat["cross_cutting_capability_axes"]] or ["  - None"]),
                    "",
                    "#### Acceptance and Testability",
                    "- Acceptance criteria:",
                    *[f"  - {item}" for item in feat["acceptance_and_testability"]["acceptance_criteria"]],
                    "- Observable outcomes:",
                    *[f"  - {item}" for item in feat["acceptance_and_testability"]["observable_outcomes"]],
                    "- Test dimensions:",
                    *[f"  - {item}" for item in feat["acceptance_and_testability"]["test_dimensions"]],
                    "- Out of scope:",
                    *[f"  - {item}" for item in feat["acceptance_and_testability"]["out_of_scope"]],
                    "- Structured acceptance checks:",
                    *[
                        f"  - {check['id']}: {check['scenario']} | given {check['given']} | when {check['when']} | then {check['then']}"
                        for check in feat["acceptance_checks"]
                    ],
                    "",
                    "#### Frozen Downstream Boundary",
                    "- Frozen product shape:",
                    *[f"  - {item}" for item in feat["frozen_downstream_boundary"]["frozen_product_shape"]],
                    "- Frozen business semantics:",
                    *[f"  - {item}" for item in feat["frozen_downstream_boundary"]["frozen_business_semantics"]],
                    "- Open technical decisions:",
                    *[f"  - {item}" for item in feat["frozen_downstream_boundary"]["open_technical_decisions"]],
                    "- Explicit non-decisions:",
                    *[f"  - {item}" for item in feat["frozen_downstream_boundary"]["explicit_non_decisions"]],
                    "",
                    "- Scope:",
                    *[f"  - {item}" for item in feat["scope"]],
                    "- Dependencies:",
                    *([f"  - {item}" for item in feat["dependencies"]] or ["  - None"]),
                    "- Constraints:",
                    *[f"  - {item}" for item in feat["constraints"]],
                ]
            )
        )

    prohibited_rule_lines = []
    for item in inference_rules:
        prohibited_rule_lines.extend(
            [
                f"### {item['id']}",
                "",
                f"- Applies to: {', '.join(item['applies_to'])}",
                f"- Rule: {item['rule']}",
                f"- Protected fields: {', '.join(item['protected_fields'])}",
                "",
            ]
        )

    markdown_body = "\n\n".join(
        [
            f"# {json_payload['title']}",
            "## FEAT Bundle Intent\n\n" + json_payload["bundle_intent"] + "\n\n" + "\n".join(bundle_shared_non_goal_lines),
            "## EPIC Context\n\n" + "\n".join(epic_context_lines),
            "## Canonical Glossary\n\n" + "\n".join(glossary_lines).strip(),
            "## Boundary Matrix\n\n" + "\n\n".join(boundary_matrix_sections),
            "## FEAT Inventory\n\n" + "\n\n".join(feat_inventory_sections),
            "## Prohibited Inference Rules\n\n" + "\n".join(prohibited_rule_lines).strip(),
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
                    "- Authoritative artifact map:",
                    *[
                        f"  - {item['feat_ref']}: {item['authoritative_artifact']}"
                        for item in handoff["authoritative_artifact_map"]
                    ],
                    "- Feature dependency map:",
                    *[
                        f"  - {item['feat_ref']}: upstream={item['upstream_feat'] or ['None']}, downstream={item['downstream_feat'] or ['None']}, gate={item['gate_decision_dependency_feat_refs'] or ['None']}, admission={item['admission_dependency_feat_refs'] or ['None']}"
                        for item in handoff["feature_dependency_map"]
                    ],
                    "- Derived child artifacts:",
                    "  - TECH",
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
            "Downstream handoff metadata preserves governed TECH and TESTSET workflow targets.",
            "FEAT track mapping preserves the foundation vs adoption/E2E overlay split for downstream flows.",
            "Boundary matrix records the horizontal split between FEAT responsibilities and adjacent non-responsibilities.",
        ],
        "decision": review_decision,
        "risks": [defect["detail"] for defect in defects],
        "recommendations": [
            "Keep downstream TECH and TESTSET derivation anchored to FEAT acceptance checks.",
            "Do not re-open the parent EPIC scope in downstream design or QA derivation stages.",
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
            "downstream_readiness": {"status": "pass", "note": "Output remains actionable for downstream TECH and TESTSET derivation."},
            "structured_acceptance_checks": {"status": "pass", "note": "Each FEAT includes structured acceptance checks."},
            "evidence_completeness": {"status": "pass", "note": "Execution and supervision evidence will ship with the package."},
        },
        "summary": "FEAT acceptance review passed." if not defects else "FEAT acceptance review requires revision.",
        "acceptance_findings": defects,
        "created_at": utc_now(),
    }
    if revision_summary:
        review_report["findings"].extend(review_report_findings)
        acceptance_report["dimensions"]["revision_response"] = {
            "status": "pass",
            "note": revision_summary,
        }

    return GeneratedFeatBundle(
        frontmatter=frontmatter,
        markdown_body=markdown_body,
        json_payload=json_payload,
        review_report=review_report,
        acceptance_report=acceptance_report,
        defect_list=defects,
        handoff=handoff,
        semantic_drift_check=semantic_drift_check,
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
    drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
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
    if drift_check.get("semantic_lock_present") and drift_check.get("semantic_lock_preserved") is not True:
        errors.append("semantic-drift-check.json must report semantic_lock_preserved=true when semantic_lock is present.")
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
            if not feature.get("slice_id"):
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include slice_id.")
            if len(feature.get("acceptance_checks") or []) < 3:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least three acceptance checks.")
            if len(feature.get("constraints") or []) < 4:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least four constraints.")
            if len(feature.get("scope") or []) < 3:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include at least three scope bullets.")
            for field in [
                "upstream_feat",
                "downstream_feat",
                "consumes",
                "produces",
                "authoritative_artifact",
                "gate_decision_dependency_feat_refs",
                "gate_decision_dependency",
                "admission_dependency_feat_refs",
                "admission_dependency",
                "dependency_kinds",
            ]:
                if field not in feature:
                    errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include {field}.")
            for field in [
                "business_value",
                "identity_and_scenario",
                "business_flow",
                "product_objects_and_deliverables",
                "collaboration_and_timeline",
                "acceptance_and_testability",
                "frozen_downstream_boundary",
            ]:
                if not isinstance(feature.get(field), dict if field != "business_value" else str):
                    errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include {field}.")
            identity = feature.get("identity_and_scenario") or {}
            if not identity.get("user_story") or not identity.get("trigger"):
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} identity_and_scenario must include user_story and trigger.")
            if not identity.get("product_interface") or not identity.get("completed_state"):
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} identity_and_scenario must include product_interface and completed_state.")
            business_flow = feature.get("business_flow") or {}
            if len(business_flow.get("main_flow") or []) < 3:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} business_flow.main_flow must include at least three steps.")
            product_objects = feature.get("product_objects_and_deliverables") or {}
            if not product_objects.get("authoritative_output"):
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include an authoritative_output.")
            if not product_objects.get("business_deliverable"):
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include a business_deliverable.")
            collaboration = feature.get("collaboration_and_timeline") or {}
            if not collaboration.get("business_sequence"):
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include a business_sequence.")
            if len(collaboration.get("loop_gate_human_involvement") or []) < 1:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include loop_gate_human_involvement.")
            acceptance = feature.get("acceptance_and_testability") or {}
            if len(acceptance.get("test_dimensions") or []) < 4:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} must include explicit test_dimensions.")
            frozen = feature.get("frozen_downstream_boundary") or {}
            if len(frozen.get("frozen_product_shape") or []) < 1 or len(frozen.get("open_technical_decisions") or []) < 1:
                errors.append(f"Feature {feature.get('feat_ref') or '<unknown>'} frozen_downstream_boundary is incomplete.")

    boundary_matrix = feat_json.get("boundary_matrix")
    if not isinstance(boundary_matrix, list) or len(boundary_matrix) != len(feat_refs):
        errors.append("feat-freeze-bundle.json must include a boundary_matrix aligned to feat_refs.")
    shared_non_goals = feat_json.get("bundle_shared_non_goals")
    if not isinstance(shared_non_goals, list) or not shared_non_goals:
        errors.append("feat-freeze-bundle.json must include bundle_shared_non_goals.")
    acceptance_conventions = feat_json.get("bundle_acceptance_conventions")
    if not isinstance(acceptance_conventions, list) or not acceptance_conventions:
        errors.append("feat-freeze-bundle.json must include bundle_acceptance_conventions.")
    glossary = feat_json.get("glossary")
    if not isinstance(glossary, list) or not glossary:
        errors.append("feat-freeze-bundle.json must include a non-empty glossary.")
    prohibited_rules = feat_json.get("prohibited_inference_rules")
    if not isinstance(prohibited_rules, list) or not prohibited_rules:
        errors.append("feat-freeze-bundle.json must include prohibited_inference_rules.")

    markdown_text = (artifacts_dir / "feat-freeze-bundle.md").read_text(encoding="utf-8")
    _, markdown_body = parse_markdown_frontmatter(markdown_text)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if f"## {heading}" not in markdown_body:
            errors.append(f"feat-freeze-bundle.md is missing section: {heading}")
    for heading in REQUIRED_FEAT_SUBHEADINGS:
        if heading not in markdown_body:
            errors.append(f"feat-freeze-bundle.md is missing feature subsection: {heading}")

    handoff = load_json(artifacts_dir / "handoff-to-feat-downstreams.json")
    if not isinstance(handoff.get("glossary"), list) or not handoff.get("glossary"):
        errors.append("handoff-to-feat-downstreams.json must include glossary.")
    if not isinstance(handoff.get("prohibited_inference_rules"), list) or not handoff.get("prohibited_inference_rules"):
        errors.append("handoff-to-feat-downstreams.json must include prohibited_inference_rules.")
    if not isinstance(handoff.get("authoritative_artifact_map"), list) or not handoff.get("authoritative_artifact_map"):
        errors.append("handoff-to-feat-downstreams.json must include authoritative_artifact_map.")
    if not isinstance(handoff.get("feature_dependency_map"), list) or not handoff.get("feature_dependency_map"):
        errors.append("handoff-to-feat-downstreams.json must include feature_dependency_map.")
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
        "semantic_lock_preserved": drift_check.get("semantic_lock_preserved"),
    }


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors

    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    checks = gate.get("checks") or {}
    readiness_errors = [name for name, status in checks.items() if status is not True]
    return not readiness_errors, readiness_errors


def executor_run(
    input_path: str | Path,
    repo_root: Path,
    run_id: str,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, repo_root)
    if errors:
        raise ValueError("; ".join(errors))

    resolved_input_dir, _ = resolve_input_artifacts_dir(input_path, repo_root)
    package = load_epic_package(resolved_input_dir)
    effective_run_id = run_id or package.run_id
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")
    revision_request_ref, revision_request = _materialize_revision_request(output_dir, revision_request_path)
    generated = build_feat_bundle(
        package,
        workflow_run_id=effective_run_id,
        revision_request_ref=revision_request_ref,
        revision_request=revision_request,
    )

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
        "input_mode": validation.get("input_mode", "package_dir"),
        "epic_freeze_ref": generated.frontmatter["epic_freeze_ref"],
        "feat_refs": generated.frontmatter["feat_refs"],
    }


def supervisor_review(
    artifacts_dir: Path,
    repo_root: Path,
    run_id: str,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
    del allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    package_manifest = load_json(artifacts_dir / "package-manifest.json")
    input_package_dir = Path(str(package_manifest.get("input_artifacts_dir") or "")).resolve()
    if not input_package_dir.exists():
        raise FileNotFoundError(f"Input package directory not found: {input_package_dir}")

    package = load_epic_package(input_package_dir)
    revision_request_ref, revision_request = _load_revision_request(artifacts_dir, revision_request_path)
    generated = build_feat_bundle(
        package,
        workflow_run_id=run_id or artifacts_dir.name,
        revision_request_ref=revision_request_ref,
        revision_request=revision_request,
    )
    supervision = build_supervision_evidence(artifacts_dir, generated)
    gate = build_gate_result(generated, supervision)

    update_supervisor_outputs(artifacts_dir, repo_root, generated, supervision, gate)

    proposal_ref = ""
    gate_ready_package_ref = ""
    authoritative_handoff_ref = ""
    gate_pending_ref = ""
    if gate["freeze_ready"]:
        active_run_id = run_id or str(generated.frontmatter.get("workflow_run_id") or artifacts_dir.name)
        proposal_path = create_handoff_proposal(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
            epic_freeze_ref=str(generated.frontmatter["epic_freeze_ref"]),
            src_root_id=str(generated.frontmatter["src_root_id"]),
            feat_refs=[str(item) for item in generated.frontmatter["feat_refs"]],
        )
        gate_ready_package = create_gate_ready_package(
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
            candidate_ref=f"epic-to-feat.{active_run_id}.feat-freeze-bundle",
            machine_ssot_ref=(artifacts_dir / "feat-freeze-bundle.json").resolve().relative_to(repo_root.resolve()).as_posix(),
            acceptance_ref=(artifacts_dir / "feat-acceptance-report.json").resolve().relative_to(repo_root.resolve()).as_posix(),
            evidence_bundle_ref=(artifacts_dir / "supervision-evidence.json").resolve().relative_to(repo_root.resolve()).as_posix(),
        )
        gate_submit = submit_gate_pending(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
            proposal_ref=proposal_path.resolve().relative_to(repo_root.resolve()).as_posix(),
            payload_path=gate_ready_package,
            trace_context_ref=(artifacts_dir / "execution-evidence.json").resolve().relative_to(repo_root.resolve()).as_posix(),
        )
        gate_submit_data = gate_submit["response"]["data"]
        package_manifest["handoff_proposal_ref"] = proposal_path.resolve().relative_to(repo_root.resolve()).as_posix()
        package_manifest["gate_ready_package_ref"] = gate_ready_package.resolve().relative_to(repo_root.resolve()).as_posix()
        package_manifest["authoritative_handoff_ref"] = str(gate_submit_data.get("handoff_ref", ""))
        package_manifest["gate_pending_ref"] = str(gate_submit_data.get("gate_pending_ref", ""))
        package_manifest["gate_submit_cli_ref"] = gate_submit["response_path"].resolve().relative_to(repo_root.resolve()).as_posix()
        dump_json(artifacts_dir / "package-manifest.json", package_manifest)
        proposal_ref = package_manifest["handoff_proposal_ref"]
        gate_ready_package_ref = package_manifest["gate_ready_package_ref"]
        authoritative_handoff_ref = package_manifest["authoritative_handoff_ref"]
        gate_pending_ref = package_manifest["gate_pending_ref"]

    return {
        "ok": True,
        "run_id": run_id or str(generated.frontmatter.get("workflow_run_id") or artifacts_dir.name),
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "freeze_ready": gate["freeze_ready"],
        "revision_request_ref": revision_request_ref,
        "handoff_proposal_ref": proposal_ref,
        "gate_ready_package_ref": gate_ready_package_ref,
        "authoritative_handoff_ref": authoritative_handoff_ref,
        "gate_pending_ref": gate_pending_ref,
    }


def run_workflow(
    input_path: str | Path,
    repo_root: Path,
    run_id: str,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
        revision_request_path=revision_request_path,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(
        artifacts_dir=artifacts_dir,
        repo_root=repo_root,
        run_id=run_id or executor_result["run_id"],
        allow_update=True,
        revision_request_path=revision_request_path,
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
        "input_mode": executor_result.get("input_mode", "package_dir"),
        "epic_freeze_ref": executor_result["epic_freeze_ref"],
        "feat_refs": executor_result["feat_refs"],
        "supervision": supervisor_result,
        "revision_request_ref": supervisor_result.get("revision_request_ref", ""),
        "handoff_proposal_ref": supervisor_result.get("handoff_proposal_ref", ""),
        "gate_ready_package_ref": supervisor_result.get("gate_ready_package_ref", ""),
        "authoritative_handoff_ref": supervisor_result.get("authoritative_handoff_ref", ""),
        "gate_pending_ref": supervisor_result.get("gate_pending_ref", ""),
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }
