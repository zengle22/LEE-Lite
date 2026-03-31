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


def _queue_index_items(repo_root: Path) -> list[tuple[str, dict[str, Any], Path]]:
    queue_items: list[tuple[str, dict[str, Any], Path]] = []
    index_path = pending_index_path(repo_root)
    pending_dir = repo_root / "artifacts" / "active" / "gates" / "pending"
    if index_path.exists():
        index = load_json(index_path)
        handoffs = index.get("handoffs", {})
        if isinstance(handoffs, dict):
            for item_key in sorted(handoffs):
                entry = handoffs[item_key]
                if isinstance(entry, dict) and str(entry.get("gate_pending_ref", "")):
                    queue_items.append((item_key, entry, repo_root / str(entry["gate_pending_ref"])))
        return queue_items
    if pending_dir.exists():
        for pending_path in sorted(pending_dir.glob("*.json")):
            if not pending_path.name.startswith("_"):
                queue_items.append((pending_path.stem, {"gate_pending_ref": repo_relative(repo_root, pending_path)}, pending_path))
    return queue_items


def _load_queue_item(repo_root: Path, item_key: str, entry: dict[str, Any], pending_path: Path) -> dict[str, Any] | None:
    handoff_ref = str(entry.get("handoff_ref", ""))
    if not handoff_ref and pending_path.exists():
        handoff_ref = str(load_json(pending_path).get("handoff_ref", ""))
    if not handoff_ref:
        return None
    handoff_path = repo_root / handoff_ref
    if not pending_path.exists() or not handoff_path.exists():
        return None
    pending = load_json(pending_path)
    handoff = load_json(handoff_path)
    payload_ref = str(handoff.get("payload_ref", "")).strip()
    if not payload_ref:
        return None
    payload_path = Path(payload_ref) if Path(payload_ref).is_absolute() else (repo_root / payload_ref)
    if not payload_path.exists():
        return None
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


def _queue_item_matches(item: dict[str, Any], preferred_item: str) -> bool:
    target = preferred_item.strip()
    if not target:
        return False
    candidates = {
        str(item.get("item_key", "")).strip(),
        str(item.get("pending_path", Path())).strip(),
        Path(str(item.get("pending_path", ""))).stem if str(item.get("pending_path", "")).strip() else "",
        str(item.get("handoff_path", Path())).strip(),
        Path(str(item.get("handoff_path", ""))).stem if str(item.get("handoff_path", "")).strip() else "",
        str(item.get("pending", {}).get("trace", {}).get("run_ref", "")).strip(),
        str(item.get("handoff", {}).get("trace", {}).get("run_ref", "")).strip(),
    }
    return target in {value for value in candidates if value}


def pending_queue_items(repo_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item_key, entry, pending_path in _queue_index_items(repo_root):
        item = _load_queue_item(repo_root, item_key, entry, pending_path)
        if item is not None:
            items.append(item)
    return items


def claimable_queue_item(repo_root: Path, preferred_item: str = "") -> dict[str, Any] | None:
    index_path = pending_index_path(repo_root)
    _ = index_path
    preferred = preferred_item.strip()
    fallback: dict[str, Any] | None = None
    for item in pending_queue_items(repo_root):
        pending = item["pending"]
        if str(pending.get("claim_status", "")).lower() == "active":
            continue
        if str(pending.get("pending_state", "")).lower() in {"closed", "released", "completed"}:
            continue
        if preferred and _queue_item_matches(item, preferred):
            return item
        if fallback is None:
            fallback = item
    if preferred:
        return None
    return fallback


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
