#!/usr/bin/env python3
"""Semantic lock checks for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, normalize_semantic_lock

PRODUCT_AXIS_IDS = {
    "minimal-onboarding-flow",
    "first-ai-advice-release",
    "extended-profile-progressive-completion",
    "device-connect-deferred-entry",
    "state-and-profile-boundary-alignment",
}

PRODUCT_DOMAIN_RULES: dict[str, dict[str, list[list[str]] | list[str]]] = {
    "product_onboarding_test_rule": {
        "required_groups": [
            ["profile_minimal_done"],
            ["homepage entry"],
            ["birthdate"],
            ["deferred device entry", "device_connection_deferred", "device connection remains deferred"],
        ],
        "template_residue_markers": [
            "authoritative decision object",
            "formal publication trigger",
            "compat_mode",
            "wave_id",
            "cutover_guard_ref",
            "pilot chain verifier",
            "producer -> gate -> formal -> consumer -> audit",
            "gated rollout",
            "guarded branch",
        ],
    },
    "first_advice_release_test_rule": {
        "required_groups": [
            ["training_advice_level"],
            ["first_week_action"],
            ["running_level", "recent_injury_status"],
            ["needs_more_info_prompt", "completion prompt"],
        ],
        "template_residue_markers": [
            "authoritative decision object",
            "formal publication trigger",
            "approve / revise / retry / handoff / reject",
            "gated rollout",
            "guarded branch",
            "gate decision object",
        ],
    },
    "extended_profile_completion_test_rule": {
        "required_groups": [
            ["首页任务卡", "homepage task card"],
            ["patch save", "incremental save"],
            ["completion percent"],
            ["retry entry"],
        ],
        "template_residue_markers": [
            "authoritative decision object",
            "formal publication trigger",
            "approve / revise / retry / handoff / reject",
            "gated rollout",
            "guarded branch",
            "gate decision object",
        ],
    },
    "device_deferred_entry_test_rule": {
        "required_groups": [
            ["device_skipped", "skip"],
            ["device_failed_nonblocking", "non-blocking"],
            ["homepage"],
            ["first advice", "first-advice"],
        ],
        "template_residue_markers": [
            "authoritative decision object",
            "formal publication trigger",
            "approve / revise / retry / handoff / reject",
            "gated rollout",
            "guarded branch",
            "gate decision object",
        ],
    },
    "state_profile_boundary_test_rule": {
        "required_groups": [
            ["primary_state"],
            ["capability_flags"],
            ["users"],
            ["user_physical_profile"],
            ["runner_profiles"],
            ["conflict_blocked", "canonical_profile_boundary"],
        ],
        "template_residue_markers": [
            "authoritative decision object",
            "formal publication trigger",
            "approve / revise / retry / handoff / reject",
            "gated rollout",
            "guarded branch",
            "gate decision object",
        ],
    },
}


def _generated_text(
    feature: dict[str, Any],
    bundle_json: dict[str, Any],
    test_set_yaml: dict[str, Any],
    handoff: dict[str, Any] | None = None,
) -> str:
    handoff = handoff or {}
    required_inputs = handoff.get("required_environment_inputs") or test_set_yaml.get("required_environment_inputs") or {}
    unit_text: list[str] = []
    for unit in (test_set_yaml.get("test_units") or []):
        if not isinstance(unit, dict):
            continue
        unit_text.extend(
            [
                str(unit.get("title") or ""),
                " ".join(ensure_list(unit.get("observation_points"))),
                " ".join(ensure_list(unit.get("pass_conditions"))),
                " ".join(ensure_list(unit.get("fail_conditions"))),
                " ".join(ensure_list(unit.get("required_evidence"))),
                " ".join(ensure_list(unit.get("supporting_refs"))),
            ]
        )
    traceability_text: list[str] = []
    for row in (test_set_yaml.get("acceptance_traceability") or []):
        if not isinstance(row, dict):
            continue
        traceability_text.extend(
            [
                str(row.get("acceptance_scenario") or ""),
                str(row.get("given") or ""),
                str(row.get("when") or ""),
                str(row.get("then") or ""),
            ]
        )
    return " ".join(
        [
            str(bundle_json.get("title") or ""),
            str(feature.get("title") or ""),
            str(feature.get("axis_id") or ""),
            str(test_set_yaml.get("title") or ""),
            " ".join(ensure_list(test_set_yaml.get("coverage_scope"))),
            " ".join(ensure_list(test_set_yaml.get("recommended_coverage_scope_name"))),
            " ".join(ensure_list(test_set_yaml.get("risk_focus"))),
            " ".join(
                [
                    " ".join(
                        [
                            str(area.get("key") or ""),
                            str(area.get("kind") or ""),
                            str(area.get("description") or ""),
                            " ".join(ensure_list(area.get("related_entities"))),
                            " ".join(ensure_list(area.get("related_commands"))),
                            " ".join(ensure_list(area.get("acceptance_refs"))),
                            " ".join(ensure_list(area.get("case_families"))),
                        ]
                    )
                    for area in ensure_list(test_set_yaml.get("functional_areas"))
                    if isinstance(area, dict)
                ]
            ),
            " ".join(
                [
                    f"{layer}:{' '.join(ensure_list((test_set_yaml.get('logic_dimensions') or {}).get(layer)))}"
                    for layer in ["universal", "stateful", "control_surface"]
                ]
            ),
            " ".join(
                [
                    " ".join(
                        [
                            str(entity.get("entity") or ""),
                            str(entity.get("functional_area_key") or ""),
                            " ".join(ensure_list(entity.get("states"))),
                            " ".join(
                                [
                                    " ".join(
                                        [
                                            str(action.get("command") or ""),
                                            " ".join(ensure_list(action.get("allowed_in"))),
                                            " ".join(ensure_list(action.get("rejected_in"))),
                                        ]
                                    )
                                    for action in ensure_list(entity.get("guarded_actions"))
                                    if isinstance(action, dict)
                                ]
                            ),
                        ]
                    )
                    for entity in ensure_list((test_set_yaml.get("state_model") or {}).get("entities"))
                    if isinstance(entity, dict)
                ]
            ),
            " ".join(
                [
                    " ".join(
                        [
                            str(item.get("acceptance_ref") or ""),
                            str(item.get("acceptance_scenario") or ""),
                            " ".join(ensure_list(item.get("functional_area_keys"))),
                            " ".join(ensure_list(item.get("unit_refs"))),
                            " ".join(ensure_list(item.get("case_families"))),
                            str(item.get("coverage_status") or ""),
                        ]
                    )
                    for item in ensure_list((test_set_yaml.get("coverage_matrix") or {}).get("acceptances"))
                    if isinstance(item, dict)
                ]
            ),
            " ".join(ensure_list(test_set_yaml.get("preconditions"))),
            " ".join(ensure_list(test_set_yaml.get("environment_assumptions"))),
            " ".join(ensure_list(test_set_yaml.get("pass_criteria"))),
            " ".join(ensure_list(test_set_yaml.get("evidence_required"))),
            " ".join(ensure_list(required_inputs.get("environment"))),
            " ".join(ensure_list(required_inputs.get("data"))),
            " ".join(ensure_list(required_inputs.get("services"))),
            " ".join(ensure_list(required_inputs.get("access"))),
            " ".join(ensure_list(required_inputs.get("feature_flags"))),
            " ".join(ensure_list(required_inputs.get("ui_or_integration_context"))),
            " ".join(unit_text),
            " ".join(traceability_text),
        ]
    ).lower()


def _topic_alignment(domain_type: str, generated_text: str) -> tuple[bool, list[str]]:
    rule = PRODUCT_DOMAIN_RULES.get(domain_type)
    if not rule:
        return True, []
    missing: list[str] = []
    for group in rule.get("required_groups", []):
        candidates = [str(item).lower() for item in group]
        if not any(candidate in generated_text for candidate in candidates):
            missing.append(str(group[0]))
    return not missing, missing


def _template_residue(domain_type: str, generated_text: str) -> list[str]:
    rule = PRODUCT_DOMAIN_RULES.get(domain_type)
    if not rule:
        return []
    return [marker for marker in rule.get("template_residue_markers", []) if str(marker).lower() in generated_text]


def build_semantic_drift_check(
    feature: dict[str, Any],
    bundle_json: dict[str, Any],
    test_set_yaml: dict[str, Any],
    handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lock = normalize_semantic_lock(feature.get("semantic_lock") or test_set_yaml.get("semantic_lock"))
    if not lock:
        return {
            "verdict": "not_applicable",
            "semantic_lock_present": False,
            "semantic_lock_preserved": True,
            "domain_type": "",
            "one_sentence_truth": "",
            "forbidden_axis_detected": [],
            "anchor_matches": [],
            "matched_allowed_capabilities": [],
            "missing_topic_markers": [],
            "template_residue_detected": [],
            "topic_alignment_ok": True,
            "lock_gate_ok": True,
            "review_gate_ok": True,
            "summary": "No semantic_lock present.",
        }

    generated_text = _generated_text(feature, bundle_json, test_set_yaml, handoff=handoff)
    forbidden_hits = [item for item in ensure_list(lock.get("forbidden_capabilities")) if str(item).strip().lower() in generated_text]
    matched_allowed = [item for item in ensure_list(lock.get("allowed_capabilities")) if str(item).strip().lower() in generated_text]
    anchor_matches: list[str] = []
    token_groups = {
        "domain_type": [str(lock.get("domain_type") or "").replace("_", " ").lower()],
        "primary_object": [token for token in str(lock.get("primary_object") or "").replace("_", " ").lower().split() if token],
        "lifecycle_stage": [token for token in str(lock.get("lifecycle_stage") or "").replace("_", " ").lower().split() if token],
    }
    for label, tokens in token_groups.items():
        if tokens and all(token in generated_text for token in tokens):
            anchor_matches.append(label)

    domain_type = str(lock.get("domain_type") or "").strip().lower()
    axis_id = str(feature.get("axis_id") or "").strip().lower()
    if domain_type == "review_projection_rule":
        if axis_id in {"projection-generation", "authoritative-snapshot", "review-focus-risk", "feedback-writeback"}:
            anchor_matches.append("review_projection_axis")
        if all(token in generated_text for token in ["projection", "gate", "ssot"]):
            anchor_matches.append("review_projection_signature")
    if domain_type == "execution_runner_rule":
        if axis_id in {
            "ready-job-emission",
            "runner-operator-entry",
            "runner-control-surface",
            "execution-runner-intake",
            "next-skill-dispatch",
            "execution-result-feedback",
            "runner-observability-surface",
            "skill-adoption-e2e",
        }:
            anchor_matches.append("execution_runner_axis")
        if "runner" in generated_text and any(
            token in generated_text
            for token in ["ready", "queue", "entry", "control", "dispatch", "feedback", "observability", "monitor", "pilot", "cutover", "fallback", "wave"]
        ):
            anchor_matches.append("execution_runner_signature")
    if domain_type in PRODUCT_DOMAIN_RULES or axis_id in PRODUCT_AXIS_IDS:
        if len(matched_allowed) >= 2:
            anchor_matches.append("product_flow_axis")

    topic_alignment_ok, missing_topic_markers = _topic_alignment(domain_type, generated_text)
    template_residue_detected = _template_residue(domain_type, generated_text)
    implementation_readiness_signature = False
    if domain_type == "implementation_readiness_rule":
        implementation_readiness_signature = all(
            bool(test_set_yaml.get(key))
            for key in ["functional_areas", "logic_dimensions", "state_model", "coverage_matrix"]
        ) and bool(test_set_yaml.get("test_units"))
        if implementation_readiness_signature and "implementation_readiness_signature" not in anchor_matches:
            anchor_matches.append("implementation_readiness_signature")
    lock_gate_ok = not forbidden_hits and (len(anchor_matches) >= 1 or implementation_readiness_signature)
    review_gate_ok = lock_gate_ok and topic_alignment_ok and not template_residue_detected

    summary_parts: list[str] = []
    if not lock_gate_ok:
        summary_parts.append("semantic_lock drift detected")
    if missing_topic_markers:
        summary_parts.append(f"missing topic markers: {', '.join(missing_topic_markers)}")
    if template_residue_detected:
        summary_parts.append(f"template residue detected: {', '.join(template_residue_detected)}")
    if not summary_parts:
        summary_parts.append("semantic_lock preserved.")

    return {
        "verdict": "pass" if review_gate_ok else "reject",
        "semantic_lock_present": True,
        "semantic_lock_preserved": lock_gate_ok,
        "domain_type": lock.get("domain_type"),
        "one_sentence_truth": lock.get("one_sentence_truth"),
        "forbidden_axis_detected": forbidden_hits,
        "anchor_matches": anchor_matches,
        "matched_allowed_capabilities": matched_allowed,
        "missing_topic_markers": missing_topic_markers,
        "template_residue_detected": template_residue_detected,
        "topic_alignment_ok": topic_alignment_ok,
        "lock_gate_ok": lock_gate_ok,
        "review_gate_ok": review_gate_ok,
        "summary": "; ".join(summary_parts),
    }
