"""Mainline handoff runtime for governed candidate submission."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, load_json, read_text, to_canonical_path, write_json
from cli.lib.registry_store import slugify


def _handoff_key(producer_ref: str, proposal_ref: str) -> str:
    return slugify(f"{producer_ref}-{proposal_ref}")


def _pending_index_path(workspace_root: Path) -> Path:
    return workspace_root / "artifacts" / "active" / "gates" / "pending" / "index.json"


def _load_pending_index(workspace_root: Path) -> dict[str, dict[str, Any]]:
    path = _pending_index_path(workspace_root)
    if path.exists():
        return load_json(path)
    return {"handoffs": {}}


def _save_pending_index(workspace_root: Path, payload: dict[str, Any]) -> None:
    write_json(_pending_index_path(workspace_root), payload)


def submit_handoff(
    workspace_root: Path,
    trace: dict[str, Any],
    producer_ref: str,
    proposal_ref: str,
    payload_ref: str,
    pending_state: str = "gate_pending",
    trace_context_ref: str | None = None,
) -> dict[str, str]:
    payload_path = canonical_to_path(payload_ref, workspace_root)
    ensure(payload_path.exists(), "PRECONDITION_FAILED", "payload_ref must resolve to an existing file")
    payload_digest = hashlib.sha256(read_text(payload_path).encode("utf-8")).hexdigest()
    handoff_id = _handoff_key(producer_ref, proposal_ref)
    handoff_ref = f"artifacts/active/gates/handoffs/{handoff_id}.json"
    pending_ref = f"artifacts/active/gates/pending/{handoff_id}.json"
    index = _load_pending_index(workspace_root)
    existing = index["handoffs"].get(handoff_id)
    if existing:
        if existing.get("payload_digest") != payload_digest:
            raise CommandError("PRECONDITION_FAILED", "duplicate_submission with different payload")
        return {
            "handoff_ref": existing["handoff_ref"],
            "gate_pending_ref": existing["gate_pending_ref"],
            "pending_state": existing.get("pending_state", pending_state),
            "assigned_gate_queue": existing.get("assigned_gate_queue", "mainline.gate.pending"),
            "trace_ref": existing.get("trace_ref", trace_context_ref or ""),
            "canonical_payload_path": to_canonical_path(payload_path, workspace_root),
            "retryable": "true",
            "idempotent_replay": "true",
        }

    write_json(
        workspace_root / handoff_ref,
        {
            "trace": trace,
            "producer_ref": producer_ref,
            "proposal_ref": proposal_ref,
            "payload_ref": to_canonical_path(payload_path, workspace_root),
            "pending_state": pending_state,
            "trace_context_ref": trace_context_ref or "",
            "payload_digest": payload_digest,
        },
    )
    write_json(
        workspace_root / pending_ref,
        {
            "trace": trace,
            "handoff_ref": handoff_ref,
            "producer_ref": producer_ref,
            "proposal_ref": proposal_ref,
            "pending_state": pending_state,
        },
    )
    index["handoffs"][handoff_id] = {
        "handoff_ref": handoff_ref,
        "gate_pending_ref": pending_ref,
        "payload_digest": payload_digest,
        "trace_ref": trace_context_ref or "",
        "pending_state": pending_state,
        "assigned_gate_queue": "mainline.gate.pending",
    }
    _save_pending_index(workspace_root, index)
    return {
        "handoff_ref": handoff_ref,
        "gate_pending_ref": pending_ref,
        "pending_state": pending_state,
        "assigned_gate_queue": "mainline.gate.pending",
        "trace_ref": trace_context_ref or "",
        "canonical_payload_path": to_canonical_path(payload_path, workspace_root),
        "retryable": "true",
        "idempotent_replay": "true",
    }


def list_pending_handoffs(workspace_root: Path) -> dict[str, Any]:
    index = _load_pending_index(workspace_root)
    items: list[dict[str, Any]] = []
    for item in index.get("handoffs", {}).values():
        pending_path = workspace_root / item["gate_pending_ref"]
        if pending_path.exists():
            items.append(load_json(pending_path))
    return {
        "pending_ref": "artifacts/active/gates/pending/index.json",
        "items": items,
        "count": len(items),
    }


def consume_decision_return(
    workspace_root: Path,
    trace: dict[str, Any],
    handoff_ref: str,
    decision_ref: str,
    decision: str,
    routing_hint: str | None = None,
) -> dict[str, str]:
    handoff_path = canonical_to_path(handoff_ref, workspace_root)
    ensure(handoff_path.exists(), "PRECONDITION_FAILED", "handoff_missing")
    handoff = load_json(handoff_path)
    handoff_id = Path(handoff_ref).stem
    if decision in {"revise", "retry"}:
        from cli.lib.reentry import build_reentry_directive

        return build_reentry_directive(
            workspace_root=workspace_root,
            trace=trace,
            handoff_ref=handoff_ref,
            decision_ref=decision_ref,
            decision=decision,
            routing_hint=routing_hint or "producer_reentry",
            producer_ref=str(handoff.get("producer_ref", "")),
        )

    boundary_ref = f"artifacts/active/gates/returns/{handoff_id}-boundary.json"
    boundary_path = workspace_root / boundary_ref
    if boundary_path.exists():
        existing = load_json(boundary_path)
        if existing.get("decision_ref") != decision_ref:
            raise CommandError("PRECONDITION_FAILED", "decision_conflict")
        return {"boundary_handoff_ref": boundary_ref, "reentry_directive_ref": ""}
    write_json(
        boundary_path,
        {
            "trace": trace,
            "handoff_ref": handoff_ref,
            "decision_ref": decision_ref,
            "decision": decision,
            "routing_hint": routing_hint or "formalization",
        },
    )
    return {"boundary_handoff_ref": boundary_ref, "reentry_directive_ref": ""}
