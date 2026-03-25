"""Shared object builders for governed gate and handoff runtime."""

from __future__ import annotations

from typing import Any

from cli.lib.errors import CommandError


ALLOWED_DECISIONS = ("approve", "revise", "retry", "handoff", "reject")
PENDING_STATES = ("handoff_prepared", "gate_pending", "reentry_pending", "closed")


def ensure_allowed_decision(value: str) -> str:
    decision = value.strip().lower()
    if decision not in ALLOWED_DECISIONS:
        raise CommandError("INVALID_REQUEST", "decision must be one of approve/revise/retry/handoff/reject")
    return decision


def normalize_pending_state(value: str | None) -> str:
    state = (value or "gate_pending").strip().lower()
    if state not in PENDING_STATES:
        raise CommandError("INVALID_REQUEST", f"unsupported pending state: {state}")
    return state


def decision_flags(decision: str) -> dict[str, bool]:
    normalized = ensure_allowed_decision(decision)
    return {
        "reentry_allowed": normalized in {"revise", "retry"},
        "materialization_required": normalized == "approve",
        "delegated_handoff_required": normalized == "handoff",
        "closure_required": normalized in {"reject", "handoff"},
    }


def build_gate_ready_package(payload: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "trace": trace,
        "candidate_ref": payload["candidate_ref"],
        "acceptance_ref": payload["acceptance_ref"],
        "evidence_bundle_ref": payload["evidence_bundle_ref"],
        "proposal_ref": payload.get("proposal_ref", ""),
        "producer_ref": payload.get("producer_ref", ""),
        "created_from": payload.get("created_from", "gate.create"),
    }


def build_gate_decision(
    trace: dict[str, Any],
    decision: str,
    handoff_ref: str,
    proposal_ref: str,
    rationale: str,
    review_context_ref: str = "",
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    normalized = ensure_allowed_decision(decision)
    flags = decision_flags(normalized)
    return {
        "trace": trace,
        "decision_type": normalized,
        "handoff_ref": handoff_ref,
        "proposal_ref": proposal_ref,
        "review_context_ref": review_context_ref,
        "rationale": rationale,
        "findings": findings or [],
        **flags,
    }
