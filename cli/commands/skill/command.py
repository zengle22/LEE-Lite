"""Governed skill producer commands."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.test_exec_runtime import execute_test_exec_skill


def _skill_handler(ctx: CommandContext):
    ensure(ctx.action in {"test-exec-web-e2e", "test-exec-cli"}, "INVALID_REQUEST", "unsupported skill action")
    payload = ctx.payload
    for field in ("test_set_ref", "test_environment_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing skill field: {field}")
    result = execute_test_exec_skill(
        workspace_root=ctx.workspace_root,
        trace=ctx.trace,
        action=ctx.action,
        request_id=ctx.request["request_id"],
        payload=payload,
    )
    evidence_refs = [
        result["candidate_receipt_ref"],
        result["candidate_registry_record_ref"],
        result["handoff_ref"],
        result["gate_pending_ref"],
    ]
    return "OK", "governed skill candidate emitted", {
        "canonical_path": result["handoff_ref"],
        **result,
    }, [], evidence_refs


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _skill_handler)
