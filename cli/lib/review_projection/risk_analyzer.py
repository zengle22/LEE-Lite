"""Risk and ambiguity extraction for review projections."""

from __future__ import annotations

from typing import Any


def analyze_risk_signals(context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    risk_items: list[dict[str, Any]] = []
    ambiguity_items: list[dict[str, Any]] = []
    if not context.get("main_flow"):
        risk_items.append(_signal(context, "omission", "Main flow is missing; verify the review scope is executable.", ["main_flow"]))
    if not context.get("boundary"):
        risk_items.append(
            _signal(
                context,
                "boundary_gap",
                "Frozen downstream boundary is missing; confirm what remains out of scope for this gate.",
                ["frozen_downstream_boundary"],
            )
        )
    if len(context.get("deliverables", [])) != 1:
        ambiguity_items.append(
            _signal(
                context,
                "deliverable_ambiguity",
                "Authoritative deliverable is not unique; confirm which output downstream should treat as canonical.",
                ["authoritative_output"],
            )
        )
    if not context.get("roles"):
        ambiguity_items.append(
            _signal(context, "responsibility_gap", "Roles are unclear; verify responsibility placement before approving.", ["roles"])
        )
    if context.get("open_technical_decisions"):
        ambiguity_items.append(
            _signal(
                context,
                "open_decision",
                "Open technical decisions remain; check whether they block this review round or only downstream implementation.",
                ["open_technical_decisions"],
            )
        )
    return _filter_traceable(risk_items), _filter_traceable(ambiguity_items)


def _signal(context: dict[str, Any], signal_type: str, prompt: str, field_names: list[str]) -> dict[str, Any]:
    trace_refs = [context["field_trace_refs"].get(name, "") for name in field_names if context["field_trace_refs"].get(name)]
    return {
        "signal_type": signal_type,
        "review_prompt": prompt,
        "source_trace_refs": trace_refs,
    }


def _filter_traceable(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if item["source_trace_refs"]]
