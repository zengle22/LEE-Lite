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
    runtime_objects = _normalize_list(semantic_lock.get("allowed_capabilities"))
    if str(semantic_lock.get("domain_type") or "").strip().lower() == "execution_runner_rule":
        runtime_objects = _normalize_list(runtime_objects + ["ready execution job", "claimed execution job", "next-skill invocation", "execution outcome"])
    monitor_surface_names = [item["name"] for item in operator_surface_inventory if item.get("entry_kind") == "monitor_surface"]
    observability_details = _matching_lines(body, ["ready backlog", "running jobs", "failed jobs", "deadletters", "waiting-human jobs"])
    observability = _normalize_list(monitor_surface_names + observability_details) or (["runner observability surface"] if "execution loop job runner" in body.lower() else [])
    entry_points = [item["name"] for item in operator_surface_inventory if item.get("entry_kind") in {"skill_entry", "cli_control_surface"}]
    return {
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
    rows = [
        {
            "target_field": "problem_statement",
            "source_ref": source_ref,
            "source_section": "问题陈述" if sections.get("问题陈述") else "body",
            "source_excerpt": str(document.get("problem_statement") or _first_paragraph(body)).strip(),
            "preservation_mode": "normalized",
        }
    ]
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


def enrich_high_fidelity_candidate(candidate: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    working = deepcopy(candidate)
    operator_surface_inventory = derive_operator_surface_inventory(document, working)
    working["operator_surface_inventory"] = operator_surface_inventory
    working["semantic_inventory"] = derive_semantic_inventory(document, working, operator_surface_inventory)
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
    return issues
