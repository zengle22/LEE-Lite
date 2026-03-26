"""Feature-owned gate actions for the mainline collaboration loop."""

from __future__ import annotations

from pathlib import Path

from cli.lib.errors import ensure
from cli.lib.fs import write_json
from cli.lib.mainline_runtime import consume_decision_return, list_pending_handoffs, submit_handoff
from cli.lib.protocol import CommandContext


def _submit_handoff_action(ctx: CommandContext):
    payload = ctx.payload
    for field in ("producer_ref", "proposal_ref", "payload_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing handoff field: {field}")
    result = submit_handoff(
        ctx.workspace_root,
        trace=ctx.trace,
        producer_ref=str(payload["producer_ref"]),
        proposal_ref=str(payload["proposal_ref"]),
        payload_ref=str(payload["payload_ref"]),
        pending_state=str(payload.get("pending_state", "gate_pending")),
        trace_context_ref=str(payload["trace_context_ref"]) if payload.get("trace_context_ref") else None,
    )
    return "OK", "authoritative handoff submitted", {"canonical_path": result["handoff_ref"], **result}, [], [
        result["handoff_ref"],
        result["gate_pending_ref"],
    ]


def _show_pending_action(ctx: CommandContext):
    result = list_pending_handoffs(ctx.workspace_root)
    return "OK", "pending handoffs listed", {
        "canonical_path": result["pending_ref"],
        "pending_ref": result["pending_ref"],
        "pending_items": result["items"],
        "pending_count": result["count"],
    }, [], [result["pending_ref"]]


def _decide_action(ctx: CommandContext):
    payload = ctx.payload
    for field in ("handoff_ref", "proposal_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing decide field: {field}")
    decision_ref = f"artifacts/active/gates/decisions/{Path(str(payload['handoff_ref'])).stem}-decision.json"
    decision_type = str(payload.get("decision") or "approve")
    decision = {
        "trace": ctx.trace,
        "proposal_ref": payload["proposal_ref"],
        "handoff_ref": payload["handoff_ref"],
        "decision_type": decision_type,
        "routing_hint": str(payload.get("routing_hint", "formalization" if decision_type in {"approve", "handoff"} else "producer_reentry")),
        "materialization_required": bool(payload.get("materialization_required", decision_type in {"approve", "handoff"})),
        "reentry_allowed": decision_type in {"revise", "retry"},
        "decision_reason": str(payload.get("decision_reason", "derived from audit findings and target constraints")),
    }
    write_json(ctx.workspace_root / decision_ref, decision)
    routing = consume_decision_return(
        ctx.workspace_root,
        trace=ctx.trace,
        handoff_ref=str(payload["handoff_ref"]),
        decision_ref=decision_ref,
        decision=decision_type,
        routing_hint=decision["routing_hint"],
    )
    evidence_refs = [decision_ref] + [value for value in routing.values() if value]
    return "OK", "gate decision produced", {"canonical_path": decision_ref, "gate_decision_ref": decision_ref, **routing}, [], evidence_refs


def collaboration_handlers() -> dict[str, object]:
    return {
        "submit-handoff": _submit_handoff_action,
        "show-pending": _show_pending_action,
        "decide": _decide_action,
    }
