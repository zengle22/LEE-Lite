"""Journey simulation and UX review helpers for impl spec review."""

from __future__ import annotations

from typing import Any

from cli.lib.impl_spec_test_findings import make_evidence, make_finding


PERSONAS = (
    ("first_time_user", "首次进入用户"),
    ("low_literacy_user", "弱认知用户"),
    ("high_risk_user", "高风险/受伤用户"),
    ("skip_device_user", "跳过设备连接用户"),
    ("invalid_input_user", "填错字段用户"),
    ("resume_user", "中断后回来用户"),
)


def build_journey_simulation(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    ui_docs = semantic_review.get("ui_docs", [])
    has_non_blocking = bool(impl.get("non_blocking_claims")) or any(doc.get("non_blocking_claims") for doc in ui_docs)
    failure_surfaces = system_views["user_journey"]["failure_surfaces"]
    recovery_surfaces = system_views["user_journey"]["recovery_surfaces"]
    simulations: list[dict[str, Any]] = []
    for persona_key, persona_label in PERSONAS:
        friction_points: list[str] = []
        status = "covered"
        if persona_key == "skip_device_user" and not has_non_blocking:
            status = "gap"
            friction_points.append("Deferred or skip behavior is not explicit for device setup.")
        if persona_key == "invalid_input_user" and not any("invalid" in item.lower() for item in failure_surfaces):
            status = "gap"
            friction_points.append("Invalid-input recovery is not explicit in the journey.")
        if persona_key == "resume_user" and not any(marker in str(item).lower() for item in recovery_surfaces for marker in ("return", "retry", "resume", "stay", "返回", "重试", "停留")):
            status = "gap"
            friction_points.append("Resume/re-entry behavior is not explicit after interruption.")
        if persona_key == "high_risk_user" and not any("risk" in item.lower() or "injury" in item.lower() for item in failure_surfaces + recovery_surfaces):
            status = "partial"
            friction_points.append("High-risk or injury-specific handling is not explicit.")
        simulations.append({"persona": persona_key, "persona_label": persona_label, "status": status, "friction_points": friction_points})
    return {"simulations": simulations}


def build_ux_review(
    normalized: dict[str, Any],
    semantic_review: dict[str, Any],
    system_views: dict[str, Any],
    journey_simulation: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    impl = semantic_review["impl"]
    ui_docs = semantic_review.get("ui_docs", [])
    ux_risks: list[dict[str, Any]] = []
    opportunities: list[dict[str, Any]] = []
    has_ui = bool(ui_docs)
    failure_surfaces = system_views["user_journey"]["failure_surfaces"]
    recovery_surfaces = system_views["user_journey"]["recovery_surfaces"]

    if has_ui and not any(doc.get("non_blocking_claims") for doc in ui_docs) and impl.get("non_blocking_claims"):
        ux_risks.append(
            make_finding(
                "ux-non-blocking-copy-gap",
                category="ux_risk",
                severity="high",
                confidence=0.82,
                title="UI copy does not explain the deferred path",
                problem="The spec declares a non-blocking or deferred path, but the UI authority does not clearly communicate it.",
                why_it_matters="Users cannot discover the intended low-friction path even if the backend allows it.",
                user_impact="Users may believe they are blocked and abandon the flow.",
                counterexample="Device setup is skippable in the state model, but the screen copy never shows a continue-without-device action.",
                evidence=[make_evidence(",".join(doc["_source_ref"] for doc in normalized.get("ui_docs", [])), section="UI Constraint Snapshot", excerpt="non-blocking path missing")],
                repair_target_artifact="UI",
                suggested_fix="Add explicit deferred action copy and exit criteria on the user-facing screen.",
                dimension="ui_usability",
            )
        )

    if failure_surfaces and not recovery_surfaces:
        ux_risks.append(
            make_finding(
                "ux-failure-recovery-hidden",
                category="ux_risk",
                severity="high",
                confidence=0.8,
                title="Failure recovery is not visible on the user journey",
                problem="Failure states exist in the spec, but the journey does not describe how the user gets unstuck.",
                why_it_matters="Users are forced to infer what to do next after an error.",
                user_impact="The flow feels broken or punitive when an error occurs.",
                counterexample="Invalid input returns an error, but there is no clear retry, stay-on-page, or recovery action in the journey.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="State Model Snapshot", excerpt=", ".join(failure_surfaces[:3]))],
                repair_target_artifact="IMPL",
                suggested_fix="Add user-visible recovery actions and map them to state or UI transitions.",
                dimension="user_journey",
            )
        )

    for simulation in journey_simulation["simulations"]:
        if simulation["status"] == "gap":
            ux_risks.append(
                make_finding(
                    f"ux-persona-gap-{simulation['persona']}",
                    category="ux_risk",
                    severity="medium",
                    confidence=0.69,
                    title=f"{simulation['persona_label']} journey is under-specified",
                    problem="The journey leaves a key persona without explicit guidance or continuation logic.",
                    why_it_matters="A real implementation will fill the gap ad hoc, usually inconsistently across UI and state logic.",
                    user_impact="That persona is more likely to get stuck, confused, or forced into an unintended path.",
                    counterexample="The user reaches this persona-specific branch, but the spec never states the next actionable step.",
                    evidence=[make_evidence(normalized["impl"]["_source_ref"], section="Journey Simulation", excerpt="; ".join(simulation["friction_points"]))],
                    repair_target_artifact="IMPL",
                    suggested_fix="Add explicit persona-facing continuation and recovery behavior for this branch.",
                    dimension="user_journey",
                )
            )

    if has_ui:
        opportunities.append(
            make_finding(
                "ux-opportunity-next-step-copy",
                category="ux_opportunity",
                severity="opportunity",
                confidence=0.66,
                title="Clarify the next-step copy after profile completion",
                problem="The current spec does not say how the UI reassures the user after the minimal completion step.",
                why_it_matters="Clear confirmation copy reduces hesitation and support burden.",
                user_impact="Users can move forward with less uncertainty.",
                counterexample="The user submits successfully but does not know whether device setup is now required or optional.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="Main Sequence Snapshot", excerpt=", ".join(impl.get("completion_signals", [])[:2]))],
                repair_target_artifact="UI",
                suggested_fix="Add confirmation text that explains what is done now and what can be deferred safely.",
                dimension="ui_usability",
            )
        )
    return ux_risks, opportunities

