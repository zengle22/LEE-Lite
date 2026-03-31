#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from tech_to_impl_common import ensure_list, unique_strings
from tech_to_impl_derivation import filtered_implementation_rules


def _ref_list(values: list[str]) -> list[str]:
    return unique_strings([str(item).strip() for item in values if str(item).strip()])


def _provisional_refs(feature: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    raw_refs = feature.get("provisional_refs")
    items = raw_refs if isinstance(raw_refs, list) else ensure_list(raw_refs)
    for item in items:
        if isinstance(item, dict):
            ref = str(item.get("ref") or "").strip()
            impact_scope = str(item.get("impact_scope") or "unspecified").strip()
            follow_up_action = str(item.get("follow_up_action") or "freeze_or_revise_before_execution").strip()
        else:
            ref = str(item).strip()
            impact_scope = "unspecified"
            follow_up_action = "freeze_or_revise_before_execution"
        if not ref:
            continue
        refs.append(
            {
                "ref": ref,
                "status": "provisional",
                "impact_scope": impact_scope,
                "follow_up_action": follow_up_action,
            }
        )
    return refs


def build_selected_upstream_refs(
    feature: dict[str, Any],
    refs: dict[str, str | None],
    source_refs: list[str],
) -> dict[str, Any]:
    return {
        "adr_refs": _ref_list([item for item in source_refs if item.startswith("ADR-")]),
        "src_ref": next((item for item in source_refs if item.startswith("SRC-")), ""),
        "epic_ref": next((item for item in source_refs if item.startswith("EPIC-")), ""),
        "feat_ref": refs["feat_ref"],
        "tech_ref": refs["tech_ref"],
        "arch_ref": refs["arch_ref"],
        "api_ref": refs["api_ref"],
        "ui_ref": str(feature.get("ui_ref") or "").strip() or None,
        "testset_ref": str(feature.get("testset_ref") or "").strip() or None,
    }


def build_contract_projection(
    package: Any,
    feature: dict[str, Any],
    refs: dict[str, str | None],
    source_refs: list[str],
    steps: list[dict[str, str]],
    checkpoints: list[dict[str, str]],
    deliverables: list[str],
) -> dict[str, Any]:
    selected_upstream_refs = build_selected_upstream_refs(feature, refs, source_refs)
    provisional_refs = _provisional_refs(feature)
    return {
        "package_semantics": {
            "canonical_package": True,
            "execution_time_single_entrypoint": True,
            "domain_truth_source": False,
            "design_truth_source": False,
            "test_truth_source": False,
        },
        "authority_scope": {
            "upstream_truth_sources": [name for name, value in selected_upstream_refs.items() if value],
            "local_authority": [
                "execution_goal",
                "scope_boundary",
                "touch_set_projection",
                "delivery_handoff",
                "acceptance_mapping",
                "evidence_requirements",
            ],
            "forbidden_authority": [
                "new_requirements",
                "design_redefinition",
                "test_truth_override",
                "repo_truth_override",
            ],
        },
        "selected_upstream_refs": selected_upstream_refs,
        "provisional_refs": provisional_refs,
        "normative_items": unique_strings(ensure_list(feature.get("constraints")) + filtered_implementation_rules(package)),
        "informative_items": unique_strings(ensure_list(feature.get("dependencies"))),
        "required_steps": [
            {"title": step["title"], "work": step["work"], "done_when": step["done_when"]}
            for step in steps
        ],
        "suggested_steps": (
            [{"title": "Resolve provisional refs", "reason": "Freeze or revise provisional upstream inputs before downstream execution."}]
            if provisional_refs
            else []
        ),
        "acceptance_trace": checkpoints,
        "handoff_artifacts": deliverables,
        "conflict_policy": {
            "upstream_precedence": ["ADR", "SRC", "EPIC", "FEAT", "ARCH", "TECH", "API", "UI", "TESTSET"],
            "testset_precedence": "TESTSET_over_IMPL",
            "repo_discrepancy_policy": "explicit_discrepancy_handling_required",
        },
        "freshness_status": "fresh_on_generation",
        "rederive_triggers": [
            "selected_upstream_ref_version_changed",
            "testset_acceptance_changed",
            "api_or_ui_contract_changed",
            "tech_boundary_or_touch_set_changed",
            "touch_set_exceeded",
            "acceptance_or_delivery_changed",
            "provisional_ref_resolved_or_rejected",
        ],
        "self_contained_policy": {
            "principle": "minimum_sufficient_information",
            "expand": [
                "rules_facts",
                "acceptance_trace",
                "critical_interfaces_and_boundaries",
                "touch_set",
                "deliverables",
            ],
            "summary_only": [
                "historical_rationale",
                "full_adr_background",
                "full_tech_detail",
                "full_ui_text",
                "full_testset_text",
            ],
            "forbidden": ["full_upstream_mirror"],
        },
        "repo_discrepancy_status": {
            "status": "not_checked_against_repo",
            "policy": "do_not_promote_repo_to_truth",
        },
    }
