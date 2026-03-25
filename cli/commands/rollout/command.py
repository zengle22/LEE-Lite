"""Rollout and readiness operations."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, load_json, write_json
from cli.lib.pilot_chain import submit_pilot_evidence
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.rollout_state import mark_cutover, write_onboarding_wave


def _rollout_handler(ctx: CommandContext):
    payload = ctx.payload
    if ctx.action == "onboard-skill":
        for field in ("skill_ref", "wave_id", "scope"):
            ensure(field in payload, "INVALID_REQUEST", f"missing onboarding field: {field}")
        result = write_onboarding_wave(
            ctx.workspace_root,
            trace=ctx.trace,
            skill_ref=str(payload["skill_ref"]),
            wave_id=str(payload["wave_id"]),
            scope=str(payload["scope"]),
            compat_mode=bool(payload.get("compat_mode", False)),
            foundation_ready=bool(payload.get("foundation_ready", False)),
        )
        return "OK", "skill onboarding assessed", {
            "canonical_path": result["runtime_binding_ref"],
            "onboarding_assessment_ref": result["runtime_binding_ref"],
            "pilot_evidence_ref": "",
            "readiness_summary_ref": "",
            "readiness_label": result["status"],
            "cutover_guard_ref": result["cutover_guard_ref"],
        }, [], [result["runtime_binding_ref"]]

    if ctx.action == "cutover-wave":
        wave_id = str(payload.get("wave_id", ""))
        ensure(wave_id, "INVALID_REQUEST", "wave_id is required")
        pilot_evidence_ref = str(payload.get("pilot_evidence_ref", ""))
        ensure(pilot_evidence_ref, "PRECONDITION_FAILED", "pilot_evidence_ref is required")
        pilot_payload = load_json(canonical_to_path(pilot_evidence_ref, ctx.workspace_root))
        ensure(pilot_payload.get("evidence_status") == "complete", "PRECONDITION_FAILED", "pilot_evidence_incomplete")
        result = mark_cutover(ctx.workspace_root, ctx.trace, wave_id, "cutover")
        return "OK", "cutover guard advanced", {
            "canonical_path": result["wave_ref"],
            "onboarding_assessment_ref": result["wave_ref"],
            "pilot_evidence_ref": "",
            "readiness_summary_ref": "",
            "readiness_label": result["status"],
            "receipt_ref": result["receipt_ref"],
        }, [], [result["wave_ref"], result["receipt_ref"]]

    if ctx.action == "fallback-wave":
        wave_id = str(payload.get("wave_id", ""))
        ensure(wave_id, "INVALID_REQUEST", "wave_id is required")
        result = mark_cutover(ctx.workspace_root, ctx.trace, wave_id, "fallback")
        return "OK", "fallback triggered", {
            "canonical_path": result["wave_ref"],
            "onboarding_assessment_ref": result["wave_ref"],
            "pilot_evidence_ref": "",
            "readiness_summary_ref": "",
            "readiness_label": result["status"],
            "receipt_ref": result["receipt_ref"],
        }, [], [result["wave_ref"], result["receipt_ref"]]

    for field in ("integration_matrix_ref", "migration_wave_ref", "pilot_chain_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing rollout field: {field}")
    if ctx.action == "assess-skill":
        assessment_ref = "artifacts/active/rollout/onboarding-assessment.json"
        write_json(_resolve(ctx, assessment_ref), {"trace": ctx.trace, "assessment": "governed-skill-scope-confirmed"})
        return "OK", "skill onboarding assessed", {
            "canonical_path": assessment_ref,
            "onboarding_assessment_ref": assessment_ref,
            "pilot_evidence_ref": "",
            "readiness_summary_ref": "",
            "readiness_label": "assessed",
        }, [], [assessment_ref]
    if ctx.action == "validate-pilot":
        result = submit_pilot_evidence(
            ctx.workspace_root,
            trace=ctx.trace,
            pilot_chain_ref=str(payload["pilot_chain_ref"]),
            producer_ref=str(payload.get("producer_ref", payload["integration_matrix_ref"])),
            consumer_ref=str(payload.get("consumer_ref", payload["migration_wave_ref"])),
            audit_ref=str(payload.get("audit_ref", "artifacts/active/audit/finding-bundle.json")),
            gate_ref=str(payload.get("gate_ref", "artifacts/active/gates/decisions/gate-decision.json")),
        )
        return "OK", "pilot chain validated", {
            "canonical_path": result["pilot_evidence_ref"],
            "onboarding_assessment_ref": "",
            "pilot_evidence_ref": result["pilot_evidence_ref"],
            "readiness_summary_ref": "",
            "readiness_label": "pilot-validated",
        }, [], [result["pilot_evidence_ref"]]
    guarded_result = payload.get("guarded_gate_result_ref")
    if guarded_result and not payload.get("guarded_enabled", False):
        raise CommandError("PROVISIONAL_SLICE_DISABLED", "guarded gate branch is not enabled for readiness")
    summary_ref = "artifacts/active/rollout/readiness-summary.json"
    label = "guarded-ready" if payload.get("guarded_enabled", False) else "core-ready"
    write_json(_resolve(ctx, summary_ref), {"trace": ctx.trace, "readiness_label": label})
    return "OK", "rollout readiness summarized", {
        "canonical_path": summary_ref,
        "onboarding_assessment_ref": "",
        "pilot_evidence_ref": "",
        "readiness_summary_ref": summary_ref,
        "readiness_label": label,
    }, [], [summary_ref]


def _resolve(ctx: CommandContext, relative: str):
    return canonical_to_path(relative, ctx.workspace_root)


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _rollout_handler)
