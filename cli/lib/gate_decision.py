"""Decision evaluation for governed gate flows."""

from __future__ import annotations

from pathlib import Path

from cli.lib.fs import canonical_to_path, load_json
from cli.lib.gate_protocol import build_gate_decision


def load_findings(workspace_root: Path, finding_refs: list[str]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for ref in finding_refs:
        path = canonical_to_path(str(ref), workspace_root)
        if path.exists():
            findings.extend(load_json(path).get("findings", []))
    return findings


def infer_decision(findings: list[dict[str, object]], requested: str | None = None) -> str:
    if requested:
        return requested
    blocker_count = sum(1 for item in findings if item.get("severity") == "blocker")
    return "revise" if blocker_count else "approve"


def build_decision_from_audit(
    trace: dict[str, object],
    handoff_ref: str,
    proposal_ref: str,
    requested_decision: str | None,
    review_context_ref: str,
    findings: list[dict[str, object]],
) -> dict[str, object]:
    decision = infer_decision(findings, requested_decision)
    rationale = "derived from audit findings and target constraints"
    return build_gate_decision(trace, decision, handoff_ref, proposal_ref, rationale, review_context_ref, findings)
