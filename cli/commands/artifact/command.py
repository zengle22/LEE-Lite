"""Artifact operations for the governed mainline runtime."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, read_text, to_canonical_path, write_json, write_text
from cli.lib.policy import policy_verdict
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.registry_store import bind_record, record_path, resolve_content_ref, verify_eligibility


def _receipt_path(ctx: CommandContext, action: str) -> Path:
    request_id = ctx.request["request_id"]
    return ctx.workspace_root / "artifacts" / "active" / "receipts" / f"{action}-{request_id}.json"


def _write_receipt(ctx: CommandContext, action: str, artifact_ref: str, target_path: Path, verdict: dict[str, str]) -> str:
    receipt_path = _receipt_path(ctx, action)
    payload = {
        "request_id": ctx.request["request_id"],
        "action": action,
        "artifact_ref": artifact_ref,
        "target_path": to_canonical_path(target_path, ctx.workspace_root),
        "policy_verdict": verdict,
        "trace": ctx.trace,
    }
    write_json(receipt_path, payload)
    return to_canonical_path(receipt_path, ctx.workspace_root)


def _write_target(ctx: CommandContext, target_path: Path, content: str, append: bool = False) -> None:
    if append:
        write_text(target_path, content, mode="a")
    else:
        write_text(target_path, content, mode="w")


def _artifact_handler(ctx: CommandContext):
    operation = ctx.action
    payload = ctx.payload
    artifact_ref = str(payload.get("artifact_ref", ""))
    target_path = canonical_to_path(str(payload.get("workspace_path", "")), ctx.workspace_root)
    ensure(artifact_ref, "INVALID_REQUEST", "artifact_ref is required")
    ensure(str(payload.get("workspace_path", "")), "INVALID_REQUEST", "workspace_path is required")
    verdict = policy_verdict(target_path, "read" if operation == "read" else operation, ctx.workspace_root)

    if operation == "read":
        record = verify_eligibility(ctx.workspace_root, artifact_ref, payload.get("lineage_expectation"))
        content = read_text(canonical_to_path(record["managed_artifact_ref"], ctx.workspace_root))
        return "OK", "managed artifact read completed", {
            "canonical_path": verdict["canonical_path"],
            "policy_verdict": "allow",
            "registry_record_ref": to_canonical_path(record_path(ctx.workspace_root, artifact_ref), ctx.workspace_root),
            "managed_artifact_ref": record["managed_artifact_ref"],
            "content": content,
        }, [], []

    if operation == "promote":
        staging_ref = payload.get("staging_ref")
        ensure(bool(staging_ref), "PRECONDITION_FAILED", "promote requires staging_ref")
        content = resolve_content_ref(ctx.workspace_root, str(staging_ref))
        status = "promoted"
        lineage = [str(staging_ref)]
    else:
        content_ref = payload.get("content_ref")
        if operation == "append-run-log":
            content = payload.get("content", "")
            if content_ref:
                content = resolve_content_ref(ctx.workspace_root, str(content_ref))
            content = str(content)
        else:
            ensure(bool(content_ref), "PRECONDITION_FAILED", f"{operation} requires content_ref")
            content = resolve_content_ref(ctx.workspace_root, str(content_ref))
        status = "committed" if operation == "commit" else "candidate"
        lineage = []

    _write_target(ctx, target_path, content, append=operation == "append-run-log")
    receipt_ref = _write_receipt(ctx, operation, artifact_ref, target_path, verdict)
    record, record_ref = bind_record(
        ctx.workspace_root,
        artifact_ref,
        verdict["canonical_path"],
        status,
        ctx.trace,
        metadata={"requested_mode": payload.get("requested_mode", operation)},
        lineage=lineage,
    )
    return "OK", f"artifact {operation} completed", {
        "canonical_path": verdict["canonical_path"],
        "policy_verdict": "allow",
        "receipt_ref": receipt_ref,
        "registry_record_ref": record_ref,
        "managed_artifact_ref": record["managed_artifact_ref"],
    }, [], [receipt_ref, record_ref]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _artifact_handler)
