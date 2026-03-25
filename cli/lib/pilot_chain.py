"""Pilot chain evidence validation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from cli.lib.fs import write_json
from cli.lib.registry_store import slugify


def _pilot_evidence_id(pilot_chain_ref: str) -> str:
    seed = Path(pilot_chain_ref).stem or pilot_chain_ref
    digest = hashlib.sha1(pilot_chain_ref.encode("utf-8")).hexdigest()[:8]
    return f"{slugify(seed)[:48]}-{digest}".strip("-")


def submit_pilot_evidence(
    workspace_root,
    trace: dict[str, Any],
    pilot_chain_ref: str,
    producer_ref: str,
    consumer_ref: str,
    audit_ref: str,
    gate_ref: str,
) -> dict[str, str]:
    evidence_id = _pilot_evidence_id(pilot_chain_ref)
    evidence_ref = f"artifacts/active/rollout/pilot-evidence-{evidence_id}.json"
    complete = all((pilot_chain_ref, producer_ref, consumer_ref, audit_ref, gate_ref))
    recommendation = "cutover_ready" if complete else "fallback_required"
    write_json(
        workspace_root / evidence_ref,
        {
            "trace": trace,
            "pilot_chain_ref": pilot_chain_ref,
            "producer_ref": producer_ref,
            "consumer_ref": consumer_ref,
            "audit_ref": audit_ref,
            "gate_ref": gate_ref,
            "evidence_status": "complete" if complete else "incomplete",
            "cutover_recommendation": recommendation,
        },
    )
    return {
        "pilot_evidence_ref": evidence_ref,
        "evidence_status": "complete" if complete else "incomplete",
        "cutover_recommendation": recommendation,
    }
