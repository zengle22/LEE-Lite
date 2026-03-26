#!/usr/bin/env python3
"""Unit derivation helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_collaboration import collaboration_units as collaboration_units_impl
from feat_to_testset_common import derive_test_set_id, ensure_list, unique_strings


def unit_payload(
    feat_ref: str,
    index: int,
    acceptance_ref: str | None,
    title: str,
    priority: str,
    layers: list[str],
    input_preconditions: list[str],
    trigger_action: str,
    observation_points: list[str],
    pass_conditions: list[str],
    fail_conditions: list[str],
    required_evidence: list[str],
    supporting_refs: list[str],
    derivation_basis: list[str] | None = None,
) -> dict[str, Any]:
    test_set_id = derive_test_set_id(feat_ref)
    payload = {
        "unit_ref": f"{test_set_id}-U{index:02d}",
        "title": title,
        "priority": priority,
        "input_preconditions": unique_strings(input_preconditions),
        "trigger_action": trigger_action,
        "observation_points": unique_strings(observation_points),
        "pass_conditions": unique_strings(pass_conditions),
        "fail_conditions": unique_strings(fail_conditions),
        "required_evidence": unique_strings(required_evidence),
        "suggested_layers": layers,
        "supporting_refs": unique_strings(supporting_refs),
    }
    if acceptance_ref:
        payload["acceptance_ref"] = acceptance_ref
    if derivation_basis:
        payload["derivation_basis"] = unique_strings(derivation_basis)
    return payload


def default_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    units: list[dict[str, Any]] = []
    for index, check in enumerate(feature.get("acceptance_checks") or [], start=1):
        acceptance_ref = str(check.get("id") or f"{feat_ref}-AC-{index:02d}")
        units.append(
            unit_payload(
                feat_ref=feat_ref,
                index=index,
                acceptance_ref=acceptance_ref,
                title=str(check.get("scenario") or f"Acceptance check {index}"),
                priority=priority,
                layers=layers,
                input_preconditions=[
                    str(check.get("given") or "上游 FEAT 前置条件满足。"),
                    *ensure_list(feature.get("dependencies"))[:2],
                ],
                trigger_action=str(check.get("when") or "执行该 acceptance 对应的产品行为。"),
                observation_points=[
                    str(check.get("then") or ""),
                    "记录与主对象、handoff、gate subject 对应的可观察结果。",
                ],
                pass_conditions=[
                    str(check.get("then") or "Acceptance 结果成立。"),
                    "输出与 selected FEAT 保持单一边界，不引入并行真相。",
                ],
                fail_conditions=[
                    "缺少 acceptance 对应 evidence。",
                    "观测结果与 FEAT acceptance 或主对象边界不一致。",
                ],
                required_evidence=[
                    f"{acceptance_ref} 对应的执行结果证据",
                    "失败时的最小可审计上下文",
                ],
                supporting_refs=refs + ensure_list(check.get("trace_hints")),
            )
        )
    return units


def collaboration_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    return collaboration_units_impl(feature, layers, priority, refs)


def gate_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "authoritative handoff 进入单一路径的 gate 决策链", priority, layers, [str(checks[0]["given"]), "candidate package 已形成 authoritative handoff submission。"], "提交 handoff 并触发 gate evaluate。", ["只生成一个 authoritative decision object。", "decision path 不出现平行 shortcut。"], ["handoff -> decision 链唯一且可追溯。", "decision object 可被 formal publish 流消费。"], ["出现并行 decision path。", "缺少 authoritative decision object。"], ["gate decision response", "decision object evidence", "handoff submission trace"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[0]["id"]), "decision object 对 approve / revise / retry / handoff / reject 保持唯一业务语义", priority, layers, ["gate evaluator 能访问候选交接与审核上下文。"], "对同一候选输入分别验证 decision 结果分支。", ["不同 decision_type 的返回去向。", "回流或终止目标是否稳定。"], ["每个 decision_type 都映射到唯一业务去向。", "formal 发布触发不与 revise/retry/reject 混层。"], ["decision_type 语义不唯一。", "返回去向与主链职责混乱。"], ["decision branch evidence", "review summary", "routing trace"], refs),
        unit_payload(feat_ref, 3, str(checks[1]["id"]), "candidate 在 gate 前不得被当作 downstream formal source", priority, layers, [str(checks[1]["given"]), "candidate package 与 formal publication package 保持分层。"], str(checks[1]["when"]), ["下游消费路径", "candidate / formal package 边界。"], ["candidate 只能作为 gate 输入，不得成为 downstream formal source。", "formal object 仍需由 formal publish flow 生成。"], ["candidate 被 downstream 直接当作 formal source。", "object layering 被绕过。"], ["layer boundary evidence", "consumer rejection evidence"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 4, str(checks[2]["id"]), "decision object 缺失、冲突或 bypass 时必须 fail closed", priority, layers, [str(checks[2]["given"]), "存在 decision 缺失、冲突或旁路风险。"], str(checks[2]["when"]), ["decision path verdict", "fallback / reject result", "旁路检测。"], ["decision 缺失、冲突或 bypass 时必须 fail closed。", "不会静默 materialize 或 dispatch。"], ["decision 缺失仍推进 formal 或 dispatch。", "旁路行为未留下 verdict。"], ["fail-closed evidence", "decision conflict evidence", "bypass detection trace"], refs + ensure_list(checks[2].get("trace_hints")) + ["decision uniqueness", "fail closed"]),
    ]


def formal_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "formal publication 产出单一 canonical formal ref", priority, layers, [str(checks[0]["given"]), "approved decision object 已形成并允许 formalize。"], str(checks[0]["when"]), ["formal ref", "formal package", "lineage record。"], ["formal publication 只产出一条 canonical formal ref。", "lineage 可回链到 gate decision 与 candidate 来源。"], ["同一正式对象出现多条 formal ref。", "formal ref 缺少 lineage。"], ["formal publication evidence", "formal ref snapshot", "lineage record"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "downstream admission 只接受满足 lineage / layer 要求的 formal object", priority, layers, [str(checks[1]["given"]), "consumer admission 依赖 formal ref 与 lineage。"], str(checks[1]["when"]), ["admission verdict", "lineage verification result。"], ["只有满足 lineage / layer 约束的 formal object 能通过 admission。", "缺少 formal ref 或 lineage 时 fail closed。"], ["layer violation 仍被 admission。", "lineage 缺失未触发 fail closed。"], ["admission verdict", "lineage verification evidence"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "candidate / intermediate artifact 不得被误当作 formal object", priority, layers, [str(checks[2]["given"]), "candidate、test output 或 freeze intermediate 仍可见。"], str(checks[2]["when"]), ["consumer input classification", "rejected non-formal object。"], ["非 formal object 不得通过 admission。", "对象分层边界保持单一 authoritative path。"], ["candidate 或中间物被当作 formal object 消费。", "层级边界被重写。"], ["classification evidence", "admission rejection evidence"], refs + ensure_list(checks[2].get("trace_hints"))),
        unit_payload(feat_ref, 4, None, "formal publication 失败时不得泄漏半正式对象", priority, layers, ["formalize 过程可能中断或前置条件不满足。"], "触发 formal publication 失败场景，并检查输出边界。", ["partial publication artifact", "registry state", "consumer visibility。"], ["formal publication 失败时不得留下可消费的半正式对象。", "consumer 只能看到明确失败 verdict。"], ["失败后仍暴露半正式对象。", "registry state 与 visibility 不一致。"], ["failed publication evidence", "registry state snapshot", "consumer visibility trace"], refs, derivation_basis=["no partial formal objects", "fail-closed formal publication"]),
    ]


def io_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "commit-governed / read-governed 只允许经 gateway 的 managed 路径", priority, layers, [str(checks[0]["given"]), "gateway / path policy / registry 已启用。"], str(checks[0]["when"]), ["gateway verdict", "receipt_ref / registry_record_ref / managed_artifact_ref。"], ["所有写读都经 gateway 并返回 managed refs。", "不出现自由写入或自由读取旁路。"], ["绕过 gateway 仍成功写读。", "managed refs 缺失。"], ["gateway verdict evidence", "receipt evidence", "registry record evidence"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "path policy 边界只覆盖 mainline governed IO，不扩张为仓库级总方案", priority, layers, [str(checks[1]["given"]), "scope boundary 已声明为 mainline governed IO。"], str(checks[1]["when"]), ["policy verdict scope", "被拒绝操作的边界说明。"], ["仅 mainline governed IO 被纳入受测边界。", "全局文件治理扩展请求被拒绝。"], ["测试边界覆盖仓库级全局治理。", "scope expansion 未被识别。"], ["boundary denial evidence", "policy scope note"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 3, str(checks[2]["id"]), "policy_deny 时不得 silent fallback 到自由写入", priority, layers, [str(checks[2]["given"]), "preflight 结果为 policy_deny。"], str(checks[2]["when"]), ["write result status", "是否存在自由写入旁路。"], ["policy_deny 返回可追溯 denied 结果。", "不存在 free write fallback。"], ["policy_deny 后仍发生自由写入。", "没有返回可审计 verdict。"], ["policy_deny evidence", "blocked fallback trace"], refs + ensure_list(checks[2].get("trace_hints")) + ["policy_deny"]),
        unit_payload(feat_ref, 4, str(checks[2]["id"]), "registry_prerequisite_failed 与 receipt_pending 都必须留下可追溯结果", priority, layers, ["registry bind 前置条件或 receipt build 可能失败。"], "分别触发 registry_prerequisite_failed 与 receipt_pending 场景。", ["partial success 标记", "失败结果 evidence", "重试/补偿上下文。"], ["registry_prerequisite_failed 与 receipt_pending 都可被追溯。", "主链不会因部分成功而静默丢失 managed refs 上下文。"], ["失败状态无 evidence。", "partial success 没有明确标记。"], ["registry_prerequisite_failed evidence", "receipt_pending evidence", "compensation trace"], refs + ["registry_prerequisite_failed", "receipt_pending"]),
    ]


def pilot_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    return [
        unit_payload(feat_ref, 1, str(checks[0]["id"]), "onboarding matrix 固化 skill、wave_id、compat_mode 与 cutover_guard_ref", priority, layers, [str(checks[0]["given"]), "rollout onboarding contract 可写回 wave state。"], "生成 onboarding matrix，并把 wave_id、compat_mode、cutover_guard_ref 写回 rollout state。", ["integration matrix", "wave_id", "compat_mode", "cutover_guard_ref。"], ["onboarding scope 与 migration waves 可追溯。", "cutover / fallback 规则以 machine-readable 形式存在。"], ["wave / compat_mode / cutover_guard_ref 缺失。", "迁移策略只能口头表达。"], ["onboarding matrix", "wave state evidence", "cutover directive"], refs + ensure_list(checks[0].get("trace_hints"))),
        unit_payload(feat_ref, 2, str(checks[1]["id"]), "pilot chain verifier 验证 producer -> gate -> formal -> consumer -> audit", priority, layers, [str(checks[1]["given"]), "foundation 流程已提供 gate / formal / IO 基础能力。"], "执行真实 pilot chain verifier。", ["producer handoff", "gate decision", "formal publication", "consumer admission", "audit evidence。"], ["至少一条真实 pilot 主链完整跑通。", "五段链路都有可追溯 evidence。"], ["任一链路缺段仍被视为通过。", "仅组件内自测而无真实 pilot evidence。"], ["pilot evidence package", "end-to-end chain trace", "audit submission evidence"], refs + ensure_list(checks[1].get("trace_hints"))),
        unit_payload(feat_ref, 3, str(checks[1]["id"]), "pilot evidence 缺失时 rollout 必须 fail closed", priority, layers, ["pilot chain verifier 未产出完整 evidence。"], "尝试推进 wave 或 cutover。", ["rollout decision", "wave state", "denied / blocked verdict。"], ["evidence 不足时不能继续 rollout。", "wave 维持 fail closed 状态。"], ["evidence 缺失仍可推进 wave。", "rollout guard 被绕过。"], ["blocked rollout evidence", "wave state denial trace"], refs + ["fail closed", "pilot evidence package"]),
        unit_payload(feat_ref, 4, None, "fallback 结果必须记录到 receipt / wave state", priority, layers, ["fallback 或 rollback 场景已触发。", "receipt 与 wave state 都允许 authoritative writeback。"], "执行 fallback / rollback，并写回 receipt 与 wave state。", ["fallback result", "receipt / wave state writeback", "fallback reason code。"], ["fallback 结果被记录并可追溯。", "receipt 与 wave state 保持同一条 authoritative update trace。"], ["fallback 未记录到 receipt 或 wave state。", "fallback 结果无法回放或审计。"], ["fallback evidence", "wave state update", "receipt writeback trace"], refs + ensure_list(checks[2].get("trace_hints")), derivation_basis=["fallback writeback obligation", "wave state auditability", "cutover / rollback trace closure"]),
        unit_payload(feat_ref, 5, str(checks[2]["id"]), "adoption scope 不得扩张为仓库级全局治理改造", priority, layers, [str(checks[2]["given"]), "待评估方案包含超出 governed skill onboarding / pilot / cutover 的全局治理动作。"], "提交包含仓库级治理动作的 adoption 方案，并执行 FEAT boundary check。", ["scope boundary verdict", "rejected expansion note", "accepted onboarding scope。"], ["scope 仅限 governed skill onboarding / pilot / cutover。", "仓库级治理扩张请求被明确拒绝。"], ["把仓库级治理清理纳入该 FEAT。", "scope expansion 未留下明确 verdict。"], ["scope boundary verdict", "rejected expansion evidence", "boundary review note"], refs + ensure_list(checks[2].get("trace_hints")) + ["scope boundary"]),
    ]


def derive_test_units(
    feature: dict[str, Any],
    layers: list[str],
    profile: str,
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    if profile == "collaboration":
        return collaboration_units(feature, layers, priority, refs)
    if profile == "gate":
        return gate_units(feature, layers, priority, refs)
    if profile == "formal":
        return formal_units(feature, layers, priority, refs)
    if profile == "io":
        return io_units(feature, layers, priority, refs)
    if profile == "pilot":
        return pilot_units(feature, layers, priority, refs)
    return default_units(feature, layers, priority, refs)


def derive_acceptance_traceability(
    feature: dict[str, Any],
    units: list[dict[str, Any]],
    profile: str,
) -> list[dict[str, Any]]:
    mapping: list[dict[str, Any]] = []
    for check in feature.get("acceptance_checks") or []:
        acceptance_ref = str(check.get("id") or "")
        covered = [unit["unit_ref"] for unit in units if unit.get("acceptance_ref") == acceptance_ref]
        scenario = str(check.get("scenario") or "")
        given = str(check.get("given") or "")
        when = str(check.get("when") or "")
        then = str(check.get("then") or "")
        if profile == "pilot" and "At least one real pilot chain is required" in scenario:
            when = "执行 pilot chain verifier 并评估 adoption readiness"
            then = "至少一条 producer -> gate -> formal -> consumer -> audit 真实 pilot 主链必须被验证，不能只依赖组件内自测。"
        elif profile == "pilot" and "Adoption scope does not expand into repository-wide governance" in scenario:
            then = "onboarding scope 必须保持在 governed skill onboarding / pilot / cutover 范围内，并拒绝仓库级治理扩张。"
        elif profile == "collaboration" and "approval and re-entry semantics outside this FEAT" in then:
            then = "提交完成后只暴露 authoritative handoff 与 pending visibility；decision-driven revise/retry runtime routing 可以回流，但 gate decision issuance / approval 语义仍在本 FEAT 外。"
        mapping.append(
            {
                "acceptance_ref": acceptance_ref,
                "acceptance_scenario": scenario,
                "given": given,
                "when": when,
                "then": then,
                "unit_refs": covered,
                "coverage_status": "covered" if covered else "missing",
                "coverage_notes": "Acceptance is explicitly mapped to executable minimum coverage units." if covered else "Acceptance has not been mapped to a test unit.",
            }
        )
    return mapping
