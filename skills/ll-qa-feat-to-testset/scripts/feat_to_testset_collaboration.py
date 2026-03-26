#!/usr/bin/env python3
"""Collaboration-profile unit derivation for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, unique_strings


def _unit_payload(
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
    test_set_id = feat_ref.replace("FEAT-", "TS-")
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


def collaboration_units(
    feature: dict[str, Any],
    layers: list[str],
    priority: str,
    refs: list[str],
) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    if not isinstance(checks, list):
        checks = []
    check_ids = [str(item.get("id") or "") for item in checks if isinstance(item, dict)]
    ac1, ac2, ac3 = (check_ids + ["", "", ""])[:3]
    common = [
        "candidate package",
        "handoff submission",
        "gate-consumable pending state",
        "revision / retry re-entry",
        "pending_state",
        "gate_pending_ref",
        "assigned_gate_queue",
        "trace_ref",
        "canonical_payload_path",
        "success envelope",
        "error envelope",
        "duplicate_submission",
        "retryable",
        "idempotent_replay",
        "decision_returned",
        "reentry_directive",
    ]
    loop_refs = refs + common + ["execution loop", "gate loop", "human loop", "responsibility split"]
    flow_refs = refs + common + ["handoff object", "gate pending", "submission completed", "not yet approved"]
    downstream_refs = refs + common + ["downstream inheritance", "queue", "handoff", "gate"]
    return [
        _unit_payload(
            feat_ref, 1, ac1,
            "candidate submit-mainline 明确 execution / gate / human loop 的责任边界",
            priority, layers,
            ensure_list(feature.get("dependencies")) + [
                "candidate package 已就绪且准备进入主链 handoff。",
                "Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。",
                "Boundary to 对象分层与准入能力: 本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。",
            ],
            "执行 candidate package submit-mainline，并记录 execution loop、gate loop、human loop 的 transition ownership。",
            ["authoritative handoff submission", "loop ownership map", "return path / re-entry target", "decision-driven runtime routing boundary"],
            ["每个 loop 只拥有一类明确 transition。", "handoff 不挟带 gate decision issuance 或 approval authority。", "revise/retry routing 由 runtime 持有而不是由业务 skill 私下拼接。"],
            ["loop ownership 重叠。", "candidate submit-mainline 暗含 gate decision / publication 职责。"],
            ["handoff submission evidence", "loop transition trace", "ownership snapshot"],
            loop_refs,
        ),
        _unit_payload(
            feat_ref, 2, ac1,
            "authoritative handoff submission 必须形成单一 payload trace 与 canonical refs",
            priority, layers,
            ensure_list(feature.get("dependencies")) + [
                "candidate package payload 与 trace context 已可解析。",
                "Boundary to 正式交接与物化能力: 本 FEAT 只负责协作责任、状态流转与回流条件，不负责 formalization 语义、升级判定与物化结果。",
                "Boundary to 对象分层与准入能力: 本 FEAT 可以要求对象交接，但对象是否具备正式消费资格由对象分层 FEAT 决定。",
            ],
            "完成一次 submit-mainline，并读取 handoff object、trace_ref 与 canonical_payload_path。",
            ["handoff object", "trace_ref / canonical_payload_path", "authoritative payload identity", "single submission path"],
            ["handoff object 必须指向单一 authoritative payload path。", "trace_ref 与 canonical_payload_path 必须可追溯。", "candidate 提交不会生成第二套并行 payload identity。"],
            ["handoff object 缺少 canonical_payload_path 或 trace_ref。", "同一次提交生成并行 payload identity。"],
            ["handoff object evidence", "trace_ref evidence", "canonical payload path evidence"],
            loop_refs,
        ),
        _unit_payload(
            feat_ref, 3, ac2,
            "submission 完成后只暴露 authoritative handoff 与 pending-intake 结果",
            priority, layers,
            ["A candidate package has been submitted into the mainline", "gate consumer 可以读取 handoff submission、pending_state 与 response envelope。"],
            "完成一次 candidate 提交后，读取 authoritative handoff object 与 gate-consumable pending state。",
            ["handoff object", "pending_state / gate_pending_ref / assigned_gate_queue", "trace_ref / canonical_payload_path", "success envelope / error envelope", "upstream visible completion signal"],
            ["上游只看到提交完成与 pending visibility。", "response envelope 必须携带 pending_state、gate_pending_ref、assigned_gate_queue、trace_ref、canonical_payload_path。", "duplicate_submission 必须维持 idempotent replay 语义，不得把提交完成误标成 approve 或 freeze。"],
            ["提交完成被误标成 approval。", "缺少 authoritative handoff object、pending_state 或 canonical refs。", "duplicate_submission 不能稳定映射到 idempotent replay。"],
            ["submission completion evidence", "handoff object read trace", "pending visibility evidence", "response envelope snapshot"],
            flow_refs,
        ),
        _unit_payload(
            feat_ref, 4, ac2,
            "duplicate_submission 相同 payload 必须返回 idempotent replay 结果",
            priority, layers,
            ["A candidate package has been submitted into the mainline", "同一 proposal_ref 与同一 payload 被再次提交。"],
            "对同一 payload 重复执行 submit-mainline，并对比返回的 handoff_ref 与 replay 语义。",
            ["handoff_ref stability", "retryable / idempotent_replay flags", "response envelope reuse"],
            ["重复提交相同 payload 时必须复用同一 handoff_ref。", "response envelope 必须明确 retryable=true 与 idempotent_replay=true。", "不得因重复提交生成第二个 pending queue item identity。"],
            ["相同 payload 重复提交生成新的 handoff_ref。", "缺少 retryable 或 idempotent_replay 标记。"],
            ["duplicate submission evidence", "handoff_ref comparison", "idempotent replay response snapshot"],
            flow_refs,
        ),
        _unit_payload(
            feat_ref, 5, ac2,
            "duplicate_submission 不同 payload 必须 fail closed 而不是静默覆盖",
            priority, layers,
            ["A candidate package has been submitted into the mainline", "同一 proposal_ref 对应不同 payload digest。"],
            "用相同 proposal_ref 但不同 payload 内容重复提交 candidate，并观察 submit-mainline 返回。",
            ["payload digest comparison", "precondition failure verdict", "queue / handoff mutation result"],
            ["不同 payload 的 duplicate_submission 必须被拒绝。", "已有 handoff / pending identity 不得被静默覆盖。", "错误结果必须保留可审计 verdict。"],
            ["不同 payload 被当成 idempotent replay 接受。", "已有 handoff / pending identity 被静默覆盖。"],
            ["payload mismatch rejection evidence", "precondition failure verdict", "handoff mutation denial trace"],
            flow_refs + ["payload_digest", "precondition_failed"],
            derivation_basis=["payload mismatch duplicate guard", "authoritative handoff immutability"],
        ),
        _unit_payload(
            feat_ref, 6, ac2,
            "revise / retry decision return 必须回到 runtime re-entry，而不是泄漏 approval 语义",
            priority, layers,
            ["A candidate package has been submitted into the mainline", "handoff 已进入 gate decision 链。"],
            "分别对已提交 handoff 触发 revise 与 retry decision，并读取 runtime return。",
            ["reentry_directive_ref", "boundary_handoff_ref", "decision_type", "routing hint"],
            ["revise / retry 必须生成 runtime re-entry directive。", "response 不得泄漏 approve / freeze / publication 完成语义。", "decision return 必须保持与 handoff 同一条 authoritative trace。"],
            ["revise / retry 没有生成 reentry directive。", "decision return 被误标成 approve / freeze / publication 完成。"],
            ["decision return evidence", "reentry directive snapshot", "routing boundary trace"],
            flow_refs,
        ),
        _unit_payload(
            feat_ref, 7, ac3,
            "下游 workflow 继承同一套协作规则而不重建并行 queue / handoff 模型",
            priority, layers,
            ["A downstream workflow consumes this FEAT", "下游 workflow 已接入 authoritative handoff submission 消费链。"],
            "让一个下游 workflow 消费 handoff submission，并校验其 queue、gate、human coordination 语义是否直接继承主链规则。",
            ["downstream queue model", "handoff contract reuse", "re-entry / retry boundary", "retryable / idempotent_replay field semantics"],
            ["下游直接继承主链 queue / handoff / gate 语义。", "没有并行 handoff model 或额外 queue。", "若上游已冻结 retryable / idempotent_replay 语义，下游必须直接复用；若上游尚未冻结完整 error mapping table，下游不得自创并行定义。"],
            ["下游重新定义 handoff 规则。", "出现并行 queue 或重写 re-entry 语义。", "在没有上游 authoritative mapping table 时，下游自行发明 retryable / idempotent_replay 规则。"],
            ["downstream integration evidence", "queue inheritance trace", "handoff contract comparison", "retryable / idempotent_replay semantics note"],
            downstream_refs,
        ),
        _unit_payload(
            feat_ref, 8, ac3,
            "下游 workflow 必须直接复用 retryable / idempotent_replay / canonical refs 语义",
            priority, layers,
            ["A downstream workflow consumes this FEAT", "下游 workflow 会消费主链 handoff response envelope。"],
            "让下游 workflow 消费已有 handoff response envelope，并校验 retryable / idempotent_replay / canonical refs 是否被原样继承。",
            ["retryable / idempotent_replay inheritance", "trace_ref reuse", "canonical_payload_path reuse"],
            ["下游不得改写 retryable / idempotent_replay / canonical refs 语义。", "trace_ref 与 canonical_payload_path 必须保持与主链同源。", "不能为同一 handoff 再造新的 queue / trace contract。"],
            ["下游改写 retryable / idempotent_replay 字段定义。", "下游为同一 handoff 生成新的 canonical refs 语义。"],
            ["downstream response envelope comparison", "canonical refs inheritance trace", "queue model comparison"],
            downstream_refs,
        ),
        _unit_payload(
            feat_ref, 9, ac2,
            "payload_ref 缺失或坏路径时 submit-mainline 必须 fail closed",
            priority, layers,
            ["A candidate package has been submitted into the mainline", "payload_ref 缺失、不可读或无法解析到 candidate payload。"],
            "提交缺失 payload_ref 或坏路径的 candidate，并读取 submit-mainline 结果。",
            ["precondition failure verdict", "payload path resolution result", "handoff / pending side effects"],
            ["payload_ref 缺失或坏路径时必须返回 fail-closed verdict。", "不得生成 handoff 或 pending item。", "错误结果必须留下可追溯 precondition failure evidence。"],
            ["payload_ref 缺失时仍生成 handoff 或 pending item。", "错误结果没有清晰 verdict 或 trace。"],
            ["missing payload rejection evidence", "path resolution failure trace", "side effect absence evidence"],
            flow_refs + ["payload_ref", "precondition_failed", "path_resolution"],
            derivation_basis=["missing payload must fail closed", "authoritative handoff requires readable payload"],
        ),
        _unit_payload(
            feat_ref, 10, ac2,
            "无待处理 handoff 时 pending visibility 不得伪造 queue 项",
            priority, layers,
            ["A candidate package has been submitted into the mainline", "当前 gate pending queue 为空。"],
            "在没有任何 submission 的前提下读取 pending visibility。",
            ["pending_count", "pending_items list", "queue visibility response"],
            ["pending_count 必须为 0。", "pending_items 为空时不得伪造 handoff / queue item。", "空队列结果仍需保持 machine-readable response shape。"],
            ["空队列被伪造为存在 pending item。", "空队列结果缺少稳定 response shape。"],
            ["empty pending evidence", "queue visibility response snapshot"],
            flow_refs + ["empty_pending"],
            derivation_basis=["pending visibility empty-state correctness", "queue result shape stability"],
        ),
    ]
