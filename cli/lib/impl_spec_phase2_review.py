"""Phase 2 deep-review helpers for impl-spec-test."""

from __future__ import annotations

import re
from typing import Any

from cli.lib.impl_spec_test_semantics import text
from cli.lib.impl_spec_test_support import as_list


RISK_SEVERITIES = ("blocker", "high", "medium", "low", "opportunity")


def _ref(normalized: dict[str, Any], key: str) -> str:
    return str(normalized[key]["_source_ref"])


def _first_ref(normalized: dict[str, Any], key: str) -> str:
    docs = normalized.get(key) or []
    return str(docs[0]["_source_ref"]) if docs else _ref(normalized, "impl")


def _section(doc: dict[str, Any], name: str) -> dict[str, Any]:
    return dict(doc.get("sections", {}).get(name, {}))


def _items(doc: dict[str, Any], name: str) -> list[str]:
    return [text(item) for item in as_list(_section(doc, name).get("items"))]


def _doc_text(doc: dict[str, Any], names: list[str]) -> str:
    return "\n".join(_section(doc, name).get("text", "") for name in names if text(_section(doc, name).get("text")))


def _evidence(ref: str, section: str, excerpt: str) -> dict[str, str]:
    payload = {"ref": ref, "section": section, "excerpt": text(excerpt)}
    return {key: value for key, value in payload.items() if value}


def _finding(
    finding_id: str,
    *,
    category: str,
    severity: str,
    confidence: float,
    title: str,
    problem: str,
    why_it_matters: str,
    user_impact: str,
    counterexample: str,
    evidence: list[dict[str, str]],
    repair_target_artifact: str,
    suggested_fix: str,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "category": category,
        "severity": severity,
        "confidence": round(max(0.0, min(1.0, confidence)), 2),
        "title": title,
        "problem": problem,
        "why_it_matters": why_it_matters,
        "user_impact": user_impact,
        "counterexample": counterexample,
        "evidence": evidence,
        "repair_target_artifact": repair_target_artifact,
        "suggested_fix": suggested_fix,
    }


def _tokenize(value: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_()/-]*", text(value).lower())
    return [token for token in tokens if token]


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    lowered = text(value).lower()
    return any(marker in lowered for marker in markers)


def _signatures(items: list[str], markers: tuple[str, ...]) -> list[tuple[str, ...]]:
    signatures: list[tuple[str, ...]] = []
    for item in items:
        lowered = text(item).lower()
        sig = tuple(sorted({token for token in _tokenize(lowered) if any(marker in token or token == marker for marker in markers)}))
        if sig:
            signatures.append(sig)
    return signatures


def _has_recovery_for_failure(failure_item: str, recovery_items: list[str]) -> bool:
    failure_tokens = {token for token in _tokenize(failure_item) if token not in {"fail", "failed", "failure", "error", "blocked", "blocking"}}
    if not failure_tokens:
        return False
    recovery_signatures = _signatures(recovery_items, ("retry", "recover", "recovery", "fallback", "return", "stay", "continue", "skip", "deferred"))
    if not recovery_signatures:
        return False
    for sig in recovery_signatures:
        if failure_tokens & set(sig):
            return True
    return any(marker in text(" ".join(recovery_items)).lower() for marker in ("retry", "recover", "fallback", "return", "stay", "continue", "skip"))


