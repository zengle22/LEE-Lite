#!/usr/bin/env python3
"""Revision-request helpers for raw-to-src."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.workflow_revision import materialize_revision_request, normalize_revision_context


def _append_unique(items: list[str], additions: list[str]) -> list[str]:
    seen = {str(item).strip() for item in items if str(item).strip()}
    merged = list(items)
    for item in additions:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        merged.append(text)
    return merged


def persist_revision_request(revision_request_path: Path | None, repo_root: Path, artifacts_dir: Path) -> str:
    revision_request_ref, _, _ = materialize_revision_request(
        artifacts_dir,
        revision_request_path=revision_request_path,
        load_json=lambda path: json.loads(path.read_text(encoding="utf-8")),
        dump_json=lambda path, payload: path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"),
    )
    if not revision_request_ref:
        return ""
    return Path(revision_request_ref).resolve().relative_to(repo_root.resolve()).as_posix()


def load_revision_request(artifacts_dir: Path, revision_request_path: Path | None = None) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if revision_request_path:
        materialize_revision_request(
            artifacts_dir,
            revision_request_path=revision_request_path,
            load_json=lambda path: json.loads(path.read_text(encoding="utf-8")),
            dump_json=lambda path, payload: path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"),
            delete_if_missing=False,
        )
    revision_request_path = artifacts_dir / "revision-request.json"
    if not revision_request_path.exists():
        return "", {}, {}
    revision_request = json.loads(revision_request_path.read_text(encoding="utf-8"))
    revision_request_ref = str(revision_request_path)
    revision_context = normalize_revision_context(
        revision_request,
        revision_request_ref=revision_request_ref,
        ensure_list=lambda values: [str(item).strip() for item in (values or []) if str(item).strip()],
    )
    return revision_request_ref, revision_request, revision_context


def apply_revision_request(
    candidate: dict[str, Any],
    revision_request: dict[str, Any],
    *,
    revision_request_ref: str,
    revision_context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    working = json.loads(json.dumps(candidate, ensure_ascii=False))
    applied: list[dict[str, Any]] = []
    context = revision_context or normalize_revision_context(
        revision_request,
        revision_request_ref=revision_request_ref,
        ensure_list=lambda values: [str(item).strip() for item in (values or []) if str(item).strip()],
    )
    decision_reason = str(context.get("decision_reason") or "").strip()
    if not decision_reason:
        return working, applied

    lower_reason = decision_reason.lower()
    revision_summary = str(context.get("summary") or "").strip()
    key_constraints = list(working.get("key_constraints", []))
    business_drivers = list(working.get("business_drivers", []))
    in_scope = list(working.get("in_scope", []))
    source_refs = list(working.get("source_refs", []))
    semantic_inventory = working.setdefault("semantic_inventory", {})
    semantic_constraints = list(semantic_inventory.get("constraints", []))

    source_ref_updates = [revision_request_ref, str(context.get("source_gate_decision_ref") or "").strip()]
    updated_source_refs = _append_unique(source_refs, source_ref_updates)
    if updated_source_refs != source_refs:
        working["source_refs"] = updated_source_refs
        applied.append(
            {
                "code": "revision_source_refs",
                "action": "Appended gate revision references into source_refs for traceability.",
                "target_fields": ["source_refs"],
            }
        )

    if any(token in lower_reason for token in ("running_level", "starter", "can_run_5k", "race_finisher", "训练基础轴")):
        additions = [
            "最小分层字段 `running_level` 必须收敛为单一训练基础轴，不得混合训练阶段、当前能力与历史赛事经历三种口径。",
            "正式比赛经历不属于最小建档必填项，应下沉到扩展画像中补充。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_running_level_axis",
                    "action": "Normalized running_level constraints into a single training-base axis.",
                    "target_fields": ["key_constraints", "semantic_inventory.constraints"],
                }
            )
            key_constraints = updated_constraints
            semantic_constraints = updated_semantic_constraints

    if any(token in lower_reason for token in ("recent_injury_status", "伤病", "疼痛", "无伤优先")):
        additions = [
            "最小建档必填字段至少包括 `gender / birthday / height_cm / weight_kg / running_level / recent_injury_status`，用于支撑首轮建议的安全门槛。",
            "AI 首轮建议必须以“无伤优先”为前置约束；若存在明显疼痛或恢复中状态，不得直接进入强度课建议。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_drivers = _append_unique(business_drivers, ["首轮建议必须先拿到最小风险输入，再决定训练强度与恢复建议。"])
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_drivers != business_drivers or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            working["business_drivers"] = updated_drivers
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_minimal_risk_input",
                    "action": "Added recent_injury_status and injury-first recommendation guardrails into the SRC constraints.",
                    "target_fields": ["key_constraints", "business_drivers", "semantic_inventory.constraints"],
                }
            )
            key_constraints = updated_constraints
            business_drivers = updated_drivers
            semantic_constraints = updated_semantic_constraints

    if any(token in lower_reason for token in ("extended_profile_completed", "device_connected", "initial_plan_ready", "组合化", "capability flags")):
        additions = [
            "状态模型应区分主阶段状态与独立 capability flags；`extended_profile_completed`、`device_connected`、`initial_plan_ready` 不得被建模为严格串行阶段。",
            "设备连接、扩展画像补全与初始计划准备应允许独立完成，避免把非阻塞能力错误建模成单线状态流。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_state_capabilities",
                    "action": "Reframed state semantics into stage state plus independent capability flags.",
                    "target_fields": ["key_constraints", "semantic_inventory.constraints"],
                }
            )
            key_constraints = updated_constraints
            semantic_constraints = updated_semantic_constraints

    hard_constraint_markers = ("一个提交动作", "首页任务卡", "增量更新", "最低输出目标", "第一周行动建议", "连接设备")
    if any(marker in decision_reason for marker in hard_constraint_markers):
        additions = [
            "最小建档页不得拆成多页向导；用户填写后应一次提交并直接进入首页。",
            "首页任务卡只用于增强，不得阻塞首次 AI 可用体验。",
            "扩展画像应支持增量更新，不要求用户一次性完成全量补充。",
            "AI 首轮建议至少应包含当前训练建议级别、第一周行动建议、是否提示补充更多信息、是否提示连接设备。",
        ]
        updated_constraints = _append_unique(key_constraints, additions)
        updated_scope = _append_unique(in_scope, ["定义最小建档单次提交边界、首页任务卡非阻塞边界，以及首轮建议的最低输出要求。"])
        updated_semantic_constraints = _append_unique(semantic_constraints, additions)
        if updated_constraints != key_constraints or updated_scope != in_scope or updated_semantic_constraints != semantic_constraints:
            working["key_constraints"] = updated_constraints
            working["in_scope"] = updated_scope
            semantic_inventory["constraints"] = updated_semantic_constraints
            applied.append(
                {
                    "code": "revision_non_blocking_onboarding",
                    "action": "Added non-blocking onboarding and minimum first-recommendation constraints from the gate revise request.",
                    "target_fields": ["key_constraints", "in_scope", "semantic_inventory.constraints"],
                }
            )

    if revision_summary:
        working["revision_context"] = context
        working["revision_request_ref"] = revision_request_ref
        working["revision_summary"] = revision_summary
    return working, applied
