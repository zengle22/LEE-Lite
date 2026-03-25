#!/usr/bin/env python3
"""Human approval round helpers for ll-gate-human-orchestrator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from gate_human_orchestrator_common import dump_json, load_gate_ready_package, load_json, repo_relative
from gate_human_orchestrator_projection import write_bundle_files
from gate_human_orchestrator_runtime import default_run_id, output_dir_for, repo_root_from, run_workflow


ALLOWED_ACTIONS = ["approve", "revise", "retry", "handoff", "reject"]


def _load_ssot_excerpt(repo_root: Path, machine_ssot_ref: str) -> list[str]:
    if not machine_ssot_ref:
        return []
    path = Path(machine_ssot_ref)
    ssot_path = path if path.is_absolute() else (repo_root / path)
    if not ssot_path.exists():
        return []
    payload = load_json(ssot_path)
    excerpt: list[str] = []
    for field in ("product_summary", "completed_state", "authoritative_output", "frozen_downstream_boundary"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            excerpt.append(value.strip())
    return excerpt[:4]


def _request_markdown(request: dict[str, Any]) -> str:
    lines = [
        f"# {request['title']}",
        "",
        "## Pending Item",
        "",
        f"- pending_human_decision_ref: {request['pending_human_decision_ref']}",
        f"- decision_target: {request['decision_target']}",
        f"- machine_ssot_ref: {request['machine_ssot_ref']}",
        "",
        "## Decision Question",
        "",
        f"- {request['decision_question']}",
        "",
        "## Focus Points",
        "",
    ]
    lines.extend(f"- {item}" for item in request["focus_points"])
    lines.extend(
        [
            "",
            "## Allowed Replies",
            "",
            *[f"- {item}" for item in request["reply_examples"]],
        ]
    )
    if request["ssot_excerpt"]:
        lines.extend(["", "## Machine SSOT Excerpt", ""])
        lines.extend(f"- {item}" for item in request["ssot_excerpt"])
    return "\n".join(lines) + "\n"


def _round_state_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / "round-state.json"


def _request_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / "human-decision-request.json"


def _submission_path(artifacts_dir: Path) -> Path:
    return artifacts_dir / "human-decision-submission.json"


def _pending_index_path(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "active" / "gates" / "pending" / "index.json"


def _claimable_queue_item(repo_root: Path) -> dict[str, Any] | None:
    index_path = _pending_index_path(repo_root)
    if not index_path.exists():
        return None
    index = load_json(index_path)
    handoffs = index.get("handoffs", {})
    if not isinstance(handoffs, dict):
        return None
    for item_key in sorted(handoffs):
        entry = handoffs[item_key]
        if not isinstance(entry, dict):
            continue
        pending_ref = str(entry.get("gate_pending_ref", ""))
        handoff_ref = str(entry.get("handoff_ref", ""))
        if not pending_ref or not handoff_ref:
            continue
        pending_path = repo_root / pending_ref
        handoff_path = repo_root / handoff_ref
        if not pending_path.exists() or not handoff_path.exists():
            continue
        pending = load_json(pending_path)
        if str(pending.get("claim_status", "")).lower() == "active":
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
            continue
        if not package.payload.get("candidate_ref"):
            continue
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


def prepare_round(input_path: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    package = load_gate_ready_package(input_path)
    effective_run_id = run_id or default_run_id(package.package_path)
    artifacts_dir = output_dir_for(repo_root, effective_run_id)
    if artifacts_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {artifacts_dir}")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    decision_target = str(package.payload.get("candidate_ref", ""))
    machine_ssot_ref = str(package.payload.get("machine_ssot_ref", ""))
    audit_ref = repo_root / "artifacts" / "active" / "audit" / "finding-bundle.json"
    audit_refs = [repo_relative(repo_root, audit_ref)] if audit_ref.exists() else []
    request = {
        "title": f"Human Decision Request {effective_run_id}",
        "input_ref": repo_relative(repo_root, package.package_path),
        "pending_human_decision_ref": f"artifacts/gate-human-orchestrator/{effective_run_id}/pending-human-decision.json",
        "decision_target": decision_target,
        "machine_ssot_ref": machine_ssot_ref,
        "decision_question": "Choose whether this candidate should approve, revise, retry, handoff, or reject.",
        "focus_points": [
            "Check whether the decision target matches the intended candidate version.",
            "Check whether the Machine SSOT and evidence are sufficient for this review round.",
            "Check whether the item should advance, re-enter, transfer, or stop.",
        ],
        "allowed_actions": ALLOWED_ACTIONS,
        "reply_examples": [
            "approve",
            "revise: <reason>",
            "retry: <reason>",
            "handoff: <target> | <reason>",
            "reject: <reason>",
        ],
        "basis_refs_hint": [repo_relative(repo_root, package.package_path), str(package.payload.get("evidence_bundle_ref", "")), *audit_refs],
        "ssot_excerpt": _load_ssot_excerpt(repo_root, machine_ssot_ref),
    }
    state = {
        "run_id": effective_run_id,
        "status": "pending_human_reply",
        "input_ref": repo_relative(repo_root, package.package_path),
        "decision_target": decision_target,
        "machine_ssot_ref": machine_ssot_ref,
        "audit_finding_refs": audit_refs,
        "request_ref": repo_relative(repo_root, _request_path(artifacts_dir)),
        "submission_ref": "",
        "bundle_ref": "",
    }
    dump_json(_request_path(artifacts_dir), request)
    (artifacts_dir / "human-decision-request.md").write_text(_request_markdown(request), encoding="utf-8")
    dump_json(
        artifacts_dir / "human-decision-submission.template.json",
        {
            "decision": "",
            "decision_reason": "",
            "decision_target": decision_target,
            "decision_basis_refs": request["basis_refs_hint"],
            "approver": "",
        },
    )
    dump_json(_round_state_path(artifacts_dir), state)
    dump_json(
        artifacts_dir / "pending-human-decision.json",
        {
            "run_id": effective_run_id,
            "state": "pending_human_reply",
            "decision_target": decision_target,
            "machine_ssot_ref": machine_ssot_ref,
        },
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(artifacts_dir),
        "request_ref": str(_request_path(artifacts_dir)),
        "pending_human_decision_ref": repo_relative(repo_root, artifacts_dir / "pending-human-decision.json"),
        "status": state["status"],
    }


def claim_next(repo_root: Path, run_id: str, allow_update: bool = False, actor_ref: str = "ll-gate-human-orchestrator") -> dict[str, Any]:
    item = _claimable_queue_item(repo_root)
    if not item:
        raise FileNotFoundError("no claimable gate pending item found")
    effective_run_id = run_id or item["item_key"]
    prepared = prepare_round(item["payload_path"], repo_root, effective_run_id, allow_update=allow_update)
    artifacts_dir = Path(prepared["artifacts_dir"])
    state = load_json(_round_state_path(artifacts_dir))
    claim_ref = artifacts_dir / "queue-claim.json"
    claim = {
        "run_id": effective_run_id,
        "handoff_ref": repo_relative(repo_root, item["handoff_path"]),
        "gate_pending_ref": repo_relative(repo_root, item["pending_path"]),
        "payload_ref": repo_relative(repo_root, item["payload_path"]),
        "claim_owner": actor_ref,
        "claim_status": "active",
    }
    dump_json(claim_ref, claim)
    pending = dict(item["pending"])
    pending["claim_owner"] = actor_ref
    pending["claim_status"] = "active"
    pending["claimed_run_id"] = effective_run_id
    dump_json(item["pending_path"], pending)
    state.update(
        {
            "handoff_ref": repo_relative(repo_root, item["handoff_path"]),
            "gate_pending_ref": repo_relative(repo_root, item["pending_path"]),
            "claim_ref": repo_relative(repo_root, claim_ref),
            "claim_owner": actor_ref,
        }
    )
    dump_json(_round_state_path(artifacts_dir), state)
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(artifacts_dir),
        "handoff_ref": repo_relative(repo_root, item["handoff_path"]),
        "gate_pending_ref": repo_relative(repo_root, item["pending_path"]),
        "claim_ref": str(claim_ref),
        "request_ref": prepared["request_ref"],
        "status": "claimed",
    }


def show_pending(repo_root: Path) -> dict[str, Any]:
    root = repo_root / "artifacts" / "gate-human-orchestrator"
    items: list[dict[str, Any]] = []
    if root.exists():
        for state_path in sorted(root.glob("*/round-state.json")):
            state = load_json(state_path)
            if state.get("status") == "pending_human_reply":
                items.append(
                    {
                        "run_id": state.get("run_id", ""),
                        "artifacts_dir": str(state_path.parent),
                        "decision_target": state.get("decision_target", ""),
                        "request_ref": state.get("request_ref", ""),
                    }
                )
    return {"ok": True, "pending_count": len(items), "items": items}


def parse_human_reply(reply: str, default_target: str) -> dict[str, Any]:
    text = reply.strip()
    if not text:
        raise ValueError("reply is required")
    if text.lower() == "approve":
        return {"decision": "approve", "decision_reason": "approved by human reviewer", "decision_target": default_target}
    match = re.match(r"^(approve|revise|retry|handoff|reject)\s*:\s*(.+)$", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError("reply must be one of: approve | revise: <reason> | retry: <reason> | handoff: <target> | <reason> | reject: <reason>")
    decision = match.group(1).lower()
    body = match.group(2).strip()
    if decision == "handoff":
        parts = [part.strip() for part in body.split("|", 1)]
        target = parts[0]
        reason = parts[1] if len(parts) == 2 else f"handoff to {target}"
        if not target:
            raise ValueError("handoff reply requires a target before '|'")
        return {"decision": "handoff", "decision_reason": reason, "decision_target": target}
    if decision == "approve":
        return {"decision": "approve", "decision_reason": body or "approved by human reviewer", "decision_target": default_target}
    if not body:
        raise ValueError(f"{decision} reply requires a reason")
    return {"decision": decision, "decision_reason": body, "decision_target": default_target}


def capture_decision(artifacts_dir: Path, repo_root: Path, reply: str, approver: str, allow_update: bool = False) -> dict[str, Any]:
    state = load_json(_round_state_path(artifacts_dir))
    if state.get("status") != "pending_human_reply":
        raise ValueError(f"round is not awaiting human reply: {state.get('status', 'unknown')}")
    parsed = parse_human_reply(reply, str(state.get("decision_target", "")))
    submission = {
        "pending_human_decision_ref": state.get("request_ref", ""),
        "decision": parsed["decision"],
        "decision_reason": parsed["decision_reason"],
        "decision_target": parsed["decision_target"],
        "decision_basis_refs": load_json(_request_path(artifacts_dir)).get("basis_refs_hint", []),
        "approver": approver,
    }
    dump_json(_submission_path(artifacts_dir), submission)
    result = run_workflow(
        input_path=repo_root / Path(state["input_ref"]),
        repo_root=repo_root,
        run_id=str(state["run_id"]),
        decision=submission["decision"],
        decision_reason=submission["decision_reason"],
        decision_target=submission["decision_target"],
        audit_finding_refs=list(state.get("audit_finding_refs", [])),
        allow_update=True,
    )
    bundle_path = Path(result["artifacts_dir"]) / "gate-decision-bundle.json"
    bundle = load_json(bundle_path)
    for ref_value in (repo_relative(repo_root, _request_path(artifacts_dir)), repo_relative(repo_root, _submission_path(artifacts_dir))):
        if ref_value not in bundle["source_refs"]:
            bundle["source_refs"].append(ref_value)
    write_bundle_files(Path(result["artifacts_dir"]), bundle)
    state.update(
        {
            "status": "decision_recorded",
            "submission_ref": repo_relative(repo_root, _submission_path(artifacts_dir)),
            "bundle_ref": repo_relative(repo_root, bundle_path),
        }
    )
    dump_json(_round_state_path(artifacts_dir), state)
    return {
        "ok": True,
        "artifacts_dir": result["artifacts_dir"],
        "decision": submission["decision"],
        "submission_ref": str(_submission_path(artifacts_dir)),
        "bundle_ref": str(bundle_path),
    }
