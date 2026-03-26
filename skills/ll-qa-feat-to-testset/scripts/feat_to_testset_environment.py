#!/usr/bin/env python3
"""Environment-input derivation helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, unique_strings


def _cli_or_web_context(downstream_target: str) -> str:
    if downstream_target == "skill.qa.test_exec_web_e2e":
        return "驱动 FEAT acceptance checks 的页面路径、locator 或浏览器执行上下文"
    return "驱动 FEAT acceptance checks 的 CLI 命令、接口调用或 integration context"


def derive_required_environment_inputs(
    feature: dict[str, Any],
    layers: list[str],
    profile: str,
    downstream_target: str,
) -> dict[str, list[str]]:
    scope_text = " ".join(ensure_list(feature.get("scope"))).lower()
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
            ["selected FEAT 所依赖的集成服务或协作 consumer"]
            + (
                ["跨 skill pilot 链路涉及的 producer / consumer / gate consumer"]
                if "pilot" in scope_text or "cross skill" in scope_text
                else []
            )
        ),
        "access": [
            "读取 FEAT candidate / freeze lineage 所需权限",
            "执行 QA evidence 采集与落盘所需权限",
        ],
        "feature_flags": ["selected FEAT 涉及的 gated rollout、cutover 或 guarded branch 开关"],
        "ui_or_integration_context": [_cli_or_web_context(downstream_target)],
    }

    if profile == "projection_generation":
        payload["data"] += ["freeze-ready Machine SSOT fixture", "projection template / derived-only marker fixture"]
        payload["services"] += ["projection template resolver", "projection renderer"]
        payload["access"] += [
            "读取 Machine SSOT authoritative fields 与写出 projection artifact 的权限",
            "projection renderer service identity 或等价账号材料",
        ]
        payload["feature_flags"] += ["projection template version / projection publish guard 开关"]
        payload["ui_or_integration_context"] += ["gate review surface projection 渲染或消费上下文"]
    elif profile == "authoritative_snapshot":
        payload["data"] += ["authoritative field fixture", "Snapshot 缺字段失败样本"]
        payload["services"] += ["authoritative snapshot extractor"]
        payload["access"] += [
            "读取 completed state / authoritative output / frozen boundary / open technical decisions 的权限",
            "snapshot extractor identity 或等价 credential material",
        ]
        payload["feature_flags"] += ["snapshot render guard / trace bind strict mode"]
        payload["ui_or_integration_context"] += ["projection 内 authoritative snapshot 区块上下文"]
    elif profile == "review_focus_risk":
        payload["data"] += [
            "Machine SSOT context fixture",
            "review focus fixture",
            "risk / ambiguity signal 样本",
            "insufficient_context / untraceable_signal 失败样本",
            "SSOT authoritative source fixture",
        ]
        payload["services"] += ["review focus extractor", "risk / ambiguity analyzer"]
        payload["access"] += [
            "读取 projection context 与写入 review focus / risk block 的权限",
            "risk analyzer identity 或等价 credential material",
        ]
        payload["feature_flags"] += ["risk block enablement / traceability strict mode"]
        payload["ui_or_integration_context"] += ["projection review focus / risks 区块上下文"]
    elif profile == "feedback_writeback":
        payload["data"] += ["projection comment fixture", "comment-to-SSOT mapping 样本", "mapping_failed / regeneration_pending 失败样本"]
        payload["services"] += ["comment mapper", "revision request builder", "projection regeneration trigger"]
        payload["access"] += [
            "提交 projection comment、创建 revision request、触发 projection regeneration 的权限",
            "writeback mapper / SSOT updater credential 或等价账号材料",
        ]
        payload["feature_flags"] += ["projection writeback enablement / direct-patch forbid guard"]
        payload["ui_or_integration_context"] += ["review comment -> SSOT writeback -> projection regeneration 上下文"]
    elif profile == "formal":
        payload["data"] += ["approved decision object、formal_ref、lineage fixture", "lineage_missing 与 layer_violation 失败样本"]
        payload["services"] += ["formal publication publisher", "registry formal-ref resolution / admission checker"]
        payload["access"] += [
            "读取 formal publication package、formal ref、admission verdict 的权限",
            "formal publisher service account、admission API token 或等价 credential material",
        ]
        payload["feature_flags"] += ["formal publication guarded-only enablement / admission strict mode"]
        payload["ui_or_integration_context"] += ["formal publication / formal-ref consumption integration context"]
    elif profile == "io":
        payload["data"] += ["authoritative handoff submission", "pending_state", "receipt_ref / registry_record_ref / managed_artifact_ref fixture"]
        payload["services"] += ["gateway / path policy verdict emitter", "registry writer / managed receipt builder"]
        payload["access"] += [
            "handoff service identity、gateway service account 或等价账号材料",
            "registry token / receipt writer credential",
        ]
        payload["feature_flags"] += ["policy deny strict mode / registry preflight guard"]
        payload["ui_or_integration_context"] += ["受治理 IO receipt / registry / verdict integration context"]
    elif profile == "pilot":
        payload["data"] += ["pilot evidence package", "wave state fixture", "fallback / rollback 失败样本"]
        payload["services"] += ["pilot chain verifier", "wave state writer", "audit evidence aggregator"]
        payload["access"] += [
            "pilot verifier credential / audit token / rollout service account",
            "读取与写回 wave state、cutover_guard_ref、fallback receipt 的权限",
        ]
        payload["feature_flags"] += ["pilot enablement / guarded rollout / compat mode switch"]
        payload["ui_or_integration_context"] += ["producer -> gate -> formal -> consumer -> audit pilot chain context"]
    elif profile == "gate":
        payload["data"] += ["authoritative decision object fixture", "approve/revise/retry/handoff/reject 样本", "decision conflict / bypass 失败样本"]
        payload["services"] += ["gate evaluator", "decision object writer", "formal publication trigger consumer"]
        payload["access"] += [
            "gate evaluator service account、decision token 或等价 credential material",
            "读取 candidate / decision object / formal trigger state 的权限",
        ]
        payload["feature_flags"] += ["guarded decision path / formal trigger gate"]
        payload["ui_or_integration_context"] += ["gate decision object / formal trigger integration context"]
    elif profile == "collaboration":
        payload["data"] += [
            "authoritative handoff submission",
            "pending_state / gate_pending_ref / assigned_gate_queue fixture",
            "duplicate payload replay / mismatch failure samples",
        ]
        payload["services"] += ["handoff runtime", "pending visibility reader", "runtime re-entry writer"]
        payload["access"] += [
            "handoff service identity 或等价账号材料",
            "读取 trace_ref、canonical_payload_path、reentry_directive 的权限",
        ]
        payload["feature_flags"] += ["idempotent replay guard / decision return routing guard"]
        payload["ui_or_integration_context"] += ["authoritative handoff / pending visibility integration context"]
    return payload
