"""Execution runner control flow."""

from __future__ import annotations

from typing import Any

from cli.lib.errors import CommandError
from cli.lib.fs import canonical_to_path, write_json
from cli.lib.job_state import (
    ensure_job_lease_active,
    ensure_job_owner,
    lease_expiry_for_now,
    load_job_record,
    resolve_lease_timeout_seconds,
    transition_job,
    update_job,
    utc_now,
)
from cli.lib.skill_invoker import invoke_target


def run_job(
    workspace_root,
    *,
    job_ref: str,
    trace: dict[str, Any],
    request_id: str,
    actor_ref: str,
    owner_ref: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _, job = load_job_record(workspace_root, job_ref)
    if str(job.get("status") or "") != "claimed":
        raise CommandError("PRECONDITION_FAILED", f"job is not claimable for run: {job_ref}")
    ensure_job_owner(job, owner_ref=owner_ref, job_ref=job_ref)
    ensure_job_lease_active(job, job_ref=job_ref)
    timeout_seconds = resolve_lease_timeout_seconds(job)

    running_ref, running_job = transition_job(
        workspace_root,
        job_ref,
        "running",
        actor_ref=actor_ref,
        note="runner started job execution",
        updates={
            "started_at": job.get("started_at") or utc_now(),
            "lease_expires_at": lease_expiry_for_now(timeout_seconds=timeout_seconds),
        },
    )
    attempt_ref = f"artifacts/evidence/execution/{running_job['job_id']}-attempt.json"
    try:
        dispatch_result = invoke_target(workspace_root, trace, request_id, running_job, payload, job_ref=running_ref)
        recommended_outcome = "done" if dispatch_result.get("ok") else "failed"
        error_message = ""
    except CommandError as exc:
        dispatch_result = {"ok": False, "target_skill": running_job.get("target_skill", ""), "error": exc.message}
        recommended_outcome = "failed"
        error_message = exc.message

    attempt_payload = {
        "trace": trace,
        "request_id": request_id,
        "job_ref": running_ref,
        "job_id": running_job["job_id"],
        "target_skill": running_job.get("target_skill", ""),
        "attempted_at": utc_now(),
        "recommended_outcome": recommended_outcome,
        "dispatch_result": dispatch_result,
    }
    write_json(canonical_to_path(attempt_ref, workspace_root), attempt_payload)
    update_job(workspace_root, running_ref, {"last_attempt_ref": attempt_ref})
    return {
        "canonical_path": attempt_ref,
        "job_ref": running_ref,
        "execution_attempt_ref": attempt_ref,
        "recommended_outcome": recommended_outcome,
        "dispatch_result": dispatch_result,
        "error": error_message,
    }
