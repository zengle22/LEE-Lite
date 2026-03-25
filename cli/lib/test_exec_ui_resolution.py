"""UI intent derivation and binding resolution for governed test execution."""

from __future__ import annotations

import copy
from typing import Any


KEYWORD_PAGE_MAP = {
    "login": "/login",
    "dashboard": "/dashboard",
    "home": "/",
}


def _case_text(case: dict[str, Any]) -> str:
    fields = [
        case.get("title", ""),
        case.get("trigger_action", ""),
        " ".join(case.get("pass_conditions", [])),
        " ".join(case.get("observation_points", [])),
        " ".join(case.get("supporting_refs", [])),
    ]
    return " ".join(str(item) for item in fields).lower()


def _semantic_page(case: dict[str, Any]) -> str:
    if case.get("page_path"):
        return str(case["page_path"])
    text = _case_text(case)
    for key, path in KEYWORD_PAGE_MAP.items():
        if key in text:
            return path
    return ""


def _semantic_targets(case: dict[str, Any]) -> list[str]:
    selectors = case.get("selectors", {})
    if isinstance(selectors, dict) and selectors:
        return sorted(str(key) for key in selectors.keys())
    text = _case_text(case)
    targets = []
    if any(token in text for token in ("sign in", "login", "submit")):
        targets.append("primary_action")
    if "email" in text:
        targets.append("email_input")
    if "password" in text:
        targets.append("password_input")
    if any(token in text for token in ("pending", "welcome", "success", "approved")):
        targets.append("status_message")
    return targets


def _infer_action_skeleton(case: dict[str, Any], semantic_page: str, semantic_targets: list[str]) -> list[dict[str, str]]:
    explicit_steps = case.get("ui_steps", [])
    if explicit_steps:
        return [{"action": str(step.get("action", "")), "target": str(step.get("target", step.get("semantic_target", "")))} for step in explicit_steps]
    skeleton = []
    if semantic_page:
        skeleton.append({"action": "goto", "target": "entry_page"})
    if "email_input" in semantic_targets:
        skeleton.append({"action": "fill", "target": "email_input"})
    if "password_input" in semantic_targets:
        skeleton.append({"action": "fill", "target": "password_input"})
    if "primary_action" in semantic_targets:
        skeleton.append({"action": "click", "target": "primary_action"})
    if case.get("expected_text") or "status_message" in semantic_targets:
        skeleton.append({"action": "assert_text", "target": "status_message"})
    if case.get("expected_url"):
        skeleton.append({"action": "assert_url", "target": "navigation"})
    return skeleton


