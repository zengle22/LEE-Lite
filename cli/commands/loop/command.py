"""Execution loop commands."""

from __future__ import annotations

from argparse import Namespace
from typing import Any

from cli.lib.errors import ensure, parse_int
from cli.lib.execution_runner import run_job
from cli.lib.job_outcome import complete_job, fail_job
from cli.lib.job_queue import claim_job, list_ready_jobs
from cli.lib.protocol import CommandContext, ExecutionRunnerStartRequest, run_with_protocol
from cli.lib.runner_entry import bootstrap_runner_entry
from cli.lib.runner_monitor import write_recovery_snapshot, write_status_snapshot


def _max_jobs(payload: dict[str, Any], ready_jobs: list[dict[str, Any]]) -> int:
    if payload.get("ready_job_ref"):
        return 1
    if payload.get("consume_all"):
        return len(ready_jobs)
    requested = parse_int(payload.get("max_jobs", 1), field_name="max_jobs", minimum=1)
    return requested


def _recovery_action(payload: dict[str, Any]) -> str | None:
    for key in ("recovery_action", "recovery_mode"):
        value = str(payload.get(key) or "").strip().lower()
        if value:
            ensure(value in {"scan", "repair"}, "INVALID_REQUEST", f"unsupported recovery_action: {value}")
            return value
    return None


def _run_execution(ctx: CommandContext):
    payload = ctx.payload
    actor_ref = str(ctx.request.get("actor_ref") or "runner.operator")
    owner_ref = str(payload.get("runner_id") or actor_ref)
    entry_request = ExecutionRunnerStartRequest.from_command_context(
        ctx,
        default_entry_mode="resume" if ctx.action == "resume-execution" else None,
    )
    entry_result = (
        bootstrap_runner_entry(
            ctx.workspace_root,
            request_id=str(ctx.request["request_id"]),
            actor_ref=actor_ref,
            trace=ctx.trace,
            start_request=entry_request,
        )
        if entry_request
        else None
    )
    ready_jobs = [{"job_ref": str(payload["ready_job_ref"])}] if payload.get("ready_job_ref") else list_ready_jobs(ctx.workspace_root)
    processed: list[dict[str, Any]] = []
    for item in ready_jobs[: _max_jobs(payload, ready_jobs)]:
        claimed = claim_job(
            ctx.workspace_root,
            str(item["job_ref"]),
            runner_id=owner_ref,
            actor_ref=actor_ref,
            runner_run_id=str(
                (entry_result.runner_run_id if entry_result else "")
                or payload.get("runner_run_id")
                or ctx.trace.get("run_ref")
                or ctx.request["request_id"]
            ),
        )
        attempt = run_job(
            ctx.workspace_root,
            job_ref=claimed["job_ref"],
            trace=ctx.trace,
            request_id=str(ctx.request["request_id"]),
            actor_ref=actor_ref,
            owner_ref=owner_ref,
            payload=payload,
        )
        if attempt["recommended_outcome"] == "done":
            outcome = complete_job(
                ctx.workspace_root,
                job_ref=attempt["job_ref"],
                trace=ctx.trace,
                actor_ref=actor_ref,
                owner_ref=owner_ref,
                execution_attempt_ref=attempt["execution_attempt_ref"],
                result=attempt["dispatch_result"] if isinstance(attempt["dispatch_result"], dict) else None,
            )
        else:
            outcome = fail_job(
                ctx.workspace_root,
                job_ref=attempt["job_ref"],
                trace=ctx.trace,
                actor_ref=actor_ref,
                owner_ref=owner_ref,
                reason=str(attempt.get("error") or "runner dispatch failed"),
                execution_attempt_ref=attempt["execution_attempt_ref"],
                failure_mode=str(payload.get("failure_mode") or "failed"),
                result=attempt["dispatch_result"] if isinstance(attempt["dispatch_result"], dict) else None,
            )
        processed.append(
            {
                "claimed_job_ref": claimed["job_ref"],
                "execution_attempt_ref": attempt["execution_attempt_ref"],
                "execution_outcome_ref": outcome["execution_outcome_ref"],
                "final_job_ref": outcome["job_ref"],
                "final_status": outcome["status"],
            }
        )
    report_ref = f"artifacts/active/runner/{ctx.request['request_id']}-run-execution.json"
    from cli.lib.fs import canonical_to_path, write_json

    write_json(canonical_to_path(report_ref, ctx.workspace_root), {"processed_jobs": processed, "requested_count": len(ready_jobs)})
    post_run_snapshot = write_status_snapshot(
        ctx.workspace_root,
        name=f"{ctx.request['request_id']}-post-run-status",
    )
    data = {
        "canonical_path": report_ref,
        "runner_run_ref": report_ref,
        "processed_count": len(processed),
        "processed_jobs": processed,
        "post_run_snapshot_ref": post_run_snapshot["snapshot_ref"],
        "post_run_counts": post_run_snapshot["counts"],
        "post_run_queue_summary": post_run_snapshot["queue_summary"],
        "recoverable_queue_summary": post_run_snapshot["recoverable_queue_summary"],
    }
    if entry_result:
        data.update(entry_result.to_dict())
    return "OK", "execution loop completed", data, [], [report_ref, post_run_snapshot["snapshot_ref"], *[item["execution_outcome_ref"] for item in processed], *(([entry_result.entry_receipt_ref, entry_result.runner_context_ref, entry_result.runner_run_ref]) if entry_result else [])]


def _run_recovery(ctx: CommandContext, recovery_action: str):
    payload = ctx.payload
    actor_ref = str(ctx.request.get("actor_ref") or "runner.operator")
    snapshot = write_recovery_snapshot(
        ctx.workspace_root,
        name=f"{ctx.request['request_id']}-recovery-{recovery_action}",
        actor_ref=actor_ref,
        recovery_action=recovery_action,
        status_filter=str(payload.get("status_filter") or "").strip() or None,
    )
    return "OK", f"runner recovery {recovery_action} completed", snapshot, [], [snapshot["snapshot_ref"]]


def _loop_handler(ctx: CommandContext):
    recovery_action = _recovery_action(ctx.payload)
    if ctx.action == "recover-jobs":
        return _run_recovery(ctx, recovery_action or "scan")
    if recovery_action:
        return _run_recovery(ctx, recovery_action)
    if ctx.action in {"run-execution", "resume-execution"}:
        return _run_execution(ctx)
    name = "runner-backlog" if ctx.action == "show-backlog" else "runner-status"
    status_filter = "ready" if ctx.action == "show-backlog" else None
    snapshot = write_status_snapshot(ctx.workspace_root, name=name, status_filter=status_filter)
    return "OK", "runner snapshot emitted", snapshot, [], [snapshot["snapshot_ref"]]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _loop_handler)
