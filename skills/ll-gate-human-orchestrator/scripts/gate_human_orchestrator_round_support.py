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
            "excerpt": excerpt[:6],
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
    if str(payload.get("problem_statement", "")).strip():
        points.append("核对 problem_statement 是否同时说明当前失控行为、为什么必须现在收敛、以及不收敛的后果。")
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
