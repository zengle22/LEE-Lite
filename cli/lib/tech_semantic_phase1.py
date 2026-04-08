"""ADR-043 semantic helpers for feat-to-tech outputs."""

from __future__ import annotations

from typing import Any

from cli.lib.workflow_semantic_coverage import build_semantic_coverage
from cli.lib.workflow_semantic_diff import build_diff_view
from cli.lib.workflow_semantic_dimensions import load_semantic_dimensions
from cli.lib.workflow_semantic_projection import build_review_views
from cli.lib.workflow_semantic_validators import is_placeholder


def build_tech_semantic_artifacts(dimensions_path: str, bundle: dict[str, Any], semantic_gate: dict[str, Any], blocking_findings: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = load_semantic_dimensions(dimensions_path)
    tech_design = bundle.get("tech_design") or {}
    need_assessment = bundle.get("need_assessment") or {}
    artifact_refs = bundle.get("artifact_refs") or {}
    design_consistency = bundle.get("design_consistency_check") or {}
    finding_details = [str(item.get("detail") or item.get("title") or "").strip() for item in blocking_findings if str(item.get("detail") or item.get("title") or "").strip()]
    api_required = bool(bundle.get("api_required"))
    arch_required = bool(bundle.get("arch_required"))
    statuses = {
        "carrier_and_module_responsibility": "explicit" if bool(tech_design.get("implementation_carrier_view")) and bool(tech_design.get("module_plan")) else "partial",
        "contracts_and_field_semantics": "explicit" if bool(tech_design.get("interface_contracts")) and (not api_required or str(artifact_refs.get("api_spec") or "").strip()) else "partial",
        "state_and_runtime_flow": "explicit" if bool(tech_design.get("state_model")) and bool(tech_design.get("main_sequence")) and semantic_gate.get("topic_alignment_ok", True) else "partial",
        "failure_and_compensation": "explicit" if bool(tech_design.get("exception_and_compensation")) and bool(tech_design.get("minimal_code_skeleton")) else "partial",
        "integration_and_compatibility": "explicit" if bool(tech_design.get("integration_points")) and bool(need_assessment.get("integration_context_sufficient")) and bool(tech_design.get("migration_constraints")) else "partial",
        "ownership_and_constraints": "explicit" if not is_placeholder(tech_design.get("technical_glossary_and_canonical_ownership")) and bool(tech_design.get("algorithm_constraints")) else "partial",
        "optional_arch_api_projection": "explicit" if ((not arch_required or str(artifact_refs.get("arch_spec") or "").strip()) and (not api_required or str(artifact_refs.get("api_spec") or "").strip())) else "partial",
    }
    if not semantic_gate.get("semantic_lock_preserved", True):
        statuses["state_and_runtime_flow"] = "conflict"
        statuses["ownership_and_constraints"] = "conflict"
    evidence = {
        "carrier_and_module_responsibility": ["tech-design-bundle.json#/tech_design/implementation_carrier_view", "tech-design-bundle.json#/tech_design/module_plan"],
        "contracts_and_field_semantics": ["tech-design-bundle.json#/tech_design/interface_contracts", "tech-design-bundle.json#/artifact_refs"],
        "state_and_runtime_flow": ["tech-design-bundle.json#/tech_design/state_model", "tech-design-bundle.json#/tech_design/main_sequence"],
        "failure_and_compensation": ["tech-design-bundle.json#/tech_design/exception_and_compensation"],
        "integration_and_compatibility": ["tech-design-bundle.json#/tech_design/integration_points", "tech-design-bundle.json#/integration_context"],
        "ownership_and_constraints": ["tech-design-bundle.json#/tech_design/technical_glossary_and_canonical_ownership", "tech-design-bundle.json#/tech_design/algorithm_constraints"],
        "optional_arch_api_projection": ["tech-design-bundle.json#/need_assessment", "tech-design-bundle.json#/artifact_refs"],
    }
    coverage = build_semantic_coverage(dimensions, statuses, evidence=evidence, notes={"state_and_runtime_flow": finding_details})
    review_views = build_review_views(
        narrative=[
            f"TECH package for {bundle.get('feat_ref') or 'selected FEAT'} freezes implementation carriers, state flow, contracts, integration points, and ownership.",
            "Optional ARCH/API projections remain justified by need assessment and must not become duplicate truth sources.",
            "Downstream IMPL should consume TECH semantics from this package and not re-derive FEAT intent.",
        ],
        coverage=coverage,
        diff=build_diff_view(
            upstream_refs=[str(item) for item in (bundle.get("source_refs") or []) if str(item).strip()],
            previous_owner_ref=str(bundle.get("surface_map_ref") or ""),
            added=[str(bundle.get("tech_ref") or "")],
            changed=[str(item) for item in (semantic_gate.get("axis_conflicts") or []) if str(item).strip()],
            preserved=["selected FEAT lineage", "integration context", "downstream handoff"],
        ),
    )
    return {
        "semantic_dimensions_ref": "skills/ll-dev-feat-to-tech/resources/semantic-dimensions.json",
        "semantic_coverage": coverage,
        "semantic_pass": coverage["semantic_pass"] and bool(design_consistency.get("semantic_passed", False)),
        "review_views": review_views,
        "handoff_updates": {
            "semantic_ready": coverage["semantic_pass"] and bool(design_consistency.get("semantic_passed", False)),
            "open_semantic_gaps": coverage["open_semantic_gaps"],
        },
        # ADR-043 L3 is an AI review layer and must be supplied by supervisor prompts + persisted artifacts.
        "l3_review": {},
    }
