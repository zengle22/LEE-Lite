"""Registry and admission operations."""

from __future__ import annotations

from argparse import Namespace

from cli.lib.errors import ensure
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.fs import to_canonical_path
from cli.lib.registry_store import record_path, save_registry_record, verify_eligibility


def _registry_handler(ctx: CommandContext):
    payload = ctx.payload
    artifact_ref = str(payload.get("artifact_ref", ""))
    ensure(artifact_ref, "INVALID_REQUEST", "artifact_ref is required")

    if ctx.action == "resolve-formal-ref":
        record = verify_eligibility(ctx.workspace_root, artifact_ref, payload.get("lineage_expectation"))
        return "OK", "formal reference resolved", {
            "canonical_path": record["managed_artifact_ref"],
            "registry_record_ref": to_canonical_path(record_path(ctx.workspace_root, artifact_ref), ctx.workspace_root),
            "resolved_artifact_ref": record["managed_artifact_ref"],
            "eligibility_result": "eligible",
            "lineage_summary": record.get("lineage", []),
        }, [], []

    if ctx.action == "verify-eligibility":
        record = verify_eligibility(ctx.workspace_root, artifact_ref, payload.get("lineage_expectation"))
        return "OK", "eligibility verified", {
            "canonical_path": record["managed_artifact_ref"],
            "registry_record_ref": to_canonical_path(record_path(ctx.workspace_root, artifact_ref), ctx.workspace_root),
            "resolved_artifact_ref": record["managed_artifact_ref"],
            "eligibility_result": "eligible",
            "lineage_summary": record.get("lineage", []),
        }, [], []

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
