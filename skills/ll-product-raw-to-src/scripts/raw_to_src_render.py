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


def _bool_label(value: Any) -> str:
    return "true" if bool(value) else "false"


def _semantic_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 语义清单", ""]
    semantic_inventory = candidate.get("semantic_inventory") or {}
    has_core_projection = any(key in semantic_inventory for key in ("core_objects", "core_states", "core_apis", "core_outputs"))
    if has_core_projection:
        api_values = normalize_list(semantic_inventory.get("core_apis"))
        api_label = "Current API anchors" if api_values and all(str(item).startswith("current_api_anchor:") for item in api_values) else "Core APIs"
        if api_label == "Current API anchors":
            api_values = [str(item).replace("current_api_anchor: ", "", 1) for item in api_values]
        lines.append(f"- Actors: {'; '.join(one_line(item) for item in normalize_list(semantic_inventory.get('actors'))) or 'None'}")
        lines.append(f"- Core objects: {'; '.join(one_line(item) for item in normalize_list(semantic_inventory.get('core_objects'))) or 'None'}")
        lines.append(f"- Core states: {'; '.join(one_line(item) for item in normalize_list(semantic_inventory.get('core_states'))) or 'None'}")
        lines.append(f"- {api_label}: {'; '.join(one_line(item) for item in api_values) or 'None'}")
        lines.append(f"- Core outputs: {'; '.join(one_line(item) for item in normalize_list(semantic_inventory.get('core_outputs'))) or 'None'}")
    detail_fields = [
        ("Product surfaces", "product_surfaces"),
        ("Operator surfaces", "operator_surfaces"),
        ("Entry points", "entry_points"),
        ("Commands", "commands"),
        ("Runtime objects", "runtime_objects"),
        ("States", "states"),
        ("Observability surfaces", "observability_surfaces"),
    ]
    if not has_core_projection:
        detail_fields.insert(0, ("Actors", "actors"))
    for label, field in detail_fields:
        values = normalize_list(semantic_inventory.get(field))
        if field == "commands" and values and all(str(item).startswith("candidate_command_surface:") for item in values):
            label = "Candidate command surfaces"
            values = [str(item).replace("candidate_command_surface: ", "", 1) for item in values]
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
        semantic_inventory = candidate.get("semantic_inventory") or {}
        if normalize_list(semantic_inventory.get("entry_points")) or normalize_list(semantic_inventory.get("commands")) or normalize_list(semantic_inventory.get("core_apis")):
            lines.append("- 未检测到需要冻结为独立 CLI/skill 的 operator surface，但已识别业务入口与 API command surface。")
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
        semantic_inventory = candidate.get("semantic_inventory") or {}
        if normalize_list(semantic_inventory.get("entry_points")) or normalize_list(semantic_inventory.get("commands")):
            lines.append("- 未检测到需要冻结为独立 skill / CLI control surface 的显式用户入口；业务入口与 command surface 已在语义清单中冻结。")
        else:
            lines.append("- 未检测到需要冻结为独立 skill / CLI control surface 的显式用户入口。")
    return lines


def _frozen_input_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 冻结输入与需求源快照", ""]
    run_id = one_line(candidate.get("workflow_run_id") or "raw-to-src-run")
    source_refs = candidate.get("source_refs", [])
    lines.append("- source_snapshot_mode: embedded")
    lines.append(f"- frozen_input_dir: artifacts/raw-to-src/{run_id}/input/")
    lines.append("- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界")
    if source_refs:
        lines.append(f"- lineage_refs: {', '.join(one_line(item) for item in source_refs)}")
    lines.append("- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。")
    return lines


def _source_snapshot_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 内嵌需求源快照", ""]
    snapshot = candidate.get("source_snapshot") or {}
    capture = snapshot.get("capture_metadata") or {}
    run_id = one_line(candidate.get("workflow_run_id") or "raw-to-src-run")
    source_refs = snapshot.get("source_refs") or candidate.get("source_refs", [])
    lines.append("- source_snapshot_mode: embedded")
    lines.append(f"- frozen_input_dir: artifacts/raw-to-src/{run_id}/input/")
    lines.append("- snapshot_scope: 问题陈述 / 目标用户 / 触发场景 / 业务动因 / 关键约束 / 范围边界")
    lines.append(f"- frozen_input_ref: {one_line(capture.get('frozen_ref', '')) or 'None'}")
    lines.append(f"- frozen_input_sha256: {one_line(capture.get('content_hash', '')) or 'None'}")
    lines.append(f"- captured_at: {one_line(capture.get('captured_at', '')) or 'None'}")
    lines.append(f"- original_source_path: {one_line(snapshot.get('source_path', '')) or 'None'}")
    lines.append(f"- embedded_title: {one_line(snapshot.get('title', '')) or one_line(candidate.get('title', ''))}")
    lines.append(f"- embedded_input_type: {one_line(snapshot.get('input_type', '')) or one_line(candidate.get('input_type', ''))}")
    if source_refs:
        lines.append(f"- lineage_refs: {', '.join(one_line(item) for item in source_refs)}")
    if snapshot.get("sections"):
        lines.append(f"- embedded_sections: {', '.join(str(name) for name in snapshot.get('sections', {}).keys())}")
    if snapshot.get("body"):
        lines.append(f"- embedded_body_excerpt: {one_line(snapshot.get('body', ''))[:400]}")
    lines.append("- review_rule: 外部 source_refs 仅用于追溯，不是理解候选的前提。")
    return lines


