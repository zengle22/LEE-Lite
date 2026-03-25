"""Onboarding and rollout state persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json


def write_onboarding_state(workspace_root: Path, payload: dict[str, Any], trace: dict[str, Any]) -> dict[str, str]:
    state_path = workspace_root / "artifacts" / "active" / "rollout" / "onboarding-assessment.json"
    wave_path = workspace_root / "artifacts" / "active" / "rollout" / "wave-state.json"
    write_json(
        state_path,
        {
            "trace": trace,
            "skill_ref": payload.get("skill_ref", ""),
            "wave_id": payload.get("wave_id", ""),
            "compat_mode": payload.get("compat_mode", ""),
            "cutover_guard_ref": payload.get("cutover_guard_ref", ""),
            "integration_matrix_ref": payload["integration_matrix_ref"],
            "migration_wave_ref": payload["migration_wave_ref"],
            "pilot_chain_ref": payload["pilot_chain_ref"],
        },
    )
    write_json(
        wave_path,
        {
            "trace": trace,
            "wave_id": payload.get("wave_id", ""),
            "compat_mode": payload.get("compat_mode", ""),
            "cutover_guard_ref": payload.get("cutover_guard_ref", ""),
            "status": "onboarded",
        },
    )
    return {
        "onboarding_assessment_ref": to_canonical_path(state_path, workspace_root),
        "wave_state_ref": to_canonical_path(wave_path, workspace_root),
    }


def write_readiness_summary(workspace_root: Path, trace: dict[str, Any], label: str) -> dict[str, str]:
    summary_path = workspace_root / "artifacts" / "active" / "rollout" / "readiness-summary.json"
    write_json(summary_path, {"trace": trace, "readiness_label": label})
    return {"readiness_summary_ref": to_canonical_path(summary_path, workspace_root)}


def resolve_pilot_evidence(workspace_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    ref = str(payload.get("pilot_evidence_ref", "")).strip()
    if ref:
        evidence = load_json(canonical_to_path(ref, workspace_root))
    else:
        evidence_path = workspace_root / "artifacts" / "active" / "rollout" / "pilot-evidence.json"
        if not evidence_path.exists():
            return {}
        evidence = load_json(evidence_path)
        ref = to_canonical_path(evidence_path, workspace_root)
    if str(evidence.get("pilot_chain_ref", "")) != str(payload.get("pilot_chain_ref", "")):
        return {}
    if str(evidence.get("evidence_status", "")) != "sufficient":
        return {}
    evidence["_ref"] = ref
    return evidence


def record_fallback(workspace_root: Path, payload: dict[str, Any], trace: dict[str, Any], request_id: str) -> dict[str, str]:
    wave_path = workspace_root / "artifacts" / "active" / "rollout" / "wave-state.json"
    receipt_path = workspace_root / "artifacts" / "active" / "receipts" / f"fallback-{request_id}.json"
    wave_state = load_json(wave_path) if wave_path.exists() else {"trace": trace}
    wave_state.update(
        {
            "status": "fallback_triggered",
            "wave_id": payload.get("wave_id", wave_state.get("wave_id", "")),
            "compat_mode": payload.get("compat_mode", wave_state.get("compat_mode", "")),
            "cutover_guard_ref": payload.get("cutover_guard_ref", wave_state.get("cutover_guard_ref", "")),
            "fallback_reason_code": payload.get("fallback_reason_code", ""),
            "fallback_receipt_ref": to_canonical_path(receipt_path, workspace_root),
        }
    )
    receipt = {
        "trace": trace,
        "wave_id": wave_state.get("wave_id", ""),
        "fallback_reason_code": payload.get("fallback_reason_code", ""),
        "cutover_guard_ref": wave_state.get("cutover_guard_ref", ""),
        "result": "fallback_recorded",
    }
    write_json(wave_path, wave_state)
    write_json(receipt_path, receipt)
    return {
        "wave_state_ref": to_canonical_path(wave_path, workspace_root),
        "fallback_receipt_ref": to_canonical_path(receipt_path, workspace_root),
    }
