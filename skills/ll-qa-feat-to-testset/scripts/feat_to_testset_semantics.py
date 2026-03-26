#!/usr/bin/env python3
"""Semantic lock checks for feat-to-testset."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import ensure_list, normalize_semantic_lock


def build_semantic_drift_check(feature: dict[str, Any], bundle_json: dict[str, Any], test_set_yaml: dict[str, Any]) -> dict[str, Any]:
    lock = normalize_semantic_lock(feature.get("semantic_lock"))
    if not lock:
        return {
            "verdict": "not_applicable",
            "semantic_lock_present": False,
            "semantic_lock_preserved": True,
            "forbidden_axis_detected": [],
            "anchor_matches": [],
            "summary": "No semantic_lock present.",
        }

    generated_text = " ".join(
        [
            str(bundle_json.get("title") or ""),
            str(feature.get("title") or ""),
            " ".join(ensure_list(test_set_yaml.get("coverage_scope"))),
            " ".join(ensure_list(test_set_yaml.get("risk_focus"))),
            " ".join(ensure_list(test_set_yaml.get("pass_criteria"))),
            " ".join(str(unit.get("title") or "") for unit in ensure_list(test_set_yaml.get("test_units")) if isinstance(unit, dict)),
        ]
    ).lower()
    forbidden_hits = [item for item in lock.get("forbidden_capabilities", []) if str(item).strip().lower() in generated_text]
    anchor_matches: list[str] = []
    token_groups = {
        "domain_type": [str(lock.get("domain_type") or "").replace("_", " ").lower()],
        "primary_object": [token for token in str(lock.get("primary_object") or "").replace("_", " ").lower().split() if token],
        "lifecycle_stage": [token for token in str(lock.get("lifecycle_stage") or "").replace("_", " ").lower().split() if token],
    }
    for label, tokens in token_groups.items():
        if tokens and all(token in generated_text for token in tokens):
            anchor_matches.append(label)
    if str(lock.get("domain_type") or "").strip().lower() == "review_projection_rule":
        axis_id = str(feature.get("axis_id") or "").strip().lower()
        if axis_id in {"projection-generation", "authoritative-snapshot", "review-focus-risk", "feedback-writeback"}:
            anchor_matches.append("review_projection_axis")
        if all(token in generated_text for token in ["projection", "gate", "ssot"]):
            anchor_matches.append("review_projection_signature")
    if str(lock.get("domain_type") or "").strip().lower() == "execution_runner_rule":
        axis_id = str(feature.get("axis_id") or "").strip().lower()
        if axis_id in {
            "ready-job-emission",
            "runner-operator-entry",
            "runner-control-surface",
            "execution-runner-intake",
            "next-skill-dispatch",
            "execution-result-feedback",
            "runner-observability-surface",
        }:
            anchor_matches.append("execution_runner_axis")
        if "runner" in generated_text and any(
            token in generated_text
            for token in ["ready", "queue", "entry", "control", "dispatch", "feedback", "observability", "monitor"]
        ):
            anchor_matches.append("execution_runner_signature")
    preserved = not forbidden_hits and len(anchor_matches) >= 1
    return {
        "verdict": "pass" if preserved else "reject",
        "semantic_lock_present": True,
        "semantic_lock_preserved": preserved,
        "domain_type": lock.get("domain_type"),
        "one_sentence_truth": lock.get("one_sentence_truth"),
        "forbidden_axis_detected": forbidden_hits,
        "anchor_matches": anchor_matches,
        "summary": "semantic_lock preserved." if preserved else "semantic_lock drift detected.",
    }