def _semantic_layer_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 文档语义层级", ""]
    declaration = candidate.get("semantic_layer_declaration") or {}
    if not declaration:
        lines.append("- None.")
        return lines
    for label, field in [("source_layer", "authoritative_fields"), ("bridge_layer", "derived_fields"), ("meta_layer", "fields")]:
        payload = declaration.get(label) or {}
        lines.append(f"- {label}.role: {one_line(payload.get('role', ''))}")
        lines.append(f"- {label}.fields: {', '.join(str(item) for item in payload.get(field, [])) or 'None'}")
        lines.append(f"- {label}.consumption_rule: {one_line(payload.get('consumption_rule', ''))}")
    lines.append(f"- precedence_order: {', '.join(str(item) for item in declaration.get('precedence_order', []))}")
    lines.append(f"- override_rule: {one_line(declaration.get('override_rule', ''))}")
    return lines


def _frozen_contracts_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## Frozen Contracts", ""]
    contracts = candidate.get("frozen_contracts") or []
    if not contracts:
        lines.append("- None.")
        return lines
    for item in contracts:
        lines.append(f"- {one_line(item.get('id', 'FC'))}: {one_line(item.get('statement', ''))}")
        lines.append(f"  applies_to={', '.join(str(value) for value in item.get('applies_to', [])) or 'None'} | authoritative_layer={one_line(item.get('authoritative_layer', ''))}")
    return lines


def _structured_object_contracts_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 结构化对象契约", ""]
    contracts = candidate.get("structured_object_contracts") or []
    if not contracts:
        lines.append("- None.")
        return lines
    for item in contracts:
        lines.append(f"- object: {one_line(item.get('object', ''))}")
        for key in [
            "purpose",
            "semantic_axis",
            "required_fields",
            "optional_fields",
            "canonical_field_policy",
            "transitional_input_aliases",
            "forbidden_fields",
            "completion_effect",
            "allowed_values",
            "value_definitions",
            "forbidden_semantics",
            "downstream_usage",
            "primary_state",
            "capability_flags",
            "constraints",
            "minimum_outputs",
            "blocked_by",
            "deferred_inputs",
            "authoritative_profile_owner",
            "physical_fields",
            "runner_profile_fields",
            "authoritative_conflict_rule",
            "forbidden_duplication",
            "bridge_split_recommendation",
            "conditional_required_fields",
            "runtime_interpretation",
            "minimum_checks",
            "failure_behavior",
            "output_contract",
        ]:
            value = item.get(key)
            if value in (None, "", [], {}):
                continue
            if isinstance(value, list):
                lines.append(f"  {key}: {', '.join(str(entry) for entry in value)}")
            elif isinstance(value, dict):
                parts = [f"{sub_key}={sub_value}" for sub_key, sub_value in value.items()]
                lines.append(f"  {key}: {', '.join(parts)}")
            else:
                lines.append(f"  {key}: {value}")
    return lines


def _enum_freeze_section(candidate: dict[str, Any]) -> list[str]:
    lines = ["", "## 枚举冻结", ""]
    enum_freezes = candidate.get("enum_freezes") or {}
    if not enum_freezes:
        lines.append("- None.")
        return lines
    for field_name, payload in enum_freezes.items():
        lines.append(f"- field: {field_name}")
        lines.append(f"  semantic_axis: {one_line(payload.get('semantic_axis', ''))}")
        lines.append(f"  allowed_values: {', '.join(str(item) for item in payload.get('allowed_values', [])) or 'None'}")
        if payload.get("value_definitions"):
            parts = [f"{sub_key}={sub_value}" for sub_key, sub_value in payload.get("value_definitions", {}).items()]
            lines.append(f"  value_definitions: {', '.join(parts)}")
        lines.append(f"  forbidden_semantics: {', '.join(str(item) for item in payload.get('forbidden_semantics', [])) or 'None'}")
        lines.append(f"  used_for: {', '.join(str(item) for item in payload.get('used_for', [])) or 'None'}")
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
    if candidate.get("governance_change_summary"):
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
    lines.append("- SSOT policy: src candidate must remain reviewable even if the original external requirement file is later removed.")
    if candidate.get("bridge_summary"):
        lines.extend(["", "## 桥接摘要", ""])
        lines.extend(f"- {one_line(item)}" for item in candidate["bridge_summary"])
    if candidate.get("bridge_context"):
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
        if bridge.get("recommended_min_profile_split"):
            lines.append(f"- recommended_min_profile_split: {'; '.join(one_line(item) for item in bridge['recommended_min_profile_split'])}")
        if bridge.get("current_api_anchors"):
            lines.append(f"- current_api_anchors: {'; '.join(one_line(item) for item in bridge['current_api_anchors'])}")
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
        "source_snapshot_mode": "embedded",
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
    lines.extend(_frozen_input_section(candidate))
    lines.extend(_source_snapshot_section(candidate))
    lines.extend(_semantic_layer_section(candidate))
    lines.extend(_frozen_contracts_section(candidate))
    lines.extend(_structured_object_contracts_section(candidate))
    lines.extend(_enum_freeze_section(candidate))
    lines.extend(_semantic_section(candidate))
    lines.extend(_normalization_section(candidate))
    lines.extend(_operator_section(candidate))
    lines.extend(_governance_sections(candidate))
    lines.extend(_boundary_sections(candidate))
    return "\n".join(lines).rstrip() + "\n"
