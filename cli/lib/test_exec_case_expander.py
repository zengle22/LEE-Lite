"""Requirement-driven case expansion helpers for test execution."""

from __future__ import annotations

import re
from typing import Any

from .test_exec_traceability import (
    build_traceability_matrix,
    build_case_traceability,
    infer_functional_areas,
    infer_logic_dimensions,
    infer_state_model,
)


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "case"


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value).strip()]


def _case_family(unit: dict[str, Any]) -> str:
    corpus = " ".join(
        [
            str(unit.get("title") or ""),
            str(unit.get("trigger_action") or ""),
            " ".join(_as_list(unit.get("pass_conditions"))),
            " ".join(_as_list(unit.get("observation_points"))),
        ]
    ).lower()
    if any(token in corpus for token in ["retry", "re-entry", "reentry", "resume"]):
        return "retry_reentry"
    if any(token in corpus for token in ["claim", "run", "dispatch", "approve", "complete", "materialize", "formal", "transition"]):
        return "state_transition"
    if any(token in corpus for token in ["read only", "monitor", "observability", "snapshot"]):
        return "read_only_guard"
    if any(token in corpus for token in ["reject", "blocked", "invalid", "missing", "conflict", "fail closed", "denied"]):
        return "negative_path"
    if any(token in corpus for token in ["boundary", "deferred", "skip", "non-blocking"]):
        return "boundary_conditions"
    return "happy_path"


def _logic_dimensions_for_case(case_family: str, logic_dimensions: dict[str, list[str]]) -> list[str]:
    selected = [f"universal:{item}" for item in logic_dimensions.get("universal", [])[:2]]
    if case_family in {"negative_path", "boundary_conditions"}:
        selected.extend(f"universal:{item}" for item in logic_dimensions.get("universal", [])[2:3])
    if case_family in {"state_transition", "retry_reentry"}:
        selected.extend(f"stateful:{item}" for item in logic_dimensions.get("stateful", [])[:2])
    if case_family in {"read_only_guard", "negative_path"}:
        selected.extend(f"control_surface:{item}" for item in logic_dimensions.get("control_surface", [])[:2])
    return list(dict.fromkeys(selected))


def _area_key_for_unit(test_set: dict[str, Any], unit: dict[str, Any]) -> str:
    functional_areas = infer_functional_areas(test_set)
    if unit.get("functional_area_key"):
        return str(unit.get("functional_area_key"))
    if functional_areas:
        return str(functional_areas[0].get("key") or "feature_surface")
    return "feature_surface"


def _risk_refs_for_unit(test_set: dict[str, Any], unit: dict[str, Any]) -> list[str]:
    refs = _as_list(unit.get("risk_refs"))
    if refs:
        return refs
    return _as_list(test_set.get("risk_focus"))[:2]


def _boundary_checks_for_unit(unit: dict[str, Any]) -> list[str]:
    checks = _as_list(unit.get("boundary_checks"))
    if checks:
        return checks
    case_family = str(unit.get("case_family") or _case_family(unit))
    inferred = _as_list(unit.get("pass_conditions"))[:2] + _as_list(unit.get("fail_conditions"))[:2]
    if case_family == "read_only_guard":
        return [f"read_only_guard:{item}" for item in inferred] or ["read_only_guard:default"]
    return inferred


