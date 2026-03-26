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
) -> dict[str, Any]:
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
            "## 7. 验收检查点\n\n" + "\n".join(f"- {item['ref']}: {item['scenario']} -> {item['expectation']}" for item in checkpoints),
        ]
    )
    return {"bundle_body": bundle_body, "impl_task_body": impl_task_body}
