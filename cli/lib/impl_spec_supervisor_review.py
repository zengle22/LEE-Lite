"""Supervisor challenge and review coverage helpers for impl spec review."""

from __future__ import annotations

from typing import Any

from cli.lib.impl_spec_test_findings import make_evidence, make_finding


def build_false_negative_challenge(
    normalized: dict[str, Any],
    semantic_review: dict[str, Any],
    dimension_reviews: dict[str, dict[str, Any]],
    risk_findings: list[dict[str, Any]],
    ux_findings: list[dict[str, Any]],
    open_questions: list[str],
) -> dict[str, Any]:
    challenges: list[dict[str, Any]] = []
    if not ux_findings and semantic_review.get("ui_docs"):
        challenges.append(
            make_finding(
                "supervisor-ux-clean-check",
                category="ux_risk",
                severity="medium",
                confidence=0.7,
                title="UI authority is present but produced no UX findings",
                problem="A fully clean UX result is suspicious when UI authority exists and the flow is non-trivial.",
                why_it_matters="The review may have stayed too close to happy-path logic and missed user-facing friction.",
                user_impact="Real users can still hit confusion or hesitation that the review did not surface.",
                counterexample="The state flow works on paper, but the user cannot discover the intended next step on screen.",
                evidence=[make_evidence(",".join(doc["_source_ref"] for doc in normalized.get("ui_docs", [])), section="Supervisor challenge", excerpt="UI present but no UX findings")],
                repair_target_artifact="UI",
                suggested_fix="Re-run UX review with persona simulation and copy/discoverability checks.",
                dimension="ui_usability",
            )
        )
    thin_dimensions = [name for name, review in dimension_reviews.items() if float(review.get("coverage_confidence", 0.0)) < 0.65]
    if thin_dimensions:
        challenges.append(
            make_finding(
                "supervisor-thin-coverage",
                category="semantic",
                severity="high",
                confidence=0.78,
                title="Some dimensions remain thinly evidenced",
                problem="Several review dimensions have low coverage confidence even after the review completed.",
                why_it_matters="A low-finding result is not trustworthy if the review never had enough evidence to search those dimensions deeply.",
                user_impact="Hidden implementation drift can survive into coding and surface later as rework.",
                counterexample="The report claims low risk, but a low-confidence dimension was never stress-tested against a counterexample.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="Supervisor challenge", excerpt=", ".join(thin_dimensions))],
                repair_target_artifact="IMPL",
                suggested_fix="Add stronger evidence or upstream authority detail for the thin dimensions before claiming full coverage.",
                dimension="implementation_executability",
            )
        )
    if not risk_findings and open_questions:
        challenges.append(
            make_finding(
                "supervisor-open-questions-clean",
                category="semantic",
                severity="medium",
                confidence=0.68,
                title="Open questions remain despite a nearly clean defect inventory",
                problem="The review still has unresolved questions even though the risk inventory is sparse.",
                why_it_matters="This often means the report is under-calling ambiguity rather than the spec being genuinely complete.",
                user_impact="Coders may answer those questions ad hoc during implementation.",
                counterexample="The report says pass, but the caller context or ownership edge is still not explicit.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="Supervisor challenge", excerpt="; ".join(open_questions[:2]))],
                repair_target_artifact="IMPL",
                suggested_fix="Either resolve the open questions upstream or convert them into explicit findings with repair routing.",
                dimension="functional_logic",
            )
        )
    return {"findings": challenges}


def derive_review_coverage(
    *,
    mode: str,
    dimension_reviews: dict[str, dict[str, Any]],
    counterexample_gap_dimensions: list[str],
    open_questions: list[str],
    false_negative_challenge: dict[str, Any],
) -> dict[str, Any]:
    low_confidence = sorted(name for name, review in dimension_reviews.items() if float(review.get("coverage_confidence", 0.0)) < 0.65)
    challenge_count = len(false_negative_challenge.get("findings", []))
    status = "sufficient"
    reasons: list[str] = []
    if counterexample_gap_dimensions:
        status = "insufficient"
        reasons.append("counterexample gaps remain for high-risk dimensions")
    if challenge_count:
        status = "partial" if status == "sufficient" else status
        reasons.append("supervisor false-negative challenges remain open")
    if low_confidence:
        status = "partial" if status == "sufficient" else status
        reasons.append("some review dimensions remain thinly evidenced")
    if mode == "deep_spec_testing" and open_questions:
        status = "partial" if status == "sufficient" else status
        reasons.append("open questions remain under deep review")
    if status == "insufficient":
        recommendation = "revise before strong pass"
    elif status == "partial":
        recommendation = "acceptable for guided revision, not for strong clean pass"
    else:
        recommendation = "coverage is strong enough for the chosen execution mode"
    return {
        "status": status,
        "counterexample_gap_dimensions": counterexample_gap_dimensions,
        "low_confidence_dimensions": low_confidence,
        "open_question_count": len(open_questions),
        "false_negative_challenge_count": challenge_count,
        "reasons": reasons,
        "recommendation": recommendation,
    }

