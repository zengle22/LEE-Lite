#!/usr/bin/env python3
"""Support helpers for feat-to-testset derivation."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, unique_strings


def supporting_contract_refs(profile: str, source_refs: list[str]) -> list[str]:
    refs = list(source_refs)
    if profile == "projection_generation":
        refs += [
            "Machine SSOT",
            "Human Review Projection",
            "derived_only_marker",
            "projection trace refs",
            "gate review projection",
        ]
    elif profile == "authoritative_snapshot":
        refs += [
            "Authoritative Snapshot",
            "completed state",
            "authoritative output",
            "frozen downstream boundary",
            "open technical decisions",
        ]
    elif profile == "review_focus_risk":
        refs += [
            "Review Focus",
            "Risks / Ambiguities",
            "risk signal",
            "ambiguity trace",
            "review prompt block",
        ]
    elif profile == "feedback_writeback":
        refs += [
            "ProjectionComment",
            "revision request",
            "SSOT writeback",
            "regenerated projection",
            "comment provenance",
        ]
    elif profile == "formal":
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
        if downstream_target == "skill.qa.test_exec_web_e2e":
            assumptions.append("若启用 e2e 层且目标为 Web sibling，必须具备可重复执行的浏览器 UI 上下文。")
        else:
            assumptions.append("若启用 e2e 层且目标为 CLI sibling，必须具备可重复执行的 CLI 或跨服务集成上下文。")
    if ensure_list(feature.get("dependencies")):
        assumptions.append("依赖服务或上游能力应以可观测、可判定的方式处于可用状态。")
    if profile == "projection_generation":
        assumptions += [
            "Machine SSOT 冻结字段必须可解析，Projection template version 必须稳定可用。",
            "Projection 输出必须保留 derived-only / non-authoritative marker 与 trace refs。",
        ]
    elif profile == "authoritative_snapshot":
        assumptions += [
            "completed state、authoritative output、frozen boundary、open technical decisions 必须能从 SSOT 中解析。",
            "Snapshot traceability 必须可回链到对应 SSOT 字段。",
        ]
    elif profile == "review_focus_risk":
        assumptions += [
            "review focus / risk extraction 依赖的 SSOT 与 projection context 必须可解析。",
            "risk signal 必须 traceable，否则应被丢弃而不是写入 projection。",
        ]
    elif profile == "feedback_writeback":
        assumptions += [
            "Projection comment、SSOT field mapping 与 revision request 流必须可追踪。",
            "Projection regeneration 必须发生在 SSOT authoritative update 之后。",
        ]
    elif profile == "formal":
        assumptions += [
            "formal publication、formal ref 与 lineage 解析链必须可被重复验证。",
            "admission checker 必须能在缺少 lineage 或 formal ref 时 fail closed。",
        ]
    elif profile == "io":
        assumptions += [
            "Gateway / Path Policy / Registry 必须在同一受治理链路中返回稳定 verdict。",
            "receipt_ref、registry_record_ref 与 managed_artifact_ref 解析上下文必须可观测。",
        ]
    elif profile == "pilot":
        assumptions += [
            "真实 pilot chain 需要 producer、gate、formal、consumer、audit 五段至少一条完整连通。",
            "wave state、compat_mode 与 cutover_guard_ref 必须可追溯且可回放。",
        ]
    elif profile == "gate":
        assumptions += [
            "candidate -> gate decision -> formal trigger 的业务链路必须只有一条 authoritative path。",
            "decision object 的唯一性与回流目标必须可观测。",
        ]
    return unique_strings(assumptions)


def derive_coverage_exclusions(feature: dict[str, Any]) -> list[str]:
    exclusions = ensure_list(feature.get("non_goals"))[:3]
    if not exclusions:
        exclusions = [
            "不覆盖 selected FEAT 之外的相邻 FEAT 语义。",
            "不把本 TESTSET 扩展为 TASK、TECH 或 runner-level 实现细节。",
        ]
    return exclusions


def derive_risk_focus(feature: dict[str, Any], profile: str) -> list[str]:
    risks = [
        "要求 every test unit 都能回链到 FEAT acceptance、governing ADR 与 expected downstream evidence。",
    ]
    if profile == "projection_generation":
        risks += ["derived-only marker 丢失", "projection 与 Machine SSOT authoritative fields 不一致"]
    elif profile == "authoritative_snapshot":
        risks += ["snapshot 混入非 authoritative 字段", "open technical decisions 丢失"]
    elif profile == "review_focus_risk":
        risks += ["risk / ambiguity 信号不可追溯", "review focus block 生成噪声结论"]
    elif profile == "feedback_writeback":
        risks += ["projection comment 不能回写到 SSOT", "writeback 破坏 projection / SSOT 分层"]
    elif profile == "formal":
        risks += ["formal ref / lineage 缺失导致 downstream admission 漂移", "跨层消费未 fail closed"]
    elif profile == "io":
        risks += ["绕过 Path Policy 或 Gateway 产生自由写入", "receipt / registry record 不可追溯"]
    elif profile == "pilot":
        risks += ["pilot evidence 不完整却继续 rollout", "compat_mode / wave state / fallback trace 漂移"]
    elif profile == "gate":
        risks += ["decision object 不唯一", "formal trigger 与 revise/retry 流混层"]
    elif profile == "collaboration":
        risks += ["queue / handoff / re-entry contract 漂移", "duplicate_submission 不可判定或被错误覆盖"]
    return unique_strings(risks)
