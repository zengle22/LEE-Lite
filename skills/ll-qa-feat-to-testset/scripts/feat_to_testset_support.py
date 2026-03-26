#!/usr/bin/env python3
"""Support helpers for feat-to-testset derivation."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, unique_strings

_SUPPORTING_REF_EXTRAS: dict[str, list[str]] = {
    "projection_generation": [
        "Machine SSOT",
        "Human Review Projection",
        "derived_only_marker",
        "projection trace refs",
        "gate review projection",
    ],
    "authoritative_snapshot": [
        "Authoritative Snapshot",
        "completed state",
        "authoritative output",
        "frozen downstream boundary",
        "open technical decisions",
    ],
    "review_focus_risk": [
        "Review Focus",
        "Risks / Ambiguities",
        "risk signal",
        "ambiguity trace",
        "review prompt block",
    ],
    "feedback_writeback": [
        "ProjectionComment",
        "revision request",
        "SSOT writeback",
        "regenerated projection",
        "comment provenance",
    ],
    "formal": ["resolve-formal-ref", "verify-eligibility", "formal_ref", "lineage", "admission verdict"],
    "io": [
        "commit-governed",
        "read-governed",
        "policy_deny",
        "registry_prerequisite_failed",
        "receipt_pending",
        "receipt_ref",
        "registry_record_ref",
        "managed_artifact_ref",
    ],
    "pilot": [
        "OnboardingMatrix",
        "CutoverDirective",
        "PilotEvidenceRef",
        "compat_mode",
        "wave_id",
        "cutover_guard_ref",
        "producer -> gate -> formal -> consumer -> audit",
    ],
    "runner_ready_job": ["ready execution job", "approve-to-job lineage", "artifacts/jobs/ready", "ready queue receipt"],
    "runner_operator_entry": [
        "Execution Loop Job Runner",
        "runner skill entry",
        "ll loop run-execution",
        "runner invocation receipt",
        "runner context ref",
    ],
    "runner_control_surface": [
        "runner CLI control surface",
        "ll job claim",
        "ll job run",
        "ll job complete",
        "ll job fail",
        "runner control action record",
    ],
    "runner_intake": ["ready queue scan", "claimed execution job", "running ownership record", "single-owner claim"],
    "runner_dispatch": ["next-skill invocation", "execution attempt record", "dispatch lineage", "target skill ref"],
    "runner_feedback": ["execution outcome record", "retry-reentry directive", "failure evidence"],
    "runner_observability": [
        "runner observability surface",
        "runner observability snapshot",
        "ready backlog",
        "waiting-human",
        "deadletters",
    ],
    "gate": ["authoritative decision object", "approve / revise / retry / handoff / reject", "formal publication trigger", "decision uniqueness"],
    "collaboration": [
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
    ],
}


def supporting_contract_refs(profile: str, source_refs: list[str]) -> list[str]:
    return unique_strings(list(source_refs) + _SUPPORTING_REF_EXTRAS.get(profile, []))


def derive_environment_assumptions(
    feature: dict[str, Any],
    layers: list[str],
    profile: str,
    downstream_target: str,
) -> list[str]:
    assumptions = [
        "需要可解析 selected FEAT 所依赖的集成环境与上游 artifact lineage。",
        "需要能读取并追踪 FEAT、EPIC、SRC 与 governing ADR 引用。",
        "需要保留 execution evidence 与 supervision evidence 所要求的最小审计链。",
    ]
    if "e2e" in layers:
        assumptions.append(
            "若启用 e2e 层且目标为 Web sibling，必须具备可重复执行的浏览器 UI 上下文。"
            if downstream_target == "skill.qa.test_exec_web_e2e"
            else "若启用 e2e 层且目标为 CLI sibling，必须具备可重复执行的 CLI 或跨服务集成上下文。"
        )
    if ensure_list(feature.get("dependencies")):
        assumptions.append("依赖服务或上游能力应以可观测、可判定的方式处于可用状态。")

    extras: dict[str, list[str]] = {
        "projection_generation": [
            "Machine SSOT 冻结字段必须可解析，Projection template version 必须稳定可用。",
            "Projection 输出必须保留 derived-only / non-authoritative marker 与 trace refs。",
        ],
        "authoritative_snapshot": [
            "completed state、authoritative output、frozen boundary、open technical decisions 必须能从 SSOT 中解析。",
            "Snapshot traceability 必须可回链到对应 SSOT 字段。",
        ],
        "review_focus_risk": [
            "review focus / risk extraction 依赖的 SSOT 与 projection context 必须可解析。",
            "risk signal 必须 traceable，否则应被丢弃而不是写入 projection。",
        ],
        "feedback_writeback": [
            "Projection comment、SSOT field mapping 与 revision request 流必须可追踪。",
            "Projection regeneration 必须发生在 SSOT authoritative update 之后。",
        ],
        "formal": [
            "formal publication、formal ref 与 lineage 解析链必须可被重复验证。",
            "admission checker 必须能在缺少 lineage 或 formal ref 时 fail closed。",
        ],
        "io": [
            "Gateway / Path Policy / Registry 必须在同一受治理链路中返回稳定 verdict。",
            "receipt_ref、registry_record_ref 与 managed_artifact_ref 解析上下文必须可观测。",
        ],
        "pilot": [
            "真实 pilot chain 需要 producer、gate、formal、consumer、audit 五段至少一条完整连通。",
            "wave state、compat_mode 与 cutover_guard_ref 必须可追溯且可回放。",
        ],
        "runner_ready_job": [
            "approve decision 与 next skill target 必须可解析为唯一 ready execution job。",
            "artifacts/jobs/ready 写入与 approve-to-job lineage 需要可重复验证。",
        ],
        "runner_operator_entry": [
            "Claude/Codex CLI 可调用 runner skill entry，且 run context 可启动或恢复。",
            "entry receipt 与 runner_run_ref 必须可回链到同一条 authoritative runner trace.",
        ],
        "runner_control_surface": [
            "runner lifecycle commands 与 ownership guard 必须在同一条 authoritative control plane 上可观测。",
            "control action record 不得与 dispatch / outcome 结果混层。",
        ],
        "runner_intake": [
            "ready queue scan 与 single-owner claim 需要可重复执行且可判定冲突。",
            "running ownership record 必须对后续 dispatch 可见。",
        ],
        "runner_dispatch": [
            "target skill ref 与 authoritative input 必须能从 claimed job 唯一解析。",
            "next-skill invocation 与 execution attempt 必须保留 lineage。",
        ],
        "runner_feedback": [
            "execution outcome、retry-reentry 与 failure evidence 必须能绑定到同一个 execution attempt。",
            "feedback 结果必须保持 authoritative，可被 orchestration 与 monitor 消费。",
        ],
        "runner_observability": [
            "ready backlog、running、failed、deadletters、waiting-human 状态必须来自 authoritative runner records。",
            "observability snapshot 必须可追溯到 queue、ownership 与 outcome source。",
        ],
        "gate": [
            "candidate -> gate decision -> formal trigger 的业务链路必须只有一条 authoritative path。",
            "decision object 的唯一性与回流目标必须可观测。",
        ],
    }
    return unique_strings(assumptions + extras.get(profile, []))


def derive_coverage_exclusions(feature: dict[str, Any]) -> list[str]:
    exclusions = ensure_list(feature.get("non_goals"))[:3]
    if not exclusions:
        exclusions = [
            "不覆盖 selected FEAT 之外的相邻 FEAT 语义。",
            "不把本 TESTSET 扩展为 TASK、TECH 或 runner-level 实现细节。",
        ]
    return exclusions


def derive_risk_focus(feature: dict[str, Any], profile: str) -> list[str]:
    risks = ["要求 every test unit 都能回链到 FEAT acceptance、governing ADR 与 expected downstream evidence。"]
    extras: dict[str, list[str]] = {
        "projection_generation": ["derived-only marker 丢失", "projection 与 Machine SSOT authoritative fields 不一致"],
        "authoritative_snapshot": ["snapshot 混入非 authoritative 字段", "open technical decisions 丢失"],
        "review_focus_risk": ["risk / ambiguity 信号不可追溯", "review focus block 生成噪声结论"],
        "feedback_writeback": ["projection comment 不能回写到 SSOT", "writeback 破坏 projection / SSOT 分层"],
        "formal": ["formal ref / lineage 缺失导致 downstream admission 漂移", "跨层消费未 fail closed"],
        "io": ["绕过 Path Policy 或 Gateway 产生自由写入", "receipt / registry record 不可追溯"],
        "pilot": ["pilot evidence 不完整却继续 rollout", "compat_mode / wave state / fallback trace 漂移"],
        "runner_ready_job": ["approve 被错误改写成 formal publication", "ready job / lineage 不一致"],
        "runner_operator_entry": ["runner 入口隐藏在后台自动化中不可见", "resume 丢失 authoritative run context"],
        "runner_control_surface": ["control verbs 分散且无统一治理", "control plane 越权改写业务结果"],
        "runner_intake": ["single-owner claim 失效", "job_not_ready / already_claimed 不可追溯"],
        "runner_dispatch": ["target skill / authoritative input 解析漂移", "dispatch 退化成 manual relay"],
        "runner_feedback": ["outcome 缺失或多写", "failure evidence 与 retry-reentry 漂移"],
        "runner_observability": ["监控面靠目录猜状态", "waiting-human / deadletter 状态不可见"],
        "gate": ["decision object 不唯一", "formal trigger 与 revise/retry 流混层"],
        "collaboration": ["queue / handoff / re-entry contract 漂移", "duplicate_submission 不可判定或被错误覆盖"],
    }
    return unique_strings(risks + extras.get(profile, []))
