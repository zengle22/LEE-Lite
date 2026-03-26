#!/usr/bin/env python3
"""Shared validation helpers for formal test execution skills."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CONFIG = {
    "web": {
        "command": "skill.test-exec-web-e2e",
        "skill_ref": "skill.qa.test_exec_web_e2e",
        "runner_skill_ref": "skill.runner.test_e2e",
        "required_env_keys": {"test_environment_ref"},
        "allowed_run_status": {
            "completed",
            "completed_with_failures",
            "completed_with_warnings",
            "invalid_run",
            "failed",
        },
    },
    "cli": {
        "command": "skill.test-exec-cli",
        "skill_ref": "skill.qa.test_exec_cli",
        "runner_skill_ref": "skill.runner.test_cli",
        "required_env_keys": {"test_environment_ref"},
        "allowed_run_status": {
            "completed",
            "completed_with_failures",
            "completed_with_warnings",
            "invalid_run",
            "failed",
        },
    },
}

REQUIRED_REQUEST_FIELDS = {
    "api_version",
    "command",
    "request_id",
    "workspace_root",
    "actor_ref",
    "trace",
    "payload",
}

REQUIRED_PAYLOAD_FIELDS = {"test_set_ref", "test_environment_ref"}

REQUIRED_RESPONSE_FIELDS = {
    "api_version",
    "command",
    "request_id",
    "result_status",
    "status_code",
    "exit_code",
    "message",
    "data",
}

REQUIRED_DATA_FIELDS = {
    "skill_ref",
    "runner_skill_ref",
    "candidate_artifact_ref",
    "candidate_managed_artifact_ref",
    "candidate_receipt_ref",
    "candidate_registry_record_ref",
    "handoff_ref",
    "run_status",
    "resolved_ssot_context_ref",
    "ui_intent_ref",
    "ui_source_context_ref",
    "ui_binding_map_ref",
    "ui_flow_plan_ref",
    "test_case_pack_ref",
    "test_case_pack_meta_ref",
    "script_pack_ref",
    "script_pack_meta_ref",
    "raw_runner_output_ref",
    "compliance_result_ref",
    "case_results_ref",
    "results_summary_ref",
    "evidence_bundle_ref",
    "bug_bundle_ref",
    "test_report_ref",
    "output_validation_ref",
    "tse_ref",
}


def fail(message: str) -> int:
    print(f"[ERROR] {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return payload


def ensure_fields(payload: dict, required: set[str], label: str) -> None:
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")


def validate_input(path: Path, modality: str) -> int:
    cfg = CONFIG[modality]
    request = load_json(path)
    ensure_fields(request, REQUIRED_REQUEST_FIELDS, "request")
    if request["api_version"] != "v1":
        raise ValueError("request api_version must be v1")
    if request["command"] != cfg["command"]:
        raise ValueError(f"request command must be {cfg['command']}")
    if not isinstance(request["trace"], dict):
        raise ValueError("request trace must be an object")
    payload = request["payload"]
    if not isinstance(payload, dict):
        raise ValueError("request payload must be an object")
    ensure_fields(payload, REQUIRED_PAYLOAD_FIELDS, "payload")
    for key in ("test_set_ref", "test_environment_ref"):
        if not isinstance(payload[key], str) or not payload[key].strip():
            raise ValueError(f"payload.{key} must be a non-empty string")
    if modality == "web":
        ui_source_spec = payload.get("ui_source_spec")
        if ui_source_spec is not None and not isinstance(ui_source_spec, dict):
            raise ValueError("payload.ui_source_spec must be an object when present")
    print(f"[OK] Input request is valid for {cfg['command']}")
    return 0


def validate_output(path: Path, modality: str) -> int:
    cfg = CONFIG[modality]
    response = load_json(path)
    ensure_fields(response, REQUIRED_RESPONSE_FIELDS, "response")
    if response["api_version"] != "v1":
        raise ValueError("response api_version must be v1")
    if response["command"] != cfg["command"]:
        raise ValueError(f"response command must be {cfg['command']}")
    data = response["data"]
    if not isinstance(data, dict):
        raise ValueError("response.data must be an object")
    ensure_fields(data, REQUIRED_DATA_FIELDS, "response.data")
    if data["skill_ref"] != cfg["skill_ref"]:
        raise ValueError(f"response.data.skill_ref must be {cfg['skill_ref']}")
    if data["runner_skill_ref"] != cfg["runner_skill_ref"]:
        raise ValueError(f"response.data.runner_skill_ref must be {cfg['runner_skill_ref']}")
    if data["run_status"] not in cfg["allowed_run_status"]:
        raise ValueError("response.data.run_status is not recognized")
    for field in sorted(REQUIRED_DATA_FIELDS - {"run_status"}):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"response.data.{field} must be a non-empty string")
    print(f"[OK] Output response is valid for {cfg['command']}")
    return 0


def collect_evidence(path: Path, modality: str) -> int:
    del modality
    response = load_json(path)
    data = response.get("data", {})
    refs = {key: value for key, value in data.items() if key.endswith("_ref")}
    print(json.dumps({"evidence_refs": refs}, ensure_ascii=False, indent=2))
    return 0


def freeze_guard(path: Path, modality: str) -> int:
    validate_output(path, modality)
    response = load_json(path)
    if response["result_status"] != "success":
        raise ValueError("freeze guard requires a successful response envelope")
    run_status = response["data"]["run_status"]
    if run_status == "failed":
        raise ValueError("freeze guard rejects failed runtime execution")
    print(f"[OK] Freeze guard passed with run_status={run_status}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate formal test execution skill requests and responses.")
    parser.add_argument("mode", choices=("validate-input", "validate-output", "collect-evidence", "freeze-guard"))
    parser.add_argument("--modality", choices=sorted(CONFIG), required=True)
    parser.add_argument("path", help="Path to the JSON request or response file")
    args = parser.parse_args()

    path = Path(args.path).resolve()
    if not path.exists():
        return fail(f"file not found: {path}")

    try:
        if args.mode == "validate-input":
            return validate_input(path, args.modality)
        if args.mode == "validate-output":
            return validate_output(path, args.modality)
        if args.mode == "collect-evidence":
            return collect_evidence(path, args.modality)
        return freeze_guard(path, args.modality)
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
