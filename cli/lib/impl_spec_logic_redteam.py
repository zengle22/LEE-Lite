"""Logic red-team and cross-artifact trace helpers for impl spec review."""

from __future__ import annotations

from typing import Any

from cli.lib.impl_spec_test_findings import make_evidence, make_finding


def _tokens(*groups: list[str]) -> set[str]:
    return {str(item).strip().lower() for group in groups for item in group if str(item).strip()}


def build_cross_artifact_trace(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    feat = semantic_review["feat"]
    tech = semantic_review["tech"]
    api = semantic_review.get("api") or {}
    testset_docs = semantic_review.get("testset_docs", [])
    ui_docs = semantic_review.get("ui_docs", [])
    completion_terms = sorted(_tokens(system_views["functional_chain"]["completion_signals"]))
    testset_observed = sorted({term.lower() for doc in testset_docs for term in doc.get("observed_terms", [])})
    api_outputs = sorted({term.lower() for term in api.get("api_outputs", [])})
    ui_terms = sorted({term.lower() for doc in ui_docs for term in doc.get("tokens", [])})
    impl_units = sorted({term.lower() for term in impl.get("implementation_units", [])})
    return {
        "feat_vs_impl": {
            "feat_goal": feat.get("title", ""),
            "impl_goal": impl.get("title", ""),
            "feat_non_goals": feat.get("non_goals", []),
            "impl_non_goals": impl.get("non_goals", []),
        },
        "completion_trace": {
            "completion_terms": completion_terms,
            "api_outputs": api_outputs,
            "ui_terms": ui_terms,
            "testset_observed_terms": testset_observed,
        },
        "state_trace": {
            "impl_states": impl.get("state_model", []),
            "tech_states": tech.get("state_model", []),
            "state_transitions": system_views["state_data_relationships"]["transitions"],
            "ownership": system_views["state_data_relationships"]["ownership"],
        },
        "implementation_trace": {
            "main_sequence": impl.get("main_sequence", []),
            "implementation_units": impl_units,
            "integration_points": impl.get("integration_points", []),
        },
    }


def build_state_invariant_check(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    tech = semantic_review["tech"]
    completion_terms = _tokens(system_views["functional_chain"]["completion_signals"])
    transition_targets = {str(item.get("to", "")).strip().lower() for item in system_views["state_data_relationships"]["transitions"] if str(item.get("to", "")).strip()}
    invariants: list[dict[str, Any]] = []
    for term in sorted(completion_terms):
        invariants.append(
            {
                "name": f"completion:{term}",
                "status": "supported" if term in transition_targets or term in _tokens(impl.get("main_sequence", []), tech.get("main_sequence", [])) else "unclear",
                "evidence": [term],
            }
        )
    ownership = system_views["state_data_relationships"]["ownership"]
    if ownership:
        invariants.append({"name": "ownership:single-authority", "status": "supported" if len(ownership) == 1 else "conflicted", "evidence": ownership})
    return {
        "invariants": invariants,
        "unclear_invariants": [item for item in invariants if item["status"] == "unclear"],
        "conflicted_invariants": [item for item in invariants if item["status"] == "conflicted"],
    }


def build_logic_risk_inventory(
    normalized: dict[str, Any],
    semantic_review: dict[str, Any],
    system_views: dict[str, Any],
    cross_artifact_trace: dict[str, Any],
    state_invariant_check: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    impl = semantic_review["impl"]
    feat = semantic_review["feat"]
    tech = semantic_review["tech"]
    api = semantic_review.get("api") or {}
    findings: list[dict[str, Any]] = []
    open_questions: list[str] = []
    completion_terms = set(cross_artifact_trace["completion_trace"]["completion_terms"])
    api_outputs = set(cross_artifact_trace["completion_trace"]["api_outputs"])
    testset_terms = set(cross_artifact_trace["completion_trace"]["testset_observed_terms"])
    impl_non_goals = _tokens(impl.get("non_goals", []), feat.get("non_goals", []))
    impl_units = _tokens(impl.get("implementation_units", []))

    if completion_terms and api_outputs and not (completion_terms & api_outputs):
        findings.append(
            make_finding(
                "logic-completion-api-closure",
                category="api_ui_closure",
                severity="high",
                confidence=0.83,
                title="Completion definition is not closed by API outputs",
                problem="IMPL or TECH define completion terms that do not appear in the API output contract.",
                why_it_matters="Frontend and backend can disagree on when the feature is actually complete.",
                user_impact="A user may complete the flow but still be blocked by downstream guards or stale UI.",
                counterexample="Patch/save succeeds, but the API response never exposes the completion signal the UI waits for.",
                evidence=[
                    make_evidence(normalized["impl"]["_source_ref"], section="Main Sequence Snapshot", excerpt=", ".join(system_views["functional_chain"]["completion_signals"][:3])),
                    make_evidence(normalized["api"]["_source_ref"] if normalized.get("api") else normalized["tech"]["_source_ref"], section="API Contract Snapshot", excerpt=", ".join(api.get("api_outputs", [])[:3])),
                ],
                repair_target_artifact="API",
                suggested_fix="Align API postconditions and completion signals so the terminal state is observable on the response boundary.",
                dimension="api_contract",
            )
        )

    if completion_terms and testset_terms and not (completion_terms & testset_terms):
        findings.append(
            make_finding(
                "logic-completion-test-closure",
                category="testability",
                severity="high",
                confidence=0.84,
                title="Completion state is not closed by TESTSET observation",
                problem="Declared completion terms are not observed by TESTSET.",
                why_it_matters="The implementation can claim success without any stable acceptance proof.",
                user_impact="Users may face regressions even though the implementation appears to pass document review.",
                counterexample="Profile save exposes a completion flag, but TESTSET only checks field persistence and never checks homepage entry.",
                evidence=[
                    make_evidence(normalized["impl"]["_source_ref"], section="Main Sequence Snapshot", excerpt=", ".join(system_views["functional_chain"]["completion_signals"][:3])),
                    make_evidence(",".join(doc["_source_ref"] for doc in normalized.get("testset_docs", [])), section="acceptance_traceability", excerpt=", ".join(sorted(testset_terms)[:3])),
                ],
                repair_target_artifact="TESTSET",
                suggested_fix="Map each terminal completion signal to explicit TESTSET observation and pass criteria.",
                dimension="testability",
            )
        )

    unclear = state_invariant_check["unclear_invariants"]
    if unclear:
        findings.append(
            make_finding(
                "logic-state-invariant-unclear",
                category="state_machine",
                severity="high",
                confidence=0.79,
                title="State invariants are declared but not proven by transitions",
                problem="Some completion or ownership invariants are not backed by explicit transitions or ordered steps.",
                why_it_matters="Coders can invent extra hidden states or update orderings during implementation.",
                user_impact="Users can get stuck between visible success and effective readiness.",
                counterexample="The UI renders completion, but the state machine never reaches a guard-passing state.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="State Model Snapshot", excerpt=", ".join(item["name"] for item in unclear[:2]))],
                repair_target_artifact="IMPL",
                suggested_fix="Add explicit transitions or terminal state definitions for each unclear invariant.",
                dimension="data_modeling",
            )
        )

    if state_invariant_check["conflicted_invariants"]:
        findings.append(
            make_finding(
                "logic-ownership-conflict",
                category="data_boundary",
                severity="blocker",
                confidence=0.87,
                title="State ownership invariants conflict across authorities",
                problem="Multiple authority candidates appear to own the same state boundary.",
                why_it_matters="Implementation can fork into competing truth sources.",
                user_impact="Users can see inconsistent data depending on which surface reads first.",
                counterexample="Homepage guard reads a projection while submit flow writes the canonical owner, leaving the user half-complete.",
                evidence=[make_evidence(normalized["tech"]["_source_ref"], section="State Model Snapshot", excerpt=", ".join(cross_artifact_trace["state_trace"]["ownership"]))],
                repair_target_artifact="TECH",
                suggested_fix="Declare one canonical owner and demote the others to projections or consumers.",
                dimension="data_modeling",
            )
        )

    leaked_non_goals = sorted(term for term in impl_non_goals if any(term in unit for unit in impl_units))
    if leaked_non_goals:
        findings.append(
            make_finding(
                "logic-non-goal-leak",
                category="semantic",
                severity="medium",
                confidence=0.73,
                title="Implementation units appear to implement declared non-goals",
                problem="Terms that are explicitly out of scope also appear in implementation units.",
                why_it_matters="The implementation boundary is no longer self-contained and can drift into undocumented work.",
                user_impact="Users may get partial or confusing surfaces that were never accepted upstream.",
                counterexample="A supposedly deferred device flow is partially implemented in the same unit as required onboarding submission.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="Implementation Unit Mapping Snapshot", excerpt=", ".join(leaked_non_goals[:3]))],
                repair_target_artifact="IMPL",
                suggested_fix="Remove non-goal work from implementation units or update upstream scope truth before coding.",
                dimension="functional_logic",
            )
        )

    if not api.get("api_preconditions"):
        open_questions.append("API preconditions are not explicit enough to test caller context and idempotent retry safety.")
    if not semantic_review.get("ui_docs"):
        open_questions.append("UX entry and exit points remain weakly evidenced because no UI authority is bound.")
    if not impl.get("non_goals") and not feat.get("non_goals"):
        open_questions.append("Non-goals are not explicit, so review cannot strongly rule out scope leakage.")
    return findings, open_questions

