"""State helpers for runner-managed jobs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cli.lib.errors import ensure, parse_int
from cli.lib.fs import canonical_to_path, ensure_parent, load_json, to_canonical_path, write_json


JOB_STATUS_DIRS = {
    "ready": "artifacts/jobs/ready",
    "claimed": "artifacts/jobs/running",
    "running": "artifacts/jobs/running",
    "done": "artifacts/jobs/done",
    "failed": "artifacts/jobs/failed",
    "waiting-human": "artifacts/jobs/waiting-human",
    "deadletter": "artifacts/jobs/deadletter",
}
RUNNING_STATUSES = {"claimed", "running"}
TERMINAL_STATUSES = {"done", "failed", "waiting-human", "deadletter"}
DEFAULT_LEASE_TIMEOUT_SECONDS = 1800
ALLOWED_TRANSITIONS = {
    "ready": {"claimed"},
    "claimed": {"running"},
    "running": {"done", "failed", "waiting-human", "deadletter"},
    "failed": {"ready", "waiting-human", "deadletter"},
    "waiting-human": {"ready"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def claimed_job_time() -> str:
    return utc_now()


def parse_utc_timestamp(value: str) -> datetime:
    normalized = value.strip()
    ensure(bool(normalized), "INVALID_REQUEST", "timestamp is required")
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def resolve_lease_timeout_seconds(payload: dict[str, Any], override: int | None = None) -> int:
    if override is not None:
        timeout = parse_int(override, field_name="lease_timeout_seconds", minimum=1)
    else:
        stored_value = payload.get("lease_timeout_seconds")
        if stored_value in (None, ""):
            timeout = DEFAULT_LEASE_TIMEOUT_SECONDS
        else:
            timeout = parse_int(stored_value, field_name="lease_timeout_seconds", minimum=1)
    return timeout


def lease_expiry_for_now(*, timeout_seconds: int) -> str:
    expiry = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=timeout_seconds)
    return expiry.isoformat().replace("+00:00", "Z")


def is_job_lease_expired(payload: dict[str, Any]) -> bool:
    status = str(payload.get("status") or "").strip()
    if status not in RUNNING_STATUSES:
        return False
    lease_expires_at = str(payload.get("lease_expires_at") or "").strip()
    if not lease_expires_at:
        return False
    return parse_utc_timestamp(lease_expires_at) <= datetime.now(timezone.utc)


def ensure_job_lease_active(payload: dict[str, Any], *, job_ref: str) -> None:
    ensure(not is_job_lease_expired(payload), "PRECONDITION_FAILED", f"job lease expired: {job_ref}")


def job_path_for_status(workspace_root: Path, status: str, filename: str) -> Path:
    ensure(status in JOB_STATUS_DIRS, "INVALID_REQUEST", f"unknown job status: {status}")
    return workspace_root / JOB_STATUS_DIRS[status] / filename


def load_job_record(workspace_root: Path, job_ref: str) -> tuple[Path, dict[str, Any]]:
    path = canonical_to_path(job_ref, workspace_root)
    ensure(path.exists(), "PRECONDITION_FAILED", f"job file not found: {job_ref}")
    payload = load_json(path)
    ensure(isinstance(payload, dict), "INVALID_REQUEST", "job payload must be an object")
    return path, payload


def ensure_job_owner(payload: dict[str, Any], *, owner_ref: str, job_ref: str) -> None:
    claim_owner = str(payload.get("claim_owner") or "").strip()
    ensure(claim_owner, "PRECONDITION_FAILED", f"job is missing claim_owner: {job_ref}")
    ensure(claim_owner == owner_ref, "PRECONDITION_FAILED", f"job is owned by a different runner: {job_ref}")


def refresh_job_lease(
    payload: dict[str, Any],
    *,
    job_ref: str,
    owner_ref: str,
    lease_timeout_seconds: int | None = None,
) -> dict[str, Any]:
    status = str(payload.get("status") or "").strip()
    ensure(status in RUNNING_STATUSES, "PRECONDITION_FAILED", f"job is not lease-renewable: {job_ref}")
    ensure_job_owner(payload, owner_ref=owner_ref, job_ref=job_ref)
    ensure_job_lease_active(payload, job_ref=job_ref)
    timeout_seconds = resolve_lease_timeout_seconds(payload, lease_timeout_seconds)
    heartbeat_count = parse_int(payload.get("heartbeat_count", 0) or 0, field_name="heartbeat_count", minimum=0) + 1
    renewed_at = utc_now()
    payload.update(
        {
            "lease_timeout_seconds": timeout_seconds,
            "lease_expires_at": lease_expiry_for_now(timeout_seconds=timeout_seconds),
            "heartbeat_at": renewed_at,
            "lease_renewed_at": renewed_at,
            "heartbeat_count": heartbeat_count,
            "updated_at": renewed_at,
        }
    )
    history = payload.setdefault("state_history", [])
    if not isinstance(history, list):
        payload["state_history"] = history = []
    history.append(
        {
            "status": status,
            "actor_ref": owner_ref,
            "at": renewed_at,
            "note": "runner renewed lease",
        }
    )
    return payload


def _append_history(payload: dict[str, Any], *, status: str, actor_ref: str, note: str | None) -> None:
    history = payload.setdefault("state_history", [])
    if not isinstance(history, list):
        payload["state_history"] = history = []
    history.append(
        {
            "status": status,
            "actor_ref": actor_ref,
            "at": utc_now(),
            "note": note or "",
        }
    )


def update_job(workspace_root: Path, job_ref: str, updates: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    path, payload = load_job_record(workspace_root, job_ref)
    payload.update(updates)
    write_json(path, payload)
    return to_canonical_path(path, workspace_root), payload


def recover_job_to_ready(
    workspace_root: Path,
    job_ref: str,
    *,
    actor_ref: str,
    note: str | None = None,
) -> tuple[str, dict[str, Any]]:
    source_path, payload = load_job_record(workspace_root, job_ref)
    source_status = str(payload.get("status") or "").strip()
    ensure(source_status in RUNNING_STATUSES, "PRECONDITION_FAILED", f"job is not recoverable: {job_ref}")
    ensure(is_job_lease_expired(payload), "PRECONDITION_FAILED", f"job lease is still active: {job_ref}")
    payload["last_recovered_from_status"] = source_status
    payload["last_recovered_owner"] = str(payload.get("claim_owner") or "")
    payload["claim_owner"] = ""
    payload["runner_run_id"] = ""
    payload["claimed_at"] = ""
    payload["started_at"] = ""
    payload["lease_expires_at"] = ""
    payload["heartbeat_at"] = ""
    payload["lease_renewed_at"] = ""
    payload["heartbeat_count"] = 0
    payload["lease_recovered_at"] = utc_now()
    payload["status"] = "ready"
    payload["updated_at"] = utc_now()
    _append_history(payload, status="ready", actor_ref=actor_ref, note=note or "runner recovered expired lease")
    target_path = job_path_for_status(workspace_root, "ready", source_path.name)
    payload["queue_path"] = to_canonical_path(target_path, workspace_root)
    ensure(not target_path.exists(), "PRECONDITION_FAILED", f"target job path already exists: {to_canonical_path(target_path, workspace_root)}")
    ensure_parent(target_path)
    write_json(target_path, payload)
    source_path.unlink()
    return to_canonical_path(target_path, workspace_root), payload


def transition_job(
    workspace_root: Path,
    job_ref: str,
    target_status: str,
    *,
    actor_ref: str,
    note: str | None = None,
    updates: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    source_path, payload = load_job_record(workspace_root, job_ref)
    source_status = str(payload.get("status") or "").strip()
    allowed_targets = ALLOWED_TRANSITIONS.get(source_status, set())
    ensure(
        target_status in allowed_targets,
        "PRECONDITION_FAILED",
        f"invalid job transition: {source_status or '<unknown>'} -> {target_status}",
    )
    payload.update(updates or {})
    payload["status"] = target_status
    payload["updated_at"] = utc_now()
    _append_history(payload, status=target_status, actor_ref=actor_ref, note=note)
    target_path = job_path_for_status(workspace_root, target_status, source_path.name)
    payload["queue_path"] = to_canonical_path(target_path, workspace_root)
    if target_path.resolve() == source_path.resolve():
        write_json(target_path, payload)
        return to_canonical_path(target_path, workspace_root), payload

    ensure(not target_path.exists(), "PRECONDITION_FAILED", f"target job path already exists: {to_canonical_path(target_path, workspace_root)}")
    ensure_parent(target_path)
    write_json(target_path, payload)
    source_path.unlink()
    return to_canonical_path(target_path, workspace_root), payload
