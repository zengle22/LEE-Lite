#!/usr/bin/env python3
"""Round support helpers for ll-gate-human-orchestrator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gate_human_orchestrator_common import dump_json, load_gate_ready_package, load_json, repo_relative


def path_variants(value: str, repo_root: Path) -> set[str]:
    raw = str(value or "").strip()
    if not raw:
        return set()
    variants = {raw, raw.replace("\\", "/")}
    try:
        path = Path(raw)
        if not path.is_absolute():
            path = repo_root / path
        resolved = path.resolve()
        variants.update({str(resolved), resolved.as_posix(), str(resolved).replace("\\", "/")})
    except Exception:
        pass
    return {item for item in variants if item}


def load_ssot_excerpt(repo_root: Path, machine_ssot_ref: str) -> list[str]:
    return load_ssot_brief(repo_root, machine_ssot_ref)["excerpt"]


def load_ssot_brief(repo_root: Path, machine_ssot_ref: str) -> dict[str, Any]:
    if not machine_ssot_ref:
        return {"excerpt": [], "outline": [], "review_points": [], "fulltext_markdown": ""}
    ssot_path = resolve_ssot_path(repo_root, machine_ssot_ref)
    if not ssot_path.exists():
        return {"excerpt": [], "outline": [], "review_points": [], "fulltext_markdown": ""}
    excerpt: list[str] = []
    outline: list[str] = []
    review_points: list[str] = []
    try:
        payload = load_json(ssot_path)
        outline = ssot_outline(payload)
        review_points = ssot_review_points(payload)
        fulltext_markdown = ssot_fulltext_markdown(payload)
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            excerpt.append(f"标题: {title.strip()}")
        for line in _artifact_specific_excerpt(payload):
            _append_unique_line(excerpt, line)
        for line in _semantic_inventory_excerpt(payload):
            _append_unique_line(excerpt, line)
        problem_statement = payload.get("problem_statement")
        if isinstance(problem_statement, str) and problem_statement.strip():
            _append_unique_line(excerpt, f"问题: {problem_statement.strip()[:160]}")
        bridge_summary = payload.get("bridge_summary")
        if isinstance(bridge_summary, list):
            for item in bridge_summary:
                if isinstance(item, str) and item.strip():
                    _append_unique_line(excerpt, f"摘要: {item.strip()}")
                    break
        key_constraints = payload.get("key_constraints")
        if isinstance(key_constraints, list):
            for item in key_constraints[:2]:
                if isinstance(item, str) and item.strip():
                    _append_unique_line(excerpt, f"约束: {item.strip()}")
        for label, field in (
            ("驱动", "business_drivers"),
            ("结果", "expected_outcomes"),
            ("继承要求", "downstream_derivation_requirements"),
            ("治理变化", "governance_change_summary"),
            ("范围", "in_scope"),
        ):
            _append_labeled_items(excerpt, payload.get(field), label, limit=1)
        semantic_layers = _semantic_layer_declaration(payload)
        precedence = semantic_layers.get("precedence_order")
        if isinstance(precedence, list) and precedence:
            labels = [str(item).strip() for item in precedence if str(item).strip()]
            if labels:
                _append_unique_line(excerpt, "语义分层: " + " > ".join(labels))
        frozen_contracts = _first_dict_items(payload.get("frozen_contracts"), limit=2)
        for entry in frozen_contracts:
            contract_id = str(entry.get("id", "")).strip()
            statement = str(entry.get("statement", "")).strip()
            if contract_id and statement:
                _append_unique_line(excerpt, f"冻结契约: {contract_id} {statement}")
        structured_contracts = _structured_object_contract_summaries(payload, limit=2)
        if structured_contracts:
            _append_unique_line(excerpt, "对象契约: " + "；".join(structured_contracts))
        enum_summaries = _enum_freeze_summaries(payload, limit=2)
        if enum_summaries:
            _append_unique_line(excerpt, "枚举冻结: " + "；".join(enum_summaries))
        for label, field in (
            ("产品摘要", "product_summary"),
            ("完成态", "completed_state"),
            ("权威输出", "authoritative_output"),
            ("冻结边界", "frozen_downstream_boundary"),
        ):
            value = payload.get(field)
            if isinstance(value, str) and value.strip():
                _append_unique_line(excerpt, f"{label}: {value.strip()}")
        return {
            "excerpt": excerpt[:8],
            "outline": outline[:8],
            "review_points": review_points[:8],
            "fulltext_markdown": fulltext_markdown,
        }
    except (json.JSONDecodeError, UnicodeDecodeError):
        text = ssot_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped == "---":
                continue
            if stripped.startswith(("artifact_type:", "workflow_key:", "workflow_run_id:", "status:", "source_refs:")):
                continue
            excerpt.append(stripped)
            if len(excerpt) >= 4:
                break
        return {"excerpt": excerpt, "outline": [], "review_points": [], "fulltext_markdown": ""}


def resolve_ssot_path(repo_root: Path, machine_ssot_ref: str) -> Path:
    path = Path(machine_ssot_ref)
    candidate = path if path.is_absolute() else (repo_root / path)
    if candidate.exists():
        return candidate
    registry_dir = repo_root / "artifacts" / "registry"
    if registry_dir.exists():
        for registry_path in sorted(registry_dir.glob("*.json")):
            try:
                record = load_json(registry_path)
            except Exception:
                continue
            artifact_ref = str(record.get("artifact_ref", "")).strip()
            managed_ref = str(record.get("managed_artifact_ref", "")).strip()
            if artifact_ref != machine_ssot_ref or not managed_ref:
                continue
            managed_path = Path(managed_ref) if Path(managed_ref).is_absolute() else (repo_root / managed_ref)
            return managed_path
    return candidate


def _append_labeled_items(target: list[str], raw_value: object, label: str, *, limit: int) -> None:
    if not isinstance(raw_value, list):
        return
    count = 0
    for item in raw_value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        target.append(f"{label}: {text}")
        count += 1
        if count >= limit:
            break


def _append_unique_line(target: list[str], line: str) -> None:
    text = str(line or "").strip()
    if text and text not in target:
        target.append(text)


def _semantic_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("semantic_inventory")
    return value if isinstance(value, dict) else {}


def _semantic_inventory_items(raw_value: object, *, limit: int) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    items: list[str] = []
    for raw in raw_value:
        if not isinstance(raw, str):
            continue
        text = raw.strip()
        if not text:
            continue
        if text[:2] in {"- ", "* "}:
            text = text[2:].strip()
        items.append(text)
        if len(items) >= limit:
            break
    return items


def _semantic_inventory_excerpt(payload: dict[str, Any]) -> list[str]:
    semantic_inventory = _semantic_inventory(payload)
    if not semantic_inventory:
        return []
    lines: list[str] = []
    actors = _semantic_inventory_items(semantic_inventory.get("actors"), limit=2)
    if actors:
        _append_unique_line(lines, "语义角色: " + _join_items(actors))
    capability_objects = _semantic_inventory_items(payload.get("target_capability_objects"), limit=3)
    if not capability_objects:
        capability_objects = _semantic_inventory_items(semantic_inventory.get("core_objects"), limit=3)
    if not capability_objects:
        capability_objects = _semantic_inventory_items(semantic_inventory.get("product_surfaces"), limit=3)
    if capability_objects:
        _append_unique_line(lines, "能力对象: " + _join_items(capability_objects))
    states = _semantic_inventory_items(semantic_inventory.get("core_states"), limit=2)
    if not states:
        states = _semantic_inventory_items(semantic_inventory.get("states"), limit=2)
    if states:
        _append_unique_line(lines, "状态/能力轴: " + _join_items(states))
    interface_items: list[str] = []
    for field in ("core_apis", "core_outputs", "operator_surfaces", "entry_points", "commands", "runtime_objects", "observability_surfaces"):
        interface_items.extend(_semantic_inventory_items(semantic_inventory.get(field), limit=2))
    top_operator_surfaces = _semantic_inventory_items(payload.get("operator_surface_inventory"), limit=2)
    if top_operator_surfaces:
        interface_items.extend(top_operator_surfaces)
    if interface_items:
        _append_unique_line(lines, "关键接口: " + _join_items(interface_items[:4]))
    else:
        _append_unique_line(lines, "关键接口: 暂无显式条目（commands / runtime_objects / operator_surfaces 仍为空）")
    constraints = _semantic_inventory_items(semantic_inventory.get("constraints"), limit=2)
    if constraints:
        _append_unique_line(lines, "语义约束: " + _join_items(constraints))
    return lines[:5]


def _semantic_layer_declaration(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("semantic_layer_declaration")
    return value if isinstance(value, dict) else {}


def _enum_freezes(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("enum_freezes")
    return value if isinstance(value, dict) else {}


def _render_mapping_items(raw_value: object) -> str:
    if isinstance(raw_value, dict):
        parts = []
        for key, value in raw_value.items():
            key_text = str(key).strip()
            value_text = str(value).strip()
            if key_text and value_text:
                parts.append(f"{key_text}={value_text}")
        return ", ".join(parts)
    if isinstance(raw_value, list):
        parts = [str(item).strip() for item in raw_value if str(item).strip()]
        return ", ".join(parts)
    if raw_value not in (None, ""):
        return str(raw_value).strip()
    return ""


def _structured_object_contract_summaries(payload: dict[str, Any], *, limit: int = 4) -> list[str]:
    summaries: list[str] = []
    for entry in _first_dict_items(payload.get("structured_object_contracts"), limit=limit):
        object_name = str(entry.get("object", "")).strip()
        if not object_name:
            continue
        parts = [f"object={object_name}"]
        for field in ("purpose", "semantic_axis", "canonical_owner"):
            text = str(entry.get(field, "")).strip()
            if text:
                parts.append(f"{field}={text}")
        required_fields = _render_mapping_items(entry.get("required_fields"))
        if required_fields:
            parts.append(f"required_fields={required_fields}")
        allowed_values = _render_mapping_items(entry.get("allowed_values"))
        if allowed_values:
            parts.append(f"allowed_values={allowed_values}")
        conflict_rule = str(entry.get("authoritative_conflict_rule", "")).strip()
        if conflict_rule:
            parts.append(f"conflict_rule={conflict_rule}")
        summaries.append(" | ".join(parts))
    return summaries


def _enum_freeze_summaries(payload: dict[str, Any], *, limit: int = 3) -> list[str]:
    summaries: list[str] = []
    for field_name, details in list(_enum_freezes(payload).items())[:limit]:
        if not isinstance(details, dict):
            continue
        parts = [f"field={field_name}"]
        semantic_axis = str(details.get("semantic_axis", "")).strip()
        if semantic_axis:
            parts.append(f"semantic_axis={semantic_axis}")
        allowed_values = _render_mapping_items(details.get("allowed_values"))
        if allowed_values:
            parts.append(f"allowed_values={allowed_values}")
        used_for = _render_mapping_items(details.get("used_for"))
        if used_for:
            parts.append(f"used_for={used_for}")
        summaries.append(" | ".join(parts))
    return summaries


def _count_list(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field)
    return len(value) if isinstance(value, list) else 0


def _first_dict_items(raw_value: object, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(raw_value, list):
        return []
    items: list[dict[str, Any]] = []
    for entry in raw_value:
        if not isinstance(entry, dict):
            continue
        items.append(entry)
        if len(items) >= limit:
            break
    return items


def _dict_field_text(entry: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _role_summaries(raw_value: object, *, limit: int) -> list[str]:
    summaries: list[str] = []
    for entry in _first_dict_items(raw_value, limit=limit):
        role = _dict_field_text(entry, "role", "name", "actor")
        responsibility = _dict_field_text(entry, "responsibility", "summary", "goal")
        if role and responsibility:
            summaries.append(f"{role}：{responsibility}")
        elif role:
            summaries.append(role)
    return summaries


def _slice_summaries(raw_value: object, *, limit: int) -> list[str]:
    summaries: list[str] = []
    for entry in _first_dict_items(raw_value, limit=limit):
        name = _dict_field_text(entry, "name", "title", "id")
        goal = _dict_field_text(entry, "goal", "summary")
        track = _dict_field_text(entry, "track")
        if name and goal and track:
            summaries.append(f"{name}（{track}）: {goal}")
        elif name and goal:
            summaries.append(f"{name}: {goal}")
        elif name:
            summaries.append(name)
    return summaries


def _feature_summaries(raw_value: object, *, limit: int) -> list[str]:
    summaries: list[str] = []
    for entry in _first_dict_items(raw_value, limit=limit):
        title = _dict_field_text(entry, "title", "name", "slice_id")
        goal = _dict_field_text(entry, "goal")
        track = _dict_field_text(entry, "track")
        if title and goal and track:
            summaries.append(f"{title}（{track}）: {goal}")
        elif title and goal:
            summaries.append(f"{title}: {goal}")
        elif title:
            summaries.append(title)
    return summaries


def _module_summaries(raw_value: object, *, limit: int) -> list[str]:
    summaries: list[str] = []
    if not isinstance(raw_value, list):
        return summaries
    for item in raw_value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        summaries.append(text)
        if len(summaries) >= limit:
            break
    return summaries


def _test_unit_summaries(raw_value: object, *, limit: int) -> list[str]:
    summaries: list[str] = []
    for entry in _first_dict_items(raw_value, limit=limit):
        unit_ref = _dict_field_text(entry, "unit_ref", "id")
        title = _dict_field_text(entry, "title", "name")
        trigger = _dict_field_text(entry, "trigger_action")
        pass_condition = _dict_field_text(entry, "pass_conditions")
        headline = title or trigger or pass_condition or unit_ref
        if not headline:
            continue
        if unit_ref and headline != unit_ref:
            summaries.append(f"{unit_ref} {headline}")
        else:
            summaries.append(headline)
    return summaries


def _artifact_specific_excerpt(payload: dict[str, Any]) -> list[str]:
    artifact_type = str(payload.get("artifact_type", "")).strip()
    excerpt: list[str] = []
    if artifact_type == "epic_freeze_package":
        business_goal = str(payload.get("business_goal", "")).strip()
        if business_goal:
            excerpt.append(f"业务目标: {business_goal}")
        slices = _slice_summaries(payload.get("product_behavior_slices"), limit=4)
        if slices:
            excerpt.append(f"产品切片: 共 {_count_list(payload, 'product_behavior_slices')} 个，重点是 {_join_items(slices)}")
        roles = _role_summaries(payload.get("actors_and_roles"), limit=3)
        if roles:
            excerpt.append(f"关键角色: {_join_items(roles)}")
        success = _first_items(payload, "epic_success_criteria", limit=2)
        if success:
            excerpt.append(f"成功标准: {_join_items(success)}")
        downstream = str(payload.get("downstream_workflow", "")).strip()
        if downstream:
            excerpt.append(f"下游交接: {downstream}")
        return excerpt
    if artifact_type == "feat_freeze_package":
        bundle_intent = str(payload.get("bundle_intent", "")).strip()
        if bundle_intent:
            excerpt.append(f"Bundle 意图: {bundle_intent}")
        epic_context = payload.get("epic_context")
        if isinstance(epic_context, dict):
            business_goal = str(epic_context.get("business_goal", "")).strip()
            if business_goal:
                excerpt.append(f"业务目标: {business_goal}")
            positioning = str(epic_context.get("product_positioning", "")).strip()
            if positioning:
                excerpt.append(f"产品定位: {positioning}")
        features = _feature_summaries(payload.get("features"), limit=4)
        if features:
            excerpt.append(f"拆分结果: 共 {_count_list(payload, 'features')} 个 FEAT，重点是 {_join_items(features)}")
        downstream_workflows = _first_items(payload, "downstream_workflows", limit=3)
        if downstream_workflows:
            excerpt.append(f"下游工作流: {_join_items(downstream_workflows)}")
        return excerpt
    if artifact_type == "tech_design_package":
        selected_feat = payload.get("selected_feat")
        if isinstance(selected_feat, dict):
            goal = str(selected_feat.get("goal", "")).strip()
            if goal:
                excerpt.append(f"实现目标: {goal}")
        state_model = _first_items(payload.get("tech_design", {}), "state_model", limit=2) if isinstance(payload.get("tech_design"), dict) else []
        if state_model:
            excerpt.append(f"状态机: {_join_items(state_model)}")
        module_plan = _first_items(payload.get("tech_design", {}), "module_plan", limit=3) if isinstance(payload.get("tech_design"), dict) else []
        if module_plan:
            excerpt.append(f"实现模块: {_join_items(module_plan)}")
        interface_contracts = _first_items(payload.get("tech_design", {}), "interface_contracts", limit=2) if isinstance(payload.get("tech_design"), dict) else []
        if interface_contracts:
            excerpt.append(f"关键合同: {_join_items(interface_contracts)}")
        downstream = payload.get("downstream_handoff")
        if isinstance(downstream, dict):
            target_workflow = str(downstream.get("target_workflow", "")).strip()
            if target_workflow:
                excerpt.append(f"下游交接: {target_workflow}")
        return excerpt
    if artifact_type == "test_set_candidate_package":
        selected_feat = payload.get("selected_feat")
        if isinstance(selected_feat, dict):
            goal = str(selected_feat.get("goal", "")).strip()
            if goal:
                excerpt.append(f"测试目标: {goal}")
        test_units = _test_unit_summaries(payload.get("strategy_draft", {}).get("test_units") if isinstance(payload.get("strategy_draft"), dict) else payload.get("test_units"), limit=3)
        if test_units:
            excerpt.append(f"关键测试单元: {_join_items(test_units)}")
        pass_criteria = _first_items(payload.get("test_set", {}), "pass_criteria", limit=2) if isinstance(payload.get("test_set"), dict) else _first_items(payload, "pass_criteria", limit=2)
        if pass_criteria:
            excerpt.append(f"通过标准: {_join_items(pass_criteria)}")
        downstream_target = str(payload.get("downstream_target", "")).strip()
        if downstream_target:
            excerpt.append(f"下游执行目标: {downstream_target}")
        return excerpt
    if artifact_type == "feature_impl_candidate_package":
        selected_scope = payload.get("selected_scope")
        if isinstance(selected_scope, dict):
            goal = str(selected_scope.get("goal", "")).strip()
            if goal:
                excerpt.append(f"实现目标: {goal}")
        workstream_assessment = payload.get("workstream_assessment")
        if isinstance(workstream_assessment, dict):
            surfaces: list[str] = []
            if bool(workstream_assessment.get("frontend_required")):
                surfaces.append("frontend")
            if bool(workstream_assessment.get("backend_required")):
                surfaces.append("backend")
            if bool(workstream_assessment.get("migration_required")):
                surfaces.append("migration")
            if surfaces:
                excerpt.append(f"执行面: {_join_items(surfaces)}")
        implementation_steps = payload.get("implementation_steps")
        if isinstance(implementation_steps, list):
            titles: list[str] = []
            for entry in implementation_steps[:3]:
                if not isinstance(entry, dict):
                    continue
                title = str(entry.get("title", "")).strip()
                if title:
                    titles.append(title)
            if titles:
                excerpt.append(f"实施步骤: {_join_items(titles)}")
        downstream = payload.get("downstream_handoff")
        if isinstance(downstream, dict):
            template_id = str(downstream.get("target_template_id", "")).strip()
            if template_id:
                excerpt.append(f"交付模板: {template_id}")
        return excerpt
    return excerpt


def ssot_outline(payload: dict[str, Any]) -> list[str]:
    outline: list[str] = []
    artifact_type = str(payload.get("artifact_type", "")).strip()
    header = []
    for field in ("artifact_type", "workflow_key", "workflow_run_id", "status", "input_type", "source_kind"):
        value = payload.get(field)
        if value not in (None, "", []):
            header.append(f"{field}={value}")
    if header:
        outline.append("标识: " + "; ".join(header))
    if artifact_type == "epic_freeze_package":
        epic_sections = [
            ("actors_and_roles", _count_list(payload, "actors_and_roles")),
            ("product_behavior_slices", _count_list(payload, "product_behavior_slices")),
            ("decomposition_rules", _count_list(payload, "decomposition_rules")),
            ("epic_success_criteria", _count_list(payload, "epic_success_criteria")),
            ("source_refs", _count_list(payload, "source_refs")),
        ]
        outline.append("EPIC 主体块: " + ", ".join(f"{name}[{count}]" for name, count in epic_sections if count))
        downstream_workflow = str(payload.get("downstream_workflow", "")).strip()
        if downstream_workflow:
            outline.append("下游工作流: " + downstream_workflow)
        return outline
    if artifact_type == "feat_freeze_package":
        feat_sections = [
            ("feat_refs", _count_list(payload, "feat_refs")),
            ("features", _count_list(payload, "features")),
            ("downstream_workflows", _count_list(payload, "downstream_workflows")),
            ("bundle_shared_non_goals", _count_list(payload, "bundle_shared_non_goals")),
            ("source_refs", _count_list(payload, "source_refs")),
        ]
        outline.append("FEAT Bundle 主体块: " + ", ".join(f"{name}[{count}]" for name, count in feat_sections if count))
        epic_context = payload.get("epic_context")
        if isinstance(epic_context, dict):
            nested = [
                ("actors_and_roles", len(epic_context.get("actors_and_roles", [])) if isinstance(epic_context.get("actors_and_roles"), list) else 0),
                ("product_behavior_slices", len(epic_context.get("product_behavior_slices", [])) if isinstance(epic_context.get("product_behavior_slices"), list) else 0),
                ("decomposition_rules", len(epic_context.get("decomposition_rules", [])) if isinstance(epic_context.get("decomposition_rules"), list) else 0),
                ("epic_success_criteria", len(epic_context.get("epic_success_criteria", [])) if isinstance(epic_context.get("epic_success_criteria"), list) else 0),
            ]
            outline.append("epic_context 子块: " + ", ".join(f"{name}[{count}]" for name, count in nested if count))
        feature_titles = [item.split(":", 1)[0] for item in _feature_summaries(payload.get("features"), limit=5)]
        if feature_titles:
            outline.append("主要 FEAT: " + "；".join(feature_titles))
        return outline
    if artifact_type == "tech_design_package":
        tech_design = payload.get("tech_design")
        if isinstance(tech_design, dict):
            tech_sections = [
                ("design_focus", len(tech_design.get("design_focus", [])) if isinstance(tech_design.get("design_focus"), list) else 0),
                ("module_plan", len(tech_design.get("module_plan", [])) if isinstance(tech_design.get("module_plan"), list) else 0),
                ("state_model", len(tech_design.get("state_model", [])) if isinstance(tech_design.get("state_model"), list) else 0),
                ("interface_contracts", len(tech_design.get("interface_contracts", [])) if isinstance(tech_design.get("interface_contracts"), list) else 0),
                ("implementation_unit_mapping", len(tech_design.get("implementation_unit_mapping", [])) if isinstance(tech_design.get("implementation_unit_mapping"), list) else 0),
            ]
            outline.append("TECH 主体块: " + ", ".join(f"{name}[{count}]" for name, count in tech_sections if count))
        selected_feat = payload.get("selected_feat")
        if isinstance(selected_feat, dict):
            title = str(selected_feat.get("title", "")).strip()
            if title:
                outline.append("Selected FEAT: " + title)
        downstream = payload.get("downstream_handoff")
        if isinstance(downstream, dict):
            target_workflow = str(downstream.get("target_workflow", "")).strip()
            if target_workflow:
                outline.append("下游工作流: " + target_workflow)
        return outline
    if artifact_type == "test_set_candidate_package":
        requirement_analysis = payload.get("requirement_analysis")
        strategy_draft = payload.get("strategy_draft")
        test_set = payload.get("test_set")
        test_sections = []
        if isinstance(requirement_analysis, dict):
            test_sections.extend(
                [
                    ("coverage_scope", len(requirement_analysis.get("coverage_scope", [])) if isinstance(requirement_analysis.get("coverage_scope"), list) else 0),
                    ("risk_focus", len(requirement_analysis.get("risk_focus", [])) if isinstance(requirement_analysis.get("risk_focus"), list) else 0),
                    ("coverage_exclusions", len(requirement_analysis.get("coverage_exclusions", [])) if isinstance(requirement_analysis.get("coverage_exclusions"), list) else 0),
                ]
            )
        if isinstance(strategy_draft, dict):
            test_sections.append(("test_units", len(strategy_draft.get("test_units", [])) if isinstance(strategy_draft.get("test_units"), list) else 0))
        if isinstance(test_set, dict):
            test_sections.extend(
                [
                    ("pass_criteria", len(test_set.get("pass_criteria", [])) if isinstance(test_set.get("pass_criteria"), list) else 0),
                    ("environment_assumptions", len(test_set.get("environment_assumptions", [])) if isinstance(test_set.get("environment_assumptions"), list) else 0),
                ]
            )
        if test_sections:
            outline.append("TESTSET 主体块: " + ", ".join(f"{name}[{count}]" for name, count in test_sections if count))
        selected_feat = payload.get("selected_feat")
        if isinstance(selected_feat, dict):
            title = str(selected_feat.get("title", "")).strip()
            if title:
                outline.append("Selected FEAT: " + title)
        downstream_target = str(payload.get("downstream_target", "")).strip()
        if downstream_target:
            outline.append("下游执行目标: " + downstream_target)
        return outline
    if artifact_type == "feature_impl_candidate_package":
        impl_sections = [
            ("source_refs", _count_list(payload, "source_refs")),
            ("implementation_steps", _count_list(payload, "implementation_steps")),
        ]
        outline.append("IMPL 主体块: " + ", ".join(f"{name}[{count}]" for name, count in impl_sections if count))
        selected_scope = payload.get("selected_scope")
        if isinstance(selected_scope, dict):
            nested = [
                ("scope", len(selected_scope.get("scope", [])) if isinstance(selected_scope.get("scope"), list) else 0),
                ("constraints", len(selected_scope.get("constraints", [])) if isinstance(selected_scope.get("constraints"), list) else 0),
                ("dependencies", len(selected_scope.get("dependencies", [])) if isinstance(selected_scope.get("dependencies"), list) else 0),
            ]
            outline.append("selected_scope 子块: " + ", ".join(f"{name}[{count}]" for name, count in nested if count))
        downstream_handoff = payload.get("downstream_handoff")
        if isinstance(downstream_handoff, dict):
            phase_inputs = downstream_handoff.get("phase_inputs")
            if isinstance(phase_inputs, dict):
                phase_sections = [f"{name}[{len(value)}]" for name, value in phase_inputs.items() if isinstance(value, list) and value]
                if phase_sections:
                    outline.append("交付输入: " + ", ".join(phase_sections))
        step_titles: list[str] = []
        for entry in payload.get("implementation_steps", []) if isinstance(payload.get("implementation_steps"), list) else []:
            if not isinstance(entry, dict):
                continue
            title = str(entry.get("title", "")).strip()
            if title:
                step_titles.append(title)
            if len(step_titles) >= 4:
                break
        if step_titles:
            outline.append("主要实施步骤: " + "；".join(step_titles))
        return outline
    top_sections = [
        ("target_users", _count_list(payload, "target_users")),
        ("trigger_scenarios", _count_list(payload, "trigger_scenarios")),
        ("business_drivers", _count_list(payload, "business_drivers")),
        ("key_constraints", _count_list(payload, "key_constraints")),
        ("expected_outcomes", _count_list(payload, "expected_outcomes")),
        ("downstream_derivation_requirements", _count_list(payload, "downstream_derivation_requirements")),
        ("in_scope", _count_list(payload, "in_scope")),
        ("out_of_scope", _count_list(payload, "out_of_scope")),
        ("source_refs", _count_list(payload, "source_refs")),
        ("uncertainties", _count_list(payload, "uncertainties")),
    ]
    outline.append("顶层章节: " + ", ".join(f"{name}[{count}]" for name, count in top_sections if count))
    bridge_context = payload.get("bridge_context")
    if isinstance(bridge_context, dict):
        bridge_sections = []
        for field in (
            "governed_by_adrs",
            "governance_objects",
            "current_failure_modes",
            "downstream_inheritance_requirements",
            "expected_downstream_objects",
            "acceptance_impact",
            "non_goals",
        ):
            value = bridge_context.get(field)
            if isinstance(value, list) and value:
                bridge_sections.append(f"{field}[{len(value)}]")
        change_scope = str(bridge_context.get("change_scope", "")).strip()
        if change_scope:
            outline.append("bridge_context.change_scope: " + change_scope[:120])
        if bridge_sections:
            outline.append("bridge_context 子块: " + ", ".join(bridge_sections))
    governance_summary = payload.get("governance_change_summary")
    if isinstance(governance_summary, list) and governance_summary:
        outline.append("治理变化主线: " + " | ".join(str(item).strip() for item in governance_summary[:2] if str(item).strip()))
    semantic_layers = _semantic_layer_declaration(payload)
    if semantic_layers:
        precedence = semantic_layers.get("precedence_order")
        if isinstance(precedence, list) and precedence:
            order = [str(item).strip() for item in precedence if str(item).strip()]
            if order:
                outline.append("文档语义层级: " + " > ".join(order))
        override_rule = str(semantic_layers.get("override_rule", "")).strip()
        if override_rule:
            outline.append("层级覆盖规则: " + override_rule)
    frozen_contracts = payload.get("frozen_contracts")
    if isinstance(frozen_contracts, list) and frozen_contracts:
        outline.append(f"Frozen Contracts: {len(frozen_contracts)} 条")
    structured_contracts = payload.get("structured_object_contracts")
    if isinstance(structured_contracts, list) and structured_contracts:
        outline.append("结构化对象契约: " + ", ".join(
            str(entry.get("object", "")).strip()
            for entry in structured_contracts[:6]
            if isinstance(entry, dict) and str(entry.get("object", "")).strip()
        ))
    enum_freezes = _enum_freezes(payload)
    if enum_freezes:
        outline.append("枚举冻结: " + ", ".join(str(key).strip() for key in list(enum_freezes.keys())[:6] if str(key).strip()))
    semantic_inventory = payload.get("semantic_inventory")
    if isinstance(semantic_inventory, dict):
        semantic_sections = [
            ("actors", _count_list(semantic_inventory, "actors")),
            ("core_objects", _count_list(semantic_inventory, "core_objects")),
            ("core_states", _count_list(semantic_inventory, "core_states")),
            ("core_apis", _count_list(semantic_inventory, "core_apis")),
            ("core_outputs", _count_list(semantic_inventory, "core_outputs")),
            ("product_surfaces", _count_list(semantic_inventory, "product_surfaces")),
            ("operator_surfaces", _count_list(semantic_inventory, "operator_surfaces")),
            ("entry_points", _count_list(semantic_inventory, "entry_points")),
            ("commands", _count_list(semantic_inventory, "commands")),
            ("runtime_objects", _count_list(semantic_inventory, "runtime_objects")),
            ("states", _count_list(semantic_inventory, "states")),
            ("observability_surfaces", _count_list(semantic_inventory, "observability_surfaces")),
            ("constraints", _count_list(semantic_inventory, "constraints")),
            ("non_goals", _count_list(semantic_inventory, "non_goals")),
        ]
        outline.append("semantic_inventory 主体块: " + ", ".join(f"{name}[{count}]" for name, count in semantic_sections if count))
        state_focus = _semantic_inventory_items(semantic_inventory.get("core_states"), limit=2)
        if not state_focus:
            state_focus = _semantic_inventory_items(semantic_inventory.get("states"), limit=2)
        if state_focus:
            outline.append("semantic_inventory 状态焦点: " + "；".join(state_focus))
    if not outline:
        visible_keys = [key for key, value in payload.items() if value not in (None, "", [], {})]
        if visible_keys:
            outline.append("可见字段: " + ", ".join(visible_keys[:12]))
        generic_sections = []
        for field in ("roles", "main_flow", "deliverables", "open_technical_decisions"):
            count = _count_list(payload, field)
            if count:
                generic_sections.append(f"{field}[{count}]")
        if generic_sections:
            outline.append("主体块: " + ", ".join(generic_sections))
    return outline


def ssot_review_points(payload: dict[str, Any]) -> list[str]:
    points: list[str] = []
    artifact_type = str(payload.get("artifact_type", "")).strip()
    if artifact_type == "epic_freeze_package":
        semantic_lock = payload.get("semantic_lock")
        domain_type = ""
        if isinstance(semantic_lock, dict):
            domain_type = str(semantic_lock.get("domain_type", "")).strip().lower()
        source_refs = [str(item).strip() for item in payload.get("source_refs", []) if str(item).strip()] if isinstance(payload.get("source_refs"), list) else []
        decomposition_rules = [str(item).strip() for item in payload.get("decomposition_rules", []) if str(item).strip()] if isinstance(payload.get("decomposition_rules"), list) else []
        success_criteria = [str(item).strip() for item in payload.get("epic_success_criteria", []) if str(item).strip()] if isinstance(payload.get("epic_success_criteria"), list) else []
        product_slices = [str(item.get("name", "")).strip() for item in payload.get("product_behavior_slices", []) if isinstance(item, dict) and str(item.get("name", "")).strip()] if isinstance(payload.get("product_behavior_slices"), list) else []
        non_goals = [str(item).strip() for item in payload.get("non_goals", []) if str(item).strip()] if isinstance(payload.get("non_goals"), list) else []
        review_projection_epic = domain_type == "review_projection_rule"
        execution_runner_epic = domain_type == "execution_runner_rule"
        governance_runtime_epic = (
            bool((payload.get("rollout_requirement") or {}).get("required"))
            or any("ADR-018" in ref for ref in source_refs)
            or any(token in " ".join(product_slices + decomposition_rules + success_criteria).lower() for token in ("runner", "handoff", "formal publish", "governed skill", "adoption_e2e"))
        )
        if review_projection_epic:
            points.append("核对 product_behavior_slices 是否完整覆盖 Projection 生成、Authoritative Snapshot、Review Focus/Risk 提示与反馈回写，而不是混入新的 SSOT 真相源。")
            points.append("核对 actors_and_roles 是否把 reviewer、SSOT owner、projection generator 与 downstream designer 的职责边界讲清楚。")
            points.append("核对 decomposition_rules 是否明确要求下游围绕审核视图切片拆分，而不是扩张到 handoff orchestration 或 formal publication。")
            points.append("核对 epic_success_criteria 是否强调 Projection derived-only、non-authoritative、可回写但不可继承。")
            points.append("核对 source_refs 是否仍然锚定当前 Machine SSOT 与 gate 审核来源，没有把 Projection 自己变成权威来源。")
            return points
        if execution_runner_epic or governance_runtime_epic:
            if _count_list(payload, "product_behavior_slices"):
                points.append("核对 product_behavior_slices 是否完整覆盖用户入口、控制面、取件、派发、回写、监控等产品切片，而不是只剩抽象 runtime 结论。")
            if _count_list(payload, "actors_and_roles"):
                points.append("核对 actors_and_roles 是否把 gate owner、runner owner、CLI operator、workflow operator 的责任边界讲清楚。")
            if _count_list(payload, "decomposition_rules"):
                points.append("核对 decomposition_rules 是否明确要求下游按独立验收 FEAT 切片拆分，而不是回退成技术轴或实现顺序。")
            if _count_list(payload, "epic_success_criteria"):
                points.append("核对 epic_success_criteria 是否仍然锚定 approve -> ready job -> runner claim -> next skill invocation 这条主链。")
            if _count_list(payload, "source_refs"):
                points.append("核对 source_refs 是否仍完整覆盖 ADR-018 及其依赖 ADR，避免下游继承时丢来源。")
            return points
        if _count_list(payload, "product_behavior_slices"):
            points.append("核对 product_behavior_slices 是否准确覆盖最小建档主链、首轮建议释放、扩展画像渐进补全、设备连接后置与状态/存储边界统一这些产品行为切片。")
        if _count_list(payload, "actors_and_roles"):
            points.append("核对 actors_and_roles 是否仍然服务于当前建档题的用户角色，没有混入 gate owner、runner owner、CLI operator 等 runtime 模板角色。")
        if _count_list(payload, "decomposition_rules"):
            points.append("核对 Product Positioning、Capability Scope 与 decomposition_rules 是否都坚持产品能力抽象，没有退回“建立需求源”或其他 SRC 层语言。")
        if _count_list(payload, "epic_success_criteria"):
            points.append("核对 epic_success_criteria 是否锚定首日最小建档、首轮建议释放与增量补全这些业务结果，而不是 runtime 主链。")
        if non_goals:
            points.append("核对 non_goals 是否只保留建档题内边界，没有混入 rollout、migration、runner 或治理底座改造模板。")
        if _count_list(payload, "source_refs"):
            points.append("核对 source_refs 是否完整覆盖当前 SRC 与本轮审批来源，没有引用与当前产品题无关的 ADR/runtime 模板来源。")
        return points
    if artifact_type == "feat_freeze_package":
        if str(payload.get("bundle_intent", "")).strip():
            points.append("核对 bundle_intent 是否准确解释了为什么要拆成当前这组 FEAT，而不是更少或更多。")
        if _count_list(payload, "features"):
            points.append("核对 features 是否把 Runner 用户入口流、控制面流、运行监控流等用户可见模块完整拆出，而不是重新压回后台 runtime。")
        epic_context = payload.get("epic_context")
        if isinstance(epic_context, dict) and isinstance(epic_context.get("decomposition_rules"), list) and epic_context.get("decomposition_rules"):
            points.append("核对 epic_context.decomposition_rules 是否被当前 FEAT bundle 正确继承，没有把产品行为切片漂移成 TECH/TASK 粒度。")
        if isinstance(epic_context, dict) and isinstance(epic_context.get("epic_success_criteria"), list) and epic_context.get("epic_success_criteria"):
            points.append("核对当前 FEAT 组合能否支撑至少一条 gate approve -> ready job -> runner claim -> next skill invocation 的真实链路。")
        if _count_list(payload, "downstream_workflows") or _count_list(payload, "source_refs"):
            points.append("核对 downstream_workflows 与 source_refs 是否完整，确保后续 feat-to-tech / feat-to-testset 不会丢失权威继承链。")
        return points
    if artifact_type == "tech_design_package":
        points.append("核对 TECH 是否明确区分 handoff submission、gate pending visibility、decision return intake 三类实现责任，没有把 formalization/publication 混进来。")
        points.append("核对 state_model 与 interface_contracts 是否闭合，尤其 duplicate_submission、decision_return、reentry 的幂等与 fail-closed 语义。")
        points.append("核对 implementation_unit_mapping 是否把 carrier 放在统一 runtime，而不是散落到业务 skill 或 gate worker。")
        points.append("核对 downstream_handoff 是否足够支撑 tech_to_impl，不要求实现层再猜 handoff/queue 规则。")
        return points
    if artifact_type == "test_set_candidate_package":
        points.append("核对 TESTSET 是否只覆盖主链候选提交与交接流本身，没有越界去定义 formalization、admission 或 publication。")
        points.append("核对 duplicate submission、payload mismatch、missing payload、empty pending 这些 fail-closed 边界是否都有测试单元覆盖。")
        points.append("核对 acceptance_traceability 是否把每个 acceptance check 映射到至少一个可执行测试单元。")
        points.append("核对 downstream_target 与 required_environment_inputs 是否足够支撑后续 test_exec，而不是一份空壳 testset。")
        return points
    if artifact_type == "feature_impl_candidate_package":
        points.append("核对 IMPL 是否严格只实现 handoff submission、pending visibility、decision return intake 与 re-entry routing，没有越界把 formal publish 或 admission 混进来。")
        points.append("核对 implementation_steps 与冻结 touch set 是否集中在统一 carrier 上，没有扩成新的平台层或把责任散落到业务 skill。")
        points.append("核对 downstream_handoff、phase_inputs 与 acceptance_refs 是否足够支撑 feature delivery，而不是让下游再猜实现边界。")
        points.append("核对 evidence / smoke gate 是否覆盖 authoritative handoff、returned decision 与 re-entry directive，而不是只给 happy path。")
        return points
    if str(payload.get("problem_statement", "")).strip():
        points.append("核对 problem_statement 是否同时说明当前失控行为、为什么必须现在收敛、以及不收敛的后果。")
    semantic_layers = _semantic_layer_declaration(payload)
    if semantic_layers:
        points.append("核对文档语义层级是否显式声明 source_layer / bridge_layer / meta_layer，并确认 bridge_layer 不会覆盖 source_layer。")
    if _count_list(payload, "frozen_contracts"):
        points.append("核对 Frozen Contracts 是否已经把首进主链、设备不阻塞、单轴 running_level、injury 风险门槛、增量补全等硬约束集中冻结。")
    if _count_list(payload, "structured_object_contracts"):
        points.append("核对结构化对象契约是否把 minimal_onboarding_page、running_level、recent_injury_status、onboarding_state_model 等对象写成机器可继承的固定结构。")
    if _enum_freezes(payload):
        points.append("核对枚举冻结是否已经给 running_level / recent_injury_status 提供稳定枚举和值语义，避免下游名称不变但语义漂移。")
    semantic_inventory = payload.get("semantic_inventory")
    if isinstance(semantic_inventory, dict):
        states = _semantic_inventory_items(semantic_inventory.get("core_states"), limit=3)
        if not states:
            states = _semantic_inventory_items(semantic_inventory.get("states"), limit=3)
        if states:
            points.append("核对 semantic_inventory.states 是否把 running_level、profile_minimal_done、initial_plan_ready 这类状态口径拆清，不要混入训练阶段、当前能力或历史经历。")
        interfaces: list[str] = []
        for field in ("core_apis", "core_outputs", "product_surfaces", "operator_surfaces", "entry_points", "commands", "runtime_objects", "observability_surfaces"):
            interfaces.extend(_semantic_inventory_items(semantic_inventory.get(field), limit=2))
        interfaces.extend(_semantic_inventory_items(payload.get("operator_surface_inventory"), limit=2))
        if interfaces:
            points.append("核对 semantic_inventory 的产品/操作者/命令面是否已显式列出关键接口边界，避免 brief 只看见状态修复却看不见可执行入口。")
        else:
            points.append("当前 semantic_inventory 里的产品/操作者/命令面仍然很空；如果本轮修复涉及接口边界，请补到显式列表里，否则 brief 只能读到状态而读不到执行面。")
        if _semantic_inventory_items(semantic_inventory.get("constraints"), limit=1):
            points.append("核对 semantic_inventory.constraints 是否与 key_constraints / out_of_scope 保持同一口径，避免语义层与治理层打架。")
    if _count_list(payload, "key_constraints") or _count_list(payload, "governance_change_summary"):
        points.append("核对 key_constraints、governance_change_summary、bridge_context.downstream_inheritance_requirements 三者是否表达一致，没有互相打架。")
    if _count_list(payload, "downstream_derivation_requirements"):
        points.append("核对 downstream_derivation_requirements 是否足够具体，能够直接约束后续 EPIC/FEAT/TASK，而不是泛泛而谈。")
    if _count_list(payload, "in_scope") or _count_list(payload, "out_of_scope"):
        points.append("核对 in_scope / out_of_scope 边界是否干净，避免在 SRC 层混入实现细节，或把关键治理对象遗漏到范围外。")
    bridge_context = payload.get("bridge_context")
    if isinstance(bridge_context, dict) and (
        isinstance(bridge_context.get("current_failure_modes"), list) or isinstance(bridge_context.get("acceptance_impact"), list)
    ):
        points.append("核对 bridge_context.current_failure_modes 与 acceptance_impact 是否足以支撑 reviewer 的审批判断，而不是只给抽象结论。")
    if _count_list(payload, "source_refs") or (isinstance(bridge_context, dict) and isinstance(bridge_context.get("governed_by_adrs"), list)):
        points.append("核对 source_refs / governed_by_adrs 是否覆盖本次治理依据，避免后续对象继承时丢失 ADR 来源。")
    if _count_list(payload, "uncertainties"):
        points.append("关注 uncertainties 里的占位和保守假设，确认这些空白不会影响本轮是否应该批准。")
    if not points:
        if str(payload.get("product_summary", "")).strip():
            points.append("核对 product_summary 是否准确说明候选对象的业务意图，而不是只有空泛结论。")
        if _count_list(payload, "main_flow"):
            points.append("核对 main_flow 是否覆盖 reviewer 需要理解的主链步骤，没有遗漏关键流程。")
        if str(payload.get("frozen_downstream_boundary", "")).strip():
            points.append("核对 frozen_downstream_boundary 是否清楚说明哪些内容可继承、哪些内容仅供评审参考。")
        if _count_list(payload, "open_technical_decisions"):
            points.append("核对 open_technical_decisions 是否会影响本轮审批，如果会，当前证据是否已经足够。")
    return points


def _first_items(payload: dict[str, Any], field: str, *, limit: int = 3) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for raw in value:
        if not isinstance(raw, str):
            continue
        text = raw.strip()
        if not text:
            continue
        items.append(text)
        if len(items) >= limit:
            break
    return items


def _join_items(items: list[str]) -> str:
    return "；".join(items)


def _semantic_layer_markdown(payload: dict[str, Any]) -> list[str]:
    layers = _semantic_layer_declaration(payload)
    if not layers:
        return []
    lines = ["### 文档语义层级", ""]
    for layer_name in ("source_layer", "bridge_layer", "meta_layer"):
        details = layers.get(layer_name)
        if not isinstance(details, dict):
            continue
        role = str(details.get("role", "")).strip()
        if role:
            lines.append(f"- {layer_name}: {role}")
        authoritative_fields = _render_mapping_items(details.get("authoritative_fields"))
        if authoritative_fields:
            lines.append(f"  authoritative_fields: {authoritative_fields}")
        derived_fields = _render_mapping_items(details.get("derived_fields"))
        if derived_fields:
            lines.append(f"  derived_fields: {derived_fields}")
        fields = _render_mapping_items(details.get("fields"))
        if fields:
            lines.append(f"  fields: {fields}")
        rule = str(details.get("consumption_rule", "")).strip()
        if rule:
            lines.append(f"  consumption_rule: {rule}")
    precedence = _render_mapping_items(layers.get("precedence_order"))
    if precedence:
        lines.append(f"- precedence_order: {precedence}")
    override_rule = str(layers.get("override_rule", "")).strip()
    if override_rule:
        lines.append(f"- override_rule: {override_rule}")
    return lines


def _frozen_contracts_markdown(payload: dict[str, Any]) -> list[str]:
    contracts = payload.get("frozen_contracts")
    if not isinstance(contracts, list) or not contracts:
        return []
    lines = ["### Frozen Contracts", ""]
    for entry in contracts:
        if not isinstance(entry, dict):
            continue
        contract_id = str(entry.get("id", "")).strip()
        statement = str(entry.get("statement", "")).strip()
        if contract_id and statement:
            lines.append(f"- {contract_id}: {statement}")
        applies_to = _render_mapping_items(entry.get("applies_to"))
        if applies_to:
            lines.append(f"  applies_to: {applies_to}")
        authoritative_layer = str(entry.get("authoritative_layer", "")).strip()
        if authoritative_layer:
            lines.append(f"  authoritative_layer: {authoritative_layer}")
    return lines


def _structured_object_contracts_markdown(payload: dict[str, Any]) -> list[str]:
    contracts = payload.get("structured_object_contracts")
    if not isinstance(contracts, list) or not contracts:
        return []
    lines = ["### 结构化对象契约", ""]
    field_order = (
        "purpose",
        "required_fields",
        "optional_fields",
        "canonical_field_policy",
        "transitional_input_aliases",
        "semantic_axis",
        "allowed_values",
        "value_definitions",
        "forbidden_semantics",
        "required_for_first_advice",
        "cannot_be_deferred",
        "downstream_usage",
        "primary_state",
        "capability_flags",
        "constraints",
        "minimum_outputs",
        "blocked_by",
        "deferred_inputs",
        "canonical_owner",
        "physical_fields",
        "forbidden_duplication",
        "authoritative_conflict_rule",
        "forbidden_fields",
        "completion_effect",
    )
    for entry in contracts:
        if not isinstance(entry, dict):
            continue
        object_name = str(entry.get("object", "")).strip()
        if not object_name:
            continue
        lines.append(f"- object: {object_name}")
        for field in field_order:
            rendered = _render_mapping_items(entry.get(field))
            if rendered:
                lines.append(f"  {field}: {rendered}")
    return lines


def _enum_freezes_markdown(payload: dict[str, Any]) -> list[str]:
    freezes = _enum_freezes(payload)
    if not freezes:
        return []
    lines = ["### 枚举冻结", ""]
    for field_name, details in freezes.items():
        if not isinstance(details, dict):
            continue
        lines.append(f"- field: {field_name}")
        for key in ("semantic_axis", "allowed_values", "value_definitions", "forbidden_semantics", "used_for"):
            rendered = _render_mapping_items(details.get(key))
            if rendered:
                lines.append(f"  {key}: {rendered}")
    return lines


def ssot_fulltext_markdown(payload: dict[str, Any]) -> str:
    artifact_type = str(payload.get("artifact_type", "")).strip()
    if artifact_type == "epic_freeze_package":
        markdown = _epic_freeze_fulltext_markdown(payload)
        if markdown:
            return markdown
    if artifact_type == "feat_freeze_package":
        markdown = _feat_freeze_fulltext_markdown(payload)
        if markdown:
            return markdown
    if artifact_type == "tech_design_package":
        markdown = _tech_design_fulltext_markdown(payload)
        if markdown:
            return markdown
    if artifact_type == "test_set_candidate_package":
        markdown = _test_set_fulltext_markdown(payload)
        if markdown:
            return markdown
    if artifact_type == "feature_impl_candidate_package":
        markdown = _impl_bundle_fulltext_markdown(payload)
        if markdown:
            return markdown
    paragraphs: list[str] = []
    title = str(payload.get("title", "")).strip()
    artifact_type = str(payload.get("artifact_type", "")).strip()
    status = str(payload.get("status", "")).strip()
    input_type = str(payload.get("input_type", "")).strip()
    intro_parts = []
    if artifact_type:
        intro_parts.append(f"这是一份 `{artifact_type}` 候选稿")
    else:
        intro_parts.append("这是一份候选稿")
    if title:
        intro_parts.append(f"标题是“{title}”")
    if status:
        intro_parts.append(f"当前状态是 `{status}`")
    if input_type:
        intro_parts.append(f"来源类型是 `{input_type}`")
    paragraphs.append("，".join(intro_parts) + "。")

    problem_statement = str(payload.get("problem_statement", "")).strip()
    if problem_statement:
        paragraphs.append("它要解决的问题是：" + problem_statement)
    semantic_inventory_paragraphs = _semantic_inventory_excerpt(payload)
    if semantic_inventory_paragraphs:
        paragraphs.append("另外，语义清单已经补进了这些修复信号：" + "；".join(semantic_inventory_paragraphs) + "。")

    target_users = _first_items(payload, "target_users", limit=5)
    trigger_scenarios = _first_items(payload, "trigger_scenarios", limit=3)
    if target_users or trigger_scenarios:
        sentence = "这份稿子主要约束或服务于"
        if target_users:
            sentence += _join_items(target_users)
        if trigger_scenarios:
            if target_users:
                sentence += "；"
            sentence += "典型触发场景包括" + _join_items(trigger_scenarios)
        paragraphs.append(sentence + "。")

    business_drivers = _first_items(payload, "business_drivers", limit=3)
    if business_drivers:
        paragraphs.append("它为什么值得现在审，是因为：" + _join_items(business_drivers) + "。")

    bridge_summary = _first_items(payload, "bridge_summary", limit=2)
    if bridge_summary:
        paragraphs.append("这份稿子的核心主张可以概括为：" + _join_items(bridge_summary) + "。")

    key_constraints = _first_items(payload, "key_constraints", limit=3)
    if key_constraints:
        paragraphs.append("它要求下游必须遵守的关键约束是：" + _join_items(key_constraints) + "。")

    expected_outcomes = _first_items(payload, "expected_outcomes", limit=3)
    if expected_outcomes:
        paragraphs.append("如果这份稿子成立，期望看到的结果是：" + _join_items(expected_outcomes) + "。")

    derivation = _first_items(payload, "downstream_derivation_requirements", limit=3)
    if derivation:
        paragraphs.append("对下游派生链路来说，它实际上在要求后续对象：" + _join_items(derivation) + "。")

    in_scope = _first_items(payload, "in_scope", limit=3)
    out_of_scope = _first_items(payload, "out_of_scope", limit=3)
    if in_scope or out_of_scope:
        sentence = []
        if in_scope:
            sentence.append("本轮明确纳入范围的是：" + _join_items(in_scope) + "。")
        if out_of_scope:
            sentence.append("明确不在本轮处理范围的是：" + _join_items(out_of_scope) + "。")
        paragraphs.append(" ".join(sentence))

    bridge_context = payload.get("bridge_context")
    if isinstance(bridge_context, dict):
        current_failure_modes = _first_items(bridge_context, "current_failure_modes", limit=3)
        acceptance_impact = _first_items(bridge_context, "acceptance_impact", limit=3)
        if current_failure_modes:
            paragraphs.append("从治理视角看，当前主要失控点包括：" + _join_items(current_failure_modes) + "。")
        if acceptance_impact:
            paragraphs.append("所以 reviewer 本轮审批时，至少要确认：" + _join_items(acceptance_impact) + "。")

    governance_summary = _first_items(payload, "governance_change_summary", limit=3)
    if governance_summary:
        paragraphs.append("如果把全文压成一句治理结论，它要表达的是：" + _join_items(governance_summary) + "。")

    uncertainties = _first_items(payload, "uncertainties", limit=3)
    if uncertainties:
        paragraphs.append("当前文稿里仍有这些需要审阅时留意的不确定项：" + _join_items(uncertainties) + "。")

    if not paragraphs:
        return ""

    lines = ["## Machine SSOT 人类友好全文", ""]
    lines.extend(paragraphs)
    extra_sections = [
        _semantic_layer_markdown(payload),
        _frozen_contracts_markdown(payload),
        _structured_object_contracts_markdown(payload),
        _enum_freezes_markdown(payload),
    ]
    for section in extra_sections:
        if section:
            lines.extend(["", *section])
    return "\n\n".join(lines) + "\n"


def _epic_freeze_fulltext_markdown(payload: dict[str, Any]) -> str:
    title = str(payload.get("title", "")).strip()
    workflow_run_id = str(payload.get("workflow_run_id", "")).strip()
    downstream_workflow = str(payload.get("downstream_workflow", "")).strip()
    lines = ["## Machine SSOT 人类友好全文", ""]
    intro = "这是一份 `epic_freeze_package` 候选稿"
    if title:
        intro += f"，标题是“{title}”"
    if workflow_run_id:
        intro += f"，本次 run 是 `{workflow_run_id}`"
    lines.append(intro + "。")
    business_goal = str(payload.get("business_goal", "")).strip()
    if business_goal:
        lines.extend(["", business_goal])
    positioning = str(payload.get("product_positioning", "")).strip()
    if positioning:
        lines.extend(["", "它在产品链路里的定位是：" + positioning])
    roles = _role_summaries(payload.get("actors_and_roles"), limit=6)
    if roles:
        lines.extend(["", "### 关键角色与责任", ""])
        lines.extend(f"- {item}" for item in roles)
    slices = _slice_summaries(payload.get("product_behavior_slices"), limit=8)
    if slices:
        lines.extend(["", "### 本轮冻结的产品切片", ""])
        lines.extend(f"- {item}" for item in slices)
    success = _first_items(payload, "epic_success_criteria", limit=5)
    if success:
        lines.extend(["", "### 通过这轮审批后，应该能看到什么", ""])
        lines.extend(f"- {item}" for item in success)
    rules = _first_items(payload, "decomposition_rules", limit=4)
    if rules:
        lines.extend(["", "### 对下游 FEAT 派生的硬约束", ""])
        lines.extend(f"- {item}" for item in rules)
    non_goals = _first_items(payload, "non_goals", limit=4)
    if non_goals:
        lines.extend(["", "### 本轮明确不做什么", ""])
        lines.extend(f"- {item}" for item in non_goals)
    if downstream_workflow:
        lines.extend(["", f"下游会继续交接给 `{downstream_workflow}`。"])
    return "\n".join(lines) + "\n"


def _feat_freeze_fulltext_markdown(payload: dict[str, Any]) -> str:
    title = str(payload.get("title", "")).strip()
    workflow_run_id = str(payload.get("workflow_run_id", "")).strip()
    feat_count = _count_list(payload, "features") or _count_list(payload, "feat_refs")
    lines = ["## Machine SSOT 人类友好全文", ""]
    intro = "这是一份 `feat_freeze_package` 候选稿"
    if title:
        intro += f"，标题是“{title}”"
    if workflow_run_id:
        intro += f"，本次 run 是 `{workflow_run_id}`"
    if feat_count:
        intro += f"，当前共拆出 {feat_count} 个 FEAT"
    lines.append(intro + "。")
    bundle_intent = str(payload.get("bundle_intent", "")).strip()
    if bundle_intent:
        lines.extend(["", "这份 FEAT bundle 的拆分意图是：" + bundle_intent])
    epic_context = payload.get("epic_context")
    if isinstance(epic_context, dict):
        business_goal = str(epic_context.get("business_goal", "")).strip()
        if business_goal:
            lines.extend(["", "它继承的上位业务目标是：" + business_goal])
        positioning = str(epic_context.get("product_positioning", "")).strip()
        if positioning:
            lines.extend(["", "从产品定位上看：" + positioning])
        roles = _role_summaries(epic_context.get("actors_and_roles"), limit=6)
        if roles:
            lines.extend(["", "### 这轮 FEAT 面向的关键角色", ""])
            lines.extend(f"- {item}" for item in roles)
    features = _feature_summaries(payload.get("features"), limit=10)
    if features:
        lines.extend(["", "### 本轮实际拆出的 FEAT", ""])
        lines.extend(f"- {item}" for item in features)
    downstream_workflows = _first_items(payload, "downstream_workflows", limit=4)
    if downstream_workflows:
        lines.extend(["", "### 这些 FEAT 接下来会交给哪些下游工作流", ""])
        lines.extend(f"- {item}" for item in downstream_workflows)
    if isinstance(epic_context, dict):
        success = _first_items(epic_context, "epic_success_criteria", limit=4)
        if success:
            lines.extend(["", "### Reviewer 本轮最该确认的成功标准", ""])
            lines.extend(f"- {item}" for item in success)
        rules = _first_items(epic_context, "decomposition_rules", limit=4)
        if rules:
            lines.extend(["", "### 这组 FEAT 必须继承的拆分规则", ""])
            lines.extend(f"- {item}" for item in rules)
    non_goals = _first_items(payload, "bundle_shared_non_goals", limit=5)
    if non_goals:
        lines.extend(["", "### 这组 FEAT 明确不应该漂向哪里", ""])
        lines.extend(f"- {item}" for item in non_goals)
    return "\n".join(lines) + "\n"


def _tech_design_fulltext_markdown(payload: dict[str, Any]) -> str:
    lines = ["## Machine SSOT 人类友好全文", ""]
    title = str(payload.get("title", "")).strip()
    workflow_run_id = str(payload.get("workflow_run_id", "")).strip()
    intro = "这是一份 `tech_design_package` 候选稿"
    if title:
        intro += f"，标题是“{title}”"
    if workflow_run_id:
        intro += f"，本次 run 是 `{workflow_run_id}`"
    lines.append(intro + "。")
    selected_feat = payload.get("selected_feat")
    if isinstance(selected_feat, dict):
        goal = str(selected_feat.get("goal", "")).strip()
        if goal:
            lines.extend(["", "它要落地的 FEAT 目标是：" + goal])
    tech_design = payload.get("tech_design")
    if isinstance(tech_design, dict):
        design_focus = _first_items(tech_design, "design_focus", limit=2)
        if design_focus:
            lines.extend(["", "### 这份 TECH 主要在实现什么", ""])
            lines.extend(f"- {item}" for item in design_focus)
        architecture = _first_items(tech_design, "implementation_architecture", limit=3)
        if architecture:
            lines.extend(["", "### 实现边界与职责分工", ""])
            lines.extend(f"- {item}" for item in architecture)
        module_plan = _first_items(tech_design, "module_plan", limit=5)
        if module_plan:
            lines.extend(["", "### 计划落到哪些模块", ""])
            lines.extend(f"- {item}" for item in module_plan)
        state_model = _first_items(tech_design, "state_model", limit=4)
        if state_model:
            lines.extend(["", "### 核心状态机", ""])
            lines.extend(f"- {item}" for item in state_model)
        contracts = _first_items(tech_design, "interface_contracts", limit=3)
        if contracts:
            lines.extend(["", "### 关键接口合同", ""])
            lines.extend(f"- {item}" for item in contracts)
        strategy = _first_items(tech_design, "implementation_strategy", limit=3)
        if strategy:
            lines.extend(["", "### 实施顺序", ""])
            lines.extend(f"- {item}" for item in strategy)
    downstream = payload.get("downstream_handoff")
    if isinstance(downstream, dict):
        target_workflow = str(downstream.get("target_workflow", "")).strip()
        if target_workflow:
            lines.extend(["", f"下游会继续交接给 `{target_workflow}`。"])
    return "\n".join(lines) + "\n"


def _test_set_fulltext_markdown(payload: dict[str, Any]) -> str:
    lines = ["## Machine SSOT 人类友好全文", ""]
    title = str(payload.get("title", "")).strip()
    workflow_run_id = str(payload.get("workflow_run_id", "")).strip()
    intro = "这是一份 `test_set_candidate_package` 候选稿"
    if title:
        intro += f"，标题是“{title}”"
    if workflow_run_id:
        intro += f"，本次 run 是 `{workflow_run_id}`"
    lines.append(intro + "。")
    selected_feat = payload.get("selected_feat")
    if isinstance(selected_feat, dict):
        goal = str(selected_feat.get("goal", "")).strip()
        if goal:
            lines.extend(["", "它要验证的 FEAT 目标是：" + goal])
    requirement_analysis = payload.get("requirement_analysis")
    if isinstance(requirement_analysis, dict):
        coverage_scope = _first_items(requirement_analysis, "coverage_scope", limit=3)
        if coverage_scope:
            lines.extend(["", "### 这份 TESTSET 要覆盖什么", ""])
            lines.extend(f"- {item}" for item in coverage_scope)
        exclusions = _first_items(requirement_analysis, "coverage_exclusions", limit=3)
        if exclusions:
            lines.extend(["", "### 明确不覆盖什么", ""])
            lines.extend(f"- {item}" for item in exclusions)
    strategy_draft = payload.get("strategy_draft")
    if isinstance(strategy_draft, dict):
        test_units = _test_unit_summaries(strategy_draft.get("test_units"), limit=6)
        if test_units:
            lines.extend(["", "### 关键测试单元", ""])
            lines.extend(f"- {item}" for item in test_units)
    test_set = payload.get("test_set")
    if isinstance(test_set, dict):
        pass_criteria = _first_items(test_set, "pass_criteria", limit=3)
        if pass_criteria:
            lines.extend(["", "### 通过标准", ""])
            lines.extend(f"- {item}" for item in pass_criteria)
        environment_assumptions = _first_items(test_set, "environment_assumptions", limit=4)
        if environment_assumptions:
            lines.extend(["", "### 执行前置环境假设", ""])
            lines.extend(f"- {item}" for item in environment_assumptions)
    downstream_target = str(payload.get("downstream_target", "")).strip()
    if downstream_target:
        lines.extend(["", f"下游执行目标是 `{downstream_target}`。"])
    return "\n".join(lines) + "\n"


def _impl_bundle_fulltext_markdown(payload: dict[str, Any]) -> str:
    lines = ["## Machine SSOT 人类友好全文", ""]
    title = str(payload.get("title", "")).strip()
    workflow_run_id = str(payload.get("workflow_run_id", "")).strip()
    intro = "这是一份 `feature_impl_candidate_package` 候选稿"
    if title:
        intro += f"，标题是“{title}”"
    if workflow_run_id:
        intro += f"，本次 run 是 `{workflow_run_id}`"
    lines.append(intro + "。")

    selected_scope = payload.get("selected_scope")
    if isinstance(selected_scope, dict):
        goal = str(selected_scope.get("goal", "")).strip()
        if goal:
            lines.extend(["", "它要落地的实现目标是：" + goal])
        scope = _first_items(selected_scope, "scope", limit=4)
        if scope:
            lines.extend(["", "### 这份 IMPL 具体覆盖什么", ""])
            lines.extend(f"- {item}" for item in scope)
        constraints = _first_items(selected_scope, "constraints", limit=4)
        if constraints:
            lines.extend(["", "### 必须继承的实现约束", ""])
            lines.extend(f"- {item}" for item in constraints)
        dependencies = _first_items(selected_scope, "dependencies", limit=3)
        if dependencies:
            lines.extend(["", "### 与相邻对象的边界", ""])
            lines.extend(f"- {item}" for item in dependencies)

    workstream_assessment = payload.get("workstream_assessment")
    if isinstance(workstream_assessment, dict):
        lines.extend(["", "### 需要落到哪些执行面", ""])
        lines.append(f"- frontend_required: {bool(workstream_assessment.get('frontend_required'))}")
        lines.append(f"- backend_required: {bool(workstream_assessment.get('backend_required'))}")
        lines.append(f"- migration_required: {bool(workstream_assessment.get('migration_required'))}")
        rationale = workstream_assessment.get("rationale")
        if isinstance(rationale, dict):
            for label in ("frontend", "backend", "migration"):
                items = rationale.get(label)
                if isinstance(items, list):
                    for item in items[:2]:
                        if isinstance(item, str) and item.strip():
                            lines.append(f"- {label}: {item.strip()}")

    upstream_refs = payload.get("upstream_design_refs")
    if isinstance(upstream_refs, dict):
        frozen = upstream_refs.get("frozen_decisions")
        if isinstance(frozen, dict):
            unit_mapping = _first_items(frozen, "implementation_unit_mapping", limit=5)
            if unit_mapping:
                lines.extend(["", "### 计划落到哪些模块", ""])
                lines.extend(f"- {item}" for item in unit_mapping)
            state_model = _first_items(frozen, "state_model", limit=4)
            if state_model:
                lines.extend(["", "### 核心状态机", ""])
                lines.extend(f"- {item}" for item in state_model)
            contracts = _first_items(frozen, "interface_contracts", limit=3)
            if contracts:
                lines.extend(["", "### 冻结接口合同", ""])
                lines.extend(f"- {item}" for item in contracts)
            main_sequence = _first_items(frozen, "main_sequence", limit=6)
            if main_sequence:
                lines.extend(["", "### 主实施顺序", ""])
                lines.extend(f"- {item}" for item in main_sequence)

    implementation_steps = payload.get("implementation_steps")
    if isinstance(implementation_steps, list) and implementation_steps:
        lines.extend(["", "### 实施任务拆分", ""])
        for entry in implementation_steps[:4]:
            if not isinstance(entry, dict):
                continue
            title_text = str(entry.get("title", "")).strip()
            work_text = str(entry.get("work", "")).strip()
            if title_text and work_text:
                lines.append(f"- {title_text}: {work_text}")
            elif title_text:
                lines.append(f"- {title_text}")

    downstream = payload.get("downstream_handoff")
    if isinstance(downstream, dict):
        lines.extend(["", "### 交付与验收", ""])
        template_id = str(downstream.get("target_template_id", "")).strip()
        if template_id:
            lines.append(f"- 目标交付模板: `{template_id}`")
        primary_artifact = str(downstream.get("primary_artifact_ref", "")).strip()
        if primary_artifact:
            lines.append(f"- 主交付物: `{primary_artifact}`")
        acceptance_refs = downstream.get("acceptance_refs")
        if isinstance(acceptance_refs, list) and acceptance_refs:
            labels = [str(item).strip() for item in acceptance_refs if str(item).strip()]
            if labels:
                lines.append(f"- 验收引用: {_join_items(labels)}")
        phase_inputs = downstream.get("phase_inputs")
        if isinstance(phase_inputs, dict):
            visible_inputs = [f"{key}[{len(value)}]" for key, value in phase_inputs.items() if isinstance(value, list) and value]
            if visible_inputs:
                lines.append(f"- 交付输入: {', '.join(visible_inputs)}")

    return "\n".join(lines) + "\n"


def request_markdown(request: dict[str, Any]) -> str:
    lines = [
        f"# {request['title']}",
        "",
        "## 待审批对象",
        "",
        f"- pending_human_decision_ref: {request['pending_human_decision_ref']}",
        f"- decision_target: {request['decision_target']}",
        f"- machine_ssot_ref: {request['machine_ssot_ref']}",
        "",
        "## 需要你做的决定",
        "",
        f"- {request['decision_question']}",
        "",
        "## 建议关注点",
        "",
    ]
    lines.extend(f"- {item}" for item in request["focus_points"])
    lines.extend(["", "## 可直接回复的格式", "", *[f"- {item}" for item in request["reply_examples"]]])
    if request["ssot_excerpt"]:
        lines.extend(["", "## Machine SSOT 摘要", ""])
        lines.extend(f"- {item}" for item in request["ssot_excerpt"])
    if request.get("ssot_fulltext_markdown"):
        lines.extend(["", request["ssot_fulltext_markdown"].rstrip()])
    if request.get("ssot_outline"):
        lines.extend(["", "## Machine SSOT 文件骨架", ""])
        lines.extend(f"- {item}" for item in request["ssot_outline"])
    if request.get("review_checkpoints"):
        lines.extend(["", "## 关键待审阅点", ""])
        lines.extend(f"- {item}" for item in request["review_checkpoints"])
    return "\n".join(lines) + "\n"


def review_summary(request: dict[str, Any], *, status: str = "") -> dict[str, Any]:
    return {
        "title": request.get("title", ""),
        "status": status or "",
        "pending_human_decision_ref": request.get("pending_human_decision_ref", ""),
        "decision_target": request.get("decision_target", ""),
        "machine_ssot_ref": request.get("machine_ssot_ref", ""),
        "decision_question": request.get("decision_question", ""),
        "focus_points": list(request.get("focus_points", [])),
        "allowed_actions": list(request.get("allowed_actions", [])),
        "reply_examples": list(request.get("reply_examples", [])),
        "basis_refs_hint": list(request.get("basis_refs_hint", [])),
        "ssot_excerpt": list(request.get("ssot_excerpt", [])),
        "ssot_fulltext_markdown": str(request.get("ssot_fulltext_markdown", "")),
        "ssot_outline": list(request.get("ssot_outline", [])),
        "review_checkpoints": list(request.get("review_checkpoints", [])),
    }


def human_brief_payload(request: dict[str, Any], *, status: str = "") -> dict[str, Any]:
    return {
        "status": status or "",
        "markdown": request_markdown(request),
        "summary": review_summary(request, status=status),
    }


def round_state_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / "round-state.json"


def request_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / "human-decision-request.json"


def submission_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / "human-decision-submission.json"


def refresh_request_brief(repo_root: Path, artifacts_dir: Path) -> dict[str, Any]:
    current_request_path = request_path(artifacts_dir)
    if not current_request_path.exists():
        return {}
    request = load_json(current_request_path)
    machine_ssot_ref = str(request.get("machine_ssot_ref", "")).strip()
    brief = load_ssot_brief(repo_root, machine_ssot_ref)
    changed = False
    field_map = {
        "ssot_excerpt": "excerpt",
        "ssot_outline": "outline",
        "review_checkpoints": "review_points",
    }
    for field, brief_key in field_map.items():
        new_value = list(brief.get(brief_key, []))
        if new_value and new_value != list(request.get(field, [])):
            request[field] = new_value
            changed = True
    fulltext_markdown = str(brief.get("fulltext_markdown", "")).strip()
    if fulltext_markdown and fulltext_markdown != str(request.get("ssot_fulltext_markdown", "")).strip():
        request["ssot_fulltext_markdown"] = fulltext_markdown
        changed = True
    if changed:
        dump_json(current_request_path, request)
        (artifacts_dir / "human-decision-request.md").write_text(request_markdown(request), encoding="utf-8")
    return request


def proposal_data(repo_root: Path, handoff: dict[str, Any]) -> dict[str, Any]:
    proposal_ref = str(handoff.get("proposal_ref", "")).strip()
    if not proposal_ref:
        return {}
    proposal_path = Path(proposal_ref) if Path(proposal_ref).is_absolute() else (repo_root / proposal_ref)
    if not proposal_path.exists():
        return {}
    try:
        return load_json(proposal_path)
    except Exception:
        return {}


def registry_candidate_ref_for_payload(repo_root: Path, payload_path: Path) -> str:
    registry_dir = repo_root / "artifacts" / "registry"
    if not registry_dir.exists():
        return repo_relative(repo_root, payload_path)
    managed_variants = path_variants(repo_relative(repo_root, payload_path), repo_root) | path_variants(str(payload_path), repo_root)
    source_dir_variants = path_variants(repo_relative(repo_root, payload_path.parent), repo_root) | path_variants(str(payload_path.parent), repo_root)
    for registry_path in sorted(registry_dir.glob("*.json")):
        try:
            record = load_json(registry_path)
        except Exception:
            continue
        managed_artifact_ref = str(record.get("managed_artifact_ref", "")).strip()
        artifact_ref = str(record.get("artifact_ref", "")).strip()
        if not managed_artifact_ref or not artifact_ref:
            continue
        metadata = record.get("metadata", {})
        source_package_ref = str(metadata.get("source_package_ref", "")).strip() if isinstance(metadata, dict) else ""
        if path_variants(managed_artifact_ref, repo_root) & managed_variants:
            return artifact_ref
        if source_package_ref and (path_variants(source_package_ref, repo_root) & source_dir_variants):
            return artifact_ref
    return repo_relative(repo_root, payload_path)


def synthetic_gate_ready_package(repo_root: Path, artifacts_dir: Path, handoff: dict[str, Any], payload_path: Path) -> Path:
    proposal = proposal_data(repo_root, handoff)
    supporting_refs = proposal.get("supporting_artifact_refs", [])
    evidence_refs = proposal.get("evidence_bundle_refs", [])
    candidate_ref = ""
    machine_ssot_ref = ""
    if payload_path.name.endswith(".json"):
        try:
            payload_json = load_json(payload_path)
        except Exception:
            payload_json = {}
        if isinstance(payload_json, dict):
            payload_block = payload_json.get("payload")
            if isinstance(payload_block, dict):
                candidate_ref = str(payload_block.get("candidate_ref", "")).strip()
                machine_ssot_ref = str(payload_block.get("machine_ssot_ref", "")).strip()
    acceptance_ref = ""
    if isinstance(supporting_refs, list):
        for ref in supporting_refs:
            ref_str = str(ref)
            if ref_str.endswith("acceptance-report.json"):
                acceptance_ref = ref_str
                break
        if not acceptance_ref and supporting_refs:
            acceptance_ref = str(supporting_refs[0])
    evidence_ref = str(evidence_refs[0]) if isinstance(evidence_refs, list) and evidence_refs else ""
    if not evidence_ref:
        evidence_ref = str(handoff.get("trace_context_ref", ""))
    package_path = artifacts_dir / "synthetic-gate-ready-package.json"
    dump_json(
        package_path,
        {
            "trace": dict(handoff.get("trace", {})),
            "payload": {
                "candidate_ref": candidate_ref or registry_candidate_ref_for_payload(repo_root, payload_path),
                "machine_ssot_ref": machine_ssot_ref or repo_relative(repo_root, payload_path),
                "acceptance_ref": acceptance_ref,
                "evidence_bundle_ref": evidence_ref,
                "proposal_ref": str(handoff.get("proposal_ref", "")),
                "handoff_ref": str(handoff.get("gate_pending_ref") or handoff.get("handoff_ref", "")),
            },
            "synthetic_from_handoff": True,
        },
    )
    return package_path


def refresh_round_input_if_needed(repo_root: Path, artifacts_dir: Path, state: dict[str, Any]) -> Path:
    input_ref = str(state.get("input_ref", "")).strip()
    input_path = repo_root / Path(input_ref)
    if not input_ref or not input_path.exists():
        return input_path
    try:
        payload = load_json(input_path)
    except Exception:
        return input_path
    if not payload.get("synthetic_from_handoff"):
        return input_path
    handoff_ref = str(state.get("handoff_ref", "")).strip()
    if not handoff_ref:
        return input_path
    handoff_path = repo_root / handoff_ref
    if not handoff_path.exists():
        return input_path
    handoff = load_json(handoff_path)
    payload_ref = str(handoff.get("payload_ref", "")).strip()
    if not payload_ref:
        return input_path
    payload_path = Path(payload_ref) if Path(payload_ref).is_absolute() else (repo_root / payload_ref)
    if not payload_path.exists():
        return input_path
    return synthetic_gate_ready_package(repo_root, artifacts_dir, handoff, payload_path)
