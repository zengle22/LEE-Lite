"""ADR-043 semantic helpers for feat-to-proto outputs."""

from __future__ import annotations

from typing import Any

from cli.lib.workflow_semantic_coverage import build_semantic_coverage
from cli.lib.workflow_semantic_diff import build_diff_view
from cli.lib.workflow_semantic_dimensions import load_semantic_dimensions
from cli.lib.workflow_semantic_projection import build_review_views


def build_prototype_semantic_artifacts(
    dimensions_path: str,
    bundle: dict[str, Any],
    review: dict[str, Any],
    completeness: dict[str, Any],
    *,
    route_map: dict[str, Any],
    reachability: dict[str, Any],
    initial_view: dict[str, Any],
    placeholder_lint: dict[str, Any],
    runtime_smoke: dict[str, Any],
    fidelity_report: dict[str, Any],
) -> dict[str, Any]:
    dimensions = load_semantic_dimensions(dimensions_path)
    pages = bundle.get("pages") or []
    review_issues = []
    for key in ("journey_check", "cta_hierarchy_check", "flow_consistency_check", "state_experience_check", "feat_alignment_check"):
        section = review.get(key) or {}
        review_issues.extend(str(item).strip() for item in (section.get("issues") or []) if str(item).strip())
    statuses = {
        "journey_and_surface_slice": "explicit" if bool(pages) and bool(bundle.get("surface_map_ref")) else "partial",
        "entry_exit_and_initial_view": "explicit" if route_map.get("decision") == "pass" and initial_view.get("decision") == "pass" else "partial",
        "cta_and_container_semantics": "explicit" if not completeness.get("journey_structural_spec", {}).get("errors") and not completeness.get("ui_shell_snapshot", {}).get("errors") else "partial",
        "primary_states_and_feedback": "explicit" if fidelity_report.get("decision") == "pass" and runtime_smoke.get("decision") == "pass" else "partial",
        "exception_retry_skip_paths": "explicit" if reachability.get("decision") == "pass" and placeholder_lint.get("decision") in {"pass", "warn"} else "partial",
        "shell_alignment_and_owner_binding": "explicit" if bool(bundle.get("surface_map_ref")) and bool(bundle.get("prototype_owner_ref")) else "partial",
        "human_review_followup": "explicit" if review.get("verdict") == "approved" else "partial",
    }
    evidence = {
        "journey_and_surface_slice": ["prototype-bundle.json#/pages", "prototype-bundle.json#/surface_map_ref"],
        "entry_exit_and_initial_view": ["prototype-route-map.json", "prototype-initial-view-report.json"],
        "cta_and_container_semantics": ["journey-ux-ascii.md", "ui-shell-spec.md", "prototype-review-report.json"],
        "primary_states_and_feedback": ["prototype-fidelity-report.json", "prototype-runtime-smoke.json"],
        "exception_retry_skip_paths": ["prototype-journey-reachability-report.json", "prototype-placeholder-lint.json"],
        "shell_alignment_and_owner_binding": ["prototype-bundle.json#/prototype_owner_ref", "prototype-bundle.json#/surface_map_ref"],
        "human_review_followup": ["prototype-review-report.json", "prototype-freeze-gate.json"],
    }
    coverage = build_semantic_coverage(
        dimensions,
        statuses,
        evidence=evidence,
        notes={"human_review_followup": review_issues or ["human review pending"]},
        l3_judgments={
            key: {
                "decision": "pass" if statuses[key] == "explicit" and review.get("verdict") == "approved" else "revise",
                "summary": "Prototype semantics are explicit for this dimension." if statuses[key] == "explicit" else "; ".join(review_issues[:2]) or f"{key} still needs review coverage.",
            }
            for key in statuses
        },
    )
    review_views = build_review_views(
        narrative=[
            f"Prototype package for {bundle.get('feat_ref') or 'selected FEAT'} freezes journey slice, CTA hierarchy, state feedback, and shell alignment.",
            "Automated prototype gates cover structure and runtime smoke, while review coverage stays separate from final approval.",
            "Downstream UI should consume prototype semantics from this package instead of re-deriving journey intent from FEAT alone.",
        ],
        coverage=coverage,
        diff=build_diff_view(
            upstream_refs=[str(item) for item in (bundle.get("source_refs") or []) if str(item).strip()],
            previous_owner_ref=str(bundle.get("prototype_owner_ref") or ""),
            added=[str(page.get("page_id") or "") for page in pages],
            changed=[str(item) for item in review_issues[:3] if str(item).strip()],
            preserved=["journey structural spec", "ui shell snapshot", "surface-map owner binding"],
        ),
    )
    return {
        "semantic_dimensions_ref": "skills/ll-dev-feat-to-proto/output/semantic-dimensions.json",
        "semantic_coverage": coverage,
        "semantic_pass": coverage["semantic_pass"] and review.get("verdict") == "approved",
        "review_views": review_views,
        "l3_review": {
            "decision": "pass" if coverage["semantic_pass"] and review.get("verdict") == "approved" else "revise",
            "summary": "Prototype package is semantically ready for downstream UI derivation." if coverage["semantic_pass"] and review.get("verdict") == "approved" else "; ".join(review_issues[:3]) or "Prototype package still has semantic gaps or unresolved review coverage.",
            "dimensions": [item["id"] for item in coverage["dimensions"] if item["status"] != "explicit"],
        },
    }
