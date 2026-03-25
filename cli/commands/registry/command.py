"""Registry and admission operations."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.admission import validate_admission
from cli.lib.formalization import materialize_formal
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.fs import to_canonical_path
from cli.lib.registry_store import record_path, save_registry_record, verify_eligibility


def _registry_handler(ctx: CommandContext):
    payload = ctx.payload
    if ctx.action == "resolve-formal-ref":
        artifact_ref = str(payload.get("artifact_ref", ""))
        ensure(artifact_ref, "INVALID_REQUEST", "artifact_ref is required")
        record = verify_eligibility(ctx.workspace_root, artifact_ref, payload.get("lineage_expectation"))
        return "OK", "formal reference resolved", {
            "canonical_path": record["managed_artifact_ref"],
            "registry_record_ref": to_canonical_path(record_path(ctx.workspace_root, artifact_ref), ctx.workspace_root),
            "resolved_artifact_ref": record["managed_artifact_ref"],
            "resolved_formal_ref": artifact_ref,
            "eligibility_result": "eligible",
            "lineage_summary": record.get("lineage", []),
        }, [], []

    if ctx.action == "verify-eligibility":
        artifact_ref = str(payload.get("artifact_ref", ""))
        ensure(artifact_ref, "INVALID_REQUEST", "artifact_ref is required")
        record = verify_eligibility(ctx.workspace_root, artifact_ref, payload.get("lineage_expectation"))
        return "OK", "eligibility verified", {
            "canonical_path": record["managed_artifact_ref"],
            "registry_record_ref": to_canonical_path(record_path(ctx.workspace_root, artifact_ref), ctx.workspace_root),
            "resolved_artifact_ref": record["managed_artifact_ref"],
            "resolved_formal_ref": artifact_ref,
            "eligibility_result": "eligible",
            "lineage_summary": record.get("lineage", []),
        }, [], []

    if ctx.action == "validate-admission":
        consumer_ref = str(payload.get("consumer_ref", ""))
        requested_ref = str(payload.get("requested_ref", payload.get("artifact_ref", "")))
        ensure(consumer_ref, "INVALID_REQUEST", "consumer_ref is required")
        ensure(requested_ref, "INVALID_REQUEST", "requested_ref is required")
        verdict = validate_admission(
            ctx.workspace_root,
            consumer_ref=consumer_ref,
            requested_ref=requested_ref,
            lineage_expectation=payload.get("lineage_expectation"),
        )
        return "OK", "admission validated", {
            "canonical_path": verdict["resolved_formal_ref"],
            "admission_result": "allow",
            "resolved_formal_ref": verdict["resolved_formal_ref"],
            "lineage_summary": verdict["upstream_refs"],
            "layer": verdict["layer"],
        }, [], []

    if ctx.action == "publish-formal":
        candidate_ref = str(payload.get("candidate_ref", ""))
        decision_ref = str(payload.get("decision_ref", ""))
        ensure(candidate_ref, "INVALID_REQUEST", "candidate_ref is required")
        ensure(decision_ref, "INVALID_REQUEST", "decision_ref is required")
        result = materialize_formal(
            ctx.workspace_root,
            trace=ctx.trace,
            candidate_ref=candidate_ref,
            decision_ref=decision_ref,
            target_formal_kind=str(payload.get("target_formal_kind", "generic")),
            formal_artifact_ref=str(payload["formal_artifact_ref"]) if payload.get("formal_artifact_ref") else None,
        )
        return "OK", "formal object published", {
            "canonical_path": result["published_ref"],
            "formal_ref": result["formal_ref"],
            "published_ref": result["published_ref"],
            "lineage_ref": result["receipt_ref"],
        }, [], [result["receipt_ref"]]

    artifact_ref = str(payload.get("artifact_ref", ""))
    ensure(artifact_ref, "INVALID_REQUEST", "artifact_ref is required")
    managed_ref = str(payload.get("managed_artifact_ref", ""))
    ensure(managed_ref, "INVALID_REQUEST", "managed_artifact_ref is required")
    record = {
        "artifact_ref": artifact_ref,
        "managed_artifact_ref": managed_ref,
        "status": str(payload.get("status", "committed")),
        "trace": ctx.trace,
        "metadata": payload.get("metadata", {}),
        "lineage": payload.get("lineage", []),
    }
    record_ref = save_registry_record(ctx.workspace_root, record)
    return "OK", "registry record bound", {
        "canonical_path": managed_ref,
        "registry_record_ref": record_ref,
        "resolved_artifact_ref": managed_ref,
        "eligibility_result": "unknown",
        "lineage_summary": record.get("lineage", []),
    }, [], [record_ref]


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _registry_handler)
