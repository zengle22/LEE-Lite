"""Governed skill producer commands."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.gate_human_orchestrator_skill import run_gate_human_orchestrator
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.test_exec_runtime import execute_test_exec_skill


def _skill_handler(ctx: CommandContext):
    ensure(ctx.action in {"test-exec-web-e2e", "test-exec-cli", "gate-human-orchestrator"}, "INVALID_REQUEST", "unsupported skill action")
    if ctx.action == "gate-human-orchestrator":
        result = run_gate_human_orchestrator(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            payload=ctx.payload,
        )
        evidence_refs = [result["bundle_ref"]]
        return "OK", "governed gate human orchestrator completed", {
            "canonical_path": result["bundle_ref"],
            **result,
        }, [], evidence_refs
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
    excluded = {"skill_ref", "runner_skill_ref", "trace_ref"}
    evidence_refs = [value for key, value in result.items() if key.endswith("_ref") and key not in excluded]
    return "OK", "governed skill candidate emitted", {
        "canonical_path": result["handoff_ref"],
        **result,
    }, [], evidence_refs


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _skill_handler)
