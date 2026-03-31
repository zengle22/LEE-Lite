"""Script mapping helpers for requirement-driven test execution."""

from __future__ import annotations

from typing import Any


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value).strip()]


def _expected_outcome(case_family: str) -> str:
    if case_family in {"negative_path", "boundary_conditions"}:
        return "exit_code_zero_with_guarded_verdict"
    if case_family in {"read_only_guard"}:
        return "exit_code_zero_with_read_only_verdict"
    return "exit_code_zero"


def map_scripts(
    test_set: dict[str, Any],
    case_pack: dict[str, Any],
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    environment = dict(environment or {})
    command_entry = str(environment.get("command_entry") or environment.get("runner_command") or "")
    bindings = []
    for case in case_pack.get("cases", []) or []:
        if not isinstance(case, dict):
            continue
        case_family = str(case.get("case_family") or "happy_path")
        bindings.append(
            {
                "case_id": str(case.get("case_id") or ""),
                "functional_area_key": str(case.get("functional_area_key") or ""),
                "case_family": case_family,
                "command_entry": command_entry,
                "expected_outcome": _expected_outcome(case_family),
                "fixture_state": str(case.get("fixture_state") or ""),
                "required_state": str(case.get("required_state") or ""),
                "boundary_checks": _as_list(case.get("boundary_checks")),
            }
        )
    return {
        "artifact_type": "script_pack",
        "execution_modality": str(environment.get("execution_modality") or test_set.get("execution_modality") or ""),
        "framework": "shell",
        "runner_skill_ref": "skill.runner.test_cli" if str(environment.get("execution_modality") or "cli") == "cli" else "skill.runner.test_e2e",
        "runner_config": {
            "command_entry": command_entry,
            "workdir": str(environment.get("workdir") or "."),
            "timeout_seconds": int(environment.get("timeout_seconds") or 30),
            "coverage_mode": str(environment.get("coverage_mode") or ""),
            "coverage_enabled": bool(environment.get("coverage_enabled")),
        },
        "bindings": bindings,
    }


def build_script_bindings(
    action: str,
    environment: dict[str, Any],
    cases: list[dict[str, Any]],
    fixture_plan: dict[str, Any] | None = None,
    ui_source_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper for older integration code."""
    execution_modality = "web_e2e" if action == "test-exec-web-e2e" else str(environment.get("execution_modality") or "cli")
    pack = map_scripts(
        {"execution_modality": execution_modality},
        {"cases": cases},
        {**environment, "execution_modality": execution_modality},
    )
    if fixture_plan is not None:
        pack["fixture_plan"] = fixture_plan
    if ui_source_spec is not None:
        pack["runner_config"]["ui_source_spec"] = ui_source_spec
    fixture_index = {item.get("case_id", ""): item for item in (fixture_plan or {}).get("fixtures", []) if isinstance(item, dict)}
    for binding in pack.get("bindings", []):
        binding["fixture"] = fixture_index.get(binding.get("case_id", ""), {})
    return pack

