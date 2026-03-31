#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from tech_to_impl_common import ensure_list, unique_strings
from tech_to_impl_derivation import filtered_implementation_rules, implementation_units, tech_list


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


def _scope_boundary(feature: dict[str, Any], package: Any) -> dict[str, list[str]]:
    in_scope = unique_strings(
        ensure_list(feature.get("scope"))[:4]
        + [f"{unit['path']} ({unit['mode']})" for unit in implementation_units(package)[:4]]
    )
    out_of_scope = unique_strings(
        ensure_list(feature.get("non_goals"))[:4]
        + [
            "Do not redefine upstream ADR/FEAT/TECH/API/UI/TESTSET authority.",
            "Do not treat current repo shape as truth source when it conflicts with frozen upstream objects.",
            "Do not expand touch set beyond declared modules without re-derive or revision review.",
        ]
    )
    return {"in_scope": in_scope[:6], "out_of_scope": out_of_scope[:6]}


def _upstream_impacts(
    feature: dict[str, Any],
    package: Any,
    selected_upstream_refs: dict[str, Any],
    checkpoints: list[dict[str, str]],
    provisional_refs: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    tech_focus = unique_strings(tech_list(package, "design_focus")[:2] + filtered_implementation_rules(package)[:2])
    interface_contracts = unique_strings(tech_list(package, "interface_contracts")[:2])
    return {
        "adr": {
            "refs": selected_upstream_refs["adr_refs"],
            "impact": "Freeze decision boundaries, authority rules, and non-override behavior for execution.",
        },
        "src_epic_feat": {
            "src_ref": selected_upstream_refs["src_ref"],
            "epic_ref": selected_upstream_refs["epic_ref"],
            "feat_ref": selected_upstream_refs["feat_ref"],
            "impact": str(feature.get("goal") or "").strip(),
        },
        "tech": {
            "ref": selected_upstream_refs["tech_ref"],
            "impact_items": tech_focus,
        },
        "arch": {
            "ref": selected_upstream_refs["arch_ref"],
            "impact": "Architecture boundaries constrain layering, ownership, and runtime attachment points."
            if selected_upstream_refs["arch_ref"]
            else "No explicit ARCH ref selected for this run.",
        },
        "api": {
            "ref": selected_upstream_refs["api_ref"],
            "impact_items": interface_contracts if selected_upstream_refs["api_ref"] else [],
            "impact": "API contract changes remain governed by upstream API truth."
            if selected_upstream_refs["api_ref"]
            else "No explicit API ref selected for this run.",
        },
        "ui": {
            "ref": selected_upstream_refs["ui_ref"],
            "impact": (
                f"UI constraints remain inherited from {selected_upstream_refs['ui_ref']} and cannot be redefined in IMPL."
                if selected_upstream_refs["ui_ref"]
                else "No explicit UI ref selected for this run."
            ),
            "provisional": any(item["ref"] == selected_upstream_refs["ui_ref"] for item in provisional_refs) if selected_upstream_refs["ui_ref"] else False,
        },
        "testset": {
            "ref": selected_upstream_refs["testset_ref"],
            "impact": (
                f"Acceptance and evidence must remain mapped to {selected_upstream_refs['testset_ref']}."
                + (
                    " This TESTSET is currently provisional and must be refreshed or re-frozen before final execution."
                    if any(item["ref"] == selected_upstream_refs["testset_ref"] for item in provisional_refs)
                    else ""
                )
                if selected_upstream_refs["testset_ref"]
                else "No explicit TESTSET ref selected; acceptance trace remains the execution-time proxy and must not be mistaken for test truth."
            ),
            "acceptance_refs": [item["ref"] for item in checkpoints],
        },
    }


def _change_controls(package: Any) -> dict[str, list[str]]:
    touch_set = unique_strings([unit["path"] for unit in implementation_units(package)])
    return {
        "touch_set": touch_set[:8],
        "allowed_changes": [
            "Implement declared touch set and governed evidence/handoff artifacts only.",
            "Wire runtime, state, and interface carriers within frozen upstream boundaries.",
            "Add compatibility-preserving changes that are already implied by frozen TECH/API constraints.",
        ],
        "forbidden_changes": [
            "Invent new requirements or redefine design truth in IMPL.",
            "Change UI/API/schema authority without upstream freeze or revision.",
            "Use repo current shape as silent override of upstream frozen objects.",
        ],
    }


def _testset_mapping(selected_upstream_refs: dict[str, Any], checkpoints: list[dict[str, str]]) -> dict[str, Any]:
    testset_ref = selected_upstream_refs["testset_ref"]
    return {
        "testset_ref": testset_ref,
        "mapping_policy": "TESTSET_over_IMPL_when_present",
        "mappings": [
            {
                "acceptance_ref": item["ref"],
                "scenario": item["scenario"],
                "expectation": item["expectation"],
                "mapped_to": testset_ref or "acceptance_trace_only_pending_testset_ref",
            }
            for item in checkpoints
        ],
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
    scope_boundary = _scope_boundary(feature, package)
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
        "scope_boundary": scope_boundary,
        "upstream_impacts": _upstream_impacts(feature, package, selected_upstream_refs, checkpoints, provisional_refs),
        "normative_items": unique_strings(ensure_list(feature.get("constraints")) + filtered_implementation_rules(package)),
        "informative_items": unique_strings(ensure_list(feature.get("dependencies"))),
        "change_controls": _change_controls(package),
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
        "testset_mapping": _testset_mapping(selected_upstream_refs, checkpoints),
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
