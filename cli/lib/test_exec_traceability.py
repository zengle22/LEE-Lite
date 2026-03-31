"""Traceability helpers for TESTSET-driven case expansion."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


def normalize_functional_areas(test_set: dict[str, Any]) -> list[dict[str, Any]]:
    areas = test_set.get("functional_areas", [])
    normalized: list[dict[str, Any]] = []
    if not isinstance(areas, list):
        return normalized
    for item in areas:
        if isinstance(item, dict):
            key = str(item.get("key", "")).strip()
            if not key:
                continue
            normalized.append(
                {
                    "key": key,
                    "kind": str(item.get("kind", "functional_area")).strip() or "functional_area",
                    "description": str(item.get("description", "")).strip(),
                    "related_entities": _list_of_strings(item.get("related_entities", [])),
                    "related_commands": _list_of_strings(item.get("related_commands", [])),
                }
            )
            continue
        key = str(item).strip()
        if key:
            normalized.append(
                {
                    "key": key,
                    "kind": "functional_area",
                    "description": "",
                    "related_entities": [],
                    "related_commands": [],
                }
            )
    return normalized


def normalize_logic_dimensions(test_set: dict[str, Any]) -> dict[str, list[str]]:
    raw = test_set.get("logic_dimensions", {})
    default = {
        "universal": ["happy_path", "invalid_input", "boundary_conditions"],
        "stateful": ["valid_transition", "invalid_transition", "retry_reentry"],
        "control_surface": ["authorized_action", "rejected_action", "read_only_guard"],
    }
    if not isinstance(raw, dict):
        return default
    normalized: dict[str, list[str]] = {}
    for key, fallback in default.items():
        normalized[key] = _list_of_strings(raw.get(key, fallback)) or list(fallback)
    return normalized


def normalize_state_model(test_set: dict[str, Any]) -> list[dict[str, Any]]:
    raw = test_set.get("state_model", [])
    normalized: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return normalized
    for item in raw:
        if not isinstance(item, dict):
            continue
        entity = str(item.get("entity", "")).strip()
        if not entity:
            continue
        valid_transitions = []
        for transition in item.get("valid_transitions", []):
            if isinstance(transition, list) and len(transition) == 2:
                valid_transitions.append([str(transition[0]), str(transition[1])])
        guarded_actions = []
        for action in item.get("guarded_actions", []):
            if not isinstance(action, dict):
                continue
            guarded_actions.append(
                {
                    "command": str(action.get("command", "")).strip(),
                    "allowed_in": _list_of_strings(action.get("allowed_in", [])),
                    "rejected_in": _list_of_strings(action.get("rejected_in", [])),
                }
            )
        normalized.append(
            {
                "entity": entity,
                "states": _list_of_strings(item.get("states", [])),
                "valid_transitions": valid_transitions,
                "guarded_actions": guarded_actions,
            }
        )
    return normalized


def normalize_coverage_matrix(test_set: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    raw = test_set.get("coverage_matrix", {})
    if not isinstance(raw, dict):
        raw = {}
    normalized = {
        "acceptances": [],
        "risks": [],
        "functional_areas": [],
    }
    for key in normalized:
        values = raw.get(key, [])
        if not isinstance(values, list):
            continue
        normalized[key] = [dict(item) for item in values if isinstance(item, dict)]
    return normalized


def build_case_traceability(
    test_set: dict[str, Any],
    unit: dict[str, Any],
    functional_areas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    functional_areas = functional_areas if functional_areas is not None else infer_functional_areas(test_set)
    area_key = str(unit.get("functional_area_key", "")).strip()
    if not area_key and functional_areas:
        area_key = str(functional_areas[0].get("key", "")).strip()
    area = next((item for item in functional_areas if item["key"] == area_key), None)
    acceptance_refs = _list_of_strings(unit.get("acceptance_refs", []))
    if not acceptance_refs and unit.get("acceptance_ref"):
        acceptance_refs = [str(unit.get("acceptance_ref"))]
    risk_refs = _list_of_strings(unit.get("risk_refs", [])) or _list_of_strings(test_set.get("risk_focus", []))[:2]
    title_text = " ".join(
        [
            str(unit.get("title", "")),
            str(unit.get("trigger_action", "")),
            " ".join(_list_of_strings(unit.get("pass_conditions", []))),
            " ".join(_list_of_strings(unit.get("fail_conditions", []))),
        ]
    ).lower()
    case_family = str(unit.get("case_family", "")).strip() or "happy_path"
    if case_family == "happy_path" and any(marker in title_text for marker in ["run", "claim", "approve", "complete", "dispatch", "formal", "transition"]):
        case_family = "state_transition"
    if case_family == "happy_path" and any(marker in title_text for marker in ["monitor", "read only", "snapshot", "observability"]):
        case_family = "read_only_guard"
    if case_family == "happy_path" and any(marker in title_text for marker in ["retry", "resume", "re-entry", "reentry"]):
        case_family = "retry_reentry"
    return {
        "functional_area_key": area_key,
        "functional_area": area or {"key": area_key, "kind": "functional_area", "description": "", "related_entities": [], "related_commands": []},
        "case_family": case_family,
        "logic_dimensions": _list_of_strings(unit.get("logic_dimensions", [])),
        "acceptance_refs": acceptance_refs,
        "risk_refs": risk_refs,
        "boundary_checks": _list_of_strings(unit.get("boundary_checks", [])),
    }


def summarize_case_traceability(cases: list[dict[str, Any]]) -> dict[str, Any]:
    acceptance_map: dict[str, list[str]] = defaultdict(list)
    risk_map: dict[str, list[str]] = defaultdict(list)
    area_map: dict[str, dict[str, Any]] = {}
    family_map: dict[str, int] = defaultdict(int)
    for case in cases:
        case_id = str(case.get("case_id", ""))
        traceability = case.get("traceability", {})
        if not isinstance(traceability, dict):
            continue
        functional_area = traceability.get("functional_area", {})
        if isinstance(functional_area, dict):
            area_key = str(functional_area.get("key", "")).strip()
            if area_key:
                area_map.setdefault(
                    area_key,
                    {
                        "key": area_key,
                        "kind": str(functional_area.get("kind", "functional_area")),
                        "case_ids": [],
                    },
                )
                area_map[area_key]["case_ids"].append(case_id)
        family = str(traceability.get("case_family", "")).strip()
        if family:
            family_map[family] += 1
        for acceptance_ref in _list_of_strings(traceability.get("acceptance_refs", [])):
            acceptance_map[acceptance_ref].append(case_id)
        for risk_ref in _list_of_strings(traceability.get("risk_refs", [])):
            risk_map[risk_ref].append(case_id)
    return {
        "acceptance_traceability": [{"acceptance_ref": key, "case_ids": value} for key, value in acceptance_map.items()],
        "risk_traceability": [{"risk_ref": key, "case_ids": value} for key, value in risk_map.items()],
        "functional_area_traceability": list(area_map.values()),
        "case_family_counts": dict(family_map),
    }


def infer_functional_areas(test_set: dict[str, Any]) -> list[dict[str, Any]]:
    areas = normalize_functional_areas(test_set)
    if areas:
        return areas
    path_text = " ".join(_list_of_strings(test_set.get("feature_owned_code_paths", []))).lower()
    title_text = str(test_set.get("title", "")).lower()
    if any(marker in path_text for marker in ["runner_entry", "execution_runner", "job_queue", "runner_monitor"]) or "runner" in title_text:
        return [
            {
                "key": "execution_runner_surface",
                "kind": "control_surface",
                "description": str(test_set.get("title", "")).strip(),
                "related_entities": ["execution_job", "runner_context"],
                "related_commands": ["loop.run-execution", "job.claim", "job.run", "loop.recover-jobs"],
            }
        ]
    if any(marker in path_text for marker in ["gate", "formal", "managed_gateway", "pilot_chain"]) or any(marker in title_text for marker in ["gate", "formal", "pilot", "adoption"]):
        return [
            {
                "key": "governed_feature_surface",
                "kind": "control_surface",
                "description": str(test_set.get("title", "")).strip(),
                "related_entities": ["candidate_package", "gate_decision", "formal_object"],
                "related_commands": ["gate.decide", "gate.materialize", "registry.validate-admission"],
            }
        ]
    return [
        {
            "key": "feature_surface",
            "kind": "functional_area",
            "description": str(test_set.get("title", "")).strip(),
            "related_entities": [],
            "related_commands": [],
        }
    ]


def infer_logic_dimensions(test_set: dict[str, Any]) -> dict[str, list[str]]:
    dimensions = normalize_logic_dimensions(test_set)
    if dimensions:
        return dimensions
    return {
        "universal": ["happy_path", "invalid_input", "boundary_conditions"],
        "stateful": ["valid_transition", "invalid_transition", "retry_reentry"],
        "control_surface": ["authorized_action", "rejected_action", "read_only_guard"],
    }


def infer_state_model(test_set: dict[str, Any]) -> list[dict[str, Any]]:
    models = normalize_state_model(test_set)
    if models:
        return models
    path_text = " ".join(_list_of_strings(test_set.get("feature_owned_code_paths", []))).lower()
    title_text = str(test_set.get("title", "")).lower()
    if any(marker in path_text for marker in ["runner", "job_queue", "job_state", "execution_runner"]) or "runner" in title_text:
        return [
            {
                "entity": "execution_job",
                "states": ["ready", "claimed", "running", "waiting_human", "failed", "deadletter"],
                "valid_transitions": [["ready", "claimed"], ["claimed", "running"], ["running", "waiting_human"], ["running", "failed"]],
                "guarded_actions": [
                    {"command": "job.claim", "allowed_in": ["ready"], "rejected_in": ["claimed", "running", "waiting_human", "deadletter"]},
                    {"command": "job.run", "allowed_in": ["claimed", "running"], "rejected_in": ["ready", "waiting_human", "deadletter"]},
                    {"command": "job.fail", "allowed_in": ["running", "waiting_human"], "rejected_in": ["ready", "claimed", "deadletter"]},
                ],
            }
        ]
    if any(marker in path_text for marker in ["gate", "formal", "pilot", "rollout"]) or any(marker in title_text for marker in ["gate", "formal", "pilot", "adoption"]):
        return [
            {
                "entity": "candidate_package",
                "states": ["draft", "pending_gate", "approved", "formalized", "rejected"],
                "valid_transitions": [["draft", "pending_gate"], ["pending_gate", "approved"], ["approved", "formalized"], ["pending_gate", "rejected"]],
                "guarded_actions": [
                    {"command": "gate.decide", "allowed_in": ["pending_gate"], "rejected_in": ["approved", "formalized", "rejected"]},
                    {"command": "gate.materialize", "allowed_in": ["approved"], "rejected_in": ["draft", "pending_gate", "rejected"]},
                ],
            }
        ]
    return [
        {
            "entity": "feature_state",
            "states": ["draft", "ready", "validated"],
            "valid_transitions": [["draft", "ready"], ["ready", "validated"]],
            "guarded_actions": [],
        }
    ]


def trace_unit(test_set: dict[str, Any], unit: dict[str, Any]) -> dict[str, Any]:
    """Build traceability info for a single test unit."""
    functional_areas = infer_functional_areas(test_set)
    return build_case_traceability(test_set, unit, functional_areas)


def build_traceability_matrix(
    test_set: dict[str, Any],
    cases: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a traceability matrix linking test set to cases."""
    functional_areas = infer_functional_areas(test_set)
    coverage_matrix = normalize_coverage_matrix(test_set)
    if cases is None:
        cases = [dict(unit) for unit in test_set.get("test_units", []) if isinstance(unit, dict)]

    acceptance_rows: list[dict[str, Any]] = []
    acceptance_map: dict[str, list[str]] = defaultdict(list)
    unit_rows: list[dict[str, Any]] = []

    for case in cases:
        case_id = str(case.get("case_id", ""))
        acceptance_refs = _list_of_strings(case.get("acceptance_refs", [])) or _list_of_strings(case.get("acceptance_ref", []))
        case_family = str(case.get("case_family", "")).strip() or "happy_path"
        logic_dimensions = _list_of_strings(case.get("logic_dimensions", []))
        if not logic_dimensions:
            if case_family in {"read_only_guard"}:
                logic_dimensions = ["control_surface:read_only_guard"]
            elif case_family in {"retry_reentry"}:
                logic_dimensions = ["stateful:retry_reentry"]
            elif case_family in {"negative_path", "boundary_conditions"}:
                logic_dimensions = ["universal:boundary_conditions"]
            elif case_family in {"state_transition"}:
                logic_dimensions = ["stateful:valid_transition"]
            else:
                logic_dimensions = ["universal:happy_path"]
        unit_rows.append(
            {
                "case_id": case_id,
                "functional_area_key": str(case.get("functional_area_key", "")),
                "case_family": case_family,
                "logic_dimensions": logic_dimensions,
                "acceptance_refs": acceptance_refs,
                "risk_refs": _list_of_strings(case.get("risk_refs", [])),
            }
        )
        for acc_ref in acceptance_refs:
            acceptance_map[acc_ref].append(case_id)

    for acc_ref, case_ids in acceptance_map.items():
        acceptance_rows.append({"acceptance_ref": acc_ref, "case_ids": case_ids, "covered_by_case": bool(case_ids)})

    return {
        "artifact_type": "traceability_matrix",
        "acceptance_rows": acceptance_rows,
        "unit_rows": unit_rows,
        "functional_areas": functional_areas,
        "logic_dimensions": infer_logic_dimensions(test_set),
        "state_model": infer_state_model(test_set),
        "coverage_matrix": coverage_matrix,
    }
