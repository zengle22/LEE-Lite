"""Observability helpers for runner-managed jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lib.fs import canonical_to_path, write_json
from cli.lib.job_queue import list_jobs, recover_expired_jobs
from cli.lib.job_state import is_job_lease_expired

MONITORED_STATUSES = ("ready", "running", "failed", "waiting-human", "deadletter")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso_now() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _job_timestamp(payload: dict[str, Any]) -> datetime | None:
    for field in (
        "created_at",
        "updated_at",
        "started_at",
        "claimed_at",
        "failed_at",
        "completed_at",
        "requeued_at",
    ):
        parsed = _parse_timestamp(payload.get(field))
        if parsed is not None:
            return parsed
    return None


def _job_view(item: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    payload = item["payload"]
    recorded_at = _job_timestamp(payload)
    age_seconds = max(0, int((now - recorded_at).total_seconds())) if recorded_at else None
    retry_count = int(payload.get("retry_count", 0) or 0)
    retry_budget = int(payload.get("retry_budget", 0) or 0)
    return {
        "job_ref": item["job_ref"],
        "job_id": item["job_id"],
        "status": item["status"],
        "target_skill": item["target_skill"],
        "created_at": payload.get("created_at", ""),
        "updated_at": payload.get("updated_at", ""),
        "claim_owner": payload.get("claim_owner", ""),
        "lease_expires_at": payload.get("lease_expires_at", ""),
        "failure_reason": payload.get("failure_reason", ""),
        "retry_count": retry_count,
        "retry_budget": retry_budget,
        "age_seconds": age_seconds,
        "authoritative_input_ref": payload.get("authoritative_input_ref", ""),
        "last_outcome_ref": payload.get("last_outcome_ref", ""),
    }


def _summarize_statuses(job_views: list[dict[str, Any]]) -> dict[str, Any]:
    status_summary: dict[str, Any] = {}
    oldest_visible_age = None
    oldest_visible_job_ref = ""
    for status in MONITORED_STATUSES:
        members = [job for job in job_views if job["status"] == status]
        age_candidates = [job["age_seconds"] for job in members if job["age_seconds"] is not None]
        oldest_age = max(age_candidates) if age_candidates else None
        oldest_job_ref = ""
        if oldest_age is not None:
            oldest_job_ref = next(job["job_ref"] for job in members if job["age_seconds"] == oldest_age)
            if oldest_visible_age is None or oldest_age > oldest_visible_age:
                oldest_visible_age = oldest_age
                oldest_visible_job_ref = oldest_job_ref
        status_summary[status] = {
            "count": len(members),
            "oldest_age_seconds": oldest_age,
            "oldest_job_ref": oldest_job_ref,
        }
    return {
        "statuses": status_summary,
        "total_visible_jobs": sum(status_summary[status]["count"] for status in MONITORED_STATUSES),
        "oldest_visible_age_seconds": oldest_visible_age,
        "oldest_visible_job_ref": oldest_visible_job_ref,
    }


def _summarize_target_skills(job_views: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for job in job_views:
        grouped.setdefault(job["target_skill"] or "<unassigned>", []).append(job)

    summaries: list[dict[str, Any]] = []
    for target_skill, members in grouped.items():
        counts = {status: 0 for status in MONITORED_STATUSES}
        for job in members:
            if job["status"] in counts:
                counts[job["status"]] += 1
        age_candidates = [job["age_seconds"] for job in members if job["age_seconds"] is not None]
        summaries.append(
            {
                "target_skill": target_skill,
                "total_jobs": len(members),
                "counts": counts,
                "oldest_age_seconds": max(age_candidates) if age_candidates else None,
                "job_refs": [job["job_ref"] for job in members],
            }
        )
    return sorted(summaries, key=lambda item: (-item["total_jobs"], item["target_skill"]))


def _recoverable_queue_summary(job_views: list[dict[str, Any]], *, status_filter: str | None) -> dict[str, Any]:
    ready_jobs = [job for job in job_views if job["status"] == "ready"]
    retryable_failed = [
        job
        for job in job_views
        if job["status"] == "failed" and int(job.get("retry_count", 0)) < int(job.get("retry_budget", 0))
    ]
    waiting_human = [job for job in job_views if job["status"] == "waiting-human"]
    deadletters = [job for job in job_views if job["status"] == "deadletter"]
    running = [job for job in job_views if job["status"] == "running"]
    recoverable_jobs = ready_jobs + retryable_failed + waiting_human
    age_candidates = [job["age_seconds"] for job in recoverable_jobs if job["age_seconds"] is not None]

    suggested_actions: list[dict[str, Any]] = []
    if ready_jobs:
        suggested_actions.append({"action": "drain-ready-queue", "count": len(ready_jobs)})
    if retryable_failed:
        suggested_actions.append({"action": "review-retryable-failures", "count": len(retryable_failed)})
    if waiting_human:
        suggested_actions.append({"action": "review-waiting-human", "count": len(waiting_human)})
    if deadletters:
        suggested_actions.append({"action": "inspect-deadletters", "count": len(deadletters)})
    if running:
        suggested_actions.append({"action": "observe-running-jobs", "count": len(running)})

    focus = status_filter or "all"
    return {
        "focus": focus,
        "recoverable_count": len(recoverable_jobs),
        "ready_count": len(ready_jobs),
        "retryable_failed_count": len(retryable_failed),
        "waiting_human_count": len(waiting_human),
        "deadletter_count": len(deadletters),
        "running_count": len(running),
        "oldest_recoverable_age_seconds": max(age_candidates) if age_candidates else None,
        "suggested_actions": suggested_actions,
    }


def _recovery_scan_summary(job_views: list[dict[str, Any]], *, now: datetime) -> dict[str, Any]:
    expired_running = [
        job
        for job in job_views
        if job["status"] in {"claimed", "running"}
        and is_job_lease_expired(
            {
                "status": job["status"],
                "lease_expires_at": job.get("lease_expires_at") or "",
            }
        )
    ]
    age_candidates = [job["age_seconds"] for job in expired_running if job["age_seconds"] is not None]
    return {
        "expired_running_count": len(expired_running),
        "expired_running_job_refs": [job["job_ref"] for job in expired_running],
        "expired_running_job_ids": [job["job_id"] for job in expired_running],
        "oldest_expired_running_age_seconds": max(age_candidates) if age_candidates else None,
        "scanned_at": now.isoformat().replace("+00:00", "Z"),
    }


def _counts(job_views: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for job in job_views:
        counts[job["status"]] = counts.get(job["status"], 0) + 1
    return counts


def _focus_job_views(job_views: list[dict[str, Any]], status_filter: str | None) -> list[dict[str, Any]]:
    if not status_filter:
        return job_views
    return [job for job in job_views if job["status"] == status_filter]


def _dedupe_jobs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        unique[item["job_ref"]] = item
    return list(unique.values())


def _collect_job_views(workspace_root: Path) -> tuple[datetime, list[dict[str, Any]], list[dict[str, Any]]]:
    now = _utc_now()
    all_jobs = _dedupe_jobs(list_jobs(workspace_root))
    all_job_views = [_job_view(item, now=now) for item in all_jobs]
    return now, all_jobs, all_job_views


def _snapshot_payload(
    job_views: list[dict[str, Any]],
    *,
    status_filter: str | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    focus_jobs = _focus_job_views(job_views, status_filter)
    return {
        "generated_at": generated_at or _iso_now(),
        "status_filter": status_filter or "all",
        "counts": _counts(job_views),
        "focus_count": len(focus_jobs),
        "queue_summary": _summarize_statuses(job_views),
        "target_skill_summary": _summarize_target_skills(job_views),
        "recoverable_queue_summary": _recoverable_queue_summary(job_views, status_filter=status_filter),
        "jobs": focus_jobs,
    }


def write_status_snapshot(workspace_root: Path, *, name: str, status_filter: str | None = None) -> dict[str, Any]:
    _, _, all_job_views = _collect_job_views(workspace_root)
    snapshot_ref = f"artifacts/active/runner/{name}.json"
    snapshot_payload = _snapshot_payload(all_job_views, status_filter=status_filter)
    write_json(canonical_to_path(snapshot_ref, workspace_root), snapshot_payload)
    return {
        "canonical_path": snapshot_ref,
        "snapshot_ref": snapshot_ref,
        "generated_at": snapshot_payload["generated_at"],
        "status_filter": snapshot_payload["status_filter"],
        "counts": snapshot_payload["counts"],
        "focus_count": snapshot_payload["focus_count"],
        "queue_summary": snapshot_payload["queue_summary"],
        "target_skill_summary": snapshot_payload["target_skill_summary"],
        "recoverable_queue_summary": snapshot_payload["recoverable_queue_summary"],
        "jobs": snapshot_payload["jobs"],
    }


def write_recovery_snapshot(
    workspace_root: Path,
    *,
    name: str,
    actor_ref: str,
    recovery_action: str,
    status_filter: str | None = None,
) -> dict[str, Any]:
    recovery_action = recovery_action.strip().lower()
    if recovery_action not in {"scan", "repair"}:
        from cli.lib.errors import ensure

        ensure(False, "INVALID_REQUEST", f"unsupported recovery_action: {recovery_action}")

    before_now, _, before_job_views = _collect_job_views(workspace_root)
    recovery_scan_summary = _recovery_scan_summary(before_job_views, now=before_now)
    recovered_jobs: list[dict[str, Any]] = []
    if recovery_action == "repair":
        recovered_jobs = recover_expired_jobs(workspace_root, actor_ref=actor_ref)
    _, _, after_job_views = _collect_job_views(workspace_root)
    snapshot_ref = f"artifacts/active/runner/{name}.json"
    snapshot_payload: dict[str, Any] = {
        "generated_at": _iso_now(),
        "recovery_action": recovery_action,
        "recovery_scan_summary": recovery_scan_summary,
        "recovery_repair_summary": {
            "repaired_count": len(recovered_jobs),
            "recovered_jobs": recovered_jobs,
        },
        **_snapshot_payload(after_job_views, status_filter=status_filter),
    }
    write_json(canonical_to_path(snapshot_ref, workspace_root), snapshot_payload)
    return {
        "canonical_path": snapshot_ref,
        "snapshot_ref": snapshot_ref,
        "generated_at": snapshot_payload["generated_at"],
        "recovery_action": snapshot_payload["recovery_action"],
        "recovery_scan_summary": snapshot_payload["recovery_scan_summary"],
        "recovery_repair_summary": snapshot_payload["recovery_repair_summary"],
        "status_filter": snapshot_payload["status_filter"],
        "counts": snapshot_payload["counts"],
        "focus_count": snapshot_payload["focus_count"],
        "queue_summary": snapshot_payload["queue_summary"],
        "target_skill_summary": snapshot_payload["target_skill_summary"],
        "recoverable_queue_summary": snapshot_payload["recoverable_queue_summary"],
        "jobs": snapshot_payload["jobs"],
    }
