"""Governed read/write gateway."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError
from cli.lib.fs import canonical_to_path, read_text, to_canonical_path, write_json, write_text
from cli.lib.policy import policy_verdict
from cli.lib.registry_store import bind_record, resolve_content_ref, verify_eligibility


def governed_write(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    artifact_ref: str,
    workspace_path: str,
    requested_mode: str,
    content_ref: str | None = None,
    content: str | None = None,
    overwrite: bool = False,
    registry_prerequisite_ref: str | None = None,
) -> dict[str, str]:
    target_path = canonical_to_path(workspace_path, workspace_root)
    verdict = policy_verdict(target_path, requested_mode, workspace_root)
    if target_path.exists() and not overwrite and requested_mode in {"write", "create", "replace"}:
        raise CommandError("PRECONDITION_FAILED", "write target exists and overwrite is false")
    if registry_prerequisite_ref:
        verify_eligibility(workspace_root, registry_prerequisite_ref)
    text = str(content or "")
    if content_ref:
        text = resolve_content_ref(workspace_root, content_ref)
    mode = "a" if requested_mode == "append-run-log" else "w"
    write_text(target_path, text, mode=mode)
    receipt_ref = f"artifacts/active/receipts/{requested_mode}-{request_id}.json"
    write_json(
        workspace_root / receipt_ref,
        {
            "request_id": request_id,
            "artifact_ref": artifact_ref,
            "target_path": to_canonical_path(target_path, workspace_root),
            "policy_verdict": verdict,
            "trace": trace,
        },
    )
    status = "promoted" if requested_mode == "promote" else "committed" if requested_mode == "commit" else "candidate"
    record, record_ref = bind_record(
        workspace_root,
        artifact_ref,
        to_canonical_path(target_path, workspace_root),
        status,
        trace,
        metadata={"requested_mode": requested_mode, "layer": "formal" if status in {"promoted", "committed"} else "candidate"},
        lineage=[registry_prerequisite_ref] if registry_prerequisite_ref else [],
    )
    return {
        "canonical_path": verdict["canonical_path"],
        "receipt_ref": receipt_ref,
        "registry_record_ref": record_ref,
        "managed_artifact_ref": record["managed_artifact_ref"],
        "policy_verdict": "allow",
    }


def governed_read(
    workspace_root: Path,
    artifact_ref: str,
    workspace_path: str,
    lineage_expectation: str | None = None,
) -> dict[str, str]:
    target_path = canonical_to_path(workspace_path, workspace_root)
    verdict = policy_verdict(target_path, "read", workspace_root)
    record = verify_eligibility(workspace_root, artifact_ref, lineage_expectation)
    content = read_text(canonical_to_path(record["managed_artifact_ref"], workspace_root))
    return {
        "canonical_path": verdict["canonical_path"],
        "registry_record_ref": "",
        "managed_artifact_ref": record["managed_artifact_ref"],
        "content": content,
        "policy_verdict": "allow",
    }
