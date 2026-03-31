#!/usr/bin/env python3
"""Coverage and traceability helpers for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, slugify, unique_strings
from feat_to_testset_profiles import derive_priority, derive_test_layers, feature_profile
from feat_to_testset_units import derive_test_units as derive_test_units_impl


PRIMARY_AREA_MAP: dict[str, tuple[str, str, list[str], list[str]]] = {
    "minimal_onboarding": ("minimal_onboarding_flow", "product_flow", ["minimal_profile", "homepage_entry"], ["onboarding.submit", "homepage.enter"]),
    "first_ai_advice": ("first_ai_advice_release", "decision_flow", ["advice_session", "risk_gate"], ["advice.generate", "risk-gate.evaluate"]),
    "extended_profile_completion": ("extended_profile_completion", "progressive_flow", ["profile_task_card", "profile_patch"], ["profile.patch", "homepage.refresh"]),
    "device_deferred_entry": ("device_deferred_entry", "deferred_flow", ["device_entry", "device_connection_result"], ["device.connect", "device.finalize"]),
    "state_profile_boundary": ("state_profile_boundary", "boundary_surface", ["primary_state", "capability_flags", "user_physical_profile"], ["state.write", "state.read"]),
    "runner_ready_job": ("runner_ready_job", "handoff_surface", ["decision_object", "ready_execution_job"], ["gate.evaluate", "job.materialize"]),
    "runner_operator_entry": ("runner_operator_entry", "control_surface", ["runner_context", "execution_runner"], ["loop.run-execution", "loop.resume-execution"]),
    "runner_control_surface": ("runner_control_surface", "control_surface", ["job_ownership", "job_state"], ["job.claim", "job.run", "job.complete", "job.fail"]),
    "runner_intake": ("runner_intake", "stateful_flow", ["job_queue", "job_lease"], ["job.claim", "job.renew-lease"]),
    "runner_dispatch": ("runner_dispatch", "dispatch_flow", ["skill_invocation", "execution_attempt"], ["job.run", "skill.invoke"]),
    "runner_feedback": ("runner_feedback", "stateful_flow", ["job_outcome", "execution_attempt"], ["job.complete", "job.fail", "job.release-hold"]),
    "runner_observability": ("runner_observability", "read_only_surface", ["monitor_snapshot", "backlog_view"], ["loop.show-status", "loop.show-backlog", "loop.recover-jobs"]),
    "projection_generation": ("projection_generation", "projection_surface", ["projection_artifact", "derived_only_marker"], ["projection.render", "projection.commit"]),
    "authoritative_snapshot": ("authoritative_snapshot", "snapshot_surface", ["snapshot_artifact", "authoritative_field"], ["snapshot.extract", "snapshot.verify"]),
    "review_focus_risk": ("review_focus_risk", "analysis_surface", ["review_focus", "risk_block"], ["review.focus", "risk.analyze"]),
    "feedback_writeback": ("feedback_writeback", "writeback_surface", ["revision_request", "projection_comment"], ["projection.comment", "ssot.writeback"]),
    "formal": ("formal_publication", "publication_surface", ["formal_ref", "lineage", "admission_verdict"], ["formal.publish", "formal.admit"]),
    "io": ("governed_io", "policy_surface", ["gateway_verdict", "managed_artifact_ref"], ["artifact.commit", "artifact.read"]),
    "pilot": ("pilot_rollout", "rollout_surface", ["wave_state", "cutover_guard_ref", "pilot_evidence"], ["rollout.start", "rollout.cutover", "rollout.fallback"]),
    "collaboration": ("candidate_handoff", "handoff_surface", ["gate_pending_ref", "assigned_gate_queue"], ["handoff.submit", "handoff.reenter"]),
}


def _case_family(text: str) -> str:
    haystack = text.lower()
    if any(marker in haystack for marker in ["retry", "re-entry", "reentry", "retryable"]):
        return "retry_reentry"
    if any(marker in haystack for marker in ["read-only", "只读", "monitor", "observability", "snapshot"]):
        return "read_only_guard"
    if any(marker in haystack for marker in ["boundary", "边界", "deferred", "skip", "non-blocking", "nonblocking"]):
        return "boundary_conditions"
    if any(marker in haystack for marker in ["invalid", "缺失", "非法", "fail", "blocked", "reject", "deny", "拒绝", "conflict"]):
        return "negative_path"
    if any(marker in haystack for marker in ["claim", "run", "complete", "resume", "recover", "dispatch", "queue", "lease", "ownership", "state"]):
        return "stateful_flow"
    return "happy_path"


def _logic_dimensions_for_case_family(case_family: str) -> dict[str, list[str]]:
    dimensions = {
        "universal": ["happy_path", "boundary_conditions", "invalid_input"],
        "stateful": ["valid_transition", "invalid_transition"],
        "control_surface": ["authorized_action", "rejected_action", "read_only_guard"],
    }
    if case_family == "retry_reentry":
        dimensions["stateful"].append("retry_reentry")
    elif case_family == "stateful_flow":
        dimensions["stateful"].append("state_conflict")
    elif case_family == "boundary_conditions":
        dimensions["stateful"].append("boundary_transition")
    elif case_family == "negative_path":
        dimensions["stateful"].append("failure_path")
    elif case_family == "read_only_guard":
        dimensions["control_surface"].append("monitor_read_only")
    return {key: unique_strings(values) for key, values in dimensions.items()}


def derive_functional_areas(feature: dict[str, Any], units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profile = feature_profile(feature)
    title = str(feature.get("title") or feature.get("feat_ref") or "functional-area")
    primary_key, primary_kind, primary_entities, primary_commands = PRIMARY_AREA_MAP.get(
        profile,
        (slugify(title), "functional_surface", [slugify(str(feature.get("feat_ref") or "feature"))], ["feature.execute"]),
    )
    areas: list[dict[str, Any]] = [
        {
            "key": primary_key,
            "kind": primary_kind,
            "description": f"{title} 的功能覆盖主链。",
            "related_entities": primary_entities,
            "related_commands": primary_commands,
            "acceptance_refs": [],
            "case_families": [],
        }
    ]
    seen_keys = {primary_key}
    for unit in units:
        acceptance_ref = str(unit.get("acceptance_ref") or "").strip()
        if not acceptance_ref:
            continue
        text = " ".join(
            [
                str(unit.get("title") or ""),
                str(unit.get("trigger_action") or ""),
                " ".join(ensure_list(unit.get("observation_points"))),
                " ".join(ensure_list(unit.get("pass_conditions"))),
                " ".join(ensure_list(unit.get("fail_conditions"))),
            ]
        )
        case_family = _case_family(text)
        area_key = slugify(f"{primary_key}-{acceptance_ref}")
        if area_key in seen_keys:
            continue
        seen_keys.add(area_key)
        areas.append(
            {
                "key": area_key,
                "kind": case_family,
                "description": str(unit.get("title") or acceptance_ref),
                "related_entities": unique_strings(primary_entities + ensure_list(unit.get("supporting_refs"))[:2]),
                "related_commands": unique_strings(primary_commands + [str(unit.get("trigger_action") or "")]),
                "acceptance_refs": [acceptance_ref],
                "case_families": [case_family],
            }
        )
    return areas


def derive_logic_dimensions(
    feature: dict[str, Any],
    units: list[dict[str, Any]],
    functional_areas: list[dict[str, Any]],
) -> dict[str, list[str]]:
    profile = feature_profile(feature)
    case_families = [str(unit.get("case_family") or "") for unit in units if str(unit.get("case_family") or "").strip()]
    area_kinds = [str(area.get("kind") or "") for area in functional_areas if str(area.get("kind") or "").strip()]
    dimensions = {
        "universal": ["happy_path", "boundary_conditions", "invalid_input"],
        "stateful": ["valid_transition", "invalid_transition"],
        "control_surface": ["authorized_action", "rejected_action", "read_only_guard"],
    }
    if any(case in {"stateful_flow", "retry_reentry", "negative_path"} for case in case_families) or profile.startswith("runner_"):
        dimensions["stateful"].extend(["retry_reentry", "state_conflict"])
    if any(case == "read_only_guard" for case in case_families) or profile in {"runner_observability", "projection_generation", "authoritative_snapshot"}:
        dimensions["control_surface"].append("monitor_read_only")
    if any(kind in {"boundary_surface", "policy_surface", "publication_surface", "rollout_surface"} for kind in area_kinds):
        dimensions["stateful"].append("guarded_transition")
    return {key: unique_strings(values) for key, values in dimensions.items()}


def _state_model_blueprint(feature: dict[str, Any], primary_area_key: str) -> dict[str, Any]:
    profile = feature_profile(feature)
    if profile.startswith("runner_"):
        entity = "execution_job"
        states = ["ready", "claimed", "running", "waiting_human", "failed", "deadletter"]
        transitions = [["ready", "claimed"], ["claimed", "running"], ["running", "waiting_human"], ["running", "failed"], ["failed", "ready"], ["waiting_human", "ready"]]
        guarded_actions = [
            {"command": "job.claim", "allowed_in": ["ready"], "rejected_in": ["claimed", "running", "deadletter"]},
            {"command": "job.run", "allowed_in": ["claimed"], "rejected_in": ["ready", "failed", "deadletter"]},
            {"command": "job.complete", "allowed_in": ["running"], "rejected_in": ["ready", "claimed", "deadletter"]},
            {"command": "job.fail", "allowed_in": ["running"], "rejected_in": ["ready", "deadletter"]},
        ]
    elif profile in {"minimal_onboarding", "first_ai_advice", "extended_profile_completion", "device_deferred_entry", "state_profile_boundary"}:
        entity = "onboarding_profile"
        states = ["ready", "blocked", "partially_completed", "completed", "failed"]
        transitions = [["ready", "partially_completed"], ["partially_completed", "completed"], ["ready", "blocked"], ["blocked", "ready"], ["completed", "failed"]]
        guarded_actions = [
            {"command": "onboarding.submit", "allowed_in": ["ready", "blocked"], "rejected_in": ["completed", "failed"]},
            {"command": "homepage.enter", "allowed_in": ["completed"], "rejected_in": ["ready", "blocked"]},
        ]
    elif profile == "gate":
        entity = "gate_decision"
        states = ["pending", "approved", "revised", "rejected", "retry_pending"]
        transitions = [["pending", "approved"], ["pending", "revised"], ["pending", "rejected"], ["revised", "retry_pending"], ["retry_pending", "pending"]]
        guarded_actions = [
            {"command": "gate.evaluate", "allowed_in": ["pending"], "rejected_in": ["approved", "rejected"]},
            {"command": "formal.publish", "allowed_in": ["approved"], "rejected_in": ["pending", "revised", "rejected"]},
        ]
    elif profile == "formal":
        entity = "formal_object"
        states = ["draft", "approved", "materialized", "admitted", "failed"]
        transitions = [["draft", "approved"], ["approved", "materialized"], ["materialized", "admitted"], ["draft", "failed"]]
        guarded_actions = [
            {"command": "formal.publish", "allowed_in": ["approved"], "rejected_in": ["draft", "failed"]},
            {"command": "registry.admit", "allowed_in": ["materialized"], "rejected_in": ["draft", "approved", "failed"]},
        ]
    elif profile == "io":
        entity = "managed_io_request"
        states = ["pending", "committed", "denied", "receipt_pending", "failed"]
        transitions = [["pending", "committed"], ["pending", "denied"], ["committed", "receipt_pending"], ["receipt_pending", "committed"]]
        guarded_actions = [
            {"command": "artifact.commit", "allowed_in": ["pending"], "rejected_in": ["denied", "failed"]},
            {"command": "artifact.read", "allowed_in": ["committed"], "rejected_in": ["pending", "denied", "failed"]},
        ]
    elif profile == "pilot":
        entity = "rollout_wave"
        states = ["planned", "running", "cutover_ready", "cutover", "fallback", "complete"]
        transitions = [["planned", "running"], ["running", "cutover_ready"], ["cutover_ready", "cutover"], ["cutover", "complete"], ["running", "fallback"]]
        guarded_actions = [
            {"command": "rollout.start", "allowed_in": ["planned"], "rejected_in": ["complete", "fallback"]},
            {"command": "rollout.fallback", "allowed_in": ["running", "cutover_ready"], "rejected_in": ["planned", "complete"]},
        ]
    elif profile == "collaboration":
        entity = "candidate_package"
        states = ["draft", "submitted", "pending_gate", "approved", "revised", "rejected"]
        transitions = [["draft", "submitted"], ["submitted", "pending_gate"], ["pending_gate", "approved"], ["pending_gate", "revised"], ["pending_gate", "rejected"]]
        guarded_actions = [
            {"command": "handoff.submit", "allowed_in": ["draft"], "rejected_in": ["approved", "rejected"]},
            {"command": "handoff.reenter", "allowed_in": ["revised"], "rejected_in": ["approved", "rejected"]},
        ]
    else:
        entity = "feature_flow"
        states = ["ready", "blocked", "active", "failed"]
        transitions = [["ready", "active"], ["ready", "blocked"], ["blocked", "ready"], ["active", "failed"]]
        guarded_actions = [{"command": "feature.execute", "allowed_in": ["ready", "blocked"], "rejected_in": ["failed"]}]
    return {
        "entities": [
            {
                "entity": entity,
                "functional_area_key": primary_area_key,
                "states": states,
                "valid_transitions": transitions,
                "guarded_actions": guarded_actions,
            }
        ]
    }


def derive_risk_refs(feature: dict[str, Any]) -> list[str]:
    return [f"RISK-{index:02d}" for index, _ in enumerate(ensure_list(feature.get("risk_focus")), start=1)] or ["RISK-01"]


def annotate_test_units(
    feature: dict[str, Any],
    units: list[dict[str, Any]],
    functional_areas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    primary_key = str(functional_areas[0].get("key") or slugify(str(feature.get("title") or feature.get("feat_ref") or "functional-area")))
    acceptance_to_area: dict[str, str] = {}
    for area in functional_areas:
        for acceptance_ref in ensure_list(area.get("acceptance_refs")):
            acceptance_to_area[acceptance_ref] = str(area.get("key") or primary_key)
    risk_refs = derive_risk_refs(feature)
    enriched: list[dict[str, Any]] = []
    for unit in units:
        text = " ".join(
            [
                str(unit.get("title") or ""),
                str(unit.get("trigger_action") or ""),
                " ".join(ensure_list(unit.get("observation_points"))),
                " ".join(ensure_list(unit.get("pass_conditions"))),
                " ".join(ensure_list(unit.get("fail_conditions"))),
            ]
        )
        case_family = _case_family(text)
        acceptance_ref = str(unit.get("acceptance_ref") or "").strip()
        area_key = acceptance_to_area.get(acceptance_ref, primary_key)
        boundary_checks = unique_strings(
            [
                item
                for item in ensure_list(unit.get("pass_conditions")) + ensure_list(unit.get("fail_conditions"))
                if any(token in item.lower() for token in ["boundary", "blocked", "fail", "reject", "skip", "conflict", "read-only", "non-blocking", "retry"])
            ]
        )
        enriched_unit = dict(unit)
        enriched_unit["functional_area_key"] = area_key
        enriched_unit["functional_area_keys"] = [area_key]
        enriched_unit["case_family"] = case_family
        enriched_unit["logic_dimensions"] = _logic_dimensions_for_case_family(case_family)
        enriched_unit["acceptance_refs"] = [acceptance_ref] if acceptance_ref else []
        enriched_unit["risk_refs"] = risk_refs[:3]
        enriched_unit["boundary_checks"] = boundary_checks or ensure_list(unit.get("fail_conditions"))[:2]
        enriched.append(enriched_unit)
    return enriched


def derive_acceptance_traceability(
    feature: dict[str, Any],
    units: list[dict[str, Any]],
    functional_areas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    area_lookup: dict[str, str] = {}
    for area in functional_areas:
        for acceptance_ref in ensure_list(area.get("acceptance_refs")):
            area_lookup[acceptance_ref] = str(area.get("key") or functional_areas[0].get("key") or "")
    risk_refs = derive_risk_refs(feature)
    profile = feature_profile(feature)
    mapping: list[dict[str, Any]] = []
    for check in feature.get("acceptance_checks") or []:
        acceptance_ref = str(check.get("id") or "")
        covered = [unit["unit_ref"] for unit in units if unit.get("acceptance_ref") == acceptance_ref]
        scenario = str(check.get("scenario") or "")
        given = str(check.get("given") or "")
        when = str(check.get("when") or "")
        then = str(check.get("then") or "")
        if profile == "pilot" and "At least one real pilot chain is required" in scenario:
            when = "执行 pilot chain verifier 并评估 adoption readiness"
            then = "至少一条 producer -> gate -> formal -> consumer -> audit 真实 pilot 主链必须被验证，不能只依赖组件内自测。"
        elif profile == "pilot" and "Adoption scope does not expand into repository-wide governance" in scenario:
            then = "onboarding scope 必须保持在 governed skill onboarding / pilot / cutover 范围内，并拒绝仓库级治理扩张。"
        elif profile == "collaboration" and "approval and re-entry semantics outside this FEAT" in then:
            then = "提交完成后只暴露 authoritative handoff 与 pending visibility；decision-driven revise/retry runtime routing 可以回流，但 gate decision issuance / approval 语义仍在本 FEAT 外。"
        elif profile == "runner_operator_entry" and "manual" in scenario.lower():
            then = "runner entry 只负责启动或恢复 execution runner，不得把正常主链 dispatch 退化为人工 relay。"
        elif profile == "runner_observability" and ("read-only" in scenario.lower() or "只读" in scenario):
            then = "monitor surface 只做 authoritative 状态读取与展示，不承担 claim、dispatch 或 outcome 改写职责。"
        mapping.append(
            {
                "acceptance_ref": acceptance_ref,
                "acceptance_scenario": scenario,
                "given": given,
                "when": when,
                "then": then,
                "unit_refs": covered,
                "functional_area_keys": unique_strings([area_lookup.get(acceptance_ref, functional_areas[0].get("key", ""))]),
                "case_family": _case_family(" ".join([scenario, given, when, then])),
                "risk_refs": risk_refs[:3],
                "coverage_status": "covered" if covered else "missing",
                "coverage_notes": "Acceptance is explicitly mapped to executable minimum coverage units." if covered else "Acceptance has not been mapped to a test unit.",
            }
        )
    return mapping


def derive_coverage_matrix(
    feature: dict[str, Any],
    units: list[dict[str, Any]],
    functional_areas: list[dict[str, Any]],
    acceptance_traceability: list[dict[str, Any]],
    state_model: dict[str, Any],
) -> dict[str, Any]:
    area_to_units: dict[str, list[str]] = {}
    area_to_acceptances: dict[str, list[str]] = {}
    area_to_case_families: dict[str, list[str]] = {}
    for unit in units:
        area_key = str(unit.get("functional_area_key") or "").strip()
        if not area_key:
            continue
        area_to_units.setdefault(area_key, []).append(str(unit.get("unit_ref") or ""))
        area_to_case_families.setdefault(area_key, []).append(str(unit.get("case_family") or ""))
    for row in acceptance_traceability:
        for area_key in ensure_list(row.get("functional_area_keys")):
            area_to_acceptances.setdefault(area_key, []).append(str(row.get("acceptance_ref") or ""))
            area_to_case_families.setdefault(area_key, []).append(str(row.get("case_family") or ""))
    acceptances = [
        {
            "acceptance_ref": row.get("acceptance_ref"),
            "acceptance_scenario": row.get("acceptance_scenario"),
            "functional_area_keys": unique_strings(ensure_list(row.get("functional_area_keys"))),
            "unit_refs": ensure_list(row.get("unit_refs")),
            "case_families": [str(row.get("case_family") or "")] if str(row.get("case_family") or "").strip() else [],
            "coverage_status": row.get("coverage_status"),
        }
        for row in acceptance_traceability
    ]
    functional_area_rows: list[dict[str, Any]] = []
    for area in functional_areas:
        key = str(area.get("key") or "").strip()
        functional_area_rows.append(
            {
                "key": key,
                "kind": str(area.get("kind") or ""),
                "description": str(area.get("description") or ""),
                "acceptance_refs": unique_strings(ensure_list(area.get("acceptance_refs")) + area_to_acceptances.get(key, [])),
                "unit_refs": unique_strings(area_to_units.get(key, [])),
                "case_families": unique_strings(ensure_list(area.get("case_families")) + area_to_case_families.get(key, [])),
            }
        )
    risk_rows: list[dict[str, Any]] = []
    dominant_units = [unit for unit in units if str(unit.get("case_family") or "") not in {"happy_path"}] or units
    dominant_unit_refs = [str(unit.get("unit_ref") or "") for unit in dominant_units]
    dominant_case_families = unique_strings([str(unit.get("case_family") or "") for unit in dominant_units])
    for index, risk_text in enumerate(ensure_list(feature.get("risk_focus")), start=1):
        risk_rows.append(
            {
                "risk_ref": f"RISK-{index:02d}",
                "risk_text": risk_text,
                "functional_area_keys": [functional_areas[0]["key"]] if functional_areas else [],
                "unit_refs": dominant_unit_refs,
                "case_families": dominant_case_families,
            }
        )
    return {
        "acceptances": acceptances,
        "functional_areas": functional_area_rows,
        "risks": risk_rows,
        "state_entities": state_model.get("entities", []) if isinstance(state_model, dict) else [],
    }


def build_test_design(feature: dict[str, Any]) -> dict[str, Any]:
    layers = derive_test_layers(feature)
    profile = feature_profile(feature)
    priority = derive_priority(feature)
    raw_units = derive_test_units_impl(feature, layers, profile, priority, [])
    functional_areas = derive_functional_areas(feature, raw_units)
    units = annotate_test_units(feature, raw_units, functional_areas)
    logic_dimensions = derive_logic_dimensions(feature, units, functional_areas)
    acceptance_traceability = derive_acceptance_traceability(feature, units, functional_areas)
    primary_key = str(functional_areas[0].get("key") or slugify(str(feature.get("title") or feature.get("feat_ref") or "functional-area")))
    state_model = _state_model_blueprint(feature, primary_key)
    coverage_matrix = derive_coverage_matrix(feature, units, functional_areas, acceptance_traceability, state_model)
    return {
        "layers": layers,
        "profile": profile,
        "priority": priority,
        "test_units": units,
        "functional_areas": functional_areas,
        "logic_dimensions": logic_dimensions,
        "state_model": state_model,
        "acceptance_traceability": acceptance_traceability,
        "coverage_matrix": coverage_matrix,
    }
