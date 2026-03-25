"""Artifact operations for the governed mainline runtime."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.managed_gateway import governed_read, governed_write
from cli.lib.protocol import CommandContext, run_with_protocol


def _artifact_handler(ctx: CommandContext):
    operation = ctx.action
    payload = ctx.payload
    artifact_ref = str(payload.get("artifact_ref", ""))
    ensure(artifact_ref, "INVALID_REQUEST", "artifact_ref is required")
    ensure(str(payload.get("workspace_path", "")), "INVALID_REQUEST", "workspace_path is required")

    if operation == "read":
        result = governed_read(
            ctx.workspace_root,
            artifact_ref=artifact_ref,
            workspace_path=str(payload.get("workspace_path", "")),
            lineage_expectation=payload.get("lineage_expectation"),
        )
        return "OK", "managed artifact read completed", result, [], []

    result = governed_write(
        ctx.workspace_root,
        trace=ctx.trace,
        request_id=ctx.request["request_id"],
        artifact_ref=artifact_ref,
        workspace_path=str(payload.get("workspace_path", "")),
        requested_mode=operation,
        content_ref=str(payload["content_ref"]) if payload.get("content_ref") else None,
        content=str(payload["content"]) if payload.get("content") is not None else None,
        overwrite=bool(payload.get("overwrite", False)),
        registry_prerequisite_ref=str(payload["registry_prerequisite_ref"]) if payload.get("registry_prerequisite_ref") else None,
    )
    return "OK", f"artifact {operation} completed", result, [], [result["receipt_ref"], result["registry_record_ref"]]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _artifact_handler)
