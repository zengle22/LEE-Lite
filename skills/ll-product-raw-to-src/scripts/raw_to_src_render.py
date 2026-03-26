#!/usr/bin/env python3
"""Markdown rendering helpers for raw-to-src candidates."""

from __future__ import annotations

import re
from typing import Any

import yaml

WORKFLOW_KEY = "product.raw-to-src"


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [item.strip("- ").strip() for item in re.split(r"[\n,;]", value) if item.strip()]
        return [item for item in parts if item]
    if isinstance(value, list):
        items: list[str] = []
        for entry in value:
            items.extend(normalize_list(entry))
        return items
    return [str(value)]


def one_line(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def _semantic_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 语义清单", ""]
    semantic_inventory = candidate.get("semantic_inventory") or {}
    for label, field in [
        ("Actors", "actors"),
        ("Product surfaces", "product_surfaces"),
        ("Operator surfaces", "operator_surfaces"),
        ("Entry points", "entry_points"),
        ("Commands", "commands"),
        ("Runtime objects", "runtime_objects"),
        ("States", "states"),
        ("Observability surfaces", "observability_surfaces"),
    ]:
        values = normalize_list(semantic_inventory.get(field))
        lines.append(f"- {label}: {'; '.join(one_line(item) for item in values) if values else 'None'}")
    return lines


def _normalization_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 标准化决策", ""]
    for decision in candidate.get("normalization_decisions", []):
        lines.append(f"- {one_line(decision.get('decision_type', 'normalization'))}: {one_line(decision.get('justification', ''))} (loss_risk={one_line(decision.get('loss_risk', 'unknown'))})")
    lines.extend(["", "## 压缩与省略说明", ""])
    omission_report = candidate.get("omission_and_compression_report") or {}
    for item in omission_report.get("compressed_items", []):
        lines.append(f"- Compressed: {one_line(item.get('item', ''))} | why={one_line(item.get('why', ''))} | risk={one_line(item.get('downstream_risk', ''))}")
    for item in omission_report.get("omitted_items", []):
        lines.append(f"- Omitted: {one_line(item.get('item', ''))} | why={one_line(item.get('why', ''))} | risk={one_line(item.get('downstream_risk', ''))}")
    if omission_report.get("summary"):
        lines.append(f"- Summary: {one_line(omission_report.get('summary', ''))}")
    return lines


def _operator_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## Operator Surface Inventory", ""]
    operator_surfaces = candidate.get("operator_surface_inventory", [])
    if operator_surfaces:
        for item in operator_surfaces:
            lines.append(f"- {one_line(item.get('entry_kind', 'surface'))}: {one_line(item.get('name', ''))} | phase={one_line(item.get('lifecycle_phase', ''))} | actor={one_line(item.get('user_actor', ''))}")
    else:
        lines.append("- None detected.")
    lines.extend(["", "## 用户入口与控制面", ""])
    skill_entries = [item for item in operator_surfaces if item.get("entry_kind") == "skill_entry"]
    cli_surfaces = [item for item in operator_surfaces if item.get("entry_kind") == "cli_control_surface"]
    monitor_surfaces = [item for item in operator_surfaces if item.get("entry_kind") == "monitor_surface"]
    if skill_entries or cli_surfaces or monitor_surfaces:
        if skill_entries:
            lines.append(f"- 主入口 skill: {'; '.join(one_line(item.get('name', '')) for item in skill_entries)}")
        if cli_surfaces:
            lines.append(f"- CLI control surface: {'; '.join(one_line(item.get('name', '')) for item in cli_surfaces)}")
        if monitor_surfaces:
            lines.append(f"- 运行监控面: {'; '.join(one_line(item.get('name', '')) for item in monitor_surfaces)}")
        lines.append("- 用户交互边界: 用户通过 Claude/Codex CLI 显式调用 skill 入口或控制命令启动、恢复、观察运行时。")
    else:
        lines.append("- 未检测到需要冻结为独立 skill / CLI control surface 的显式用户入口。")
    return lines


def _governance_sections(candidate: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    contradictions = candidate.get("contradiction_register", [])
    lines.extend(["", "## 冲突与未决点", ""])
    if contradictions:
        for item in contradictions:
            lines.append(f"- {one_line(item.get('topic', ''))}: {one_line(item.get('current_resolution', 'unresolved'))} | requires_human_confirmation={item.get('requires_human_confirmation', False)}")
    else:
        lines.append("- No explicit contradictions detected during normalization.")
    if candidate.get("target_capability_objects"):
        lines.extend(["", "## 目标能力对象", ""])
        lines.extend(f"- {one_line(item)}" for item in candidate["target_capability_objects"])
    if candidate.get("expected_outcomes"):
        lines.extend(["", "## 成功结果", ""])
        lines.extend(f"- {one_line(item)}" for item in candidate["expected_outcomes"])
    if candidate["source_kind"] == "governance_bridge_src" and candidate.get("governance_change_summary"):
        lines.extend(["", "## 治理变更摘要", ""])
        lines.extend(f"- {one_line(item)}" for item in candidate["governance_change_summary"])
    if candidate.get("semantic_lock"):
        lock = candidate["semantic_lock"]
        lines.extend(["", "## Semantic Lock", ""])
        lines.append(f"- domain_type: {one_line(lock.get('domain_type', ''))}")
        lines.append(f"- one_sentence_truth: {one_line(lock.get('one_sentence_truth', ''))}")
        lines.append(f"- primary_object: {one_line(lock.get('primary_object', ''))}")
        lines.append(f"- lifecycle_stage: {one_line(lock.get('lifecycle_stage', ''))}")
        lines.append(f"- allowed_capabilities: {'; '.join(one_line(item) for item in lock.get('allowed_capabilities', []))}")
        lines.append(f"- forbidden_capabilities: {'; '.join(one_line(item) for item in lock.get('forbidden_capabilities', []))}")
        lines.append(f"- inheritance_rule: {one_line(lock.get('inheritance_rule', ''))}")
    if candidate.get("downstream_derivation_requirements"):
        lines.extend(["", "## 下游派生要求", ""])
        lines.extend(f"- {one_line(item)}" for item in candidate["downstream_derivation_requirements"])
    return lines


def _boundary_sections(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 关键约束", ""]
    lines.extend(f"- {one_line(item)}" for item in candidate["key_constraints"])
    lines.extend(["", "## 范围边界", ""])
    lines.extend(f"- In scope: {one_line(item)}" for item in candidate["in_scope"])
    lines.extend(f"- Out of scope: {one_line(item)}" for item in candidate["out_of_scope"])
    lines.extend(["", "## 来源追溯", ""])
    lines.append(f"- Source refs: {', '.join(candidate['source_refs'])}")
    lines.append(f"- Input type: {candidate['input_type']}")
    if candidate["source_kind"] == "governance_bridge_src" and candidate.get("bridge_context"):
        if candidate.get("bridge_summary"):
            lines.extend(["", "## 桥接摘要", ""])
            lines.extend(f"- {one_line(item)}" for item in candidate["bridge_summary"])
        bridge = candidate["bridge_context"]
        lines.extend(["", "## Bridge Context", ""])
        lines.append("- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。")
        lines.append(f"- governed_by_adrs: {', '.join(bridge['governed_by_adrs'])}")
        lines.append(f"- change_scope: {one_line(bridge['change_scope'])}")
        lines.append(f"- governance_objects: {'; '.join(one_line(item) for item in bridge['governance_objects'])}")
        lines.append(f"- current_failure_modes: {'; '.join(one_line(item) for item in bridge['current_failure_modes'])}")
        lines.append(f"- downstream_inheritance_requirements: {'; '.join(one_line(item) for item in bridge['downstream_inheritance_requirements'])}")
        lines.append(f"- expected_downstream_objects: {', '.join(bridge['expected_downstream_objects'])}")
        lines.append(f"- acceptance_impact: {'; '.join(one_line(item) for item in bridge['acceptance_impact'])}")
        lines.append(f"- non_goals: {'; '.join(one_line(item) for item in bridge['non_goals'])}")
    return lines


def render_candidate_markdown(candidate: dict[str, Any]) -> str:
    frontmatter = {
        "artifact_type": "src_candidate",
        "workflow_key": WORKFLOW_KEY,
        "workflow_run_id": candidate["workflow_run_id"],
        "title": candidate["title"],
        "status": candidate["status"],
        "source_kind": candidate["source_kind"],
        "source_refs": candidate["source_refs"],
    }
    if candidate.get("semantic_lock"):
        frontmatter["semantic_lock"] = candidate["semantic_lock"]
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    lines = ["---", header, "---", "", f"# {candidate['title']}", "", "## 问题陈述", "", one_line(candidate["problem_statement"]), "", "## 目标用户", ""]
    lines.extend(f"- {one_line(item)}" for item in candidate["target_users"])
    lines.extend(["", "## 触发场景", ""])
    lines.extend(f"- {one_line(item)}" for item in candidate["trigger_scenarios"])
    lines.extend(["", "## 业务动因", ""])
    lines.extend(f"- {one_line(item)}" for item in candidate["business_drivers"])
    lines.extend(_semantic_section(candidate))
    lines.extend(_normalization_section(candidate))
    lines.extend(_operator_section(candidate))
    lines.extend(_governance_sections(candidate))
    lines.extend(_boundary_sections(candidate))
    return "\n".join(lines).rstrip() + "\n"
