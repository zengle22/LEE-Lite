"""CLI integration for ll-governance-failure-capture."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure
from cli.lib.skill_runtime_paths import resolve_skill_scripts_dir


SKILL_REF = "skill.governance.failure_capture"
RUNNER_SKILL_REF = "skill.runner.governance_failure_capture"
SCRIPT_NAME = "workflow_runtime.py"


def run_failure_capture(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    request_payload = _build_request(workspace_root, trace, request_id, payload)
    result = _invoke_runtime(workspace_root, request_payload)
    ensure(bool(result.get("ok")), "PRECONDITION_FAILED", "failure capture runtime reported failure")
    return _normalize_result(result)


def _build_request(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    request = dict(payload)
    request.setdefault("artifact_type", "failure_capture_request")
    request.setdefault("schema_version", "0.1.0")
    request.setdefault("status", "triaged")
    request.setdefault("repo_root", str(workspace_root))
    request.setdefault("request_id", request_id)
    request.setdefault("trace", trace)
    required = [
        "skill_id",
        "sku",
        "run_id",
        "artifact_id",
        "failure_scope",
        "detected_stage",
        "detected_by",
        "severity",
        "triage_level",
        "symptom_summary",
        "problem_description",
        "failed_artifact_ref",
        "upstream_refs",
        "repair_goal",
    ]
    for field in required:
        ensure(field in request, "INVALID_REQUEST", f"missing skill field: {field}")
    return request


def _invoke_runtime(workspace_root: Path, request_payload: dict[str, Any]) -> dict[str, Any]:
    scripts_dir = resolve_skill_scripts_dir(workspace_root, "l3/ll-governance-failure-capture")
    script_path = scripts_dir / SCRIPT_NAME
    ensure(script_path.exists(), "PRECONDITION_FAILED", f"missing runtime script: {script_path}")
    with tempfile.TemporaryDirectory() as temp_dir:
        request_path = Path(temp_dir) / "failure-capture-request.json"
        request_path.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        command = [
            sys.executable,
            str(script_path),
            "run",
            "--input",
            str(request_path),
            "--repo-root",
            str(workspace_root),
            "--allow-update",
        ]
        completed = subprocess.run(
            command,
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = completed.stdout.strip()
        if completed.returncode != 0:
            message = completed.stderr.strip() or stdout or "failure capture runtime failed"
            raise CommandError("PRECONDITION_FAILED", message)
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise CommandError("INTERNAL_ERROR", "invalid failure capture runtime output", [str(exc), stdout]) from exc


def _normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    files = result.get("files", {})
    ensure(isinstance(files, dict), "INTERNAL_ERROR", "failure capture runtime returned invalid files map")
    canonical_path = str(result.get("capture_manifest_ref") or "").strip()
    ensure(canonical_path, "INTERNAL_ERROR", "failure capture runtime did not return capture_manifest_ref")
    return {
        "canonical_path": canonical_path,
        "skill_ref": SKILL_REF,
        "runner_skill_ref": RUNNER_SKILL_REF,
        "package_kind": str(result.get("package_kind") or ""),
        "package_id": str(result.get("package_id") or ""),
        "package_dir": str(result.get("package_dir") or ""),
        "capture_manifest_ref": canonical_path,
        **files,
    }
