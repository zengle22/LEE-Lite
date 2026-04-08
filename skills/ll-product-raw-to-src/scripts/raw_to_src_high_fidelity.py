"""High-fidelity candidate enrichment helpers for raw-to-src."""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any


def _slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "src"


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [item.strip("- ").strip() for item in re.split(r"[\n,;]", value) if item.strip()]
        return [item for item in parts if item]
    if isinstance(value, list):
        items: list[str] = []
        for entry in value:
            items.extend(_normalize_list(entry))
        return items
    return [str(value)]


def _unique_dicts(items: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for item in items:
        key = tuple(str(item.get(field, "")).strip().casefold() for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def _first_paragraph(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return paragraphs[0] if paragraphs else ""


def enrich_governance_bridge_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate["source_kind"] != "governance_bridge_src":
        return candidate
    bridge = candidate.get("bridge_context") or {}
    source_text = " ".join(
        [
            candidate.get("title", ""),
            candidate.get("problem_statement", ""),
            " ".join(candidate.get("key_constraints", [])),
            " ".join(bridge.get("governance_objects", [])),
        ]
    ).lower()
    if _is_qa_execution_candidate(source_text):
        return _enrich_qa_execution_bridge(candidate)
    return _enrich_generic_bridge(candidate, bridge)


def _enrich_qa_execution_bridge(candidate: dict[str, Any]) -> dict[str, Any]:
    dedupe = _dedupe_strings
    if not candidate.get("bridge_summary"):
        candidate["bridge_summary"] = dedupe(
            [
                "本 SRC 不重新论证上游 ADR 的正确性，而是将治理结论转译为下游需求链可直接继承的正式边界。",
                "下游不应再重新讨论核心边界，而应默认继承本 SRC 定义的对象模型、状态语义、冻结规则与证据约束。",
            ]
        )
    candidate["target_capability_objects"] = dedupe(candidate.get("target_capability_objects", []) + [
        "skill.qa.test_exec_web_e2e",
        "skill.runner.test_e2e",
        "TestEnvironmentSpec contract/schema",
        "TestCasePack contract/schema/revision policy",
        "ScriptPack contract/schema/revision policy",
        "EvidenceBundle minimum evidence policy",
        "TSE 主文件 contract",
        "run_status / acceptance_status 状态模型",
        "rerun / repair lifecycle contract",
    ])
    candidate["expected_outcomes"] = dedupe(candidate.get("expected_outcomes", []) + [
        "skill author 不再自行定义等价对象、状态语义或冻结规则。",
        "reviewer 可独立判断 run 是否可采信，以及是否已进入最终接受状态。",
        "report、bug、evidence 与 TSE 消费方可直接按统一 contract 读取产物。",
        "rerun / repair 不再依赖隐式口头约定或临时人工解释。",
        "human gate 可稳定区分 execution complete 与 acceptance complete。",
    ])
    candidate["downstream_derivation_requirements"] = dedupe(candidate.get("downstream_derivation_requirements", []) + [
        "宽 skill contract 与 lifecycle",
        "runner skill contract",
        "TestEnvironmentSpec schema 与 resolver",
        "TestCasePack / ScriptPack freeze、revision 与 repair hooks",
        "compliance、result judgment、output validation 分层",
        "run_status、acceptance_status 与 gate decision 模型",
        "EvidenceBundle minimum evidence policy",
        "rerun mode 与 lineage 规则",
    ])
    candidate["governance_change_summary"] = [
        "从分散的 workflow 模板、runner 和口头约定，升级为可继承的 QA test execution governed skill 边界。",
        "引入 TestEnvironmentSpec、TestCasePack、ScriptPack、EvidenceBundle、TSE 等结构化对象与冻结链。",
        "分离执行状态、合规状态与最终接受状态，并明确 rerun / repair / review 的继承规则。",
    ]
    candidate["in_scope"] = [
        "定义 QA test execution governed skill 的对象模型、状态语义、冻结链、证据规则与下游继承边界。",
        "为后续 contract、schema、policy、script、report、bug bundle 与 TSE 提供统一治理来源。",
    ]
    return candidate


def _enrich_generic_bridge(candidate: dict[str, Any], bridge: dict[str, Any]) -> dict[str, Any]:
    dedupe = _dedupe_strings
    if not candidate.get("bridge_summary"):
        candidate["bridge_summary"] = dedupe(
            [
                "本 SRC 的作用不是重复 ADR 论证，而是把治理结论转译成下游可直接继承的正式边界。",
                "下游应默认继承这里定义的治理对象、约束和交接边界，而不是重新发明等价规则。",
            ]
        )
    if not candidate.get("target_capability_objects"):
        candidate["target_capability_objects"] = dedupe(
            [f"{item} 对应的正式对象、contract 或 policy" for item in bridge.get("governance_objects", [])[:5]]
        )
    if not candidate.get("expected_outcomes"):
        candidate["expected_outcomes"] = dedupe(
            [
                "skill author 不再自行定义等价治理对象或边界。",
                "reviewer 可在不回读原始 ADR 的前提下判断候选是否满足主要约束。",
                "下游消费方可按统一 contract、boundary 与 lineage 读取正式对象。",
            ]
        )
    if not candidate.get("downstream_derivation_requirements"):
        candidate["downstream_derivation_requirements"] = dedupe(
            [
                "围绕治理对象定义正式 contract、schema、policy 与 lifecycle。",
                "把关键约束落成可校验的 validation、evidence 与 gate-ready 输出。",
                "确保下游 EPIC / FEAT / TASK 不遗漏主要治理对象与继承边界。",
            ]
        )
    return candidate


def _is_qa_execution_candidate(source_text: str) -> bool:
    qa_patterns = (
        r"\bqa test execution\b",
        r"\btestenvironmentspec\b",
        r"\btestcasepack\b",
        r"\bscriptpack\b",
        r"\btse\b",
        r"\bevidencebundle\b",
    )
    return any(re.search(pattern, source_text) for pattern in qa_patterns)


def _dedupe_strings(values: list[str]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text:
            key = text.casefold()
            if key not in seen:
                seen.add(key)
                items.append(text)
    return items


PROJECTOR_REGISTRY: list[dict[str, Any]] = [
    {
        "projector_id": "training-plan-projector",
        "bundle_kind": "training-plan",
        "priority": 100,
        "min_score": 3,
        "match_markers": [
            "current_training_state",
            "risk gate",
            "risk_gate_result",
            "plan_draft",
            "today_session",
            "body_checkin",
            "session_feedback",
            "micro_adjustment",
            "plan_lifecycle",
            "weekly_volume_km",
            "longest_run_km",
            "recent_consistency",
            "taper",
            "draft -> active",
            "only one active plan",
        ],
        "selected_facets": [
            "semantic_layer",
            "machine_contract",
            "object_model",
            "state_machine",
            "enumeration",
            "constraint",
            "workflow",
            "view_deliverable",
            "semantic_inventory",
            "provenance_normalization",
        ],
        "bundle_id": "training-plan-closed-loop",
        "bundle_summary": "训练计划 raw 具备闭环生成、执行反馈和微调语义，应冻结为高保真 training-plan bundle。",
    },
    {
        "projector_id": "onboarding-projector",
        "bundle_kind": "onboarding",
        "priority": 90,
        "min_score": 3,
        "match_markers": [
            "用户建档",
            "user-onboarding",
            "最小建档页",
            "首进主链",
            "profile_minimal_done",
            "device_connected",
            "initial_plan_ready",
            "first_ai_advice_output",
            "user_physical_profile",
            "homepage_task_cards",
        ],
        "selected_facets": [
            "actor_role",
            "object_model",
            "enumeration",
            "constraint",
            "workflow",
            "view_deliverable",
            "provenance_normalization",
        ],
        "bundle_id": "onboarding-minimal-profile",
        "bundle_summary": "用户建档 raw 具备首进链路和可渐进补全语义，应继续作为 onboarding bundle 处理。",
    },
    {
        "projector_id": "generic-projector",
        "bundle_kind": "generic",
        "priority": 10,
        "min_score": 0,
        "match_markers": [],
        "selected_facets": [
            "provenance_normalization",
            "constraint",
        ],
        "bundle_id": "generic-raw-requirement",
        "bundle_summary": "未命中更强领域 bundle 时，至少保留 provenance 和约束层的通用冻结。",
    },
]


def _projector_source_text(document: dict[str, Any] | None, candidate: dict[str, Any]) -> str:
    if document is not None:
        sections = document.get("sections") or {}
        return " ".join(
            [
                str(document.get("title", "")),
                str(document.get("problem_statement", "")),
                str(document.get("body", "")),
                " ".join(str(value) for value in sections.values()),
                " ".join(str(item) for item in document.get("source_refs", [])),
            ]
        ).lower()
    source_snapshot = candidate.get("source_snapshot") or {}
    return " ".join(
        [
            str(source_snapshot.get("title", "")),
            str(source_snapshot.get("body", "")),
            " ".join(str(item) for item in source_snapshot.get("source_refs", [])),
        ]
    ).lower()


def _build_facet_inference(selected_facets: list[str], matched_signals: list[str], projector_id: str) -> list[dict[str, Any]]:
    if not selected_facets:
        return []
    confidence = "high" if len(matched_signals) >= 3 else "medium"
    return [
        {
            "facet": facet,
            "confidence": confidence,
            "evidence": matched_signals[:5],
            "projector_id": projector_id,
        }
        for facet in selected_facets
    ]


def _select_projector_bundle(document: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    source_text = _projector_source_text(document, candidate)
    recommendations: list[dict[str, Any]] = []
    for spec in PROJECTOR_REGISTRY:
        matched_signals = [marker for marker in spec["match_markers"] if marker.lower() in source_text]
        score = len(matched_signals)
        recommendation = {
            "projector_id": spec["projector_id"],
            "bundle_kind": spec["bundle_kind"],
            "bundle_id": spec["bundle_id"],
            "priority": spec["priority"],
            "min_score": spec["min_score"],
            "selection_score": score,
            "matched_signals": matched_signals,
            "selected_facets": deepcopy(spec["selected_facets"]),
            "bundle_summary": spec["bundle_summary"],
            "selected": False,
        }
        recommendations.append(recommendation)

    eligible = [item for item in recommendations if item["selection_score"] >= item["min_score"]]
    if eligible:
        winner = max(eligible, key=lambda item: (item["selection_score"], item["priority"], len(item["selected_facets"])))
    else:
        winner = next(item for item in recommendations if item["bundle_kind"] == "generic")

    selected_facets = deepcopy(winner["selected_facets"])
    winner["selected"] = True
    projector_selection = {
        "projector_id": winner["projector_id"],
        "bundle_kind": winner["bundle_kind"],
        "bundle_id": winner["bundle_id"],
        "selected_facets": deepcopy(selected_facets),
        "matched_signals": deepcopy(winner["matched_signals"]),
        "selection_score": winner["selection_score"],
        "selection_basis": "max_signal_count_then_priority",
        "bundle_summary": winner["bundle_summary"],
    }
    if selected_facets:
        projector_selection["facet_density_class"] = "high" if len(selected_facets) >= 5 else "medium"
    return {
        "projector_selection": projector_selection,
        "facet_bundle_recommendation": recommendations,
        "facet_inference": _build_facet_inference(selected_facets, winner["matched_signals"], winner["projector_id"]),
        "selected_facets": selected_facets,
    }


def _merge_semantic_inventory(base: dict[str, Any], derived: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base) if base else {}
    authoritative_list_fields = {
        "core_objects",
        "core_states",
        "core_apis",
        "core_outputs",
        "product_surfaces",
        "entry_points",
        "commands",
        "runtime_objects",
        "states",
    }
    for key, value in derived.items():
        if key not in merged or not merged.get(key):
            merged[key] = deepcopy(value)
            continue
        if isinstance(merged[key], list) and isinstance(value, list):
            if key in authoritative_list_fields:
                merged[key] = _dedupe_strings([str(item) for item in merged[key]])
            else:
                merged[key] = _dedupe_strings([str(item) for item in merged[key]] + [str(item) for item in value])
        elif isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key].update(value)
    return merged


def _project_generic_raw_requirement_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("source_kind") != "raw_requirement":
        return candidate
    if candidate.get("bridge_summary"):
        return candidate

    problem = str(candidate.get("problem_statement") or "").strip()
    constraints = _normalize_list(candidate.get("key_constraints"))
    candidate["bridge_summary"] = _dedupe_strings(
        [
            f"本 SRC 需要把 {problem or candidate.get('title', 'raw requirement')} 收敛成可继承的正式边界。",
            "下游应默认继承这里定义的约束、来源追溯和最小冻结结构，而不是继续从 prose 重新猜结构。",
        ]
    )
    candidate["target_capability_objects"] = _dedupe_strings(
        candidate.get("target_capability_objects", [])
        + [
            "provenance_normalization",
            "constraint",
        ]
    )
    candidate["expected_outcomes"] = _dedupe_strings(
        candidate.get("expected_outcomes", [])
        + [
            "reviewer 可以在不回读外部原文的前提下理解当前 SRC 的最小冻结边界。",
            "下游 workflow 能继承来源追溯、约束和推导方向，而不是继续重写同一层语义。",
        ]
    )
    candidate["downstream_derivation_requirements"] = _dedupe_strings(
        candidate.get("downstream_derivation_requirements", [])
        + [
            "下游必须继承本 SRC 已显式记录的来源追溯与关键约束。",
            "若需要在下游重写语义，必须给出派生理由而不是默默改写事实层。",
        ]
    )
    candidate["governance_change_summary"] = _dedupe_strings(
        candidate.get("governance_change_summary", [])
        + [
            "generic raw requirement 也必须暴露可继承的边界，而不是只给摘要壳。",
            "bundle recommender 只提供保守的通用 facet 组合，不会把弱 raw 伪装成强领域 bundle。",
        ]
    )
    candidate["bridge_context"] = {
        "governed_by_adrs": deepcopy(candidate.get("source_refs", [])),
        "change_scope": problem or candidate.get("title", ""),
        "governance_objects": constraints[:5] if constraints else _normalize_list(candidate.get("target_users"))[:5],
        "current_failure_modes": _dedupe_strings([problem] if problem else []),
        "downstream_inheritance_requirements": _dedupe_strings(candidate["downstream_derivation_requirements"]),
        "expected_downstream_objects": ["normalized source", "frozen constraint", "derived consumer"],
        "acceptance_impact": _dedupe_strings(candidate["expected_outcomes"]),
        "non_goals": _normalize_list(candidate.get("out_of_scope")),
    }
    return candidate


def _build_training_plan_semantic_layer_declaration() -> dict[str, Any]:
    declaration = _build_semantic_layer_declaration()
    declaration["meta_layer"]["fields"] = declaration["meta_layer"]["fields"] + [
        "facet_inference",
        "facet_bundle_recommendation",
        "selected_facets",
        "projector_selection",
    ]
    return declaration


def extract_cli_commands(text: str) -> list[str]:
    commands: list[str] = []
    for match in re.findall(r"`(ll\s+[a-z0-9-]+(?:\s+[a-z0-9-]+){0,3})`", text, flags=re.IGNORECASE):
        commands.append(re.sub(r"\s+", " ", match).strip())
    for match in re.findall(r"\b(ll\s+(?:loop|job|gate|artifact|registry|audit|rollout)\s+[a-z0-9-]+(?:\s+[a-z0-9-]+)?)\b", text, flags=re.IGNORECASE):
        commands.append(re.sub(r"\s+", " ", match).strip())
    ordered: list[str] = []
    seen: set[str] = set()
    for command in commands:
        key = command.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(command)
    return ordered


def _matching_lines(body: str, patterns: list[str]) -> list[str]:
    lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line and any(pattern.lower() in line.lower() for pattern in patterns):
            lines.append(line)
    return lines


def _normalize_section_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"^#+\s*", "", raw_line).strip()
        line = re.sub(r"^[*-]\s*", "", line).strip()
        line = re.sub(r"^\d+(?:\.\d+)*\s*[：:.、-]\s*", "", line).strip()
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return _dedupe_strings(lines)


def _section_lines(document: dict[str, Any], section_name: str) -> list[str]:
    sections = document.get("sections") or {}
    return _normalize_section_lines(str(sections.get(section_name, "")).strip())


def derive_operator_surface_inventory(document: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    body = str(document.get("body", ""))
    source_refs = [str(item) for item in document.get("source_refs", [])]
    text = " ".join(
        [
            str(document.get("title", "")),
            str(document.get("problem_statement", "")),
            body,
            " ".join(source_refs),
            str((candidate.get("semantic_lock") or {}).get("one_sentence_truth", "")),
        ]
    )
    lowered = text.lower()
    inventory: list[dict[str, Any]] = []
    commands = extract_cli_commands(text)
    execution_runner = str((candidate.get("semantic_lock") or {}).get("domain_type") or "").strip().lower() == "execution_runner_rule"
    adr018_like = execution_runner or "adr-018" in {item.strip().lower() for item in source_refs} or "execution loop job runner" in lowered

    if adr018_like:
        inventory.append(
            {
                "entry_kind": "skill_entry",
                "name": "Execution Loop Job Runner",
                "purpose": "作为 operator-facing skill 入口启动 execution loop，并承接初始化与运行控制。",
                "lifecycle_phase": "start",
                "user_actor": "workflow / orchestration operator",
                "required_inputs": ["ready queue visibility", "runner binding or target scope"],
                "expected_outputs": ["runner start record", "execution loop state"],
                "source_refs": source_refs or ["ADR-018"],
            }
        )
        if "ll loop run-execution" not in {item.casefold() for item in commands}:
            commands.append("ll loop run-execution")

    for command in commands:
        phase = "run"
        if "run-execution" in command:
            phase = "start"
        elif "claim" in command:
            phase = "init"
        elif "complete" in command or "fail" in command:
            phase = "repair"
        inventory.append(
            {
                "entry_kind": "cli_control_surface",
                "name": command,
                "purpose": "通过 CLI 控制 execution loop 或 job lifecycle。",
                "lifecycle_phase": phase,
                "user_actor": "Claude/Codex CLI operator",
                "required_inputs": ["structured job or queue context"],
                "expected_outputs": ["structured execution state transition"],
                "source_refs": source_refs,
            }
        )

    observability_lines = _matching_lines(
        body,
        ["ready backlog", "running jobs", "aging jobs", "failed jobs", "deadletters", "waiting-human jobs", "监控", "观测", "backlog", "deadletter", "cli scan", "派生 report", "目录视图"],
    )
    if observability_lines or adr018_like:
        inventory.append(
            {
                "entry_kind": "monitor_surface",
                "name": "runner observability surface",
                "purpose": "向 operator 暴露 ready/running/failed/deadletter/waiting-human 等运行观测结果。",
                "lifecycle_phase": "monitor",
                "user_actor": "workflow / orchestration operator",
                "required_inputs": ["queue state", "job state", "failure evidence"],
                "expected_outputs": ["backlog view", "running view", "failure view"],
                "source_refs": source_refs or ["ADR-018"],
            }
        )

    return _unique_dicts(inventory, ["entry_kind", "name", "lifecycle_phase"])


def derive_semantic_inventory(document: dict[str, Any], candidate: dict[str, Any], operator_surface_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    semantic_lock = candidate.get("semantic_lock") or {}
    body = str(document.get("body", ""))
    commands = [item["name"] for item in operator_surface_inventory if item.get("entry_kind") == "cli_control_surface"]

    title_text = str(candidate.get("title") or "")
    problem_text = str(candidate.get("problem_statement") or "")
    hint_text = f"{title_text} {problem_text} {body}".lower()

    core_objects: list[str] = []
    if any(token in hint_text for token in ["payment", "\u652f\u4ed8", "checkout"]):
        core_objects.append("payment_attempt")
    if any(token in hint_text for token in ["retry", "\u91cd\u8bd5"]):
        core_objects.extend(["retry_policy", "retry_message"])
    if any(token in hint_text for token in ["failure code", "\u5931\u8d25\u7801"]):
        core_objects.append("failure_code")
    if not core_objects and title_text.strip():
        core_objects.append(title_text.strip())
    core_objects = _dedupe_strings(core_objects)

    runtime_objects = _normalize_list(semantic_lock.get("allowed_capabilities"))
    if str(semantic_lock.get("domain_type") or "").strip().lower() == "execution_runner_rule":
        runtime_objects = _normalize_list(runtime_objects + ["ready execution job", "claimed execution job", "next-skill invocation", "execution outcome"])
    elif not runtime_objects and core_objects:
        runtime_objects = _dedupe_strings(core_objects + ["user_visible_message"])

    if not commands and any(token in hint_text for token in ["retry", "\u91cd\u8bd5"]):
        commands = ["render_retry_message", "retry_payment"]
    monitor_surface_names = [item["name"] for item in operator_surface_inventory if item.get("entry_kind") == "monitor_surface"]
    observability_details = _matching_lines(body, ["ready backlog", "running jobs", "failed jobs", "deadletters", "waiting-human jobs"])
    observability = _normalize_list(monitor_surface_names + observability_details) or (["runner observability surface"] if "execution loop job runner" in body.lower() else [])
    entry_points = [item["name"] for item in operator_surface_inventory if item.get("entry_kind") in {"skill_entry", "cli_control_surface"}]
    return {
        "core_objects": core_objects,
        "actors": _normalize_list(candidate.get("target_users")),
        "product_surfaces": _normalize_list(candidate.get("target_capability_objects")) + _normalize_list(candidate.get("expected_outcomes")),
        "operator_surfaces": _normalize_list(entry_points + monitor_surface_names),
        "entry_points": entry_points,
        "commands": commands,
        "runtime_objects": runtime_objects,
        "states": _matching_lines(body, ["ready", "running", "done", "failed", "deadletter", "waiting-human", "retry", "claim"])[:8],
        "observability_surfaces": observability,
        "constraints": _normalize_list(candidate.get("key_constraints")),
        "non_goals": _normalize_list(candidate.get("out_of_scope")),
    }


def derive_source_provenance_map(document: dict[str, Any], candidate: dict[str, Any], operator_surface_inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_ref = (document.get("source_refs") or [Path(document["path"]).name])[0]
    sections = document.get("sections") or {}
    body = str(document.get("body", ""))
    source_snapshot = candidate.get("source_snapshot") or {}
    capture_metadata = source_snapshot.get("capture_metadata") or {}
    rows = [
        {
            "target_field": "problem_statement",
            "source_ref": source_ref,
            "source_section": "问题陈述" if sections.get("问题陈述") else "body",
            "source_excerpt": str(document.get("problem_statement") or _first_paragraph(body)).strip(),
            "preservation_mode": "normalized",
        }
    ]
    if source_snapshot:
        rows.append(
            {
                "target_field": "source_snapshot",
                "source_ref": source_ref,
                "source_section": "source_snapshot",
                "source_excerpt": str(source_snapshot.get("title") or document.get("title") or "").strip(),
                "preservation_mode": "frozen_snapshot",
                "frozen_ref": str(capture_metadata.get("frozen_ref", "")),
            }
        )
    for field in ["target_users", "trigger_scenarios", "business_drivers", "key_constraints"]:
        values = _normalize_list(candidate.get(field))
        if values:
            rows.append(
                {
                    "target_field": field,
                    "source_ref": source_ref,
                    "source_section": field,
                    "source_excerpt": values[0],
                    "preservation_mode": "normalized",
                }
            )
    if candidate.get("semantic_lock"):
        rows.append(
            {
                "target_field": "semantic_lock",
                "source_ref": source_ref,
                "source_section": "semantic_lock",
                "source_excerpt": str(candidate["semantic_lock"].get("one_sentence_truth", "")),
                "preservation_mode": "summarized",
            }
        )
    for field in ["semantic_layer_declaration", "frozen_contracts", "structured_object_contracts", "enum_freezes"]:
        if candidate.get(field):
            rows.append(
                {
                    "target_field": field,
                    "source_ref": source_ref,
                    "source_section": "建议方向",
                    "source_excerpt": str(candidate.get("title") or source_ref),
                    "preservation_mode": "machine_contract_projection",
                }
            )
    for item in operator_surface_inventory:
        rows.append(
            {
                "target_field": f"operator_surface_inventory.{item['entry_kind']}.{item['name']}",
                "source_ref": source_ref,
                "source_section": "body",
                "source_excerpt": item["name"],
                "preservation_mode": "normalized",
            }
        )
    return _unique_dicts(rows, ["target_field", "source_excerpt"])


def derive_contradiction_register(document: dict[str, Any]) -> list[dict[str, Any]]:
    lines = [line.strip() for line in str(document.get("body", "")).splitlines() if line.strip()]
    contradictions: list[dict[str, Any]] = []
    rule_pairs = [
        ("UI 控制台", ["不要求", "不需要"], ["必须", "应提供"]),
        ("第三会话", ["不需要", "不再需要"], ["需要", "必须"]),
        ("formal publication", ["不是", "不应"], ["必须", "应当"]),
    ]
    for topic, negative_markers, positive_markers in rule_pairs:
        negative_lines = [line for line in lines if topic.lower() in line.lower() and any(marker in line for marker in negative_markers)]
        positive_lines = [line for line in lines if topic.lower() in line.lower() and any(marker in line for marker in positive_markers)]
        if negative_lines and positive_lines:
            contradictions.append(
                {
                    "id": f"contradiction-{_slugify(topic)}",
                    "topic": topic,
                    "conflicting_statements": _normalize_list(negative_lines[:2] + positive_lines[:2]),
                    "current_resolution": "unresolved",
                    "requires_human_confirmation": True,
                }
            )
    return contradictions


def derive_normalization_decisions(document: dict[str, Any], candidate: dict[str, Any], operator_surface_inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions = [
        {
            "decision_type": "source_projection",
            "input_fragments": ["raw input title", "raw input body", "source refs"],
            "normalized_output": "src_candidate core fields",
            "justification": "将原始输入统一映射为主链兼容的标准字段。",
            "loss_risk": "low",
        },
        {
            "decision_type": "bridge_projection",
            "input_fragments": ["problem_statement", "constraints", "source_refs"],
            "normalized_output": "bridge_context and governance_change_summary",
            "justification": "为下游 workflow 提供兼容的 bridge projection，同时保留 high-fidelity source layer。",
            "loss_risk": "medium",
        },
    ]
    if candidate.get("semantic_lock"):
        decisions.append(
            {
                "decision_type": "semantic_lock_freeze",
                "input_fragments": ["dominant runtime or inheritance anchor"],
                "normalized_output": "semantic_lock",
                "justification": "避免下游 workflow 继续从 generic bridge prose 推断主导语义。",
                "loss_risk": "low",
            }
        )
    if operator_surface_inventory:
        decisions.append(
            {
                "decision_type": "operator_surface_preservation",
                "input_fragments": ["operator-facing commands and monitoring cues"],
                "normalized_output": "operator_surface_inventory",
                "justification": "避免 CLI/operator/control surface 在 SRC 层被静默压缩。",
                "loss_risk": "low",
            }
        )
    if candidate.get("semantic_layer_declaration"):
        decisions.append(
            {
                "decision_type": "semantic_layer_separation",
                "input_fragments": ["source layer facts", "bridge projection fields", "meta governance records"],
                "normalized_output": "semantic_layer_declaration",
                "justification": "显式声明 source / bridge / meta 的优先级，避免下游把桥接层误当成原始事实层。",
                "loss_risk": "low",
            }
        )
    if candidate.get("frozen_contracts") or candidate.get("structured_object_contracts") or candidate.get("enum_freezes"):
        decisions.append(
            {
                "decision_type": "machine_contract_extraction",
                "input_fragments": ["问题陈述", "建议方向", "补充硬约束"],
                "normalized_output": "frozen_contracts, structured_object_contracts, enum_freezes",
                "justification": "把分散在 prose 中的关键冻结事实收敛成机器优先的契约结构，降低下游继承漂移。",
                "loss_risk": "low",
            }
        )
    return decisions


def derive_omission_and_compression_report(document: dict[str, Any], candidate: dict[str, Any], operator_surface_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    compressed_items = [
        {"item": "problem_statement", "why": "正文会被整理为适合下游消费的规范化问题陈述。", "downstream_risk": "low"},
        {"item": "bridge_context", "why": "bridge projection 会把 raw 中分散的治理语义压缩为统一继承视图。", "downstream_risk": "medium"},
    ]
    omitted_items: list[dict[str, str]] = []
    domain_type = str((candidate.get("semantic_lock") or {}).get("domain_type") or "").strip().lower()
    if domain_type == "execution_runner_rule" and not operator_surface_inventory:
        omitted_items.append(
            {
                "item": "operator surface",
                "why": "未从输入中稳定解析出 operator-facing entry surface。",
                "downstream_risk": "high",
            }
        )
    return {
        "omitted_items": omitted_items,
        "compressed_items": compressed_items,
        "summary": "SRC 同时保留 high-fidelity source layer 和 bridge projection；任何压缩都必须显式记录。",
    }


def _onboarding_detection_text(document: dict[str, Any] | None, candidate: dict[str, Any]) -> str:
    if document is not None:
        sections = document.get("sections") or {}
        return " ".join(
            [
                str(document.get("title", "")),
                str(document.get("problem_statement", "")),
                str(document.get("body", "")),
                " ".join(str(value) for value in sections.values()),
                " ".join(str(item) for item in document.get("source_refs", [])),
            ]
        ).lower()
    source_snapshot = candidate.get("source_snapshot") or {}
    return " ".join(
        [
            str(source_snapshot.get("title", "")),
            str(source_snapshot.get("body", "")),
            " ".join(str(item) for item in source_snapshot.get("source_refs", [])),
        ]
    ).lower()


def _is_onboarding_candidate(candidate: dict[str, Any], document: dict[str, Any] | None = None) -> bool:
    if _is_training_plan_candidate(candidate, document):
        return False
    source_text = _onboarding_detection_text(document, candidate)
    strong_markers = (
        "用户建档",
        "user-onboarding",
        "最小建档页",
        "首页任务卡",
        "首轮 ai 建议",
        "profile_minimal_done",
        "device_connected",
        "initial_plan_ready",
        "minimal-profile",
        "首进主链",
    )
    title_text = str(candidate.get("title", "")).lower()
    if "用户建档" in title_text or "user-onboarding" in title_text:
        return True
    return sum(1 for token in strong_markers if token in source_text) >= 2


def _training_plan_detection_text(document: dict[str, Any] | None, candidate: dict[str, Any]) -> str:
    if document is not None:
        sections = document.get("sections") or {}
        return " ".join(
            [
                str(document.get("title", "")),
                str(document.get("problem_statement", "")),
                str(document.get("body", "")),
                " ".join(str(value) for value in sections.values()),
                " ".join(str(item) for item in document.get("source_refs", [])),
            ]
        ).lower()
    source_snapshot = candidate.get("source_snapshot") or {}
    return " ".join(
        [
            str(source_snapshot.get("title", "")),
            str(source_snapshot.get("body", "")),
            " ".join(str(item) for item in source_snapshot.get("source_refs", [])),
        ]
    ).lower()


def _is_training_plan_candidate(candidate: dict[str, Any], document: dict[str, Any] | None = None) -> bool:
    if candidate.get("source_kind") != "raw_requirement":
        return False
    source_text = _training_plan_detection_text(document, candidate)
    strong_markers = (
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
    title_text = str(candidate.get("title", "")).lower()
    if "训练计划" in title_text or "training plan" in title_text:
        return True
    return sum(1 for token in strong_markers if token in source_text) >= 3


def _build_semantic_layer_declaration() -> dict[str, Any]:
    return {
        "source_layer": {
            "role": "高保真冻结需求层",
            "authoritative_fields": [
                "problem_statement",
                "target_users",
                "trigger_scenarios",
                "business_drivers",
                "key_constraints",
                "in_scope",
                "out_of_scope",
                "source_snapshot",
                "frozen_contracts",
                "structured_object_contracts",
                "enum_freezes",
            ],
            "consumption_rule": "source_layer 是最高优先级事实层；bridge_layer 不得覆盖或重写 source_layer。",
        },
        "bridge_layer": {
            "role": "下游兼容投影层",
            "derived_fields": [
                "semantic_inventory",
                "target_capability_objects",
                "expected_outcomes",
                "downstream_derivation_requirements",
                "bridge_summary",
                "bridge_context",
                "governance_change_summary",
            ],
            "consumption_rule": "bridge_layer 只负责兼容下游 workflow 的消费视图，不得替代 source_layer 事实定义。",
        },
        "meta_layer": {
            "role": "追溯与治理元数据层",
            "fields": [
                "source_refs",
                "source_provenance_map",
                "normalization_decisions",
                "omission_and_compression_report",
                "contradiction_register",
                "operator_surface_inventory",
            ],
            "consumption_rule": "meta_layer 仅用于 lineage、治理和审计，不得重定义业务事实或替代 source_layer。",
        },
        "precedence_order": ["source_layer", "bridge_layer", "meta_layer"],
        "override_rule": "当 source_layer 与 bridge/meta layer 表达不一致时，必须以 source_layer 为准。",
    }


def _build_frozen_contracts() -> list[dict[str, Any]]:
    return [
        {
            "id": "FC-001",
            "statement": "首进主链仅允许 登录/注册 -> 最小建档页 -> 首页 -> AI 首轮建议。",
            "authoritative_layer": "source_layer",
            "applies_to": ["minimal_onboarding_page", "first_ai_advice_output"],
        },
        {
            "id": "FC-002",
            "statement": "最小建档页必须单页完成，且只能有一个提交动作。",
            "authoritative_layer": "source_layer",
            "applies_to": ["minimal_onboarding_page"],
        },
        {
            "id": "FC-003",
            "statement": "设备绑定不得阻塞首页进入，也不得阻塞首轮 AI 建议产出。",
            "authoritative_layer": "source_layer",
            "applies_to": ["device_connect_entry", "first_ai_advice_output"],
        },
        {
            "id": "FC-004",
            "statement": "running_level 必须使用单一训练基础轴 current_training_base，不得混入训练阶段、历史赛事经历或自由文本。",
            "authoritative_layer": "source_layer",
            "applies_to": ["running_level"],
        },
        {
            "id": "FC-005",
            "statement": "recent_injury_status 必须作为首轮风险门槛输入，且不得延后到首页补全。",
            "authoritative_layer": "source_layer",
            "applies_to": ["recent_injury_status", "first_ai_advice_output"],
        },
        {
            "id": "FC-006",
            "statement": "users / user_physical_profile / runner_profiles 不得重复存储身体字段；如出现跨对象冲突，必须以 user_physical_profile 为唯一事实源。",
            "authoritative_layer": "source_layer",
            "applies_to": ["profile_storage_boundary"],
        },
        {
            "id": "FC-007",
            "statement": "首轮建议最低输出必须包含训练建议级别、第一周行动建议、是否提示补充信息、是否提示连接设备。",
            "authoritative_layer": "source_layer",
            "applies_to": ["first_ai_advice_output"],
        },
        {
            "id": "FC-008",
            "statement": "onboarding 状态模型必须使用 primary_state + capability_flags；capability_flags 不得回写为页面流转状态机。",
            "authoritative_layer": "source_layer",
            "applies_to": ["onboarding_state_model"],
        },
        {
            "id": "FC-009",
            "statement": "扩展画像必须支持首页渐进补全与增量保存，不得设计为首日阻塞式完整表单。",
            "authoritative_layer": "source_layer",
            "applies_to": ["extended_profile", "homepage_task_cards"],
        },
    ]


def _build_enum_freezes() -> dict[str, Any]:
    return {
        "running_level": {
            "semantic_axis": "current_training_base",
            "allowed_values": ["beginner", "intermediate", "experienced"],
            "value_definitions": {
                "beginner": "尚不能稳定轻松连续跑 30 分钟，或刚开始恢复跑步。",
                "intermediate": "可稳定轻松完成约 5km 训练，具备基础训练承受能力。",
                "experienced": "已具备稳定训练基础，可承接更系统的结构化训练安排。",
            },
            "forbidden_semantics": ["race_history_only", "phase_label", "free_text"],
            "used_for": ["training_intensity_band", "weekly_volume_band", "first_advice_risk_gate"],
        },
        "recent_injury_status": {
            "semantic_axis": "current_running_limiting_condition",
            "allowed_values": ["none", "minor_but_runnable", "pain_or_recovering"],
            "value_definitions": {
                "none": "没有影响跑步的疼痛或伤病。",
                "minor_but_runnable": "有轻微不适但仍可跑步。",
                "pain_or_recovering": "有明显疼痛或正处于恢复中，应触发更保守建议。",
            },
            "forbidden_semantics": ["historical_injury_archive", "free_text", "deferred_collection"],
            "used_for": ["first_advice_risk_gate", "conservative_recovery_branch"],
        },
    }


def _build_structured_object_contracts() -> list[dict[str, Any]]:
    return [
        {
            "object": "minimal_onboarding_page",
            "purpose": "在首日最小输入下完成建档并立即释放首页与 AI 首轮建议。",
            "required_fields": ["gender", "birthdate", "height", "weight", "running_level", "recent_injury_status"],
            "optional_fields": ["nickname"],
            "canonical_field_policy": "年龄相关 canonical_field 必须为 birthdate；如前端临时采集 age，只能作为 transitional_input_alias，入库前必须归一化为 birthdate。",
            "transitional_input_aliases": {"age": "birthdate"},
            "forbidden_fields": ["best_record_time", "weekly_mileage_range", "goal_race_date", "device_binding"],
            "completion_effect": ["profile_minimal_done=true", "allow_homepage_entry=true", "enable_first_ai_advice=true"],
        },
        {
            "object": "running_level",
            "semantic_axis": "current_training_base",
            "allowed_values": ["beginner", "intermediate", "experienced"],
            "value_definitions": {
                "beginner": "尚不能稳定轻松连续跑 30 分钟，或刚开始恢复跑步。",
                "intermediate": "可稳定轻松完成约 5km 训练，具备基础训练承受能力。",
                "experienced": "已具备稳定训练基础，可承接更系统的结构化训练安排。",
            },
            "forbidden_semantics": ["race_history_only", "phase_label", "free_text"],
            "downstream_usage": ["training_intensity_band", "weekly_volume_band", "first_advice_risk_gate"],
        },
        {
            "object": "recent_injury_status",
            "purpose": "作为 AI 首轮建议的风险门槛输入。",
            "allowed_values": ["none", "minor_but_runnable", "pain_or_recovering"],
            "required_for_first_advice": True,
            "cannot_be_deferred": True,
            "downstream_usage": ["first_advice_risk_gate", "conservative_recovery_branch"],
        },
        {
            "object": "onboarding_state_model",
            "primary_state": ["registered", "profile_minimal_done"],
            "capability_flags": {
                "extended_profile_completed": "boolean",
                "device_connected": "boolean",
                "initial_plan_ready": "boolean",
            },
            "constraints": [
                "primary_state 只表达首进最低完成阶段。",
                "capability_flags 只表达增强能力完成情况。",
                "capability_flags 不得回写为页面流转状态机。",
            ],
        },
        {
            "object": "first_ai_advice_output",
            "minimum_outputs": ["training_advice_level", "first_week_action", "needs_more_info_prompt", "device_connect_prompt"],
            "blocked_by": ["missing_running_level", "missing_recent_injury_status"],
            "deferred_inputs": ["running_background_detail", "device_data_sync", "goal_race_plan"],
        },
        {
            "object": "profile_storage_boundary",
            "authoritative_profile_owner": "user_physical_profile",
            "physical_fields": ["gender", "birthdate", "height", "weight"],
            "runner_profile_fields": [
                "running_level",
                "running_experience",
                "best_record_type",
                "best_record_time",
                "weekly_mileage_range",
                "training_days_per_week",
                "goal_type",
                "goal_race_date",
                "has_device_data",
            ],
            "canonical_field_policy": "身体基础事实字段只允许在 user_physical_profile 中保留 canonical 版本。",
            "authoritative_conflict_rule": "当身体字段出现跨对象冲突时，必须以 user_physical_profile 为唯一事实源。",
            "forbidden_duplication": [
                "runner_profiles.gender",
                "runner_profiles.birthdate",
                "runner_profiles.height",
                "runner_profiles.weight",
            ],
        },
    ]


def _build_training_plan_frozen_contracts() -> list[dict[str, Any]]:
    return [
        {
            "id": "FC-101",
            "statement": "训练计划 MVP 主链路必须收敛为 min_profile + current_training_state -> risk_gate_result -> plan_draft -> plan_lifecycle(active) -> today_session -> body_checkin + session_feedback -> micro_adjustment，不得回退到完整产品式长链路。",
            "authoritative_layer": "source_layer",
            "applies_to": ["min_profile", "current_training_state", "risk_gate_result", "plan_draft", "plan_lifecycle", "today_session", "body_checkin", "session_feedback", "micro_adjustment"],
        },
        {
            "id": "FC-102",
            "statement": "risk_gate_result 必须作为生成前内联 gate 运行；不可拆回独立 risk 页面或独立前置流程。",
            "authoritative_layer": "source_layer",
            "applies_to": ["risk_gate_result", "plan_draft"],
        },
        {
            "id": "FC-103",
            "statement": "计划生成必须显式消费 current_training_state，且不得只依据画像、目标或设备占位信息推断训练能力。",
            "authoritative_layer": "source_layer",
            "applies_to": ["current_training_state", "risk_gate_result", "plan_draft"],
        },
        {
            "id": "FC-104",
            "statement": "计划草案输出必须以 plan_draft 概览与 today_session 为主，不得把完整解释型全量周表作为 MVP 主交付物。",
            "authoritative_layer": "source_layer",
            "applies_to": ["plan_draft", "today_session"],
        },
        {
            "id": "FC-105",
            "statement": "计划草案不得直接信任 LLM 输出，必须经过规则护栏层校验；违反训练日、长跑日、周跑量增长、高强度连续安排、taper 或伤病约束时必须修正或拒绝。",
            "authoritative_layer": "source_layer",
            "applies_to": ["plan_draft", "plan_generation_guardrail", "micro_adjustment"],
        },
        {
            "id": "FC-106",
            "statement": "body_checkin 与 session_feedback 必须共同构成日常闭环输入；Daily Adjust 不得只消费训练前状态。",
            "authoritative_layer": "source_layer",
            "applies_to": ["body_checkin", "session_feedback", "micro_adjustment"],
        },
        {
            "id": "FC-107",
            "statement": "plan_lifecycle 必须显式区分 draft 与 active；同一用户最多一个 active plan，但可存在多个 draft。",
            "authoritative_layer": "source_layer",
            "applies_to": ["plan_lifecycle", "plan_draft"],
        },
        {
            "id": "FC-108",
            "statement": "intensity_strategy 在 MVP 阶段必须由系统根据目标、基线、风险和伤病史内部推断，不得作为用户显式风险开关。",
            "authoritative_layer": "source_layer",
            "applies_to": ["risk_gate_result", "plan_draft"],
        },
    ]


def _build_training_plan_enum_freezes() -> dict[str, Any]:
    return {
        "risk_gate_outcome": {
            "semantic_axis": "generation_gate_outcome",
            "allowed_values": ["pass", "degraded", "blocked"],
            "value_definitions": {
                "pass": "输入通过最小风险门槛，可正常生成计划草案。",
                "degraded": "允许生成，但必须先降级目标、训练频次或质量课配置。",
                "blocked": "输入不满足最小安全前提，必须阻断生成并返回原因。",
            },
            "forbidden_semantics": ["independent_page_state", "soft_warning_only", "free_text"],
            "used_for": ["risk_gate_result.outcome", "plan_generation_gate", "goal_downgrade", "training_load_rewrite"],
        },
        "goal_priority": {
            "semantic_axis": "goal_outcome_priority",
            "allowed_values": ["finish", "pb"],
            "value_definitions": {
                "finish": "优先安全完赛与稳定执行。",
                "pb": "在安全边界内争取成绩提升。",
            },
            "forbidden_semantics": ["motivation_copy", "training_style", "free_text"],
            "used_for": ["risk_gate_result", "plan_draft", "micro_adjustment"],
        },
        "recent_consistency": {
            "semantic_axis": "recent_training_continuity",
            "allowed_values": ["none", "low", "medium", "high"],
            "value_definitions": {
                "none": "最近基本未形成连续训练。",
                "low": "有零散训练，但连续性较弱。",
                "medium": "已有较稳定训练习惯，但仍需保守推进。",
                "high": "近阶段训练连续性稳定，可承接更系统训练安排。",
            },
            "forbidden_semantics": ["fitness_score", "race_level", "free_text"],
            "used_for": ["current_training_state", "risk_gate_result", "plan_draft"],
        },
        "micro_adjustment_action": {
            "semantic_axis": "near_term_plan_adjustment",
            "allowed_values": ["keep", "downgrade", "replace", "skip"],
            "value_definitions": {
                "keep": "维持原训练安排。",
                "downgrade": "保留训练目的但降低强度、时长或距离。",
                "replace": "替换为更安全的训练内容。",
                "skip": "本次训练取消，恢复优先。",
            },
            "forbidden_semantics": ["long_term_plan_regeneration", "coach_note_only", "free_text"],
            "used_for": ["today_session", "micro_adjustment", "session_feedback"],
        },
        "micro_adjustment_target_scope": {
            "semantic_axis": "near_term_adjustment_window",
            "allowed_values": ["next_session", "next_3_days", "rest_of_week"],
            "value_definitions": {
                "next_session": "只调整下一次训练。",
                "next_3_days": "调整未来三天内的训练安排。",
                "rest_of_week": "调整本周余下训练安排。",
            },
            "forbidden_semantics": ["full_plan_scope", "free_text", "user_interface_label"],
            "used_for": ["micro_adjustment", "today_session"],
        },
        "readiness_to_train": {
            "semantic_axis": "same_day_execution_readiness",
            "allowed_values": ["yes", "uncertain", "no"],
            "value_definitions": {
                "yes": "当前状态允许按计划执行。",
                "uncertain": "当前状态存在不确定性，需要保守处理或降级。",
                "no": "当前状态不适合执行原计划，应跳过或替换。",
            },
            "forbidden_semantics": ["motivation_only", "free_text", "page_copy"],
            "used_for": ["body_checkin", "micro_adjustment", "today_session"],
        },
        "pain_trend": {
            "semantic_axis": "same_day_pain_direction",
            "allowed_values": ["new", "worse", "same", "better"],
            "value_definitions": {
                "new": "出现新的疼痛或不适。",
                "worse": "既有疼痛明显加重。",
                "same": "疼痛状态与近期基线相近。",
                "better": "疼痛较近期基线改善。",
            },
            "forbidden_semantics": ["body_part_only", "free_text", "severity_score_only"],
            "used_for": ["body_checkin", "risk_gate_result", "micro_adjustment"],
        },
        "plan_lifecycle_status": {
            "semantic_axis": "plan_runtime_status",
            "allowed_values": ["onboarding", "draft", "active", "completed", "cancelled"],
            "value_definitions": {
                "onboarding": "计划实体尚未生成前的 intake runtime state，而非 UI page step。",
                "draft": "计划草案已生成，但尚未激活。",
                "active": "当前唯一有效训练计划。",
                "completed": "计划按生命周期完成。",
                "cancelled": "计划已停止，不再继续执行。",
            },
            "forbidden_semantics": ["page_step", "ui_tab", "free_text"],
            "used_for": ["plan_lifecycle", "plan_draft", "today_session"],
        },
        "deviation_reason": {
            "semantic_axis": "why_session_deviated",
            "allowed_values": ["schedule_conflict", "fatigue", "pain", "illness", "motivation_low", "environmental", "unknown"],
            "value_definitions": {
                "schedule_conflict": "因时间或日程冲突未按计划完成。",
                "fatigue": "因疲劳过高未按计划完成。",
                "pain": "因疼痛或伤病风险未按计划完成。",
                "illness": "因生病或身体异常未按计划完成。",
                "motivation_low": "因动力不足未按计划完成。",
                "environmental": "因天气、场地等外部环境未按计划完成。",
                "unknown": "用户未给出明确原因。",
            },
            "forbidden_semantics": ["long_form_note_only", "free_text_only"],
            "used_for": ["session_feedback", "micro_adjustment"],
        },
        "intensity_strategy": {
            "semantic_axis": "system_derived_training_aggressiveness",
            "allowed_values": ["conservative", "standard", "stretched"],
            "value_definitions": {
                "conservative": "安全优先，适合较高风险或较低基线。",
                "standard": "默认平衡策略。",
                "stretched": "在安全前提下略有进取，但仍受规则护栏层约束。",
            },
            "forbidden_semantics": ["user_direct_choice", "aggressive_label", "free_text"],
            "used_for": ["risk_gate_result", "plan_draft"],
        },
    }


def _build_training_plan_structured_object_contracts() -> list[dict[str, Any]]:
    return [
        {
            "object": "min_profile",
            "purpose": "以最少输入释放训练计划 draft 生成，不再承载完整画像或设备接入。",
            "required_fields": [
                "age",
                "sex",
                "weight_kg",
                "running_age",
                "current_level_or_best_result",
                "race_type",
                "race_date",
                "goal_priority",
                "weekly_training_days",
                "long_run_day",
                "injury_history_summary",
                "has_current_pain_or_fatigue",
            ],
            "optional_fields": ["notes"],
            "forbidden_fields": ["device_binding", "history_sync", "preferred_time", "user_selected_intensity_level", "full_report_preferences"],
            "bridge_split_recommendation": ["runner_profile_min", "plan_goal_min", "training_availability_min", "risk_hint_min"],
            "completion_effect": ["allow_plan_generation=true", "risk_gate_input_ready=true"],
        },
        {
            "object": "current_training_state",
            "purpose": "作为风险 gate 与计划生成的训练能力基线，不依赖设备接入也可手填。",
            "required_fields": ["weekly_volume_km", "weekly_days", "longest_run_km", "recent_consistency"],
            "optional_fields": ["last_race_result", "training_continuity", "days_since_last_run"],
            "forbidden_fields": ["device_binding_required", "opaque_fitness_score_only"],
            "completion_effect": ["risk_gate_uses_baseline=true", "plan_generator_uses_baseline=true"],
        },
        {
            "object": "risk_gate_result",
            "purpose": "在生成前判断 pass/degraded/blocked，并在 degraded 时重写目标或训练偏好。",
            "required_fields": ["outcome", "reasons"],
            "optional_fields": ["downgraded_goal_priority", "downgraded_weekly_days", "downgraded_quality_sessions", "intensity_strategy"],
            "forbidden_fields": ["standalone_page_state", "ui_only_warning"],
            "completion_effect": ["blocked_stops_generation=true", "degraded_rewrites_generation_inputs=true"],
        },
        {
            "object": "plan_draft",
            "purpose": "承载可激活的计划草案，主输出为计划骨架、当前周和 today_session。",
            "required_fields": ["plan_status", "plan_overview", "current_week", "today_session", "safety_notes"],
            "optional_fields": ["key_sessions", "recovery_weeks", "generated_by"],
            "forbidden_fields": ["standalone_plan_confirm_page", "full_explanatory_report_as_primary_output"],
            "completion_effect": ["allow_activation=true", "downstream_primary_output=today_session"],
        },
        {
            "object": "today_session",
            "purpose": "作为用户日常主视图，回答今天练什么、怎么练、什么时候不该练。",
            "required_fields": ["session_id", "session_type", "target_duration_min_or_distance_km", "intensity_note", "safety_notes", "cancel_conditions"],
            "optional_fields": ["warmup_note", "cooldown_note", "terrain_note"],
            "forbidden_fields": ["full_week_table_only", "multi_day_report_only"],
            "completion_effect": ["daily_execution_ready=true"],
        },
        {
            "object": "body_checkin",
            "purpose": "统一生成前与日常训练前身体状态输入，避免两套不一致字段。",
            "required_fields": ["fatigue_level", "sleep_quality", "pain_status", "pain_trend", "readiness_to_train"],
            "optional_fields": ["sleep_hours", "illness_status", "notes"],
            "forbidden_fields": ["duplicate_precheck_model", "page_specific_field_forks"],
            "constraints": [
                "pain_trend 必须表达同近期状态相比的新发/加重/持平/改善，而不是仅记录部位。",
                "readiness_to_train=no 时，micro_adjustment 不得继续输出 keep。",
            ],
            "completion_effect": ["daily_adjust_input_ready=true"],
        },
        {
            "object": "session_feedback",
            "purpose": "记录训练后执行结果，驱动未来 1-3 天或本周余下计划微调。",
            "required_fields": ["session_id", "completed"],
            "optional_fields": ["actual_duration_min", "actual_distance_km", "perceived_exertion", "pain_after", "deviation_reason", "notes"],
            "forbidden_fields": ["completion_without_session_binding", "free_text_only_feedback"],
            "conditional_required_fields": {"completed=false": "deviation_reason"},
            "constraints": ["当 completed=false 时，必须提供 deviation_reason，不能只留 notes。"],
            "completion_effect": ["micro_adjustment_can_update_future_sessions=true"],
        },
        {
            "object": "micro_adjustment",
            "purpose": "基于 body_checkin 与 session_feedback 对未来近端训练做 keep/downgrade/replace/skip。",
            "required_fields": ["action", "target_scope", "rationale"],
            "optional_fields": ["effective_until", "replacement_session"],
            "forbidden_fields": ["full_plan_regeneration_only", "advice_without_action"],
            "completion_effect": ["near_term_training_updated=true"],
        },
        {
            "object": "plan_generation_guardrail",
            "purpose": "在 risk gate 之后、计划草案输出之前执行运行时规则护栏，避免不安全或不自洽计划进入主输出。",
            "minimum_checks": [
                "weekly_training_days_not_exceeded",
                "long_run_day_within_training_days",
                "weekly_volume_growth_bounded",
                "no_back_to_back_high_intensity",
                "taper_week_reduction_present",
                "injury_risk_session_filter",
                "low_baseline_blocks_aggressive_strategy",
                "race_date_shortfall_forces_degrade",
            ],
            "failure_behavior": ["rewrite_plan_draft", "degrade_goal_or_load", "reject_generation"],
            "output_contract": ["guardrail_passed", "guardrail_adjustments", "guardrail_failure_reason"],
        },
        {
            "object": "plan_lifecycle",
            "purpose": "冻结训练计划生命周期与 active 唯一性约束。",
            "required_fields": ["states", "allowed_transitions", "active_plan_uniqueness_rule"],
            "optional_fields": ["terminal_states"],
            "forbidden_fields": ["page_step_state_machine", "multiple_active_plans"],
            "constraints": ["onboarding 在本 SRC 中指计划实体尚未生成前的 intake runtime state，而非 UI page step。"],
            "completion_effect": ["draft_active_boundary_stable=true"],
        },
    ]


def _project_onboarding_bridge_fields(document: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("source_kind") != "raw_requirement":
        return candidate
    if not _is_onboarding_candidate(candidate, document):
        return candidate

    baseline_lines = _section_lines(document, "现状基线")
    direction_lines = _section_lines(document, "建议方向")
    hard_constraint_lines = _section_lines(document, "补充硬约束")
    non_goal_lines = _section_lines(document, "非目标")

    target_capability_objects = _dedupe_strings(
        candidate.get("target_capability_objects", [])
        + [
            "最小建档页",
            "running_level",
            "recent_injury_status",
            "主状态 + capability flags",
            "设备绑定增强入口",
            "users / user_physical_profile / runner_profiles",
            "首页任务卡渐进补全",
            "AI 首轮建议",
        ]
    )
    expected_outcomes = _dedupe_strings(
        candidate.get("expected_outcomes", [])
        + [
            "用户完成最小建档后可以立即进入首页，不再被设备绑定阻塞。",
            "AI 首轮建议可输出训练建议级别、第一周行动建议、是否提示补充信息和是否提示连接设备。",
            "running_level、recent_injury_status 与 capability flags 的语义边界保持稳定，不再混写训练阶段、当前能力和历史履历。",
        ]
    )
    downstream_derivation_requirements = _dedupe_strings(
        candidate.get("downstream_derivation_requirements", [])
        + [
            "下游 EPIC / FEAT / TASK 必须继承“单页最小建档 + 首页渐进补全”的链路边界。",
            "running_level 必须保持单一训练基础轴，不得混入训练阶段或历史赛事经历。",
            "recent_injury_status 必须作为首日风险门槛的单选字段。",
            "主状态 + capability flags 必须用于表达真实完成情况，不能退回页面流转式状态机。",
        ]
    )
    bridge_summary = _dedupe_strings(
        candidate.get("bridge_summary", [])
        + [
            "首进链路从完整建档收敛为登录/注册后的最小建档页，目标是先拿到第一条可用 AI 建议。",
            "设备绑定、扩展画像和训练计划后置为首页渐进补全，不再阻塞首日体验。",
            "running_level 与 recent_injury_status 被固定为首日最小训练与风险语义，状态模型改为主状态 + capability flags。",
        ]
    )
    governance_change_summary = _dedupe_strings(
        candidate.get("governance_change_summary", [])
        + [
            "首日核心目标从完整建档调整为 1 分钟内获得第一条可用建议。",
            "guide state 的页面流转职责与业务状态职责拆分为主状态 + capability flags。",
            "users / user_physical_profile / runner_profiles 的去重边界与设备绑定后置策略同步冻结。",
        ]
    )
    current_failure_modes = _dedupe_strings(
        candidate.get("current_failure_modes", [])
        + [
            "首进路径过长，用户在感受到 AI 教练价值之前需要完成过多输入和跳转。",
            "users 与 runner_profiles 存在双写和双真相源风险。",
            "设备绑定仍处于主链路中，阻塞首次体验。",
            "guide state 仍同时承担页面流转和业务状态职责。",
        ]
    )
    semantic_layer_declaration = _build_semantic_layer_declaration()
    frozen_contracts = _build_frozen_contracts()
    enum_freezes = _build_enum_freezes()
    structured_object_contracts = _build_structured_object_contracts()
    bridge_context = candidate.get("bridge_context") or {}
    bridge_context.update(
        {
            "governed_by_adrs": deepcopy(candidate["source_refs"]),
            "change_scope": "登录/注册后的 onboarding 只保留最小建档与首轮建议入口，设备绑定和扩展画像后置到首页渐进补全。",
            "governance_objects": target_capability_objects[:6],
            "current_failure_modes": current_failure_modes,
            "downstream_inheritance_requirements": downstream_derivation_requirements,
            "expected_downstream_objects": [
                "onboarding/minimal-profile",
                "homepage task card",
                "running-background profile update",
                "device connect flow",
            ],
            "acceptance_impact": _dedupe_strings(
                [
                    "用户完成最小建档后可立即进入首页，不再被设备绑定阻塞。",
                    "AI 首轮建议可以在最小输入下仍然给出安全可执行的训练建议。",
                    "后续扩展画像和设备连接可以增量完成，不阻塞首日体验。",
                ]
            ),
            "non_goals": deepcopy(non_goal_lines or candidate.get("out_of_scope", [])),
        }
    )
    candidate["target_capability_objects"] = target_capability_objects
    candidate["expected_outcomes"] = expected_outcomes
    candidate["downstream_derivation_requirements"] = downstream_derivation_requirements
    candidate["bridge_summary"] = bridge_summary
    candidate["governance_change_summary"] = governance_change_summary
    candidate["bridge_context"] = bridge_context
    candidate["semantic_layer_declaration"] = semantic_layer_declaration
    candidate["frozen_contracts"] = frozen_contracts
    candidate["structured_object_contracts"] = structured_object_contracts
    candidate["enum_freezes"] = enum_freezes
    candidate["semantic_inventory"] = {
        "actors": _normalize_list(candidate.get("target_users")),
        "core_objects": [
            "minimal_onboarding_page",
            "running_level",
            "recent_injury_status",
            "onboarding_state_model",
            "first_ai_advice_output",
            "profile_storage_boundary",
        ],
        "core_states": ["registered", "profile_minimal_done", "extended_profile_completed", "device_connected", "initial_plan_ready"],
        "core_apis": [
            "POST /v1/onboarding/minimal-profile",
            "POST /v1/profile/running-background",
            "POST /v1/devices/connect",
        ],
        "core_outputs": ["training_advice_level", "first_week_action", "needs_more_info_prompt", "device_connect_prompt"],
        "product_surfaces": ["minimal_onboarding_page", "homepage_task_cards", "device_connect_entry"],
        "operator_surfaces": _normalize_list((candidate.get("semantic_inventory") or {}).get("operator_surfaces")),
        "entry_points": ["login_or_register", "minimal_onboarding_page", "homepage_task_cards"],
        "commands": ["POST /v1/onboarding/minimal-profile", "POST /v1/profile/running-background", "POST /v1/devices/connect"],
        "runtime_objects": ["user_physical_profile", "runner_profiles", "first_ai_advice_output"],
        "states": ["registered", "profile_minimal_done", "extended_profile_completed", "device_connected", "initial_plan_ready"],
        "observability_surfaces": _normalize_list((candidate.get("semantic_inventory") or {}).get("observability_surfaces")),
        "constraints": _normalize_list(candidate.get("key_constraints")),
        "non_goals": _normalize_list(candidate.get("out_of_scope")),
    }
    return candidate


def _project_training_plan_phase1_fields(document: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if not _is_training_plan_candidate(candidate, document):
        return candidate

    direction_lines = _section_lines(document, "建议方向")
    hard_constraint_lines = _section_lines(document, "补充硬约束")
    non_goal_lines = _section_lines(document, "非目标")
    generic_target_noise = {"provenance_normalization", "constraint"}
    generic_expected_noise = {
        "reviewer 可以在不回读外部原文的前提下理解当前 SRC 的最小冻结边界。",
        "下游 workflow 能继承来源追溯、约束和推导方向，而不是继续重写同一层语义。",
    }
    generic_downstream_noise = {
        "下游必须继承本 SRC 已显式记录的来源追溯与关键约束。",
        "若需要在下游重写语义，必须给出派生理由而不是默默改写事实层。",
    }
    generic_bridge_noise_prefixes = (
        "本 SRC 需要把 ",
        "下游应默认继承这里定义的约束、来源追溯和最小冻结结构",
    )
    generic_governance_summary_noise = {
        "generic raw requirement 也必须暴露可继承的边界，而不是只给摘要壳。",
        "bundle recommender 只提供保守的通用 facet 组合，不会把弱 raw 伪装成强领域 bundle。",
    }
    target_capability_objects = _dedupe_strings(
        [item for item in candidate.get("target_capability_objects", []) if item not in generic_target_noise]
        + [
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
        ]
    )
    expected_outcomes = _dedupe_strings(
        [item for item in candidate.get("expected_outcomes", []) if item not in generic_expected_noise]
        + [
            "用户用最少输入即可获得可执行的训练计划草案，并能在激活后直接看到 today_session。",
            "风险评估不再独立成页，而是在生成前以内联 gate 形式稳定执行。",
            "系统可根据 body_checkin 与 session_feedback 对未来 1-3 天或本周余下训练给出微调。",
        ]
    )
    downstream_derivation_requirements = _dedupe_strings(
        [item for item in candidate.get("downstream_derivation_requirements", []) if item not in generic_downstream_noise]
        + [
            "下游 EPIC / FEAT / TASK 必须继承 current_training_state 作为生成与风控的能力基线输入。",
            "若下游需要展开 intake/API 设计，应优先将 min_profile 投影为 runner_profile_min、plan_goal_min、training_availability_min、risk_hint_min 四个 bridge-level 子对象。",
            "today_session 必须继续作为日常主输出，完整周表只能作为附属视图。",
            "session_feedback 与 micro_adjustment 不得在后续层被降级为可选增强项。",
            "plan_lifecycle 必须保持 draft / active 分离且只允许一个 active。",
            "plan_generation_guardrail 必须作为运行时对象显式存在，不能只埋在 prompt 或测试用例里。",
        ]
    )
    bridge_summary = _dedupe_strings(
        [
            item
            for item in candidate.get("bridge_summary", [])
            if not any(str(item).startswith(prefix) for prefix in generic_bridge_noise_prefixes)
        ]
        + [
            "训练计划模块从完整产品式长链路收缩为生成、执行、反馈、微调的最小闭环。",
            "风险评估与计划生成被收敛为同一条生成链：校验输入 -> risk gate -> 生成草案 -> 规则护栏层 -> 输出。",
            "计划主输出从完整解释型周表改为 plan_draft 概览与 today_session。",
        ]
    )
    governance_change_summary = _dedupe_strings(
        [item for item in candidate.get("governance_change_summary", []) if item not in generic_governance_summary_noise]
        + [
            "MVP 生成输入补齐 current_training_state，不再只依赖画像与目标做弱推断。",
            "Daily Adjust 从附属功能提升为闭环核心，必须同时消费 body_checkin 与 session_feedback。",
            "计划生命周期从页面步骤导向切换为 onboarding / draft / active / completed / cancelled。",
            "计划生成 guardrail 从隐式逻辑提升为显式运行时对象，避免下游把它漂移成 prompt 约定。",
        ]
    )
    current_failure_modes = _dedupe_strings(
        [
            "主链路过长，用户在看到今日训练卡前需要完成过多输入、页面与可选集成。",
            "风险评估与计划生成分离，导致前端状态分叉和后端降级逻辑不稳定。",
            "缺少 current_training_state，目标可行性和训练负荷判断不扎实。",
            "Daily Adjust 只消费训练前状态，无法根据执行结果形成真正收敛。",
            "guardrail 没有对象化时，容易在实现层被拆成隐式逻辑、prompt 约定或测试规则，导致运行时分叉。",
        ]
    )
    current_api_anchors = [
        "current_api_anchor: POST /v1/plans/smart-generate",
        "current_api_anchor: POST /v1/plans/{plan_id}/activate",
        "current_api_anchor: POST /v1/plans/check-in",
        "current_api_anchor: POST /v1/plans/session-feedback",
        "current_api_anchor: POST /v1/ai/coach/daily-adjust",
    ]
    governance_objects = [
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
    ]
    bridge_context = candidate.get("bridge_context") or {}
    bridge_context.update(
        {
            "change_scope": "训练计划模块 2.0 MVP 只冻结生成 -> 执行 -> 反馈 -> 微调最小闭环，不继续扩成完整产品链路。",
            "governance_objects": governance_objects,
            "current_failure_modes": current_failure_modes,
            "downstream_inheritance_requirements": downstream_derivation_requirements,
            "expected_downstream_objects": ["runner_profile_min", "plan_goal_min", "training_availability_min", "risk_hint_min", "plan_generation_guardrail"],
            "acceptance_impact": expected_outcomes,
            "non_goals": deepcopy(non_goal_lines or candidate.get("out_of_scope", [])),
            "recommended_min_profile_split": ["runner_profile_min", "plan_goal_min", "training_availability_min", "risk_hint_min"],
            "current_api_anchors": current_api_anchors,
            "selected_facets": deepcopy(candidate.get("selected_facets") or ["object_model", "state_machine", "enumeration", "constraint", "workflow", "view"]),
            "facet_bundle_recommendation": deepcopy(candidate.get("facet_bundle_recommendation") or []),
            "facet_inference": deepcopy(candidate.get("facet_inference") or []),
            "projector_selection": deepcopy(candidate.get("projector_selection") or {}),
        }
    )

    semantic_layer_declaration = _build_training_plan_semantic_layer_declaration()
    candidate["target_capability_objects"] = target_capability_objects
    candidate["expected_outcomes"] = expected_outcomes
    candidate["downstream_derivation_requirements"] = downstream_derivation_requirements
    candidate["bridge_summary"] = bridge_summary
    candidate["governance_change_summary"] = governance_change_summary
    candidate["bridge_context"] = bridge_context
    candidate["semantic_layer_declaration"] = semantic_layer_declaration
    candidate["frozen_contracts"] = _build_training_plan_frozen_contracts()
    candidate["structured_object_contracts"] = _build_training_plan_structured_object_contracts()
    candidate["enum_freezes"] = _build_training_plan_enum_freezes()
    candidate["semantic_inventory"] = {
        "actors": _normalize_list(candidate.get("target_users")),
        "core_objects": [
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
        ],
        "core_states": ["onboarding", "draft", "active", "completed", "cancelled"],
        "core_apis": current_api_anchors,
        "core_outputs": ["plan_overview", "current_week", "today_session", "safety_notes", "micro_adjustment"],
        "product_surfaces": ["minimal_plan_intake", "plan_draft_review", "today_session_card", "daily_checkin", "session_feedback_sheet"],
        "operator_surfaces": _normalize_list((candidate.get("semantic_inventory") or {}).get("operator_surfaces")),
        "entry_points": ["minimal_plan_intake", "plan_draft_review", "today_session_card"],
        "commands": [],
        "runtime_objects": [
            "current_training_state",
            "risk_gate_result",
            "plan_draft",
            "today_session",
            "body_checkin",
            "session_feedback",
            "micro_adjustment",
            "plan_generation_guardrail",
            "plan_lifecycle",
        ],
        "states": ["onboarding", "draft", "active", "completed", "cancelled"],
        "observability_surfaces": _normalize_list((candidate.get("semantic_inventory") or {}).get("observability_surfaces")),
        "constraints": _dedupe_strings(_normalize_list(candidate.get("key_constraints")) + direction_lines + hard_constraint_lines),
        "non_goals": _normalize_list(candidate.get("out_of_scope")),
    }
    return candidate


def enrich_high_fidelity_candidate(candidate: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    working = deepcopy(candidate)
    projector_bundle = _select_projector_bundle(document, working)
    working.update(projector_bundle)
    working = _project_generic_raw_requirement_fields(working)
    projector_selection = working.get("projector_selection") or {}
    if str(projector_selection.get("bundle_kind") or "").strip().lower() == "generic":
        contracts = working.get("structured_object_contracts")
        if not isinstance(contracts, list) or not contracts:
            object_name = "feature_subject"
            title_text = str(working.get("title") or "")
            hint_text = f"{title_text} {working.get('problem_statement') or ''}".lower()
            if any(token in hint_text for token in ["payment", "\u652f\u4ed8", "checkout"]):
                object_name = "payment_attempt"
            elif any(token in hint_text for token in ["retry", "\u91cd\u8bd5"]):
                object_name = "retry_policy"
            working["structured_object_contracts"] = [
                {
                    "object": object_name,
                    "required_fields": ["status", "states", "allowed_transitions"],
                    "notes": "Generic raw-requirement scaffold for FRZ MSC anchoring.",
                }
            ]
    if projector_selection.get("bundle_kind") == "training-plan":
        working = _project_training_plan_phase1_fields(document, working)
    elif projector_selection.get("bundle_kind") == "onboarding":
        working = _project_onboarding_bridge_fields(document, working)
    operator_surface_inventory = derive_operator_surface_inventory(document, working)
    working["operator_surface_inventory"] = operator_surface_inventory
    working["semantic_inventory"] = _merge_semantic_inventory(
        working.get("semantic_inventory") or {},
        derive_semantic_inventory(document, working, operator_surface_inventory),
    )
    working["source_provenance_map"] = derive_source_provenance_map(document, working, operator_surface_inventory)
    working["contradiction_register"] = derive_contradiction_register(document)
    working["normalization_decisions"] = derive_normalization_decisions(document, working, operator_surface_inventory)
    working["omission_and_compression_report"] = derive_omission_and_compression_report(document, working, operator_surface_inventory)
    return working


def structural_check(candidate: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not candidate["problem_statement"]:
        issues.append({"code": "missing_problem_statement", "severity": "error", "message": "Problem statement is required."})
    if not candidate["source_refs"]:
        issues.append({"code": "missing_source_refs", "severity": "error", "message": "Source refs are required."})
    source_snapshot = candidate.get("source_snapshot") or {}
    capture_metadata = source_snapshot.get("capture_metadata") or {}
    if not source_snapshot:
        issues.append({"code": "missing_source_snapshot", "severity": "error", "message": "Source snapshot is required."})
    else:
        for field in ["title", "input_type", "body", "sections", "source_refs", "source_path", "capture_metadata"]:
            if field not in source_snapshot:
                issues.append({"code": "missing_source_snapshot", "severity": "error", "message": f"source_snapshot.{field} is required."})
        for field in ["captured_at", "captured_by", "capture_mode", "source_path", "content_hash", "content_hash_algo"]:
            if field not in capture_metadata:
                issues.append({"code": "missing_source_snapshot_metadata", "severity": "error", "message": f"source_snapshot.capture_metadata.{field} is required."})
    if candidate["source_kind"] == "governance_bridge_src" and not candidate.get("bridge_context"):
        issues.append({"code": "missing_bridge_context", "severity": "error", "message": "ADR-derived candidate requires bridge context."})
    for field, code in [
        ("semantic_inventory", "missing_semantic_inventory"),
        ("source_provenance_map", "missing_source_provenance_map"),
        ("normalization_decisions", "missing_normalization_decisions"),
        ("omission_and_compression_report", "missing_omission_and_compression_report"),
        ("operator_surface_inventory", "missing_operator_surface_inventory"),
        ("contradiction_register", "missing_contradiction_register"),
    ]:
        if field not in candidate:
            issues.append({"code": code, "severity": "error", "message": f"{field} is required."})
    if candidate["source_kind"] == "raw_requirement":
        projector_selection = candidate.get("projector_selection") or {}
        selected_facets = candidate.get("selected_facets") or projector_selection.get("selected_facets") or []
        if not projector_selection:
            issues.append({"code": "missing_projector_selection", "severity": "error", "message": "projector_selection is required for raw requirement candidates."})
        if not selected_facets:
            issues.append({"code": "missing_selected_facets", "severity": "error", "message": "selected_facets is required for raw requirement candidates."})
        if not candidate.get("facet_bundle_recommendation"):
            issues.append({"code": "missing_facet_bundle_recommendation", "severity": "error", "message": "facet_bundle_recommendation is required for raw requirement candidates."})
    if _is_onboarding_candidate(candidate):
        if not candidate.get("semantic_layer_declaration"):
            issues.append({"code": "missing_semantic_layer_declaration", "severity": "error", "message": "semantic_layer_declaration is required for onboarding SRC candidates."})
        else:
            declaration = candidate.get("semantic_layer_declaration") or {}
            for field in ["source_layer", "bridge_layer", "meta_layer", "precedence_order", "override_rule"]:
                if field not in declaration:
                    issues.append({"code": "invalid_semantic_layer_declaration", "severity": "error", "message": f"semantic_layer_declaration.{field} is required."})
        if not candidate.get("frozen_contracts"):
            issues.append({"code": "missing_frozen_contracts", "severity": "error", "message": "frozen_contracts is required for onboarding SRC candidates."})
        else:
            for contract in candidate.get("frozen_contracts", []):
                for field in ["id", "statement", "authoritative_layer", "applies_to"]:
                    if field not in contract:
                        issues.append({"code": "invalid_frozen_contract", "severity": "error", "message": f"frozen_contract.{field} is required."})
        object_contracts = candidate.get("structured_object_contracts") or []
        if not object_contracts:
            issues.append({"code": "missing_structured_object_contracts", "severity": "error", "message": "structured_object_contracts is required for onboarding SRC candidates."})
        else:
            required_objects = {
                "minimal_onboarding_page",
                "running_level",
                "recent_injury_status",
                "onboarding_state_model",
                "first_ai_advice_output",
                "profile_storage_boundary",
            }
            existing_objects = {str(item.get("object", "")).strip() for item in object_contracts}
            missing_objects = sorted(required_objects - existing_objects)
            if missing_objects:
                issues.append({"code": "missing_structured_object_contract", "severity": "error", "message": f"Missing structured object contracts: {', '.join(missing_objects)}"})
        enum_freezes = candidate.get("enum_freezes") or {}
        for field in ["running_level", "recent_injury_status"]:
            if field not in enum_freezes:
                issues.append({"code": "missing_enum_freeze", "severity": "error", "message": f"enum_freezes.{field} is required for onboarding SRC candidates."})
    if _is_training_plan_candidate(candidate):
        if not candidate.get("semantic_layer_declaration"):
            issues.append({"code": "missing_semantic_layer_declaration", "severity": "error", "message": "semantic_layer_declaration is required for training-plan SRC candidates."})
        if not candidate.get("frozen_contracts"):
            issues.append({"code": "missing_frozen_contracts", "severity": "error", "message": "frozen_contracts is required for training-plan SRC candidates."})
        required_objects = {
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
        object_contracts = candidate.get("structured_object_contracts") or []
        if not object_contracts:
            issues.append({"code": "missing_structured_object_contracts", "severity": "error", "message": "structured_object_contracts is required for training-plan SRC candidates."})
        else:
            existing_objects = {str(item.get("object", "")).strip() for item in object_contracts}
            missing_objects = sorted(required_objects - existing_objects)
            if missing_objects:
                issues.append({"code": "missing_structured_object_contract", "severity": "error", "message": f"Missing structured object contracts: {', '.join(missing_objects)}"})
        enum_freezes = candidate.get("enum_freezes") or {}
        for field in [
            "risk_gate_outcome",
            "goal_priority",
            "recent_consistency",
            "micro_adjustment_action",
            "micro_adjustment_target_scope",
            "readiness_to_train",
            "pain_trend",
            "deviation_reason",
            "plan_lifecycle_status",
        ]:
            if field not in enum_freezes:
                issues.append({"code": "missing_enum_freeze", "severity": "error", "message": f"enum_freezes.{field} is required for training-plan SRC candidates."})
        semantic_inventory = candidate.get("semantic_inventory") or {}
        for field in ["core_objects", "product_surfaces", "entry_points", "runtime_objects", "states", "core_outputs"]:
            if not semantic_inventory.get(field):
                issues.append({"code": "semantic_inventory_too_thin", "severity": "error", "message": f"semantic_inventory.{field} is required for training-plan SRC candidates."})
    return issues
