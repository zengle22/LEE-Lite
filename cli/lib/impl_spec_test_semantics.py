"""Semantic extraction helpers for ADR-036 implementation spec testing."""

from __future__ import annotations

import re
from typing import Any

from cli.lib.impl_spec_test_support import as_list


SECTION_ALIASES = {
    "scope": ("in scope", "scope", "coverage scope"),
    "non_goals": ("out of scope", "non goals", "non-goals", "coverage exclusions"),
    "state_model": ("state model snapshot", "state model"),
    "main_sequence": ("main sequence snapshot", "main sequence"),
    "integration_points": ("integration points snapshot", "integration points"),
    "implementation_units": ("implementation unit mapping snapshot", "implementation unit mapping", "ordered tasks"),
    "api_contract": ("api contract snapshot", "api contract"),
    "ui_constraints": ("ui constraint snapshot", "ui constraints", "ux flow notes"),
    "acceptance": ("acceptance mappings", "acceptance traceability", "pass criteria"),
}
ACTOR_KEYWORDS = ("user", "coach", "runner", "system", "backend", "service", "frontend", "homepage", "guard", "device")
GOAL_KEYWORDS = ("goal", "allow", "complete", "enter", "visible", "ready", "continue", "submit", "finish", "完成", "进入", "继续")
INVARIANT_KEYWORDS = ("always", "must", "canonical", "sole", "invariant", "唯一事实源", "必须", "始终")

FAILURE_KEYWORDS = (
    "fail",
    "failed",
    "failure",
    "error",
    "invalid",
    "blocked",
    "blocking",
    "conflict",
    "风险",
    "失败",
    "错误",
    "阻塞",
    "冲突",
)
RECOVERY_KEYWORDS = (
    "retry",
    "recover",
    "recovery",
    "fallback",
    "skip",
    "deferred",
    "stay",
    "return",
    "fail closed",
    "重试",
    "恢复",
    "回退",
    "跳过",
    "后置",
    "停留",
    "返回",
    "阻断",
)
NON_BLOCKING_KEYWORDS = ("non-blocking", "nonblocking", "deferred", "skip", "后置", "不阻塞", "跳过")
BLOCKING_KEYWORDS = ("must connect before", "block", "blocking", "before continue", "must complete first", "阻塞", "前置")
MIGRATION_KEYWORDS = ("legacy", "compat", "compatibility", "migration", "旧系统", "兼容", "迁移")


def text(value: Any) -> str:
    return str(value or "").strip()


def normalize_heading(value: str) -> str:
    heading = re.sub(r"[`*_#:\\-]+", " ", text(value).lower())
    return re.sub(r"\s+", " ", heading).strip()


def canonical_section_key(heading: str) -> str:
    normalized = normalize_heading(heading)
    for key, aliases in SECTION_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return key
    return normalized or "body"


def collect_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            if current:
                items.append(" ".join(current).strip())
                current = []
            continue
        if stripped.startswith("|"):
            continue
        if stripped.startswith(("- ", "* ")) or re.match(r"^\d+\.\s+", stripped):
            if current:
                items.append(" ".join(current).strip())
                current = []
            items.append(re.sub(r"^(?:[-*]|\d+\.)\s+", "", stripped))
            continue
        current.append(stripped)
    if current:
        items.append(" ".join(current).strip())
    return items


def parse_markdown_sections(body: str) -> dict[str, dict[str, Any]]:
    sections: dict[str, dict[str, Any]] = {"body": {"heading": "body", "items": [], "lines": []}}
    current = "body"
    for line in body.splitlines():
        match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if match:
            current = canonical_section_key(match.group(2))
            sections.setdefault(current, {"heading": match.group(2).strip(), "items": [], "lines": []})
            continue
        sections[current]["lines"].append(line)
    for payload in sections.values():
        payload["items"] = collect_items(payload["lines"])
        payload["text"] = "\n".join(payload["lines"]).strip()
    return sections


