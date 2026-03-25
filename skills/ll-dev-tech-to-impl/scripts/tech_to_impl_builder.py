#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tech_to_impl_common import ensure_list, unique_strings
from tech_to_impl_derivation import (
    acceptance_checkpoints,
    assess_workstreams,
    backend_workstream_items,
    build_refs,
    consistency_check,
    deliverable_files,
    evidence_rows,
    filtered_implementation_rules,
    frontend_workstream_items,
    implementation_units,
    implementation_scope,
    implementation_steps,
    integration_plan_items,
    migration_plan_items,
    risk_items,
    tech_list,
    workstream_required_inputs,
)


DOWNSTREAM_TEMPLATE_ID = "template.dev.feature_delivery_l2"
DOWNSTREAM_TEMPLATE_PATH = "E:\\ai\\LEE\\spec-global\\departments\\dev\\workflows\\templates\\feature-delivery-l2-template.yaml"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _md_frontmatter(artifact_type: str, refs: dict[str, str | None], source_refs: list[str]) -> dict[str, Any]:
    payload = {
        "artifact_type": artifact_type,
        "status": "draft",
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "source_refs": source_refs,
    }
    if refs.get("arch_ref"):
        payload["arch_ref"] = refs["arch_ref"]
    if refs.get("api_ref"):
        payload["api_ref"] = refs["api_ref"]
    return payload


def _non_empty_phase_input_names(handoff: dict[str, Any]) -> list[str]:
    phase_inputs = handoff.get("phase_inputs") or {}
    if not isinstance(phase_inputs, dict):
        return []
    return [name for name, items in phase_inputs.items() if ensure_list(items)]


