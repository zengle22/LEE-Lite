"""Artifact operations for the governed mainline runtime."""

from __future__ import annotations

from argparse import Namespace
from cli.lib.managed_gateway import commit_governed
from cli.lib.protocol import CommandContext, run_with_protocol


def _artifact_handler(ctx: CommandContext):
    result = commit_governed(ctx.workspace_root, ctx.payload, ctx.trace, ctx.action, ctx.request["request_id"])
    evidence_refs = [ref for ref in (result.get("receipt_ref"), result.get("registry_record_ref")) if ref]
    return "OK", f"artifact {ctx.action} completed", result, [], evidence_refs


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _artifact_handler)
