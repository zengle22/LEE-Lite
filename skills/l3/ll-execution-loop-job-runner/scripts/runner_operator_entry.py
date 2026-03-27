#!/usr/bin/env python3
"""Canonical skill wrapper for the execution loop job runner."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

SKILL_COMMAND = "skill.execution-loop-job-runner"
SKILL_REF = "skill.execution_loop_job_runner"
RUNNER_SKILL_REF = "skill.runner.execution_loop_job_runner"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _resolve_workspace_root(request_root: str | None, arg_root: str | None, request_path: Path) -> Path:
    root_value = arg_root or request_root or str(request_path.parent)
    return Path(root_value).resolve()


def _to_canonical_path(path: Path, workspace_root: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _load_request(path: Path, workspace_root: str | None) -> tuple[dict[str, Any], Path]:
    request = _load_json(path)
    root = _resolve_workspace_root(str(request.get("workspace_root") or ""), workspace_root, path)
    return request, root


def _entry_mode(payload: dict[str, Any]) -> str:
    return str(payload.get("entry_mode") or "").strip().lower()


def _delegated_action(request: dict[str, Any]) -> str:
    payload = request.get("payload", {})
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    mode = _entry_mode(payload)
    if mode not in {"start", "resume"}:
        raise ValueError("entry_mode must be start or resume")
    return "resume-execution" if mode == "resume" else "run-execution"


def _delegated_request(request: dict[str, Any], action: str) -> dict[str, Any]:
    payload = dict(request)
    payload["command"] = f"loop.{action}"
    return payload


def _skill_response(request: dict[str, Any], delegated: dict[str, Any], action: str) -> dict[str, Any]:
    data = dict(delegated.get("data") or {})
    payload = request.get("payload", {})
    mode = "resume" if action == "resume-execution" else "start"
    data.update(
        {
            "canonical_path": str(data.get("entry_receipt_ref") or data.get("canonical_path") or ""),
            "skill_ref": SKILL_REF,
            "runner_skill_ref": RUNNER_SKILL_REF,
            "entry_mode": mode,
            "runner_scope_ref": str(data.get("runner_scope_ref") or payload.get("runner_scope_ref") or ""),
            "delegated_command_ref": f"ll loop {action}",
        }
    )
    return {
        **delegated,
        "command": SKILL_COMMAND,
        "message": f"execution runner canonical skill {mode} completed" if delegated.get("status_code") == "OK" else delegated.get("message", ""),
        "data": data,
    }


def _invalid_request_response(request: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    return {
        "api_version": "v1",
        "command": SKILL_COMMAND,
        "request_id": str(request.get("request_id") or ""),
        "result_status": "failed",
        "status_code": "INVALID_REQUEST",
        "exit_code": 2,
        "message": errors[0],
        "data": {
            "canonical_path": "",
            "skill_ref": SKILL_REF,
            "runner_skill_ref": RUNNER_SKILL_REF,
            "entry_mode": _entry_mode(request.get("payload", {}) if isinstance(request.get("payload"), dict) else {}),
            "runner_scope_ref": str((request.get("payload", {}) if isinstance(request.get("payload"), dict) else {}).get("runner_scope_ref") or ""),
            "delegated_command_ref": "",
        },
        "diagnostics": errors,
        "evidence_refs": [],
    }


def _invoke(args: argparse.Namespace) -> int:
    request_path = Path(args.request).resolve()
    response_path = Path(args.response_out)
    request, workspace_root = _load_request(request_path, args.workspace_root)
    if not response_path.is_absolute():
        response_path = workspace_root / response_path
    errors = _validate_request_envelope(request)
    if errors:
        _write_json(response_path, _invalid_request_response(request, errors))
        return 2
    action = _delegated_action(request)
    import sys

    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))
    from cli.ll import main as ll_main

    with tempfile.TemporaryDirectory() as temp_dir:
        delegated_request_path = Path(temp_dir) / "delegated-request.json"
        delegated_response_path = Path(temp_dir) / "delegated-response.json"
        persisted_delegated_ref = ""
        _write_json(delegated_request_path, _delegated_request(request, action))
        exit_code = ll_main(
            [
                "loop",
                action,
                "--request",
                str(delegated_request_path),
                "--response-out",
                str(delegated_response_path),
                *([] if not args.workspace_root else ["--workspace-root", args.workspace_root]),
                *(["--strict"] if args.strict else []),
            ]
        )
        delegated_response = _load_json(delegated_response_path)
        response = _skill_response(request, delegated_response, action)
        _write_json(response_path, response)
        if args.evidence_out:
            evidence_path = Path(args.evidence_out)
            if not evidence_path.is_absolute():
                evidence_path = workspace_root / evidence_path
            delegated_copy = workspace_root / "artifacts" / "active" / "runner" / "delegated-responses" / f"{request['request_id']}.json"
            _write_json(delegated_copy, delegated_response)
            persisted_delegated_ref = _to_canonical_path(delegated_copy, workspace_root)
            _write_json(
                evidence_path,
                {
                    "command": SKILL_COMMAND,
                    "request_id": request["request_id"],
                    "response_ref": _to_canonical_path(response_path, workspace_root),
                    "delegated_response_ref": persisted_delegated_ref,
                    "trace": request.get("trace", {}),
                },
            )
        return exit_code


def _validate_request_envelope(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("api_version", "command", "request_id", "workspace_root", "actor_ref", "trace", "payload"):
        if field not in payload:
            errors.append(f"missing field: {field}")
    if payload.get("command") != SKILL_COMMAND:
        errors.append(f"command must be {SKILL_COMMAND}")
    if not isinstance(payload.get("payload"), dict):
        errors.append("payload must be an object")
    else:
        mode = _entry_mode(payload["payload"])
        if mode not in {"start", "resume"}:
            errors.append("payload.entry_mode must be start or resume")
        if not str(payload["payload"].get("runner_scope_ref") or "").strip():
            errors.append("payload.runner_scope_ref is required")
    return errors


def _validate_input(args: argparse.Namespace) -> int:
    request, _ = _load_request(Path(args.request).resolve(), args.workspace_root)
    errors = _validate_request_envelope(request)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def _validate_output_fields(response: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if response.get("command") != SKILL_COMMAND:
        errors.append(f"command must be {SKILL_COMMAND}")
    for field in ("result_status", "status_code", "exit_code", "message", "data"):
        if field not in response:
            errors.append(f"missing field: {field}")
    data = response.get("data")
    if not isinstance(data, dict):
        errors.append("data must be an object")
        return errors
    required = [
        ("skill_ref", SKILL_REF),
        ("runner_skill_ref", RUNNER_SKILL_REF),
        ("entry_mode", None),
        ("delegated_command_ref", None),
        ("runner_run_ref", None),
        ("runner_context_ref", None),
        ("entry_receipt_ref", None),
        ("runner_scope_ref", None),
    ]
    for field, exact in required:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"data.{field} is required")
        elif exact and value != exact:
            errors.append(f"data.{field} must be {exact}")
    return errors


def _validate_output(args: argparse.Namespace) -> int:
    response = _load_json(Path(args.response).resolve())
    errors = _validate_output_fields(response)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical execution loop job runner skill wrapper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    invoke = subparsers.add_parser("invoke")
    invoke.add_argument("--request", required=True)
    invoke.add_argument("--response-out", required=True)
    invoke.add_argument("--evidence-out")
    invoke.add_argument("--workspace-root")
    invoke.add_argument("--strict", action="store_true")
    invoke.set_defaults(func=_invoke)

    validate_input = subparsers.add_parser("validate-input")
    validate_input.add_argument("--request", required=True)
    validate_input.add_argument("--workspace-root")
    validate_input.set_defaults(func=_validate_input)

    validate_output = subparsers.add_parser("validate-output")
    validate_output.add_argument("--response", required=True)
    validate_output.set_defaults(func=_validate_output)

    freeze_guard = subparsers.add_parser("freeze-guard")
    freeze_guard.add_argument("--response", required=True)
    freeze_guard.set_defaults(func=_validate_output)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
