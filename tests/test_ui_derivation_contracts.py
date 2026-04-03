from __future__ import annotations

from cli.lib.prototype_review_contract import build_prototype_review, validate_prototype_review
from cli.lib.ui_derivation_routing import DIRECT_UI_ALLOWED, PROTOTYPE_REQUIRED, route_ui_derivation
from cli.lib.ui_semantic_ledger import build_ui_semantic_ledger, validate_ui_semantic_ledger


def test_route_ui_derivation_marks_simple_single_surface_low() -> None:
    route = route_ui_derivation(
        {
            "title": "Edit profile nickname",
            "goal": "Allow user to update one display field",
            "scope": ["single page field edit"],
            "constraints": ["no new flow"],
            "acceptance_checks": ["can save nickname"],
        }
    )
    assert route["ui_complexity_level"] == "low"
    assert route["route_decision"] == DIRECT_UI_ALLOWED


def test_route_ui_derivation_marks_complex_flow_high() -> None:
    route = route_ui_derivation(
        {
            "title": "Deferred device connection journey",
            "goal": "Guide user through multi-step connection and retry path",
            "scope": ["multi-step", "skip", "retry", "state sync"],
            "constraints": ["non-blocking", "error recovery"],
            "acceptance_checks": ["user can retry after failure", "journey preserves state"],
            "ui_units": [{"page_name": "entry"}, {"page_name": "result"}],
        }
    )
    assert route["ui_complexity_level"] == "high"
    assert route["route_decision"] == PROTOTYPE_REQUIRED


def test_prototype_review_requires_full_coverage() -> None:
    review = build_prototype_review(
        verdict="approved",
        review_contract_ref="skills/ll-dev-feat-to-proto/resources/review-contract.yaml",
        reviewer_identity="human.reviewer",
        reviewed_at="2026-04-03T10:00:00Z",
        checks={
            "journey_check": {"passed": True, "issues": []},
            "cta_hierarchy_check": {"passed": True, "issues": []},
            "flow_consistency_check": {"passed": True, "issues": []},
            "state_experience_check": {"passed": True, "issues": []},
            "feat_alignment_check": {"passed": True, "issues": []},
        },
    )
    assert validate_prototype_review(review) == []


def test_ui_semantic_ledger_rejects_unreviewed_high_risk_inference() -> None:
    ledger = build_ui_semantic_ledger(
        from_prototype=[{"semantic_area": "layout", "refs": ["prototype/index.html#main"]}],
        from_feat=[{"semantic_area": "business_constraints", "refs": ["FEAT-001"]}],
        inferred_by_ai=[
            {
                "semantic_area": "api_mapping",
                "rationale": "derived from button labels",
                "confidence": "medium",
                "requires_explicit_review": False,
            }
        ],
    )
    errors = validate_ui_semantic_ledger(ledger)
    assert any("high-risk inferred_by_ai entry must require explicit review: api_mapping" in error for error in errors)
