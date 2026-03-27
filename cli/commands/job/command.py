"""Runner job control commands."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.execution_runner import run_job
from cli.lib.job_outcome import complete_job, fail_job
from cli.lib.job_queue import claim_job, release_hold_job, renew_job_lease
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.errors import ensure, parse_int


def _job_handler(ctx: CommandContext):
    payload = ctx.payload
    actor_ref = str(ctx.request.get("actor_ref") or "runner.operator")
    owner_ref = str(payload.get("runner_id") or actor_ref)
    if ctx.action == "renew-lease":
        job_ref = str(payload.get("job_ref") or "")
        ensure(job_ref, "INVALID_REQUEST", "job_ref is required")
        result = renew_job_lease(
            ctx.workspace_root,
            job_ref=job_ref,
            runner_id=owner_ref,
            actor_ref=actor_ref,
            lease_timeout_seconds=parse_int(payload.get("lease_timeout_seconds"), field_name="lease_timeout_seconds", minimum=1)
            if payload.get("lease_timeout_seconds") is not None
            else None,
        )
        return "OK", "job lease renewed", result, [], [result["renewed_job_ref"]]
    if ctx.action == "claim":
        ready_job_ref = str(payload.get("ready_job_ref") or payload.get("job_ref") or "")
        ensure(ready_job_ref, "INVALID_REQUEST", "ready_job_ref is required")
        result = claim_job(
            ctx.workspace_root,
            ready_job_ref,
            runner_id=owner_ref,
            actor_ref=actor_ref,
            runner_run_id=str(payload.get("runner_run_id") or ctx.trace.get("run_ref") or ctx.request["request_id"]),
            lease_timeout_seconds=parse_int(payload.get("lease_timeout_seconds"), field_name="lease_timeout_seconds", minimum=1)
            if payload.get("lease_timeout_seconds") is not None
            else None,
        )
        return "OK", "job claimed", result, [], [result["claimed_job_ref"]]
    if ctx.action == "release-hold":
        job_ref = str(payload.get("job_ref") or "")
        ensure(job_ref, "INVALID_REQUEST", "job_ref is required")
        result = release_hold_job(
            ctx.workspace_root,
            job_ref,
            actor_ref=actor_ref,
            note=str(payload.get("note") or "").strip() or None,
        )
        return "OK", "job released from hold", result, [], [result["released_job_ref"]]
    if ctx.action == "run":
        job_ref = str(payload.get("job_ref") or "")
        ensure(job_ref, "INVALID_REQUEST", "job_ref is required")
        if payload.get("heartbeat_only") or payload.get("lease_action") == "heartbeat":
            result = renew_job_lease(
                ctx.workspace_root,
                job_ref=job_ref,
                runner_id=owner_ref,
                actor_ref=actor_ref,
                lease_timeout_seconds=parse_int(payload.get("lease_timeout_seconds"), field_name="lease_timeout_seconds", minimum=1)
                if payload.get("lease_timeout_seconds") is not None
                else None,
            )
            return "OK", "job lease renewed", result, [], [result["renewed_job_ref"]]
        result = run_job(
            ctx.workspace_root,
            job_ref=job_ref,
            trace=ctx.trace,
            request_id=str(ctx.request["request_id"]),
            actor_ref=actor_ref,
            owner_ref=owner_ref,
            payload=payload,
        )
        return "OK", "job run completed", result, [], [result["execution_attempt_ref"], result["job_ref"]]
    if ctx.action == "complete":
        job_ref = str(payload.get("job_ref") or "")
        ensure(job_ref, "INVALID_REQUEST", "job_ref is required")
        result = complete_job(
            ctx.workspace_root,
            job_ref=job_ref,
            trace=ctx.trace,
            actor_ref=actor_ref,
            owner_ref=owner_ref,
            execution_attempt_ref=str(payload.get("execution_attempt_ref") or ""),
            result=payload.get("result") if isinstance(payload.get("result"), dict) else None,
        )
        return "OK", "job marked complete", result, [], [result["execution_outcome_ref"], result["completed_job_ref"]]
    job_ref = str(payload.get("job_ref") or "")
    ensure(job_ref, "INVALID_REQUEST", "job_ref is required")
    result = fail_job(
        ctx.workspace_root,
        job_ref=job_ref,
        trace=ctx.trace,
        actor_ref=actor_ref,
        owner_ref=owner_ref,
        reason=str(payload.get("reason") or "job execution failed"),
        execution_attempt_ref=str(payload.get("execution_attempt_ref") or ""),
        failure_mode=str(payload.get("failure_mode") or "failed"),
        result=payload.get("result") if isinstance(payload.get("result"), dict) else None,
    )
    return "OK", "job marked failed", result, [], [result["execution_outcome_ref"], result["job_ref"]]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _job_handler)