def _build_case(
    test_set: dict[str, Any],
    unit: dict[str, Any],
    *,
    projection_mode: str,
    qualification_round: int,
    qualification_family: str = "",
) -> dict[str, Any]:
    case_family = str(unit.get("case_family") or _case_family(unit))
    logic_dimensions = unit.get("logic_dimensions")
    if not isinstance(logic_dimensions, list) or not logic_dimensions:
        logic_dimensions = _logic_dimensions_for_case(case_family, infer_logic_dimensions(test_set))
    derivation_basis = unit.get("derivation_basis")
    if qualification_family:
        derivation_basis = "qualification_expansion"
    elif not derivation_basis:
        derivation_basis = "test_unit"
    case = {
        "case_id": str(unit.get("unit_ref") or ""),
        "title": str(unit.get("title") or ""),
        "priority": str(unit.get("priority") or "P1"),
        "functional_area_key": _area_key_for_unit(test_set, unit),
        "case_family": case_family,
        "logic_dimensions": logic_dimensions,
        "acceptance_ref": str(unit.get("acceptance_ref") or ""),
        "acceptance_refs": _as_list(unit.get("acceptance_refs")) or _as_list(unit.get("acceptance_ref")),
        "risk_refs": _risk_refs_for_unit(test_set, unit),
        "boundary_checks": _boundary_checks_for_unit(unit),
        "preconditions": _as_list(unit.get("input_preconditions") or unit.get("preconditions")),
        "trigger_action": str(unit.get("trigger_action") or ""),
        "pass_conditions": _as_list(unit.get("pass_conditions")),
        "fail_conditions": _as_list(unit.get("fail_conditions")),
        "required_evidence": _as_list(unit.get("required_evidence")),
        "supporting_refs": _as_list(unit.get("supporting_refs")),
        "observation_points": _as_list(unit.get("observation_points")),
        "selectors": dict(unit.get("selectors") or {}),
        "ui_steps": list(unit.get("ui_steps") or []),
        "page_path": str(unit.get("page_path") or ""),
        "expected_url": str(unit.get("expected_url") or ""),
        "expected_text": str(unit.get("expected_text") or ""),
        "test_data": dict(unit.get("test_data") or {}),
        "source_traceability": {
            "feat_ref": str(test_set.get("feat_ref") or ""),
            "epic_ref": str(test_set.get("epic_ref") or ""),
            "src_ref": str(test_set.get("src_ref") or ""),
            "governing_adrs": _as_list(test_set.get("governing_adrs")),
        },
        "derivation_basis": derivation_basis,
        "derivation_tags": [projection_mode, "requirement_driven_expansion"],
    }
    if case["acceptance_ref"]:
        case["acceptance_refs"] = list(dict.fromkeys(case["acceptance_refs"] + [case["acceptance_ref"]]))
    if qualification_round:
        case["qualification_round"] = qualification_round
    if qualification_family:
        case["qualification_family"] = qualification_family
    case["traceability"] = build_case_traceability(
        test_set,
        {
            "functional_area_key": case["functional_area_key"],
            "case_family": case["case_family"],
            "logic_dimensions": case["logic_dimensions"],
            "acceptance_refs": case["acceptance_refs"],
            "risk_refs": case["risk_refs"],
            "boundary_checks": case["boundary_checks"],
        },
        infer_functional_areas(test_set),
    )
    return case


def _select_source_unit(units: list[dict[str, Any]], expansion_target: str) -> dict[str, Any]:
    if not units:
        return {}
    tokens = {token for token in re.split(r"[^a-z0-9]+", expansion_target.lower()) if token}
    if not tokens:
        return units[0]
    best_unit = units[0]
    best_score = -1
    for unit in units:
        corpus = " ".join(
            [
                str(unit.get("unit_ref") or ""),
                str(unit.get("title") or ""),
                str(unit.get("trigger_action") or ""),
                str(unit.get("page_path") or ""),
                str(unit.get("expected_url") or ""),
                str(unit.get("expected_text") or ""),
                " ".join(_as_list(unit.get("supporting_refs"))),
                " ".join(_as_list(unit.get("observation_points"))),
                " ".join(_as_list(unit.get("pass_conditions"))),
                " ".join(_as_list(unit.get("fail_conditions"))),
            ]
        ).lower()
        unit_tokens = {token for token in re.split(r"[^a-z0-9]+", corpus) if token}
        score = len(tokens & unit_tokens)
        if str(unit.get("page_path") or "").lower() in expansion_target.lower():
            score += 1
        if str(unit.get("expected_url") or "").lower() in expansion_target.lower():
            score += 1
        if str(unit.get("expected_text") or "").lower() in expansion_target.lower():
            score += 1
        if score > best_score:
            best_score = score
            best_unit = unit
    return best_unit


