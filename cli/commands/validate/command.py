"""Generic request and response validation."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.protocol import CommandContext, run_with_protocol


def _validate_handler(ctx: CommandContext):
    if ctx.action == "request":
        for field in ("api_version", "command", "request_id", "workspace_root", "actor_ref", "trace", "payload"):
            ensure(field in ctx.request, "INVALID_REQUEST", f"missing field: {field}")
        return "OK", "request validation passed", {
            "canonical_path": ctx.request_path.as_posix(),
            "validated_object_ref": ctx.request_path.as_posix(),
        }, [], []
    data = ctx.payload.get("response", {})
    for field in ("api_version", "command", "request_id", "result_status", "status_code", "exit_code", "message", "data"):
        ensure(field in data, "INVALID_REQUEST", f"missing response field: {field}")
    return "OK", "response validation passed", {
        "canonical_path": ctx.request_path.as_posix(),
        "validated_object_ref": ctx.request_path.as_posix(),
    }, [], []


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _validate_handler)

