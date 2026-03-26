#!/usr/bin/env python3
"""Queue helpers for ll-gate-human-orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gate_human_orchestrator_common import load_gate_ready_package, load_json, repo_relative
from gate_human_orchestrator_round_support import request_path, round_state_path
from gate_human_orchestrator_runtime import output_dir_for


def pending_index_path(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "active" / "gates" / "pending" / "index.json"


def claimable_queue_item(repo_root: Path) -> dict[str, Any] | None:
    index_path = pending_index_path(repo_root)
    queue_items: list[tuple[str, dict[str, Any], Path]] = []
    pending_dir = repo_root / "artifacts" / "active" / "gates" / "pending"
    if index_path.exists():
        index = load_json(index_path)
        handoffs = index.get("handoffs", {})
        if isinstance(handoffs, dict):
            for item_key in sorted(handoffs):
                entry = handoffs[item_key]
                if isinstance(entry, dict) and str(entry.get("gate_pending_ref", "")):
                    queue_items.append((item_key, entry, repo_root / str(entry["gate_pending_ref"])))
    elif pending_dir.exists():
        for pending_path in sorted(pending_dir.glob("*.json")):
            if not pending_path.name.startswith("_"):
                queue_items.append((pending_path.stem, {"gate_pending_ref": repo_relative(repo_root, pending_path)}, pending_path))

    for item_key, entry, pending_path in queue_items:
        handoff_ref = str(entry.get("handoff_ref", ""))
        if not handoff_ref and pending_path.exists():
            handoff_ref = str(load_json(pending_path).get("handoff_ref", ""))
        if not handoff_ref:
            continue
        handoff_path = repo_root / handoff_ref
        if not pending_path.exists() or not handoff_path.exists():
            continue
        pending = load_json(pending_path)
        if str(pending.get("claim_status", "")).lower() == "active":
            continue
        if str(pending.get("pending_state", "")).lower() in {"closed", "released", "completed"}:
            continue
        handoff = load_json(handoff_path)
        payload_ref = str(handoff.get("payload_ref", "")).strip()
        if not payload_ref:
            continue
        payload_path = Path(payload_ref) if Path(payload_ref).is_absolute() else (repo_root / payload_ref)
        if not payload_path.exists():
            continue
        try:
            package = load_gate_ready_package(payload_path)
        except Exception:
            package = None
        return {
            "item_key": item_key,
            "entry": entry,
            "pending": pending,
            "pending_path": pending_path,
            "handoff": handoff,
            "handoff_path": handoff_path,
            "payload_path": payload_path,
            "package": package,
        }
    return None


def active_claimed_item(repo_root: Path, actor_ref: str) -> dict[str, Any] | None:
    pending_dir = repo_root / "artifacts" / "active" / "gates" / "pending"
    if not pending_dir.exists():
        return None
    for pending_path in sorted(pending_dir.glob("*.json")):
        if pending_path.name.startswith("_"):
            continue
        pending = load_json(pending_path)
        if str(pending.get("claim_status", "")).lower() != "active":
            continue
        if str(pending.get("claim_owner", "")) != actor_ref:
            continue
        claimed_run_id = str(pending.get("claimed_run_id", "")).strip()
        if not claimed_run_id:
            continue
        artifacts_dir = output_dir_for(repo_root, claimed_run_id)
        current_request = request_path(artifacts_dir)
        current_state = round_state_path(artifacts_dir)
        if not current_request.exists() or not current_state.exists():
            continue
        return {
            "run_id": claimed_run_id,
            "artifacts_dir": artifacts_dir,
            "request": load_json(current_request),
            "state": load_json(current_state),
            "handoff_ref": str(pending.get("handoff_ref", "")).strip(),
            "gate_pending_ref": repo_relative(repo_root, pending_path),
            "claim_ref": repo_relative(repo_root, artifacts_dir / "queue-claim.json"),
            "request_ref": repo_relative(repo_root, current_request),
        }
    return None
