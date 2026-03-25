"""Artifact builders for governed test execution."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _checksum(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def resolve_ssot_context(test_set: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_type": "resolved_ssot_context",
        "test_set_id": test_set.get("test_set_id", test_set.get("id", "")),
        "execution_modality": environment.get("execution_modality", ""),
        "title": test_set.get("title", ""),
        "source_refs": test_set.get("source_refs", []),
        "governing_adrs": test_set.get("governing_adrs", []),
        "environment_assumptions": test_set.get("environment_assumptions", []),
        "coverage_scope": test_set.get("coverage_scope", []),
        "risk_focus": test_set.get("risk_focus", []),
        "environment_contract": {
            "execution_modality": environment.get("execution_modality", ""),
            "workdir": environment.get("workdir", "."),
            "timeout_seconds": int(environment.get("timeout_seconds", 30)),
            "base_url": environment.get("base_url"),
            "browser": environment.get("browser"),
            "headless": environment.get("headless"),
            "has_command_entry": bool(environment.get("command_entry") or environment.get("runner_command")),
        },
    }


def _normalize_ui_steps(unit: dict[str, Any]) -> list[dict[str, Any]]:
    ui_steps = unit.get("ui_steps")
    if isinstance(ui_steps, list):
        return [dict(step) for step in ui_steps if isinstance(step, dict)]
    steps = unit.get("steps")
    if isinstance(steps, list):
        return [dict(step) for step in steps if isinstance(step, dict)]
    return []


def _build_case(test_set: dict[str, Any], unit: dict[str, Any]) -> dict[str, Any]:
    case = {
        "case_id": unit.get("unit_ref", ""),
        "title": unit.get("title", ""),
        "priority": unit.get("priority", "P1"),
        "preconditions": unit.get("input_preconditions", unit.get("preconditions", [])),
        "trigger_action": unit.get("trigger_action", ""),
        "pass_conditions": unit.get("pass_conditions", []),
        "fail_conditions": unit.get("fail_conditions", []),
        "required_evidence": unit.get("required_evidence", []),
        "acceptance_ref": unit.get("acceptance_ref", ""),
        "supporting_refs": unit.get("supporting_refs", []),
        "observation_points": unit.get("observation_points", []),
        "selectors": unit.get("selectors", {}),
        "ui_steps": _normalize_ui_steps(unit),
        "page_path": unit.get("page_path", ""),
        "expected_url": unit.get("expected_url", ""),
        "expected_text": unit.get("expected_text", ""),
        "test_data": unit.get("test_data", {}),
        "source_traceability": {
            "feat_ref": test_set.get("feat_ref", ""),
            "epic_ref": test_set.get("epic_ref", ""),
            "src_ref": test_set.get("src_ref", ""),
            "governing_adrs": test_set.get("governing_adrs", []),
        },
    }
    return case


def build_test_case_pack(test_set: dict[str, Any]) -> dict[str, Any]:
    cases = [_build_case(test_set, unit) for unit in test_set.get("test_units", [])]
    return {
        "artifact_type": "test_case_pack",
        "source_test_set_id": test_set.get("test_set_id", test_set.get("id", "")),
        "execution_modality": test_set.get("execution_modality"),
        "cases": cases,
    }


def build_script_pack(action: str, environment: dict[str, Any], case_pack: dict[str, Any]) -> dict[str, Any]:
    command_entry = str(environment.get("command_entry", environment.get("runner_command", "")))
    is_web = action == "test-exec-web-e2e"
    bindings = []
    for case in case_pack["cases"]:
        bindings.append(
            {
                "case_id": case["case_id"],
                "command_entry": command_entry if not is_web else "",
                "expected_outcome": "page_load_visible_body" if is_web else "exit_code_zero",
                "page_path": case.get("page_path", ""),
                "expected_url": case.get("expected_url", ""),
                "expected_text": case.get("expected_text", ""),
                "ui_step_count": len(case.get("ui_steps", [])),
            }
        )
    return {
        "artifact_type": "script_pack",
        "execution_modality": environment.get("execution_modality", ""),
        "framework": "playwright" if is_web else "shell",
        "runner_skill_ref": "skill.runner.test_e2e" if is_web else "skill.runner.test_cli",
        "runner_config": {
            "command_entry": command_entry,
            "workdir": str(environment.get("workdir", ".")),
            "timeout_seconds": int(environment.get("timeout_seconds", 30)),
            "base_url": environment.get("base_url"),
            "browser": environment.get("browser"),
        },
        "bindings": bindings,
    }


def build_freeze_meta(artifact_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    count = len(payload.get("cases", payload.get("bindings", [])))
    return {
        "artifact_type": f"{artifact_type}_meta",
        "status": "frozen",
        "item_count": count,
        "checksum": _checksum(payload),
    }


def render_report(summary: dict[str, Any], compliance: dict[str, Any], case_results: list[dict[str, Any]]) -> str:
    lines = [
        "# Test Report",
        "",
        f"- run_status: {summary['run_status']}",
        f"- compliance_status: {compliance['status']}",
        f"- passed: {summary['passed']}",
        f"- failed: {summary['failed']}",
        f"- blocked: {summary['blocked']}",
        f"- invalid: {summary['invalid']}",
        f"- not_executed: {summary['not_executed']}",
        "",
        "## Case Results",
    ]
    for item in case_results:
        lines.append(f"- {item['case_id']}: {item['status']} ({item['actual']})")
    return "\n".join(lines) + "\n"
