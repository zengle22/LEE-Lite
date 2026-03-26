#!/usr/bin/env python3
"""
Lite-native runtime support for src-to-epic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src_to_epic_derivation import (
    assess_rollout_requirement,
    choose_epic_freeze_ref,
    choose_src_root_id,
    derive_actors_and_roles,
    derive_optional_architecture_refs,
    derive_business_value_problem,
    derive_business_goal,
    derive_capability_axes,
    derive_constraint_groups,
    derive_decomposition_rules,
    derive_epic_title,
    derive_non_goals,
    derive_product_positioning,
    derive_product_behavior_slices,
    derive_rollout_plan,
    derive_scope,
    derive_success_metrics,
    derive_traceability,
    derive_upstream_downstream,
    derive_validation_findings,
    epic_source_refs,
    flatten_constraint_groups,
    is_review_projection_package,
    multi_feat_score,
    prerequisite_foundations,
    semantic_lock,
)
from src_to_epic_common import (
    dump_json,
    ensure_list,
    guess_repo_root_from_input,
    load_json,
    load_src_package,
    normalize_semantic_lock,
    parse_markdown_frontmatter,
    unique_strings,
    validate_input_package,
)
from src_to_epic_cli_integration import (
    build_gate_result,
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    write_executor_outputs,
)
REQUIRED_OUTPUT_FILES = (
    "epic-freeze.md", "epic-freeze.json", "epic-review-report.json", "epic-acceptance-report.json",
    "epic-defect-list.json", "epic-freeze-gate.json", "handoff-to-epic-to-feat.json", "semantic-drift-check.json",
    "execution-evidence.json", "supervision-evidence.json",
)
REQUIRED_MARKDOWN_HEADINGS = (
    "Epic Intent", "Business Goal", "Business Value and Problem", "Product Positioning", "Actors and Roles",
    "Capability Scope", "Upstream and Downstream", "Epic Success Criteria", "Non-Goals", "Decomposition Rules",
    "Rollout and Adoption", "Constraints and Dependencies", "Acceptance and Review", "Downstream Handoff",
    "Traceability",
)
def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "src-to-epic" / run_id


@dataclass
class GeneratedEpic:
    frontmatter: dict[str, Any]
    markdown_body: str
    json_payload: dict[str, Any]
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    handoff: dict[str, Any]
    rollout_plan: dict[str, Any]
    semantic_drift_check: dict[str, Any]


def build_semantic_drift_check(
    package: Any,
    epic_title: str,
    business_goal: str,
    scope: list[str],
    product_behavior_slices: list[dict[str, Any]],
) -> dict[str, Any]:
    lock = semantic_lock(package)
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
            epic_title,
            business_goal,
            " ".join(scope),
            " ".join(str(item.get("name") or "") for item in product_behavior_slices),
            " ".join(str(item.get("goal") or "") for item in product_behavior_slices),
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
    summary = "semantic_lock preserved." if preserved else "semantic_lock drift detected."
    return {
        "verdict": "pass" if preserved else "reject",
        "semantic_lock_present": True,
        "semantic_lock_preserved": preserved,
        "domain_type": lock.get("domain_type"),
        "one_sentence_truth": lock.get("one_sentence_truth"),
        "forbidden_axis_detected": forbidden_hits,
        "anchor_matches": anchor_matches,
        "summary": summary,
    }


def build_epic_payload(package: Any, workflow_run_id: str | None = None) -> GeneratedEpic:
    active_run_id = workflow_run_id or package.run_id
    src_root_id = choose_src_root_id(package)
    rollout_requirement, epic_freeze_ref, epic_title = assess_rollout_requirement(package), choose_epic_freeze_ref(package), derive_epic_title(package)
    capability_axes = derive_capability_axes(package, rollout_requirement)
    product_behavior_slices = derive_product_behavior_slices(package, rollout_requirement)
    scope = derive_scope(package, capability_axes, product_behavior_slices)
    non_goals, success_metrics = derive_non_goals(package, rollout_requirement), derive_success_metrics(package, capability_axes, product_behavior_slices)
    decomposition_rules, constraint_groups = derive_decomposition_rules(package, capability_axes, product_behavior_slices), derive_constraint_groups(package, rollout_requirement)
    constraints = flatten_constraint_groups(constraint_groups)
    traceability = derive_traceability(package, src_root_id)
    business_goal = derive_business_goal(package, capability_axes, product_behavior_slices)
    multi_feat = multi_feat_score(package)
    architecture_refs = derive_optional_architecture_refs(package, src_root_id); source_refs = epic_source_refs(package, src_root_id, architecture_refs)
    rollout_plan = derive_rollout_plan(package, rollout_requirement); validation_findings = derive_validation_findings(package, constraint_groups, decomposition_rules, success_metrics); prereq = prerequisite_foundations(package)
    business_value_problem = derive_business_value_problem(package)
    product_positioning = derive_product_positioning(package, capability_axes, product_behavior_slices)
    actors_and_roles = derive_actors_and_roles(package, rollout_requirement)
    upstream_downstream = derive_upstream_downstream(package, rollout_requirement)
    semantic_drift_check = build_semantic_drift_check(package, epic_title, business_goal, scope, product_behavior_slices)

    epic_intent = (
        f"将《{package.src_candidate.get('title') or package.run_id}》中的治理问题空间进一步收敛为“{epic_title}”这一 EPIC 级产品能力块，"
        "让下游可以围绕稳定的产品行为切片拆分 FEAT，并把 capability axes 保留在 cross-cutting constraints 层，"
        "而不是继续复述 SRC 原则或沿治理对象逐项平移。"
    )

    review_findings = [
        "EPIC 已从 SRC 原文上浮到产品能力块层，Scope 以产品行为切片而非治理对象清单表达。",
        f"Multi-FEAT readiness: {', '.join(multi_feat['reasons'])}.",
        "输出追溯链同时保留了 raw-to-src 批次引用、src_root_id 与原始 source_refs。",
        "Decomposition Rules 已显式给出产品行为切片、cross-cutting constraints 与 rollout overlay 规则。",
    ]
    if rollout_requirement["required"]:
        review_findings.append("该 SRC 命中 rollout/adoption 判定，主 EPIC 已显式包含 rollout 段落与 adoption/E2E FEAT 拆分要求。")
    review_risks = [] if multi_feat["is_multi_feat_ready"] else ["当前输入显示的独立能力边界不足，可能更适合直接落到 FEAT 层。"]

    acceptance_dimensions = {
        "multi_feat_boundary": {
            "status": "pass" if multi_feat["is_multi_feat_ready"] else "fail",
            "note": "EPIC 保持为多 FEAT 能力边界。" if multi_feat["is_multi_feat_ready"] else "EPIC 可能塌缩为单 FEAT。",
        },
        "goal_scope_clarity": {"status": "pass", "note": "业务目标、scope、non-goals 已显式化。"},
        "decomposition_readiness": {"status": "pass", "note": "已给出下游 FEAT 拆分规则、建议 FEAT 轴与 handoff。"},
        "constraint_preservation": {"status": "pass", "note": "关键约束和上游 inheritance requirements 已保留。"},
        "traceability": {"status": "pass", "note": "输出包含 raw-to-src run ref、src_root_id 与 source_refs。"},
        "evidence_completeness": {"status": "pass", "note": "执行与监督证据将作为 package artifacts 一并落盘。"},
        "rollout_adoption_readiness": {
            "status": "pass",
            "note": "主 EPIC 已显式给出 rollout/adoption/E2E 拆分要求。"
            if rollout_requirement["required"]
            else "当前 SRC 不需要单独的 rollout/adoption/E2E FEAT 族。",
        },
    }

    defects: list[dict[str, Any]] = list(validation_findings)
    if semantic_drift_check["verdict"] == "reject":
        defects.append(
            {
                "severity": "P1",
                "title": "semantic_lock drift detected",
                "detail": semantic_drift_check["summary"],
            }
        )
    if not multi_feat["is_multi_feat_ready"]:
        defects.append(
            {
                "severity": "P1",
                "title": "EPIC boundary may collapse to a single FEAT",
                "detail": "The input package does not show enough independent capability slices to justify an EPIC.",
            }
        )
    if validation_findings:
        acceptance_dimensions["constraint_preservation"] = {
            "status": "fail",
            "note": "EPIC 约束分层或下游保留规则不完整，需要修订。",
        }
        acceptance_dimensions["decomposition_readiness"] = {
            "status": "fail",
            "note": "主轴/切面或完成定义不完整，不能稳定下传到 epic-to-feat。",
        }

    acceptance_decision = "approve" if not defects else "revise"
    review_decision = "pass" if not defects else "revise"

    handoff = {
        "handoff_id": f"handoff-{active_run_id}-to-epic-to-feat",
        "from_skill": "ll-product-src-to-epic",
        "to_skill": "product.epic-to-feat",
        "source_run_id": active_run_id,
        "epic_freeze_ref": epic_freeze_ref,
        "src_root_id": src_root_id,
        "primary_artifact_ref": "epic-freeze.md",
        "supporting_artifact_refs": ["epic-freeze.json", "epic-review-report.json", "epic-acceptance-report.json", "epic-defect-list.json"],
        "required_context": ["epic intent and business goal", "decomposition rules", "rollout and adoption requirements", "constraints and dependencies", "traceability map"],
        "expected_output_type": "feat_freeze_package",
        "rollout_required": rollout_requirement["required"],
        "required_feat_tracks": rollout_plan["required_feat_tracks"],
        "prerequisite_foundations": prereq,
        "created_at": utc_now(),
    }

    json_payload = {
        "artifact_type": "epic_freeze_package",
        "workflow_key": "product.src-to-epic",
        "workflow_run_id": active_run_id,
        "title": epic_title,
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "epic_kind": "primary",
        "epic_freeze_ref": epic_freeze_ref,
        "src_root_id": src_root_id,
        "downstream_workflow": "product.epic-to-feat",
        "source_refs": source_refs,
        "epic_intent": epic_intent,
        "business_goal": business_goal,
        "business_value_problem": business_value_problem,
        "product_positioning": product_positioning,
        "actors_and_roles": actors_and_roles,
        "scope": scope,
        "upstream_and_downstream": upstream_downstream,
        "non_goals": non_goals,
        "epic_success_criteria": success_metrics,
        "success_metrics": success_metrics,
        "decomposition_rules": decomposition_rules,
        "capability_axes": capability_axes,
        "product_behavior_slices": product_behavior_slices,
        "feat_axis_mapping": [
            {
                "product_behavior_slice": item["name"],
                "cross_cutting_capability_axes": item.get("capability_axes") or [],
                "track": item.get("track") or "foundation",
            }
            for item in product_behavior_slices
        ],
        "constraint_groups": constraint_groups,
        "constraints_and_dependencies": constraints,
        "acceptance_and_review": {
            "upstream_acceptance_decision": package.acceptance_report.get("decision"),
            "upstream_acceptance_summary": package.acceptance_report.get("summary"),
            "semantic_review_decision": package.source_semantic_findings.get("decision"),
            "semantic_review_summary": package.source_semantic_findings.get("summary"),
            "epic_review_decision": review_decision,
            "epic_acceptance_decision": acceptance_decision,
        },
        "downstream_handoff": handoff,
        "traceability": traceability,
        "multi_feat_assessment": multi_feat,
        "rollout_requirement": rollout_requirement,
        "rollout_plan": rollout_plan,
        "prerequisite_foundations": prereq,
        "semantic_lock": semantic_lock(package) or None,
        "semantic_drift_check": semantic_drift_check,
    }

    frontmatter = {
        "artifact_type": "epic_freeze_package",
        "workflow_key": "product.src-to-epic",
        "workflow_run_id": active_run_id,
        "status": "accepted" if not defects else "revised",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_freeze_ref,
        "src_root_id": src_root_id,
        "downstream_workflow": "product.epic-to-feat",
        "source_refs": source_refs,
        "rollout_required": rollout_requirement["required"],
        "semantic_lock": semantic_lock(package) or None,
    }

    rollout_lines = [f"- rollout_required: `{str(rollout_requirement['required']).lower()}`", f"- trigger_score: `{rollout_requirement['score']}`"]
    rollout_lines.extend(f"- {item}" for item in rollout_requirement["rationale"])
    rollout_lines.append(f"- required_feat_tracks: `{', '.join(rollout_plan['required_feat_tracks'])}`")
    rollout_lines.extend(f"- {item}" for item in rollout_plan["planning_notes"])
    rollout_lines.extend(f"- prerequisite foundation: {item}" for item in prereq)
    if rollout_plan["required_feat_families"]:
        rollout_lines.append("- required_feat_families:")
        for item in rollout_plan["required_feat_families"]:
            rollout_lines.append(f"  - {item['family']}: {item['goal']}")

    markdown_body = "\n\n".join(
        [
            f"# {json_payload['title']}",
            "## Epic Intent\n\n" + epic_intent,
            "## Business Goal\n\n" + business_goal,
            "## Business Value and Problem\n\n" + "\n".join(f"- {item}" for item in business_value_problem),
            "## Product Positioning\n\n" + product_positioning,
            "## Actors and Roles\n\n" + "\n".join(f"- {item['role']}：{item['responsibility']}" for item in actors_and_roles),
            "## Capability Scope\n\n" + "\n".join(f"- {item}" for item in scope),
            "## Upstream and Downstream\n\n" + "\n".join(f"- {item}" for item in upstream_downstream),
            "## Epic Success Criteria\n\n" + "\n".join(f"- {item}" for item in success_metrics),
            "## Non-Goals\n\n" + "\n".join(f"- {item}" for item in non_goals),
            "## Decomposition Rules\n\n"
            + "\n".join(f"- {item}" for item in decomposition_rules)
            + (
                "\n- 建议产品行为切片：\n"
                + "\n".join(
                    f"  - {item['name']} <- {', '.join(item.get('capability_axes') or ['未声明 cross-cutting capability axis'])}"
                    for item in product_behavior_slices
                )
                if product_behavior_slices
                else ""
            ),
            "## Rollout and Adoption\n\n" + "\n".join(rollout_lines),
            "## Constraints and Dependencies\n\n"
            + "\n\n".join(
                f"### {group['name']}\n\n" + "\n".join(f"- {item}" for item in group["items"])
                for group in constraint_groups
            ),
            "## Acceptance and Review\n\n"
            + "\n".join(
                [
                    f"- Upstream acceptance: {package.acceptance_report.get('decision')} ({package.acceptance_report.get('summary')})",
                    f"- Upstream semantic review: {package.source_semantic_findings.get('decision')} ({package.source_semantic_findings.get('summary')})",
                    f"- Epic review: {review_decision}",
                    f"- Epic acceptance: {acceptance_decision}",
                ]
            ),
            "## Downstream Handoff\n\n"
            + "\n".join(
                [
                    "- Next workflow: `product.epic-to-feat`",
                    f"- epic_freeze_ref: `{epic_freeze_ref}`",
                    f"- src_root_id: `{src_root_id}`",
                    *[f"- prerequisite foundation: {item}" for item in prereq],
                    "- Required carry-over: source refs, decomposition rules, constraints, acceptance evidence",
                ]
            ),
            "## Traceability\n\n"
            + "\n".join(
                f"- {item['epic_section']}: {', '.join(item['input_fields'])} <- {', '.join(item['source_refs'])}"
                for item in traceability
            ),
        ]
    )

    review_report = {
        "review_id": f"review-{active_run_id}",
        "review_type": "epic_review",
        "subject_refs": [epic_freeze_ref],
        "summary": "EPIC package preserves the SRC problem space at a multi-FEAT capability layer.",
        "findings": review_findings,
        "decision": review_decision,
        "risks": review_risks,
        "recommendations": [
            "在 epic-to-feat 阶段按 decomposition rules 继续拆分，不要重新定义问题空间。",
            "优先围绕产品行为切片冻结 FEAT，把 capability axes 保留为跨切片约束，而不是直接按能力轴平移。",
            "对路径与目录治理相关 FEAT 持续维持主链边界限定，避免滑向全局文件治理。",
            "保持 raw-to-src provenance、src_root_id 和 gate 分层在下游继续可见。",
            "若 rollout_required 为 true，需在 epic-to-feat 中强制拆出 adoption / integration / cross-skill E2E FEAT。",
        ],
        "created_at": utc_now(),
    }

    acceptance_report = {
        "stage_id": "epic_acceptance_review",
        "created_by_role": "supervisor",
        "decision": acceptance_decision,
        "dimensions": acceptance_dimensions,
        "summary": "Epic acceptance review passed." if not defects else "Epic acceptance review requires revision.",
        "acceptance_findings": defects,
        "created_at": utc_now(),
    }

    return GeneratedEpic(
        frontmatter=frontmatter,
        markdown_body=markdown_body,
        json_payload=json_payload,
        review_report=review_report,
        acceptance_report=acceptance_report,
        defect_list=defects,
        handoff=handoff,
        rollout_plan=rollout_plan,
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

    epic_json = load_json(artifacts_dir / "epic-freeze.json")
    if epic_json.get("artifact_type") != "epic_freeze_package":
        errors.append("epic-freeze.json artifact_type must be epic_freeze_package.")
    if epic_json.get("workflow_key") != "product.src-to-epic":
        errors.append("epic-freeze.json workflow_key must be product.src-to-epic.")
    if epic_json.get("downstream_workflow") != "product.epic-to-feat":
        errors.append("epic-freeze.json downstream_workflow must be product.epic-to-feat.")

    epic_freeze_ref = str(epic_json.get("epic_freeze_ref") or "")
    src_root_id = str(epic_json.get("src_root_id") or "")
    if not epic_freeze_ref:
        errors.append("epic-freeze.json must include epic_freeze_ref.")
    if not src_root_id:
        errors.append("epic-freeze.json must include src_root_id.")

    source_refs = ensure_list(epic_json.get("source_refs"))
    semantic_lock_payload = normalize_semantic_lock(epic_json.get("semantic_lock"))
    is_review_projection = str((semantic_lock_payload or {}).get("domain_type") or "").strip().lower() == "review_projection_rule"
    is_execution_runner = str((semantic_lock_payload or {}).get("domain_type") or "").strip().lower() == "execution_runner_rule"
    if not any(ref.startswith("product.raw-to-src::") for ref in source_refs):
        errors.append("epic-freeze.json source_refs must include product.raw-to-src::<run_id>.")
    if not any(ref.startswith("SRC-") for ref in source_refs):
        errors.append("epic-freeze.json source_refs must include SRC-*.")
    drift_check = load_json(artifacts_dir / "semantic-drift-check.json")
    if drift_check.get("semantic_lock_present") and drift_check.get("semantic_lock_preserved") is not True:
        errors.append("semantic-drift-check.json must report semantic_lock_preserved=true when semantic_lock is present.")
    rollout_requirement = epic_json.get("rollout_requirement") or {}
    rollout_plan = epic_json.get("rollout_plan") or {}
    if rollout_requirement.get("required") and "adoption_e2e" not in ensure_list(rollout_plan.get("required_feat_tracks")):
        errors.append("epic-freeze.json rollout_plan.required_feat_tracks must include adoption_e2e when rollout_requirement.required is true.")
    constraint_groups = epic_json.get("constraint_groups") or []
    group_map = {str(group.get("name") or ""): ensure_list(group.get("items")) for group in constraint_groups if isinstance(group, dict)}
    required_groups = {"Epic-level constraints", "Authoritative inherited constraints", "Downstream preservation rules"}
    has_governance_layers = required_groups.issubset(group_map)
    if required_groups.intersection(group_map) and not has_governance_layers:
        errors.append("epic-freeze.json governance constraint_groups must separate epic-level, inherited, and downstream-preservation rules.")
    epic_level_text = " ".join(group_map.get("Epic-level constraints", []))
    inherited_text = " ".join(group_map.get("Authoritative inherited constraints", []))
    source_markers = ("TestEnvironmentSpec", "TestCasePack", "ScriptPack", "skill.qa.test_exec_web_e2e", "skill.runner.test_e2e", "invalid_run", "acceptance_status")
    qa_source_detected = any(marker in " ".join(ensure_list(epic_json.get("constraints_and_dependencies"))) for marker in source_markers)
    if has_governance_layers and any(marker in epic_level_text for marker in source_markers):
        errors.append("epic-freeze.json Epic-level constraints must not repeat source object-level QA execution rules.")
    if has_governance_layers and qa_source_detected and not any(marker in inherited_text for marker in source_markers):
        errors.append("epic-freeze.json Authoritative inherited constraints must preserve source object-level rules where applicable.")
    decomposition_rules = ensure_list(epic_json.get("decomposition_rules"))
    if has_governance_layers and not any("产品行为切片" in rule for rule in decomposition_rules):
        errors.append("epic-freeze.json decomposition_rules must declare product behavior slices as the primary FEAT decomposition unit.")
    if has_governance_layers and not is_review_projection and not is_execution_runner and not any("cross-cutting constraints" in rule for rule in decomposition_rules):
        errors.append("epic-freeze.json decomposition_rules must declare capability axes as cross-cutting constraints rather than direct FEATs.")
    if has_governance_layers and not is_review_projection and not is_execution_runner and not any("mandatory overlays" in rule or "mandatory cross-cutting overlays" in rule or "mandatory overlays" in rule for rule in decomposition_rules):
        errors.append("epic-freeze.json decomposition_rules must declare rollout families as mandatory cross-cutting overlays.")
    product_behavior_slices = epic_json.get("product_behavior_slices")
    if not isinstance(product_behavior_slices, list) or not product_behavior_slices:
        errors.append("epic-freeze.json must include non-empty product_behavior_slices.")
    if not ensure_list(epic_json.get("business_value_problem")):
        errors.append("epic-freeze.json must include business_value_problem.")
    if not str(epic_json.get("product_positioning") or "").strip():
        errors.append("epic-freeze.json must include product_positioning.")
    actors = epic_json.get("actors_and_roles")
    if not isinstance(actors, list) or not actors:
        errors.append("epic-freeze.json must include actors_and_roles.")
    if not ensure_list(epic_json.get("upstream_and_downstream")):
        errors.append("epic-freeze.json must include upstream_and_downstream.")
    if not ensure_list(epic_json.get("epic_success_criteria")):
        errors.append("epic-freeze.json must include epic_success_criteria.")
    metrics_text = " ".join(ensure_list(epic_json.get("success_metrics")))
    metric_tokens = (
        (
            ("approve -> ready execution job -> runner claim -> next skill invocation", "runner auto-progression"),
            ("formal publication", "anti-formal-publication drift"),
        )
        if is_execution_runner
        else (
            ("producer -> consumer -> audit -> gate", "pilot chain"),
            ("formal publish", "materialization"),
            ("adoption / cutover / fallback", "rollout verification"),
        )
    )
    for token, label in metric_tokens:
        if has_governance_layers and not is_review_projection and token not in metrics_text:
            errors.append(f"epic-freeze.json success_metrics must include the {label} completion signal.")

    markdown_text = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")
    _, markdown_body = parse_markdown_frontmatter(markdown_text)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if f"## {heading}" not in markdown_body:
            errors.append(f"epic-freeze.md is missing section: {heading}")

    handoff = load_json(artifacts_dir / "handoff-to-epic-to-feat.json")
    if handoff.get("to_skill") != "product.epic-to-feat":
        errors.append("handoff-to-epic-to-feat.json to_skill must be product.epic-to-feat.")

    gate = load_json(artifacts_dir / "epic-freeze-gate.json")
    if gate.get("epic_freeze_ref") != epic_freeze_ref:
        errors.append("epic-freeze-gate.json must point to the same epic_freeze_ref.")

    result = {
        "valid": not errors,
        "epic_freeze_ref": epic_freeze_ref,
        "src_root_id": src_root_id,
        "source_refs": source_refs,
        "rollout_required": bool(rollout_requirement.get("required")),
        "semantic_lock_preserved": drift_check.get("semantic_lock_preserved"),
    }
    return errors, result


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors

    gate = load_json(artifacts_dir / "epic-freeze-gate.json")
    checks = gate.get("checks") or {}
    readiness_errors = [name for name, status in checks.items() if status is not True]
    return not readiness_errors, readiness_errors


def executor_run(input_path: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path)
    if errors:
        raise ValueError("; ".join(errors))
    package = load_src_package(input_path)
    effective_run_id = run_id or package.run_id
    generated = build_epic_payload(package, workflow_run_id=effective_run_id)
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")
    write_executor_outputs(
        output_dir=output_dir,
        repo_root=repo_root,
        package=package,
        generated=generated,
        command_name=f"python scripts/src_to_epic.py executor-run --input {input_path}",
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "epic_freeze_ref": generated.frontmatter["epic_freeze_ref"],
        "src_root_id": generated.frontmatter["src_root_id"],
    }


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    package_manifest = load_json(artifacts_dir / "package-manifest.json")
    epic_json = load_json(artifacts_dir / "epic-freeze.json")
    input_run_id = run_id or str(epic_json.get("workflow_run_id") or package_manifest.get("status") or artifacts_dir.name)

    source_run_ref = next((ref for ref in ensure_list(epic_json.get("source_refs")) if ref.startswith("product.raw-to-src::")), "")
    package_run_id = source_run_ref.split("::", 1)[1] if "::" in source_run_ref else input_run_id
    source_package_dir = guess_repo_root_from_input(artifacts_dir) / "artifacts" / "raw-to-src" / package_run_id
    package = load_src_package(source_package_dir)
    generated = build_epic_payload(package, workflow_run_id=input_run_id)

    supervision = build_supervision_evidence(package, artifacts_dir, generated)
    gate = build_gate_result(generated, supervision)

    update_supervisor_outputs(artifacts_dir, repo_root, package, generated, supervision, gate)

    return {
        "ok": True,
        "run_id": input_run_id,
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
        "src_root_id": executor_result["src_root_id"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }
