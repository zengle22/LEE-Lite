"""Pilot chain validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError
from cli.lib.fs import canonical_to_path, read_text, to_canonical_path, write_json


def _load_chain(workspace_root: Path, ref: str) -> list[str]:
    path = canonical_to_path(ref, workspace_root)
    if not path.exists():
        raise CommandError("PRECONDITION_FAILED", f"pilot chain not found: {ref}")
    text = read_text(path)
    try:
        payload = json.loads(text)
        chain = payload.get("chain", [])
        return [str(item) for item in chain]
    except json.JSONDecodeError:
        return [segment.strip() for segment in text.split("->") if segment.strip()]


def validate_pilot_chain(workspace_root: Path, payload: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    chain = _load_chain(workspace_root, str(payload["pilot_chain_ref"]))
    required = ["producer", "gate", "formal", "consumer", "audit"]
    missing = [item for item in required if not any(item in segment for segment in chain)]
    if missing:
        raise CommandError("PRECONDITION_FAILED", "pilot chain is incomplete", missing)
    evidence_path = workspace_root / "artifacts" / "active" / "rollout" / "pilot-evidence.json"
    write_json(
        evidence_path,
        {
            "trace": trace,
            "integration_matrix_ref": payload["integration_matrix_ref"],
            "migration_wave_ref": payload["migration_wave_ref"],
            "pilot_chain_ref": payload["pilot_chain_ref"],
            "chain": chain,
            "evidence_status": "sufficient",
            "cutover_recommendation": "proceed",
        },
    )
    return {
        "pilot_evidence_ref": to_canonical_path(evidence_path, workspace_root),
        "evidence_status": "sufficient",
        "cutover_recommendation": "proceed",
    }
