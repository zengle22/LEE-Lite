#!/usr/bin/env python3
"""Derivation helpers for the lite-native src-to-epic runtime."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src_to_epic_common import ensure_list, guess_repo_root_from_input, normalize_semantic_lock, shorten_identifier, unique_strings


ROLLOUT_KEYWORD_GROUPS = {
    "shared_runtime_or_governance_change": ["governance", "gateway", "registry", "audit", "external gate", "path policy", "formal materialization", "主链", "统一治理", "受管"],
    "requires_existing_skill_migration": ["skill", "workflow", "consumer", "producer", "迁移", "接入", "rollout", "adoption", "onboarding"],
    "effectiveness_depends_on_real_skill_integration": ["managed read", "formal reference", "handoff", "dispatch", "不得重新发明等价规则", "统一继承", "旁路", "consumer"],
    "requires_cross_skill_e2e_validation": ["e2e", "cross-skill", "human gate", "repair", "follow-up", "dispatch", "handoff", "downstream", "上下游"],
}


NUMERIC_SRC_REF_RE = re.compile(r"^SRC-\d+$", re.IGNORECASE)


def _canonical_to_repo(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _resolve_materialized_src_root_id(package: Any) -> str:
    artifacts_dir = getattr(package, "artifacts_dir", None)
    if not isinstance(artifacts_dir, Path) or not artifacts_dir.exists():
        return ""
    repo_root = guess_repo_root_from_input(artifacts_dir.resolve())
    registry_dir = repo_root / "artifacts" / "registry"
    if not registry_dir.exists():
        return ""
    source_package_ref = _canonical_to_repo(artifacts_dir, repo_root)
    for record_path in registry_dir.glob("formal-src-*.json"):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        metadata = record.get("metadata") or {}
        if not isinstance(metadata, dict):
            continue
        assigned_id = str(metadata.get("assigned_id") or "").strip().upper()
        if not NUMERIC_SRC_REF_RE.fullmatch(assigned_id):
            continue
        candidate_package_ref = str(metadata.get("candidate_package_ref") or "").strip()
        source_package_metadata_ref = str(metadata.get("source_package_ref") or "").strip()
        if source_package_ref in {candidate_package_ref, source_package_metadata_ref}:
            return assigned_id
    return ""


def choose_src_root_id(package: Any) -> str:
    existing = package.src_candidate.get("src_root_id")
    existing_value = str(existing or "").strip().upper()
    if NUMERIC_SRC_REF_RE.fullmatch(existing_value):
        return existing_value
    for ref in ensure_list(package.src_candidate.get("source_refs")):
        normalized = str(ref).strip().upper()
        if NUMERIC_SRC_REF_RE.fullmatch(normalized):
            return normalized
    resolved_formal_id = _resolve_materialized_src_root_id(package)
    if resolved_formal_id:
        return resolved_formal_id
    if existing_value:
        return existing_value
    return f"SRC-{shorten_identifier(package.run_id, limit=64)}"


def semantic_lock(package: Any) -> dict[str, Any]:
    return normalize_semantic_lock(package.src_candidate.get("semantic_lock")) or {}


def is_review_projection_package(package: Any) -> bool:
    return str(semantic_lock(package).get("domain_type") or "").strip().lower() == "review_projection_rule"


def is_execution_runner_package(package: Any) -> bool:
    return str(semantic_lock(package).get("domain_type") or "").strip().lower() == "execution_runner_rule"


def is_governance_bridge_package(package: Any) -> bool:
    if is_review_projection_package(package) or is_execution_runner_package(package):
        return False
    source_kind = str(package.src_candidate.get("source_kind") or "")
    title = str(package.src_candidate.get("title") or "")
    constraints_text = " ".join(ensure_list(package.src_candidate.get("key_constraints")))
    return source_kind == "governance_bridge_src" or any(marker in f"{title} {constraints_text}" for marker in ["gate", "handoff", "formal", "双会话双队列", "文件化"])


def uses_adr005_prerequisite(package: Any) -> bool:
    refs = {item.upper() for item in ensure_list(package.src_candidate.get("source_refs"))}
    bridge = package.src_candidate.get("bridge_context") or {}
    bridge_text = " ".join(ensure_list(bridge.get("governance_objects")) + ensure_list(package.src_candidate.get("in_scope")))
    return is_governance_bridge_package(package) and (
        "ADR-005" in refs or ({"ADR-001", "ADR-003", "ADR-006"}.issubset(refs) and any(token in bridge_text for token in ["路径", "IO", "artifact", "目录"]))
    )


def prerequisite_foundations(package: Any) -> list[str]:
    if not uses_adr005_prerequisite(package):
        return []
    return [
        "ADR-005 作为主链文件 IO / 路径治理前置基础，要求在本 EPIC 启动前已交付或已可稳定复用。",
        "本 EPIC 只消费 ADR-005 提供的 Gateway / Path Policy / Registry 能力，不在本 EPIC 内重新实现这些模块。",
    ]


def epic_source_refs(package: Any, src_root_id: str, architecture_refs: list[str]) -> list[str]:
    base = [f"product.raw-to-src::{package.run_id}", src_root_id] + ensure_list(package.src_candidate.get("source_refs")) + architecture_refs
    return unique_strings(base + (["ADR-005"] if uses_adr005_prerequisite(package) else []))


def operator_surface_inventory(package: Any) -> list[dict[str, Any]]:
    raw = package.src_candidate.get("operator_surface_inventory")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def operator_surface_names(package: Any, entry_kind: str) -> list[str]:
    names: list[str] = []
    for item in operator_surface_inventory(package):
        if str(item.get("entry_kind") or "").strip() != entry_kind:
            continue
        name = str(item.get("name") or "").strip()
        if name:
            names.append(name)
    return unique_strings(names)


def derive_capability_axes(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, str]]:
    if is_review_projection_package(package):
        return review_projection_axes()
    if is_execution_runner_package(package):
        return execution_runner_axes(package)
    if is_governance_bridge_package(package):
        return governance_bridge_axes(package, rollout_requirement)
    return default_capability_axes(package)


def review_projection_axes() -> list[dict[str, str]]:
    return [
        {"id": "projection-generation", "name": "Gate Projection 生成能力", "scope": "在 gate 审核阶段，把机器优先 SSOT 渲染成人类友好的 Human Review Projection，并保持与 SSOT 的单向派生关系。", "feat_axis": "Human Review Projection 生成流"},
        {"id": "authoritative-snapshot", "name": "Authoritative Snapshot 摘要能力", "scope": "从 SSOT 提炼 completed state、authoritative output、frozen downstream boundary、open technical decisions，供人类快速校验权威约束。", "feat_axis": "Authoritative Snapshot 生成流"},
        {"id": "review-focus-risk", "name": "Review Focus 与风险提示能力", "scope": "从 SSOT 提取 review focus、risks、ambiguities，帮助审核人快速发现产品边界遗漏、歧义和责任下沉问题。", "feat_axis": "Review Focus 与风险提示流"},
        {"id": "feedback-writeback", "name": "Projection 批注回写能力", "scope": "把 gate 审核意见稳定回写到 Machine SSOT，并确保 Projection 只能重生成，不能变成新的真相源。", "feat_axis": "Projection 批注回写流"},
    ]


def execution_runner_axes(package: Any) -> list[dict[str, str]]:
    axes = [{"id": "ready-job-emission", "name": "批准后 Ready Job 生成能力", "scope": "把 gate approve 稳定映射成 ready execution job，而不是停在 formal publication 或人工接力。", "feat_axis": "approve 后 ready job 生成流"}]
    if operator_surface_names(package, "skill_entry"):
        axes.append({"id": "runner-operator-entry", "name": "Runner 用户入口能力", "scope": "把 Execution Loop Job Runner 冻结成用户可显式调用的独立 skill 入口，而不是隐藏在抽象后台流程里。", "feat_axis": "runner 用户入口流"})
    if operator_surface_names(package, "cli_control_surface"):
        axes.append({"id": "runner-control-surface", "name": "Runner 控制面能力", "scope": "定义 Claude/Codex CLI 如何启动、恢复、驱动 runner 与 job lifecycle，而不是依赖目录猜测或口头操作。", "feat_axis": "runner CLI 控制流"})
    axes.extend([
        {"id": "execution-runner-intake", "name": "Execution Runner 取件能力", "scope": "让 Execution Loop Job Runner 自动消费 artifacts/jobs/ready 中的 job，并形成唯一 claim / running 责任边界。", "feat_axis": "ready job 自动取件流"},
        {"id": "next-skill-dispatch", "name": "下游 Skill 自动派发能力", "scope": "把 claimed job 稳定推进到下一个 governed skill，并保留 authoritative refs、目标 skill 和输入边界。", "feat_axis": "next skill 自动派发流"},
        {"id": "execution-result-feedback", "name": "执行结果回写与重试边界能力", "scope": "把执行结果、重试回流与失败终止冻结成可审计的 runner 输出，而不是把 approve 当作终态。", "feat_axis": "执行结果回写流"},
    ])
    if operator_surface_names(package, "monitor_surface"):
        axes.append({"id": "runner-observability-surface", "name": "Runner 监控与观察能力", "scope": "定义用户如何查看 ready backlog、running、failed、deadletters 与 waiting-human 等运行态，而不是把监控面留成隐含实现细节。", "feat_axis": "runner 运行监控流"})
    return axes


def governance_bridge_axes(package: Any, rollout_requirement: dict[str, Any] | None = None) -> list[dict[str, str]]:
    axes = [
        {"id": "collaboration-loop", "name": "主链协作闭环能力", "scope": "定义 execution loop、gate loop、human loop 在 governed skill 主链中的协作责任、交接界面与回流边界，使不同 FEAT 不再各自重写等价 loop 规则。", "feat_axis": "主链候选交接提交流"},
        {"id": "handoff-formalization", "name": "正式交接与物化能力", "scope": "统一 handoff、gate decision、formal materialization 的正式推进链路，使 candidate 到 formal 的升级路径可以被下游稳定继承。", "feat_axis": "主链 gate 审核与裁决流"},
        {"id": "object-layering", "name": "对象分层与准入能力", "scope": "固定 candidate package、formal object 与 downstream consumption 的层级规则、准入条件和引用约束，防止业务 skill 再次混入裁决职责。", "feat_axis": "formal 物化与下游准入流"},
        {"id": "artifact-io-governance", "name": "主链文件 IO 与路径治理能力", "scope": "定义主链如何接入 ADR-005 已提供的文件 IO / 路径治理能力，约束交接对象的 IO 入口、出口、物化落点与引用稳定性，只覆盖 handoff、formal materialization 与 governed skill IO，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。" if uses_adr005_prerequisite(package) else "约束主链交接对象的 IO 入口、出口、物化落点与引用稳定性，只覆盖 handoff、formal materialization 与 governed skill IO，不覆盖业务代码目录治理、全仓通用文件系统策略或非 governed skill 的任意运行时写入。", "feat_axis": "主链受治理 IO 落盘流"},
    ]
    if rollout_requirement and rollout_requirement.get("required"):
        axes.append({"id": "skill-adoption-e2e", "name": "技能接入与跨 skill 闭环验证能力", "scope": "定义现有 governed skill 的 onboarding、迁移切换与跨 skill E2E 验证边界，使治理主链的成立不依赖口头假设、组件内自测或一次性全仓切换。", "feat_axis": "governed skill 接入与 pilot 闭环流"})
    return axes


def default_capability_axes(package: Any) -> list[dict[str, str]]:
    in_scope = ensure_list(package.src_candidate.get("in_scope"))
    title = str(package.src_candidate.get("title") or package.run_id)
    axes: list[dict[str, str]] = []
    for index, item in enumerate(in_scope[:4], start=1):
        axes.append({"id": f"axis-{index}", "name": f"{title} 能力包 {index}", "scope": item, "feat_axis": item})
    if not axes:
        axes.append({"id": "axis-1", "name": f"{title} 核心能力包", "scope": "围绕上游问题空间形成一个可继续拆分的能力边界。", "feat_axis": "核心能力拆分"})
    return axes
