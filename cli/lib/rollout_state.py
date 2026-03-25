"""Persistent rollout state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import load_json, write_json


def _wave_path(workspace_root: Path, wave_id: str) -> Path:
    return workspace_root / "artifacts" / "active" / "rollout" / "waves" / f"{wave_id}.json"


def write_onboarding_wave(
    workspace_root: Path,
    trace: dict[str, Any],
    skill_ref: str,
    wave_id: str,
    scope: str,
    compat_mode: bool,
    foundation_ready: bool,
) -> dict[str, str]:
    ensure(foundation_ready, "PRECONDITION_FAILED", "foundation_missing")
    wave_ref = f"artifacts/active/rollout/waves/{wave_id}.json"
    write_json(
        _wave_path(workspace_root, wave_id),
        {
            "trace": trace,
            "skill_ref": skill_ref,
            "wave_id": wave_id,
            "scope": scope,
            "compat_mode": compat_mode,
            "status": "pilot_enabled",
        },
    )
    return {
        "status": "pilot_enabled",
        "runtime_binding_ref": wave_ref,
        "cutover_guard_ref": f"artifacts/active/rollout/cutover-guards/{wave_id}.json",
    }


def mark_cutover(workspace_root: Path, trace: dict[str, Any], wave_id: str, mode: str) -> dict[str, str]:
    path = _wave_path(workspace_root, wave_id)
    ensure(path.exists(), "PRECONDITION_FAILED", "wave_missing")
    state = load_json(path)
    state["trace"] = trace
    state["status"] = "cutover_guarded" if mode == "cutover" else "fallback_triggered"
    write_json(path, state)
    receipt_ref = f"artifacts/active/rollout/receipts/{wave_id}-{mode}.json"
    write_json(
        workspace_root / receipt_ref,
        {
            "trace": trace,
            "wave_id": wave_id,
            "mode": mode,
            "status": state["status"],
        },
    )
    return {
        "wave_ref": f"artifacts/active/rollout/waves/{wave_id}.json",
        "status": state["status"],
        "receipt_ref": receipt_ref,
    }