def extract_tokens(text_value: str) -> list[str]:
    tokens = re.findall(r"`([^`]+)`", text_value)
    tokens.extend(re.findall(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b", text_value))
    tokens.extend(re.findall(r"\b[a-z]+(?:_[a-z0-9]+)+\b", text_value))
    seen: list[str] = []
    for token in tokens:
        normalized = text(token)
        if normalized and normalized not in seen:
            seen.append(normalized)
    return seen


def extract_state_transitions(lines: list[str]) -> list[dict[str, str]]:
    transitions: list[dict[str, str]] = []
    for line in lines:
        for source, target in re.findall(r"`([^`]+)`\s*->\s*`([^`]+)`", line):
            transitions.append({"from": text(source), "to": text(target)})
    return transitions


def extract_completion_signals(items: list[str], tokens: list[str]) -> list[str]:
    signals = [token for token in tokens if any(marker in token.lower() for marker in ("done", "complete", "completed", "allowed", "visible", "entered", "ready"))]
    for item in items:
        lowered = item.lower()
        if "完成态" in item or "allow immediate" in lowered or "allow homepage" in lowered:
            signals.append(item)
    return list(dict.fromkeys(signals))


def extract_owner_candidates(lines: list[str]) -> list[str]:
    owners: list[str] = []
    for line in lines:
        lowered = line.lower()
        if (
            "sole authority" not in lowered
            and "sole source" not in lowered
            and "唯一事实源" not in line
            and "canonical source" not in lowered
            and "canonical" not in lowered
        ):
            continue
        owners.extend(extract_tokens(line))
    return list(dict.fromkeys(owners))


def classify_blocking_claims(items: list[str]) -> list[str]:
    claims: list[str] = []
    for item in items:
        lowered = item.lower()
        if any(marker in lowered for marker in NON_BLOCKING_KEYWORDS):
            continue
        if any(marker in lowered for marker in BLOCKING_KEYWORDS):
            claims.append(item)
    return claims


def extract_api_terms(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    outputs: list[str] = []
    errors: list[str] = []
    preconditions: list[str] = []
    for line in lines:
        for field, bucket in (("output", outputs), ("errors", errors), ("precondition", preconditions)):
            match = re.search(rf"{field}\s*=\s*([^;]+)", line, re.IGNORECASE)
            if match:
                bucket.extend(extract_tokens(match.group(1)))
    return list(dict.fromkeys(outputs)), list(dict.fromkeys(errors)), list(dict.fromkeys(preconditions))


def extract_named_sentences(items: list[str], keywords: tuple[str, ...]) -> list[str]:
    return [item for item in items if any(keyword in item.lower() for keyword in keywords)]


def extract_testset_semantics(doc: dict[str, Any]) -> dict[str, Any]:
    units = [dict(item) for item in doc.get("test_units", []) if isinstance(item, dict)]
    acceptance = [dict(item) for item in doc.get("acceptance_traceability", []) if isinstance(item, dict)]
    observed_terms: list[str] = []
    failure_terms: list[str] = []
    for unit in units:
        observed_terms.extend(extract_tokens(" ".join(as_list(unit.get("observation_points")) + as_list(unit.get("pass_conditions")))))
        failure_terms.extend(extract_tokens(" ".join(as_list(unit.get("fail_conditions")))))
    text_value = "\n".join(as_list(doc.get("coverage_scope")) + as_list(doc.get("pass_criteria")) + as_list(doc.get("risk_focus")))
    return {
        "sections": {},
        "scope": as_list(doc.get("coverage_scope")),
        "non_goals": as_list(doc.get("coverage_exclusions")),
        "state_model": [],
        "main_sequence": [],
        "integration_points": as_list(doc.get("environment_assumptions")),
        "implementation_units": [],
        "api_contract": [],
        "ui_constraints": [],
        "acceptance": [row.get("then", "") for row in acceptance],
        "tokens": list(dict.fromkeys(extract_tokens(text_value) + observed_terms + failure_terms)),
        "title": text(doc.get("title")),
        "body_text": text_value,
        "state_transitions": [],
        "completion_signals": observed_terms,
        "failure_signals": failure_terms,
        "recovery_signals": [term for term in failure_terms if any(marker in term.lower() for marker in ("retry", "blocked", "deferred"))],
        "non_blocking_claims": [item for item in as_list(doc.get("coverage_scope")) if any(marker in item.lower() for marker in NON_BLOCKING_KEYWORDS)],
        "blocking_claims": classify_blocking_claims(as_list(doc.get("coverage_scope"))),
        "owner_candidates": [],
        "api_outputs": [],
        "api_errors": [],
        "api_preconditions": [],
        "acceptance_refs": [row.get("acceptance_ref", "") for row in acceptance if text(row.get("acceptance_ref"))],
        "observed_terms": list(dict.fromkeys(observed_terms)),
        "testable_failure_terms": list(dict.fromkeys(failure_terms)),
        "actors": extract_named_sentences(as_list(doc.get("coverage_scope")) + as_list(doc.get("environment_assumptions")), ACTOR_KEYWORDS),
        "user_goals": extract_named_sentences(as_list(doc.get("coverage_scope")) + [row.get("then", "") for row in acceptance], GOAL_KEYWORDS),
        "state_invariants": [],
        "api_postconditions": [],
        "ux_entry_points": [],
        "ux_exit_points": [],
        "out_of_scope_promises": as_list(doc.get("coverage_exclusions")),
    }


def extract_doc_semantics(doc: dict[str, Any]) -> dict[str, Any]:
    if text(doc.get("ssot_type")) == "TESTSET":
        return extract_testset_semantics(doc)
    body = text(doc.get("_body"))
    sections = parse_markdown_sections(body)
    combined_text = "\n".join(section.get("text", "") for section in sections.values())
    state_model = sections.get("state_model", {}).get("items", [])
    main_sequence = sections.get("main_sequence", {}).get("items", [])
    integration_points = sections.get("integration_points", {}).get("items", [])
    api_contract = sections.get("api_contract", {}).get("items", [])
    ui_constraints = sections.get("ui_constraints", {}).get("items", [])
    acceptance = sections.get("acceptance", {}).get("items", [])
    tokens = extract_tokens(combined_text)
    outputs, errors, preconditions = extract_api_terms(api_contract + sections.get("api_contract", {}).get("lines", []))
    review_lines = state_model + main_sequence + api_contract + integration_points + acceptance
    return {
        "sections": sections,
        "scope": sections.get("scope", {}).get("items", []),
        "non_goals": sections.get("non_goals", {}).get("items", []),
        "state_model": state_model,
        "main_sequence": main_sequence,
        "integration_points": integration_points,
        "implementation_units": sections.get("implementation_units", {}).get("items", []),
        "api_contract": api_contract,
        "ui_constraints": ui_constraints,
        "acceptance": acceptance,
        "tokens": tokens,
        "title": text(doc.get("title") or doc.get("id")),
        "body_text": combined_text,
        "state_transitions": extract_state_transitions(state_model),
        "completion_signals": extract_completion_signals(state_model + main_sequence + api_contract + acceptance, tokens + outputs),
        "failure_signals": [item for item in review_lines if any(keyword in item.lower() for keyword in FAILURE_KEYWORDS)],
        "recovery_signals": [item for item in review_lines + ui_constraints if any(keyword in item.lower() for keyword in RECOVERY_KEYWORDS)],
        "non_blocking_claims": [item for item in review_lines + ui_constraints if any(keyword in item.lower() for keyword in NON_BLOCKING_KEYWORDS)],
        "blocking_claims": classify_blocking_claims(review_lines + ui_constraints),
        "owner_candidates": extract_owner_candidates(state_model + api_contract + integration_points),
        "api_outputs": outputs,
        "api_errors": errors,
        "api_preconditions": preconditions,
        "acceptance_refs": [],
        "observed_terms": [],
        "testable_failure_terms": [],
        "actors": extract_named_sentences(main_sequence + integration_points + ui_constraints, ACTOR_KEYWORDS),
        "user_goals": extract_named_sentences(scope + main_sequence + acceptance, GOAL_KEYWORDS) if (scope := sections.get("scope", {}).get("items", [])) is not None else [],
        "state_invariants": extract_named_sentences(state_model + integration_points + api_contract, INVARIANT_KEYWORDS),
        "api_postconditions": outputs,
        "ux_entry_points": extract_named_sentences(main_sequence + ui_constraints, ("enter", "start", "open", "show", "进入", "展示")),
        "ux_exit_points": extract_named_sentences(main_sequence + ui_constraints + acceptance, ("continue", "return", "homepage", "done", "完成", "继续", "返回")),
        "out_of_scope_promises": sections.get("non_goals", {}).get("items", []),
    }


def build_semantic_review(normalized: dict[str, Any]) -> dict[str, Any]:
    return {
        "impl": extract_doc_semantics(normalized["impl"]),
        "feat": extract_doc_semantics(normalized["feat"]),
        "tech": extract_doc_semantics(normalized["tech"]),
        "arch": extract_doc_semantics(normalized["arch"]) if normalized.get("arch") else None,
        "api": extract_doc_semantics(normalized["api"]) if normalized.get("api") else None,
        "ui_docs": [extract_doc_semantics(doc) for doc in normalized.get("ui_docs", [])],
        "testset_docs": [extract_doc_semantics(doc) for doc in normalized.get("testset_docs", [])],
    }


def build_system_views(semantic_review: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    tech = semantic_review["tech"]
    api = semantic_review.get("api") or {"api_outputs": [], "api_errors": []}
    completion_signals = list(dict.fromkeys(impl.get("completion_signals", []) + tech.get("completion_signals", []) + api.get("api_outputs", [])))
    failure_terms = list(dict.fromkeys(impl.get("failure_signals", []) + tech.get("failure_signals", []) + api.get("api_errors", [])))
    acceptance_refs: list[str] = []
    ui_constraints: list[str] = []
    for doc in semantic_review.get("testset_docs", []):
        acceptance_refs.extend(doc.get("acceptance_refs", []))
    for doc in semantic_review.get("ui_docs", []):
        ui_constraints.extend(doc.get("ui_constraints", []))
    return {
        "functional_chain": {
            "goal": semantic_review["feat"].get("title"),
            "actors": list(dict.fromkeys(impl.get("actors", []) + semantic_review["feat"].get("actors", []))),
            "user_goals": list(dict.fromkeys(impl.get("user_goals", []) + semantic_review["feat"].get("user_goals", []))),
            "ordered_steps": impl.get("main_sequence") or tech.get("main_sequence"),
            "completion_signals": completion_signals,
            "non_goals": impl.get("non_goals") or semantic_review["feat"].get("non_goals"),
        },
        "user_journey": {
            "primary_journey": impl.get("main_sequence"),
            "entry_points": impl.get("ux_entry_points", []),
            "exit_points": impl.get("ux_exit_points", []),
            "failure_surfaces": failure_terms,
            "recovery_surfaces": impl.get("recovery_signals") + ui_constraints,
        },
        "state_data_relationships": {
            "states": impl.get("state_model") + tech.get("state_model"),
            "transitions": impl.get("state_transitions") + tech.get("state_transitions"),
            "ownership": list(dict.fromkeys(impl.get("owner_candidates", []) + tech.get("owner_candidates", []))),
            "invariants": list(dict.fromkeys(impl.get("state_invariants", []) + tech.get("state_invariants", []))),
        },
        "ui_api_state_mapping": {
            "ui_constraints": ui_constraints,
            "api_outputs": api.get("api_outputs", []),
            "api_errors": api.get("api_errors", []),
            "api_postconditions": api.get("api_postconditions", []),
            "state_signals": completion_signals,
            "test_acceptance_refs": list(dict.fromkeys(acceptance_refs)),
        },
    }
