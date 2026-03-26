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
SKILL_REF = "skill.gate.human_orchestrator"
RUNNER_SKILL_REF = "skill.runner.gate_human_orchestrator"
SUPPORTED_OPERATIONS = {
    "run",
    "prepare-round",
    "show-pending",
    "claim-next",
    "capture-decision",
    "close-run",
}


def run_gate_human_orchestrator(workspace_root: Path, trace: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    operation = _normalize_operation(payload)
    command = _build_command(workspace_root, trace, payload, operation)
    result = _run(command)
    return _normalize_result(workspace_root, operation, result)


def _build_command(
    workspace_root: Path,
    trace: dict[str, Any],
    payload: dict[str, Any],
    operation: str,
) -> list[str]:
    command = [sys.executable, str(SCRIPT_PATH), operation, "--repo-root", str(workspace_root)]
    run_id = str(payload.get("run_id") or trace.get("run_ref") or "").strip()
    if operation in {"run", "prepare-round", "claim-next"}:
        _append_optional(command, "--run-id", run_id)
    if operation in {"run", "prepare-round"}:
        ensure("input_ref" in payload, "INVALID_REQUEST", "missing skill field: input_ref")
        command.extend(["--input", _resolve_ref(workspace_root, str(payload["input_ref"]))])
    if operation == "run":
        _append_optional(command, "--decision", payload.get("decision"))
        _append_optional(command, "--decision-reason", payload.get("decision_reason"))
        _append_optional(command, "--decision-target", payload.get("decision_target"))
        for ref_value in _string_list(payload.get("audit_finding_refs", [])):
            command.extend(["--audit-finding-ref", ref_value])
    elif operation == "claim-next":
        _append_optional(command, "--actor-ref", payload.get("actor_ref"))
    elif operation == "capture-decision":
        ensure("artifacts_dir" in payload, "INVALID_REQUEST", "missing skill field: artifacts_dir")
        ensure("reply" in payload, "INVALID_REQUEST", "missing skill field: reply")
        ensure("approver" in payload, "INVALID_REQUEST", "missing skill field: approver")
        command.extend(["--artifacts-dir", _resolve_ref(workspace_root, str(payload["artifacts_dir"]))])
        command.extend(["--reply", str(payload["reply"])])
        command.extend(["--approver", str(payload["approver"])])
    elif operation == "close-run":
        ensure("artifacts_dir" in payload, "INVALID_REQUEST", "missing skill field: artifacts_dir")
        command.extend(["--artifacts-dir", _resolve_ref(workspace_root, str(payload["artifacts_dir"]))])
    if payload.get("allow_update"):
        command.append("--allow-update")
    return command


def _normalize_result(workspace_root: Path, operation: str, result: dict[str, Any]) -> dict[str, Any]:
    if operation == "run":
        return _normalize_run_result(result)

    normalized = {
        "skill_ref": SKILL_REF,
        "runner_skill_ref": RUNNER_SKILL_REF,
        "operation": operation,
        **result,
    }
    if operation == "show-pending":
        _promote_single_pending_item(normalized)
    _promote_review_summary_fields(normalized)
    _attach_human_brief_fields(normalized)
    normalized["canonical_path"] = _canonical_path_for_result(workspace_root, operation, normalized)
    return normalized


def _normalize_run_result(result: dict[str, Any]) -> dict[str, Any]:
    artifacts_dir = Path(str(result["artifacts_dir"]))
    bundle_ref = artifacts_dir / "gate-decision-bundle.json"
    bundle = json.loads(bundle_ref.read_text(encoding="utf-8"))
    return {
        "skill_ref": SKILL_REF,
        "runner_skill_ref": RUNNER_SKILL_REF,
        "operation": "run",
        "canonical_path": str(bundle_ref),
        "artifacts_dir": str(artifacts_dir),
        "bundle_ref": str(bundle_ref),
        "decision": result["decision"],
        "decision_ref": bundle["decision_ref"],
        "dispatch_target": bundle["dispatch_target"],
        "human_projection_ref": bundle["human_projection_ref"],
        "projection_status": bundle["projection_status"],
        "machine_ssot_ref": bundle["machine_ssot_ref"],
    }


def _promote_single_pending_item(result: dict[str, Any]) -> None:
    items = result.get("items", [])
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
        return
    item = items[0]
    for field in ("run_id", "artifacts_dir", "decision_target", "request_ref", "review_summary", "human_brief"):
        if field in item and field not in result:
            result[field] = item[field]


def _promote_review_summary_fields(result: dict[str, Any]) -> None:
    review_summary = result.get("review_summary")
    if not isinstance(review_summary, dict):
        return
    for field in ("decision_target", "machine_ssot_ref", "allowed_actions", "reply_examples"):
        if field in review_summary and field not in result:
            result[field] = review_summary[field]


def _attach_human_brief_fields(result: dict[str, Any]) -> None:
    human_brief = result.get("human_brief")
    if isinstance(human_brief, dict):
        markdown = str(human_brief.get("markdown", "")).strip()
        if markdown:
            result["human_brief_markdown"] = markdown
    items = result.get("items")
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        brief = item.get("human_brief")
        if isinstance(brief, dict):
            markdown = str(brief.get("markdown", "")).strip()
            if markdown:
                item["human_brief_markdown"] = markdown


def _canonical_path_for_result(workspace_root: Path, operation: str, result: dict[str, Any]) -> str:
    candidate_refs: list[str] = []
    if operation == "show-pending":
        candidate_refs.append(str(result.get("request_ref", "")))
    elif operation in {"prepare-round", "claim-next"}:
        candidate_refs.extend([str(result.get("request_ref", "")), str(result.get("claim_ref", ""))])
    elif operation == "capture-decision":
        candidate_refs.extend([str(result.get("bundle_ref", "")), str(result.get("submission_ref", ""))])
    elif operation == "close-run":
        candidate_refs.extend([str(result.get("run_closure_ref", "")), str(result.get("artifacts_dir", ""))])
    for ref_value in candidate_refs:
        resolved = _resolve_if_present(workspace_root, ref_value)
        if resolved:
            return resolved
    return str((workspace_root / "artifacts" / "active" / "gates" / "pending" / "index.json").resolve())


def _resolve_if_present(workspace_root: Path, ref_value: str) -> str:
    text = ref_value.strip()
    if not text:
        return ""
    return _resolve_ref(workspace_root, text)


def _normalize_operation(payload: dict[str, Any]) -> str:
    raw_value = payload.get("operation") or payload.get("mode") or payload.get("skill_action") or payload.get("queue_action") or "run"
    operation = str(raw_value).strip().replace("_", "-").lower()
    ensure(operation in SUPPORTED_OPERATIONS, "INVALID_REQUEST", f"unsupported skill operation: {operation}")
    return operation


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
    return str(path if path.is_absolute() else (workspace_root / path).resolve())


def _string_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def _append_optional(command: list[str], flag: str, value: object) -> None:
    if value is None:
        return
    text = str(value).strip()
    if text:
        command.extend([flag, text])
