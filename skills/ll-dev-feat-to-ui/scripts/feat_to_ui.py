#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

INPUT_FILES = [
    "package-manifest.json",
    "feat-freeze-bundle.md",
    "feat-freeze-bundle.json",
    "feat-review-report.json",
    "feat-acceptance-report.json",
    "feat-defect-list.json",
    "feat-freeze-gate.json",
    "handoff-to-feat-downstreams.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
OUTPUT_FILES = [
    "package-manifest.json",
    "ui-spec-bundle.md",
    "ui-spec-bundle.json",
    "ui-flow-map.md",
    "ui-spec-completeness-report.json",
    "ui-spec-review-report.json",
    "ui-spec-defect-list.json",
    "ui-spec-freeze-gate.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(text: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", str(text or "").strip())).strip("-").lower() or "main"


def repo_root_from(repo_root: str | None) -> Path:
    return Path(repo_root).resolve() if repo_root else Path.cwd().resolve()


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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def default_ascii(title: str) -> str:
    return "\n".join(
        [
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
    )


def default_states() -> list[dict[str, Any]]:
    return [
        {"name": "initial", "trigger": "页面首次进入", "ui_behavior": "展示默认结构与说明", "user_options": "开始主路径操作"},
        {"name": "ready", "trigger": "首屏可交互", "ui_behavior": "页面主要结构和主操作已就绪", "user_options": "执行主路径操作"},
        {"name": "validation_error", "trigger": "前端校验失败", "ui_behavior": "高亮错误字段", "user_options": "修正后重试"},
        {"name": "submitting", "trigger": "提交中", "ui_behavior": "主按钮 loading 且禁重", "user_options": "等待响应"},
        {"name": "submit_error", "trigger": "提交失败", "ui_behavior": "展示错误并保留上下文", "user_options": "重试或返回修改"},
        {"name": "submit_success", "trigger": "提交成功", "ui_behavior": "进入下一步或刷新结果", "user_options": "继续流程"},
    ]


def has_forbidden_open_question(questions: list[str]) -> bool:
    keywords = [
        "主路径",
        "关键状态",
        "跳转",
        "必填",
        "接口",
        "触点",
        "失败反馈",
        "失败提示",
        "提交后",
        "api",
    ]
    for question in questions:
        text = str(question).strip().lower()
        if any(keyword.lower() in text for keyword in keywords):
            return True
    return False


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
    units = d_list(feature.get("ui_units"))
    if not units:
        units = [
            {
                "page_name": first(feature.get("title"), feat_ref),
                "slug": slugify(first(feature.get("title"), feat_ref)),
                "open_questions": ["ui_units 未显式提供，当前页面拆分由 feat-to-ui skill 基于 FEAT 内容推断。"],
            }
        ]
    result: list[dict[str, Any]] = []
    for raw in units:
        page_name = first(raw.get("page_name"), raw.get("name"), first(feature.get("title"), feat_ref))
        branch_paths = raw.get("branch_paths") if isinstance(raw.get("branch_paths"), list) else []
        if not branch_paths:
            branch_paths = [
                {"title": "Branch A", "steps": ["点击主按钮", "校验失败", "修正信息", "重新提交"]},
                {"title": "Branch B", "steps": ["提交请求", "服务端失败", "展示错误", "允许重试"]},
            ]
        result.append(
            {
                "slug": first(raw.get("slug"), slugify(page_name)),
                "page_name": page_name,
                "page_type": first(raw.get("page_type"), "single-page feature flow"),
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
                "main_user_path": s_list(raw.get("main_user_path")) or [
                    f"进入 {page_name}",
                    "查看首屏说明",
                    "执行核心输入或选择",
                    "点击主按钮",
                    "接收校验与提交反馈",
                    "进入下一步或完成本页",
                ],
                "branch_paths": branch_paths,
                "ux_flow_notes": s_list(raw.get("ux_flow_notes")) or ["首屏必须清楚说明目标", "主动作优先级必须明确", "失败与恢复必须显式反馈"],
                "page_sections": s_list(raw.get("page_sections")) or ["Header", "Intro Note", "Main Content", "Help Section", "Footer Actions"],
                "information_priority": s_list(raw.get("information_priority")) or ["目标与上下文优先", "主操作区其次", "帮助与异常反馈最后"],
                "action_priority": s_list(raw.get("action_priority")) or ["主提交动作优先", "返回或取消次之"],
                "ascii_wireframe": first(raw.get("ascii_wireframe"), default_ascii(page_name)),
                "states": raw.get("states") if isinstance(raw.get("states"), list) and raw.get("states") else default_states(),
                "input_fields": [normalize_field(item) for item in (raw.get("input_fields") or feature.get("ui_input_fields") or [])],
                "display_fields": [normalize_field(item) for item in (raw.get("display_fields") or feature.get("ui_display_fields") or feature.get("outputs") or [])],
                "required_fields": s_list(raw.get("required_fields")) or s_list(feature.get("required_fields")),
                "derived_fields": s_list(raw.get("derived_fields")) or s_list(feature.get("derived_fields")),
                "user_actions": s_list(raw.get("user_actions")) or ["填写或编辑内容", "点击主按钮", "返回上一层"],
                "system_actions": s_list(raw.get("system_actions")) or ["初始化页面", "前端校验", "提交请求", "更新页面状态"],
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
        "technical_touchpoints_included": bool(unit["data_dependencies"] or unit["api_touchpoints"]),
        "feedback_rules_included": bool(unit["validation_feedback"] and unit["error_feedback"] and unit["retry_behavior"]),
    }
    questions = list(unit["open_questions"])
    if not checks["field_boundary_included"]:
        questions.append("需要补充字段边界。")
    if not checks["technical_touchpoints_included"]:
        questions.append("需要补充 data_dependencies 与 api_touchpoints。")
    if not unit["frontend_validation_rules"]:
        questions.append("需要补充前端校验规则。")
    if not checks["feedback_rules_included"]:
        questions.append("需要补充失败反馈与重试规则。")
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
    ]
    if not all(checks[key] for key in hard_fail):
        return "fail", checks, questions
    if has_forbidden_open_question(questions):
        return "fail", checks, questions
    if not questions and all(checks.values()):
        return "pass", checks, questions
    return "conditional_pass", checks, questions


def render_spec(unit: dict[str, Any]) -> str:
    branches: list[str] = []
    for branch in unit["branch_paths"]:
        branches.append(f"#### {branch.get('title', 'Branch')}")
        branches.extend([f"- {step}" for step in s_list(branch.get("steps"))])
    states: list[str] = []
    for state in unit["states"]:
        if not isinstance(state, dict):
            continue
        states.extend([f"### state: {first(state.get('name'), 'state')}", f"* trigger: {first(state.get('trigger'), '')}", f"* ui_behavior: {first(state.get('ui_behavior'), '无')}", f"* user_options: {first(state.get('user_options'), '无')}", ""])
    in_scope = [f"  - {item}" for item in unit["in_scope"]] or ["  - 无"]
    out_of_scope = [f"  - {item}" for item in unit["out_of_scope"]] or ["  - 无"]
    input_fields = [f"- {field['field']} ({field['type']}, required={str(field['required']).lower()})" for field in unit["input_fields"]] or ["- 无"]
    display_fields = [f"- {field['field']}" for field in unit["display_fields"]] or ["- 无"]
    required_fields = [f"- {item}" for item in unit["required_fields"]] or ["- 无"]
    derived_fields = [f"- {item}" for item in unit["derived_fields"]] or ["- 无"]
    frontend_rules = [f"- {item}" for item in unit["frontend_validation_rules"]] or ["- 无"]
    backend_rules = [f"- {item}" for item in unit["backend_validation_assumptions"]] or ["- 无"]
    data_dependencies = [f"  - {item}" for item in unit["data_dependencies"]] or ["  - 无"]
    api_touchpoints = [f"  - {item}" for item in unit["api_touchpoints"]] or ["  - 无"]
    derived_logic = [f"  - {item}" for item in unit["derived_logic"]] or ["  - 无"]
    open_questions = [f"- {item}" for item in unit["open_questions"]] or ["- 无"]
    return "\n".join(
        [
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
            *in_scope,
            "- out_of_scope:",
            *out_of_scope,
            "",
            "## 4. Entry & Exit",
            f"- entry_condition: {unit['entry_condition']}",
            f"- exit_condition: {unit['exit_condition']}",
            f"- upstream: {unit['upstream']}",
            f"- downstream: {unit['downstream']}",
            "",
            "## 5. User Path",
            "### Main Path",
            *[f"{index}. {step}" for index, step in enumerate(unit["main_user_path"], start=1)],
            "",
            "### Branch Paths",
            *branches,
            "",
            "## 6. UX Flow Notes",
            *[f"- {item}" for item in unit["ux_flow_notes"]],
            "",
            "## 7. Layout Structure",
            "- page_sections:",
            *[f"  - {item}" for item in unit["page_sections"]],
            "- information_priority:",
            *[f"  - {item}" for item in unit["information_priority"]],
            "- action_priority:",
            *[f"  - {item}" for item in unit["action_priority"]],
            "",
            "## 8. ASCII Wireframe",
            "```text",
            unit["ascii_wireframe"],
            "```",
            "",
            "## 9. States",
            *states,
            "## 10. Fields",
            "### Input Fields",
            *input_fields,
            "",
            "### Display Fields",
            *display_fields,
            "",
            "### Required Fields",
            *required_fields,
            "",
            "### Derived Fields",
            *derived_fields,
            "",
            "## 11. Actions",
            "### User Actions",
            *[f"- {item}" for item in unit["user_actions"]],
            "",
            "### System Actions",
            *[f"- {item}" for item in unit["system_actions"]],
            "",
            "## 12. Validation Rules",
            "### Frontend Validation",
            *frontend_rules,
            "",
            "### Backend Assumptions",
            *backend_rules,
            "",
            "## 13. Technical Boundary",
            "- data_dependencies:",
            *data_dependencies,
            "- api_touchpoints:",
            *api_touchpoints,
            "- derived_logic:",
            *derived_logic,
            "",
            "## 14. Feedback Rules",
            f"- loading_feedback: {unit['loading_feedback']}",
            f"- validation_feedback: {unit['validation_feedback']}",
            f"- success_feedback: {unit['success_feedback']}",
            f"- error_feedback: {unit['error_feedback']}",
            f"- retry_behavior: {unit['retry_behavior']}",
            "",
            "## 15. Open Questions",
            *open_questions,
            "",
            "## 16. Completeness Checklist",
            *[f"* [{'x' if ok else ' '}] {name}" for name, ok in unit["checklist"].items()],
        ]
    )


def validate_input_package(input_path: str | Path, feat_ref: str, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    input_dir = Path(input_path).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        return [f"input path is not a directory: {input_dir}"], {}
    errors = [f"missing required input artifact: {name}" for name in INPUT_FILES if not (input_dir / name).exists()]
    if errors:
        return errors, {}
    bundle = load_json(input_dir / "feat-freeze-bundle.json")
    gate = load_json(input_dir / "feat-freeze-gate.json")
    feature = next((item for item in d_list(bundle.get("features")) if str(item.get("feat_ref")) == feat_ref), None)
    if bundle.get("artifact_type") != "feat_freeze_package":
        errors.append("artifact_type must be feat_freeze_package")
    if bundle.get("workflow_key") != "product.epic-to-feat":
        errors.append("workflow_key must be product.epic-to-feat")
    if str(bundle.get("status") or "").strip() not in {"accepted", "frozen"}:
        errors.append("status must be accepted or frozen")
    if not gate.get("freeze_ready"):
        errors.append("feat-freeze-gate.json freeze_ready must be true")
    if feature is None:
        errors.append(f"selected feat_ref not found in bundle: {feat_ref}")
    if feature and feature.get("ui_required") is False:
        errors.append(f"selected FEAT {feat_ref} explicitly disables UI derivation via ui_required=false")
    return errors, {"input_dir": input_dir, "bundle": bundle, "feature": feature, "feat_ref": feat_ref, "repo_root": repo_root}


def build_package(context: dict[str, Any], repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    feat_ref = context["feat_ref"]
    feature = context["feature"]
    output_dir = repo_root / "artifacts" / "feat-to-ui" / f"{slugify(run_id or feat_ref)}--{slugify(feat_ref)}"
    if output_dir.exists() and not allow_update:
        return {"ok": False, "errors": [f"output directory already exists: {output_dir}"], "artifacts_dir": str(output_dir)}
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob("*__ui_spec.md"):
        stale.unlink()
    units, questions = [], []
    for unit in build_units(feature, feat_ref):
        decision, checklist, unit_questions = assess_unit(unit)
        spec_id = f"UI-{feat_ref}-{unit['slug']}"
        output_name = f"[{spec_id}]__ui_spec.md"
        unit.update({"ui_spec_id": spec_id, "linked_feat": feat_ref, "output_ref": rel(output_dir / output_name, repo_root), "completeness_result": decision, "checklist": checklist, "open_questions": unit_questions})
        write_text(output_dir / output_name, render_spec(unit))
        units.append(unit)
        questions.extend(unit_questions)
    overall = "fail" if any(unit["completeness_result"] == "fail" for unit in units) else "pass" if all(unit["completeness_result"] == "pass" for unit in units) else "conditional_pass"
    flow_edges = [
        {
            "from": units[index]["ui_spec_id"],
            "to": units[index + 1]["ui_spec_id"],
            "relation": "next",
        }
        for index in range(len(units) - 1)
    ]
    bundle = {
        "artifact_type": "ui_spec_package",
        "workflow_key": "dev.feat-to-ui",
        "workflow_run_id": run_id or slugify(feat_ref),
        "status": overall,
        "schema_version": "1.0.0",
        "feat_ref": feat_ref,
        "feat_title": first(feature.get("title"), feat_ref),
        "ui_spec_count": len(units),
        "ui_spec_refs": [unit["output_ref"] for unit in units],
        "ui_specs": units,
        "package_entry_spec_id": units[0]["ui_spec_id"],
        "package_exit_spec_id": units[-1]["ui_spec_id"],
        "flow_edges": flow_edges,
        "completeness_result": overall,
        "gate_name": "UI Spec Completeness Check",
        "source_refs": s_list(feature.get("source_refs")) or s_list(context["bundle"].get("source_refs")),
        "open_questions": sorted(set(questions)),
        "source_package_ref": rel(context["input_dir"], repo_root),
    }
    defects = [{"ui_spec_id": unit["ui_spec_id"], "check": name} for unit in units for name, ok in unit["checklist"].items() if not ok]
    write_json(output_dir / "package-manifest.json", {"artifact_type": "ui_spec_package", "workflow_key": "dev.feat-to-ui", "run_id": run_id or slugify(feat_ref), "feat_ref": feat_ref, "status": overall, "ui_spec_refs": bundle["ui_spec_refs"], "source_package_ref": bundle["source_package_ref"], "ui_flow_map_ref": rel(output_dir / "ui-flow-map.md", repo_root)})
    write_text(output_dir / "ui-spec-bundle.md", "\n".join([f"# UI Spec Bundle for {feat_ref}", "", "## Selected FEAT", f"- feat_ref: {feat_ref}", f"- title: {bundle['feat_title']}", f"- ui_spec_count: {bundle['ui_spec_count']}", f"- completeness_result: {overall}", "", "## UI Spec Inventory", *[f"- {unit['ui_spec_id']} | {unit['page_name']} | {unit['completeness_result']}" for unit in units], "", "## Traceability", *[f"- {item}" for item in bundle["source_refs"]]]))
    write_text(
        output_dir / "ui-flow-map.md",
        "\n".join(
            [
                f"# UI Flow Map for {feat_ref}",
                "",
                "## Package Entry / Exit",
                f"- package_entry_spec_id: {bundle['package_entry_spec_id']}",
                f"- package_exit_spec_id: {bundle['package_exit_spec_id']}",
                "",
                "## UI Spec Order",
                *[f"{index}. {unit['ui_spec_id']} | {unit['page_name']} | {'主页面' if index == 1 else '后续页面'}" for index, unit in enumerate(units, start=1)],
                "",
                "## Flow Edges",
                *([f"- {edge['from']} -> {edge['to']} ({edge['relation']})" for edge in flow_edges] or ["- 单页场景，无跨页面边。"]),
                "",
                "## Package Flow Notes",
                "- 本文件用于多 UI Spec 场景下的包级总览。",
                "- 单页场景仍保留该文件，以固定 package-level index 形态。",
            ]
        ),
    )
    write_json(output_dir / "ui-spec-bundle.json", bundle)
    write_json(output_dir / "ui-spec-completeness-report.json", {"gate_name": "UI Spec Completeness Check", "decision": overall, "freeze_ready": overall != "fail", "ui_specs": [{"ui_spec_id": unit["ui_spec_id"], "decision": unit["completeness_result"], "checklist": unit["checklist"], "open_questions": unit["open_questions"]} for unit in units], "open_questions": bundle["open_questions"], "checked_at": utc_now()})
    write_json(output_dir / "ui-spec-review-report.json", {"workflow_key": "dev.feat-to-ui", "decision": overall, "summary": f"UI Spec Completeness Check => {overall}", "reviewed_at": utc_now(), "open_questions": bundle["open_questions"]})
    write_json(output_dir / "ui-spec-defect-list.json", defects)
    write_json(output_dir / "ui-spec-freeze-gate.json", {"workflow_key": "dev.feat-to-ui", "gate_name": "UI Spec Completeness Check", "decision": overall, "freeze_ready": overall != "fail", "checked_at": utc_now()})
    write_json(output_dir / "execution-evidence.json", {"workflow_key": "dev.feat-to-ui", "run_id": run_id or slugify(feat_ref), "input_path": str(context["input_dir"]), "artifacts_dir": str(output_dir), "decision": overall, "generated_at": utc_now()})
    write_json(output_dir / "supervision-evidence.json", {"workflow_key": "dev.feat-to-ui", "run_id": run_id or slugify(feat_ref), "artifacts_dir": str(output_dir), "decision": overall, "review_completed_at": utc_now(), "gate_name": "UI Spec Completeness Check"})
    write_text(output_dir / "evidence-report.md", "\n".join(["# Evidence Report", "", f"- decision: {overall}", f"- generated_at: {utc_now()}"]))
    return {"ok": overall != "fail", "artifacts_dir": str(output_dir), "artifacts_ref": rel(output_dir, repo_root), "ui_spec_refs": bundle["ui_spec_refs"], "ui_spec_count": len(units), "completeness_result": overall, "open_questions": bundle["open_questions"]}


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"artifacts_dir does not exist: {artifacts_dir}"], {}
    errors = [f"missing required output artifact: {name}" for name in OUTPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {}
    bundle = load_json(artifacts_dir / "ui-spec-bundle.json")
    report = load_json(artifacts_dir / "ui-spec-completeness-report.json")
    gate = load_json(artifacts_dir / "ui-spec-freeze-gate.json")
    if bundle.get("artifact_type") != "ui_spec_package":
        errors.append("ui-spec-bundle.json artifact_type must be ui_spec_package")
    if bundle.get("workflow_key") != "dev.feat-to-ui":
        errors.append("ui-spec-bundle.json workflow_key must be dev.feat-to-ui")
    if bundle.get("schema_version") != "1.0.0":
        errors.append("ui-spec-bundle.json schema_version must be 1.0.0")
    if int(bundle.get("ui_spec_count") or 0) != len(bundle.get("ui_spec_refs") or []):
        errors.append("ui_spec_count must match ui_spec_refs length")
    if report.get("decision") != gate.get("decision"):
        errors.append("completeness report decision must match freeze gate decision")
    return errors, {"bundle": bundle, "report": report, "gate": gate}


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, result = validate_output_package(artifacts_dir)
    if errors:
        return False, errors
    if result["gate"].get("decision") == "fail":
        return False, ["UI Spec Completeness Check failed."]
    return True, []


def collect_evidence_report(artifacts_dir: Path) -> Path:
    report_path = artifacts_dir / "evidence-report.md"
    if not report_path.exists():
        write_text(report_path, "# Evidence Report\n")
    return report_path


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str = "") -> dict[str, Any]:
    ok, errors = validate_package_readiness(artifacts_dir)
    gate = load_json(artifacts_dir / "ui-spec-freeze-gate.json") if (artifacts_dir / "ui-spec-freeze-gate.json").exists() else {}
    write_json(artifacts_dir / "supervision-evidence.json", {"workflow_key": "dev.feat-to-ui", "run_id": run_id, "artifacts_dir": str(artifacts_dir), "decision": gate.get("decision", "fail"), "review_completed_at": utc_now(), "gate_name": "UI Spec Completeness Check", "errors": errors})
    return {"ok": ok, "freeze_ready": ok, "errors": errors, "artifacts_dir": str(artifacts_dir), "evidence_report_ref": rel(collect_evidence_report(artifacts_dir), repo_root)}


def run_workflow(input_path: str | Path, feat_ref: str, repo_root: Path, run_id: str = "", allow_update: bool = False) -> dict[str, Any]:
    errors, context = validate_input_package(input_path, feat_ref, repo_root)
    return {"ok": False, "errors": errors, "input_path": str(Path(input_path).resolve())} if errors else build_package(context, repo_root, run_id, allow_update)


def command_run(args: argparse.Namespace) -> int:
    result = run_workflow(args.input, args.feat_ref, repo_root_from(args.repo_root), args.run_id or "", args.allow_update)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_executor_run(args: argparse.Namespace) -> int:
    result = run_workflow(args.input, args.feat_ref, repo_root_from(args.repo_root), args.run_id or "", args.allow_update)
    print(json.dumps(result, ensure_ascii=False))
    return 0


def command_supervisor_review(args: argparse.Namespace) -> int:
    result = supervisor_review(Path(args.artifacts_dir).resolve(), repo_root_from(args.repo_root), args.run_id or "")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("freeze_ready") else 1


def command_validate_input(args: argparse.Namespace) -> int:
    errors, result = validate_input_package(args.input, args.feat_ref, repo_root_from(args.repo_root))
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_validate_output(args: argparse.Namespace) -> int:
    errors, result = validate_output_package(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_collect_evidence(args: argparse.Namespace) -> int:
    print(json.dumps({"ok": True, "report_path": str(collect_evidence_report(Path(args.artifacts_dir).resolve()))}, ensure_ascii=False))
    return 0


def command_validate_package_readiness(args: argparse.Namespace) -> int:
    ok, errors = validate_package_readiness(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the feat-to-ui workflow.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in [("run", command_run), ("executor-run", command_executor_run)]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--input", required=True)
        cmd.add_argument("--feat-ref", required=True)
        cmd.add_argument("--repo-root")
        cmd.add_argument("--run-id")
        cmd.add_argument("--allow-update", action="store_true")
        cmd.set_defaults(func=func)
    review = sub.add_parser("supervisor-review")
    review.add_argument("--artifacts-dir", required=True)
    review.add_argument("--repo-root")
    review.add_argument("--run-id")
    review.set_defaults(func=command_supervisor_review)
    vin = sub.add_parser("validate-input")
    vin.add_argument("--input", required=True)
    vin.add_argument("--feat-ref", required=True)
    vin.add_argument("--repo-root")
    vin.set_defaults(func=command_validate_input)
    vout = sub.add_parser("validate-output")
    vout.add_argument("--artifacts-dir", required=True)
    vout.set_defaults(func=command_validate_output)
    ev = sub.add_parser("collect-evidence")
    ev.add_argument("--artifacts-dir", required=True)
    ev.set_defaults(func=command_collect_evidence)
    ready = sub.add_parser("validate-package-readiness")
    ready.add_argument("--artifacts-dir", required=True)
    ready.set_defaults(func=command_validate_package_readiness)
    freeze = sub.add_parser("freeze-guard")
    freeze.add_argument("--artifacts-dir", required=True)
    freeze.set_defaults(func=command_validate_package_readiness)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
