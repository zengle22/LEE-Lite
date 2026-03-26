"""UI flow planning helpers for governed test execution."""

from __future__ import annotations

import copy
from typing import Any


def _page_segment(page_id: str, page_path: str, steps: list[dict[str, Any]], expected_url: str, expected_text: str) -> dict[str, Any]:
    exit_assertions = []
    if expected_url:
        exit_assertions.append({"type": "url_contains", "value": expected_url})
    if expected_text:
        exit_assertions.append({"type": "text_visible", "value": expected_text})
    return {
        "page_id": page_id,
        "path": page_path,
        "enter_condition": {"type": "url_contains", "value": page_path} if page_path else {"type": "none", "value": ""},
        "steps": steps,
        "exit_assertions": exit_assertions,
    }


def _split_into_pages(page_path: str, steps: list[dict[str, Any]], expected_url: str, expected_text: str) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    current_path = page_path
    current_steps: list[dict[str, Any]] = []
    page_index = 1
    for step in steps:
        action = str(step.get("action", "")).lower()
        if action in {"goto", "visit", "open"}:
            if current_steps or current_path:
                pages.append(_page_segment(f"page_{page_index}", current_path, current_steps, "", ""))
                page_index += 1
                current_steps = []
            current_path = str(step.get("path") or step.get("url") or page_path or "")
            continue
        current_steps.append(step)
    pages.append(_page_segment(f"page_{page_index}", current_path, current_steps, expected_url, expected_text))
    return [page for page in pages if page["path"] or page["steps"] or page["exit_assertions"]]


def _transitions(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions = []
    for current, nxt in zip(pages, pages[1:]):
        action = ""
        if current["steps"]:
            action = str(current["steps"][-1].get("semantic_target") or current["steps"][-1].get("target") or current["steps"][-1].get("action") or "")
        transitions.append({"from": current["page_id"], "action": action, "to": nxt["page_id"]})
    return transitions


def _flow_for_case(case: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    steps = copy.deepcopy(binding.get("resolved_ui_steps", case.get("ui_steps", [])))
    page_path = str(binding.get("page_path") or case.get("page_path") or "")
    expected_url = str(binding.get("expected_url") or case.get("expected_url") or "")
    expected_text = str(binding.get("expected_text") or case.get("expected_text") or "")
    status = str(binding.get("binding_status", binding.get("resolution_status", "fallback_smoke")))
    if not steps and not page_path:
        return {
            "case_id": case["case_id"],
            "flow_status": "non_ui",
            "flow_confidence": 0.0,
            "pages": [],
            "transitions": [],
        }
    pages = _split_into_pages(page_path, steps, expected_url, expected_text)
    flow_status = "resolved" if status == "resolved" else "partial" if status == "partial" else "fallback_smoke"
    return {
        "case_id": case["case_id"],
        "flow_status": flow_status,
        "flow_confidence": float(binding.get("binding_confidence", 0.0)),
        "pages": pages,
        "transitions": _transitions(pages),
    }


def derive_ui_flow_plan(case_pack: dict[str, Any], ui_binding_map: dict[str, Any]) -> dict[str, Any]:
    binding_map = {item["case_id"]: item for item in ui_binding_map.get("cases", [])}
    cases = [_flow_for_case(case, binding_map.get(case["case_id"], {})) for case in case_pack.get("cases", [])]
    return {
        "artifact_type": "ui_flow_plan",
        "version": "v1",
        "source_test_set_id": case_pack.get("source_test_set_id", ""),
        "resolved_case_count": sum(1 for item in cases if item["flow_status"] == "resolved"),
        "partial_case_count": sum(1 for item in cases if item["flow_status"] == "partial"),
        "fallback_case_count": sum(1 for item in cases if item["flow_status"] == "fallback_smoke"),
        "non_ui_case_count": sum(1 for item in cases if item["flow_status"] == "non_ui"),
        "cases": cases,
    }


def apply_ui_flow_plan(case_pack: dict[str, Any], ui_flow_plan: dict[str, Any]) -> dict[str, Any]:
    bound_pack = copy.deepcopy(case_pack)
    flow_map = {item["case_id"]: item for item in ui_flow_plan.get("cases", [])}
    for case in bound_pack.get("cases", []):
        flow = flow_map.get(case["case_id"], {})
        case["ui_flow_plan"] = flow
        case["ui_flow_status"] = flow.get("flow_status", "non_ui")
        case["ui_flow_confidence"] = flow.get("flow_confidence", 0.0)
    return bound_pack
