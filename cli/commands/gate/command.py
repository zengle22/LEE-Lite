"""Gate package, decision, materialization, dispatch, and run closure."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json
from cli.lib.protocol import CommandContext, run_with_protocol


def _artifact_path(ctx: CommandContext, relative: str):
    return ctx.workspace_root / relative


def _decision_type(findings: list[dict[str, object]]) -> str:
    blocker_count = sum(1 for item in findings if item.get("severity") == "blocker")
    return "revise" if blocker_count else "approve"


def _gate_handler(ctx: CommandContext):
    payload = ctx.payload
    if ctx.action in {"create", "verify"}:
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

    if ctx.action == "evaluate":
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
        decision = {
            "trace": ctx.trace,
            "decision_type": _decision_type(findings),
            "target_matrix": payload["target_matrix"],
            "rationale": "derived from audit findings and target constraints",
        }
        write_json(_artifact_path(ctx, decision_ref), decision)
        return "OK", "gate decision produced", {
            "canonical_path": decision_ref,
            "gate_decision_ref": decision_ref,
            "enablement_scope": "guarded-only" if payload.get("guarded_enablement_ref") else "core",
        }, [], [decision_ref]

    if ctx.action == "materialize":
        decision_ref = str(payload.get("gate_decision_ref", ""))
        ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref is required")
        decision = load_json(canonical_to_path(decision_ref, ctx.workspace_root))
        ensure(decision.get("decision_type") == "approve", "PRECONDITION_FAILED", "only approve can materialize")
        handoff_ref = "artifacts/active/handoffs/materialized-handoff.json"
        write_json(_artifact_path(ctx, handoff_ref), {"trace": ctx.trace, "gate_decision_ref": decision_ref, "handoff_type": "downstream"})
        return "OK", "formal handoff materialized", {
            "canonical_path": handoff_ref,
            "gate_decision_ref": decision_ref,
            "materialized_handoff_ref": handoff_ref,
            "materialized_job_ref": "",
            "run_closure_ref": "",
            "enablement_scope": "guarded-only" if payload.get("guarded_only") else "core",
        }, [], [handoff_ref]

    if ctx.action == "dispatch":
        decision_ref = str(payload.get("gate_decision_ref", ""))
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


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _gate_handler)