def _project_issues(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets = {"blocking": [], "high": [], "normal": [], "missing_information": []}
    for item in findings:
        severity = item.get("severity")
        if severity not in RISK_SEVERITIES:
            continue
        issue = {
            "id": item["id"],
            "title": item["title"],
            "impact": item["why_it_matters"],
            "evidence": [f"{e['ref']}#{e['section']}" for e in item["evidence"]],
            "repair_action": item["suggested_fix"],
            "repair_target_artifact": item["repair_target_artifact"],
            "category": item["category"],
            "confidence": item["confidence"],
        }
        if severity == "blocker":
            buckets["blocking"].append(issue)
        elif severity == "high":
            buckets["high"].append(issue)
        elif severity in {"medium", "low"}:
            buckets["normal"].append(issue)
    return buckets


def _build_logic_risks(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    feat = semantic_review["feat"]
    tech = semantic_review["tech"]
    api = semantic_review.get("api") or {"api_outputs": [], "api_errors": [], "api_preconditions": [], "sections": {}}
    testset_docs = semantic_review.get("testset_docs", [])
    ui_docs = semantic_review.get("ui_docs", [])
    impl_state = _items(impl, "state_model")
    impl_main = _items(impl, "main_sequence")
    impl_integration = _items(impl, "integration_points")
    impl_units = _items(impl, "implementation_units")
    feat_scope = _items(feat, "scope")
    tech_state = _items(tech, "state_model")
    tech_main = _items(tech, "main_sequence")
    tech_integration = _items(tech, "integration_points")
    api_outputs = list(api.get("api_outputs", []))
    api_errors = list(api.get("api_errors", []))
    ui_constraints = [item for doc in ui_docs for item in _items(doc, "ui_constraints")]
    test_scope = []
    for doc in testset_docs:
        test_scope.extend(as_list(doc.get("coverage_scope")))
        test_scope.extend(as_list(doc.get("pass_criteria")))
        test_scope.extend(as_list(doc.get("risk_focus")))
        for unit in doc.get("test_units", []) if isinstance(doc.get("test_units"), list) else []:
            if isinstance(unit, dict):
                test_scope.extend(as_list(unit.get("observation_points")))
                test_scope.extend(as_list(unit.get("fail_conditions")))
                test_scope.extend(as_list(unit.get("pass_conditions")))
    failure_items = [item for item in impl_state + impl_main + impl_integration + tech_state + tech_main + tech_integration + api_errors + test_scope + ui_constraints if _contains_any(item, ("fail", "error", "invalid", "conflict", "blocked", "risk"))]
    recovery_items = [item for item in impl_state + impl_main + impl_integration + tech_main + tech_integration + ui_constraints + test_scope if _contains_any(item, ("retry", "recover", "fallback", "return", "stay", "continue", "skip", "deferred"))]
    findings: list[dict[str, Any]] = []
    for item in failure_items:
        if not _has_recovery_for_failure(item, recovery_items):
            findings.append(_finding(
                f"logic-failure-path-{len(findings)+1:03d}",
                category="logic",
                severity="blocker" if _contains_any(item, ("error", "fail", "blocked", "conflict")) else "high",
                confidence=0.91,
                title="Critical failure path lacks matching recovery",
                problem=item,
                why_it_matters="The implementation spec describes a failure state but not a corresponding recovery or fail-closed route.",
                user_impact="Users may get stuck or the implementation may invent recovery behavior.",
                counterexample=item,
                evidence=[_evidence(_ref(normalized, "impl"), "state_model" if item in impl_state else "main_sequence", item)],
                repair_target_artifact="IMPL",
                suggested_fix="Add explicit recovery, retry, stay-on-page, fallback, or fail-closed behavior for this failure path.",
            ))
    completion_signals = list(dict.fromkeys(system_views["functional_chain"]["completion_signals"]))
    observed_terms = set()
    for doc in testset_docs:
        observed_terms.update(as_list(doc.get("observed_terms")))
        observed_terms.update(as_list(doc.get("pass_criteria")))
    for signal in completion_signals:
        if signal and signal not in observed_terms:
            findings.append(_finding(
                f"logic-completion-observability-{len(findings)+1:03d}",
                category="data_boundary",
                severity="medium",
                confidence=0.74,
                title="Completion signal is not directly observable in TESTSET",
                problem=signal,
                why_it_matters="A terminal state can be described in the docs but remain unverified in acceptance evidence.",
                user_impact="Users may think the flow is done while test evidence never proves it.",
                counterexample=f"Write succeeds but completion signal {signal!r} is never asserted.",
                evidence=[_evidence(_ref(normalized, "impl"), "main_sequence", signal)],
                repair_target_artifact="TESTSET",
                suggested_fix="Add explicit observation points and pass conditions for the completion signal.",
            ))
    owner_candidates = list(dict.fromkeys(system_views["state_data_relationships"]["ownership"]))
    canonical_terms = [item for item in owner_candidates if _contains_any(item, ("canonical", "sole", "authority", "birthdate", "user_profile"))]
    if len(canonical_terms) > 1:
        findings.append(_finding(
            f"logic-owner-conflict-{len(findings)+1:03d}",
            category="data_boundary",
            severity="high",
            confidence=0.85,
            title="Canonical ownership is ambiguous",
            problem=", ".join(canonical_terms),
            why_it_matters="Multiple candidates can cause implementation drift in field ownership or source-of-truth selection.",
            user_impact="Users may see inconsistent data after save or resume.",
            counterexample="Two different sources both claim authority over the same field.",
            evidence=[_evidence(_ref(normalized, "tech"), "state_model", canonical_terms[0])],
            repair_target_artifact="TECH",
            suggested_fix="State one canonical owner and demote others to projections or consumers.",
        ))
    return {
        "summary": {
            "blocking": sum(1 for item in findings if item["severity"] == "blocker"),
            "high": sum(1 for item in findings if item["severity"] == "high"),
            "medium": sum(1 for item in findings if item["severity"] == "medium"),
        },
        "findings": findings,
    }


def _build_ux_risks(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    feat = semantic_review["feat"]
    impl = semantic_review["impl"]
    ui_docs = semantic_review.get("ui_docs", [])
    ui_constraints = [item for doc in ui_docs for item in _items(doc, "ui_constraints")]
    non_blocking_claims = list(dict.fromkeys(feat.get("non_blocking_claims", []) + impl.get("non_blocking_claims", []) + ui_constraints))
    blocking_claims = list(dict.fromkeys(feat.get("blocking_claims", []) + impl.get("blocking_claims", []) + ui_constraints))
    risks: list[dict[str, Any]] = []
    if non_blocking_claims and blocking_claims:
        risks.append(_finding(
            "ux-contradiction-001",
            category="ux_risk",
            severity="blocker",
            confidence=0.96,
            title="UI contradicts the declared non-blocking journey",
            problem=" / ".join(non_blocking_claims[:1] + blocking_claims[:1]),
            why_it_matters="A user-facing promise and the actual interaction path diverge.",
            user_impact="Users can be blocked after being told they can continue.",
            counterexample="Flow says skip is allowed, but UI requires completion before continue.",
            evidence=[_evidence(_ref(normalized, "impl"), "integration_points", non_blocking_claims[0] if non_blocking_claims else blocking_claims[0])],
            repair_target_artifact="UI",
            suggested_fix="Align UI entry/exit logic with the non-blocking journey or revise upstream truth.",
        ))
    elif feat.get("non_blocking_claims") and not non_blocking_claims:
        risks.append(_finding(
            "ux-non-blocking-missing-001",
            category="ux_risk",
            severity="high",
            confidence=0.81,
            title="Declared non-blocking behavior is not surfaced in UI",
            problem="Users are not told they can defer or skip a step.",
            why_it_matters="The flow may be correct but still feel blocked or ambiguous.",
            user_impact="Users may abandon the journey or fear losing progress.",
            counterexample="Backend permits continuation, but the UI never shows the option.",
            evidence=[_evidence(_ref(normalized, "feat"), "scope", feat.get("title", "non-blocking flow"))],
            repair_target_artifact="UI",
            suggested_fix="Add explicit skip, deferred, or continue language and actions.",
        ))
    failure_items = [item for item in system_views["user_journey"]["failure_surfaces"] if _contains_any(item, ("fail", "error", "invalid", "network", "risk"))]
    recovery_items = [item for item in system_views["user_journey"]["recovery_surfaces"] if _contains_any(item, ("retry", "recover", "fallback", "return", "stay", "continue"))]
    if failure_items and not recovery_items:
        risks.append(_finding(
            "ux-recovery-missing-001",
            category="ux_risk",
            severity="high",
            confidence=0.79,
            title="Failure paths are visible but recovery is not",
            problem=", ".join(failure_items[:2]),
            why_it_matters="The user can hit an error with no obvious next action.",
            user_impact="Users may get stuck on an error page or retry blindly.",
            counterexample="Network failure occurs and the UI does not expose a retry or fallback action.",
            evidence=[_evidence(_ref(normalized, "impl"), "state_model", failure_items[0])],
            repair_target_artifact="UI",
            suggested_fix="Expose retry, fallback, or fail-closed copy for each critical failure state.",
        ))
    improvements: list[dict[str, Any]] = []
    if non_blocking_claims:
        improvements.append(_finding(
            "ux-opportunity-001",
            category="ux_opportunity",
            severity="opportunity",
            confidence=0.69,
            title="Make the deferred path explicit",
            problem=non_blocking_claims[0],
            why_it_matters="The journey reads cleaner when the skip/continue affordance is clear.",
            user_impact="Lower cognitive load and fewer false assumptions about blocking steps.",
            counterexample="The user wonders whether the step is mandatory.",
            evidence=[_evidence(_ref(normalized, "impl"), "integration_points", non_blocking_claims[0])],
            repair_target_artifact="UI",
            suggested_fix="Use explicit deferred / skip / continue microcopy and preserve progress affordances.",
        ))
    if recovery_items:
        improvements.append(_finding(
            "ux-opportunity-002",
            category="ux_opportunity",
            severity="opportunity",
            confidence=0.67,
            title="Surface recovery actions where failures can occur",
            problem=recovery_items[0],
            why_it_matters="Recovery is more usable when the action is visible at the point of failure.",
            user_impact="Users can recover faster and with less ambiguity.",
            counterexample="A failure occurs but the recovery action is hidden in surrounding prose.",
            evidence=[_evidence(_ref(normalized, "impl"), "main_sequence", recovery_items[0])],
            repair_target_artifact="UI",
            suggested_fix="Attach retry or fallback affordances directly to the relevant failure state.",
        ))
    return {"summary": {"risks": len(risks), "improvements": len(improvements)}, "risks": risks, "improvements": improvements}


def _build_journey_simulation(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    failure_items = system_views["user_journey"]["failure_surfaces"]
    recovery_items = system_views["user_journey"]["recovery_surfaces"]
    personas = [
        ("first_entry_user", "first-time onboarding", impl.get("main_sequence", [])),
        ("invalid_input_user", "filled form with mistakes", failure_items),
        ("network_failure_user", "network interruption", failure_items),
        ("device_skip_user", "wants to continue without device", system_views["user_journey"]["primary_journey"]),
        ("interrupted_return_user", "returns after pause", recovery_items),
        ("high_risk_user", "risk gate scenario", failure_items + recovery_items),
    ]
    scenarios: list[dict[str, Any]] = []
    for persona, entry, path in personas:
        status = "covered" if path else "gap"
        outcome = "recoverable" if _contains_any(" ".join(path), ("retry", "recover", "fallback", "continue", "skip")) else "blocked"
        scenarios.append({
            "persona": persona,
            "entry_point": entry,
            "path": path[:4],
            "outcome": outcome if status == "covered" else "unknown",
            "status": status,
            "evidence": [
                _evidence(_ref(normalized, "impl"), "main_sequence", path[0] if path else entry),
            ] if path else [],
        })
    return {"summary": {"covered": sum(1 for item in scenarios if item["status"] == "covered"), "gaps": sum(1 for item in scenarios if item["status"] != "covered")}, "scenarios": scenarios}


def _build_state_invariants(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    testset_docs = semantic_review.get("testset_docs", [])
    completion_signals = list(dict.fromkeys(system_views["functional_chain"]["completion_signals"]))
    failure_surfaces = system_views["user_journey"]["failure_surfaces"]
    recovery_surfaces = system_views["user_journey"]["recovery_surfaces"]
    ownership = system_views["state_data_relationships"]["ownership"]
    failure_details = [(item, _has_recovery_for_failure(item, recovery_surfaces)) for item in failure_surfaces]
    invariants = []
    completion_observed = set()
    for doc in testset_docs:
        completion_observed.update(as_list(doc.get("observed_terms")))
        completion_observed.update(as_list(doc.get("pass_criteria")))
    invariants.append({
        "name": "completion-visible",
        "status": "pass" if not completion_signals or any(signal in completion_observed for signal in completion_signals) else "fail",
        "evidence": [_evidence(_first_ref(normalized, "testset_docs"), "observed_terms", next(iter(completion_observed), ""))] if completion_observed else [],
    })
    invariants.append({
        "name": "failure-recovery",
        "status": "pass" if not failure_details or all(hit for _, hit in failure_details) else "fail",
        "evidence": [_evidence(_ref(normalized, "impl"), "state_model", failure_details[0][0])] if failure_details else [],
    })
    invariants.append({
        "name": "canonical-owner",
        "status": "pass" if len([item for item in ownership if _contains_any(item, ("canonical", "sole", "authority", "birthdate", "user_profile"))]) <= 1 else "fail",
        "evidence": [_evidence(_ref(normalized, "tech"), "state_model", ownership[0])] if ownership else [],
    })
    invariants.append({
        "name": "ui-alignment",
        "status": "pass" if not system_views["user_journey"]["failure_surfaces"] or not any(_contains_any(item, ("must connect", "before continue", "blocking")) for item in system_views["ui_api_state_mapping"]["ui_constraints"]) else "fail",
        "evidence": [_evidence(_first_ref(normalized, "ui_docs"), "ui_constraints", system_views["ui_api_state_mapping"]["ui_constraints"][0])] if system_views["ui_api_state_mapping"]["ui_constraints"] else [],
    })
    return {"status": "pass" if all(item["status"] == "pass" for item in invariants) else "fail", "invariants": invariants}


def _build_cross_artifact_trace(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    impl = semantic_review["impl"]
    feat = semantic_review["feat"]
    tech = semantic_review["tech"]
    api = semantic_review.get("api") or {"api_outputs": [], "api_errors": []}
    ui_docs = semantic_review.get("ui_docs", [])
    testset_docs = semantic_review.get("testset_docs", [])
    rows = []
    rows.append({"family": "completion", "artifacts": [k for k, items in (("IMPL", system_views["functional_chain"]["completion_signals"]), ("FEAT", feat.get("completion_signals", [])), ("TECH", tech.get("completion_signals", [])), ("API", api.get("api_outputs", []))) if items], "status": "aligned" if system_views["functional_chain"]["completion_signals"] else "missing"})
    rows.append({"family": "failure", "artifacts": [k for k, items in (("IMPL", system_views["user_journey"]["failure_surfaces"]), ("API", api.get("api_errors", [])), ("TESTSET", [item for doc in testset_docs for item in as_list(doc.get("testable_failure_terms"))])) if items], "status": "aligned" if system_views["user_journey"]["failure_surfaces"] else "missing"})
    rows.append({"family": "recovery", "artifacts": [k for k, items in (("IMPL", system_views["user_journey"]["recovery_surfaces"]), ("UI", [item for doc in ui_docs for item in _items(doc, "ui_constraints")]), ("TESTSET", [item for doc in testset_docs for item in as_list(doc.get("observed_terms"))])) if items], "status": "aligned" if system_views["user_journey"]["recovery_surfaces"] else "partial"})
    rows.append({"family": "ownership", "artifacts": ["IMPL", "TECH"], "status": "aligned" if len(system_views["state_data_relationships"]["ownership"]) <= 1 else "conflict"})
    rows.append({"family": "non_blocking", "artifacts": ["FEAT", "UI", "IMPL"], "status": "conflict" if feat.get("non_blocking_claims") and any(_contains_any(item, ("must connect", "before continue")) for doc in ui_docs for item in _items(doc, "ui_constraints")) else "aligned"})
    return {"rows": rows, "coverage": {"artifact_count": 6, "row_count": len(rows)}}


def _build_open_questions(normalized: dict[str, Any], state_check: dict[str, Any], trace: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for item in state_check["invariants"]:
        if item["status"] != "pass":
            questions.append({"question": f"Which authoritative artifact resolves the {item['name']} invariant?", "reason": "state invariant is not fully closed", "artifact": "MULTI", "evidence": item["evidence"]})
    for row in trace["rows"]:
        if row["status"] in {"conflict", "partial", "missing"}:
            questions.append({"question": f"Clarify the {row['family']} trace across the linked authorities.", "reason": f"{row['status']} trace", "artifact": "MULTI", "evidence": []})
    return questions


def _build_false_negative_challenge(normalized: dict[str, Any], logic: dict[str, Any], ux: dict[str, Any], state_check: dict[str, Any]) -> dict[str, Any]:
    challenges = []
    assumptions = [
        ("happy_path_is_enough", "happy-path text alone proves implementation readiness", logic["summary"]["blocking"] == 0),
        ("completion_is_observable", "completion signals are directly observable", state_check["invariants"][0]["status"] == "pass"),
        ("recovery_is_clear", "users can recover from declared failures", state_check["invariants"][1]["status"] == "pass"),
        ("ui_is_not_blocking", "UI journey matches the declared non-blocking behavior", state_check["invariants"][3]["status"] == "pass"),
    ]
    for name, assumption, covered in assumptions:
        challenges.append({"challenge_id": name, "assumption": assumption, "status": "covered" if covered else "gap", "evidence": []})
    coverage_gaps = [item["challenge_id"] for item in challenges if item["status"] == "gap"]
    return {
        "status": "pass" if not coverage_gaps else "warning",
        "challenges": challenges,
        "coverage_gaps": coverage_gaps,
        "support_hooks": ["logic-risk-inventory", "ux-risk-inventory", "journey-simulation", "state-invariant-check", "cross-artifact-trace"],
    }


def build_phase2_review(normalized: dict[str, Any], semantic_review: dict[str, Any], system_views: dict[str, Any]) -> dict[str, Any]:
    logic_risks = _build_logic_risks(normalized, semantic_review, system_views)
    ux_risks = _build_ux_risks(normalized, semantic_review, system_views)
    journey_simulation = _build_journey_simulation(normalized, semantic_review, system_views)
    state_check = _build_state_invariants(normalized, semantic_review, system_views)
    trace = _build_cross_artifact_trace(normalized, semantic_review, system_views)
    open_questions = _build_open_questions(normalized, state_check, trace)
    false_negative = _build_false_negative_challenge(normalized, logic_risks, ux_risks, state_check)
    projected = _project_issues(logic_risks["findings"] + ux_risks["risks"])
    projected["missing_information"] = [item["question"] for item in open_questions]
    projected["normal"].extend(
        {
            "id": item["challenge_id"],
            "title": item["assumption"],
            "impact": "false-negative challenge uncovered a review coverage gap" if item["status"] != "covered" else "challenge covered",
            "evidence": [hook for hook in false_negative["support_hooks"]],
            "repair_action": "add explicit evidence for the challenged assumption" if item["status"] != "covered" else "retain the current evidence set",
            "repair_target_artifact": "MULTI",
            "category": "testability",
            "confidence": 0.61,
        }
        for item in false_negative["challenges"]
        if item["status"] != "covered"
    )
    phase2_coverage = {
        "status": "insufficient" if false_negative["coverage_gaps"] or any(item["severity"] == "blocker" for item in logic_risks["findings"]) else "sufficient",
        "coverage_gaps": false_negative["coverage_gaps"],
    }
    return {
        "logic_risk_inventory": logic_risks,
        "ux_risk_inventory": ux_risks,
        "ux_improvement_inventory": {"summary": ux_risks["summary"], "improvements": ux_risks["improvements"]},
        "journey_simulation": journey_simulation,
        "state_invariant_check": state_check,
        "cross_artifact_trace": trace,
        "open_questions": open_questions,
        "false_negative_challenge": false_negative,
        "phase2_review_coverage": phase2_coverage,
        "issue_projection": projected,
    }
