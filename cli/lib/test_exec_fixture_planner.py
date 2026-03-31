"""Fixture planning helpers for requirement-driven test execution."""

from __future__ import annotations

from typing import Any

from .test_exec_traceability import infer_state_model


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value).strip()]


def _default_state_for_case(case: dict[str, Any], state_model: list[dict[str, Any]]) -> str:
    case_family = str(case.get("case_family") or "happy_path")
    if not state_model:
        return "ready"
    states = _as_list(state_model[0].get("states"))
    if not states:
        return "ready"
    if case_family in {"negative_path", "boundary_conditions"}:
        return states[-1]
    if case_family in {"retry_reentry", "state_transition"}:
        return states[min(2, len(states) - 1)]
    if case_family in {"read_only_guard"}:
        return states[0]
    return states[0]


def _seeded_actions(case: dict[str, Any]) -> list[str]:
    actions = [str(case.get("trigger_action") or "").strip()]
    actions.extend(_as_list(case.get("pass_conditions"))[:2])
    actions.extend(_as_list(case.get("fail_conditions"))[:2])
    return [item for item in actions if item]


def plan_fixtures(
    test_set: dict[str, Any],
    case_pack: dict[str, Any],
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    environment = dict(environment or {})
    state_model = infer_state_model(test_set)
    fixtures = []
    for case in case_pack.get("cases", []) or []:
        if not isinstance(case, dict):
            continue
        fixtures.append(
            {
                "case_id": str(case.get("case_id") or ""),
                "functional_area_key": str(case.get("functional_area_key") or ""),
                "case_family": str(case.get("case_family") or "happy_path"),
                "entity_type": state_model[0]["entity"] if state_model else "feature_state",
                "required_state": _default_state_for_case(case, state_model),
                "seed_actions": _seeded_actions(case),
                "boundary_checks": _as_list(case.get("boundary_checks")),
                "environment_markers": {
                    "execution_modality": environment.get("execution_modality", ""),
                    "coverage_mode": environment.get("coverage_mode", ""),
                    "coverage_branch_enabled": bool(environment.get("coverage_branch_enabled")),
                },
            }
        )
    return {
        "artifact_type": "fixture_plan",
        "source_test_set_id": str(test_set.get("test_set_id") or test_set.get("id") or ""),
        "execution_modality": str(environment.get("execution_modality") or test_set.get("execution_modality") or ""),
        "state_model": state_model,
        "fixtures": fixtures,
    }


def build_fixture_plan(
    test_set: dict[str, Any],
    cases: list[dict[str, Any]],
    environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper for integration points that still pass bare cases."""
    return plan_fixtures(test_set, {"cases": cases}, environment)
