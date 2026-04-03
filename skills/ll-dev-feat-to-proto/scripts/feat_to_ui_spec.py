#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any


def slugify(text: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", str(text or "").strip())).strip("-").lower() or "main"


def s_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def d_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def first(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def page_type_family(page_type: str) -> str:
    text = str(page_type or "").strip().lower()
    if not text:
        return "generic"
    if any(token in text for token in ["status layer", "status panel", "state boundary", "unified state", "conflict"]):
        return "status"
    if any(token in text for token in ["enhancement entry", "deferred device", "device connection"]):
        return "entry"
    if any(token in text for token in ["task card", "card list", "task cards"]):
        return "card_list"
    if any(token in text for token in ["advice panel", "banner", "panel"]):
        return "panel"
    if any(token in text for token in ["form", "onboarding form", "single-page form"]):
        return "form"
    return "generic"


def is_form_like_page_type(page_type: str) -> bool:
    return page_type_family(page_type) == "form"


def is_technical_payload_field_name(field_name: str) -> bool:
    name = str(field_name or "").strip().lower()
    if not name:
        return False
    return any(
        token in name
        for token in [
            "_ref",
            "_patch",
            "_state",
            "_flags",
            "_result",
            "_session",
            "_context",
            "_payload",
            "_service",
            "_mode",
            "_reason",
            "_percent",
            "_id",
        ]
    )


def is_ui_visible_field(field: dict[str, Any]) -> bool:
    source = str(field.get("source") or "").strip().lower()
    name = str(field.get("field") or "").strip()
    if source in {"user_input", "user_choice", "display", "ui_state"}:
        return not is_technical_payload_field_name(name)
    return False


def is_technical_field(field: dict[str, Any]) -> bool:
    source = str(field.get("source") or "").strip().lower()
    name = str(field.get("field") or "").strip()
    if source.startswith("system") or source in {"submit_result", "task_service", "connection_result", "risk_gate", "advice_result", "unified_state"}:
        return True
    return is_technical_payload_field_name(name)


def default_layout_plan(page_type: str) -> tuple[list[str], list[str], list[str]]:
    family = page_type_family(page_type)
    if family == "panel":
        return (
            ["Header", "Summary Signal", "Primary Panel Content", "Supporting Actions", "Recovery Slot"],
            ["Summary / signal first", "Primary result or recommendation second", "Recovery / next-step guidance last"],
            ["Inspect result", "Expand details", "Refresh or retry"],
        )
    if family == "card_list":
        return (
            ["Header", "Completion Summary", "Task Card List", "Active Card Drawer", "Save / Retry Feedback"],
            ["Completion summary first", "Active task card second", "Next tasks and recovery last"],
            ["Open task card", "Save current card", "Skip for later", "Refresh list"],
        )
    if family == "entry":
        return (
            ["Header", "Deferred Entry Notice", "Provider Picker", "Connect / Skip CTA", "Result Feedback"],
            ["Non-blocking notice first", "Primary connection choice second", "Retry guidance last"],
            ["Choose provider", "Connect device", "Skip for now", "Retry connection"],
        )
    if family == "status":
        return (
            ["Header", "Unified State Summary", "Conflict Banner", "Recovery Guidance", "Downstream Impact"],
            ["Canonical state first", "Conflict or blocking reason second", "Recovery guidance last"],
            ["Inspect state", "Resolve conflict", "Refresh status", "Return to the blocked path"],
        )
    return (
        ["Header", "Intro / Context", "Main Content", "Help / Error / Recovery Slot", "Footer"],
        ["Goal and context first", "Primary interaction next", "Help and recovery last"],
        ["Fill or edit content", "Click primary action", "Go back"],
    )


def default_ascii(title: str, page_type: str = "") -> str:
    family = page_type_family(page_type)
    if family == "panel":
        rows = [
            "+--------------------------------------------------+",
            f"| Header: {title[:38]:<38} |",
            "| Summary Signal / Recommendation                  |",
            "+--------------------------------------------------+",
            "| Primary Panel Content                            |",
            "| Supporting Prompt / Inline Guidance              |",
            "+--------------------------------------------------+",
            "| Recovery / Retry / Secondary Action              |",
            "+--------------------------------------------------+",
            "| Footer: [查看详情]                    [重试]      |",
            "+--------------------------------------------------+",
        ]
    elif family == "card_list":
        rows = [
            "+--------------------------------------------------+",
            f"| Header: {title[:38]:<38} |",
            "| Completion Summary                               |",
            "+--------------------------------------------------+",
            "| Task Card List                                   |",
            "| Active Card / Drawer                             |",
            "+--------------------------------------------------+",
            "| Save Feedback / Next Tasks                       |",
            "+--------------------------------------------------+",
            "| Footer: [稍后再做]                  [保存]       |",
            "+--------------------------------------------------+",
        ]
    elif family == "entry":
        rows = [
            "+--------------------------------------------------+",
            f"| Header: {title[:38]:<38} |",
            "| Deferred Entry Notice                            |",
            "+--------------------------------------------------+",
            "| Provider Picker                                  |",
            "| Connect CTA / Skip CTA                           |",
            "+--------------------------------------------------+",
            "| Result Feedback / Retry                          |",
            "+--------------------------------------------------+",
            "| Footer: [跳过]                      [连接]       |",
            "+--------------------------------------------------+",
        ]
    elif family == "status":
        rows = [
            "+--------------------------------------------------+",
            f"| Header: {title[:38]:<38} |",
            "| Unified State Summary                            |",
            "+--------------------------------------------------+",
            "| Conflict Banner / Blocking Reason                |",
            "| Recovery Guidance / Canonical Source Note        |",
            "+--------------------------------------------------+",
            "| Downstream Impact / Refresh State                |",
            "+--------------------------------------------------+",
            "| Footer: [返回]                          [刷新]   |",
            "+--------------------------------------------------+",
        ]
    else:
        rows = [
            "+--------------------------------------------------+",
            f"| Header: {title[:38]:<38} |",
            "| Intro / Context                                  |",
            "+--------------------------------------------------+",
            "| Main Content                                     |",
            "| Core Form / Core Decision / Core Result          |",
            "+--------------------------------------------------+",
            "| Help / Error / Recovery Slot                     |",
            "+--------------------------------------------------+",
            "| Footer: [返回]                          [下一步] |",
            "+--------------------------------------------------+",
        ]
    return "\n".join(rows)


def default_states(page_type: str = "") -> list[dict[str, Any]]:
    family = page_type_family(page_type)
    if family == "panel":
        return [
            {"name": "initial", "trigger": "页面首次进入", "ui_behavior": "展示骨架或默认推荐位", "user_options": "查看当前结果"},
            {"name": "content_ready", "trigger": "主要内容到达", "ui_behavior": "展示首屏核心内容与主提示", "user_options": "查看详情或继续"},
            {"name": "partial_or_empty", "trigger": "内容不足或为空", "ui_behavior": "展示空态或补充说明", "user_options": "补充信息或稍后重试"},
            {"name": "retryable_error", "trigger": "数据加载失败", "ui_behavior": "展示可重试错误", "user_options": "重试或保留当前首页"},
            {"name": "refreshed", "trigger": "内容刷新完成", "ui_behavior": "更新卡片内容但不改变页面结构", "user_options": "继续使用"},
        ]
    if family == "card_list":
        return [
            {"name": "initial", "trigger": "页面首次进入", "ui_behavior": "展示任务卡列表骨架", "user_options": "打开某个任务卡"},
            {"name": "list_ready", "trigger": "任务卡加载完成", "ui_behavior": "展示完成度与任务卡列表", "user_options": "打开或编辑任务卡"},
            {"name": "card_opened", "trigger": "打开任务卡", "ui_behavior": "展示当前任务卡编辑区", "user_options": "填写当前卡片"},
            {"name": "patch_saving", "trigger": "保存当前卡片", "ui_behavior": "仅当前卡片 loading", "user_options": "等待保存结果"},
            {"name": "patch_save_failed_retryable", "trigger": "保存失败", "ui_behavior": "展示当前卡片错误并保留上下文", "user_options": "修正后重试"},
            {"name": "patch_saved", "trigger": "保存成功", "ui_behavior": "刷新完成度与下一批任务卡", "user_options": "继续下一卡或返回首页"},
        ]
    if family == "entry":
        return [
            {"name": "offered", "trigger": "页面首次进入", "ui_behavior": "展示后置连接入口与跳过说明", "user_options": "连接设备或跳过"},
            {"name": "connecting", "trigger": "用户选择连接", "ui_behavior": "展示连接中的局部 loading", "user_options": "等待完成或返回"},
            {"name": "connected", "trigger": "连接成功", "ui_behavior": "解锁增强体验入口", "user_options": "继续首页主链"},
            {"name": "skipped", "trigger": "用户跳过", "ui_behavior": "保留首页可用并收起入口", "user_options": "稍后再做"},
            {"name": "failed_nonblocking", "trigger": "连接失败", "ui_behavior": "展示非阻塞失败提示与重试入口", "user_options": "重试连接或离开"},
        ]
    if family == "status":
        return [
            {"name": "initial", "trigger": "页面首次进入", "ui_behavior": "展示统一状态骨架", "user_options": "查看当前阻断状态"},
            {"name": "state_loaded", "trigger": "统一状态读取成功", "ui_behavior": "展示 canonical state 与能力标记", "user_options": "继续主链或修正问题"},
            {"name": "conflict_blocked", "trigger": "检测到跨边界冲突", "ui_behavior": "展示阻断 banner 与冲突原因", "user_options": "修复冲突或返回"},
            {"name": "recovery_prompt_visible", "trigger": "需要恢复动作", "ui_behavior": "展示恢复指引或回退入口", "user_options": "按指引修复"},
            {"name": "resolved", "trigger": "冲突已解决", "ui_behavior": "恢复统一状态视图", "user_options": "继续流程"},
        ]
    if family == "form":
        return [
            {"name": "initial", "trigger": "页面首次进入", "ui_behavior": "展示默认结构与说明", "user_options": "开始主路径操作"},
            {"name": "ready", "trigger": "首屏可交互", "ui_behavior": "页面主要结构和主操作已就绪", "user_options": "执行主路径操作"},
            {"name": "validation_error", "trigger": "前端校验失败", "ui_behavior": "高亮错误字段", "user_options": "修正后重试"},
            {"name": "submitting", "trigger": "提交中", "ui_behavior": "主按钮 loading 且禁重", "user_options": "等待响应"},
            {"name": "submit_error", "trigger": "提交失败", "ui_behavior": "展示错误并保留上下文", "user_options": "重试或返回修改"},
            {"name": "submit_success", "trigger": "提交成功", "ui_behavior": "进入下一步或刷新结果", "user_options": "继续流程"},
        ]
    return [
        {"name": "initial", "trigger": "页面首次进入", "ui_behavior": "展示默认结构与说明", "user_options": "开始主路径操作"},
        {"name": "ready", "trigger": "首屏可交互", "ui_behavior": "页面主要结构和主操作已就绪", "user_options": "执行主路径操作"},
        {"name": "partial", "trigger": "内容加载不完整", "ui_behavior": "展示局部状态和骨架", "user_options": "等待或刷新"},
        {"name": "retryable_error", "trigger": "页面内容获取失败", "ui_behavior": "展示错误并保留上下文", "user_options": "重试或退出"},
        {"name": "settled", "trigger": "内容稳定", "ui_behavior": "展示最终结构", "user_options": "继续操作"},
    ]


def default_user_actions(page_type: str = "") -> list[str]:
    family = page_type_family(page_type)
    if family == "panel":
        return ["查看建议或结果", "展开详情", "刷新内容", "执行补充动作"]
    if family == "card_list":
        return ["打开任务卡", "编辑当前卡片", "保存当前卡片", "稍后再做"]
    if family == "entry":
        return ["选择设备厂商", "连接设备", "跳过连接", "重试连接"]
    if family == "status":
        return ["查看当前状态", "修正冲突", "刷新统一状态", "返回被阻断的主链"]
    if family == "form":
        return ["填写或编辑内容", "点击主按钮", "返回上一层"]
    return ["填写或编辑内容", "点击主按钮", "返回上一层"]


def default_system_actions(page_type: str = "") -> list[str]:
    family = page_type_family(page_type)
    if family == "panel":
        return ["初始化推荐位", "加载结果数据", "刷新卡片内容", "保持首页可用"]
    if family == "card_list":
        return ["初始化任务卡列表", "读取完成度", "提交当前卡片", "刷新下一批任务卡"]
    if family == "entry":
        return ["初始化后置入口", "发起连接流程", "处理回调结果", "保持主链可用"]
    if family == "status":
        return ["读取统一状态", "检测冲突", "阻断非法继续", "暴露恢复指引"]
    if family == "form":
        return ["初始化页面", "前端校验", "提交请求", "更新页面状态"]
    return ["初始化页面", "前端校验", "提交请求", "更新页面状态"]


def default_section_plan(page_type: str = "") -> tuple[list[str], list[str], list[str]]:
    return default_layout_plan(page_type)


def _split_field_roles(fields: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ui_visible: list[dict[str, Any]] = []
    technical: list[dict[str, Any]] = []
    for field in fields:
        if is_ui_visible_field(field):
            ui_visible.append(field)
        elif is_technical_field(field):
            technical.append(field)
        else:
            technical.append(field)
    return ui_visible, technical


def _required_ui_field_names(fields: list[dict[str, Any]]) -> list[str]:
    return [str(field.get("field") or "").strip() for field in fields if field.get("required") and is_ui_visible_field(field) and str(field.get("field") or "").strip()]


def _required_input_field_names(fields: list[dict[str, Any]]) -> list[str]:
    return [str(field.get("field") or "").strip() for field in fields if field.get("required") and str(field.get("field") or "").strip()]


def _field_name_set(fields: list[dict[str, Any]]) -> set[str]:
    return {str(field.get("field") or "").strip() for field in fields if str(field.get("field") or "").strip()}


def _generic_default_template_used(unit: dict[str, Any]) -> bool:
    family = page_type_family(unit.get("page_type", ""))
    if family == "form":
        return False
    default_layout = default_ascii(unit["page_name"], "form").strip()
    return (
        unit["ascii_wireframe"].strip() == default_layout
        or unit["states"] == default_states("form")
        or unit["user_actions"] == default_user_actions("form")
        or unit["system_actions"] == default_system_actions("form")
    )


def has_forbidden_open_question(questions: list[str]) -> bool:
    keywords = ["主路径", "关键状态", "跳转", "必填", "接口", "触点", "失败反馈", "失败提示", "提交后", "api"]
    return any(any(keyword.lower() in str(question).strip().lower() for keyword in keywords) for question in questions)


def normalize_field(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return {
            "field": first(item.get("field"), item.get("name")),
            "type": first(item.get("type"), "string"),
            "required": bool(item.get("required")),
            "source": first(item.get("source"), "feat_input"),
            "note": first(item.get("note"), "无"),
        }
    return {"field": str(item).strip(), "type": "string", "required": False, "source": "feat_input", "note": "无"}


def build_units(feature: dict[str, Any], feat_ref: str) -> list[dict[str, Any]]:
    units = d_list(feature.get("ui_units")) or [{"page_name": first(feature.get("title"), feat_ref), "slug": slugify(first(feature.get("title"), feat_ref)), "open_questions": ["ui_units 未显式提供，当前页面拆分由 feat-to-ui skill 基于 FEAT 内容推断。"]}]
    result: list[dict[str, Any]] = []
    for raw in units:
        page_name = first(raw.get("page_name"), raw.get("name"), first(feature.get("title"), feat_ref))
        page_type = first(raw.get("page_type"), first(feature.get("page_type"), "single-page feature flow"))
        family = page_type_family(page_type)
        branch_paths = raw.get("branch_paths") if isinstance(raw.get("branch_paths"), list) else []
        if not branch_paths:
            branch_paths = [
                {"title": "Branch A", "steps": ["点击主按钮", "校验失败", "修正信息", "重新提交"]},
                {"title": "Branch B", "steps": ["提交请求", "服务端失败", "展示错误", "允许重试"]},
            ]
        page_sections, information_priority, action_priority = default_section_plan(page_type)
        input_fields = [normalize_field(item) for item in (raw.get("input_fields") or feature.get("ui_input_fields") or [])]
        display_fields = [normalize_field(item) for item in (raw.get("display_fields") or feature.get("ui_display_fields") or feature.get("outputs") or [])]
        editable_ui_fields, technical_payload_fields = _split_field_roles(input_fields)
        ui_visible_fields = editable_ui_fields + display_fields
        required_ui_fields = _required_ui_field_names(input_fields)
        required_input_fields = _required_input_field_names(input_fields)
        required_fields = s_list(raw.get("required_fields")) or required_ui_fields or (required_input_fields if family == "form" else [])
        result.append(
            {
                "slug": first(raw.get("slug"), slugify(page_name)),
                "page_name": page_name,
                "page_type": page_type,
                "page_type_family": family,
                "platform": first(raw.get("platform"), first(feature.get("platform"), "web")),
                "page_goal": first(raw.get("page_goal"), first(feature.get("goal"), f"帮助用户完成 {page_name}")),
                "user_job": first(raw.get("user_job"), f"用户在界面中完成“{page_name}”对应的核心动作。"),
                "page_role_in_flow": first(raw.get("page_role_in_flow"), f"承接 {feat_ref} 的主要用户可见步骤。"),
                "completion_definition": first(raw.get("completion_definition"), "用户完成主路径并满足 FEAT 成功标准。"),
                "in_scope": s_list(raw.get("in_scope")) or s_list(feature.get("scope")),
                "out_of_scope": s_list(raw.get("out_of_scope")) or s_list(feature.get("non_goals")) or ["最终视觉稿", "代码结构", "测试用例细节"],
                "entry_condition": first(raw.get("entry_condition"), first(feature.get("trigger_scenario"), f"用户进入 {page_name} 页面。")),
                "exit_condition": first(raw.get("exit_condition"), "用户完成主路径后离开当前页面或进入下一步。"),
                "upstream": first(raw.get("upstream"), f"FEAT {feat_ref} 触发入口"),
                "downstream": first(raw.get("downstream"), "后续 UI/TECH 开发"),
                "main_user_path": s_list(raw.get("main_user_path")) or [f"进入 {page_name}", "查看首屏说明", "执行核心输入或选择", "点击主按钮", "接收校验与提交反馈", "进入下一步或完成本页"],
                "branch_paths": branch_paths,
                "ux_flow_notes": s_list(raw.get("ux_flow_notes")) or ["首屏必须清楚说明目标", "主动作优先级必须明确", "失败与恢复必须显式反馈"],
                "page_sections": s_list(raw.get("page_sections")) or page_sections,
                "information_priority": s_list(raw.get("information_priority")) or information_priority,
                "action_priority": s_list(raw.get("action_priority")) or action_priority,
                "ascii_wireframe": first(raw.get("ascii_wireframe"), default_ascii(page_name, page_type)),
                "states": raw.get("states") if isinstance(raw.get("states"), list) and raw.get("states") else default_states(page_type),
                "input_fields": input_fields,
                "display_fields": display_fields,
                "editable_ui_fields": editable_ui_fields,
                "ui_visible_fields": ui_visible_fields,
                "technical_payload_fields": technical_payload_fields,
                "required_fields": required_fields,
                "required_input_fields": required_input_fields,
                "required_ui_fields": required_ui_fields,
                "derived_fields": s_list(raw.get("derived_fields")) or s_list(feature.get("derived_fields")),
                "user_actions": s_list(raw.get("user_actions")) or default_user_actions(page_type),
                "system_actions": s_list(raw.get("system_actions")) or default_system_actions(page_type),
                "frontend_validation_rules": s_list(raw.get("frontend_validation_rules")) or s_list(feature.get("ui_validation_rules")),
                "backend_validation_assumptions": s_list(raw.get("backend_validation_assumptions")) or ["后端负责最终业务校验。"],
                "data_dependencies": s_list(raw.get("data_dependencies")) or s_list(feature.get("ui_data_dependencies")),
                "api_touchpoints": s_list(raw.get("api_touchpoints")) or s_list(feature.get("ui_api_touchpoints")),
                "derived_logic": s_list(raw.get("derived_logic")) or s_list(feature.get("ui_derived_logic")),
                "state_owned_by_ui": s_list(raw.get("state_owned_by_ui")) or ["本地输入值", "校验状态", "按钮 loading 状态"],
                "state_owned_by_backend": s_list(raw.get("state_owned_by_backend")) or ["持久化结果", "业务拒绝原因"],
                "loading_feedback": first(raw.get("loading_feedback"), "关键区域局部 loading。"),
                "validation_feedback": first(raw.get("validation_feedback"), "字段或区域级错误反馈优先。"),
                "success_feedback": first(raw.get("success_feedback"), "成功后进入下一步或刷新结果。"),
                "error_feedback": first(raw.get("error_feedback"), "失败时展示明确错误并保留上下文。"),
                "retry_behavior": first(raw.get("retry_behavior"), "修正后允许再次提交。"),
                "open_questions": s_list(raw.get("open_questions")) or s_list(feature.get("ui_open_questions")),
            }
        )
    return result


def assess_unit(unit: dict[str, Any]) -> tuple[str, dict[str, bool], list[str]]:
    family = str(unit.get("page_type_family") or page_type_family(unit.get("page_type", ""))).strip() or "generic"
    inferred_ui_scope = any("ui_units 未显式提供" in str(question) for question in unit.get("open_questions") or [])
    required_ui_names = set(unit.get("required_ui_fields") or _required_ui_field_names(unit["input_fields"]))
    required_field_names = _field_name_set([{"field": name} for name in unit["required_fields"]])
    input_field_names = _field_name_set(unit["input_fields"])
    editable_ui_names = _field_name_set(unit.get("editable_ui_fields") or [])
    ui_visible_names = _field_name_set(unit.get("ui_visible_fields") or [])
    technical_payload_names = _field_name_set(unit.get("technical_payload_fields") or [])
    template_leakage = _generic_default_template_used(unit)
    checks = {
        "page_goal_clear": bool(unit["page_goal"]),
        "entry_exit_defined": bool(unit["entry_condition"] and unit["exit_condition"]),
        "main_user_path_defined": len(unit["main_user_path"]) >= 4,
        "key_branch_paths_defined": len(unit["branch_paths"]) >= 2,
        "ascii_wireframe_included": bool(unit["ascii_wireframe"].strip()),
        "key_states_included": len(unit["states"]) >= 5,
        "field_boundary_included": bool(unit["input_fields"] or unit["display_fields"] or unit["required_fields"] or unit["derived_fields"]),
        "action_boundary_included": bool(unit["user_actions"] and unit["system_actions"]),
        "validation_rules_included": bool(unit["frontend_validation_rules"] or unit["backend_validation_assumptions"]),
        "technical_touchpoints_included": bool(unit["data_dependencies"] or unit["api_touchpoints"] or inferred_ui_scope),
        "feedback_rules_included": bool(unit["validation_feedback"] and unit["error_feedback"] and unit["retry_behavior"]),
        "page_type_matches_layout": family == "form" or not template_leakage or inferred_ui_scope,
        "required_field_consistency": not required_ui_names or required_ui_names.issubset(required_field_names),
        "editable_field_boundary_present": family not in {"card_list", "entry"} or bool(editable_ui_names),
        "ui_technical_field_split_present": family == "form" or bool(ui_visible_names or technical_payload_names),
    }
    questions = list(unit["open_questions"])
    if template_leakage and family != "form":
        questions.append("页面类型与默认整页表单模板不匹配，需要专用 wireframe / states / actions。")
    if not checks["field_boundary_included"]:
        questions.append("需要补充字段边界。")
    if required_ui_names and not checks["required_field_consistency"]:
        missing = sorted(required_ui_names - required_field_names)
        extra = sorted(required_field_names - input_field_names)
        details = []
        if missing:
            details.append(f"missing={', '.join(missing)}")
        if extra:
            details.append(f"extra={', '.join(extra)}")
        questions.append("Required Fields must match required input fields. " + "; ".join(details))
    if not checks["technical_touchpoints_included"]:
        questions.append("需要补充 data_dependencies 与 api_touchpoints。")
    if not unit["frontend_validation_rules"]:
        questions.append("需要补充前端校验规则。")
    if not checks["feedback_rules_included"]:
        questions.append("需要补充失败反馈与重试规则。")
    if family in {"card_list", "entry"} and not editable_ui_names:
        questions.append("需要显式列出可编辑的 UI-visible fields，而不是只保留技术 payload。")
    hard_fail = [
        "page_goal_clear",
        "entry_exit_defined",
        "main_user_path_defined",
        "key_branch_paths_defined",
        "ascii_wireframe_included",
        "key_states_included",
        "field_boundary_included",
        "action_boundary_included",
        "validation_rules_included",
        "technical_touchpoints_included",
        "feedback_rules_included",
        "page_type_matches_layout",
        "required_field_consistency",
        "editable_field_boundary_present",
        "ui_technical_field_split_present",
    ]
    if not all(checks[key] for key in hard_fail) or has_forbidden_open_question(questions):
        return "fail", checks, questions
    if not questions and all(checks.values()):
        return "pass", checks, questions
    return "conditional_pass", checks, questions


def _bullet_lines(items: list[str], default: str) -> list[str]:
    return [f"- {item}" for item in items] or [f"- {default}"]


def _indented_lines(items: list[str], default: str) -> list[str]:
    return [f"  - {item}" for item in items] or [f"  - {default}"]


def _render_branch_lines(unit: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for branch in unit["branch_paths"]:
        lines.append(f"#### {branch.get('title', 'Branch')}")
        lines.extend(f"- {step}" for step in s_list(branch.get("steps")))
    return lines


def _render_state_lines(unit: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for state in unit["states"]:
        if not isinstance(state, dict):
            continue
        lines.extend(
            [
                f"### state: {first(state.get('name'), 'state')}",
                f"* trigger: {first(state.get('trigger'), '')}",
                f"* ui_behavior: {first(state.get('ui_behavior'), '无')}",
                f"* user_options: {first(state.get('user_options'), '无')}",
                "",
            ]
        )
    return lines


def _render_meta_scope_lines(unit: dict[str, Any]) -> list[str]:
    return [
        "# UI Spec",
        "",
        "## 1. Meta",
        f"- ui_spec_id: {unit['ui_spec_id']}",
        f"- linked_feat: {unit['linked_feat']}",
        f"- page_name: {unit['page_name']}",
        f"- page_type: {unit['page_type']}",
        f"- platform: {unit['platform']}",
        f"- status: {unit['completeness_result']}",
        "",
        "## 2. Page Goal",
        f"- page_goal: {unit['page_goal']}",
        f"- user_job: {unit['user_job']}",
        f"- page_role_in_flow: {unit['page_role_in_flow']}",
        f"- completion_definition: {unit['completion_definition']}",
        "",
        "## 3. Scope",
        "- in_scope:",
        *_indented_lines(unit["in_scope"], "无"),
        "- out_of_scope:",
        *_indented_lines(unit["out_of_scope"], "无"),
        "",
        "## 4. Entry & Exit",
        f"- entry_condition: {unit['entry_condition']}",
        f"- exit_condition: {unit['exit_condition']}",
        f"- upstream: {unit['upstream']}",
        f"- downstream: {unit['downstream']}",
        "",
    ]


def _render_path_layout_lines(unit: dict[str, Any]) -> list[str]:
    return [
        "## 5. User Path",
        "### Main Path",
        *[f"{index}. {step}" for index, step in enumerate(unit["main_user_path"], start=1)],
        "",
        "### Branch Paths",
        *_render_branch_lines(unit),
        "",
        "## 6. UX Flow Notes",
        *_bullet_lines(unit["ux_flow_notes"], "无"),
        "",
        "## 7. Layout Structure",
        "- page_sections:",
        *_indented_lines(unit["page_sections"], "无"),
        "- information_priority:",
        *_indented_lines(unit["information_priority"], "无"),
        "- action_priority:",
        *_indented_lines(unit["action_priority"], "无"),
        "",
        "## 8. ASCII Wireframe",
        "```text",
        unit["ascii_wireframe"],
        "```",
        "",
        "## 9. States",
        *_render_state_lines(unit),
    ]


def _render_field_action_lines(unit: dict[str, Any]) -> list[str]:
    input_fields = [f"- {field['field']} ({field['type']}, required={str(field['required']).lower()})" for field in unit["input_fields"]] or ["- 无"]
    display_fields = _bullet_lines([field["field"] for field in unit["display_fields"]], "无")
    ui_visible_fields = _bullet_lines([field["field"] for field in unit.get("ui_visible_fields") or []], "无")
    technical_payload_fields = _bullet_lines([field["field"] for field in unit.get("technical_payload_fields") or []], "无")
    required_fields = _bullet_lines(unit["required_fields"], "无")
    derived_fields = _bullet_lines(unit["derived_fields"], "无")
    return [
        "## 10. Fields",
        "### Input Fields",
        *input_fields,
        "",
        "### Display Fields",
        *display_fields,
        "",
        "### UI Visible Fields",
        *ui_visible_fields,
        "",
        "### Technical Payload Fields",
        *technical_payload_fields,
        "",
        "### Required Fields",
        *required_fields,
        "",
        "### Derived Fields",
        *derived_fields,
        "",
        "## 11. Actions",
        "### User Actions",
        *_bullet_lines(unit["user_actions"], "无"),
        "",
        "### System Actions",
        *_bullet_lines(unit["system_actions"], "无"),
        "",
    ]


def _render_validation_footer_lines(unit: dict[str, Any]) -> list[str]:
    frontend_rules = _bullet_lines(unit["frontend_validation_rules"], "无")
    backend_rules = _bullet_lines(unit["backend_validation_assumptions"], "无")
    return [
        "## 12. Validation Rules",
        "### Frontend Validation",
        *frontend_rules,
        "",
        "### Backend Assumptions",
        *backend_rules,
        "",
        "## 13. Technical Boundary",
        "- data_dependencies:",
        *_indented_lines(unit["data_dependencies"], "无"),
        "- api_touchpoints:",
        *_indented_lines(unit["api_touchpoints"], "无"),
        "- derived_logic:",
        *_indented_lines(unit["derived_logic"], "无"),
        "",
        "## 14. Feedback Rules",
        f"- loading_feedback: {unit['loading_feedback']}",
        f"- validation_feedback: {unit['validation_feedback']}",
        f"- success_feedback: {unit['success_feedback']}",
        f"- error_feedback: {unit['error_feedback']}",
        f"- retry_behavior: {unit['retry_behavior']}",
        "",
        "## 15. Open Questions",
        *_bullet_lines(unit["open_questions"], "无"),
        "",
        "## 16. Completeness Checklist",
        *[f"* [{'x' if ok else ' '}] {name}" for name, ok in unit["checklist"].items()],
    ]


def render_spec(unit: dict[str, Any]) -> str:
    return "\n".join(_render_meta_scope_lines(unit) + _render_path_layout_lines(unit) + _render_field_action_lines(unit) + _render_validation_footer_lines(unit))
