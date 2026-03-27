"""Bootstrap and restore runner entry context for execution loop entry surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError
from cli.lib.fs import load_json, to_canonical_path, write_json
from cli.lib.job_state import utc_now
from cli.lib.protocol import ExecutionRunnerRunRef, ExecutionRunnerStartRequest, RunnerEntryReceipt
from cli.lib.registry_store import slugify


def bootstrap_runner_entry(
    workspace_root: Path,
    *,
    request_id: str,
    actor_ref: str,
    trace: dict[str, Any],
    start_request: ExecutionRunnerStartRequest,
) -> ExecutionRunnerRunRef:
    context_path = _context_path(workspace_root, start_request.runner_scope_ref)
    runner_path = _run_path(workspace_root, start_request.runner_scope_ref)
    receipt_path = _receipt_path(workspace_root, start_request.runner_scope_ref, start_request.entry_mode)
    now = utc_now()

    if start_request.entry_mode == "resume" and not context_path.exists():
        raise CommandError("PRECONDITION_FAILED", "resume_target_not_found: runner context not found")

    if context_path.exists():
        context = load_json(context_path)
        _ensure_context_matches(context, start_request)
        started_at = str(context.get("started_at") or now)
        runner_run_id = str(context.get("runner_run_id") or start_request.runner_run_id)
    else:
        started_at = now
        runner_run_id = start_request.runner_run_id
        context = {
            "runner_scope_ref": start_request.runner_scope_ref,
            "queue_ref": start_request.queue_ref,
            "runner_run_id": runner_run_id,
            "started_at": started_at,
        }

    runner_run_ref = to_canonical_path(runner_path, workspace_root)
    runner_context_ref = to_canonical_path(context_path, workspace_root)
    entry_receipt_ref = to_canonical_path(receipt_path, workspace_root)

    context.update(
        {
            "runner_scope_ref": start_request.runner_scope_ref,
            "queue_ref": start_request.queue_ref,
            "runner_run_id": runner_run_id,
            "runner_run_ref": runner_run_ref,
            "runner_context_ref": runner_context_ref,
            "last_entry_mode": start_request.entry_mode,
            "last_entry_at": now,
            "last_entry_receipt_ref": entry_receipt_ref,
            "last_actor_ref": actor_ref,
            "trace": trace,
            "started_at": started_at,
        }
    )
    if start_request.entry_mode == "resume":
        context["resumed_at"] = now
    write_json(context_path, context)

    run_record = {
        "runner_scope_ref": start_request.runner_scope_ref,
        "runner_run_id": runner_run_id,
        "runner_run_ref": runner_run_ref,
        "runner_context_ref": runner_context_ref,
        "queue_ref": start_request.queue_ref,
        "entry_mode": start_request.entry_mode,
        "started_at": started_at,
        "last_entry_at": now,
        "actor_ref": actor_ref,
        "trace": trace,
    }
    write_json(runner_path, run_record)

    receipt = RunnerEntryReceipt(
        runner_run_ref=runner_run_ref,
        runner_context_ref=runner_context_ref,
        entry_receipt_ref=entry_receipt_ref,
        entry_mode=start_request.entry_mode,
        started_at=started_at,
    )
    write_json(
        receipt_path,
        {
            **receipt.to_dict(),
            "runner_scope_ref": start_request.runner_scope_ref,
            "runner_run_id": runner_run_id,
            "queue_ref": start_request.queue_ref,
            "request_id": request_id,
            "accepted_at": now,
            "actor_ref": actor_ref,
            "trace": trace,
        },
    )

    return ExecutionRunnerRunRef(
        runner_run_ref=runner_run_ref,
        runner_context_ref=runner_context_ref,
        entry_receipt_ref=entry_receipt_ref,
        runner_scope_ref=start_request.runner_scope_ref,
        entry_mode=start_request.entry_mode,
        queue_ref=start_request.queue_ref,
        started_at=started_at,
        runner_run_id=runner_run_id,
    )


def _context_path(workspace_root: Path, runner_scope_ref: str) -> Path:
    return workspace_root / "artifacts" / "active" / "runner" / "contexts" / f"{slugify(runner_scope_ref)}.json"


def _run_path(workspace_root: Path, runner_scope_ref: str) -> Path:
    return workspace_root / "artifacts" / "active" / "runner" / "runs" / f"{slugify(runner_scope_ref)}.json"


def _receipt_path(workspace_root: Path, runner_scope_ref: str, entry_mode: str) -> Path:
    slug = slugify(f"{runner_scope_ref}-{entry_mode}")
    return workspace_root / "artifacts" / "active" / "runner" / "receipts" / f"{slug}.json"


def _ensure_context_matches(context: dict[str, Any], start_request: ExecutionRunnerStartRequest) -> None:
    existing_scope = str(context.get("runner_scope_ref") or "").strip()
    if existing_scope and existing_scope != start_request.runner_scope_ref:
        raise CommandError("PRECONDITION_FAILED", "runner_context_conflict: runner scope mismatch")
    existing_queue = str(context.get("queue_ref") or "").strip()
    if existing_queue and existing_queue != start_request.queue_ref:
        raise CommandError("PRECONDITION_FAILED", "runner_context_conflict: queue scope mismatch")
    existing_run_id = str(context.get("runner_run_id") or "").strip()
    if start_request.entry_mode == "start" and existing_run_id and existing_run_id != start_request.runner_run_id:
        raise CommandError("PRECONDITION_FAILED", "runner_context_conflict: runner_run_id mismatch")
