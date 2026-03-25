"""CLI integration for ll-gate-human-orchestrator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "skills" / "ll-gate-human-orchestrator" / "scripts" / "gate_human_orchestrator.py"
SCRIPT_CWD = SCRIPT_PATH.parents[3]


def run_gate_human_orchestrator(workspace_root: Path, trace: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    ensure("input_ref" in payload, "INVALID_REQUEST", "missing skill field: input_ref")
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "run",
        "--input",
        _resolve_ref(workspace_root, str(payload["input_ref"])),
        "--repo-root",
        str(workspace_root),
        "--run-id",
        str(payload.get("run_id") or trace.get("run_ref") or ""),
    ]
    _append_optional(command, "--decision", payload.get("decision"))
    _append_optional(command, "--decision-reason", payload.get("decision_reason"))
    _append_optional(command, "--decision-target", payload.get("decision_target"))
    for ref_value in payload.get("audit_finding_refs", []):
        _append_optional(command, "--audit-finding-ref", ref_value)
    if payload.get("allow_update"):
        command.append("--allow-update")
    result = _run(command)
    artifacts_dir = Path(result["artifacts_dir"])
    bundle_ref = artifacts_dir / "gate-decision-bundle.json"
    bundle = json.loads(bundle_ref.read_text(encoding="utf-8"))
    return {
        "skill_ref": "skill.gate.human_orchestrator",
        "runner_skill_ref": "skill.runner.gate_human_orchestrator",
        "artifacts_dir": str(artifacts_dir),
        "bundle_ref": str(bundle_ref),
        "decision": result["decision"],
        "decision_ref": bundle["decision_ref"],
        "dispatch_target": bundle["dispatch_target"],
        "human_projection_ref": bundle["human_projection_ref"],
        "projection_status": bundle["projection_status"],
        "machine_ssot_ref": bundle["machine_ssot_ref"],
    }


def _run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=str(SCRIPT_CWD), capture_output=True, text=True, check=False)
    stdout = completed.stdout.strip()
    if completed.returncode != 0:
        message = completed.stderr.strip() or stdout or "ll-gate-human-orchestrator failed"
        raise CommandError("PRECONDITION_FAILED", message)
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise CommandError("INTERNAL_ERROR", "invalid ll-gate-human-orchestrator output", [str(exc), stdout]) from exc


def _resolve_ref(workspace_root: Path, ref_value: str) -> str:
    path = Path(ref_value)
    return str(path if path.is_absolute() else (workspace_root / path))


def _append_optional(command: list[str], flag: str, value: object) -> None:
    if value is None:
        return
    text = str(value).strip()
    if text:
        command.extend([flag, text])
