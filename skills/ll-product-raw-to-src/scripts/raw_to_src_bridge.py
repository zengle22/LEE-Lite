#!/usr/bin/env python3
"""
ADR bridge synthesis and review helpers for raw-to-src.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


ACCEPTANCE_DIMENSIONS = [
    "functional_closure",
    "user_story_experience",
    "feature_completeness",
    "logic_vulnerability",
    "industry_gap",
    "improvement_opportunities",
]
BRIDGE_ACCEPTANCE_DIMENSIONS = [
    "bridge_semantic_density",
    "downstream_actionability",
    "governance_constraint_clarity",
    "non_goal_explicitness",
]
GENERIC_PHRASES = {
    "受该问题影响的业务角色",
    "当原始问题被触发并需要正式需求源时。",
    "将原始问题收敛为下游可复用的正式需求源。",
    "下游需求链需要继承本次治理变化的边界与约束。",
    "保持与原始输入同题，不扩展到 EPIC、FEAT、TASK 或实现设计。",
}
META_PREFIXES = ("状态：", "日期：", "决策者：", "适用范围：", "相关 ADR：")


def _find_nested(payload: Any, *paths: str) -> Any:
    for path in paths:
        current = payload
        found = True
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
                continue
            found = False
            break
        if found and current not in (None, "", [], {}):
            return current
    return None


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _unique(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = item.strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(text)
    return ordered


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def _is_generic_text(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    if text in GENERIC_PHRASES:
        return True
    generic_patterns = [
        r"^受该问题影响的.+角色$",
        r"^当原始问题被触发并需要正式需求源时。",
        r"^将原始问题收敛为下游可复用的正式需求源。",
        r"^围绕《.+》建立稳定、可追溯的需求源。",
        r"^下游需求链需要继承本次治理变化的边界与约束。",
    ]
    return any(re.match(pattern, text) for pattern in generic_patterns)


def _is_title_echo(title: str, text: str) -> bool:
    normalized_title = _normalized(title)
    normalized_text = _normalized(text)
    if not normalized_title or not normalized_text:
        return False
    if normalized_text == normalized_title:
        return True
    return normalized_text.startswith(normalized_title) and len(normalized_text) - len(normalized_title) < 16


def _looks_like_adr_heading(text: str) -> bool:
    return bool(re.match(r"^(?:#\s*)?ADR[-\s]?\d+\b", text.strip(), flags=re.IGNORECASE))


def _clean_markdown_line(value: str) -> str:
    text = value.strip()
    if not text or text == "---":
        return ""
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^[*-]\s*", "", text)
    text = text.replace("`", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    if any(text.startswith(prefix) for prefix in META_PREFIXES):
        return ""
    if re.match(r"^\d+(?:\.\d+)*\s*[：:.、-]\s*", text):
        return ""
    if re.match(r"^\d+(?:\.\d+)*\s+\S+$", text):
        return ""
    return text


def _trim_terminal_punctuation(value: str) -> str:
    return value.strip().rstrip("。；;，,：:")


def _compact_fragment(value: str) -> str:
    text = _trim_terminal_punctuation(value)
    for prefix in ("从而导致", "这会直接造成", "这会导致", "最终结果不是“目录有点乱”，而是", "最终结果不是目录有点乱，而是"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    return text


def _meaningful_body_lines(document: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for raw_line in str(document.get("body", "")).splitlines():
        cleaned = _clean_markdown_line(raw_line)
        if not cleaned or _is_title_echo(document["title"], cleaned) or _looks_like_adr_heading(cleaned):
            continue
        if len(_normalized(cleaned)) < 6:
            continue
        lines.append(cleaned)
    return _unique(lines)


def _select_lines(lines: list[str], keywords: tuple[str, ...], limit: int = 3) -> list[str]:
    selected = [line for line in lines if any(keyword in line for keyword in keywords)]
    return _unique(selected[:limit])


def _select_focus_statement(document: dict[str, Any]) -> str:
    preferred = _first_non_empty(document.get("problem_statement"))
    if preferred and not _is_title_echo(document["title"], preferred) and not _looks_like_adr_heading(preferred):
        return preferred
    lines = _meaningful_body_lines(document)
    keywords = ("自由能力", "受控能力", "导致", "失效", "漂移", "越权", "路径猜测", "不可信", "污染")
    for line in lines:
        if any(keyword in line for keyword in keywords):
            return line
    return lines[0] if lines else preferred


def _extract_failure_modes(document: dict[str, Any], fallback: str) -> list[str]:
    explicit_problem = document.get("problem_statement", "") if "## 问题陈述" in str(document.get("body", "")) else ""
    lines = _unique(
        [
            cleaned
            for raw_line in str(explicit_problem).splitlines()
            if (cleaned := _clean_markdown_line(raw_line)) and not _is_title_echo(document["title"], cleaned)
        ]
    ) or _meaningful_body_lines(document)
    keywords = ("落点", "覆盖", "路径猜测", "消费", "散写", "临时", "越权", "注册", "信任", "漂移", "失控", "污染")
    findings = _select_lines(lines, keywords)
    if not findings and fallback:
        findings = [fallback]
    return _unique(findings[:3])


def _extract_consequences(document: dict[str, Any]) -> list[str]:
    lines = _meaningful_body_lines(document)
    weighted_keywords = {
        "无法": 5,
        "不可信": 5,
        "污染": 5,
        "不稳定": 4,
        "失效": 4,
        "下降": 4,
        "修错": 4,
        "找错": 4,
        "侵蚀": 3,
        "失控": 3,
        "导致": 2,
        "后果": 2,
        "成本": 1,
    }
    scored: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        score = sum(weight for keyword, weight in weighted_keywords.items() if keyword in line)
        if score:
            scored.append((score, -index, line))
    ranked = [line for _, _, line in sorted(scored, key=lambda item: (-item[0], item[1], len(item[2])))]
    return _unique(ranked[:3])


def _is_mainline_bridge(governance_objects: list[str]) -> bool:
    return all(keyword in " ".join(governance_objects).lower() for keyword in ("双会话双队列", "handoff runtime", "external gate"))


def _has_source_ref(source_refs: list[str], target: str) -> bool:
    return target.upper() in {str(item).strip().upper() for item in source_refs}


def _derive_unified_principle(governance_objects: list[str]) -> str:
    primary = "、".join(governance_objects[:3]) if governance_objects else "统一治理边界"
    if _is_mainline_bridge(governance_objects):
        return f"{primary} 统一构成主链治理闭环，下游必须按同一继承源消费，不得依赖分散约定。"
    return f"正式文件读写统一纳入围绕 {primary} 的治理边界，不再依赖分散约定。"


def _compose_problem_statement(focus_statement: str, failure_modes: list[str], consequences: list[str], unification_reason: str) -> str:
    parts: list[str] = []
    if focus_statement and not _is_title_echo(focus_statement, unification_reason):
        parts.append(focus_statement)
    if failure_modes:
        parts.append(f"当前执行链已经出现{'、'.join(_compact_fragment(item) for item in failure_modes[:3])}等失控行为。")
    if consequences:
        parts.append(f"这会直接造成{'、'.join(_compact_fragment(item) for item in consequences[:3])}。")
    parts.append(unification_reason)
    return " ".join(part for part in parts if part.strip())


def _compose_business_drivers(
    governance_objects: list[str],
    consequences: list[str],
    downstream_requirements: list[str],
) -> list[str]:
    consequence_clause = "、".join(_compact_fragment(item) for item in consequences[:2]) if consequences else "下游消费、审计和交付对象持续不稳定"
    governance_clause = "、".join(governance_objects[:3]) if governance_objects else "统一治理对象"
    requirements_clause = "；".join(_trim_terminal_punctuation(item) for item in downstream_requirements[:2]) if downstream_requirements else "下游必须继承统一治理边界"
    return _unique(
        [
            f"需要现在就把这类治理变化收敛成正式需求源，否则{consequence_clause}会继续沿后续需求链扩散。",
            f"将 ADR 归一为 bridge SRC 的价值，是让下游围绕 {governance_clause} 共享同一组继承约束，而不是继续各自猜路径或重写规则。",
            f"这能为后续链路提供稳定输入：{requirements_clause}。",
        ]
    )


def _compose_governance_summary(
    governance_objects: list[str],
    unification_principle: str,
    downstream_requirements: list[str],
) -> list[str]:
    return _unique(
        [
            f"治理对象：{'; '.join(governance_objects[:4])}",
            f"统一原则：{unification_principle}",
            f"下游必须继承的约束：{'; '.join(downstream_requirements[:3])}",
        ]
    )


def _replace_generic_list(existing: list[str], derived: list[str]) -> list[str]:
    if not existing or all(_is_generic_text(item) for item in existing):
        return _unique(derived)
    return _unique(existing)


def _derive_governance_objects(document: dict[str, Any], constraints: list[str]) -> list[str]:
    title = document["title"]
    description = _first_non_empty(document.get("problem_statement"), _select_focus_statement(document))
    context = _first_non_empty(
        _find_nested(document.get("payload"), "requirement_overview.context", "context"),
        _select_focus_statement(document),
    )
    objects = [
        item for item in constraints
        if len(item.strip()) <= 24 and not re.search(r"[，。；;:：]|必须|不得|不应|负责|通过|进入", item)
    ]
    keyword_pairs = [
        ("双会话双队列", "双会话双队列闭环"),
        ("handoff runtime", "文件化 handoff runtime"),
        ("external gate", "external gate 独立裁决与物化"),
        ("materialization", "candidate package 与 formal object 分层"),
        ("artifact io gateway", "Artifact IO Gateway"),
        ("path policy", "Path Policy"),
        ("placement", "artifact 落点与放置规则"),
        ("manifest", "manifest 合同与产物声明"),
        ("路径", "路径与目录治理"),
        ("目录", "目录与 artifact 边界"),
        ("artifact", "artifact 输入输出边界"),
        ("io gateway", "Artifact IO Gateway"),
    ]
    combined = f"{title} {description} {context}".lower()
    for keyword, label in keyword_pairs:
        if keyword in combined:
            objects.append(label)
    if not objects:
        objects.append(f"{title} 涉及的治理边界")
    return _unique(objects)


def _derive_trigger_scenarios(governance_objects: list[str]) -> list[str]:
    scenarios: list[str] = []
    if _is_mainline_bridge(governance_objects):
        scenarios.append("当下游对象需要继承主链 loop、handoff、gate 与 materialization 边界时。")
    for item in governance_objects:
        lowered = item.lower()
        if "path" in lowered or "路径" in item or "目录" in item or "placement" in lowered:
            scenarios.append("当 skill 需要决定 artifact 目录、路径或落点策略时。")
        if "gateway" in lowered or "io" in lowered:
            scenarios.append("当 workflow 需要通过统一 IO 边界读取或写入 artifact 时。")
        if "manifest" in lowered:
            scenarios.append("当产物需要以 manifest 或 contract 声明输入输出边界时。")
    if not scenarios:
        scenarios.append("当治理类变更需要被下游 skill 继承时。")
    return _unique(scenarios)


def _derive_downstream_requirements(governance_objects: list[str], constraints: list[str]) -> list[str]:
    primary = "、".join(governance_objects[:3]) if governance_objects else "统一治理闭环"
    return [
        f"下游需求链必须将 {primary} 视为同一治理闭环的组成部分统一继承，不得在本链路中重新发明等价规则。"
    ]


def _derive_target_users(document: dict[str, Any]) -> list[str]:
    if len(document.get("target_users", [])) >= 2 and not all(_is_generic_text(item) for item in document["target_users"]):
        return _unique(document["target_users"])
    return _unique(
        document.get("target_users", [])
        + [
            "受该治理规则约束的 skill 作者",
            "workflow / orchestration 设计者",
            "human gate / reviewer",
            "artifact 管理与治理消费者",
        ]
    )


def _derive_in_scope(governance_objects: list[str]) -> list[str]:
    if _is_mainline_bridge(governance_objects):
        return [
            "定义主链中 skill 文件读写、artifact 输入输出边界、路径策略与 handoff、gate、formal materialization 的统一治理边界。",
            "为后续主链对象提供统一继承源与交接依据，不展开实现设计。",
        ]
    return [
        "定义 skill 文件读写、artifact 输入输出边界与路径策略的统一治理边界。",
        "为后续主链对象提供统一约束来源与交接依据，而不是在本层展开 API 或实现设计。",
    ]


def _derive_acceptance_impact(_: list[str], __: list[str]) -> list[str]:
    return _unique(
        [
            "下游 gate、auditor 与 handoff 必须基于同一组受治理边界判断正式产物是否合法。",
            "下游消费方应能在不回读原始 ADR 的前提下理解主要失控行为与统一治理理由。",
            "审计链应能回答谁推进了 candidate、谁做了 final decision、为什么允许推进、正式物化了什么对象。",
        ]
    )

def _append_missing(items: list[str], additions: list[str]) -> list[str]:
    existing = {item.strip() for item in items}; return items + [item for item in additions if item.strip() not in existing]


def synthesize_adr_bridge_candidate(candidate: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    working = deepcopy(candidate)
    payload = document.get("payload")
    focus_statement = _select_focus_statement(document)
    explicit_problem = document.get("problem_statement", "") if "## 问题陈述" in str(document.get("body", "")) else ""
    description = _first_non_empty(focus_statement, document.get("problem_statement"), document.get("body", ""))
    context = _first_non_empty(
        _find_nested(payload, "requirement_overview.context", "context"),
        focus_statement,
    )
    drivers = _unique(document.get("business_drivers", []))
    constraints = _unique(document.get("key_constraints", []))
    non_goals = _unique(document.get("non_goals", []))
    governance_objects = _derive_governance_objects(document, constraints)
    downstream_requirements = _derive_downstream_requirements(governance_objects, constraints)
    failure_modes = _extract_failure_modes(document, context or description)
    consequences = _extract_consequences(document)
    unification_principle = _derive_unified_principle(governance_objects)
    acceptance_impact = _derive_acceptance_impact(failure_modes, consequences)
    change_scope = f"将《{working['title']}》涉及的{'、'.join(governance_objects[:3])}收敛为统一主链继承边界，明确 loop、handoff、gate 与 formal materialization 的协作责任。"
    if not change_scope: change_scope = f"{working['title']} 需要被重写为可继承的治理约束，而不是仅停留在 ADR 标题。"

    working["problem_statement"] = explicit_problem or _compose_problem_statement(focus_statement, failure_modes, consequences, unification_principle) or working["problem_statement"]
    working["target_users"] = _replace_generic_list(working["target_users"], _derive_target_users(document))
    working["trigger_scenarios"] = _replace_generic_list(
        working["trigger_scenarios"],
        _derive_trigger_scenarios(governance_objects),
    )
    working["business_drivers"] = _replace_generic_list(working["business_drivers"], drivers + _compose_business_drivers(governance_objects, consequences, downstream_requirements))
    working["key_constraints"] = _replace_generic_list(
        working["key_constraints"],
        constraints + [f"正式文件读写必须围绕 {'、'.join(governance_objects[:2])} 的统一边界建模，不得在下游恢复自由路径写入。"] + downstream_requirements,
    )
    working["in_scope"] = _derive_in_scope(governance_objects)
    working["out_of_scope"] = _replace_generic_list(working["out_of_scope"], non_goals)
    working["governance_change_summary"] = _compose_governance_summary(governance_objects, unification_principle, downstream_requirements)
    working["bridge_context"] = {
        "governed_by_adrs": deepcopy(working["source_refs"]),
        "change_scope": change_scope,
        "governance_objects": governance_objects,
        "current_failure_modes": failure_modes,
        "downstream_inheritance_requirements": downstream_requirements,
        "expected_downstream_objects": ["EPIC", "FEAT", "TASK"],
        "acceptance_impact": acceptance_impact,
        "non_goals": deepcopy(working["out_of_scope"]),
    }
    if _is_mainline_bridge(governance_objects) and _has_source_ref(working["source_refs"], "ADR-006"):
        working["source_refs"] = _append_missing(working["source_refs"], ["ADR-005"])
        working["in_scope"] = [working["in_scope"][0].replace("定义主链中 skill 文件读写、artifact 输入输出边界、路径策略与 handoff、gate、formal materialization 的统一治理边界。", "定义主链中 skill 文件读写、artifact 输入输出边界、路径策略如何接入 ADR-005 已提供的治理基础，以及 handoff、gate、formal materialization 的统一治理边界。")] + working["in_scope"][1:]
        working["out_of_scope"] = _append_missing(working["out_of_scope"], ["不在本 SRC 中重新实现 ADR-005 的 Gateway / Path Policy / Registry 模块，只冻结主链对其的消费边界。"])
        working["key_constraints"] = _append_missing(working["key_constraints"], ["external gate 必须以 approve、revise、retry、handoff、reject 形成唯一决策，不得并列批准语义。", "candidate package 仅作为 gate 消费对象；经 gate 批准并物化后的 formal object 才能作为下游正式输入。", "ADR-005 作为主链文件 IO / 路径治理前置基础；本 SRC 只冻结主链对其的消费边界，不重写其模块。"])
        working["governance_change_summary"] = _append_missing(working["governance_change_summary"], ["决策语义：external gate 必须输出 approve、revise、retry、handoff、reject 之一作为唯一最终决策。", "输入/物化边界：candidate package 是 gate 消费对象；formal object 是 gate 批准后供下游消费的正式输入。", "前置基础：ADR-005 为主链文件 IO / 路径治理提供已交付治理基础，本 SRC 只冻结主链对其的消费边界。"])
        working["bridge_context"]["governed_by_adrs"] = deepcopy(working["source_refs"]); working["bridge_context"]["non_goals"] = deepcopy(working["out_of_scope"])
    return working


def semantic_review(candidate: dict[str, Any], duplicate_path: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    if duplicate_path is not None:
        findings.append({"severity": "P1", "type": "duplicate_title", "description": f"Duplicate SRC title already exists at {duplicate_path}"})
    if re.search(r"\b(epic|feat|task)\b", candidate["problem_statement"], flags=re.IGNORECASE):
        findings.append({"severity": "P1", "type": "layer_boundary", "description": "Problem statement drifts into downstream artifact layers."})
    semantic_lock = candidate.get("semantic_lock") or {}
    if semantic_lock:
        required_fields = ["domain_type", "one_sentence_truth", "primary_object", "lifecycle_stage", "inheritance_rule"]
        missing_fields = [field for field in required_fields if not semantic_lock.get(field)]
        if missing_fields:
            findings.append(
                {
                    "severity": "P1",
                    "type": "semantic_lock_incomplete",
                    "description": f"semantic_lock is missing required fields: {', '.join(missing_fields)}.",
                }
            )
        if not semantic_lock.get("allowed_capabilities") or not semantic_lock.get("forbidden_capabilities"):
            findings.append(
                {
                    "severity": "P1",
                    "type": "semantic_lock_capability_bounds_missing",
                    "description": "semantic_lock must declare both allowed_capabilities and forbidden_capabilities.",
                }
            )
    if candidate["source_kind"] == "governance_bridge_src":
        bridge = candidate.get("bridge_context") or {}
        if not bridge:
            findings.append({"severity": "P1", "type": "missing_bridge_context", "description": "ADR-derived candidate is missing bridge context."})
        if _is_title_echo(candidate["title"], candidate["problem_statement"]):
            findings.append({"severity": "P1", "type": "title_echo_problem_statement", "description": "Problem statement is largely a title rewrite and does not explain the current governance problem."})
        generic_sections = [
            name
            for name, values in [
                ("target_users", candidate.get("target_users", [])),
                ("trigger_scenarios", candidate.get("trigger_scenarios", [])),
                ("business_drivers", candidate.get("business_drivers", [])),
                ("key_constraints", candidate.get("key_constraints", [])),
                ("change_scope", [bridge.get("change_scope", "")]),
                ("acceptance_impact", bridge.get("acceptance_impact", [])),
            ]
            if values and all(_is_generic_text(str(item)) for item in values)
        ]
        if generic_sections:
            findings.append({"severity": "P1", "type": "generic_placeholder_content", "description": f"Bridge SRC still contains generic placeholder content in: {', '.join(generic_sections)}."})
        weak_change_scope = _is_title_echo(candidate["title"], bridge.get("change_scope", ""))
        if weak_change_scope:
            findings.append({"severity": "P1", "type": "weak_bridge_change_scope", "description": "Bridge change_scope repeats the ADR title instead of summarizing the governance change."})
        required_fields = ["governance_objects", "current_failure_modes", "downstream_inheritance_requirements", "non_goals"]
        shallow_failure_modes = all(
            _is_title_echo(candidate["title"], str(item)) or len(str(item).strip()) < 20
            for item in bridge.get("current_failure_modes", [])
        )
        if any(not bridge.get(field) for field in required_fields) or weak_change_scope or shallow_failure_modes:
            findings.append({"severity": "P1", "type": "downstream_actionability_insufficient", "description": "Bridge context does not yet expose enough governance objects, failure modes, or downstream inheritance requirements for stable downstream consumption."})
    review = {
        "decision": "pass" if not findings else "revise",
        "summary": "No semantic issue detected." if not findings else f"{len(findings)} semantic findings detected.",
        "findings": findings,
    }
    return review, findings


def _bridge_acceptance_findings(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if candidate["source_kind"] != "governance_bridge_src":
        return findings

    bridge = candidate.get("bridge_context") or {}
    governance_summary = candidate.get("governance_change_summary", [])
    acceptance_impact = bridge.get("acceptance_impact", [])
    non_goals = bridge.get("non_goals", candidate.get("out_of_scope", []))
    constraints = candidate.get("key_constraints", [])

    if len(governance_summary) < 2:
        findings.append(
            {
                "severity": "P1",
                "type": "bridge_summary_insufficient",
                "description": "Governance bridge summary does not yet explain enough of the change for downstream consumers.",
            }
        )
    if len(acceptance_impact) < 2 or not any("继承" in item or "下游" in item for item in acceptance_impact):
        findings.append(
            {
                "severity": "P1",
                "type": "acceptance_impact_insufficient",
                "description": "Bridge acceptance impact is not explicit enough about downstream inheritance requirements.",
            }
        )
    if len(constraints) < 2 or not any("继承" in item or "约束" in item for item in constraints):
        findings.append(
            {
                "severity": "P1",
                "type": "governance_constraint_clarity_insufficient",
                "description": "Governance constraints are not explicit enough for freeze-readiness.",
            }
        )
    if not non_goals:
        findings.append(
            {
                "severity": "P1",
                "type": "non_goal_explicitness_insufficient",
                "description": "Bridge SRC does not yet make non-goals explicit enough for downstream inheritance.",
            }
        )
    return findings


def acceptance_review(candidate: dict[str, Any], source_review: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_findings = deepcopy(source_review["findings"])
    acceptance_findings: list[dict[str, Any]] = []
    dimensions = {name: {"status": "pass", "note": "No blocking issue detected."} for name in ACCEPTANCE_DIMENSIONS}
    if candidate["source_kind"] == "governance_bridge_src":
        dimensions.update({name: {"status": "pass", "note": "Bridge density is acceptable."} for name in BRIDGE_ACCEPTANCE_DIMENSIONS})
        bridge_acceptance_findings = _bridge_acceptance_findings(candidate)
        if any(item["type"] == "bridge_summary_insufficient" for item in bridge_acceptance_findings):
            dimensions["bridge_semantic_density"] = {"status": "revise", "note": "Governance summary is still too thin for downstream consumption."}
        if any(item["type"] == "acceptance_impact_insufficient" for item in bridge_acceptance_findings):
            dimensions["downstream_actionability"] = {"status": "revise", "note": "Acceptance impact does not yet make downstream inheritance explicit enough."}
        if any(item["type"] == "governance_constraint_clarity_insufficient" for item in bridge_acceptance_findings):
            dimensions["governance_constraint_clarity"] = {"status": "revise", "note": "Governance constraints are not yet explicit enough."}
        if any(item["type"] == "non_goal_explicitness_insufficient" for item in bridge_acceptance_findings):
            dimensions["non_goal_explicitness"] = {"status": "revise", "note": "Non-goals are not yet explicit enough."}
        acceptance_findings.extend(bridge_acceptance_findings)
    if source_findings:
        dimensions["feature_completeness"] = {"status": "revise", "note": "Defects remain after semantic review."}
        bridge_types = {"generic_placeholder_content", "title_echo_problem_statement", "weak_bridge_change_scope", "downstream_actionability_insufficient"}
        if candidate["source_kind"] == "governance_bridge_src" and any(item["type"] in bridge_types for item in source_findings):
            dimensions["bridge_semantic_density"] = {"status": "revise", "note": "Bridge SRC is still too thin for downstream consumption."}
            dimensions["downstream_actionability"] = {"status": "revise", "note": "Downstream cannot safely infer governance intent from the SRC alone."}
            dimensions["governance_constraint_clarity"] = {"status": "revise", "note": "Governance constraints are not yet explicit enough."}
            dimensions["non_goal_explicitness"] = {"status": "revise", "note": "Non-goals are not yet explicit enough for downstream inheritance."}
            acceptance_findings.append(
                {
                    "severity": "P1",
                    "type": "bridge_density_insufficient",
                    "description": "ADR-derived bridge SRC is too thin to act as a stable downstream source without reading the ADR.",
                    "linked_semantic_finding_types": [item["type"] for item in source_findings if item["type"] in bridge_types],
                }
            )
        acceptance_findings.append(
            {
                "severity": "P1",
                "type": "semantic_findings_unresolved",
                "description": "Semantic findings remain unresolved at acceptance review.",
                "linked_semantic_finding_types": [item["type"] for item in source_findings],
            }
        )
    report = {
        "decision": "approve" if not source_findings and not acceptance_findings else "revise",
        "dimensions": dimensions,
        "summary": "Acceptance review passed." if not source_findings and not acceptance_findings else "Acceptance review found unresolved semantic or acceptance risk.",
        "acceptance_findings": acceptance_findings,
    }
    return report, acceptance_findings
