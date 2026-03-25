#!/usr/bin/env python3
"""
Deterministic derivation helpers for feat-to-testset.
"""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import (
    derive_test_set_id,
    derive_test_set_ref,
    ensure_list,
    slugify,
    unique_strings,
)


def governing_adrs(feature: dict[str, Any], package_json: dict[str, Any]) -> list[str]:
    refs = ensure_list(feature.get("source_refs")) + ensure_list(package_json.get("source_refs"))
    return unique_strings([ref for ref in refs if ref.startswith("ADR-")])


def feature_profile(feature: dict[str, Any]) -> str:
    title_text = " ".join(
        [
            str(feature.get("title") or ""),
            str(feature.get("authoritative_artifact") or ""),
            str(feature.get("axis_id") or ""),
            str(feature.get("derived_axis") or ""),
        ]
    ).lower()
    related_text = " ".join(
        ensure_list(feature.get("consumes")) + ensure_list(feature.get("produces"))
    ).lower()
    fallback_text = " ".join(
        ensure_list(feature.get("scope"))
        + ensure_list(feature.get("constraints"))
        + ensure_list(feature.get("dependencies"))
        + [
            str(feature.get("gate_decision_dependency") or ""),
            str(feature.get("admission_dependency") or ""),
        ]
    ).lower()
    if any(marker in title_text for marker in ["governed write-read receipt", "managed ref", "receipt", "registry", "artifact-io-governance", "governed io", "落盘与读取流"]):
        return "io"
    if any(marker in title_text for marker in ["formal publication", "formal ref", "lineage", "admission", "formal object", "formal 发布", "准入流"]):
        return "formal"
    if any(marker in title_text for marker in ["gate", "decision object", "handoff-formalization", "审核与裁决流"]):
        return "gate"
    if any(marker in title_text for marker in ["candidate", "handoff submission", "collaboration-loop", "候选提交与交接流"]):
        return "collaboration"
    if any(marker in title_text for marker in ["pilot", "onboarding", "cutover", "fallback", "wave", "compat mode", "skill-adoption-e2e", "接入与 pilot 验证流"]):
        return "pilot"
    if any(marker in related_text for marker in ["governed write-read receipt", "managed ref", "receipt", "registry", "commit-governed", "path policy"]):
        return "io"
    if any(marker in related_text for marker in ["formal publication", "formal ref", "lineage", "admission", "formal object"]):
        return "formal"
    if any(marker in related_text for marker in ["gate", "decision object", "decision path"]):
        return "gate"
    if any(marker in related_text for marker in ["candidate", "handoff submission", "loop", "re-entry"]):
        return "collaboration"
    if any(marker in related_text for marker in ["pilot", "onboarding", "cutover", "fallback", "wave", "compat mode"]):
        return "pilot"
    text = f"{title_text} {related_text} {fallback_text}"
    if any(marker in text for marker in ["managed ref", "receipt", "registry", "commit-governed", "path policy"]):
        return "io"
    if any(marker in text for marker in ["formal publication", "formal ref", "lineage", "admission", "formal object"]):
        return "formal"
    if any(marker in text for marker in ["gate", "decision object", "decision path", "approve / revise / retry / handoff / reject"]):
        return "gate"
    if any(marker in text for marker in ["candidate", "handoff submission", "loop", "re-entry"]):
        return "collaboration"
    if any(marker in text for marker in ["pilot", "onboarding", "cutover", "fallback", "wave", "compat mode"]):
        return "pilot"
    return "default"


def derive_priority(feature: dict[str, Any]) -> str:
    track = str(feature.get("track") or "").lower()
    profile = feature_profile(feature)
    text = " ".join(
        ensure_list(feature.get("scope"))
        + ensure_list(feature.get("constraints"))
        + [str(feature.get("title") or "")]
    ).lower()
    if profile == "pilot" or "adoption" in track or "e2e" in track or "pilot" in text:
        return "P1"
    return "P0"


def derive_test_layers(feature: dict[str, Any]) -> list[str]:
    layers = ["integration"]
    joined_text = " ".join(
        ensure_list(feature.get("scope"))
        + [str(feature.get("axis_id") or ""), str(feature.get("track") or ""), feature_profile(feature)]
    ).lower()
    if any(marker in joined_text for marker in ["e2e", "pilot", "ui", "cross skill", "cross-skill"]):
        layers.append("e2e")
    return layers


