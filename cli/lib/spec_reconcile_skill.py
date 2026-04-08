"""CLI integration for ll-governance-spec-reconcile (ADR-044 Phase 0/1)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure
from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir


SKILL_REF = "skill.governance.spec_reconcile"
RUNNER_SKILL_REF = "skill.runner.governance_spec_reconcile"
SCRIPT_NAME = "workflow_runtime.py"


def run_spec_reconcile(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    request_payload = _build_request(workspace_root, trace, request_id, payload)
    result = _invoke_runtime(workspace_root, request_payload)
    ensure(bool(result.get("ok")), "PRECONDITION_FAILED", "spec reconcile runtime reported failure")
    return _normalize_result(result)


def _build_request(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    request = dict(payload)
    request.setdefault("artifact_type", "spec_reconcile_request")
    request.setdefault("schema_version", "0.1.0")
    request.setdefault("status", "requested")
    request.setdefault("repo_root", str(workspace_root))
    request.setdefault("request_id", request_id)
    request.setdefault("trace", trace)
    ensure("package_dir_ref" in request, "INVALID_REQUEST", "missing skill field: package_dir_ref")
    request.setdefault("queue_ref", "artifacts/reports/governance/spec-backport/spec-backport-queue.json")
    request.setdefault("allow_update", False)
    request.setdefault("decisions", [])
    return request


def _invoke_runtime(workspace_root: Path, request_payload: dict[str, Any]) -> dict[str, Any]:
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "l3/ll-governance-spec-reconcile")
    script_path = scripts_dir / SCRIPT_NAME
    ensure(script_path.exists(), "PRECONDITION_FAILED", f"missing runtime script: {script_path}")
    with tempfile.TemporaryDirectory() as temp_dir:
        request_path = Path(temp_dir) / "spec-reconcile-request.json"
        request_path.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        command = [
            sys.executable,
            str(script_path),
            "run",
            "--input",
            str(request_path),
            "--repo-root",
            str(workspace_root),
        ]
        if request_payload.get("allow_update"):
            command.append("--allow-update")
        completed = subprocess.run(
            command,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = completed.stdout.strip()
        if completed.returncode != 0:
            message = completed.stderr.strip() or stdout or "spec reconcile runtime failed"
            raise CommandError("PRECONDITION_FAILED", message)
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise CommandError("INTERNAL_ERROR", "invalid spec reconcile runtime output", [str(exc), stdout]) from exc


def _normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    files = result.get("files", {})
    ensure(isinstance(files, dict), "INTERNAL_ERROR", "spec reconcile runtime returned invalid files map")
    canonical_path = str(result.get("spec_reconcile_report_ref") or "").strip()
    ensure(canonical_path, "INTERNAL_ERROR", "spec reconcile runtime did not return spec_reconcile_report_ref")
    return {
        "canonical_path": canonical_path,
        "skill_ref": SKILL_REF,
        "runner_skill_ref": RUNNER_SKILL_REF,
        "spec_reconcile_report_ref": canonical_path,
        **files,
    }

