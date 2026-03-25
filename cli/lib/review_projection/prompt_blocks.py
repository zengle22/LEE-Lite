"""Prompt block composition for review projections."""

from __future__ import annotations


def compose_prompt_blocks(focus_result: dict[str, object]) -> list[dict[str, object]]:
    return [
        _focus_block(focus_result),
        _risk_block(focus_result),
    ]


def _focus_block(focus_result: dict[str, object]) -> dict[str, object]:
    items = list(focus_result.get("focus_items", []))
    content = [item["review_prompt"] for item in items] or ["Review focus unavailable; inspect Machine SSOT directly."]
    trace_refs = _collect_trace_refs(items)
    return {
        "id": "review_focus",
        "title": "Review Focus",
        "content": content,
        "status": "complete" if items else focus_result.get("status", "insufficient_context"),
        "source_trace_refs": trace_refs,
    }


def _risk_block(focus_result: dict[str, object]) -> dict[str, object]:
    risk_items = list(focus_result.get("risk_items", []))
    ambiguity_items = list(focus_result.get("ambiguity_items", []))
    content = [item["review_prompt"] for item in risk_items + ambiguity_items]
    if not content:
        content = ["No additional risks or ambiguities were derived from the current SSOT."]
    return {
        "id": "risks_ambiguities",
        "title": "Risks / Ambiguities",
        "content": content,
        "status": "complete" if risk_items or ambiguity_items else "empty",
        "source_trace_refs": _collect_trace_refs(risk_items + ambiguity_items),
    }


def _collect_trace_refs(items: list[dict[str, object]]) -> list[str]:
    trace_refs: list[str] = []
    for item in items:
        for trace_ref in item.get("source_trace_refs", []):
            if trace_ref not in trace_refs:
                trace_refs.append(trace_ref)
    return trace_refs