def expand_requirement_cases(
    test_set: dict[str, Any],
    environment: dict[str, Any] | None = None,
    *,
    projection_mode: str = "minimal_projection",
    qualification_round: int = 0,
    qualification_lineage: list[dict[str, Any]] | None = None,
    qualification_budget: int | None = None,
    max_expansion_rounds: int | None = None,
    expansion_targets: list[str] | None = None,
) -> dict[str, Any]:
    environment = dict(environment or {})
    units = [unit for unit in test_set.get("test_units", []) if isinstance(unit, dict)]
    functional_areas = infer_functional_areas(test_set)
    logic_dimensions = infer_logic_dimensions(test_set)
    state_model = infer_state_model(test_set)
    cases = [_build_case(test_set, unit, projection_mode=projection_mode, qualification_round=0) for unit in units]
    traceability_matrix = build_traceability_matrix(test_set, cases)
    if projection_mode == "qualification_expansion":
        sources = [str(item).strip() for item in (expansion_targets or []) if str(item).strip()]
        if not sources:
            sources = [str(item).strip() for item in _as_list(test_set.get("branch_families")) + _as_list(test_set.get("expansion_hints")) if str(item).strip()]
        if sources:
            raw_budget = qualification_budget if qualification_budget is not None else environment.get("qualification_budget", test_set.get("qualification_budget", len(units)))
            try:
                budget = max(0, int(raw_budget))
            except (TypeError, ValueError):
                budget = len(units)
            if budget <= len(cases):
                budget = len(cases) + len(sources)
            source_index = 0
            while len(cases) < budget:
                source_text = sources[source_index % len(sources)]
                source_index += 1
                base_unit = _select_source_unit(units, source_text)
                if not base_unit:
                    break
                synthetic = dict(base_unit)
                synthetic["unit_ref"] = f"{base_unit.get('unit_ref', 'QUAL')}-EXP-R{qualification_round}-{_slugify(source_text)}"
                synthetic["title"] = f"{base_unit.get('title', 'qualification')} [R{qualification_round}:{source_text}]"
                synthetic["qualification_family"] = source_text
                synthetic["case_family"] = synthetic.get("case_family") or _case_family(synthetic)
                synthetic["derivation_basis"] = "qualification_expansion"
                cases.append(
                    _build_case(
                        test_set,
                        synthetic,
                        projection_mode=projection_mode,
                        qualification_round=qualification_round,
                        qualification_family=source_text,
                    )
                )
                if len(cases) >= budget:
                    break
    return {
        "artifact_type": "test_case_pack",
        "source_test_set_id": str(test_set.get("test_set_id") or test_set.get("id") or ""),
        "execution_modality": str(environment.get("execution_modality") or test_set.get("execution_modality") or ""),
        "projection_mode": projection_mode,
        "generation_mode": projection_mode,
        "qualification_round": qualification_round if projection_mode == "qualification_expansion" else 0,
        "qualification_revision": qualification_round if projection_mode == "qualification_expansion" else 0,
        "qualification_max_expansion_rounds": int(max_expansion_rounds or test_set.get("max_expansion_rounds") or 0),
        "qualification_plan": {
            "coverage_goal": test_set.get("coverage_goal", {}),
            "branch_families": _as_list(test_set.get("branch_families")),
            "expansion_hints": _as_list(test_set.get("expansion_hints")),
            "qualification_budget": qualification_budget if qualification_budget is not None else test_set.get("qualification_budget"),
            "max_expansion_rounds": max_expansion_rounds if max_expansion_rounds is not None else test_set.get("max_expansion_rounds"),
            "qualification_expectation": str(test_set.get("qualification_expectation") or ""),
            "coverage_mode": str(environment.get("coverage_mode") or ""),
            "coverage_matrix": test_set.get("coverage_matrix") or traceability_matrix.get("acceptance_rows", []),
        },
        "qualification_budget": qualification_budget if qualification_budget is not None else test_set.get("qualification_budget"),
        "qualification_lineage": qualification_lineage or [],
        "expansion_round": qualification_round if projection_mode == "qualification_expansion" else 0,
        "expansion_stop_reason": "qualification_expansion" if projection_mode == "qualification_expansion" else "minimal_projection_only",
        "functional_areas": functional_areas,
        "logic_dimensions": logic_dimensions,
        "state_model": state_model,
        "coverage_matrix": traceability_matrix,
        "cases": cases,
    }


def expand_cases(
    test_set: dict[str, Any],
    environment: dict[str, Any] | None = None,
    *,
    projection_mode: str = "minimal_projection",
    expansion_round: int = 0,
    expansion_targets: list[str] | None = None,
    qualification_lineage: list[dict[str, Any]] | None = None,
    qualification_budget: int | None = None,
    max_expansion_rounds: int | None = None,
) -> dict[str, Any]:
    return expand_requirement_cases(
        test_set,
        environment,
        projection_mode=projection_mode,
        qualification_round=expansion_round,
        qualification_lineage=qualification_lineage,
        qualification_budget=qualification_budget,
        max_expansion_rounds=max_expansion_rounds,
        expansion_targets=expansion_targets,
    )
