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
    scope_boundary = contract_projection["scope_boundary"]
    upstream_impacts = contract_projection["upstream_impacts"]
    normative_items = contract_projection["normative_items"]
    informative_items = contract_projection["informative_items"]
    change_controls = contract_projection["change_controls"]
    required_steps = contract_projection["required_steps"]
    suggested_steps = contract_projection["suggested_steps"]
    testset_mapping = contract_projection["testset_mapping"]
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
            "## 1. 任务标识\n\n"
            + "\n".join(
                [
                    f"- impl_ref: `{refs['impl_ref']}`",
                    f"- title: {bundle_json['title']}",
                    f"- workflow_key: `{bundle_json['workflow_key']}`",
                    f"- workflow_run_id: `{bundle_json['workflow_run_id']}`",
                    f"- status: `{bundle_json['status']}`",
                    f"- derived_from: `{refs['feat_ref']}`, `{refs['tech_ref']}`",
                    "- package role: canonical execution package / execution-time single entrypoint",
                ]
            ),
            "## 2. 本次目标\n\n"
            + "\n".join(
                [
                    f"- 覆盖目标: {feature.get('goal')}",
                    f"- 完成标准: {len(required_steps)} 个 required steps、{len(testset_mapping['mappings'])} 条 acceptance mappings 与 handoff artifacts 全部齐备。",
                    "- 完成条件: coder/tester 可直接消费本契约，不必运行期沿链补捞关键约束。",
                ]
            ),
            "## 3. 范围与非目标\n\n"
            + "### In Scope\n\n"
            + "\n".join(f"- {item}" for item in scope_boundary["in_scope"])
            + "\n\n### Out of Scope\n\n"
            + "\n".join(f"- {item}" for item in scope_boundary["out_of_scope"]),
            "## 4. 上游收敛结果\n\n"
            + "\n".join(
                [
                    f"- ADR refs: {', '.join(upstream_impacts['adr']['refs']) or 'not present'} -> {upstream_impacts['adr']['impact']}",
                    f"- SRC / EPIC / FEAT: `{upstream_impacts['src_epic_feat']['src_ref'] or 'not present'}` / `{upstream_impacts['src_epic_feat']['epic_ref'] or 'not present'}` / `{upstream_impacts['src_epic_feat']['feat_ref']}` -> {upstream_impacts['src_epic_feat']['impact']}",
                    f"- TECH: `{upstream_impacts['tech']['ref']}` -> {'; '.join(upstream_impacts['tech']['impact_items'])}",
                    f"- ARCH: `{upstream_impacts['arch']['ref'] or 'not present'}` -> {upstream_impacts['arch']['impact']}",
                    f"- API: `{upstream_impacts['api']['ref'] or 'not present'}` -> {('; '.join(upstream_impacts['api']['impact_items']) + '; ') if upstream_impacts['api']['impact_items'] else ''}{upstream_impacts['api']['impact']}",
                    f"- UI: `{upstream_impacts['ui']['ref'] or 'not present'}` -> {upstream_impacts['ui']['impact']}",
                    f"- TESTSET: `{upstream_impacts['testset']['ref'] or 'not present'}` -> {upstream_impacts['testset']['impact']}",
                    f"- provisional_refs: {', '.join(item['ref'] for item in provisional_refs) if provisional_refs else 'none'}",
                ]
            ),
            "## 5. 规范性约束\n\n"
            + "### Normative / MUST\n\n"
            + "\n".join(f"- {item}" for item in normative_items)
            + "\n\n### Informative / Context Only\n\n"
            + ("\n".join(f"- {item}" for item in informative_items) if informative_items else "- None."),
            "## 6. 实施要求\n\n"
            + "### Touch Set / Module Plan\n\n"
            + "\n".join(f"- {item}" for item in change_controls["touch_set"])
            + "\n\n### Allowed\n\n"
            + "\n".join(f"- {item}" for item in change_controls["allowed_changes"])
            + "\n\n### Forbidden\n\n"
            + "\n".join(f"- {item}" for item in change_controls["forbidden_changes"])
            + "\n\n### Execution Boundary\n\n"
            + "\n".join(
                [
                    "- 继承规则: 上游冻结决策只能被实现和验证，不能在 IMPL 中被改写。",
                    "- discrepancy handling: 若 repo 现状与上游冻结对象冲突，不得默认以代码现状为准。",
                ]
            ),
            "## 7. 交付物要求\n\n"
            + "\n".join(f"- {item}" for item in deliverables)
            + "\n\n### Handoff Artifacts\n\n"
            + "\n".join(f"- {item}" for item in contract_projection["handoff_artifacts"]),
            "## 8. 验收标准与 TESTSET 映射\n\n"
            + f"- testset_ref: `{testset_mapping['testset_ref'] or 'not present'}`\n"
            + f"- mapping_policy: `{testset_mapping['mapping_policy']}`\n"
            + "### Acceptance Trace\n\n"
            + "\n".join(
                f"- {item['acceptance_ref']}: {item['scenario']} -> {item['expectation']} | mapped_to: `{item['mapped_to']}`"
                for item in testset_mapping["mappings"]
            ),
            "## 9. 执行顺序建议\n\n"
            + "### Required\n\n"
            + "\n".join(
                f"- {index}. {step['title']}: {step['done_when']}" for index, step in enumerate(required_steps, start=1)
            )
            + "\n\n### Suggested\n\n"
            + ("\n".join(f"- {step['title']}: {step['reason']}" for step in suggested_steps) if suggested_steps else "- None."),
            "## 10. 风险与注意事项\n\n"
            + "\n".join(f"- {item}" for item in risks)
            + "\n"
            + (
                "\n" + "\n".join(f"- provisional note: `{item['ref']}` impacts {item['impact_scope']} and requires {item['follow_up_action']}." for item in provisional_refs)
                if provisional_refs
                else ""
            ),
        ]
    )
    return {"bundle_body": bundle_body, "impl_task_body": impl_task_body}