def build_candidate_package(package: Any, run_id: str) -> dict[str, Any]:
    feature = package.selected_feat
    refs = build_refs(package)
    assessment = assess_workstreams(feature, package)
    consistency = consistency_check(assessment)
    checkpoints = acceptance_checkpoints(feature)
    scope = implementation_scope(feature, package)
    steps = implementation_steps(feature, assessment, package)
    risks = risk_items(feature, assessment, package)
    deliverables = deliverable_files(assessment)
    smoke_required_inputs = workstream_required_inputs(assessment)
    integration_items = integration_plan_items(feature, assessment, package)
    evidence_plan_rows = evidence_rows(feature, assessment)
    frontend_items = frontend_workstream_items(feature)
    backend_items = backend_workstream_items(feature, package)
    migration_items = migration_plan_items(feature, package)
    implementation_units_payload = implementation_units(package)

    source_refs = unique_strings(
        [f"dev.feat-to-tech::{package.run_id}", refs["feat_ref"], refs["tech_ref"]]
        + ensure_list(package.tech_json.get("source_refs"))
    )

    upstream_design_refs = {
        "artifact_type": "UPSTREAM_DESIGN_REFS",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "upstream_workflow_key": str(package.tech_json.get("workflow_key") or ""),
        "upstream_run_id": package.run_id,
        "primary_artifacts": {
            "tech_design_bundle": "tech-design-bundle.json",
            "tech_spec": "tech-spec.md",
            "tech_impl": "tech-impl.md",
            "arch_design": "arch-design.md" if refs["arch_ref"] else None,
            "api_contract": "api-contract.md" if refs["api_ref"] else None,
        },
        "frozen_source_refs": source_refs,
        "frozen_decisions": {
            "design_focus": ensure_list((package.tech_json.get("tech_design") or {}).get("design_focus")),
            "implementation_rules": filtered_implementation_rules(package),
            "state_model": tech_list(package, "state_model"),
            "main_sequence": tech_list(package, "main_sequence"),
            "integration_points": tech_list(package, "integration_points"),
            "implementation_unit_mapping": [
                f"{unit['path']} ({unit['mode']}): {unit['detail']}" for unit in implementation_units_payload
            ],
            "interface_contracts": tech_list(package, "interface_contracts"),
            "consistency_passed": bool((package.tech_json.get("design_consistency_check") or {}).get("passed")),
        },
    }

    handoff = {
        "handoff_id": f"handoff-{run_id}-to-feature-delivery",
        "from_skill": "ll-dev-tech-to-impl",
        "source_run_id": run_id,
        "target_template_id": DOWNSTREAM_TEMPLATE_ID,
        "target_template_path": DOWNSTREAM_TEMPLATE_PATH,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "primary_artifact_ref": "impl-bundle.json",
        "phase_inputs": {
            "implementation_task": ["impl-task.md"],
            "frontend": ["frontend-workstream.md"] if assessment["frontend_required"] else [],
            "backend": ["backend-workstream.md"] if assessment["backend_required"] else [],
            "migration": ["migration-cutover-plan.md"] if assessment["migration_required"] else [],
            "integration": ["integration-plan.md"],
            "evidence": ["dev-evidence-plan.json", "smoke-gate-subject.json"],
            "upstream_design": ["upstream-design-refs.json"],
        },
        "deliverables": deliverables,
        "acceptance_refs": [item["ref"] for item in checkpoints],
        "supporting_artifact_refs": deliverables,
        "created_at": utc_now(),
    }

    defects: list[dict[str, Any]] = []
    if not consistency["passed"]:
        defects.append(
            {
                "severity": "P1",
                "title": "No implementation surface selected",
                "detail": "; ".join(consistency["issues"]),
            }
        )

    bundle_json = {
        "artifact_type": "feature_impl_candidate_package",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "title": f"{feature.get('title') or refs['feat_ref']} Implementation Task Package",
        "status": "in_progress",
        "package_role": "candidate",
        "schema_version": "1.0.0",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "source_refs": source_refs,
        "selected_scope": {
            "title": feature.get("title"),
            "goal": feature.get("goal"),
            "scope": ensure_list(feature.get("scope")),
            "constraints": ensure_list(feature.get("constraints")),
            "dependencies": ensure_list(feature.get("dependencies")),
        },
        "workstream_assessment": assessment,
        "status_model": {
            "package": "in_progress",
            "smoke_gate": "pending_review",
        },
        "artifact_refs": {
            "bundle_markdown": "impl-bundle.md",
            "bundle_json": "impl-bundle.json",
            "impl_task": "impl-task.md",
            "upstream_design_refs": "upstream-design-refs.json",
            "frontend_workstream": "frontend-workstream.md" if assessment["frontend_required"] else None,
            "backend_workstream": "backend-workstream.md" if assessment["backend_required"] else None,
            "migration_cutover_plan": "migration-cutover-plan.md" if assessment["migration_required"] else None,
            "integration_plan": "integration-plan.md",
            "dev_evidence_plan": "dev-evidence-plan.json",
            "smoke_gate_subject": "smoke-gate-subject.json",
            "review_report": "impl-review-report.json",
            "acceptance_report": "impl-acceptance-report.json",
            "defect_list": "impl-defect-list.json",
            "handoff": "handoff-to-feature-delivery.json",
        },
        "upstream_design_refs": upstream_design_refs,
        "consistency_check": consistency,
        "downstream_handoff": handoff,
    }

    bundle_frontmatter = {
        "artifact_type": bundle_json["artifact_type"],
        "workflow_key": bundle_json["workflow_key"],
        "workflow_run_id": bundle_json["workflow_run_id"],
        "status": bundle_json["status"],
        "package_role": bundle_json["package_role"],
        "schema_version": bundle_json["schema_version"],
        "feat_ref": bundle_json["feat_ref"],
        "impl_ref": bundle_json["impl_ref"],
        "tech_ref": bundle_json["tech_ref"],
        "source_refs": bundle_json["source_refs"],
    }

    bundle_body = "\n\n".join(
        [
            f"# {bundle_json['title']}",
            "## Selected Upstream\n\n"
            + "\n".join(
                [
                    f"- feat_ref: `{refs['feat_ref']}`",
                    f"- tech_ref: `{refs['tech_ref']}`",
                    f"- arch_ref: `{refs['arch_ref']}`" if refs["arch_ref"] else "- arch_ref: not present",
                    f"- api_ref: `{refs['api_ref']}`" if refs["api_ref"] else "- api_ref: not present",
                    f"- title: {feature.get('title')}",
                    f"- goal: {feature.get('goal')}",
                ]
            ),
            "## Applicability Assessment\n\n"
            + "\n".join(
                [
                    f"- frontend_required: {assessment['frontend_required']}",
                    *[f"  - {item}" for item in assessment["rationale"]["frontend"]],
                    f"- backend_required: {assessment['backend_required']}",
                    *[f"  - {item}" for item in assessment["rationale"]["backend"]],
                    f"- migration_required: {assessment['migration_required']}",
                    *[f"  - {item}" for item in assessment["rationale"]["migration"]],
                ]
            ),
            "## Implementation Task\n\n"
            + "\n".join([f"- {index}. {step['title']}: {step['done_when']}" for index, step in enumerate(steps, start=1)]),
            "## Integration Plan\n\n" + "\n".join(f"- {item}" for item in integration_items),
            "## Evidence Plan\n\n" + "\n".join(f"- {row['acceptance_ref']}: {', '.join(row['evidence_types'])}" for row in evidence_plan_rows),
            "## Smoke Gate Subject\n\n- See `smoke-gate-subject.json` for the current `status`, `decision`, and `ready_for_execution` state.",
            "## Delivery Handoff\n\n"
            + "\n".join(
                [
                    f"- target_template_id: `{DOWNSTREAM_TEMPLATE_ID}`",
                    f"- primary_artifact_ref: `{handoff['primary_artifact_ref']}`",
                    f"- phase_inputs: {', '.join(_non_empty_phase_input_names(handoff))}",
                ]
            ),
            "## Traceability\n\n" + "\n".join(f"- {item}" for item in source_refs),
        ]
    )

    impl_task_body = "\n\n".join(
        [
            f"# {refs['impl_ref']}",
            "## 1. 目标\n\n"
            + "\n".join(
                [
                    f"- 覆盖目标: {feature.get('goal')}",
                    "- 不覆盖内容: 不在 IMPL 中重写上游 TECH/ARCH/API 决策，只组织实施、接线、迁移与验收。",
                ]
            ),
            "## 2. 上游依赖\n\n"
            + "\n".join(
                [
                    f"- FEAT: `{refs['feat_ref']}`",
                    f"- TECH: `{refs['tech_ref']}`",
                    f"- ARCH: `{refs['arch_ref']}`" if refs["arch_ref"] else "- ARCH: not present",
                    f"- API: `{refs['api_ref']}`" if refs["api_ref"] else "- API: not present",
                    "- 继承规则: 上游冻结决策只能被实现和验证，不能在 IMPL 中被改写。",
                ]
            ),
            "## 3. 实施范围\n\n" + "\n".join(f"- {item}" for item in scope),
            "## 4. 实施步骤\n\n"
            + "\n".join(
                [
                    f"### Step {index}: {step['title']}\n- 工作内容: {step['work']}\n- 完成条件: {step['done_when']}"
                    for index, step in enumerate(steps, start=1)
                ]
            ),
            "## 5. 风险与阻塞\n\n" + "\n".join(f"- {item}" for item in risks),
            "## 6. 交付物\n\n" + "\n".join(f"- {item}" for item in deliverables),
            "## 7. 验收检查点\n\n"
            + "\n".join(f"- {item['ref']}: {item['scenario']} -> {item['expectation']}" for item in checkpoints),
        ]
    )

    integration_body = "\n\n".join(
        [
            f"# INTEGRATION-{refs['impl_ref']}",
            "## Integration Sequence\n\n" + "\n".join(f"- {item}" for item in integration_items),
            "## Blocking Conditions\n\n"
            + "\n".join(
                [
                    "- Upstream refs must remain resolvable.",
                    "- Optional workstreams can only enter execution if their applicability assessment is true.",
                    "- Smoke review is blocked until evidence plan artifacts are available.",
                ]
            ),
        ]
    )

    frontend_body = None
    if assessment["frontend_required"]:
        frontend_body = "\n\n".join(
            [
                f"# FRONTEND-{refs['impl_ref']}",
                "## Frontend Surface\n\n" + "\n".join(f"- {item}" for item in frontend_items),
                "## Done Criteria\n\n- Frontend implementation stays inside the selected IMPL boundary and traceability chain.",
            ]
        )

    backend_body = None
    if assessment["backend_required"]:
        backend_body = "\n\n".join(
            [
                f"# BACKEND-{refs['impl_ref']}",
                "## Backend Surface\n\n" + "\n".join(f"- {item}" for item in backend_items),
                "## Done Criteria\n\n- Backend changes satisfy frozen TECH/ARCH/API decisions without introducing new design truth.",
            ]
        )

    migration_body = None
    if assessment["migration_required"]:
        migration_body = "\n\n".join(
            [
                f"# MIGRATION-{refs['impl_ref']}",
                "## Migration and Cutover\n\n" + "\n".join(f"- {item}" for item in migration_items),
                "## Done Criteria\n\n- Rollout and rollback expectations are explicit enough for downstream execution.",
            ]
        )

    smoke_gate_subject = {
        "artifact_type": "SMOKE_GATE_SUBJECT",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "gate_ref": f"SMOKE-GATE-{refs['impl_ref']}",
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "tech_ref": refs["tech_ref"],
        "status": "pending_review",
        "decision": "pending",
        "ready_for_execution": False,
        "required_inputs": ["impl-task.md", "integration-plan.md", "dev-evidence-plan.json"],
        "required_workstreams": smoke_required_inputs,
        "required_inputs": smoke_required_inputs,
        "acceptance_refs": [item["ref"] for item in checkpoints],
        "created_at": utc_now(),
    }

    evidence_plan = {
        "artifact_type": "DEV_EVIDENCE_PLAN",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "rows": evidence_plan_rows,
        "status": "draft",
    }

    review_report = {
        "report_id": f"impl-review-{run_id}",
        "report_type": "feature_impl_review",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "status": "pending",
        "decision": "pending",
        "summary": "Pending supervisor review.",
        "findings": [],
        "created_at": utc_now(),
    }

    acceptance_report = {
        "report_id": f"impl-acceptance-{run_id}",
        "report_type": "feature_impl_acceptance",
        "workflow_key": "dev.tech-to-impl",
        "workflow_run_id": run_id,
        "feat_ref": refs["feat_ref"],
        "impl_ref": refs["impl_ref"],
        "status": "pending",
        "decision": "pending",
        "summary": "Pending supervisor review.",
        "acceptance_findings": [],
        "created_at": utc_now(),
    }

    return {
        "refs": refs,
        "assessment": assessment,
        "consistency": consistency,
        "bundle_frontmatter": bundle_frontmatter,
        "bundle_body": bundle_body,
        "bundle_json": bundle_json,
        "impl_task_frontmatter": _md_frontmatter("IMPL_TASK", refs, source_refs),
        "impl_task_body": impl_task_body,
        "upstream_design_refs": upstream_design_refs,
        "integration_frontmatter": _md_frontmatter("INTEGRATION_PLAN", refs, source_refs),
        "integration_body": integration_body,
        "frontend_frontmatter": _md_frontmatter("FRONTEND_WORKSTREAM", refs, source_refs) if frontend_body else None,
        "frontend_body": frontend_body,
        "backend_frontmatter": _md_frontmatter("BACKEND_WORKSTREAM", refs, source_refs) if backend_body else None,
        "backend_body": backend_body,
        "migration_frontmatter": _md_frontmatter("MIGRATION_CUTOVER_PLAN", refs, source_refs) if migration_body else None,
        "migration_body": migration_body,
        "evidence_plan": evidence_plan,
        "smoke_gate_subject": smoke_gate_subject,
        "review_report": review_report,
        "acceptance_report": acceptance_report,
        "defect_list": defects,
        "handoff": handoff,
        "execution_decisions": [
            f"Selected TECH package {refs['tech_ref']} from upstream run {package.run_id}.",
            f"frontend_required={assessment['frontend_required']}, backend_required={assessment['backend_required']}, migration_required={assessment['migration_required']}.",
            f"Prepared downstream handoff to {DOWNSTREAM_TEMPLATE_ID}.",
        ],
        "execution_uncertainties": consistency["issues"][:],
    }

