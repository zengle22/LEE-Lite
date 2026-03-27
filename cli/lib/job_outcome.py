"""Outcome writeback for runner-managed jobs."""

from __future__ import annotations

from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, write_json
from cli.lib.job_state import ensure_job_lease_active, ensure_job_owner, load_job_record, transition_job, utc_now


def _outcome_ref(job_id: str, suffix: str) -> str:
    return f"artifacts/evidence/execution/{job_id}-{suffix}.json"


def complete_job(
    workspace_root,
    *,
    job_ref: str,
    trace: dict[str, Any],
    actor_ref: str,
    owner_ref: str,
    execution_attempt_ref: str | None = None,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _, job = load_job_record(workspace_root, job_ref)
    ensure(str(job.get("status") or "") == "running", "PRECONDITION_FAILED", f"job is not running: {job_ref}")
    ensure_job_owner(job, owner_ref=owner_ref, job_ref=job_ref)
    ensure_job_lease_active(job, job_ref=job_ref)
    outcome_ref = _outcome_ref(job["job_id"], "outcome")
    outcome_payload = {
        "trace": trace,
        "job_ref": job_ref,
        "job_id": job["job_id"],
        "outcome": "done",
        "execution_attempt_ref": execution_attempt_ref or str(job.get("last_attempt_ref") or ""),
        "recorded_at": utc_now(),
        "result": result or {},
    }
    write_json(canonical_to_path(outcome_ref, workspace_root), outcome_payload)
    done_ref, done_job = transition_job(
        workspace_root,
        job_ref,
        "done",
        actor_ref=actor_ref,
        note="runner marked job done",
        updates={"completed_at": utc_now(), "last_outcome_ref": outcome_ref},
    )
    return {
        "canonical_path": outcome_ref,
        "job_ref": done_ref,
        "completed_job_ref": done_ref,
        "execution_outcome_ref": outcome_ref,
        "status": done_job["status"],
    }


def fail_job(
    workspace_root,
    *,
    job_ref: str,
    trace: dict[str, Any],
    actor_ref: str,
    owner_ref: str,
    reason: str,
    execution_attempt_ref: str | None = None,
    failure_mode: str = "failed",
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _, job = load_job_record(workspace_root, job_ref)
    ensure(str(job.get("status") or "") == "running", "PRECONDITION_FAILED", f"job is not running: {job_ref}")
    ensure_job_owner(job, owner_ref=owner_ref, job_ref=job_ref)
    ensure_job_lease_active(job, job_ref=job_ref)
    ensure(failure_mode in {"failed", "waiting-human", "deadletter", "retry-reentry"}, "INVALID_REQUEST", f"unknown failure_mode: {failure_mode}")
    outcome_ref = _outcome_ref(job["job_id"], "outcome")
    outcome_payload = {
        "trace": trace,
        "job_ref": job_ref,
        "job_id": job["job_id"],
        "outcome": failure_mode,
        "execution_attempt_ref": execution_attempt_ref or str(job.get("last_attempt_ref") or ""),
        "recorded_at": utc_now(),
        "reason": reason,
        "result": result or {},
    }
    write_json(canonical_to_path(outcome_ref, workspace_root), outcome_payload)
    if failure_mode == "retry-reentry":
        retry_count = int(job.get("retry_count", 0))
        retry_budget = int(job.get("retry_budget", 0))
        ensure(retry_count < retry_budget, "PRECONDITION_FAILED", "retry budget exhausted")
        failed_ref, _ = transition_job(
            workspace_root,
            job_ref,
            "failed",
            actor_ref=actor_ref,
            note="runner recorded retryable failure",
            updates={"last_outcome_ref": outcome_ref, "failure_reason": reason, "failed_at": utc_now()},
        )
        ready_ref, ready_job = transition_job(
            workspace_root,
            failed_ref,
            "ready",
            actor_ref=actor_ref,
            note="runner requeued job for retry",
            updates={
                "retry_count": retry_count + 1,
                "requeued_at": utc_now(),
                "claim_owner": "",
                "runner_run_id": "",
                "claimed_at": "",
                "started_at": "",
                "lease_expires_at": "",
            },
        )
        return {
            "canonical_path": outcome_ref,
            "job_ref": ready_ref,
            "requeued_job_ref": ready_ref,
            "execution_outcome_ref": outcome_ref,
            "status": ready_job["status"],
        }
    failed_ref, failed_job = transition_job(
        workspace_root,
        job_ref,
        failure_mode,
        actor_ref=actor_ref,
        note="runner marked job failed",
        updates={"failed_at": utc_now(), "last_outcome_ref": outcome_ref, "failure_reason": reason},
    )
    return {
        "canonical_path": outcome_ref,
        "job_ref": failed_ref,
        "execution_outcome_ref": outcome_ref,
        "status": failed_job["status"],
    }
