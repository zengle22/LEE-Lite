"""Semantic review heuristics for ADR-036 implementation spec testing."""

from __future__ import annotations

import re
from typing import Any

from cli.lib.impl_spec_test_findings import make_evidence, make_finding
from cli.lib.impl_spec_test_semantics import MIGRATION_KEYWORDS


def _failure_signature(value: str) -> set[str]:
    lowered = str(value or "").strip().lower()
    signature = set(re.findall(r"[a-z_][a-z0-9_()/-]*", lowered))
    for marker in ("invalid", "network", "timeout", "risk", "device", "auth", "error", "blocked", "conflict"):
        if marker in lowered:
            signature.add(marker)
    return {item for item in signature if item}


def _has_recovery_for_all_failures(failure_signals: list[str], recovery_signals: list[str]) -> bool:
    normalized_recoveries = [_failure_signature(item) for item in recovery_signals if str(item or "").strip()]
    if not failure_signals:
        return True
    if not normalized_recoveries:
        return False
    for failure in failure_signals:
        failure_terms = _failure_signature(failure)
        if failure_terms and not any(failure_terms & recovery for recovery in normalized_recoveries):
            return False
    return True


def derive_semantic_findings(
    normalized: dict[str, Any],
    semantic_review: dict[str, Any],
    system_views: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    impl = semantic_review["impl"]
    feat = semantic_review["feat"]
    tech = semantic_review["tech"]
    api = semantic_review.get("api") or {"api_errors": [], "api_outputs": []}
    ui_docs = semantic_review.get("ui_docs", [])
    testset_docs = semantic_review.get("testset_docs", [])
    findings: list[dict[str, Any]] = []
    missing_information: list[str] = []

    if not impl.get("main_sequence"):
        findings.append(
            make_finding(
                "task-order-undefined",
                category="logic",
                severity="blocker",
                confidence=0.94,
                title="IMPL main sequence is missing",
                problem="The implementation package does not define an ordered execution chain.",
                why_it_matters="Coders cannot derive a stable implementation order from the package alone.",
                user_impact="The feature can be implemented inconsistently across modules.",
                counterexample="A coder persists the terminal state before wiring validation because no order was specified.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="Main Sequence Snapshot")],
                repair_target_artifact="IMPL",
                suggested_fix="Add an ordered main sequence that defines the implementation chain and completion step.",
                dimension="implementation_executability",
            )
        )
    if not impl.get("implementation_units"):
        findings.append(
            make_finding(
                "touch-set-missing",
                category="logic",
                severity="blocker",
                confidence=0.93,
                title="IMPL implementation unit mapping is missing",
                problem="The package does not say which modules or touch points must change.",
                why_it_matters="A coder cannot safely scope the implementation boundary.",
                user_impact="Critical behavior can be omitted or implemented in the wrong place.",
                counterexample="Homepage guard is never updated because the touch set was not listed.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="Implementation Unit Mapping Snapshot")],
                repair_target_artifact="IMPL",
                suggested_fix="Add implementation unit mapping or explicit touch-set ownership.",
                dimension="implementation_executability",
            )
        )
    if not system_views["functional_chain"]["completion_signals"]:
        findings.append(
            make_finding(
                "closure-not-achieved",
                category="semantic",
                severity="blocker",
                confidence=0.91,
                title="Completion signals are not explicit",
                problem="The feature does not define a stable terminal success signal across the implementation chain.",
                why_it_matters="Neither coding nor testing can prove the feature is actually complete.",
                user_impact="Users may appear complete in one surface but remain blocked elsewhere.",
                counterexample="Profile submission appears successful, but no state or API output marks the user as ready for homepage entry.",
                evidence=[
                    make_evidence(normalized["impl"]["_source_ref"], section="Main Sequence Snapshot"),
                    make_evidence(normalized["tech"]["_source_ref"], section="State Model Snapshot"),
                ],
                repair_target_artifact="IMPL",
                suggested_fix="Add explicit completion state, success outputs, or a terminal user-visible outcome.",
                dimension="functional_logic",
            )
        )

    owner_candidates = [item for item in system_views["state_data_relationships"]["ownership"] if any(marker in item.lower() for marker in ("profile", "state", "user", "birthdate"))]
    if len(set(owner_candidates)) > 1:
        findings.append(
            make_finding(
                "canonical-ownership-conflict",
                category="data_boundary",
                severity="blocker",
                confidence=0.9,
                title="Canonical ownership is ambiguous across authorities",
                problem="Multiple authorities appear to own the same business data boundary.",
                why_it_matters="AI implementation can pick different truth sources for the same field or state.",
                user_impact="Users may see inconsistent completion or field values across screens.",
                counterexample="The submit flow writes one owner while the homepage guard reads another projection.",
                evidence=[
                    make_evidence(normalized["impl"]["_source_ref"], section="State Model Snapshot", excerpt=", ".join(owner_candidates[:3])),
                    make_evidence(normalized["tech"]["_source_ref"], section="State Model Snapshot", excerpt=", ".join(owner_candidates[:3])),
                ],
                repair_target_artifact="TECH",
                suggested_fix="State one canonical owner and demote the others to projections or consumers.",
                dimension="data_modeling",
            )
        )

    explicit_recoveries = [item for item in impl.get("recovery_signals", []) if any(marker in item.lower() for marker in ("retry", "recover", "fallback", "stay", "return", "fail closed", "重试", "恢复", "回退", "停留", "返回", "阻断"))]
    if impl.get("failure_signals") and not _has_recovery_for_all_failures(impl.get("failure_signals", []), explicit_recoveries):
        findings.append(
            make_finding(
                "recovery-path-missing",
                category="journey",
                severity="blocker",
                confidence=0.9,
                title="Failure paths exist without recovery handling",
                problem="Critical failure states are described, but no stable recovery or fail-closed path is defined.",
                why_it_matters="Implementation will invent recovery behavior ad hoc during coding.",
                user_impact="Users can get stuck with no safe way to proceed or retry.",
                counterexample="Invalid input or failed state transition occurs, but the spec never states whether the user stays, retries, or exits.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="State Model Snapshot", excerpt=", ".join(impl.get("failure_signals", [])[:3]))],
                repair_target_artifact="IMPL",
                suggested_fix="Add recovery, retry, stay-on-page, fallback, or fail-closed behavior for each critical failure path.",
                dimension="user_journey",
            )
        )

    if api.get("api_outputs") and not api.get("api_errors"):
        findings.append(
            make_finding(
                "failure-contract-underdefined",
                category="logic",
                severity="high",
                confidence=0.82,
                title="API contract does not describe failure semantics",
                problem="The API contract defines success outputs but not corresponding failure results or error families.",
                why_it_matters="Frontend and backend can drift on retry, blocking, and error visibility logic.",
                user_impact="Users can see inconsistent or silent failure handling.",
                counterexample="SubmitProfile returns success shape on paper, but no error contract defines invalid input or network behavior.",
                evidence=[make_evidence(normalized["api"]["_source_ref"], section="API Contract Snapshot")] if normalized.get("api") else [make_evidence(normalized["impl"]["_source_ref"], section="Main Sequence Snapshot")],
                repair_target_artifact="API",
                suggested_fix="Add explicit error families, failure results, and retry or fail-closed expectations to the API contract.",
                dimension="api_contract",
            )
        )

    feat_non_blocking = feat.get("non_blocking_claims") or impl.get("non_blocking_claims") or tech.get("non_blocking_claims")
    ui_non_blocking = any(doc.get("non_blocking_claims") for doc in ui_docs)
    ui_blocking = any(doc.get("blocking_claims") for doc in ui_docs)
    if feat_non_blocking and ui_blocking:
        findings.append(
            make_finding(
                "severe-design-conflict-non-blocking-ui",
                category="ux_risk",
                severity="blocker",
                confidence=0.92,
                title="UI contradicts the declared non-blocking journey",
                problem="The product promises a deferred or skippable step, but the UI authority still blocks user progress.",
                why_it_matters="The implementation can follow either the UI or the state/journey truth, but not both.",
                user_impact="Users are blocked by a step that the spec says should be deferrable.",
                counterexample="Device connection is declared deferred, but the screen still says the user must connect before continuing.",
                evidence=[
                    make_evidence(normalized["impl"]["_source_ref"], section="Integration Points Snapshot"),
                    make_evidence(",".join(doc["_source_ref"] for doc in normalized.get("ui_docs", [])), section="UI Constraint Snapshot"),
                ],
                repair_target_artifact="UI",
                suggested_fix="Align UI entry and exit logic with the non-blocking journey or revise upstream truth.",
                dimension="ui_usability",
            )
        )
    elif feat_non_blocking and ui_docs and not ui_non_blocking:
        findings.append(
            make_finding(
                "non-blocking-not-reflected-in-ui",
                category="ux_risk",
                severity="high",
                confidence=0.8,
                title="UI does not express the declared non-blocking behavior",
                problem="A deferred or skip path exists in the logic, but not in the user-facing description.",
                why_it_matters="Users cannot discover the intended low-friction path.",
                user_impact="Users may abandon or assume the flow is hard-blocking.",
                counterexample="Device setup is skippable in state logic, but the screen copy never exposes it.",
                evidence=[
                    make_evidence(normalized["impl"]["_source_ref"], section="Integration Points Snapshot"),
                    make_evidence(",".join(doc["_source_ref"] for doc in normalized.get("ui_docs", [])), section="UI Constraint Snapshot"),
                ],
                repair_target_artifact="UI",
                suggested_fix="Add explicit deferred, skip, or continue-later UI language and actions.",
                dimension="ui_usability",
            )
        )

    if testset_docs:
        observed_terms = set().union(*[set(doc.get("observed_terms", [])) for doc in testset_docs])
        failure_terms = set().union(*[set(doc.get("testable_failure_terms", [])) for doc in testset_docs])
        completion_terms = set(system_views["functional_chain"]["completion_signals"])
        if completion_terms and not (completion_terms & observed_terms):
            findings.append(
                make_finding(
                    "acceptance-not-observable",
                    category="testability",
                    severity="high",
                    confidence=0.84,
                    title="TESTSET does not observe the declared completion signals",
                    problem="Completion signals exist in IMPL or TECH, but TESTSET does not watch them.",
                    why_it_matters="The feature can claim success in documents without any stable acceptance observation.",
                    user_impact="Users can hit regressions that escaped the implementation-readiness review.",
                    counterexample="The report says completion is `homepage_entry_allowed`, but TESTSET never checks it.",
                    evidence=[
                        make_evidence(normalized["impl"]["_source_ref"], section="Main Sequence Snapshot", excerpt=", ".join(sorted(completion_terms)[:3])),
                        make_evidence(",".join(doc["_source_ref"] for doc in normalized.get("testset_docs", [])), section="acceptance_traceability", excerpt=", ".join(sorted(observed_terms)[:3])),
                    ],
                    repair_target_artifact="TESTSET",
                    suggested_fix="Map completion outputs or terminal states into TESTSET observation points and pass conditions.",
                    dimension="testability",
                )
            )
        if api.get("api_errors") and not (set(api.get("api_errors", [])) & failure_terms):
            findings.append(
                make_finding(
                    "critical-failure-not-testable",
                    category="testability",
                    severity="blocker",
                    confidence=0.89,
                    title="TESTSET does not cover critical failure semantics",
                    problem="Failure handling declared in API or state logic is not testable via TESTSET.",
                    why_it_matters="Implementation can drift on the hardest edge cases before coding even starts.",
                    user_impact="Users may see broken retry or recovery flows in production.",
                    counterexample="Network failure is defined in API errors, but no TESTSET path asserts what the user sees or can do next.",
                    evidence=[
                        make_evidence(normalized["api"]["_source_ref"] if normalized.get("api") else normalized["impl"]["_source_ref"], section="API Contract Snapshot", excerpt=", ".join(api.get("api_errors", [])[:3])),
                        make_evidence(",".join(doc["_source_ref"] for doc in normalized.get("testset_docs", [])), section="test_units", excerpt=", ".join(sorted(failure_terms)[:3])),
                    ],
                    repair_target_artifact="TESTSET",
                    suggested_fix="Add failure-path observations, fail conditions, and evidence points for the declared API or state errors.",
                    dimension="testability",
                )
            )

    migration_context = " ".join([*impl.get("scope", []), *impl.get("integration_points", []), *tech.get("integration_points", []), *tech.get("state_model", [])]).lower()
    if normalized.get("migration_required") or any(marker in migration_context for marker in MIGRATION_KEYWORDS):
        if not any(keyword in migration_context for keyword in ("fallback", "priority", "precedence", "fail closed", "回退", "优先", "fail-closed")):
            findings.append(
                make_finding(
                    "migration-fallback-missing",
                    category="logic",
                    severity="high",
                    confidence=0.82,
                    title="Migration or compatibility path lacks fallback rules",
                    problem="Legacy coexistence is mentioned, but fallback or precedence rules are not explicit.",
                    why_it_matters="Compatibility behavior will drift at runtime if ownership or precedence is guessed during coding.",
                    user_impact="Users can see inconsistent behavior during migration windows.",
                    counterexample="Old and new fields coexist, but the spec never says which one wins when they disagree.",
                    evidence=[
                        make_evidence(normalized["impl"]["_source_ref"], section="Integration Points Snapshot"),
                        make_evidence(normalized["tech"]["_source_ref"], section="State Model Snapshot"),
                    ],
                    repair_target_artifact="IMPL",
                    suggested_fix="Document fallback, precedence, or fail-closed behavior for migration-sensitive flows.",
                    dimension="migration_compatibility",
                )
            )
            missing_information.append("migration fallback or precedence rules are missing")

    if feat.get("title") and impl.get("title") and feat["title"] not in impl["title"] and feat["title"] not in impl.get("body_text", ""):
        findings.append(
            make_finding(
                "feature-subject-drift-suspected",
                category="semantic",
                severity="low",
                confidence=0.61,
                title="IMPL title does not clearly anchor the FEAT subject",
                problem="The implementation title does not clearly restate the product behavior subject defined by FEAT.",
                why_it_matters="The package can slowly drift from product behavior into implementation convenience.",
                user_impact="Users may receive a technically coherent but behaviorally wrong implementation.",
                counterexample="The implementation focuses on a save flow but omits the actual user outcome FEAT is promising.",
                evidence=[
                    make_evidence(normalized["impl"]["_source_ref"], section="title", excerpt=impl.get("title", "")),
                    make_evidence(normalized["feat"]["_source_ref"], section="title", excerpt=feat.get("title", "")),
                ],
                repair_target_artifact="IMPL",
                suggested_fix="Make the IMPL title or goal explicitly restate the FEAT product behavior subject.",
                dimension="functional_logic",
            )
        )

    if normalized.get("api") and not system_views["ui_api_state_mapping"]["api_outputs"]:
        missing_information.append("api outputs are not explicit enough to map into state and UI surfaces")

    blocking = [item for item in findings if item["severity"] == "blocker"]
    high = [item for item in findings if item["severity"] == "high"]
    normal = [item for item in findings if item["severity"] in {"medium", "low"}]
    return blocking, high, normal, list(dict.fromkeys(missing_information))


def build_dimension_reviews(
    semantic_review: dict[str, Any],
    system_views: dict[str, Any],
    blocking: list[dict[str, Any]],
    high: list[dict[str, Any]],
    normal: list[dict[str, Any]],
    missing_information: list[str],
) -> dict[str, dict[str, Any]]:
    impl = semantic_review["impl"]
    evidence_map = {
        "functional_logic": ["impl.main_sequence", "impl.completion_signals", "feat.title"],
        "data_modeling": ["impl.state_model", "tech.state_model", "ownership"],
        "user_journey": ["impl.main_sequence", "impl.integration_points", "impl.recovery_signals"],
        "ui_usability": ["ui.constraints", "non_blocking_claims", "blocking_claims"],
        "api_contract": ["api.outputs", "api.errors", "api.preconditions"],
        "implementation_executability": ["impl.implementation_units", "impl.main_sequence"],
        "testability": ["testset.acceptance", "testset.observed_terms", "testset.failure_terms"],
        "migration_compatibility": ["migration_notes", "compatibility_terms", "fallback_terms"],
    }
    reviews: dict[str, dict[str, Any]] = {}
    combined = blocking + high + normal
    for dimension, evidence in evidence_map.items():
        issues = [item for item in combined if item.get("dimension") == dimension]
        score = 8
        if any(item["severity"] == "blocker" for item in issues):
            score = 3
        elif any(item["severity"] == "high" for item in issues):
            score = 5
        elif issues:
            score = 7
        if dimension == "data_modeling" and semantic_review.get("arch"):
            score += 1
        if dimension == "api_contract" and semantic_review.get("api"):
            score += 1
        if dimension == "implementation_executability" and missing_information:
            score -= 1
        if dimension == "functional_logic" and not system_views["functional_chain"]["ordered_steps"]:
            score = min(score, 4)
        if dimension == "testability" and not semantic_review.get("testset_docs"):
            score = min(score, 4)
        coverage_confidence = 0.86
        if dimension == "functional_logic" and not impl.get("main_sequence"):
            coverage_confidence = 0.45
        if dimension == "implementation_executability" and not impl.get("implementation_units"):
            coverage_confidence = 0.35
        if dimension == "testability" and not semantic_review.get("testset_docs"):
            coverage_confidence = 0.4
        if dimension == "migration_compatibility" and not any(marker in (impl.get("body_text", "") + semantic_review["tech"].get("body_text", "")).lower() for marker in MIGRATION_KEYWORDS):
            coverage_confidence = 0.7
        reviews[dimension] = {
            "score": max(0, min(10, score)),
            "coverage_confidence": round(coverage_confidence, 2),
            "findings": [item["id"] for item in issues],
            "evidence": evidence,
        }
    return reviews


def build_counterexample_result(
    normalized: dict[str, Any],
    semantic_review: dict[str, Any],
    system_views: dict[str, Any],
    dimension_reviews: dict[str, dict[str, Any]],
    blocking: list[dict[str, Any]],
    high: list[dict[str, Any]],
) -> dict[str, Any]:
    impl = semantic_review["impl"]
    api = semantic_review.get("api") or {"api_errors": []}
    scenarios: list[dict[str, Any]] = []

    def add_scenario(scenario_id: str, dimension: str, summary: str, evidence: list[str], relevant: bool = True) -> None:
        status = "not_applicable" if not relevant else ("covered" if evidence else "coverage_gap")
        scenarios.append({"scenario_id": scenario_id, "dimension": dimension, "status": status, "summary": summary, "evidence": [item for item in evidence if str(item or "").strip()]})

    mode = normalized["execution_mode"]["mode"]
    if mode != "deep_spec_testing":
        scenarios.append({"scenario_id": "preflight-scan", "dimension": "functional_logic", "status": "sampled", "summary": "quick preflight sampled high-risk semantic edges", "evidence": impl.get("main_sequence", [])[:2]})
        return {
            "mode": mode,
            "simulate_counterexamples": normalized["execution_mode"]["simulate_counterexamples"],
            "scenarios": scenarios,
            "blocking_issue_count": len(blocking),
            "high_priority_issue_count": len(high),
            "high_risk_dimensions": [],
            "required_gap_dimensions": [],
        }

    body_text = impl.get("body_text", "").lower()
    tech_text = semantic_review["tech"].get("body_text", "").lower()
    testset_failure_terms = [term for doc in semantic_review.get("testset_docs", []) for term in doc.get("testable_failure_terms", [])]
    canonical_evidence = [item for item in impl.get("owner_candidates", []) + semantic_review["tech"].get("owner_candidates", []) + impl.get("completion_signals", []) if any(marker in item.lower() for marker in ("canonical", "birthdate", "sole", "authority"))]
    add_scenario("canonical-field-missing", "data_modeling", "canonical field absence or source conflict reviewed", canonical_evidence, relevant=bool(canonical_evidence) or "canonical" in body_text or "birthdate" in body_text or "唯一事实源" in impl.get("body_text", ""))
    add_scenario("invalid-input", "functional_logic", "invalid input and authority mismatch paths reviewed", impl.get("failure_signals", []) + api.get("api_errors", []), relevant=True)

    write_related = any(marker in item.lower() for item in impl.get("main_sequence", []) + impl.get("implementation_units", []) for marker in ("patch", "save", "write", "persist"))
    add_scenario("patch-save-success-completion-not-updated", "implementation_executability", "write succeeds but completion or visibility update is missing", system_views["functional_chain"]["completion_signals"], relevant=write_related)
    add_scenario("state-write-failed", "data_modeling", "state transitions and fail-closed handling reviewed", impl.get("state_model", []) + semantic_review["tech"].get("state_model", []), relevant=bool(impl.get("state_model") or semantic_review["tech"].get("state_model")))

    network_evidence = [item for item in impl.get("failure_signals", []) + impl.get("recovery_signals", []) + api.get("api_errors", []) + testset_failure_terms if "network" in item.lower() or "timeout" in item.lower()]
    network_relevant = bool(normalized.get("api")) or any(marker in item.lower() for item in impl.get("implementation_units", []) + impl.get("main_sequence", []) for marker in ("submit", "api", "persist"))
    add_scenario("network-failure", "api_contract", "network failure, retry, and fail-closed behavior reviewed", network_evidence, relevant=network_relevant)

    risk_relevant = any("risk" in item.lower() or "injury" in item.lower() for item in impl.get("body_text", "").splitlines())
    risk_evidence = [item for item in impl.get("failure_signals", []) + impl.get("recovery_signals", []) if "risk" in item.lower() or "injury" in item.lower()]
    add_scenario("risk-gate-fail", "user_journey", "risk gate failure and recovery path reviewed", risk_evidence, relevant=risk_relevant)

    device_relevant = any("device" in item.lower() for item in impl.get("body_text", "").splitlines())
    device_evidence = [item for item in impl.get("non_blocking_claims", []) + impl.get("failure_signals", []) + impl.get("recovery_signals", []) if "device" in item.lower()]
    add_scenario("device-auth-finalize-fail", "ui_usability", "device auth/finalize failure stays non-blocking", device_evidence, relevant=device_relevant)

    migration_relevant = bool(normalized.get("migration_required")) or any((marker in body_text) or (marker in tech_text) for marker in MIGRATION_KEYWORDS)
    migration_evidence = [
        item
        for item in impl.get("recovery_signals", []) + semantic_review["tech"].get("recovery_signals", []) + impl.get("integration_points", []) + semantic_review["tech"].get("integration_points", [])
        if any(marker in item.lower() for marker in (*MIGRATION_KEYWORDS, "fallback", "priority", "precedence", "fail closed", "回退", "优先"))
    ]
    add_scenario("compatibility-conflict-blocked", "migration_compatibility", "compatibility conflict and precedence fallback reviewed", migration_evidence, relevant=migration_relevant)

    high_risk_dimensions = [name for name, review in dimension_reviews.items() if review["score"] <= 6]
    covered_dimensions = {item["dimension"] for item in scenarios if item["status"] == "covered"}
    for dimension in high_risk_dimensions:
        if dimension not in covered_dimensions:
            scenarios.append({"scenario_id": f"{dimension}-coverage-gap", "dimension": dimension, "status": "coverage_gap", "summary": "high-risk dimension does not have an explicit counterexample scenario", "evidence": []})
    required_gap_dimensions = sorted({item["dimension"] for item in scenarios if item["status"] == "coverage_gap"})
    return {
        "mode": mode,
        "simulate_counterexamples": normalized["execution_mode"]["simulate_counterexamples"],
        "scenarios": scenarios,
        "blocking_issue_count": len(blocking),
        "high_priority_issue_count": len(high),
        "high_risk_dimensions": high_risk_dimensions,
        "required_gap_dimensions": required_gap_dimensions,
    }

