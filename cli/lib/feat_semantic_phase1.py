"""ADR-043 semantic helpers for epic-to-feat outputs."""

from __future__ import annotations

from typing import Any

from cli.lib.workflow_semantic_coverage import build_semantic_coverage
from cli.lib.workflow_semantic_diff import build_diff_view
from cli.lib.workflow_semantic_dimensions import load_semantic_dimensions
from cli.lib.workflow_semantic_projection import build_review_views
from cli.lib.workflow_semantic_validators import is_placeholder


def build_feat_semantic_artifacts(dimensions_path: str, bundle: dict[str, Any], defects: list[dict[str, Any]], handoff: dict[str, Any], semantic_drift_check: dict[str, Any]) -> dict[str, Any]:
    dimensions = load_semantic_dimensions(dimensions_path)
    features = [item for item in (bundle.get("features") or []) if isinstance(item, dict)]
    boundary_matrix = bundle.get("boundary_matrix") or []
    findings = [str(item.get("detail") or item.get("title") or "").strip() for item in defects if str(item.get("detail") or item.get("title") or "").strip()]

    def all_features(predicate) -> bool:
        return bool(features) and all(predicate(feature) for feature in features)

    statuses = {
        "actor_and_intent": "explicit" if all_features(lambda item: not is_placeholder(item.get("identity_and_scenario")) and not is_placeholder(item.get("goal"))) else "partial",
        "flow_and_journey": "explicit" if all_features(lambda item: not is_placeholder(item.get("business_flow")) and not is_placeholder(item.get("collaboration_and_timeline"))) else "partial",
        "rules_and_constraints": "explicit" if bool(boundary_matrix) and all_features(lambda item: len(item.get("constraints") or []) >= 3) else "partial",
        "inputs_outputs_and_authority": "explicit" if all_features(lambda item: not is_placeholder(item.get("authoritative_artifact")) and bool(item.get("consumes")) and bool(item.get("produces"))) else "partial",
        "edge_cases_and_boundary": "explicit" if bool(boundary_matrix) and all_features(lambda item: bool(item.get("frozen_downstream_boundary")) and len(item.get("acceptance_checks") or []) >= 3) else "partial",
        "acceptance_and_testability": "explicit" if all_features(lambda item: len(item.get("acceptance_checks") or []) >= 3 and not is_placeholder(item.get("acceptance_and_testability"))) else "partial",
        "design_surface_routing": "explicit" if all(not item.get("design_impact_required") or bool(item.get("design_surfaces")) for item in features) else "partial",
    }
    if semantic_drift_check.get("semantic_lock_present") and not semantic_drift_check.get("semantic_lock_preserved", True):
        statuses["actor_and_intent"] = "conflict"
        statuses["flow_and_journey"] = "conflict"

    evidence = {
        "actor_and_intent": ["feat-freeze-bundle.json#/features/*/identity_and_scenario", "feat-freeze-bundle.json#/features/*/goal"],
        "flow_and_journey": ["feat-freeze-bundle.json#/features/*/business_flow", "feat-freeze-bundle.json#/features/*/collaboration_and_timeline"],
        "rules_and_constraints": ["feat-freeze-bundle.json#/boundary_matrix", "feat-freeze-bundle.json#/features/*/constraints"],
        "inputs_outputs_and_authority": ["feat-freeze-bundle.json#/features/*/consumes", "feat-freeze-bundle.json#/features/*/authoritative_artifact"],
        "edge_cases_and_boundary": ["feat-freeze-bundle.json#/features/*/acceptance_checks", "feat-freeze-bundle.json#/features/*/frozen_downstream_boundary"],
        "acceptance_and_testability": ["feat-freeze-bundle.json#/features/*/acceptance_and_testability"],
        "design_surface_routing": ["handoff-to-feat-downstreams.json#/design_gate_required", "feat-freeze-bundle.json#/features/*/design_surfaces"],
    }
    coverage = build_semantic_coverage(dimensions, statuses, evidence=evidence, notes={"flow_and_journey": findings, "edge_cases_and_boundary": findings})
    review_views = build_review_views(
        narrative=[
            f"Generated {len(features)} FEAT slices for {bundle.get('epic_freeze_ref') or 'upstream EPIC'}.",
            "Semantic coverage stays tied to FEAT-owned actors, flow, rules, authority, edge cases, and acceptance truth.",
            "Downstream consumers should inherit FEAT semantics from this bundle and not re-open EPIC scope.",
        ],
        coverage=coverage,
        diff=build_diff_view(
            upstream_refs=[str(item) for item in (bundle.get("source_refs") or []) if str(item).strip()],
            previous_owner_ref=str(handoff.get("integration_context_ref") or ""),
            added=[str(item.get("feat_ref") or "") for item in features],
            changed=[str(item) for item in (semantic_drift_check.get("forbidden_axis_detected") or []) if str(item).strip()],
            preserved=["epic_freeze_ref", "src_root_id", "structured acceptance checks"],
        ),
    )
    return {
        "semantic_dimensions_ref": "skills/ll-product-epic-to-feat/output/semantic-dimensions.json",
        "semantic_coverage": coverage,
        "semantic_pass": coverage["semantic_pass"],
        "review_views": review_views,
        "handoff_updates": {
            "semantic_ready": coverage["semantic_pass"],
            "open_semantic_gaps": coverage["open_semantic_gaps"],
        },
        # ADR-043 L3 is an AI review layer and must be supplied by supervisor prompts + persisted artifacts.
        "l3_review": {},
    }
