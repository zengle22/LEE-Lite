"""Rollout and readiness operations."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import CommandError, ensure
from cli.lib.pilot_chain import validate_pilot_chain
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.rollout_boundary import check_scope_boundary
from cli.lib.rollout_state import record_fallback, resolve_pilot_evidence, write_onboarding_state, write_readiness_summary


def _rollout_handler(ctx: CommandContext):
    payload = ctx.payload
    for field in ("integration_matrix_ref", "migration_wave_ref", "pilot_chain_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing rollout field: {field}")
    if ctx.action in {"assess-skill", "onboard-skill"}:
        result = write_onboarding_state(ctx.workspace_root, payload, ctx.trace)
        return "OK", "skill onboarding assessed", {
            "canonical_path": result["onboarding_assessment_ref"],
            "onboarding_assessment_ref": result["onboarding_assessment_ref"],
            "wave_state_ref": result["wave_state_ref"],
            "pilot_evidence_ref": "",
            "readiness_summary_ref": "",
            "readiness_label": "assessed",
        }, [], [result["onboarding_assessment_ref"], result["wave_state_ref"]]
    if ctx.action == "validate-pilot":
        result = validate_pilot_chain(ctx.workspace_root, payload, ctx.trace)
        return "OK", "pilot chain validated", {
            "canonical_path": result["pilot_evidence_ref"],
            "onboarding_assessment_ref": "",
            "pilot_evidence_ref": result["pilot_evidence_ref"],
            "readiness_summary_ref": "",
            "readiness_label": "pilot-validated",
            "evidence_status": result["evidence_status"],
            "cutover_recommendation": result["cutover_recommendation"],
        }, [], [result["pilot_evidence_ref"]]
    if ctx.action == "record-fallback":
        for field in ("wave_id", "fallback_reason_code"):
            ensure(field in payload, "INVALID_REQUEST", f"missing rollout fallback field: {field}")
        result = record_fallback(ctx.workspace_root, payload, ctx.trace, ctx.request["request_id"])
        return "OK", "fallback recorded", {
            "canonical_path": result["fallback_receipt_ref"],
            "wave_state_ref": result["wave_state_ref"],
            "fallback_receipt_ref": result["fallback_receipt_ref"],
        }, [], [result["wave_state_ref"], result["fallback_receipt_ref"]]
    if ctx.action == "check-scope":
        result = check_scope_boundary(ctx.workspace_root, payload, ctx.trace)
        return "OK", "scope boundary checked", {
            "canonical_path": result["scope_boundary_verdict_ref"],
            "scope_boundary_verdict_ref": result["scope_boundary_verdict_ref"],
            "boundary_review_note_ref": result["boundary_review_note_ref"],
        }, [], [result["scope_boundary_verdict_ref"], result["boundary_review_note_ref"]]
    guarded_result = payload.get("guarded_gate_result_ref")
    if guarded_result and not payload.get("guarded_enabled", False):
        raise CommandError("PROVISIONAL_SLICE_DISABLED", "guarded gate branch is not enabled for readiness")
    evidence = resolve_pilot_evidence(ctx.workspace_root, payload)
    ensure(bool(evidence), "PRECONDITION_FAILED", "pilot evidence is required for readiness")
    label = "guarded-ready" if payload.get("guarded_enabled", False) else "core-ready"
    result = write_readiness_summary(ctx.workspace_root, ctx.trace, label)
    return "OK", "rollout readiness summarized", {
        "canonical_path": result["readiness_summary_ref"],
        "onboarding_assessment_ref": "",
        "pilot_evidence_ref": evidence["_ref"],
        "readiness_summary_ref": result["readiness_summary_ref"],
        "readiness_label": label,
    }, [], [evidence["_ref"], result["readiness_summary_ref"]]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _rollout_handler)

