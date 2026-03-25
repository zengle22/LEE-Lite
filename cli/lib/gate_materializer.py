"""Materialized handoff and job creation helpers."""

from __future__ import annotations

from pathlib import Path

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json
from cli.lib.registry_store import slugify


def _artifact_slug(trace: dict[str, object], request_id: str) -> str:
    return slugify(f"{trace.get('run_ref', 'run')}-{request_id}")


def materialize_handoff(
    workspace_root: Path,
    decision_ref: str,
    trace: dict[str, object],
    request_id: str,
) -> dict[str, str]:
    decision = load_json(canonical_to_path(decision_ref, workspace_root))
    ensure(decision.get("decision_type") == "approve", "PRECONDITION_FAILED", "only approve can materialize")
    slug = _artifact_slug(trace, request_id)
    handoff_path = workspace_root / "artifacts" / "active" / "handoffs" / f"materialized-handoff-{slug}.json"
    write_json(
        handoff_path,
        {"trace": trace, "gate_decision_ref": decision_ref, "handoff_type": "downstream", "request_id": request_id},
    )
    return {"materialized_handoff_ref": to_canonical_path(handoff_path, workspace_root)}


def dispatch_materialized_job(
    workspace_root: Path,
    decision_ref: str,
    trace: dict[str, object],
    request_id: str,
) -> dict[str, str]:
    decision = load_json(canonical_to_path(decision_ref, workspace_root))
    ensure(decision.get("decision_type") == "approve", "PRECONDITION_FAILED", "only approve can dispatch")
    slug = _artifact_slug(trace, request_id)
    job_path = workspace_root / "artifacts" / "jobs" / "ready" / f"materialized-job-{slug}.json"
    write_json(
        job_path,
        {"trace": trace, "gate_decision_ref": decision_ref, "job_type": "next-execution", "request_id": request_id},
    )
    return {"materialized_job_ref": to_canonical_path(job_path, workspace_root)}
