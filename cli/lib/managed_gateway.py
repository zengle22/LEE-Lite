"""Managed read/write adapter for governed artifact IO."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, read_text, to_canonical_path, write_json, write_text
from cli.lib.policy import policy_verdict
from cli.lib.registry_store import bind_record, record_path, resolve_content_ref, verify_eligibility


def _receipt_path(workspace_root: Path, action: str, request_id: str) -> Path:
    return workspace_root / "artifacts" / "active" / "receipts" / f"{action}-{request_id}.json"


def _resolve_content(workspace_root: Path, payload: dict[str, Any], action: str) -> tuple[str, list[str]]:
    lineage = [str(item) for item in payload.get("lineage", []) if str(item)]
    if action == "promote":
        staging_ref = str(payload.get("staging_ref", ""))
        ensure(bool(staging_ref), "PRECONDITION_FAILED", "promote requires staging_ref")
        return resolve_content_ref(workspace_root, staging_ref), lineage + [staging_ref]
    if action == "append-run-log":
        if payload.get("content_ref"):
            return resolve_content_ref(workspace_root, str(payload["content_ref"])), lineage
        return str(payload.get("content", "")), lineage
    content_ref = str(payload.get("content_ref", ""))
    ensure(bool(content_ref), "PRECONDITION_FAILED", f"{action} requires content_ref")
    return resolve_content_ref(workspace_root, content_ref), lineage


def commit_governed(
    workspace_root: Path,
    payload: dict[str, Any],
    trace: dict[str, Any],
    action: str,
    request_id: str,
) -> dict[str, Any]:
    artifact_ref = str(payload.get("artifact_ref", ""))
    workspace_path = str(payload.get("workspace_path", ""))
    ensure(artifact_ref, "INVALID_REQUEST", "artifact_ref is required")
    ensure(workspace_path, "INVALID_REQUEST", "workspace_path is required")
    target_path = canonical_to_path(workspace_path, workspace_root)
    requested_mode = _policy_mode(action)
    verdict = policy_verdict(target_path, requested_mode, workspace_root)
    if action in {"read", "read-governed"}:
        record = verify_eligibility(workspace_root, artifact_ref, payload.get("lineage_expectation"))
        content = read_text(canonical_to_path(record["managed_artifact_ref"], workspace_root))
        return {
            "canonical_path": verdict["canonical_path"],
            "policy_verdict": "allow",
            "registry_record_ref": to_canonical_path(record_path(workspace_root, artifact_ref), workspace_root),
            "managed_artifact_ref": record["managed_artifact_ref"],
            "content": content,
        }
    content, lineage = _resolve_content(workspace_root, payload, action)
    write_text(target_path, content, mode="a" if action == "append-run-log" else "w")
    receipt_path = _receipt_path(workspace_root, action, request_id)
    write_json(receipt_path, {"request_id": request_id, "action": action, "artifact_ref": artifact_ref, "trace": trace, "policy_verdict": verdict})
    status = str(payload.get("status_override") or ("materialized" if action == "publish-formal" else "promoted" if action == "promote" else "committed" if action in {"commit", "commit-governed"} else "candidate"))
    metadata = payload.get("metadata", {})
    record, record_ref = bind_record(workspace_root, artifact_ref, verdict["canonical_path"], status, trace, metadata=metadata, lineage=lineage)
    return {
        "canonical_path": verdict["canonical_path"],
        "policy_verdict": "allow",
        "receipt_ref": to_canonical_path(receipt_path, workspace_root),
        "registry_record_ref": record_ref,
        "managed_artifact_ref": record["managed_artifact_ref"],
        "write_status": status,
    }


def _policy_mode(action: str) -> str:
    if action in {"read", "read-governed"}:
        return "read"
    if action in {"commit-governed", "publish-formal"}:
        return "commit"
    return action
