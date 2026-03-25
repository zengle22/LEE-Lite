"""Mainline handoff submission and pending visibility runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json
from cli.lib.gate_protocol import normalize_pending_state
from cli.lib.registry_store import slugify


def _queue_index_path(workspace_root: Path) -> Path:
    return workspace_root / "artifacts" / "active" / "gates" / "pending" / "_queue-index.json"


def _next_queue_slot(workspace_root: Path) -> str:
    index_path = _queue_index_path(workspace_root)
    next_index = 1
    if index_path.exists():
        next_index = int(load_json(index_path).get("next_index", 1))
    write_json(index_path, {"next_index": next_index + 1})
    return f"gate-queue-{next_index:03d}"


def _handoff_slug(trace: dict[str, Any], request_id: str) -> str:
    run_ref = str(trace.get("run_ref") or "run")
    return slugify(f"{run_ref}-{request_id}")


def submit_handoff(workspace_root: Path, payload: dict[str, Any], trace: dict[str, Any], request_id: str) -> dict[str, str]:
    for field in ("producer_ref", "proposal_ref", "payload_ref"):
        ensure(bool(payload.get(field)), "INVALID_REQUEST", f"{field} is required")
    state = normalize_pending_state(payload.get("pending_state"))
    slug = _handoff_slug(trace, request_id)
    queue_slot = _next_queue_slot(workspace_root)
    handoff_ref = f"artifacts/active/handoffs/{slug}.json"
    pending_ref = f"artifacts/active/gates/pending/{slug}.json"
    trace_ref = f"artifacts/active/traces/{slug}.json"
    handoff = {
        "trace": trace,
        "producer_ref": payload["producer_ref"],
        "proposal_ref": payload["proposal_ref"],
        "payload_ref": payload["payload_ref"],
        "trace_context_ref": payload.get("trace_context_ref", ""),
        "state": state,
        "queue_slot": queue_slot,
        "gate_pending_ref": pending_ref,
        "trace_ref": trace_ref,
    }
    pending = {
        "handoff_ref": handoff_ref,
        "pending_state": state,
        "assigned_gate_queue": queue_slot,
        "trace_ref": trace_ref,
    }
    write_json(canonical_to_path(handoff_ref, workspace_root), handoff)
    write_json(canonical_to_path(pending_ref, workspace_root), pending)
    write_json(canonical_to_path(trace_ref, workspace_root), {"trace": trace, "handoff_ref": handoff_ref})
    return {
        "handoff_ref": handoff_ref,
        "queue_slot": queue_slot,
        "gate_pending_ref": pending_ref,
        "trace_ref": trace_ref,
    }


def show_pending(workspace_root: Path, handoff_ref: str) -> dict[str, Any]:
    handoff = load_json(canonical_to_path(handoff_ref, workspace_root))
    pending_ref = str(handoff.get("gate_pending_ref", ""))
    ensure(bool(pending_ref), "PRECONDITION_FAILED", "handoff is missing gate_pending_ref")
    pending = load_json(canonical_to_path(pending_ref, workspace_root))
    pending["handoff_ref"] = handoff_ref
    pending["canonical_path"] = pending_ref
    pending["trace_ref"] = str(handoff.get("trace_ref", pending.get("trace_ref", "")))
    return pending


def register_reentry_state(workspace_root: Path, handoff_ref: str, reentry_ref: str) -> None:
    handoff_path = canonical_to_path(handoff_ref, workspace_root)
    handoff = load_json(handoff_path)
    handoff["state"] = "reentry_pending"
    handoff["reentry_ref"] = reentry_ref
    pending_ref = str(handoff.get("gate_pending_ref", ""))
    if pending_ref:
        pending_path = canonical_to_path(pending_ref, workspace_root)
        pending = load_json(pending_path)
        pending["pending_state"] = "reentry_pending"
        pending["reentry_ref"] = reentry_ref
        write_json(pending_path, pending)
    write_json(handoff_path, handoff)


def mark_handoff_closed(workspace_root: Path, handoff_ref: str, closure_ref: str) -> None:
    handoff_path = canonical_to_path(handoff_ref, workspace_root)
    handoff = load_json(handoff_path)
    handoff["state"] = "closed"
    handoff["closure_ref"] = closure_ref
    write_json(handoff_path, handoff)
