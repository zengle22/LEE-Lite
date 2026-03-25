"""Formal publication helpers."""

from __future__ import annotations

from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, load_json, write_json
from cli.lib.registry_store import bind_record, resolve_registry_record, slugify


def materialize_formal(
    workspace_root,
    trace: dict[str, Any],
    candidate_ref: str,
    decision_ref: str,
    target_formal_kind: str,
    formal_artifact_ref: str | None = None,
) -> dict[str, str]:
    decision = load_json(canonical_to_path(decision_ref, workspace_root))
    ensure(decision.get("decision_type") in {"approve", "handoff"}, "PRECONDITION_FAILED", "decision_not_approvable")
    candidate = resolve_registry_record(workspace_root, candidate_ref)
    formal_ref = formal_artifact_ref or f"formal.{target_formal_kind}.{slugify(candidate['artifact_ref'])}"
    published_ref = f"artifacts/formal/{slugify(formal_ref)}.json"
    write_json(
        workspace_root / published_ref,
        {
            "trace": trace,
            "candidate_ref": candidate["artifact_ref"],
            "candidate_managed_artifact_ref": candidate["managed_artifact_ref"],
            "decision_ref": decision_ref,
            "target_formal_kind": target_formal_kind,
        },
    )
    receipt_ref = f"artifacts/active/formalization/{slugify(formal_ref)}-receipt.json"
    write_json(
        workspace_root / receipt_ref,
        {
            "trace": trace,
            "candidate_ref": candidate["artifact_ref"],
            "formal_artifact_ref": formal_ref,
            "published_ref": published_ref,
            "decision_ref": decision_ref,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata={"layer": "formal", "target_formal_kind": target_formal_kind},
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    return {"formal_ref": formal_ref, "published_ref": published_ref, "receipt_ref": receipt_ref}
