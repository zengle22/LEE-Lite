"""Artifact builders for governed test execution."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def _checksum(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def normalize_ui_source_spec(payload: dict[str, Any]) -> dict[str, Any]:
    explicit = payload.get("ui_source_spec", {})
    if not isinstance(explicit, dict):
        explicit = {}
    spec = {
        "codebase_ref": explicit.get("codebase_ref", payload.get("frontend_code_ref", "")),
        "runtime_ref": explicit.get("runtime_ref", payload.get("ui_runtime_ref", "")),
        "prototype_ref": explicit.get("prototype_ref", payload.get("ui_prototype_ref", "")),
    }
    return spec


def resolve_ssot_context(test_set: dict[str, Any], environment: dict[str, Any], ui_source_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_type": "resolved_ssot_context",
        "test_set_id": test_set.get("test_set_id", test_set.get("id", "")),
        "execution_modality": environment.get("execution_modality", ""),
        "title": test_set.get("title", ""),
        "source_refs": test_set.get("source_refs", []),
        "governing_adrs": test_set.get("governing_adrs", []),
        "environment_assumptions": test_set.get("environment_assumptions", []),
        "coverage_scope": test_set.get("coverage_scope", []),
        "recommended_coverage_scope_name": test_set.get("recommended_coverage_scope_name", []),
        "feature_owned_code_paths": test_set.get("feature_owned_code_paths", []),
        "coverage_goal": test_set.get("coverage_goal", {}),
        "branch_families": test_set.get("branch_families", []),
        "expansion_hints": test_set.get("expansion_hints", []),
        "qualification_budget": test_set.get("qualification_budget", environment.get("qualification_budget")),
        "max_expansion_rounds": test_set.get("max_expansion_rounds", environment.get("max_expansion_rounds")),
        "qualification_expectation": test_set.get("qualification_expectation", ""),
        "risk_focus": test_set.get("risk_focus", []),
        "ui_source_spec": ui_source_spec,
        "environment_contract": {
            "execution_modality": environment.get("execution_modality", ""),
            "workdir": environment.get("workdir", "."),
            "timeout_seconds": int(environment.get("timeout_seconds", 30)),
            "base_url": environment.get("base_url"),
            "browser": environment.get("browser"),
            "headless": environment.get("headless"),
            "has_command_entry": bool(environment.get("command_entry") or environment.get("runner_command")),
            "coverage_enabled": bool(environment.get("coverage_enabled")),
            "coverage_scope_name": environment.get("coverage_scope_name", []),
            "coverage_include": environment.get("coverage_include", []),
            "coverage_scope_origin": environment.get("coverage_scope_origin", "environment"),
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


def _build_case(
    test_set: dict[str, Any],
    unit: dict[str, Any],
    *,
    derivation_basis: str = "test_unit",
    qualification_round: int = 0,
    qualification_family: str = "",
) -> dict[str, Any]:
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
        "derivation_basis": derivation_basis,
    }
    if qualification_round:
        case["qualification_round"] = qualification_round
    if qualification_family:
        case["qualification_family"] = qualification_family
    return case


def _qualification_plan(test_set: dict[str, Any], environment: dict[str, Any] | None = None) -> dict[str, Any]:
    environment = environment or {}
    qualification_budget = environment.get("qualification_budget", test_set.get("qualification_budget"))
    return {
        "coverage_goal": test_set.get("coverage_goal", {}),
        "branch_families": test_set.get("branch_families", []),
        "expansion_hints": test_set.get("expansion_hints", []),
        "qualification_budget": qualification_budget,
        "max_expansion_rounds": environment.get("max_expansion_rounds", test_set.get("max_expansion_rounds")),
        "qualification_expectation": test_set.get("qualification_expectation", ""),
        "coverage_mode": environment.get("coverage_mode", ""),
        "coverage_branch_enabled": bool(environment.get("coverage_branch_enabled")),
    }


def _tokenize(value: Any) -> set[str]:
    text = str(value or "").lower()
    return {token for token in re.split(r"[^a-z0-9]+", text) if token}


def _select_source_unit(units: list[dict[str, Any]], expansion_target: str) -> dict[str, Any]:
    if not units:
        return {}
    target_tokens = _tokenize(expansion_target)
    if not target_tokens:
        return units[0]
    best_unit = units[0]
    best_score = -1
    for unit in units:
        corpus: list[Any] = [
            unit.get("unit_ref", ""),
            unit.get("title", ""),
            unit.get("trigger_action", ""),
            unit.get("acceptance_ref", ""),
            unit.get("page_path", ""),
            unit.get("expected_url", ""),
            unit.get("expected_text", ""),
        ]
        corpus.extend(unit.get("supporting_refs", []) or [])
        corpus.extend(unit.get("observation_points", []) or [])
        corpus.extend(unit.get("pass_conditions", []) or [])
        corpus.extend(unit.get("fail_conditions", []) or [])
        test_data = unit.get("test_data", {})
        if isinstance(test_data, dict):
            corpus.extend(test_data.values())
            corpus.extend(test_data.keys())
        selectors = unit.get("selectors", {})
        if isinstance(selectors, dict):
            corpus.extend(selectors.values())
            corpus.extend(selectors.keys())
        unit_tokens: set[str] = set()
        for item in corpus:
            unit_tokens |= _tokenize(item)
        overlap = len(target_tokens & unit_tokens)
        score = overlap
        if overlap:
            score += 1 if any(token in _tokenize(unit.get("page_path", "")) for token in target_tokens) else 0
            score += 1 if any(token in _tokenize(unit.get("expected_url", "")) for token in target_tokens) else 0
            score += 1 if any(token in _tokenize(unit.get("expected_text", "")) for token in target_tokens) else 0
        if score > best_score:
            best_score = score
            best_unit = unit
    return best_unit


def _expanded_cases(
    test_set: dict[str, Any],
    environment: dict[str, Any],
    *,
    expansion_round: int = 1,
    expansion_targets: list[str] | None = None,
) -> list[dict[str, Any]]:
    if str(environment.get("coverage_mode", "")).strip().lower() != "qualification":
        return []
    branch_families = test_set.get("branch_families", [])
    expansion_hints = test_set.get("expansion_hints", [])
    if not isinstance(branch_families, list):
        branch_families = []
    if not isinstance(expansion_hints, list):
        expansion_hints = []
    units = test_set.get("test_units", [])
    if not isinstance(units, list) or not units:
        return []
    expanded: list[dict[str, Any]] = []
    explicit_targets = [str(item).strip() for item in (expansion_targets or []) if str(item).strip()]
    expansion_sources = explicit_targets or [str(item).strip() for item in branch_families + expansion_hints if str(item).strip()]
    if not expansion_sources:
        return []
    raw_budget = environment.get("qualification_budget", test_set.get("qualification_budget"))
    try:
        budget = int(raw_budget)
    except (TypeError, ValueError):
        budget = 0
    if budget <= len(units):
        budget = len(units) + len(expansion_sources)
    target_count = max(len(units), budget)
    source_index = 0
    while len(units) + len(expanded) < target_count:
        family_text = expansion_sources[source_index % len(expansion_sources)]
        source_index += 1
        base_unit = _select_source_unit(units, family_text)
        synthetic = dict(base_unit)
        synthetic["unit_ref"] = f"{base_unit.get('unit_ref', 'QUAL')}-EXP-R{expansion_round}-{family_text}"
        synthetic["title"] = f"{base_unit.get('title', 'qualification')} [R{expansion_round}:{family_text}]"
        synthetic["qualification_family"] = family_text
        expanded.append(
            _build_case(
                test_set,
                synthetic,
                derivation_basis="qualification_expansion",
                qualification_round=expansion_round,
                qualification_family=family_text,
            )
        )
    return expanded


def build_test_case_pack(
    test_set: dict[str, Any],
    environment: dict[str, Any] | None = None,
    *,
    projection_mode: str | None = None,
    qualification_lineage: list[dict[str, Any]] | None = None,
    qualification_budget: int | None = None,
    qualification_round: int = 0,
    qualification_revision: int = 0,
    max_expansion_rounds: int | None = None,
    qualification_stop_reason: str | None = None,
    expansion_round: int = 0,
    expansion_targets: list[str] | None = None,
) -> dict[str, Any]:
    environment = environment or {}
    environment_mode = str(environment.get("coverage_mode", "")).strip().lower()
    projection_mode = projection_mode or ("qualification_expansion" if environment_mode == "qualification" else "minimal_projection")
    cases = [_build_case(test_set, unit, derivation_basis="test_unit") for unit in test_set.get("test_units", [])]
    expanded_cases = (
        _expanded_cases(
            test_set,
            environment,
            expansion_round=max(1, expansion_round or 1),
            expansion_targets=expansion_targets,
        )
        if projection_mode == "qualification_expansion"
        else []
    )
    cases.extend(expanded_cases)
    lineage = qualification_lineage or []
    budget = qualification_budget if qualification_budget is not None else environment.get("qualification_budget", test_set.get("qualification_budget", 1))
    max_rounds = max_expansion_rounds if max_expansion_rounds is not None else environment.get("max_expansion_rounds", test_set.get("max_expansion_rounds"))
    stop_reason = qualification_stop_reason
    if stop_reason is None:
        stop_reason = "branch_families_exhausted" if projection_mode == "qualification_expansion" and expanded_cases else "minimal_projection_only"
    return {
        "artifact_type": "test_case_pack",
        "source_test_set_id": test_set.get("test_set_id", test_set.get("id", "")),
        "execution_modality": test_set.get("execution_modality"),
        "projection_mode": projection_mode,
        "generation_mode": projection_mode,
        "qualification_round": qualification_round if projection_mode == "qualification_expansion" else 0,
        "qualification_revision": qualification_revision if projection_mode == "qualification_expansion" else 0,
        "qualification_max_expansion_rounds": max_rounds,
        "qualification_plan": _qualification_plan(test_set, environment),
        "qualification_budget": budget,
        "qualification_lineage": lineage,
        "expansion_round": expansion_round if projection_mode == "qualification_expansion" else 0,
        "expansion_stop_reason": stop_reason,
        "cases": cases,
    }


def build_script_pack(action: str, environment: dict[str, Any], case_pack: dict[str, Any], ui_source_spec: dict[str, Any]) -> dict[str, Any]:
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
            "ui_source_spec": ui_source_spec,
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
    ]
    coverage = summary.get("coverage") or {}
    if coverage:
        lines.extend(
            [
                f"- coverage_status: {coverage.get('status')}",
                f"- coverage_line_rate_percent: {coverage.get('line_rate_percent')}",
                f"- coverage_covered_lines: {coverage.get('covered_lines')}",
                f"- coverage_num_statements: {coverage.get('num_statements')}",
                f"- coverage_scope: {', '.join(coverage.get('scope') or [])}",
                f"- coverage_scope_origin: {coverage.get('scope_origin')}",
            ]
        )
    if summary.get("projection_mode"):
        lines.append(f"- projection_mode: {summary.get('projection_mode')}")
    if summary.get("generation_mode"):
        lines.append(f"- generation_mode: {summary.get('generation_mode')}")
    if "expansion_round" in summary:
        lines.append(f"- expansion_round: {summary.get('expansion_round')}")
    if "qualification_budget" in summary:
        lines.append(f"- qualification_budget: {summary.get('qualification_budget')}")
    if summary.get("expansion_stop_reason"):
        lines.append(f"- expansion_stop_reason: {summary.get('expansion_stop_reason')}")
    lines.extend(
        [
            "",
            "## Case Results",
        ]
    )
    for item in case_results:
        lines.append(f"- {item['case_id']}: {item['status']} ({item['actual']})")
    return "\n".join(lines) + "\n"
