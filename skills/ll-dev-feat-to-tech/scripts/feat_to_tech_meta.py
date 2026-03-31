from __future__ import annotations

from typing import Any

from feat_to_tech_common import ensure_list, unique_strings


def selected_feat_snapshot(feature: dict[str, Any], resolved_axis: str) -> dict[str, Any]:
    raw_provisional_refs = feature.get("provisional_refs")
    provisional_refs = raw_provisional_refs if isinstance(raw_provisional_refs, list) else ensure_list(raw_provisional_refs)
    return {
        "feat_ref": str(feature.get("feat_ref") or ""),
        "axis_id": str(feature.get("axis_id") or ""),
        "title": str(feature.get("title") or ""),
        "goal": str(feature.get("goal") or ""),
        "authoritative_artifact": str(feature.get("authoritative_artifact") or ""),
        "upstream_feat": ensure_list(feature.get("upstream_feat")),
        "downstream_feat": ensure_list(feature.get("downstream_feat")),
        "consumes": ensure_list(feature.get("consumes")),
        "produces": ensure_list(feature.get("produces")),
        "scope": ensure_list(feature.get("scope"))[:6],
        "constraints": ensure_list(feature.get("constraints"))[:6],
        "dependencies": ensure_list(feature.get("dependencies"))[:6],
        "outputs": ensure_list(feature.get("outputs"))[:6],
        "acceptance_checks": feature.get("acceptance_checks") or [],
        "source_refs": ensure_list(feature.get("source_refs"))[:8],
        "ui_ref": str(feature.get("ui_ref") or ""),
        "testset_ref": str(feature.get("testset_ref") or ""),
        "provisional_refs": provisional_refs,
        "derived_axis": resolved_axis,
    }


def design_focus(feature: dict[str, Any], resolved_axis: str) -> str:
    axis = resolved_axis.replace("_", " ")
    title = str(feature.get("title") or "").strip()
    return f"Freeze a concrete TECH design for {title or axis}, preserving FEAT semantics while making runtime carriers and contracts implementation-ready."


def api_compatibility_rules(axis: str) -> list[str]:
    rules = [
        "新增 CLI flag 或返回字段必须保持向后兼容；破坏性变化需要新的 design revision。",
        "command stdout/stderr 与 receipt schema 需要版本化，不允许用隐式文本变化替代 schema 变更。",
    ]
    extra = {
        "collaboration": "提交与 pending 可见性命令不得偷带决策语义；`approve / revise / retry / handoff / reject` 只能留在 gate decision FEAT。",
        "formalization": "`ll gate evaluate` 与 `ll gate dispatch` 的 decision vocabulary / dispatch_target 必须共享同一份枚举与 target 语义，不允许把 human decision actions 漂成 runtime states。",
        "layering": "resolve/admission 命令必须始终返回 authoritative formal refs，不允许退化为路径猜测结果。",
        "io_governance": "governed IO 命令不得 silent fallback 到自由读写；兼容模式也必须显式返回 warning/code。",
        "first_ai_advice": "首轮建议契约必须保留 risk gate 与最低输出字段，不允许退化成 generic request/receipt 模式。",
        "extended_profile_completion": "渐进补全契约必须支持 task card + incremental save，不允许把首页可用性和补全保存绑成同一次阻塞事务。",
        "device_deferred_entry": "设备连接契约必须保持 deferred / non-blocking 语义，失败不得撤销首页进入或首轮建议可用性。",
        "state_profile_boundary": "状态与存储边界契约必须显式区分 primary_state、capability_flags 和 canonical profile source，冲突写入必须 fail closed。",
        "minimal_onboarding": "最小建档契约必须保持 `birthdate` 为 canonical 字段、`profile_minimal_done` 为唯一首页放行完成标记，设备连接不能重新变成阻塞前置。",
        "adoption_e2e": "onboarding/cutover 命令必须保留 compat_mode 开关，并把 fallback 结果显式记录到 receipt。",
    }.get(axis)
    if extra:
        rules.append(extra)
    return rules


def traceability_rows(feature: dict[str, Any], run_id: str, refs: dict[str, str]) -> list[dict[str, Any]]:
    source_refs = unique_strings([f"product.epic-to-feat::{run_id}", refs["feat_ref"], refs["epic_ref"], refs["src_ref"]] + ensure_list(feature.get("source_refs")))
    return [
        {"design_section": "Need Assessment", "feat_fields": ["scope", "dependencies", "acceptance_checks"], "source_refs": source_refs[:4]},
        {"design_section": "TECH Design", "feat_fields": ["goal", "scope", "constraints"], "source_refs": source_refs[:4]},
        {"design_section": "Cross-Artifact Consistency", "feat_fields": ["dependencies", "outputs", "acceptance_checks"], "source_refs": source_refs[:4]},
    ]
