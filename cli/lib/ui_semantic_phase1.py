"""ADR-043 semantic helpers for proto-to-ui outputs."""

from __future__ import annotations

from typing import Any

from cli.lib.workflow_semantic_coverage import build_semantic_coverage
from cli.lib.workflow_semantic_diff import build_diff_view
from cli.lib.workflow_semantic_dimensions import load_semantic_dimensions
from cli.lib.workflow_semantic_projection import build_review_views


def build_ui_semantic_artifacts(dimensions_path: str, bundle: dict[str, Any], pages: list[dict[str, Any]], ledger: dict[str, Any], ledger_errors: list[str]) -> dict[str, Any]:
    dimensions = load_semantic_dimensions(dimensions_path)
    sources = ledger.get("ui_spec_semantic_sources") or {}
    from_other = sources.get("from_other_authority") or []
    inferred = sources.get("inferred_by_ai") or []
    statuses = {
        "page_goal_and_task_flow": "explicit" if bool(pages) and bool(bundle.get("ui_spec_refs")) else "partial",
        "information_hierarchy_and_regions": "explicit" if any(item.get("semantic_area") == "layout" for item in (sources.get("from_prototype") or [])) and any(item.get("semantic_area") == "shell_frame" for item in from_other) else "partial",
        "field_action_validation_and_feedback": "explicit" if any(page.get("buttons") for page in pages) else "partial",
        "state_behaviors": "explicit" if any(page.get("states") for page in pages) else "partial",
        "component_container_contracts": "explicit" if any(item.get("semantic_area") == "shell_container_rules" for item in from_other) and bool(bundle.get("ui_owner_ref")) else "partial",
        "source_ledger_and_inference_disclosure": "explicit" if not ledger_errors and all("requires_explicit_review" in item for item in inferred) else "partial",
        "owner_diff_projection": "explicit" if bool(bundle.get("prototype_owner_ref")) else "partial",
    }
    evidence = {
        "page_goal_and_task_flow": ["ui-spec-bundle.json#/ui_spec_refs", "ui-flow-map.md"],
        "information_hierarchy_and_regions": ["ui-semantic-source-ledger.json#/ui_spec_semantic_sources/from_prototype", "ui-semantic-source-ledger.json#/ui_spec_semantic_sources/from_other_authority"],
        "field_action_validation_and_feedback": ["generated ui spec markdown"],
        "state_behaviors": ["generated ui spec markdown"],
        "component_container_contracts": ["ui-spec-bundle.json#/ui_owner_ref", "ui-semantic-source-ledger.json#/ui_spec_semantic_sources/from_other_authority"],
        "source_ledger_and_inference_disclosure": ["ui-semantic-source-ledger.json", "ui-spec-review-report.json"],
        "owner_diff_projection": ["ui-flow-map.md", "ui-spec-review-report.json"],
    }
    coverage = build_semantic_coverage(
        dimensions,
        statuses,
        evidence=evidence,
        notes={"source_ledger_and_inference_disclosure": ledger_errors},
        l3_judgments={
            key: {
                "decision": "pass" if statuses[key] == "explicit" and not ledger_errors else "revise",
                "summary": "UI spec is implementation-facing and traceable for this dimension." if statuses[key] == "explicit" and not ledger_errors else "; ".join(ledger_errors[:2]) or f"{key} still needs stronger semantic disclosure.",
            }
            for key in statuses
        },
    )
    review_views = build_review_views(
        narrative=[
            f"UI spec package for {bundle.get('feat_ref') or 'selected FEAT'} turns prototype semantics into implementation-facing page contracts.",
            "The semantic ledger distinguishes prototype, FEAT, other authorities, and AI inferences instead of collapsing them into one prose layer.",
            "Diff view stays owner-scoped so reviewers can see what changed relative to prototype and current UI ownership.",
        ],
        coverage=coverage,
        diff=build_diff_view(
            upstream_refs=[str(item) for item in (bundle.get("source_refs") or []) if str(item).strip()],
            previous_owner_ref=str(bundle.get("ui_owner_ref") or ""),
            added=[str(item) for item in (bundle.get("ui_spec_refs") or []) if str(item).strip()],
            changed=[str(item) for item in ledger_errors if str(item).strip()],
            preserved=["journey structural spec authority", "ui shell snapshot authority", "explicit inference disclosure"],
        ),
    )
    return {
        "semantic_dimensions_ref": "skills/ll-dev-proto-to-ui/output/semantic-dimensions.json",
        "semantic_coverage": coverage,
        "semantic_pass": coverage["semantic_pass"] and not ledger_errors,
        "review_views": review_views,
        "l3_review": {
            "decision": "pass" if coverage["semantic_pass"] and not ledger_errors else "revise",
            "summary": "UI spec is semantically ready for implementation." if coverage["semantic_pass"] and not ledger_errors else "; ".join(ledger_errors[:3]) or "UI spec still has semantic coverage gaps.",
            "dimensions": [item["id"] for item in coverage["dimensions"] if item["status"] != "explicit"],
        },
    }
