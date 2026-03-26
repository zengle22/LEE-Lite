#!/usr/bin/env python3
"""Human approval round orchestration for ll-gate-human-orchestrator."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from gate_human_orchestrator_common import dump_json, load_gate_ready_package, load_json, repo_relative
from gate_human_orchestrator_projection import write_bundle_files
from gate_human_orchestrator_queue import active_claimed_item, claimable_queue_item
from gate_human_orchestrator_round_support import (
    human_brief_payload,
    load_ssot_brief,
    refresh_round_input_if_needed,
    refresh_request_brief,
    request_markdown,
    request_path,
    review_summary,
    round_state_path,
    submission_path,
    synthetic_gate_ready_package,
)
from gate_human_orchestrator_runtime import _run_gate_command, default_run_id, output_dir_for, run_workflow


ALLOWED_ACTIONS = ["approve", "revise", "retry", "handoff", "reject"]
_CLOSEABLE_STATUSES = {"decision_recorded", "closed"}


def prepare_round(input_path: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    package = load_gate_ready_package(input_path)
    effective_run_id = run_id or default_run_id(package.package_path)
    artifacts_dir = output_dir_for(repo_root, effective_run_id)
    if artifacts_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {artifacts_dir}")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    decision_target = str(package.payload.get("candidate_ref", ""))
    machine_ssot_ref = str(package.payload.get("machine_ssot_ref", ""))
    ssot_brief = load_ssot_brief(repo_root, machine_ssot_ref)
    audit_ref = repo_root / "artifacts" / "active" / "audit" / "finding-bundle.json"
    audit_refs = [repo_relative(repo_root, audit_ref)] if audit_ref.exists() else []
    request = {
        "title": f"人工审批处理单 {effective_run_id}",
        "input_ref": repo_relative(repo_root, package.package_path),
        "pending_human_decision_ref": f"artifacts/gate-human-orchestrator/{effective_run_id}/pending-human-decision.json",
        "decision_target": decision_target,
        "machine_ssot_ref": machine_ssot_ref,
        "decision_question": "请判断这个候选对象应当通过、退回修改、重试、转交，还是拒绝。",
        "focus_points": [
            "确认 decision target 是否就是这次要审批的候选版本。",
            "确认当前 Machine SSOT 和 evidence 是否足够支撑本轮审批。",
            "确认该对象应继续推进、退回修订、重新入队、转交处理，还是直接终止。",
        ],
        "allowed_actions": ALLOWED_ACTIONS,
        "reply_examples": [
            "approve",
            "revise: <原因>",
            "retry: <原因>",
            "handoff: <目标> | <原因>",
            "reject: <原因>",
        ],
        "basis_refs_hint": [repo_relative(repo_root, package.package_path), str(package.payload.get("evidence_bundle_ref", "")), *audit_refs],
        "ssot_excerpt": ssot_brief["excerpt"],
        "ssot_fulltext_markdown": ssot_brief["fulltext_markdown"],
        "ssot_outline": ssot_brief["outline"],
        "review_checkpoints": ssot_brief["review_points"],
    }
    state = {
        "run_id": effective_run_id,
        "status": "pending_human_reply",
        "input_ref": repo_relative(repo_root, package.package_path),
        "decision_target": decision_target,
        "machine_ssot_ref": machine_ssot_ref,
        "audit_finding_refs": audit_refs,
        "request_ref": repo_relative(repo_root, request_path(artifacts_dir)),
        "submission_ref": "",
        "bundle_ref": "",
    }
    dump_json(request_path(artifacts_dir), request)
    (artifacts_dir / "human-decision-request.md").write_text(request_markdown(request), encoding="utf-8")
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
    dump_json(round_state_path(artifacts_dir), state)
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
        "request_ref": str(request_path(artifacts_dir)),
        "pending_human_decision_ref": repo_relative(repo_root, artifacts_dir / "pending-human-decision.json"),
        "status": state["status"],
        "review_summary": review_summary(request, status=state["status"]),
        "human_brief": human_brief_payload(request, status=state["status"]),
    }


def claim_next(repo_root: Path, run_id: str, allow_update: bool = False, actor_ref: str = "ll-gate-human-orchestrator") -> dict[str, Any]:
    item = claimable_queue_item(repo_root)
    if not item:
        active = active_claimed_item(repo_root, actor_ref)
        if active:
            status = str(active["state"].get("status", "claimed"))
            request = refresh_request_brief(repo_root, active["artifacts_dir"]) or active["request"]
            return {
                "ok": True,
                "run_id": active["run_id"],
                "artifacts_dir": str(active["artifacts_dir"]),
                "handoff_ref": active["handoff_ref"],
                "gate_pending_ref": active["gate_pending_ref"],
                "claim_ref": active["claim_ref"],
                "request_ref": active["request_ref"],
                "status": status,
                "reused_active_claim": True,
                "review_summary": review_summary(request, status=status),
                "human_brief": human_brief_payload(request, status=status),
            }
        raise FileNotFoundError("no claimable gate pending item found")

    effective_run_id = run_id or item["item_key"]
    artifacts_dir = output_dir_for(repo_root, effective_run_id)
    package_input = item["payload_path"]
    if item.get("package") is None:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        package_input = synthetic_gate_ready_package(repo_root, artifacts_dir, item["handoff"], item["payload_path"])
    prepared = prepare_round(package_input, repo_root, effective_run_id, allow_update=True)
    artifacts_dir = Path(prepared["artifacts_dir"])
    state = load_json(round_state_path(artifacts_dir))
    claim_ref = artifacts_dir / "queue-claim.json"
    dump_json(
        claim_ref,
        {
            "run_id": effective_run_id,
            "handoff_ref": repo_relative(repo_root, item["handoff_path"]),
            "gate_pending_ref": repo_relative(repo_root, item["pending_path"]),
            "payload_ref": repo_relative(repo_root, item["payload_path"]),
            "claim_owner": actor_ref,
            "claim_status": "active",
        },
    )
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
    dump_json(round_state_path(artifacts_dir), state)
    request = load_json(request_path(artifacts_dir))
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(artifacts_dir),
        "handoff_ref": repo_relative(repo_root, item["handoff_path"]),
        "gate_pending_ref": repo_relative(repo_root, item["pending_path"]),
        "claim_ref": str(claim_ref),
        "request_ref": prepared["request_ref"],
        "status": "claimed",
        "review_summary": review_summary(request, status=state["status"]),
        "human_brief": human_brief_payload(request, status=state["status"]),
    }


def show_pending(repo_root: Path) -> dict[str, Any]:
    root = repo_root / "artifacts" / "gate-human-orchestrator"
    items: list[dict[str, Any]] = []
    if root.exists():
        for state_path in sorted(root.glob("*/round-state.json")):
            state = load_json(state_path)
            if state.get("status") != "pending_human_reply":
                continue
            request = refresh_request_brief(repo_root, state_path.parent)
            items.append(
                {
                    "run_id": state.get("run_id", ""),
                    "artifacts_dir": str(state_path.parent),
                    "decision_target": state.get("decision_target", ""),
                    "request_ref": state.get("request_ref", ""),
                    "review_summary": review_summary(request, status=str(state.get("status", ""))),
                    "human_brief": human_brief_payload(request, status=str(state.get("status", ""))),
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
        if not target:
            raise ValueError("handoff reply requires a target before '|'")
        return {"decision": "handoff", "decision_reason": parts[1] if len(parts) == 2 else f"handoff to {target}", "decision_target": target}
    if decision == "approve":
        return {"decision": "approve", "decision_reason": body or "approved by human reviewer", "decision_target": default_target}
    if not body:
        raise ValueError(f"{decision} reply requires a reason")
    return {"decision": decision, "decision_reason": body, "decision_target": default_target}


def capture_decision(artifacts_dir: Path, repo_root: Path, reply: str, approver: str, allow_update: bool = False) -> dict[str, Any]:
    state = load_json(round_state_path(artifacts_dir))
    if state.get("status") != "pending_human_reply":
        raise ValueError(f"round is not awaiting human reply: {state.get('status', 'unknown')}")
    input_path = refresh_round_input_if_needed(repo_root, artifacts_dir, state)
    package = load_gate_ready_package(input_path)
    runtime_target = str(package.payload.get("candidate_ref", "")) or str(state.get("decision_target", ""))
    parsed = parse_human_reply(reply, runtime_target)
    dump_json(
        submission_path(artifacts_dir),
        {
            "pending_human_decision_ref": state.get("request_ref", ""),
            "decision": parsed["decision"],
            "decision_reason": parsed["decision_reason"],
            "decision_target": parsed["decision_target"],
            "decision_basis_refs": load_json(request_path(artifacts_dir)).get("basis_refs_hint", []),
            "approver": approver,
        },
    )
    result = run_workflow(
        input_path=input_path,
        repo_root=repo_root,
        run_id=str(state["run_id"]),
        decision=parsed["decision"],
        decision_reason=parsed["decision_reason"],
        decision_target=parsed["decision_target"],
        audit_finding_refs=list(state.get("audit_finding_refs", [])),
        allow_update=True,
    )
    bundle_path = Path(result["artifacts_dir"]) / "gate-decision-bundle.json"
    bundle = load_json(bundle_path)
    for ref_value in (repo_relative(repo_root, request_path(artifacts_dir)), repo_relative(repo_root, submission_path(artifacts_dir))):
        if ref_value not in bundle["source_refs"]:
            bundle["source_refs"].append(ref_value)
    write_bundle_files(Path(result["artifacts_dir"]), bundle)
    state.update(
        {
            "status": "decision_recorded",
            "submission_ref": repo_relative(repo_root, submission_path(artifacts_dir)),
            "bundle_ref": repo_relative(repo_root, bundle_path),
        }
    )
    dump_json(round_state_path(artifacts_dir), state)
    return {
        "ok": True,
        "artifacts_dir": result["artifacts_dir"],
        "decision": parsed["decision"],
        "submission_ref": str(submission_path(artifacts_dir)),
        "bundle_ref": str(bundle_path),
    }


def close_run(artifacts_dir: Path, repo_root: Path, allow_update: bool = False) -> dict[str, Any]:
    del allow_update
    state_path = round_state_path(artifacts_dir)
    if not state_path.exists():
        raise FileNotFoundError(f"round-state not found: {state_path}")
    state = load_json(state_path)
    run_id = str(state.get("run_id", "")).strip()
    status = str(state.get("status", "")).strip()
    if not run_id:
        raise ValueError("round-state missing run_id")
    if status == "closed":
        return {
            "ok": True,
            "run_id": run_id,
            "artifacts_dir": str(artifacts_dir),
            "status": "closed",
            "run_closure_ref": str(state.get("run_closure_ref", "")),
            "gate_pending_ref": str(state.get("gate_pending_ref", "")),
            "gate_decision_ref": "",
        }
    if status not in _CLOSEABLE_STATUSES:
        raise ValueError(f"round is not closeable: {status or 'unknown'}")

    bundle_ref = str(state.get("bundle_ref", "")).strip()
    gate_decision_ref = ""
    if bundle_ref:
        bundle_path = repo_root / Path(bundle_ref)
        if bundle_path.exists():
            gate_decision_ref = str(load_json(bundle_path).get("decision_ref", "")).strip()
    if not gate_decision_ref:
        raise ValueError("cannot close round before gate decision is recorded")

    request_path_cli = artifacts_dir / "_cli" / "gate-close-run.request.json"
    response_path_cli = artifacts_dir / "_cli" / "gate-close-run.response.json"
    dump_json(
        request_path_cli,
        {
            "api_version": "v1",
            "command": "gate.close-run",
            "request_id": f"req-gate-close-run-{run_id}",
            "workspace_root": repo_root.as_posix(),
            "actor_ref": "ll-gate-human-orchestrator",
            "trace": {"run_ref": run_id, "workflow_key": "governance.gate-human-orchestrator"},
            "payload": {"run_ref": run_id, "gate_decision_ref": gate_decision_ref},
        },
    )
    close_data = _run_gate_command(["gate", "close-run"], request_path_cli, response_path_cli)["data"]

    gate_pending_ref = str(state.get("gate_pending_ref", "")).strip()
    if gate_pending_ref:
        pending_path = repo_root / Path(gate_pending_ref)
        if pending_path.exists():
            pending = load_json(pending_path)
            pending.update(
                {
                    "claim_status": "released",
                    "claim_owner": "",
                    "released_run_id": run_id,
                    "pending_state": "closed",
                    "run_closure_ref": str(close_data.get("run_closure_ref", "")),
                    "gate_decision_ref": gate_decision_ref,
                }
            )
            dump_json(pending_path, pending)

    claim_path = artifacts_dir / "queue-claim.json"
    if claim_path.exists():
        claim = load_json(claim_path)
        claim["claim_status"] = "released"
        claim["run_closure_ref"] = str(close_data.get("run_closure_ref", ""))
        dump_json(claim_path, claim)

    state["status"] = "closed"
    state["run_closure_ref"] = str(close_data.get("run_closure_ref", ""))
    dump_json(state_path, state)
    return {
        "ok": True,
        "run_id": run_id,
        "artifacts_dir": str(artifacts_dir),
        "status": "closed",
        "run_closure_ref": str(close_data.get("run_closure_ref", "")),
        "gate_pending_ref": gate_pending_ref,
        "gate_decision_ref": gate_decision_ref,
    }
