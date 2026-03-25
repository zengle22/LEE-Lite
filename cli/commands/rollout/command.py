"""Rollout and readiness operations."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import canonical_to_path, write_json
from cli.lib.protocol import CommandContext, run_with_protocol


def _rollout_handler(ctx: CommandContext):
    payload = ctx.payload
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
        pilot_ref = "artifacts/active/rollout/pilot-evidence.json"
        write_json(
            _resolve(ctx, pilot_ref),
            {
                "trace": ctx.trace,
                "integration_matrix_ref": payload["integration_matrix_ref"],
                "migration_wave_ref": payload["migration_wave_ref"],
                "pilot_chain_ref": payload["pilot_chain_ref"],
            },
        )
        return "OK", "pilot chain validated", {
            "canonical_path": pilot_ref,
            "onboarding_assessment_ref": "",
            "pilot_evidence_ref": pilot_ref,
            "readiness_summary_ref": "",
            "readiness_label": "pilot-validated",
        }, [], [pilot_ref]
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

