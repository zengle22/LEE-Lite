"""Gate package, decision, materialization, dispatch, and run closure."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json
from cli.lib.formalization import materialize_formal
from cli.lib.mainline_runtime import consume_decision_return, list_pending_handoffs, submit_handoff
from cli.lib.protocol import CommandContext, run_with_protocol


def _artifact_path(ctx: CommandContext, relative: str):
    return ctx.workspace_root / relative


def _decision_type(findings: list[dict[str, object]]) -> str:
    blocker_count = sum(1 for item in findings if item.get("severity") == "blocker")
    return "revise" if blocker_count else "approve"


def _submit_handoff_action(ctx: CommandContext):
    payload = ctx.payload
    for field in ("producer_ref", "proposal_ref", "payload_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing handoff field: {field}")
    result = submit_handoff(
        ctx.workspace_root,
        trace=ctx.trace,
        producer_ref=str(payload["producer_ref"]),
        proposal_ref=str(payload["proposal_ref"]),
        payload_ref=str(payload["payload_ref"]),
        pending_state=str(payload.get("pending_state", "gate_pending")),
        trace_context_ref=str(payload["trace_context_ref"]) if payload.get("trace_context_ref") else None,
    )
    return "OK", "authoritative handoff submitted", {"canonical_path": result["handoff_ref"], **result}, [], [
        result["handoff_ref"],
        result["gate_pending_ref"],
    ]


def _show_pending_action(ctx: CommandContext):
    result = list_pending_handoffs(ctx.workspace_root)
    return "OK", "pending handoffs listed", {
        "canonical_path": result["pending_ref"],
        "pending_ref": result["pending_ref"],
        "pending_items": result["items"],
        "pending_count": result["count"],
    }, [], [result["pending_ref"]]


def _decide_action(ctx: CommandContext):
    payload = ctx.payload
    for field in ("handoff_ref", "proposal_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing decide field: {field}")
    findings = []
    for ref in payload.get("audit_finding_refs", []):
        finding_path = canonical_to_path(str(ref), ctx.workspace_root)
        if finding_path.exists():
            findings.extend(load_json(finding_path).get("findings", []))
    decision_type = str(payload.get("decision") or _decision_type(findings))
    decision_ref = f"artifacts/active/gates/decisions/{Path(str(payload['handoff_ref'])).stem}-decision.json"
    decision = {
        "trace": ctx.trace,
        "proposal_ref": payload["proposal_ref"],
        "handoff_ref": payload["handoff_ref"],
        "decision_type": decision_type,
        "routing_hint": str(payload.get("routing_hint", "formalization" if decision_type in {"approve", "handoff"} else "producer_reentry")),
        "materialization_required": bool(payload.get("materialization_required", decision_type in {"approve", "handoff"})),
        "reentry_allowed": decision_type in {"revise", "retry"},
        "decision_reason": str(payload.get("decision_reason", "derived from audit findings and target constraints")),
    }
    write_json(_artifact_path(ctx, decision_ref), decision)
    routing = consume_decision_return(
        ctx.workspace_root,
        trace=ctx.trace,
        handoff_ref=str(payload["handoff_ref"]),
        decision_ref=decision_ref,
        decision=decision_type,
        routing_hint=decision["routing_hint"],
    )
    evidence_refs = [decision_ref] + [value for value in routing.values() if value]
    return "OK", "gate decision produced", {"canonical_path": decision_ref, "gate_decision_ref": decision_ref, **routing}, [], evidence_refs


def _package_action(ctx: CommandContext):
    payload = ctx.payload
    for field in ("candidate_ref", "acceptance_ref", "evidence_bundle_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing gate package field: {field}")
    package_ref = "artifacts/active/gates/packages/gate-ready-package.json"
    if ctx.action == "create":
        write_json(_artifact_path(ctx, package_ref), {"trace": ctx.trace, "payload": payload})
    return "OK", f"gate package {ctx.action} completed", {
        "canonical_path": package_ref,
        "gate_ready_package_ref": package_ref,
        "completeness_result": "complete",
        "validation_summary": {"required_fields_present": True},
    }, [], [package_ref]


def _evaluate_action(ctx: CommandContext):
    payload = ctx.payload
    for field in ("gate_ready_package_ref", "audit_finding_refs", "target_matrix"):
        ensure(field in payload, "INVALID_REQUEST", f"missing gate evaluate field: {field}")
    if payload.get("guard_required") and not payload.get("guarded_enablement_ref"):
        raise CommandError("PROVISIONAL_SLICE_DISABLED", "guarded slice is not enabled")
    findings = []
    for ref in payload.get("audit_finding_refs", []):
        finding_path = canonical_to_path(str(ref), ctx.workspace_root)
        if finding_path.exists():
            findings.extend(load_json(finding_path).get("findings", []))
    decision_ref = "artifacts/active/gates/decisions/gate-decision.json"
    write_json(
        _artifact_path(ctx, decision_ref),
        {
            "trace": ctx.trace,
            "decision_type": _decision_type(findings),
            "target_matrix": payload["target_matrix"],
            "rationale": "derived from audit findings and target constraints",
        },
    )
    return "OK", "gate decision produced", {
        "canonical_path": decision_ref,
        "gate_decision_ref": decision_ref,
        "enablement_scope": "guarded-only" if payload.get("guarded_enablement_ref") else "core",
    }, [], [decision_ref]


def _materialize_action(ctx: CommandContext):
    payload = ctx.payload
    decision_ref = str(payload.get("gate_decision_ref", ""))
    ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref is required")
    decision = load_json(canonical_to_path(decision_ref, ctx.workspace_root))
    ensure(decision.get("decision_type") == "approve", "PRECONDITION_FAILED", "only approve can materialize")
    candidate_ref = str(payload.get("candidate_ref", decision.get("candidate_ref", payload.get("artifact_ref", ""))))
    ensure(candidate_ref, "INVALID_REQUEST", "candidate_ref is required for materialize")
    result = materialize_formal(
        ctx.workspace_root,
        trace=ctx.trace,
        candidate_ref=candidate_ref,
        decision_ref=decision_ref,
        target_formal_kind=str(payload.get("target_formal_kind", "handoff")),
        formal_artifact_ref=str(payload["formal_artifact_ref"]) if payload.get("formal_artifact_ref") else None,
    )
    handoff_ref = "artifacts/active/handoffs/materialized-handoff.json"
    write_json(
        _artifact_path(ctx, handoff_ref),
        {
            "trace": ctx.trace,
            "gate_decision_ref": decision_ref,
            "handoff_type": "downstream",
            "formal_ref": result["formal_ref"],
            "published_ref": result["published_ref"],
        },
    )
    return "OK", "formal handoff materialized", {
        "canonical_path": handoff_ref,
        "gate_decision_ref": decision_ref,
        "materialized_handoff_ref": handoff_ref,
        "materialized_job_ref": "",
        "run_closure_ref": "",
        "enablement_scope": "guarded-only" if payload.get("guarded_only") else "core",
        "formal_ref": result["formal_ref"],
    }, [], [handoff_ref, result["receipt_ref"]]


def _dispatch_action(ctx: CommandContext):
    decision_ref = str(ctx.payload.get("gate_decision_ref", ""))
    ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref is required")
    job_ref = "artifacts/jobs/ready/materialized-job.json"
    write_json(_artifact_path(ctx, job_ref), {"trace": ctx.trace, "gate_decision_ref": decision_ref, "job_type": "next-execution"})
    return "OK", "materialized job dispatched", {
        "canonical_path": job_ref,
        "gate_decision_ref": decision_ref,
        "materialized_handoff_ref": "",
        "materialized_job_ref": job_ref,
        "run_closure_ref": "",
        "enablement_scope": "core",
    }, [], [job_ref]


def _close_action(ctx: CommandContext):
    payload = ctx.payload
    run_ref = str(payload.get("run_ref", ctx.trace.get("run_ref", "")))
    ensure(run_ref, "INVALID_REQUEST", "run_ref is required")
    closure_ref = "artifacts/active/closures/run-closure.json"
    write_json(_artifact_path(ctx, closure_ref), {"trace": ctx.trace, "run_ref": run_ref, "final_status": "closed"})
    return "OK", "run closed", {
        "canonical_path": closure_ref,
        "gate_decision_ref": str(payload.get("gate_decision_ref", "")),
        "materialized_handoff_ref": "",
        "materialized_job_ref": "",
        "run_closure_ref": closure_ref,
        "enablement_scope": "core",
    }, [], [closure_ref]


def _gate_handler(ctx: CommandContext):
    handlers = {
        "submit-handoff": _submit_handoff_action,
        "show-pending": _show_pending_action,
        "decide": _decide_action,
        "create": _package_action,
        "verify": _package_action,
        "evaluate": _evaluate_action,
        "materialize": _materialize_action,
        "dispatch": _dispatch_action,
        "close-run": _close_action,
    }
    return handlers[ctx.action](ctx)


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _gate_handler)
