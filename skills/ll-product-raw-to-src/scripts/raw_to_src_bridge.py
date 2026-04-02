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
    "semantic_preservation",
    "operator_surface_preservation",
    "contradiction_explicitness",
    "compression_risk",
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
ONBOARDING_DOCUMENT_MARKERS = (
    "用户建档",
    "user-onboarding",
    "onboarding",
    "最小建档页",
    "首页任务卡",
    "首轮 ai 建议",
    "profile_minimal_done",
    "device_connected",
    "initial_plan_ready",
)
ONBOARDING_PROJECTION_OBJECTS = {
    "minimal_onboarding_page",
    "running_level",
    "recent_injury_status",
    "onboarding_state_model",
    "first_ai_advice_output",
    "profile_storage_boundary",
    "device_connect_entry",
}
EMPTY_TEXT_MARKERS = {"none", "none.", "null", "n/a", "na", "未检测到", "未定义", "无"}
TRAINING_PLAN_DOCUMENT_MARKERS = (
    "训练计划",
    "training plan",
    "current_training_state",
    "risk gate",
    "plan_draft",
    "today_session",
    "body_checkin",
    "session_feedback",
    "micro_adjustment",
    "daily adjust",
    "今日训练卡",
    "微调",
)
TRAINING_PLAN_PROJECTION_OBJECTS = {
    "min_profile",
    "current_training_state",
    "risk_gate_result",
    "plan_draft",
    "today_session",
    "body_checkin",
    "session_feedback",
    "micro_adjustment",
    "plan_lifecycle",
}

DOWNSTREAM_LAYER_TOKENS = ("epic", "feat", "task")
DOWNSTREAM_LAYER_GUARD_PHRASES = (
    "继承边界",
    "治理边界",
    "统一边界",
    "同题",
    "不扩展到 epic",
    "不扩展到 feat",
    "不扩展到 task",
    "不展开实现设计",
    "不在本层展开",
    "不在此层展开",
)
DOWNSTREAM_LAYER_DRIFT_MARKERS = (
    "拆分",
    "分解",
    "实现设计",
    "实现细节",
    "任务拆分",
    "任务分解",
    "代码实现",
    "落到 epic",
    "落到 feat",
    "落到 task",
)


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


def _is_effectively_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip().casefold()
        return not text or text in EMPTY_TEXT_MARKERS
    if isinstance(value, dict):
        return all(_is_effectively_empty(item) for item in value.values())
    if isinstance(value, list):
        return all(_is_effectively_empty(item) for item in value)
    return False


def _has_meaningful_entries(value: Any) -> bool:
    if _is_effectively_empty(value):
        return False
    if isinstance(value, list):
        return any(not _is_effectively_empty(item) for item in value)
    if isinstance(value, dict):
        return any(not _is_effectively_empty(item) for item in value.values())
    return True


