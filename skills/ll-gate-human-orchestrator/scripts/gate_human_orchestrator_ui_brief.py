#!/usr/bin/env python3
"""UI spec specific human-friendly brief rendering."""

from __future__ import annotations

from typing import Any


def ui_spec_fulltext_markdown(payload: dict[str, Any]) -> str:
    if str(payload.get("artifact_type", "")).strip() != "ui_spec_package":
        return ""
    ui_specs = payload.get("ui_specs")
    if not isinstance(ui_specs, list) or not ui_specs:
        return ""
    primary_spec = next((item for item in ui_specs if isinstance(item, dict)), {})
    if not primary_spec:
        return ""

    title = str(primary_spec.get("page_name", "")).strip() or str(payload.get("feat_title", "")).strip()
    workflow_run_id = str(payload.get("workflow_run_id", "")).strip()
    lines = ["## Machine SSOT 人类友好全文", ""]
    intro = "这是一份 `ui_spec_package` 候选稿"
    if title:
        intro += f"，当前主页面是“{title}”"
    if workflow_run_id:
        intro += f"，本次 run 是 `{workflow_run_id}`"
    lines.append(intro + "。")

    feat_title = str(payload.get("feat_title", "")).strip()
    page_goal = str(primary_spec.get("page_goal", "")).strip()
    if feat_title:
        lines.extend(["", f"它承接的 FEAT 是“{feat_title}”。"])
    if page_goal:
        lines.extend(["", "这个页面要完成的目标是：" + page_goal])

    page_type = str(primary_spec.get("page_type", "")).strip()
    page_type_family = str(primary_spec.get("page_type_family", "")).strip()
    page_role = str(primary_spec.get("page_role_in_flow", "")).strip()
    completion_definition = str(primary_spec.get("completion_definition", "")).strip()
    lines.extend(["", "### 页面定位", ""])
    if page_type or page_type_family:
        type_line = " / ".join(part for part in [page_type, page_type_family] if part)
        lines.append(f"- 页面类型: {type_line}")
    if page_role:
        lines.append(f"- 流程角色: {page_role}")
    if completion_definition:
        lines.append(f"- 完成定义: {completion_definition}")

    main_user_path = _items(primary_spec.get("main_user_path"), limit=6)
    if main_user_path:
        lines.extend(["", "### 主用户路径", ""])
        lines.extend(f"- {item}" for item in main_user_path)

    branch_paths = primary_spec.get("branch_paths")
    if isinstance(branch_paths, list):
        branch_lines = []
        for branch in branch_paths[:4]:
            if not isinstance(branch, dict):
                continue
            title_text = str(branch.get("title", "")).strip()
            steps = _items(branch.get("steps"), limit=4)
            if title_text and steps:
                branch_lines.append(f"- {title_text}: {' -> '.join(steps)}")
            elif title_text:
                branch_lines.append(f"- {title_text}")
        if branch_lines:
            lines.extend(["", "### 关键分支与恢复路径", ""])
            lines.extend(branch_lines)

    sections = _items(primary_spec.get("page_sections"), limit=6)
    info_priority = _items(primary_spec.get("information_priority"), limit=4)
    action_priority = _items(primary_spec.get("action_priority"), limit=4)
    if sections or info_priority or action_priority:
        lines.extend(["", "### 信息结构与动作优先级", ""])
        if sections:
            lines.append("- 页面分区: " + " / ".join(sections))
        if info_priority:
            lines.append("- 信息优先级: " + "；".join(info_priority))
        if action_priority:
            lines.append("- 动作优先级: " + "；".join(action_priority))

    field_lines = _field_lines(primary_spec)
    if field_lines:
        lines.extend(["", "### 核心字段边界", ""])
        lines.extend(field_lines)

    state_lines = _state_lines(primary_spec.get("states"))
    if state_lines:
        lines.extend(["", "### 关键状态", ""])
        lines.extend(state_lines)

    validation_rules = _items(primary_spec.get("frontend_validation_rules"), limit=4)
    api_touchpoints = _items(primary_spec.get("api_touchpoints"), limit=4)
    if validation_rules or api_touchpoints:
        lines.extend(["", "### 校验与接口触点", ""])
        if validation_rules:
            lines.extend(f"- 校验: {item}" for item in validation_rules)
        if api_touchpoints:
            lines.extend(f"- 接口: {item}" for item in api_touchpoints)

    feedback_lines = _feedback_lines(primary_spec)
    if feedback_lines:
        lines.extend(["", "### 反馈与恢复", ""])
        lines.extend(feedback_lines)

    return "\n".join(lines) + "\n"


def _items(raw_value: object, *, limit: int) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    items: list[str] = []
    for item in raw_value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        items.append(text)
        if len(items) >= limit:
            break
    return items


def _field_lines(spec: dict[str, Any]) -> list[str]:
    field_names = _items(spec.get("required_ui_fields"), limit=8)
    if not field_names:
        field_names = _items(spec.get("required_fields"), limit=8)
    visible_fields = spec.get("ui_visible_fields")
    if not isinstance(visible_fields, list):
        visible_fields = spec.get("input_fields")
    if not isinstance(visible_fields, list):
        visible_fields = []
    option_lines: list[str] = []
    for field in visible_fields[:8]:
        if not isinstance(field, dict):
            continue
        field_name = str(field.get("field", "")).strip()
        note = str(field.get("note", "")).strip()
        if field_name and "options:" in note:
            option_lines.append(f"- {field_name}: {note}")
    lines: list[str] = []
    if field_names:
        lines.append("- 必填字段: " + "、".join(field_names))
    lines.extend(option_lines[:4])
    return lines


def _state_lines(raw_value: object) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    lines: list[str] = []
    for state in raw_value[:6]:
        if not isinstance(state, dict):
            continue
        name = str(state.get("name", "")).strip()
        trigger = str(state.get("trigger", "")).strip()
        behavior = str(state.get("ui_behavior", "")).strip()
        if not name:
            continue
        details = "；".join(part for part in [trigger, behavior] if part)
        lines.append(f"- {name}: {details}" if details else f"- {name}")
    return lines


def _feedback_lines(spec: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for label, field in (
        ("loading", "loading_feedback"),
        ("validation", "validation_feedback"),
        ("success", "success_feedback"),
        ("error", "error_feedback"),
        ("retry", "retry_behavior"),
    ):
        text = str(spec.get(field, "")).strip()
        if text:
            lines.append(f"- {label}: {text}")
    return lines