def derive_ui_intent(case_pack: dict[str, Any], ui_source_spec: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for case in case_pack.get("cases", []):
        semantic_page = _semantic_page(case)
        semantic_targets = _semantic_targets(case)
        action_skeleton = _infer_action_skeleton(case, semantic_page, semantic_targets)
        derivation_mode = "explicit_contract" if case.get("ui_steps") else "governance_inferred"
        if not action_skeleton and not semantic_page:
            derivation_mode = "fallback_smoke"
        cases.append(
            {
                "case_id": case["case_id"],
                "derivation_mode": derivation_mode,
                "semantic_page": semantic_page,
                "semantic_targets": semantic_targets,
                "action_skeleton": action_skeleton,
                "assertion_hints": {
                    "expected_url": case.get("expected_url", ""),
                    "expected_text": case.get("expected_text", ""),
                },
                "source_fields": [
                    key
                    for key in ("trigger_action", "pass_conditions", "observation_points", "supporting_refs", "page_path", "expected_url", "expected_text", "ui_steps", "selectors")
                    if case.get(key)
                ],
            }
        )
    return {
        "artifact_type": "ui_intent",
        "source_test_set_id": case_pack.get("source_test_set_id", ""),
        "ui_source_spec": ui_source_spec,
        "cases": cases,
    }


def _selector_binding(selectors: dict[str, Any], target: str) -> dict[str, Any]:
    binding = selectors.get(target)
    if isinstance(binding, str):
        return {"selector": binding}
    if isinstance(binding, dict):
        return dict(binding)
    return {}


def _resolve_step(step: dict[str, Any], selectors: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(step)
    target = str(resolved.get("target", resolved.get("semantic_target", "")))
    if target:
        resolved["semantic_target"] = target
        binding = _selector_binding(selectors, target)
        for key, value in binding.items():
            resolved.setdefault(key, value)
        if binding:
            resolved.setdefault("binding_source", "explicit_selectors")
    return resolved


def _resolved_steps(case: dict[str, Any], intent: dict[str, Any]) -> list[dict[str, Any]]:
    selectors = case.get("selectors", {}) if isinstance(case.get("selectors"), dict) else {}
    explicit_steps = case.get("ui_steps", [])
    if explicit_steps:
        return [_resolve_step(step, selectors) for step in explicit_steps if isinstance(step, dict)]
    return [_resolve_step(step, selectors) for step in intent.get("action_skeleton", [])]


def _step_is_bound(step: dict[str, Any]) -> bool:
    action = str(step.get("action", "")).lower()
    if action in {"goto", "visit", "open", "assert_url"}:
        return True
    locator_keys = ("selector", "testid", "data_testid", "role", "text")
    return any(step.get(key) for key in locator_keys)


def _runtime_pages_for_case(source_context: dict[str, Any], page_path: str) -> list[dict[str, Any]]:
    pages = source_context.get("runtime", {}).get("pages", [])
    if page_path:
        exact = [item for item in pages if item.get("page_path") == page_path]
        if exact:
            return exact
    return pages


def _candidate_pool(source_context: dict[str, Any], page_path: str) -> dict[str, list[dict[str, Any]]]:
    runtime_pages = _runtime_pages_for_case(source_context, page_path)
    pool = {
        "testids": list(source_context.get("codebase", {}).get("testids", [])),
        "ids": list(source_context.get("codebase", {}).get("ids", [])),
        "inputs": list(source_context.get("codebase", {}).get("inputs", [])),
        "buttons": list(source_context.get("codebase", {}).get("buttons", [])),
        "paths": list(source_context.get("codebase", {}).get("paths", [])),
    }
    for page in runtime_pages:
        for key in pool:
            pool[key].extend(page.get(key, []))
    return pool


def _contains(candidate: dict[str, Any], tokens: list[str]) -> bool:
    text = " ".join(str(candidate.get(key, "")) for key in ("value", "selector", "name", "role")).lower()
    return any(token in text for token in tokens)


def _best_fill_binding(target: str, pool: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    target_lower = target.lower()
    preferred = []
    if "email" in target_lower:
        preferred = ["email", "user"]
    elif "password" in target_lower:
        preferred = ["password", "pass"]
    for item in pool["testids"]:
        if _contains(item, preferred or [target_lower]):
            return {"testid": item["value"], "binding_source": "source_scan"}
    for item in pool["inputs"]:
        if _contains(item, preferred or [target_lower]):
            return {"selector": item["selector"], "binding_source": "source_scan"}
    for item in pool["ids"]:
        if _contains(item, preferred or [target_lower]):
            return {"selector": item["selector"], "binding_source": "source_scan"}
    return {}


def _best_click_binding(target: str, pool: dict[str, list[dict[str, Any]]], case: dict[str, Any]) -> dict[str, Any]:
    tokens = [target.lower(), "sign in", "login", "submit", "continue"]
    title_tokens = case.get("title", "").lower().split()
    tokens.extend(title_tokens)
    for item in pool["buttons"]:
        if _contains(item, tokens):
            return {"role": item.get("role", "button"), "name": item.get("name", item.get("value", "")), "binding_source": "source_scan"}
    if len(pool["buttons"]) == 1:
        item = pool["buttons"][0]
        return {"role": item.get("role", "button"), "name": item.get("name", item.get("value", "")), "binding_source": "source_scan"}
    return {}


def _bind_from_sources(step: dict[str, Any], case: dict[str, Any], source_context: dict[str, Any], page_path: str) -> dict[str, Any]:
    if _step_is_bound(step):
        return step
    action = str(step.get("action", "")).lower()
    target = str(step.get("semantic_target", step.get("target", "")))
    pool = _candidate_pool(source_context, page_path)
    if action == "fill":
        binding = _best_fill_binding(target, pool)
        if binding:
            return {**step, **binding}
    if action == "click":
        binding = _best_click_binding(target, pool, case)
        if binding:
            return {**step, **binding}
    if action == "assert_text" and case.get("expected_text"):
        return {**step, "text": case["expected_text"], "binding_source": "case_expected_text"}
    return step


def _source_summary(source_context: dict[str, Any], page_path: str) -> dict[str, Any]:
    runtime_pages = _runtime_pages_for_case(source_context, page_path)
    return {
        "codebase_resolved": bool(source_context.get("codebase", {}).get("resolved")),
        "runtime_pages_considered": [item.get("page_path", "") for item in runtime_pages],
        "codebase_testids": len(source_context.get("codebase", {}).get("testids", [])),
        "runtime_testids": sum(len(item.get("testids", [])) for item in runtime_pages),
        "runtime_buttons": sum(len(item.get("buttons", [])) for item in runtime_pages),
    }


def resolve_ui_binding(
    case_pack: dict[str, Any],
    ui_intent: dict[str, Any],
    ui_source_spec: dict[str, Any],
    source_context: dict[str, Any],
) -> dict[str, Any]:
    intent_map = {item["case_id"]: item for item in ui_intent.get("cases", [])}
    cases = []
    for case in case_pack.get("cases", []):
        intent = intent_map.get(case["case_id"], {})
        page_path = case.get("page_path", "") or intent.get("semantic_page", "")
        steps = [_bind_from_sources(step, case, source_context, page_path) for step in _resolved_steps(case, intent)]
        unresolved_targets = []
        for step in steps:
            if not _step_is_bound(step):
                unresolved_targets.append(str(step.get("semantic_target", step.get("target", "unknown"))))
        resolution_status = "resolved"
        if not steps and not page_path:
            resolution_status = "fallback_smoke"
        elif unresolved_targets:
            resolution_status = "partial"
        cases.append(
            {
                "case_id": case["case_id"],
                "resolution_status": resolution_status,
                "page_path": page_path,
                "expected_url": case.get("expected_url", ""),
                "expected_text": case.get("expected_text", ""),
                "resolved_ui_steps": steps,
                "unresolved_targets": unresolved_targets,
                "binding_sources": {
                    "explicit_ui_steps": bool(case.get("ui_steps")),
                    "selectors": sorted(case.get("selectors", {}).keys()) if isinstance(case.get("selectors"), dict) else [],
                    "intent_mode": intent.get("derivation_mode", ""),
                    "source_summary": _source_summary(source_context, page_path),
                },
            }
        )
    return {
        "artifact_type": "ui_binding_map",
        "source_test_set_id": case_pack.get("source_test_set_id", ""),
        "ui_source_spec": ui_source_spec,
        "cases": cases,
    }


def apply_ui_binding(case_pack: dict[str, Any], ui_binding_map: dict[str, Any]) -> dict[str, Any]:
    bound_pack = copy.deepcopy(case_pack)
    binding_map = {item["case_id"]: item for item in ui_binding_map.get("cases", [])}
    for case in bound_pack.get("cases", []):
        binding = binding_map.get(case["case_id"], {})
        case["ui_steps"] = binding.get("resolved_ui_steps", case.get("ui_steps", []))
        case["page_path"] = binding.get("page_path", case.get("page_path", ""))
        case["expected_url"] = binding.get("expected_url", case.get("expected_url", ""))
        case["expected_text"] = binding.get("expected_text", case.get("expected_text", ""))
        case["ui_resolution_status"] = binding.get("resolution_status", "fallback_smoke")
        case["unresolved_targets"] = binding.get("unresolved_targets", [])
    return bound_pack
