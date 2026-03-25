"""Gate package, decision, materialization, dispatch, and run closure."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json
from cli.lib.gate_closure import close_run
from cli.lib.gate_decision import build_decision_from_audit, load_findings
from cli.lib.gate_materializer import dispatch_materialized_job, materialize_handoff
from cli.lib.gate_protocol import build_gate_ready_package, ensure_allowed_decision
from cli.lib.gate_reader import load_gate_ready_package, load_handoff
from cli.lib.mainline_runtime import mark_handoff_closed, register_reentry_state, show_pending, submit_handoff
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.reentry import create_reentry


def _gate_handler(ctx: CommandContext):
    payload = ctx.payload
    if ctx.action == "submit-handoff":
        result = submit_handoff(ctx.workspace_root, payload, ctx.trace, ctx.request["request_id"])
        evidence_refs = [result["handoff_ref"], result["gate_pending_ref"], result["trace_ref"]]
        return "OK", "handoff submitted", {"canonical_path": result["handoff_ref"], **result}, [], evidence_refs
    if ctx.action == "show-pending":
        handoff_ref = str(payload.get("handoff_ref", ""))
        ensure(handoff_ref, "INVALID_REQUEST", "handoff_ref is required")
        result = show_pending(ctx.workspace_root, handoff_ref)
        return "OK", "pending state resolved", result, [], [result["canonical_path"]]
    if ctx.action in {"create", "verify"}:
        for field in ("candidate_ref", "acceptance_ref", "evidence_bundle_ref"):
            ensure(field in payload, "INVALID_REQUEST", f"missing gate package field: {field}")
        package_ref = "artifacts/active/gates/packages/gate-ready-package.json"
        if ctx.action == "create":
            write_json(ctx.workspace_root / package_ref, build_gate_ready_package(payload, ctx.trace))
        return "OK", f"gate package {ctx.action} completed", {
            "canonical_path": package_ref,
            "gate_ready_package_ref": package_ref,
            "completeness_result": "complete",
            "validation_summary": {"required_fields_present": True},
        }, [], [package_ref]

    if ctx.action == "evaluate":
        for field in ("gate_ready_package_ref", "audit_finding_refs", "target_matrix"):
            ensure(field in payload, "INVALID_REQUEST", f"missing gate evaluate field: {field}")
        if payload.get("guard_required") and not payload.get("guarded_enablement_ref"):
            raise CommandError("PROVISIONAL_SLICE_DISABLED", "guarded slice is not enabled")
        package = load_gate_ready_package(ctx.workspace_root, str(payload["gate_ready_package_ref"]))
        findings = load_findings(ctx.workspace_root, list(payload.get("audit_finding_refs", [])))
        decision_ref = f"artifacts/active/gates/decisions/{ctx.request['request_id']}.json"
        decision = build_decision_from_audit(
            ctx.trace,
            str(payload.get("handoff_ref", payload["gate_ready_package_ref"])),
            str(package.get("proposal_ref", "")),
            None,
            str(payload.get("review_context_ref", "")),
            findings,
        )
        decision["target_matrix"] = payload["target_matrix"]
        write_json(ctx.workspace_root / decision_ref, decision)
        return "OK", "gate decision produced", {
            "canonical_path": decision_ref,
            "gate_decision_ref": decision_ref,
            "enablement_scope": "guarded-only" if payload.get("guarded_enablement_ref") else "core",
        }, [], [decision_ref]

    if ctx.action == "decide":
        for field in ("handoff_ref", "proposal_ref", "decision"):
            ensure(field in payload, "INVALID_REQUEST", f"missing gate decide field: {field}")
        handoff = load_handoff(ctx.workspace_root, str(payload["handoff_ref"]))
        decision_type = ensure_allowed_decision(str(payload["decision"]))
        decision_ref = f"artifacts/active/gates/decisions/{ctx.request['request_id']}.json"
        decision = build_decision_from_audit(
            ctx.trace,
            str(payload["handoff_ref"]),
            str(payload["proposal_ref"]),
            decision_type,
            str(payload.get("review_context_ref", "")),
            [],
        )
        decision["decision_reason"] = str(payload.get("decision_reason", ""))
        write_json(ctx.workspace_root / decision_ref, decision)
        data = {
            "canonical_path": decision_ref,
            "gate_decision_ref": decision_ref,
            "decision": decision_type,
            "reentry_ref": "",
            "child_run_ref": "",
        }
        if decision_type in {"revise", "retry"}:
            reentry = create_reentry(
                ctx.workspace_root,
                str(payload["handoff_ref"]),
                decision_ref,
                decision_type,
                ctx.trace,
                str(payload["proposal_ref"]),
                str(payload.get("review_context_ref", "")),
            )
            register_reentry_state(ctx.workspace_root, str(payload["handoff_ref"]), reentry["reentry_ref"])
            data.update(reentry)
        if decision_type == "reject":
            closure = close_run(
                ctx.workspace_root,
                ctx.trace,
                str(ctx.trace.get("run_ref", "")),
                ctx.request["request_id"],
                decision_ref,
            )
            mark_handoff_closed(ctx.workspace_root, str(payload["handoff_ref"]), closure["run_closure_ref"])
            data.update(closure)
        if decision_type == "handoff":
            data["delegated_handler"] = str(handoff.get("producer_ref", ""))
        return "OK", "gate decision produced", data, [], [decision_ref]

    if ctx.action == "materialize":
        decision_ref = str(payload.get("gate_decision_ref", ""))
        ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref is required")
        result = materialize_handoff(ctx.workspace_root, decision_ref, ctx.trace, ctx.request["request_id"])
        return "OK", "formal handoff materialized", {
            "canonical_path": result["materialized_handoff_ref"],
            "gate_decision_ref": decision_ref,
            "materialized_handoff_ref": result["materialized_handoff_ref"],
            "materialized_job_ref": "",
            "run_closure_ref": "",
            "enablement_scope": "guarded-only" if payload.get("guarded_only") else "core",
        }, [], [result["materialized_handoff_ref"]]

    if ctx.action == "dispatch":
        decision_ref = str(payload.get("gate_decision_ref", ""))
        ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref is required")
        result = dispatch_materialized_job(ctx.workspace_root, decision_ref, ctx.trace, ctx.request["request_id"])
        return "OK", "materialized job dispatched", {
            "canonical_path": result["materialized_job_ref"],
            "gate_decision_ref": decision_ref,
            "materialized_handoff_ref": "",
            "materialized_job_ref": result["materialized_job_ref"],
            "run_closure_ref": "",
            "enablement_scope": "core",
        }, [], [result["materialized_job_ref"]]

    run_ref = str(payload.get("run_ref", ctx.trace.get("run_ref", "")))
    ensure(run_ref, "INVALID_REQUEST", "run_ref is required")
    closure = close_run(
        ctx.workspace_root,
        ctx.trace,
        run_ref,
        ctx.request["request_id"],
        str(payload.get("gate_decision_ref", "")),
    )
    return "OK", "run closed", {
        "canonical_path": closure["run_closure_ref"],
        "gate_decision_ref": str(payload.get("gate_decision_ref", "")),
        "materialized_handoff_ref": "",
        "materialized_job_ref": "",
        "run_closure_ref": closure["run_closure_ref"],
        "enablement_scope": "core",
    }, [], [closure["run_closure_ref"]]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _gate_handler)

