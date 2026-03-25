"""Admission checks for downstream consumers."""

from __future__ import annotations

from typing import Any

from cli.lib.errors import CommandError
from cli.lib.lineage import resolve_lineage


def validate_admission(
    workspace_root,
    consumer_ref: str,
    requested_ref: str,
    lineage_expectation: str | None = None,
) -> dict[str, Any]:
    lineage = resolve_lineage(workspace_root, requested_ref)
    if lineage["layer"] != "formal":
        raise CommandError("ELIGIBILITY_DENIED", "candidate or intermediate objects are not admissible", ["layer_violation"])
    if lineage_expectation and lineage_expectation not in lineage["upstream_refs"]:
        raise CommandError("ELIGIBILITY_DENIED", "lineage expectation not satisfied", [lineage_expectation])
    return {
        "allow": True,
        "consumer_ref": consumer_ref,
        "resolved_formal_ref": lineage["authoritative_ref"],
        "layer": lineage["layer"],
        "reason_code": "eligible",
        "upstream_refs": lineage["upstream_refs"],
        "downstream_refs": lineage["downstream_refs"],
    }