def supporting_contract_refs(feature: dict[str, Any]) -> list[str]:
    profile = feature_profile(feature)
    refs = ensure_list(feature.get("source_refs"))
    if profile == "formal":
        refs += ["resolve-formal-ref", "verify-eligibility", "formal_ref", "lineage", "admission verdict"]
    elif profile == "io":
        refs += [
            "commit-governed",
            "read-governed",
            "policy_deny",
            "registry_prerequisite_failed",
            "receipt_pending",
            "receipt_ref",
            "registry_record_ref",
            "managed_artifact_ref",
        ]
    elif profile == "pilot":
        refs += [
            "OnboardingMatrix",
            "CutoverDirective",
            "PilotEvidenceRef",
            "compat_mode",
            "wave_id",
            "cutover_guard_ref",
            "producer -> gate -> formal -> consumer -> audit",
        ]
    elif profile == "gate":
        refs += [
            "authoritative decision object",
            "approve / revise / retry / handoff / reject",
            "formal publication trigger",
            "decision uniqueness",
        ]
    elif profile == "collaboration":
        refs += [
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
    return unique_strings(refs)


def derive_environment_assumptions(feature: dict[str, Any], layers: list[str]) -> list[str]:
    assumptions = [
        "需要可解析 selected FEAT 所依赖的集成环境与上游 artifact lineage。",
        "需要能读取并追踪 FEAT、EPIC、SRC 与 governing ADR 引用。",
        "需要保留 execution evidence 与 supervision evidence 所要求的最小审计链。",
    ]
    profile = feature_profile(feature)
    if "e2e" in layers:
        assumptions.append("若启用 e2e 层，必须具备可重复执行的 UI 或跨服务集成上下文。")
    if ensure_list(feature.get("dependencies")):
        assumptions.append("依赖服务或上游能力应以可观测、可判定的方式处于可用状态。")
    if profile == "formal":
        assumptions.extend(
            [
                "formal publication、formal ref 与 lineage 解析链必须可被重复验证。",
                "admission checker 必须能在缺少 lineage 或 formal ref 时 fail closed。",
            ]
        )
    elif profile == "io":
        assumptions.extend(
            [
                "Gateway / Path Policy / Registry 必须在同一受治理链路中返回稳定 verdict。",
                "receipt_ref、registry_record_ref 与 managed_artifact_ref 解析上下文必须可观测。",
            ]
        )
    elif profile == "pilot":
        assumptions.extend(
            [
                "真实 pilot chain 需要 producer、gate、formal、consumer、audit 五段至少一条完整连通。",
                "wave state、compat_mode 与 cutover_guard_ref 必须可追溯且可回放。",
            ]
        )
    elif profile == "gate":
        assumptions.extend(
            [
                "candidate -> gate decision -> formal trigger 的业务链路必须只有一条 authoritative path。",
                "decision object 的唯一性与回流目标必须可观测。",
            ]
        )
    return unique_strings(assumptions)


def derive_required_environment_inputs(feature: dict[str, Any], layers: list[str]) -> dict[str, list[str]]:
    scope_text = " ".join(ensure_list(feature.get("scope"))).lower()
    profile = feature_profile(feature)
    payload = {
        "environment": unique_strings(
            [
                "可运行 selected FEAT 的集成环境",
                "可解析 source_refs 的受治理 workspace 上下文",
            ]
            + (["可重复的端到端验证环境"] if "e2e" in layers else [])
        ),
        "data": [
            "覆盖 FEAT acceptance checks 所需的最小测试数据或 fixtures",
            "可重建 analysis/strategy trace 的输入样本",
        ],
        "services": unique_strings(
            [
                "selected FEAT 所依赖的集成服务或协作 consumer",
            ]
            + (["跨 skill pilot 链路涉及的 producer / consumer / gate consumer"] if "pilot" in scope_text or "cross skill" in scope_text else [])
        ),
        "access": [
            "读取 FEAT candidate / freeze lineage 所需权限",
            "执行 QA evidence 采集与落盘所需权限",
        ],
        "feature_flags": [
            "selected FEAT 涉及的 gated rollout、cutover 或 guarded branch 开关",
        ],
        "ui_or_integration_context": [
            "驱动 FEAT acceptance checks 的 UI 路径或 integration context",
        ],
    }
    if profile == "formal":
        payload["data"] += ["approved decision object、formal_ref、lineage fixture", "lineage_missing 与 layer_violation 失败样本"]
        payload["services"] += ["formal publication publisher", "registry formal-ref resolution / admission checker"]
        payload["access"] += [
            "读取 formal publication package、formal ref、admission verdict 的权限",
            "formal publisher service account、admission API token 或等价 credential material",
        ]
        payload["feature_flags"] += ["formal publication guarded-only enablement / admission strict mode"]
        payload["ui_or_integration_context"] += ["resolve-formal-ref / verify-eligibility 调用上下文"]
    elif profile == "collaboration":
        payload["data"] += [
            "candidate package、authoritative handoff submission、pending_state fixture",
            "gate_pending_ref、assigned_gate_queue、trace_ref、canonical_payload_path fixture",
            "submission completion、response envelope、re-entry boundary、downstream inheritance 样本",
        ]
        payload["services"] += [
            "authoritative handoff submission writer",
            "pending-intake state reader / downstream handoff consumer",
            "decision-return reader / runtime re-entry directive consumer",
        ]
        payload["access"] += [
            "提交 authoritative handoff submission、读取 pending-intake state 与 downstream inheritance evidence 的权限",
            "execution/gate/human loop handoff service identity 或等价账号材料",
        ]
        payload["feature_flags"] += ["submit-mainline visibility / re-entry boundary guard 开关"]
        payload["ui_or_integration_context"] += ["candidate submit-mainline -> pending-intake -> downstream inherit 业务流上下文"]
    elif profile == "io":
        payload["environment"] += ["Gateway / Path Policy / Registry 共用的 governed runtime 环境"]
        payload["data"] += ["receipt_ref、registry_record_ref、managed_artifact_ref fixture", "policy_deny / registry_prerequisite_failed / receipt_pending 失败样本"]
        payload["services"] += ["Artifact IO Gateway", "Path Policy evaluator", "Registry binder / managed read resolver"]
        payload["access"] += [
            "执行 commit-governed / read-governed、查看 receipt 与 registry record 的权限",
            "Gateway service account、registry binder credential、managed read/write API token 或等价账号材料",
        ]
        payload["feature_flags"] += ["compat_mode / managed-write enforcement / fallback guard 开关"]
        payload["ui_or_integration_context"] += ["commit-governed 与 read-governed 请求响应上下文"]
    elif profile == "pilot":
        payload["environment"] += ["包含 producer / gate / formal / consumer / audit 的真实 pilot chain 环境"]
        payload["data"] += ["onboarding matrix、wave state、pilot evidence、cutover recommendation", "fallback / rollback evidence fixture"]
        payload["services"] += ["rollout onboarding registry", "pilot chain verifier", "audit evidence submitter"]
        payload["access"] += [
            "rollout owner、audit submit、gate consume、consumer validate 权限",
            "pilot producer/consumer service account、audit submit token、cutover operator credential 或等价账号材料",
        ]
        payload["feature_flags"] += ["compat_mode、wave gate、cutover_guard_ref、fallback enablement 开关"]
        payload["ui_or_integration_context"] += ["producer -> gate -> formal -> consumer -> audit pilot chain 上下文"]
    elif profile == "gate":
        payload["data"] += ["candidate package、handoff submission、decision object fixture", "approve / revise / retry / handoff / reject 决策样本"]
        payload["services"] += ["gate evaluator / reviewer context", "formal publication trigger consumer"]
        payload["access"] += [
            "读取 candidate package、写入 decision evidence、查看 gate decision result 的权限",
            "gate evaluator service account、decision writer token 或等价 credential material",
        ]
        payload["feature_flags"] += ["gate decision routing / formal trigger guard 开关"]
        payload["ui_or_integration_context"] += ["handoff -> gate decision -> formal trigger 业务流上下文"]
    return {key: unique_strings(values) for key, values in payload.items()}


def derive_coverage_exclusions(feature: dict[str, Any]) -> list[str]:
    exclusions = ensure_list(feature.get("non_goals"))[:3]
    if not exclusions:
        exclusions = [
            "不覆盖 selected FEAT 之外的相邻 FEAT 语义。",
            "不把本 TESTSET 扩展为 TASK、TECH 或 runner-level 实现细节。",
        ]
    return exclusions


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


def default_units(feature: dict[str, Any], layers: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    units: list[dict[str, Any]] = []
    priority = derive_priority(feature)
    refs = supporting_contract_refs(feature)
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


def collaboration_units(feature: dict[str, Any], layers: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    refs = supporting_contract_refs(feature)
    return [
        unit_payload(
            feat_ref,
            1,
            str(checks[0]["id"]),
            "candidate submit-mainline 明确 execution / gate / human loop 的责任边界",
            derive_priority(feature),
            layers,
            [str(checks[0]["given"]), "candidate package 已就绪且准备进入主链 handoff。"] + ensure_list(feature.get("dependencies"))[:2],
            "执行 candidate package submit-mainline，并记录 execution loop、gate loop、human loop 的 transition ownership。",
            [
                "authoritative handoff submission",
                "loop ownership map",
                "return path / re-entry target",
                "decision-driven runtime routing boundary",
            ],
            ["每个 loop 只拥有一类明确 transition。", "handoff 不挟带 formalization 或 approval authority。", "revise/retry routing 由 runtime 持有而不是由业务 skill 私下拼接。"],
            ["loop ownership 重叠。", "candidate submit-mainline 暗含 formalization 职责。"],
            ["handoff submission evidence", "loop transition trace", "ownership snapshot"],
            refs + ensure_list(checks[0].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            2,
            str(checks[1]["id"]),
            "submission 完成后只暴露 authoritative handoff 与 pending-intake 结果",
            derive_priority(feature),
            layers,
            [str(checks[1]["given"]), "gate consumer 可以读取 handoff submission、pending_state 与 response envelope。"] + ensure_list(feature.get("dependencies"))[:2],
            "完成一次 candidate 提交后，读取 authoritative handoff object 与 gate-consumable pending state。",
            [
                "handoff object",
                "pending_state / gate_pending_ref / assigned_gate_queue",
                "trace_ref / canonical_payload_path",
                "success envelope / error envelope",
                "upstream visible completion signal",
            ],
            [
                "上游只看到提交完成与 pending visibility。",
                "response envelope 必须携带 pending_state、gate_pending_ref、assigned_gate_queue、trace_ref、canonical_payload_path。",
                "duplicate_submission 必须维持 idempotent replay 语义，不得把提交完成误标成 approve 或 freeze。",
            ],
            [
                "提交完成被误标成 approval。",
                "缺少 authoritative handoff object、pending_state 或 canonical refs。",
                "duplicate_submission 不能稳定映射到 idempotent replay。",
            ],
            [
                "submission completion evidence",
                "handoff object read trace",
                "pending visibility evidence",
                "response envelope snapshot",
            ],
            refs + ensure_list(checks[1].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            3,
            str(checks[2]["id"]),
            "下游 workflow 继承同一套协作规则而不重建并行 queue / handoff 模型",
            derive_priority(feature),
            layers,
            [str(checks[2]["given"]), "下游 workflow 已接入 authoritative handoff submission 消费链。"] + ensure_list(feature.get("dependencies"))[:2],
            "让一个下游 workflow 消费 handoff submission，并校验其 queue、gate、human coordination 语义是否直接继承主链规则。",
            [
                "downstream queue model",
                "handoff contract reuse",
                "re-entry / retry boundary",
                "retryable / idempotent_replay field semantics",
            ],
            [
                "下游直接继承主链 queue / handoff / gate 语义。",
                "没有并行 handoff model 或额外 queue。",
                "若上游已冻结 retryable / idempotent_replay 语义，下游必须直接复用；若上游尚未冻结完整 error mapping table，下游不得自创并行定义。",
            ],
            [
                "下游重新定义 handoff 规则。",
                "出现并行 queue 或重写 re-entry 语义。",
                "在没有上游 authoritative mapping table 时，下游自行发明 retryable / idempotent_replay 规则。",
            ],
            [
                "downstream integration evidence",
                "queue inheritance trace",
                "handoff contract comparison",
                "retryable / idempotent_replay semantics note",
            ],
            refs + ensure_list(checks[2].get("trace_hints")),
        ),
    ]


def gate_units(feature: dict[str, Any], layers: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    refs = supporting_contract_refs(feature)
    return [
        unit_payload(
            feat_ref,
            1,
            str(checks[0]["id"]),
            "authoritative handoff 进入单一路径的 gate 决策链",
            derive_priority(feature),
            layers,
            [str(checks[0]["given"]), "candidate package 已形成 authoritative handoff submission。"],
            "提交 handoff 并触发 gate evaluate。",
            ["只生成一个 authoritative decision object。", "decision path 不出现平行 shortcut。"],
            ["handoff -> decision 链唯一且可追溯。", "decision object 可被 formal publish 流消费。"],
            ["出现并行 decision path。", "缺少 authoritative decision object。"],
            ["gate decision response", "decision object evidence", "handoff submission trace"],
            refs + ensure_list(checks[0].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            2,
            str(checks[0]["id"]),
            "decision object 对 approve / revise / retry / handoff / reject 保持唯一业务语义",
            derive_priority(feature),
            layers,
            ["gate evaluator 能访问候选交接与审核上下文。"],
            "对同一候选输入分别验证 decision 结果分支。",
            ["不同 decision_type 的返回去向。", "回流或终止目标是否稳定。"],
            ["每个 decision_type 都映射到唯一业务去向。", "formal 发布触发不与 revise/retry/reject 混层。"],
            ["decision_type 语义不唯一。", "返回去向与主链职责混乱。"],
            ["decision branch evidence", "review summary", "routing trace"],
            refs,
        ),
        unit_payload(
            feat_ref,
            3,
            str(checks[1]["id"]),
            "candidate 在 gate 前不得被当作 downstream formal source",
            derive_priority(feature),
            layers,
            [str(checks[1]["given"]), "candidate package 与 formal publication package 保持分层。"],
            str(checks[1]["when"]),
            ["下游读取对象类型。", "是否绕过 gate 直接消费 candidate。"],
            ["candidate 不得作为 formal downstream source。", "必须等待 authoritative decision object。"],
            ["candidate 被直接当作 formal 输入。", "绕过 gate 的旁路成立。"],
            ["negative path evidence", "downstream resolution trace"],
            refs + ensure_list(checks[1].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            4,
            str(checks[2]["id"]),
            "formal publication 只由 approve decision object 触发",
            derive_priority(feature),
            layers,
            [str(checks[2]["given"]), "formal publish control layer 可消费 approve decision object。"],
            str(checks[2]["when"]),
            ["formal publication trigger source。", "business skill 是否承担 approval authority。"],
            ["只有 approve decision object 能触发 formal publish。", "业务 skill 不得替代 gate approval authority。"],
            ["非 decision 对象也可触发 formal publish。", "business skill 静默承担审批职责。"],
            ["formal publication trigger evidence", "approval path audit trace"],
            refs + ensure_list(checks[2].get("trace_hints")),
        ),
    ]


def formal_units(feature: dict[str, Any], layers: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    refs = supporting_contract_refs(feature)
    return [
        unit_payload(
            feat_ref,
            1,
            str(checks[0]["id"]),
            "approved decision 进入唯一 formal publication -> admission 链",
            derive_priority(feature),
            layers,
            [str(checks[0]["given"]), "approve decision object 与 approval lineage context 可解析。"],
            str(checks[0]["when"]),
            ["formal publication package 是否唯一。", "formal ref / lineage 是否形成 authoritative downstream input。"],
            ["approved decision 只对应一条 formal publication -> admission 链。", "旁路对象不能跳过 formal ref 与 lineage。"],
            ["存在多条 formal publication path。", "formal ref / lineage 缺失仍被放行。"],
            ["formal publication package", "formal_ref resolution evidence", "lineage build evidence"],
            refs + ensure_list(checks[0].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            2,
            str(checks[1]["id"]),
            "resolve-formal-ref 返回 authoritative formal ref",
            derive_priority(feature),
            layers,
            [str(checks[1]["given"]), "registry 中存在 formal publication record。"],
            "调用 resolve-formal-ref。",
            ["resolved_artifact_ref", "registry_record_ref", "canonical_path。"],
            ["consumer 能先 resolve authoritative formal ref 再继续 admission。", "返回结果包含 formal ref / registry trace。"],
            ["formal ref 无法解析且被路径猜测替代。", "缺少 registry_record_ref。"],
            ["resolve-formal-ref response", "registry record evidence"],
            refs + ensure_list(checks[1].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            3,
            str(checks[1]["id"]),
            "verify-eligibility 基于 formal ref / lineage 判定 admission",
            derive_priority(feature),
            layers,
            ["admission checker 可访问 formal ref、lineage_summary 与 admission_context。"],
            "调用 verify-eligibility。",
            ["eligibility_result", "lineage_summary", "admission verdict。"],
            ["admission 仅基于 formal ref / lineage 成立。", "缺少 lineage 时必须 deny。"],
            ["基于目录邻近关系放行。", "lineage_missing 时未 fail closed。"],
            ["admission verdict evidence", "deny path evidence for lineage_missing"],
            refs + ["lineage_missing", "admission verdict"],
        ),
        unit_payload(
            feat_ref,
            4,
            str(checks[2]["id"]),
            "candidate 或 intermediate object 不能伪装成 formal deliverable",
            derive_priority(feature),
            layers,
            [str(checks[2]["given"]), "candidate package 与 intermediate object 仍可见。"],
            str(checks[2]["when"]),
            ["downstream resolved input", "layer violation verdict。"],
            ["只有 formal publication package 能通过 admission。", "candidate / intermediate object 必须被拒绝。"],
            ["candidate 或 intermediate object 被当作 formal deliverable。", "layer_violation 未被识别。"],
            ["layer_violation evidence", "downstream resolution trace"],
            refs + ensure_list(checks[2].get("trace_hints")) + ["layer_violation"],
        ),
    ]


def io_units(feature: dict[str, Any], layers: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    refs = supporting_contract_refs(feature)
    return [
        unit_payload(
            feat_ref,
            1,
            str(checks[0]["id"]),
            "commit-governed 写入返回 receipt_ref / registry_record_ref / managed_artifact_ref",
            derive_priority(feature),
            layers,
            [str(checks[0]["given"]), "Gateway / Path Policy / Registry 已连通。"],
            "执行主链正式 write/read。",
            ["policy_verdict", "receipt_ref", "registry_record_ref", "managed_artifact_ref。"],
            ["主链正式写入只走 commit-governed/read-governed。", "成功路径返回完整 managed refs 与 receipt。"],
            ["正式写入绕过 Gateway。", "成功路径缺少 receipt 或 registry trace。"],
            ["governed write happy path evidence", "receipt_ref", "registry_record_ref", "managed_artifact_ref"],
            refs + ensure_list(checks[0].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            2,
            str(checks[1]["id"]),
            "主链 IO 边界拒绝扩展为仓库级全局文件治理",
            derive_priority(feature),
            layers,
            [str(checks[1]["given"]), "测试请求包含超出 handoff / formalization / governed skill IO 的目录动作。"],
            str(checks[1]["when"]),
            ["policy verdict scope", "被拒绝操作的边界说明。"],
            ["仅 mainline governed IO 被纳入受测边界。", "全局文件治理扩展请求被拒绝。"],
            ["测试边界覆盖仓库级全局治理。", "scope expansion 未被识别。"],
            ["boundary denial evidence", "policy scope note"],
            refs + ensure_list(checks[1].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            3,
            str(checks[2]["id"]),
            "policy_deny 时不得 silent fallback 到自由写入",
            derive_priority(feature),
            layers,
            [str(checks[2]["given"]), "preflight 结果为 policy_deny。"],
            str(checks[2]["when"]),
            ["write result status", "是否存在自由写入旁路。"],
            ["policy_deny 返回可追溯 denied 结果。", "不存在 free write fallback。"],
            ["policy_deny 后仍发生自由写入。", "没有返回可审计 verdict。"],
            ["policy_deny evidence", "blocked fallback trace"],
            refs + ensure_list(checks[2].get("trace_hints")) + ["policy_deny"],
        ),
        unit_payload(
            feat_ref,
            4,
            str(checks[2]["id"]),
            "registry_prerequisite_failed 与 receipt_pending 都必须留下可追溯结果",
            derive_priority(feature),
            layers,
            ["registry bind 前置条件或 receipt build 可能失败。"],
            "分别触发 registry_prerequisite_failed 与 receipt_pending 场景。",
            ["partial success 标记", "失败结果 evidence", "重试/补偿上下文。"],
            ["registry_prerequisite_failed 与 receipt_pending 都可被追溯。", "主链不会因部分成功而静默丢失 managed refs 上下文。"],
            ["失败状态无 evidence。", "partial success 没有明确标记。"],
            ["registry_prerequisite_failed evidence", "receipt_pending evidence", "compensation trace"],
            refs + ["registry_prerequisite_failed", "receipt_pending"],
        ),
    ]


def pilot_units(feature: dict[str, Any], layers: list[str]) -> list[dict[str, Any]]:
    feat_ref = str(feature.get("feat_ref") or "")
    checks = feature.get("acceptance_checks") or []
    refs = supporting_contract_refs(feature)
    return [
        unit_payload(
            feat_ref,
            1,
            str(checks[0]["id"]),
            "onboarding matrix 固化 skill、wave_id、compat_mode 与 cutover_guard_ref",
            derive_priority(feature),
            layers,
            [str(checks[0]["given"]), "rollout onboarding contract 可写回 wave state。"],
            "生成 onboarding matrix，并把 wave_id、compat_mode、cutover_guard_ref 写回 rollout state。",
            ["integration matrix", "wave_id", "compat_mode", "cutover_guard_ref。"],
            ["onboarding scope 与 migration waves 可追溯。", "cutover / fallback 规则以 machine-readable 形式存在。"],
            ["wave / compat_mode / cutover_guard_ref 缺失。", "迁移策略只能口头表达。"],
            ["onboarding matrix", "wave state evidence", "cutover directive"],
            refs + ensure_list(checks[0].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            2,
            str(checks[1]["id"]),
            "pilot chain verifier 验证 producer -> gate -> formal -> consumer -> audit",
            derive_priority(feature),
            layers,
            [str(checks[1]["given"]), "foundation 流程已提供 gate / formal / IO 基础能力。"],
            "执行真实 pilot chain verifier。",
            ["producer handoff", "gate decision", "formal publication", "consumer admission", "audit evidence。"],
            ["至少一条真实 pilot 主链完整跑通。", "五段链路都有可追溯 evidence。"],
            ["任一链路缺段仍被视为通过。", "仅组件内自测而无真实 pilot evidence。"],
            ["pilot evidence package", "end-to-end chain trace", "audit submission evidence"],
            refs + ensure_list(checks[1].get("trace_hints")),
        ),
        unit_payload(
            feat_ref,
            3,
            str(checks[1]["id"]),
            "pilot evidence 缺失时 rollout 必须 fail closed",
            derive_priority(feature),
            layers,
            ["pilot chain verifier 未产出完整 evidence。"],
            "尝试推进 wave 或 cutover。",
            ["rollout decision", "wave state", "denied / blocked verdict。"],
            ["evidence 不足时不能继续 rollout。", "wave 维持 fail closed 状态。"],
            ["evidence 缺失仍可推进 wave。", "rollout guard 被绕过。"],
            ["blocked rollout evidence", "wave state denial trace"],
            refs + ["fail closed", "pilot evidence package"],
        ),
        unit_payload(
            feat_ref,
            4,
            None,
            "fallback 结果必须记录到 receipt / wave state",
            derive_priority(feature),
            layers,
            ["fallback 或 rollback 场景已触发。", "receipt 与 wave state 都允许 authoritative writeback。"],
            "执行 fallback / rollback，并写回 receipt 与 wave state。",
            ["fallback result", "receipt / wave state writeback", "fallback reason code。"],
            ["fallback 结果被记录并可追溯。", "receipt 与 wave state 保持同一条 authoritative update trace。"],
            ["fallback 未记录到 receipt 或 wave state。", "fallback 结果无法回放或审计。"],
            ["fallback evidence", "wave state update", "receipt writeback trace"],
            refs + ensure_list(checks[2].get("trace_hints")),
            derivation_basis=["fallback writeback obligation", "wave state auditability", "cutover / rollback trace closure"],
        ),
        unit_payload(
            feat_ref,
            5,
            str(checks[2]["id"]),
            "adoption scope 不得扩张为仓库级全局治理改造",
            derive_priority(feature),
            layers,
            [str(checks[2]["given"]), "待评估方案包含超出 governed skill onboarding / pilot / cutover 的全局治理动作。"],
            "提交包含仓库级治理动作的 adoption 方案，并执行 FEAT boundary check。",
            ["scope boundary verdict", "rejected expansion note", "accepted onboarding scope。"],
            ["scope 仅限 governed skill onboarding / pilot / cutover。", "仓库级治理扩张请求被明确拒绝。"],
            ["把仓库级治理清理纳入该 FEAT。", "scope expansion 未留下明确 verdict。"],
            ["scope boundary verdict", "rejected expansion evidence", "boundary review note"],
            refs + ensure_list(checks[2].get("trace_hints")) + ["scope boundary"],
        ),
    ]


def derive_test_units(feature: dict[str, Any]) -> list[dict[str, Any]]:
    layers = derive_test_layers(feature)
    profile = feature_profile(feature)
    if profile == "collaboration":
        return collaboration_units(feature, layers)
    if profile == "gate":
        return gate_units(feature, layers)
    if profile == "formal":
        return formal_units(feature, layers)
    if profile == "io":
        return io_units(feature, layers)
    if profile == "pilot":
        return pilot_units(feature, layers)
    return default_units(feature, layers)


def derive_acceptance_traceability(feature: dict[str, Any], units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapping: list[dict[str, Any]] = []
    profile = feature_profile(feature)
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
            then = (
                "提交完成后只暴露 authoritative handoff 与 pending visibility；"
                "decision-driven revise/retry runtime routing 可以回流，但 formalization / approval 语义仍在本 FEAT 外。"
            )
        mapping.append(
            {
                "acceptance_ref": acceptance_ref,
                "acceptance_scenario": scenario,
                "given": given,
                "when": when,
                "then": then,
                "unit_refs": covered,
                "coverage_status": "covered" if covered else "missing",
                "coverage_notes": (
                    "Acceptance is explicitly mapped to executable minimum coverage units."
                    if covered
                    else "Acceptance has not been mapped to a test unit."
                ),
            }
        )
    return mapping


def derive_risk_focus(feature: dict[str, Any]) -> list[str]:
    focus = ensure_list(feature.get("constraints"))[:3] + ensure_list(feature.get("dependencies"))[:2]
    if not focus:
        focus = ["保持 FEAT acceptance、traceability 与 evidence closure 一致。"]
    profile = feature_profile(feature)
    if profile == "formal":
        focus += ["formal_ref / lineage 缺失时必须 fail closed。", "candidate 与 formal object 不得混层。"]
    elif profile == "io":
        focus += ["policy_deny 不得 fallback 到自由写入。", "registry / receipt 顺序错误会形成脏 managed ref。"]
    elif profile == "pilot":
        focus += ["真实 pilot chain 缺段会让 adoption 结论失真。", "evidence 不足时 wave 推进必须被阻断。"]
    return unique_strings(focus)


def derive_preconditions(feature: dict[str, Any]) -> list[str]:
    preconditions = ensure_list(feature.get("dependencies"))[:3]
    if not preconditions:
        preconditions = ["selected FEAT 及其上游 source refs 可被稳定解析。"]
    profile = feature_profile(feature)
    if profile == "formal":
        preconditions += ["approve decision object 已存在。", "formal publication / admission contract 可被解析。"]
    elif profile == "io":
        preconditions += ["Gateway / Path Policy / Registry 已接入主链。", "managed write/read preflight 可独立输出 verdict。"]
    elif profile == "pilot":
        preconditions += ["foundation FEAT 对应主链已可执行。", "至少一个真实 pilot scope 已被选定。"]
    return unique_strings(preconditions)


def derive_pass_criteria(feature: dict[str, Any]) -> list[str]:
    criteria = [
        "每条 acceptance check 都有至少一个可执行测试单元映射。",
        "TESTSET 不越界覆盖相邻 FEAT 或新需求。",
        "candidate package 在外置 approval 前保持 machine-readable traceability 与 gate subject identity。",
    ]
    profile = feature_profile(feature)
    if derive_priority(feature) == "P1":
        criteria.append("高风险或 adoption/E2E 路径需要明确的环境、数据与 pilot execution 前提。")
    if profile == "formal":
        criteria += [
            "formal_ref / lineage / admission verdict 必须形成单一 authoritative consumption path。",
            "lineage_missing 或 layer_violation 必须 fail closed。",
        ]
    elif profile == "io":
        criteria += [
            "commit-governed / read-governed 成功路径必须返回 receipt_ref、registry_record_ref、managed_artifact_ref。",
            "policy_deny / registry_prerequisite_failed / receipt_pending 必须留下可追溯结果且不得 fallback。",
        ]
    elif profile == "pilot":
        criteria += [
            "至少一条 producer -> gate -> formal -> consumer -> audit 真实 pilot 主链被验证。",
            "pilot evidence 缺失时 rollout 必须 fail closed，fallback / wave state 必须可追溯。",
        ]
    elif profile == "gate":
        criteria += [
            "gate decision path 必须唯一，decision object 不得并行分叉。",
            "formal publication 只由 approve decision object 触发。",
        ]
    return unique_strings(criteria)


def derive_evidence_required(feature: dict[str, Any], layers: list[str]) -> list[str]:
    evidence = [
        "analysis 与 strategy 形成过程的 execution evidence",
        "supervisor 对 TESTSET 与 traceability 的 review evidence",
        "candidate package 的 machine-readable gate subject records",
    ]
    profile = feature_profile(feature)
    if "e2e" in layers:
        evidence.append("若进入 e2e 层，需补充 pilot 链路或 UI/integration context 的执行前提证据")
    if profile == "formal":
        evidence += ["formal_ref resolution evidence", "lineage build / lineage_missing evidence", "admission verdict evidence"]
    elif profile == "io":
        evidence += ["receipt_ref", "registry_record_ref", "managed_artifact_ref", "policy_deny / registry_prerequisite_failed / receipt_pending evidence"]
    elif profile == "pilot":
        evidence += ["pilot evidence package", "wave state / cutover_guard_ref evidence", "fallback / rollback evidence"]
    elif profile == "gate":
        evidence += ["decision object evidence", "approve / revise / retry / handoff / reject routing evidence"]
    return unique_strings(evidence)


def derive_analysis_markdown(feature: dict[str, Any], package_json: dict[str, Any], derived_slug: str) -> str:
    source_refs = unique_strings(ensure_list(feature.get("source_refs")) + ensure_list(package_json.get("source_refs")))
    governing = governing_adrs(feature, package_json)
    return "\n\n".join(
        [
            f"# Requirement Analysis for {feature.get('feat_ref')}",
            "## Selected FEAT\n\n"
            + "\n".join(
                [
                    f"- feat_ref: `{feature.get('feat_ref')}`",
                    f"- title: {feature.get('title')}",
                    f"- derived_slug: `{derived_slug}`",
                    f"- epic_ref: `{feature.get('epic_ref') or package_json.get('epic_freeze_ref')}`",
                    f"- src_ref: `{package_json.get('src_root_id')}`",
                    f"- profile: `{feature_profile(feature)}`",
                ]
            ),
            "## Boundary Analysis\n\n"
            + "\n".join([f"- {item}" for item in ensure_list(feature.get("scope"))])
            + "\n\n## Non-Goals\n\n"
            + "\n".join([f"- {item}" for item in ensure_list(feature.get("non_goals")) or ["- 未声明额外 non-goals，按 FEAT 现有边界执行。"]]),
            "## Constraint and Risk Intake\n\n"
            + "\n".join([f"- {item}" for item in derive_risk_focus(feature)]),
            "## Governing References\n\n"
            + "\n".join([f"- {item}" for item in governing] or ["- No explicit ADR refs inherited."])
            + "\n\n## Source Refs\n\n"
            + "\n".join([f"- {item}" for item in source_refs]),
        ]
    )


def derive_strategy_yaml(feature: dict[str, Any], package_json: dict[str, Any]) -> dict[str, Any]:
    layers = derive_test_layers(feature)
    units = derive_test_units(feature)
    return {
        "strategy_id": f"strategy-{slugify(str(feature.get('feat_ref') or 'feat'))}",
        "selected_feat_ref": feature.get("feat_ref"),
        "profile": feature_profile(feature),
        "priority": derive_priority(feature),
        "test_layers": layers,
        "risk_focus": derive_risk_focus(feature),
        "environment_assumptions": derive_environment_assumptions(feature, layers),
        "coverage_exclusions": derive_coverage_exclusions(feature),
        "test_units": units,
        "acceptance_traceability": derive_acceptance_traceability(feature, units),
        "governing_adrs": governing_adrs(feature, package_json),
    }


def build_gate_subjects(run_id: str, feat_ref: str) -> dict[str, dict[str, Any]]:
    return {
        "analysis_review": {
            "subject_id": f"gate-subject-{run_id}-analysis",
            "gate_type": "analysis_review",
            "subject_kind": "gate_subject",
            "workflow_key": "qa.feat-to-testset",
            "workflow_run_id": run_id,
            "feat_ref": feat_ref,
            "artifact_ref": "analysis.md",
            "related_refs": ["test-set.yaml", "test-set-bundle.json"],
        },
        "strategy_review": {
            "subject_id": f"gate-subject-{run_id}-strategy",
            "gate_type": "strategy_review",
            "subject_kind": "gate_subject",
            "workflow_key": "qa.feat-to-testset",
            "workflow_run_id": run_id,
            "feat_ref": feat_ref,
            "artifact_ref": "strategy-draft.yaml",
            "related_refs": ["test-set.yaml", "test-set-bundle.json"],
        },
        "test_set_approval": {
            "subject_id": f"gate-subject-{run_id}-approval",
            "gate_type": "test_set_approval",
            "subject_kind": "gate_subject",
            "workflow_key": "qa.feat-to-testset",
            "workflow_run_id": run_id,
            "feat_ref": feat_ref,
            "artifact_ref": "test-set.yaml",
            "related_refs": [
                "test-set-review-report.json",
                "test-set-acceptance-report.json",
                "test-set-bundle.json",
            ],
        },
    }


def build_test_set_yaml(feature: dict[str, Any], package_json: dict[str, Any]) -> dict[str, Any]:
    feat_ref = str(feature.get("feat_ref") or "")
    layers = derive_test_layers(feature)
    units = derive_test_units(feature)
    return {
        "id": derive_test_set_ref(feat_ref),
        "ssot_type": "TESTSET",
        "workflow_key": "qa.feat-to-testset",
        "template_id": "template.qa.test_set_production",
        "template_workflow_key": "workflow.qa.test_set_production_l3",
        "test_set_id": derive_test_set_id(feat_ref),
        "feat_ref": feat_ref,
        "epic_ref": str(feature.get("epic_ref") or package_json.get("epic_freeze_ref") or ""),
        "src_ref": str(package_json.get("src_root_id") or ""),
        "title": f"{feature.get('title')} Test Set",
        "description": f"{feature.get('title')} governed QA candidate package",
        "derived_slug": slugify(str(feature.get("title") or feat_ref)),
        "coverage_scope": ensure_list(feature.get("scope")),
        "risk_focus": derive_risk_focus(feature),
        "preconditions": derive_preconditions(feature),
        "environment_assumptions": derive_environment_assumptions(feature, layers),
        "test_layers": layers,
        "test_units": units,
        "coverage_exclusions": derive_coverage_exclusions(feature),
        "pass_criteria": derive_pass_criteria(feature),
        "evidence_required": derive_evidence_required(feature, layers),
        "acceptance_traceability": derive_acceptance_traceability(feature, units),
        "source_refs": unique_strings(
            [f"product.epic-to-feat::{package_json.get('workflow_run_id')}", feat_ref]
            + ensure_list(feature.get("source_refs"))
            + ensure_list(package_json.get("source_refs"))
        ),
        "governing_adrs": governing_adrs(feature, package_json),
        "status": "draft",
    }
