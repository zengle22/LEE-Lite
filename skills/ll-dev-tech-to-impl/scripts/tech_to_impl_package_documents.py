#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def _build_text_sections(
    feature: dict[str, Any],
    refs: dict[str, str | None],
    assessment: dict[str, Any],
    steps: list[dict[str, str]],
    risks: list[str],
    deliverables: list[str],
    checkpoints: list[dict[str, str]],
    integration_items: list[str],
    evidence_plan_rows: list[dict[str, Any]],
    handoff: dict[str, Any],
    source_refs: list[str],
    bundle_json: dict[str, Any],
    scope: list[str],
    contract_projection: dict[str, Any],
) -> dict[str, Any]:
    selected_upstream_refs = contract_projection["selected_upstream_refs"]
    provisional_refs = contract_projection["provisional_refs"]
    normative_items = contract_projection["normative_items"]
    informative_items = contract_projection["informative_items"]
    required_steps = contract_projection["required_steps"]
    suggested_steps = contract_projection["suggested_steps"]
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
            "## Package Semantics\n\n"
            + "\n".join(
                [
                    "- IMPL is the canonical execution package / execution-time single entrypoint for this run.",
                    "- IMPL is not the business, design, or test truth source.",
                    f"- freshness_status: `{bundle_json['freshness_status']}`",
                    f"- provisional_refs: {len(provisional_refs)}",
                    f"- repo_discrepancy_status: `{bundle_json['repo_discrepancy_status']['status']}`",
                    "- self-contained policy: minimum sufficient information, not upstream mirroring.",
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
            "## Implementation Task\n\n" + "\n".join([f"- {index}. {step['title']}: {step['done_when']}" for index, step in enumerate(steps, start=1)]),
            "## Integration Plan\n\n" + "\n".join(f"- {item}" for item in integration_items),
            "## Evidence Plan\n\n" + "\n".join(f"- {row['acceptance_ref']}: {', '.join(row['evidence_types'])}" for row in evidence_plan_rows),
            "## Smoke Gate Subject\n\n- See `smoke-gate-subject.json` for the current `status`, `decision`, and `ready_for_execution` state.",
            "## Delivery Handoff\n\n"
            + "\n".join(
                [
                    f"- target_template_id: `template.dev.feature_delivery_l2`",
                    f"- primary_artifact_ref: `{handoff['primary_artifact_ref']}`",
                    f"- phase_inputs: {', '.join([name for name, items in (handoff.get('phase_inputs') or {}).items() if items])}",
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
                    f"- ADR refs: {', '.join(selected_upstream_refs['adr_refs']) or 'not present'}",
                    f"- SRC: `{selected_upstream_refs['src_ref'] or 'not present'}`",
                    f"- EPIC: `{selected_upstream_refs['epic_ref'] or 'not present'}`",
                    f"- FEAT: `{refs['feat_ref']}`",
                    f"- TECH: `{refs['tech_ref']}`",
                    f"- ARCH: `{refs['arch_ref']}`" if refs["arch_ref"] else "- ARCH: not present",
                    f"- API: `{refs['api_ref']}`" if refs["api_ref"] else "- API: not present",
                    f"- UI: `{selected_upstream_refs['ui_ref']}`" if selected_upstream_refs["ui_ref"] else "- UI: not present",
                    f"- TESTSET: `{selected_upstream_refs['testset_ref']}`" if selected_upstream_refs["testset_ref"] else "- TESTSET: not present",
                    f"- provisional_refs: {', '.join(item['ref'] for item in provisional_refs) if provisional_refs else 'none'}",
                    "- 继承规则: 上游冻结决策只能被实现和验证，不能在 IMPL 中被改写。",
                    "- discrepancy handling: 若 repo 现状与上游冻结对象冲突，不得默认以代码现状为准。",
                ]
            ),
            "## 3. 实施范围\n\n" + "\n".join(f"- {item}" for item in scope),
            "## 4. 实施步骤\n\n"
            + "### Required\n\n"
            + "\n".join(
                f"- {index}. {step['title']}: {step['done_when']}" for index, step in enumerate(required_steps, start=1)
            )
            + "\n\n### Suggested\n\n"
            + ("\n".join(f"- {step['title']}: {step['reason']}" for step in suggested_steps) if suggested_steps else "- None."),
            "## 5. 风险与阻塞\n\n" + "\n".join(f"- {item}" for item in risks),
            "## 6. 交付物\n\n"
            + "\n".join(f"- {item}" for item in deliverables)
            + "\n\n### Normative / MUST\n\n"
            + "\n".join(f"- {item}" for item in normative_items)
            + "\n\n### Informative / Context Only\n\n"
            + ("\n".join(f"- {item}" for item in informative_items) if informative_items else "- None."),
            "## 7. 验收检查点\n\n" + "\n".join(f"- {item['ref']}: {item['scenario']} -> {item['expectation']}" for item in checkpoints),
        ]
    )
    return {"bundle_body": bundle_body, "impl_task_body": impl_task_body}