def _bundle_density_findings(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    projector_selection = candidate.get("projector_selection") or {}
    selected_facets = candidate.get("selected_facets") or projector_selection.get("selected_facets") or []
    bundle_kind = str(projector_selection.get("bundle_kind", "")).strip()
    if not projector_selection:
        findings.append(
            {
                "severity": "P1",
                "type": "projector_selection_missing",
                "description": "Facet-aware projector selection is required before a candidate can be freeze-ready.",
            }
        )
    if not selected_facets:
        findings.append(
            {
                "severity": "P1",
                "type": "selected_facets_missing",
                "description": "Facet-aware candidate must expose selected_facets so downstream composition can inherit the selected bundle.",
            }
        )
    if not candidate.get("facet_bundle_recommendation"):
        findings.append(
            {
                "severity": "P1",
                "type": "facet_bundle_recommendation_missing",
                "description": "Facet bundle recommendation is required so review can select the final high-fidelity bundle.",
            }
        )
    if not candidate.get("facet_inference"):
        findings.append(
            {
                "severity": "P1",
                "type": "facet_inference_missing",
                "description": "Facet inference is required so the bundle recommender has a non-empty semantic basis.",
            }
        )

    bridge_fields = ["target_capability_objects", "expected_outcomes", "downstream_derivation_requirements", "bridge_summary"]
    meaningful_bridge_fields = [field for field in bridge_fields if _has_meaningful_entries(candidate.get(field))]
    if len(meaningful_bridge_fields) < 4:
        findings.append(
            {
                "severity": "P1",
                "type": "semantic_density_insufficient",
                "description": "High-fidelity candidate must keep bridge summary, target objects, expected outcomes, and downstream requirements non-empty.",
            }
        )

    semantic_inventory = candidate.get("semantic_inventory") or {}
    inventory_fields = ["core_objects", "product_surfaces", "runtime_objects", "states", "entry_points", "commands", "constraints"]
    inventory_score = sum(1 for field in inventory_fields if _has_meaningful_entries(semantic_inventory.get(field)))
    if inventory_score < 4:
        findings.append(
            {
                "severity": "P1",
                "type": "semantic_inventory_too_thin",
                "description": "semantic_inventory is too thin; core_objects, product_surfaces, runtime_objects, states and commands must not collapse to empty shells.",
            }
        )

    if bundle_kind in {"onboarding", "training-plan"}:
        contract_fields = ["semantic_layer_declaration", "frozen_contracts", "structured_object_contracts", "enum_freezes"]
        if any(_is_effectively_empty(candidate.get(field)) for field in contract_fields):
            findings.append(
                {
                    "severity": "P1",
                    "type": "frozen_contract_density_insufficient",
                    "description": f"{bundle_kind} bundle must expose semantic_layer_declaration, frozen_contracts, structured_object_contracts, and enum_freezes as non-empty machine contracts.",
                }
            )
    return findings


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
        ("路径策略", "Path Policy"),
        ("路径治理", "Path Policy"),
        ("artifact path", "Path Policy"),
        ("placement", "artifact 落点与放置规则"),
        ("manifest", "manifest 合同与产物声明"),
        ("目录治理", "目录与 artifact 边界"),
        ("目录边界", "目录与 artifact 边界"),
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


def _is_onboarding_document_evidence(document: dict[str, Any] | None) -> bool:
    if not document:
        return False
    text = " ".join(
        [
            str(document.get("title", "")),
            str(document.get("problem_statement", "")),
            str(document.get("body", "")),
        ]
    ).lower()
    title_text = str(document.get("title", "")).lower()
    if "用户建档" in title_text or "user-onboarding" in title_text or "onboarding" in title_text:
        return True
    return sum(1 for token in ONBOARDING_DOCUMENT_MARKERS if token in text) >= 2


def _has_onboarding_projection(candidate: dict[str, Any]) -> bool:
    object_names = {
        str(item.get("object", "")).strip()
        for item in candidate.get("structured_object_contracts", [])
        if isinstance(item, dict)
    }
    applies_to = {
        str(value).strip()
        for contract in candidate.get("frozen_contracts", [])
        if isinstance(contract, dict)
        for value in contract.get("applies_to", [])
    }
    semantic_objects = {str(value).strip() for value in (candidate.get("semantic_inventory") or {}).get("core_objects", [])}
    target_objects = {str(value).strip() for value in candidate.get("target_capability_objects", [])}
    return bool((object_names | applies_to | semantic_objects | target_objects) & ONBOARDING_PROJECTION_OBJECTS)


def _is_training_plan_document_evidence(document: dict[str, Any] | None) -> bool:
    if not document:
        return False
    text = " ".join(
        [
            str(document.get("title", "")),
            str(document.get("problem_statement", "")),
            str(document.get("body", "")),
        ]
    ).lower()
    title_text = str(document.get("title", "")).lower()
    if "训练计划" in title_text or "training plan" in title_text:
        return True
    return sum(1 for token in TRAINING_PLAN_DOCUMENT_MARKERS if token in text) >= 3


def _has_training_plan_projection(candidate: dict[str, Any]) -> bool:
    object_names = {
        str(item.get("object", "")).strip()
        for item in candidate.get("structured_object_contracts", [])
        if isinstance(item, dict)
    }
    applies_to = {
        str(value).strip()
        for contract in candidate.get("frozen_contracts", [])
        if isinstance(contract, dict)
        for value in contract.get("applies_to", [])
    }
    semantic_objects = {str(value).strip() for value in (candidate.get("semantic_inventory") or {}).get("core_objects", [])}
    target_objects = {str(value).strip() for value in candidate.get("target_capability_objects", [])}
    return bool((object_names | applies_to | semantic_objects | target_objects) & TRAINING_PLAN_PROJECTION_OBJECTS)


def _append_missing(items: list[str], additions: list[str]) -> list[str]:
    existing = {item.strip() for item in items}; return items + [item for item in additions if item.strip() not in existing]


def _is_execution_runner_bridge(document: dict[str, Any], governance_objects: list[str], failure_modes: list[str]) -> bool:
    source_refs = {str(item).strip().upper() for item in document.get("source_refs", [])}
    text = " ".join(
        [
            str(document.get("title") or ""),
            str(document.get("problem_statement") or ""),
            " ".join(governance_objects),
            " ".join(failure_modes),
        ]
    ).lower()
    runner_markers = (
        "adr-018" in source_refs
        or "execution loop job runner" in text
        or "artifacts/jobs/ready" in text
        or "run-execution" in text
        or ("自动推进" in text and "job" in text)
    )
    return runner_markers


def _document_is_onboarding_like(document: dict[str, Any] | None) -> bool:
    if document is None:
        return False
    text = " ".join(
        [
            str(document.get("title", "")),
            str(document.get("problem_statement", "")),
            str(document.get("body", "")),
            " ".join(str(item) for item in document.get("source_refs", [])),
        ]
    ).lower()
    if not any(token in text for token in ("用户建档", "最小建档", "onboarding", "minimal-profile")):
        return False
    return any(token in text for token in ("running_level", "recent_injury_status", "capability flags", "首轮建议"))


def _candidate_contains_onboarding_projection(candidate: dict[str, Any]) -> bool:
    fields: list[str] = []
    fields.extend(str(item) for item in candidate.get("target_capability_objects", []))
    fields.extend(str(item.get("statement", "")) for item in candidate.get("frozen_contracts", []))
    fields.extend(str(item.get("object", "")) for item in candidate.get("structured_object_contracts", []))
    fields.extend(str(item) for item in (candidate.get("semantic_inventory") or {}).get("core_objects", []))
    fields.extend(str(item) for item in (candidate.get("semantic_inventory") or {}).get("product_surfaces", []))
    text = " ".join(fields).lower()
    return any(
        token in text
        for token in (
            "minimal_onboarding_page",
            "onboarding_state_model",
            "first_ai_advice_output",
            "device_connect_entry",
            "running_level",
            "recent_injury_status",
            "user_physical_profile",
        )
    )


def _document_is_training_plan_like(document: dict[str, Any] | None) -> bool:
    if document is None:
        return False
    text = " ".join(
        [
            str(document.get("title", "")),
            str(document.get("problem_statement", "")),
            str(document.get("body", "")),
            " ".join(str(item) for item in document.get("source_refs", [])),
        ]
    ).lower()
    if "训练计划" in text or "training plan" in text:
        return True
    return sum(1 for token in TRAINING_PLAN_DOCUMENT_MARKERS if token in text) >= 3


def _candidate_contains_training_plan_projection(candidate: dict[str, Any]) -> bool:
    fields: list[str] = []
    fields.extend(str(item) for item in candidate.get("target_capability_objects", []))
    fields.extend(str(item.get("statement", "")) for item in candidate.get("frozen_contracts", []))
    fields.extend(str(item.get("object", "")) for item in candidate.get("structured_object_contracts", []))
    fields.extend(str(item) for item in (candidate.get("semantic_inventory") or {}).get("core_objects", []))
    fields.extend(str(item) for item in (candidate.get("semantic_inventory") or {}).get("runtime_objects", []))
    text = " ".join(fields).lower()
    return any(token in text for token in TRAINING_PLAN_PROJECTION_OBJECTS)


def _meaningful_list(values: Any) -> list[str]:
    items: list[str] = []
    if isinstance(values, list):
        for value in values:
            text = str(value).strip()
            if text and text.lower() != "none":
                items.append(text)
    return items


def _object_contract(candidate: dict[str, Any], object_name: str) -> dict[str, Any]:
    for item in candidate.get("structured_object_contracts", []):
        if isinstance(item, dict) and str(item.get("object", "")).strip() == object_name:
            return item
    return {}


def _looks_like_object_token(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if len(text) > 48:
        return False
    return bool(re.fullmatch(r"[a-z0-9_:-]+", text))


def _machine_contract_section_empty(candidate: dict[str, Any], field: str) -> bool:
    value = candidate.get(field)
    if isinstance(value, dict):
        return not any(item not in (None, "", [], {}, "None") for item in value.values())
    if isinstance(value, list):
        return not any(str(item).strip() and str(item).strip().lower() != "none" for item in value)
    return value in (None, "", "None")


def _append_training_plan_density_findings(candidate: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    required_sections = ["semantic_layer_declaration", "frozen_contracts", "structured_object_contracts", "enum_freezes"]
    missing_sections = [field for field in required_sections if _machine_contract_section_empty(candidate, field)]
    if missing_sections:
        findings.append(
            {
                "severity": "P1",
                "type": "machine_contracts_missing",
                "description": f"Training-plan SRC is missing machine-contract sections: {', '.join(missing_sections)}.",
            }
        )
    semantic_inventory = candidate.get("semantic_inventory") or {}
    thin_fields = [
        field
        for field in ["core_objects", "product_surfaces", "entry_points", "runtime_objects", "states", "core_outputs"]
        if not _meaningful_list(semantic_inventory.get(field))
    ]
    if thin_fields:
        findings.append(
            {
                "severity": "P1",
                "type": "semantic_inventory_too_thin",
                "description": f"Training-plan semantic inventory is too thin in: {', '.join(thin_fields)}.",
            }
        )
    downstream_fields = [
        field
        for field in ["target_capability_objects", "expected_outcomes", "downstream_derivation_requirements", "bridge_summary"]
        if not _meaningful_list(candidate.get(field))
    ]
    if downstream_fields:
        findings.append(
            {
                "severity": "P1",
                "type": "downstream_actionability_insufficient",
                "description": f"Training-plan SRC does not yet expose enough downstream actionability in: {', '.join(downstream_fields)}.",
            }
        )
    required_object_names = {
        "min_profile",
        "current_training_state",
        "risk_gate_result",
        "plan_draft",
        "today_session",
        "body_checkin",
        "session_feedback",
        "micro_adjustment",
        "plan_generation_guardrail",
        "plan_lifecycle",
    }
    object_names = {
        str(item.get("object", "")).strip()
        for item in candidate.get("structured_object_contracts", [])
        if isinstance(item, dict)
    }
    missing_objects = sorted(required_object_names - object_names)
    if missing_objects:
        findings.append(
            {
                "severity": "P1",
                "type": "training_plan_objects_missing",
                "description": f"Training-plan object contracts are missing: {', '.join(missing_objects)}.",
            }
        )
    body_checkin = _object_contract(candidate, "body_checkin")
    body_required = set(_meaningful_list(body_checkin.get("required_fields")))
    missing_body_fields = sorted({"pain_trend", "readiness_to_train"} - body_required)
    if missing_body_fields:
        findings.append(
            {
                "severity": "P1",
                "type": "body_checkin_decision_fields_missing",
                "description": f"body_checkin is missing decision-critical required fields: {', '.join(missing_body_fields)}.",
            }
        )
    session_feedback = _object_contract(candidate, "session_feedback")
    session_optional = set(_meaningful_list(session_feedback.get("optional_fields")))
    conditional_required = session_feedback.get("conditional_required_fields") or {}
    if "deviation_reason" not in session_optional and "deviation_reason" not in _meaningful_list(session_feedback.get("required_fields")):
        findings.append(
            {
                "severity": "P1",
                "type": "session_feedback_deviation_reason_missing",
                "description": "session_feedback must preserve deviation_reason so unfinished sessions can drive different micro-adjustment decisions.",
            }
        )
    if "completed=false" not in conditional_required:
        findings.append(
            {
                "severity": "P1",
                "type": "session_feedback_condition_rule_missing",
                "description": "session_feedback must declare that completed=false requires deviation_reason.",
            }
        )
    min_profile = _object_contract(candidate, "min_profile")
    if not _meaningful_list(min_profile.get("bridge_split_recommendation")):
        findings.append(
            {
                "severity": "P1",
                "type": "min_profile_split_recommendation_missing",
                "description": "min_profile still looks overloaded; bridge-level split recommendation is missing.",
            }
        )
    plan_lifecycle = _object_contract(candidate, "plan_lifecycle")
    lifecycle_constraints = " ".join(_meaningful_list(plan_lifecycle.get("constraints"))).lower()
    if "intake runtime state" not in lifecycle_constraints and "ui page step" not in lifecycle_constraints:
        findings.append(
            {
                "severity": "P1",
                "type": "plan_lifecycle_onboarding_clarity_missing",
                "description": "plan_lifecycle must clarify that onboarding is an intake runtime state, not a UI page step.",
            }
        )
    guardrail = _object_contract(candidate, "plan_generation_guardrail")
    if not guardrail:
        findings.append(
            {
                "severity": "P1",
                "type": "guardrail_object_missing",
                "description": "Training-plan SRC must objectize plan_generation_guardrail instead of leaving guardrails only in prose contracts.",
            }
        )
    else:
        for field in ["minimum_checks", "failure_behavior", "output_contract"]:
            if not _meaningful_list(guardrail.get(field)):
                findings.append(
                    {
                        "severity": "P1",
                        "type": "guardrail_contract_incomplete",
                        "description": f"plan_generation_guardrail must declare {field} as a non-empty machine-readable field.",
                    }
                )
    bridge = candidate.get("bridge_context") or {}
    recommended_split = _meaningful_list(bridge.get("recommended_min_profile_split"))
    if len(recommended_split) < 4:
        findings.append(
            {
                "severity": "P1",
                "type": "bridge_split_recommendation_missing",
                "description": "Bridge context should recommend how min_profile can be decomposed downstream.",
            }
        )
    governance_objects = _meaningful_list(bridge.get("governance_objects"))
    if not governance_objects or not all(_looks_like_object_token(item) for item in governance_objects):
        findings.append(
            {
                "severity": "P1",
                "type": "bridge_governance_objects_invalid",
                "description": "bridge_context.governance_objects must be an object-name list, not copied prose constraints.",
            }
        )
    target_objects = set(_meaningful_list(candidate.get("target_capability_objects")))
    if recommended_split and target_objects & set(recommended_split):
        findings.append(
            {
                "severity": "P1",
                "type": "bridge_split_objects_mixed_into_target_objects",
                "description": "target_capability_objects should keep source/bridge core objects only; bridge split recommendation objects must stay in bridge_context.recommended_min_profile_split.",
            }
        )
    current_api_anchors = _meaningful_list(bridge.get("current_api_anchors"))
    if not current_api_anchors:
        findings.append(
            {
                "severity": "P1",
                "type": "current_api_anchors_missing",
                "description": "bridge_context.current_api_anchors must preserve current route anchors as bridge-level compatibility metadata.",
            }
        )
    core_apis = _meaningful_list((candidate.get("semantic_inventory") or {}).get("core_apis"))
    if core_apis and any(not item.startswith("current_api_anchor:") for item in core_apis):
        findings.append(
            {
                "severity": "P1",
                "type": "current_api_anchor_label_missing",
                "description": "Training-plan API references must be labeled as current_api_anchor values, not rendered as final authoritative API specs.",
            }
        )
    commands = _meaningful_list((candidate.get("semantic_inventory") or {}).get("commands"))
    normalized_api_anchors = {item.replace("current_api_anchor: ", "", 1).strip() for item in core_apis}
    normalized_commands = {
        item.replace("candidate_command_surface: ", "", 1).replace("derived_command_candidate: ", "", 1).strip()
        for item in commands
    }
    if normalized_api_anchors and normalized_commands and normalized_api_anchors == normalized_commands:
        findings.append(
            {
                "severity": "P1",
                "type": "duplicate_api_command_surfaces",
                "description": "Current API anchors and candidate command surfaces currently duplicate the same route set and should not both be frozen in semantic_inventory.",
            }
        )
    risk_gate = _object_contract(candidate, "risk_gate_result")
    risk_gate_required = set(_meaningful_list(risk_gate.get("required_fields")))
    enum_freezes = candidate.get("enum_freezes") or {}
    if "risk_gate_result" in enum_freezes and {"result", "outcome"} & risk_gate_required:
        findings.append(
            {
                "severity": "P1",
                "type": "risk_gate_naming_collision",
                "description": "risk_gate_result is used as both object name and enum field name; rename the enum field or object field to avoid downstream ambiguity.",
                }
            )


def _problem_statement_mentions_downstream_layer_drift(problem_statement: str) -> bool:
    text = problem_statement.strip()
    if not text:
        return False
    lowered = text.lower()
    if not any(token in lowered for token in DOWNSTREAM_LAYER_TOKENS):
        return False
    if any(phrase in lowered for phrase in DOWNSTREAM_LAYER_GUARD_PHRASES):
        return False
    return any(marker in text for marker in DOWNSTREAM_LAYER_DRIFT_MARKERS)


def _execution_runner_semantic_lock() -> dict[str, Any]:
    return {
        "domain_type": "execution_runner_rule",
        "one_sentence_truth": "gate approve 后必须生成 ready execution job，并由 Execution Loop Job Runner 自动消费 artifacts/jobs/ready 后推进到下一个 skill，而不是停在 formal publication 或人工接力。",
        "primary_object": "execution_loop_job_runner",
        "lifecycle_stage": "post_gate_auto_progression",
        "allowed_capabilities": [
            "ready_execution_job_materialization",
            "ready_queue_consumption",
            "next_skill_dispatch",
            "execution_result_recording",
            "retry_reentry_return",
        ],
        "forbidden_capabilities": [
            "formal_publication_substitution",
            "admission_only_decomposition",
            "third_session_human_relay",
            "directory_guessing_consumer",
        ],
        "inheritance_rule": "approve semantics must stay coupled to ready-job emission and runner-driven next-skill progression; downstream may not replace this with formal publication or admission-only flows.",
    }


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
    working["key_constraints"] = _append_missing(
        _replace_generic_list(working["key_constraints"], constraints),
        [
            f"正式文件读写必须围绕 {'、'.join(governance_objects[:2])} 的统一边界建模，不得在下游恢复自由路径写入。",
            *downstream_requirements,
            "下游继承约束必须显式声明主测试对象优先级、authority non-override、score-to-verdict 绑定、repair_target_artifact 与 counterexample coverage。",
        ],
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
    if not working.get("semantic_lock") and _is_execution_runner_bridge(document, governance_objects, failure_modes):
        working["semantic_lock"] = _execution_runner_semantic_lock()
    if _is_mainline_bridge(governance_objects) and _has_source_ref(working["source_refs"], "ADR-006"):
        working["source_refs"] = _append_missing(working["source_refs"], ["ADR-005"])
        working["in_scope"] = [working["in_scope"][0].replace("定义主链中 skill 文件读写、artifact 输入输出边界、路径策略与 handoff、gate、formal materialization 的统一治理边界。", "定义主链中 skill 文件读写、artifact 输入输出边界、路径策略如何接入 ADR-005 已提供的治理基础，以及 handoff、gate、formal materialization 的统一治理边界。")] + working["in_scope"][1:]
        working["out_of_scope"] = _append_missing(working["out_of_scope"], ["不在本 SRC 中重新实现 ADR-005 的 Gateway / Path Policy / Registry 模块，只冻结主链对其的消费边界。"])
        working["key_constraints"] = _append_missing(working["key_constraints"], ["external gate 必须以 approve、revise、retry、handoff、reject 形成唯一决策，不得并列批准语义。", "candidate package 仅作为 gate 消费对象；经 gate 批准并物化后的 formal object 才能作为下游正式输入。", "ADR-005 作为主链文件 IO / 路径治理前置基础；本 SRC 只冻结主链对其的消费边界，不重写其模块。"])
        working["governance_change_summary"] = _append_missing(working["governance_change_summary"], ["决策语义：external gate 必须输出 approve、revise、retry、handoff、reject 之一作为唯一最终决策。", "输入/物化边界：candidate package 是 gate 消费对象；formal object 是 gate 批准后供下游消费的正式输入。", "前置基础：ADR-005 为主链文件 IO / 路径治理提供已交付治理基础，本 SRC 只冻结主链对其的消费边界。"])
        working["bridge_context"]["governed_by_adrs"] = deepcopy(working["source_refs"]); working["bridge_context"]["non_goals"] = deepcopy(working["out_of_scope"])
    return working


def semantic_review(candidate: dict[str, Any], duplicate_path: Any, document: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    if duplicate_path is not None:
        findings.append({"severity": "P1", "type": "duplicate_title", "description": f"Duplicate SRC title already exists at {duplicate_path}"})
    if _problem_statement_mentions_downstream_layer_drift(candidate["problem_statement"]):
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
    if not candidate.get("semantic_inventory"):
        findings.append(
            {
                "severity": "P1",
                "type": "semantic_inventory_missing",
                "description": "SRC candidate is missing semantic_inventory, so high-fidelity source semantics cannot be reviewed.",
            }
        )
    if "source_provenance_map" not in candidate:
        findings.append(
            {
                "severity": "P1",
                "type": "source_provenance_missing",
                "description": "SRC candidate is missing source_provenance_map, so preservation traceability is incomplete.",
            }
        )
    if "normalization_decisions" not in candidate:
        findings.append(
            {
                "severity": "P1",
                "type": "normalization_decisions_missing",
                "description": "SRC candidate is missing normalization_decisions, so source compression choices are opaque.",
            }
        )
    if "omission_and_compression_report" not in candidate:
        findings.append(
            {
                "severity": "P1",
                "type": "compression_report_missing",
                "description": "SRC candidate is missing omission_and_compression_report, so compressed or omitted semantics are not explicit.",
            }
        )
    findings.extend(_bundle_density_findings(candidate))
    if _candidate_contains_onboarding_projection(candidate) and not _document_is_onboarding_like(document):
        findings.append(
            {
                "severity": "P0",
                "type": "source_topic_drift",
                "description": "Candidate introduces onboarding-specific contracts or objects that are not supported by the raw source topic.",
            }
        )
    if _has_onboarding_projection(candidate) and not _is_onboarding_document_evidence(document):
        findings.append(
            {
                "severity": "P0",
                "type": "domain_projection_mismatch",
                "description": "Candidate contains onboarding-specific contracts or objects, but the raw input does not provide onboarding-specific evidence.",
            }
        )
    if _candidate_contains_training_plan_projection(candidate) and not _document_is_training_plan_like(document):
        findings.append(
            {
                "severity": "P0",
                "type": "source_topic_drift",
                "description": "Candidate introduces training-plan-specific contracts or objects that are not supported by the raw source topic.",
            }
        )
    if _has_training_plan_projection(candidate) and not _is_training_plan_document_evidence(document):
        findings.append(
            {
                "severity": "P0",
                "type": "domain_projection_mismatch",
                "description": "Candidate contains training-plan-specific contracts or objects, but the raw input does not provide training-plan evidence.",
            }
        )
    contradiction_register = candidate.get("contradiction_register")
    if contradiction_register is None:
        findings.append(
            {
                "severity": "P1",
                "type": "contradiction_register_missing",
                "description": "SRC candidate is missing contradiction_register, so unresolved conflicts are not explicit.",
            }
        )
    if _document_is_training_plan_like(document) or _has_training_plan_projection(candidate):
        _append_training_plan_density_findings(candidate, findings)
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
        bridge_text = " ".join(
            [
                candidate.get("title", ""),
                candidate.get("problem_statement", ""),
                bridge.get("change_scope", ""),
                " ".join(bridge.get("current_failure_modes", [])),
            ]
        ).lower()
        needs_runtime_anchor = any(
            marker in bridge_text
            for marker in ("execution loop job runner", "artifacts/jobs/ready", "run-execution", "自动推进")
        )
        if needs_runtime_anchor and not semantic_lock:
            findings.append(
                {
                    "severity": "P1",
                    "type": "semantic_runtime_anchor_missing",
                    "description": "Bridge SRC describes a dominant runtime anchor but does not freeze it as semantic_lock, so downstream skills can drift into generic governance decomposition.",
                }
            )
        required_fields = ["governance_objects", "current_failure_modes", "downstream_inheritance_requirements", "non_goals"]
        shallow_failure_modes = all(
            _is_title_echo(candidate["title"], str(item)) or len(str(item).strip()) < 20
            for item in bridge.get("current_failure_modes", [])
        )
        if any(not bridge.get(field) for field in required_fields) or weak_change_scope or shallow_failure_modes:
            findings.append({"severity": "P1", "type": "downstream_actionability_insufficient", "description": "Bridge context does not yet expose enough governance objects, failure modes, or downstream inheritance requirements for stable downstream consumption."})
    raw_text = ""
    if document is not None:
        raw_text = " ".join(
            [
                str(document.get("title", "")),
                str(document.get("problem_statement", "")),
                str(document.get("body", "")),
                " ".join(document.get("source_refs", [])),
            ]
        ).lower()
    operator_surfaces = candidate.get("operator_surface_inventory", [])
    expects_operator_surface = any(
        marker in raw_text or marker in str((candidate.get("semantic_lock") or {}).get("one_sentence_truth", "")).lower()
        for marker in (
            "run-execution",
            "job claim",
            "job run",
            "job complete",
            "job fail",
            "workflow 入口",
            "cli-first",
            "backlog",
            "running jobs",
            "failed jobs",
            "deadletter",
            "execution loop job runner",
        )
    )
    if expects_operator_surface and not operator_surfaces:
        findings.append(
            {
                "severity": "P1",
                "type": "operator_surface_missing",
                "description": "Raw input exposes operator/CLI/monitor surfaces, but SRC did not preserve them in operator_surface_inventory.",
            }
        )
    omission_report = candidate.get("omission_and_compression_report") or {}
    high_risk_omissions = [
        item for item in omission_report.get("omitted_items", [])
        if str(item.get("downstream_risk", "")).strip().lower() == "high"
    ]
    if high_risk_omissions:
        findings.append(
            {
                "severity": "P1",
                "type": "high_risk_omission_present",
                "description": "SRC still reports high-risk omitted semantics and should not be treated as freeze-ready.",
            }
        )
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
    if not candidate.get("semantic_inventory"):
        findings.append(
            {
                "severity": "P1",
                "type": "semantic_preservation_insufficient",
                "description": "Bridge SRC does not yet expose a high-fidelity semantic inventory for downstream inheritance.",
            }
        )
    if "source_provenance_map" not in candidate:
        findings.append(
            {
                "severity": "P1",
                "type": "provenance_preservation_insufficient",
                "description": "Bridge SRC does not yet expose source provenance for normalized fields.",
            }
        )
    return findings


def acceptance_review(candidate: dict[str, Any], source_review: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_findings = deepcopy(source_review["findings"])
    acceptance_findings: list[dict[str, Any]] = []
    dimensions = {name: {"status": "pass", "note": "No blocking issue detected."} for name in ACCEPTANCE_DIMENSIONS}
    source_findings.extend(_bundle_density_findings(candidate))
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
        if any(item["type"] == "semantic_preservation_insufficient" for item in bridge_acceptance_findings):
            dimensions["semantic_preservation"] = {"status": "revise", "note": "High-fidelity semantic preservation is not yet explicit enough."}
        if any(item["type"] == "provenance_preservation_insufficient" for item in bridge_acceptance_findings):
            dimensions["semantic_preservation"] = {"status": "revise", "note": "Field provenance is not explicit enough."}
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
        if any(item["type"] in {"operator_surface_missing"} for item in source_findings):
            dimensions["operator_surface_preservation"] = {"status": "revise", "note": "Operator/CLI/monitor surfaces were not preserved from the raw source."}
        if any(item["type"] in {"contradiction_register_missing"} for item in source_findings):
            dimensions["contradiction_explicitness"] = {"status": "revise", "note": "Contradictions are not explicit enough for downstream consumption."}
        if any(item["type"] in {"compression_report_missing", "high_risk_omission_present"} for item in source_findings):
            dimensions["compression_risk"] = {"status": "revise", "note": "Compression risk is not explicit or remains too high."}
        if any(item["type"] in {"semantic_inventory_missing", "source_provenance_missing", "normalization_decisions_missing"} for item in source_findings):
            dimensions["semantic_preservation"] = {"status": "revise", "note": "High-fidelity source semantics are not preserved well enough."}
        if any(item["type"] in {"projector_selection_missing", "selected_facets_missing", "facet_bundle_recommendation_missing", "facet_inference_missing", "semantic_density_insufficient", "semantic_inventory_too_thin", "frozen_contract_density_insufficient"} for item in source_findings):
            dimensions["feature_completeness"] = {"status": "revise", "note": "Facet-aware candidate remains too thin to be freeze-ready."}
            dimensions["semantic_preservation"] = {"status": "revise", "note": "Facet-aware inherited semantics are still not dense enough."}
        if any(item["type"] in {"machine_contracts_missing", "semantic_inventory_too_thin"} for item in source_findings):
            dimensions["semantic_preservation"] = {"status": "revise", "note": "Machine-contract sections or semantic inventory are too thin for stable downstream derivation."}
        if any(item["type"] in {"downstream_actionability_insufficient"} for item in source_findings):
            dimensions["feature_completeness"] = {"status": "revise", "note": "Downstream inheritance requirements are still too thin for stable consumption."}
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
