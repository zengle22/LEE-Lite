#!/usr/bin/env python3
"""Shared helpers for feat-to-testset unit derivation."""

from __future__ import annotations

from typing import Any

from feat_to_testset_common import derive_test_set_id, unique_strings


def unit_payload(
    feat_ref: str,
    index: int,
    acceptance_ref: str | None,
    title: str,
    priority: str,
    layers: list[str],
    input_preconditions: list[str],
    trigger_action: str,
    observation_points: list[str],
    pass_conditions: list[str],
    fail_conditions: list[str],
    required_evidence: list[str],
    supporting_refs: list[str],
    derivation_basis: list[str] | None = None,
) -> dict[str, Any]:
    test_set_id = derive_test_set_id(feat_ref)
    payload = {
        "unit_ref": f"{test_set_id}-U{index:02d}",
        "title": title,
        "priority": priority,
        "input_preconditions": unique_strings(input_preconditions),
        "trigger_action": trigger_action,
        "observation_points": unique_strings(observation_points),
        "pass_conditions": unique_strings(pass_conditions),
        "fail_conditions": unique_strings(fail_conditions),
        "required_evidence": unique_strings(required_evidence),
        "suggested_layers": layers,
        "supporting_refs": unique_strings(supporting_refs),
    }
    if acceptance_ref:
        payload["acceptance_ref"] = acceptance_ref
    if derivation_basis:
        payload["derivation_basis"] = unique_strings(derivation_basis)
    return payload
