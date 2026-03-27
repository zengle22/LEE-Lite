"""Queue operations for runner-managed jobs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import to_canonical_path
from cli.lib.job_state import (
    JOB_STATUS_DIRS,
    RUNNING_STATUSES,
    claimed_job_time,
    is_job_lease_expired,
    lease_expiry_for_now,
    load_job_record,
    recover_job_to_ready,
    resolve_lease_timeout_seconds,
    refresh_job_lease,
    transition_job,
    update_job,
)


def list_jobs(workspace_root: Path, status_filter: str | None = None) -> list[dict[str, Any]]:
    statuses = [status_filter] if status_filter else list(JOB_STATUS_DIRS)
    items: list[dict[str, Any]] = []
    seen_refs: set[str] = set()
    for status in statuses:
        directory = workspace_root / JOB_STATUS_DIRS[status]
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            job_ref = to_canonical_path(path, workspace_root)
            if job_ref in seen_refs:
                continue
            seen_refs.add(job_ref)
            _, payload = load_job_record(workspace_root, job_ref)
            current_status = str(payload.get("status") or status)
            if status_filter and current_status != status_filter:
                continue
            items.append(
                {
                    "job_ref": job_ref,
                    "job_id": str(payload.get("job_id") or path.stem),
                    "status": current_status,
                    "target_skill": str(payload.get("target_skill") or ""),
                    "payload": payload,
                }
            )
    return items


def list_ready_jobs(workspace_root: Path) -> list[dict[str, Any]]:
    recover_expired_jobs(workspace_root, actor_ref="runner.recovery")
    return list_jobs(workspace_root, "ready")


def recover_expired_jobs(workspace_root: Path, *, actor_ref: str) -> list[dict[str, Any]]:
    recovered: list[dict[str, Any]] = []
    running_dir = workspace_root / JOB_STATUS_DIRS["running"]
    if not running_dir.exists():
        return recovered
    for path in sorted(running_dir.glob("*.json")):
        job_ref = to_canonical_path(path, workspace_root)
        _, payload = load_job_record(workspace_root, job_ref)
        if str(payload.get("status") or "").strip() not in RUNNING_STATUSES:
            continue
        if not is_job_lease_expired(payload):
            continue
        recovered_ref, recovered_job = recover_job_to_ready(
            workspace_root,
            job_ref,
            actor_ref=actor_ref,
            note="runner recovered expired claimed/running job",
        )
        recovered.append({"job_ref": recovered_ref, "job_id": str(recovered_job.get("job_id") or path.stem), "status": recovered_job["status"]})
    return recovered


def claim_job(
    workspace_root: Path,
    ready_job_ref: str,
    *,
    runner_id: str,
    actor_ref: str,
    runner_run_id: str,
    lease_timeout_seconds: int | None = None,
) -> dict[str, Any]:
    _, payload = load_job_record(workspace_root, ready_job_ref)
    if str(payload.get("status") or "").strip() in RUNNING_STATUSES and is_job_lease_expired(payload):
        ready_job_ref, payload = recover_job_to_ready(
            workspace_root,
            ready_job_ref,
            actor_ref=actor_ref,
            note="runner recovered expired job before claim",
        )
    ensure(str(payload.get("status") or "") == "ready", "PRECONDITION_FAILED", f"job is not ready: {ready_job_ref}")
    timeout_seconds = resolve_lease_timeout_seconds(payload, lease_timeout_seconds)
    claimed_ref, claimed_job = transition_job(
        workspace_root,
        ready_job_ref,
        "claimed",
        actor_ref=actor_ref,
        note="runner claimed ready job",
        updates={
            "claim_owner": runner_id,
            "claimed_at": claimed_job_time(),
            "runner_run_id": runner_run_id,
            "lease_timeout_seconds": timeout_seconds,
            "lease_expires_at": lease_expiry_for_now(timeout_seconds=timeout_seconds),
            "heartbeat_count": 0,
            "heartbeat_at": "",
            "lease_renewed_at": "",
        },
    )
    return {
        "canonical_path": claimed_ref,
        "job_ref": claimed_ref,
        "claimed_job_ref": claimed_ref,
        "job_id": claimed_job["job_id"],
        "status": claimed_job["status"],
    }


def renew_job_lease(
    workspace_root: Path,
    job_ref: str,
    *,
    runner_id: str,
    actor_ref: str,
    lease_timeout_seconds: int | None = None,
) -> dict[str, Any]:
    _, payload = load_job_record(workspace_root, job_ref)
    refreshed = refresh_job_lease(
        payload,
        job_ref=job_ref,
        owner_ref=runner_id,
        lease_timeout_seconds=lease_timeout_seconds,
    )
    updated_ref, updated_job = update_job(
        workspace_root,
        job_ref,
        {
            "lease_timeout_seconds": refreshed["lease_timeout_seconds"],
            "lease_expires_at": refreshed["lease_expires_at"],
            "heartbeat_at": refreshed["heartbeat_at"],
            "lease_renewed_at": refreshed["lease_renewed_at"],
            "heartbeat_count": refreshed["heartbeat_count"],
            "updated_at": refreshed["updated_at"],
            "state_history": refreshed["state_history"],
        },
    )
    return {
        "canonical_path": updated_ref,
        "job_ref": updated_ref,
        "renewed_job_ref": updated_ref,
        "job_id": updated_job["job_id"],
        "status": updated_job["status"],
        "lease_expires_at": updated_job.get("lease_expires_at", ""),
        "heartbeat_count": updated_job.get("heartbeat_count", 0),
    }
