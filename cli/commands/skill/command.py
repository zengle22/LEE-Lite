"""Governed skill producer commands."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.failure_capture_skill import run_failure_capture
from cli.lib.gate_human_orchestrator_skill import run_gate_human_orchestrator
from cli.lib.impl_spec_test_runtime import execute_impl_spec_test_skill
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.spec_reconcile_skill import run_spec_reconcile
from cli.lib.test_exec_runtime import execute_test_exec_skill


def _skill_handler(ctx: CommandContext):
    ensure(
        ctx.action in {"impl-spec-test", "test-exec-web-e2e", "test-exec-cli", "gate-human-orchestrator", "failure-capture", "spec-reconcile"},
        "INVALID_REQUEST",
        "unsupported skill action",
    )
    if ctx.action == "spec-reconcile":
        result = run_spec_reconcile(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            request_id=ctx.request["request_id"],
            payload=ctx.payload,
        )
        evidence_refs = _collect_refs(result)
        return "OK", "spec reconcile report emitted", {
            "canonical_path": result["canonical_path"],
            **result,
        }, [], evidence_refs
    if ctx.action == "failure-capture":
        result = run_failure_capture(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            request_id=ctx.request["request_id"],
            payload=ctx.payload,
        )
        evidence_refs = _collect_refs(result)
        return "OK", "governed failure capture package emitted", {
            "canonical_path": result["canonical_path"],
            **result,
        }, [], evidence_refs
    if ctx.action == "gate-human-orchestrator":
        result = run_gate_human_orchestrator(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            payload=ctx.payload,
        )
        evidence_refs = _collect_refs(result)
        message = "governed gate human orchestrator completed"
        if result.get("human_brief_markdown"):
            message = "governed gate human orchestrator prepared a pending human brief"
        return "OK", message, {
            "canonical_path": result["canonical_path"],
            **result,
        }, [], evidence_refs
    payload = ctx.payload
    if ctx.action == "impl-spec-test":
        for field in ("impl_ref", "impl_package_ref", "feat_ref", "tech_ref"):
            ensure(field in payload, "INVALID_REQUEST", f"missing skill field: {field}")
        result = execute_impl_spec_test_skill(
            workspace_root=ctx.workspace_root,
            trace=ctx.trace,
            request_id=ctx.request["request_id"],
            payload=payload,
        )
        excluded = {"skill_ref", "runner_skill_ref", "trace_ref"}
        evidence_refs = [value for key, value in result.items() if key.endswith("_ref") and key not in excluded]
        return "OK", "governed impl spec test candidate emitted", {
            "canonical_path": result["handoff_ref"],
            **result,
        }, [], evidence_refs
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


def _collect_refs(payload: dict[str, object]) -> list[str]:
    excluded = {"skill_ref", "runner_skill_ref"}
    refs: list[str] = []
    for key, value in payload.items():
        if key.endswith("_ref") and key not in excluded and isinstance(value, str) and value.strip():
            refs.append(value)
        elif key == "items" and isinstance(value, list):
            for item in value:
                if not isinstance(item, dict):
                    continue
                for nested_key, nested_value in item.items():
                    if nested_key.endswith("_ref") and nested_key not in excluded and isinstance(nested_value, str) and nested_value.strip():
                        refs.append(nested_value)
    return list(dict.fromkeys(refs))


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _skill_handler)
