"""Runtime for the governed implementation spec testing skill."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import write_json
from cli.lib.impl_spec_journey_reviewer import build_journey_simulation, build_ux_review
from cli.lib.impl_spec_logic_redteam import build_cross_artifact_trace, build_logic_risk_inventory, build_state_invariant_check
from cli.lib.impl_spec_supervisor_review import build_false_negative_challenge, derive_review_coverage
from cli.lib.impl_spec_test_findings import make_evidence, make_finding, split_risk_findings
from cli.lib.impl_spec_test_review import build_counterexample_result, build_dimension_reviews, derive_semantic_findings
from cli.lib.impl_spec_test_semantics import build_semantic_review, build_system_views
from cli.lib.impl_spec_test_support import as_list, build_candidate_payload, load_document, load_optional_documents, safe_name, write_candidate_package
from cli.lib.mainline_runtime import submit_handoff
from cli.lib.managed_gateway import governed_write


SKILL_REF = "skill.qa.impl_spec_test"
RUNNER_SKILL_REF = "skill.runner.impl_spec_test"
ALLOWED_DOC_STATUSES = {"accepted", "approved", "execution_ready", "frozen"}
REPAIR_TARGETS = {"IMPL", "FEAT", "TECH", "ARCH", "API", "UI", "TESTSET", "MULTI"}
DEEP_TRIGGER_FLAGS = (
    "migration_required",
    "state_boundary_sensitive",
    "cross_surface_chain",
    "introduces_new_surface",
    "external_gate_candidate",
)


def _normalize_execution_mode(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    mode_payload = payload.get("execution_mode") if isinstance(payload.get("execution_mode"), dict) else {}
    requested_mode = str(mode_payload.get("mode") or "quick_preflight").strip().lower()
    if requested_mode not in {"quick_preflight", "deep_spec_testing"}:
        requested_mode = "quick_preflight"
    deep_triggers = [flag for flag in DEEP_TRIGGER_FLAGS if bool(payload.get(flag))]
    repo_context = payload.get("repo_context") if isinstance(payload.get("repo_context"), dict) else {}
    if str(repo_context.get("migration_notes_ref") or "").strip() and "migration_required" not in deep_triggers:
        deep_triggers.append("migration_required")
    mode = "deep_spec_testing" if requested_mode == "deep_spec_testing" or deep_triggers else "quick_preflight"
    return {
        "mode": mode,
        "requested_mode": requested_mode,
        "require_strong_self_contained": bool(mode_payload.get("require_strong_self_contained", True)),
        "allow_upstream_follow": bool(mode_payload.get("allow_upstream_follow", False)),
        "simulate_counterexamples": bool(mode_payload.get("simulate_counterexamples", mode == "deep_spec_testing")),
    }, deep_triggers


def _normalize_repo_context(payload: dict[str, Any]) -> dict[str, Any]:
    repo_context = payload.get("repo_context") if isinstance(payload.get("repo_context"), dict) else {}
    return {
        "enabled": bool(repo_context.get("enabled", bool(repo_context))),
        "touchable_paths": as_list(repo_context.get("touchable_paths")),
        "observable_paths": as_list(repo_context.get("observable_paths")),
        "migration_notes_ref": str(repo_context.get("migration_notes_ref") or "").strip(),
    }


def _normalize_risk_profile(payload: dict[str, Any]) -> dict[str, str]:
    risk_profile = payload.get("risk_profile") if isinstance(payload.get("risk_profile"), dict) else {}
    return {
        "domain": str(risk_profile.get("domain") or "product_impl").strip() or "product_impl",
        "strictness": str(risk_profile.get("strictness") or "high").strip() or "high",
    }


def _binding_rows(normalized: dict[str, Any]) -> list[dict[str, str]]:
    bindings: list[dict[str, str]] = []
    for label, key, required in (("IMPL", "impl", True), ("FEAT", "feat", True), ("TECH", "tech", True), ("ARCH", "arch", False), ("API", "api", False)):
        doc = normalized.get(key)
        bindings.append({"authority": label, "status": "bound" if doc else "missing", "ref": str(normalized.get(f"{key}_ref") or ""), "required": str(required).lower()})
    for label, docs_key in (("UI", "ui_docs"), ("TESTSET", "testset_docs")):
        refs = [doc["_source_ref"] for doc in normalized.get(docs_key, [])]
        bindings.append({"authority": label, "status": "bound" if refs else "missing", "ref": ",".join(refs), "required": "false"})
    return bindings


def _authority_finding(
    finding_id: str,
    *,
    category: str,
    severity: str,
    title: str,
    problem: str,
    why_it_matters: str,
    user_impact: str,
    counterexample: str,
    evidence: list[dict[str, str]],
    repair_target_artifact: str,
    suggested_fix: str,
    dimension: str,
    confidence: float = 0.9,
) -> dict[str, Any]:
    ensure(repair_target_artifact in REPAIR_TARGETS, "INVARIANT_VIOLATION", f"unsupported repair target: {repair_target_artifact}")
    return make_finding(
        finding_id,
        category=category,
        severity=severity,
        confidence=confidence,
        title=title,
        problem=problem,
        why_it_matters=why_it_matters,
        user_impact=user_impact,
        counterexample=counterexample,
        evidence=evidence,
        repair_target_artifact=repair_target_artifact,
        suggested_fix=suggested_fix,
        dimension=dimension,
    )


def _derive_authority_findings(normalized: dict[str, Any], deep_triggers: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    missing_information: list[str] = []
    impl = normalized["impl"]
    for field, expected, target in (("feat_ref", normalized["feat_ref"], "FEAT"), ("tech_ref", normalized["tech_ref"], "IMPL")):
        declared = str(impl.get(field) or "").strip()
        if declared and declared != expected:
            findings.append(
                _authority_finding(
                    f"conflict-{field}",
                    category="semantic",
                    severity="blocker",
                    title=f"IMPL declared {field} does not match the requested authority",
                    problem="The main tested object and the requested authority point to different upstream truth.",
                    why_it_matters="The review would be judging the wrong authority chain.",
                    user_impact="Implementation could start from a mismatched FEAT or TECH baseline.",
                    counterexample="The IMPL package says it was derived from one TECH object, but the request asks to review another.",
                    evidence=[make_evidence(impl["_source_ref"], section="frontmatter", excerpt=f"{field}={declared}"), make_evidence(expected, section="request payload")],
                    repair_target_artifact=target,
                    suggested_fix="Re-freeze the IMPL package or reroute the request to the matching upstream authority.",
                    dimension="functional_logic" if field == "feat_ref" else "implementation_executability",
                )
            )
    for label, doc in (("FEAT", normalized["feat"]), ("TECH", normalized["tech"])):
        status = str(doc.get("status") or "").strip()
        if status and status not in ALLOWED_DOC_STATUSES:
            findings.append(
                _authority_finding(
                    f"{label.lower()}-not-frozen",
                    category="semantic",
                    severity="blocker",
                    title=f"{label} is not in a freeze-ready state",
                    problem=f"{label} is linked as authority but is still in status={status}.",
                    why_it_matters="Implementation readiness cannot be claimed on top of an unstable upstream authority.",
                    user_impact="Coders may implement against a moving target.",
                    counterexample="A later FEAT or TECH revision changes the subject after coding already began.",
                    evidence=[make_evidence(doc["_source_ref"], section="frontmatter", excerpt=f"status={status}")],
                    repair_target_artifact=label,
                    suggested_fix=f"Freeze or approve the {label} object before implementation start.",
                    dimension="functional_logic" if label == "FEAT" else "implementation_executability",
                )
            )
    if not normalized.get("ui_docs"):
        findings.append(
            _authority_finding(
                "ui-authority-missing",
                category="ux_risk",
                severity="high",
                title="UI authority is missing",
                problem="No UI authority is bound, so user-facing entry and exit behavior is weakly evidenced.",
                why_it_matters="Journey and UX checks cannot close the loop without a UI surface.",
                user_impact="Users may encounter copy or blocking mismatches that the review cannot see.",
                counterexample="The state logic is non-blocking, but the eventual UI copy silently hard-blocks the user.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="request context")],
                repair_target_artifact="UI",
                suggested_fix="Freeze a UI authority or explicitly document why the slice remains UI-free.",
                dimension="ui_usability",
                confidence=0.76,
            )
        )
        missing_information.append("ui authority ref is missing")
    if not normalized.get("testset_docs"):
        findings.append(
            _authority_finding(
                "testset-authority-missing",
                category="testability",
                severity="high",
                title="TESTSET authority is missing",
                problem="No TESTSET authority is bound, so acceptance truth remains provisional.",
                why_it_matters="The review cannot prove completion and failure coverage end to end.",
                user_impact="Critical failure behavior may reach coding without acceptance coverage.",
                counterexample="The implementation starts coding even though no TESTSET says what completion or failure handling must be observed.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="request context")],
                repair_target_artifact="TESTSET",
                suggested_fix="Freeze a TESTSET authority before final execution or sign-off.",
                dimension="testability",
                confidence=0.8,
            )
        )
        missing_information.append("testset authority ref is missing")
    for doc in normalized.get("testset_docs", []):
        status = str(doc.get("status") or "").strip()
        if status and status not in ALLOWED_DOC_STATUSES:
            findings.append(
                _authority_finding(
                    "testset-not-frozen",
                    category="testability",
                    severity="high",
                    title="TESTSET authority is present but not freeze-ready",
                    problem=f"TESTSET is linked but still in status={status}.",
                    why_it_matters="Acceptance truth exists but is not stable enough for implementation dispatch.",
                    user_impact="The coder can meet one TESTSET revision and still fail the final accepted one.",
                    counterexample="The report passes against a provisional TESTSET that later changes failure handling expectations.",
                    evidence=[make_evidence(doc["_source_ref"], section="frontmatter", excerpt=f"status={status}")],
                    repair_target_artifact="TESTSET",
                    suggested_fix="Freeze the TESTSET authority before coding.",
                    dimension="testability",
                    confidence=0.75,
                )
            )
    if normalized.get("migration_required") and not normalized["repo_context"]["migration_notes_ref"]:
        findings.append(
            _authority_finding(
                "migration-notes-missing",
                category="logic",
                severity="high",
                title="Migration is required but migration notes are missing",
                problem="The request marks migration as required, but there is no migration notes authority in repo context.",
                why_it_matters="Compatibility, rollback, and precedence cannot be judged reliably.",
                user_impact="Users can hit inconsistent behavior during migration windows.",
                counterexample="Old and new fields coexist, but the coder has no frozen fallback notes to implement against.",
                evidence=[make_evidence(normalized["impl"]["_source_ref"], section="request context")],
                repair_target_artifact="IMPL",
                suggested_fix="Attach migration notes before coding or gate review.",
                dimension="migration_compatibility",
                confidence=0.83,
            )
        )
        missing_information.append("migration notes are missing")
    if deep_triggers and not normalized["execution_mode"]["simulate_counterexamples"]:
        findings.append(
            _authority_finding(
                "counterexample-simulation-disabled",
                category="logic",
                severity="low",
                title="Counterexample simulation is disabled while deep mode is required",
                problem="Deep mode was triggered, but counterexample simulation is off.",
                why_it_matters="Failure-path coverage will be thinner than the requested mode implies.",
                user_impact="Risky implementation edges may survive the review.",
                counterexample="The flow is reviewed in deep mode, but no failure family is actually stress-tested.",
                evidence=[make_evidence(",".join(deep_triggers), section="execution_mode")],
                repair_target_artifact="IMPL",
                suggested_fix="Enable counterexample simulation for deep runs.",
                dimension="implementation_executability",
                confidence=0.7,
            )
        )
    if not as_list(normalized.get("source_refs")) and not as_list(impl.get("source_refs")):
        missing_information.append("source_refs are missing")
    return split_risk_findings(findings) + (list(dict.fromkeys(missing_information)),)


def _repair_target(blocking: list[dict[str, Any]], high: list[dict[str, Any]]) -> str:
    target = str((blocking or high or [{"repair_target_artifact": "IMPL"}])[0].get("repair_target_artifact") or "IMPL").upper()
    return target if target in REPAIR_TARGETS else "IMPL"


def _journey_summary(journey_simulation: dict[str, Any]) -> dict[str, int]:
    summary = {"covered": 0, "partial": 0, "gap": 0}
    for item in journey_simulation.get("simulations", []):
        status = str(item.get("status") or "gap")
        if status in summary:
            summary[status] += 1
    return summary


def _build_summary(
    normalized: dict[str, Any],
    dimension_reviews: dict[str, dict[str, Any]],
    blocking: list[dict[str, Any]],
    high: list[dict[str, Any]],
    review_coverage: dict[str, Any],
) -> dict[str, Any]:
    self_contained_mode = "strong_self_contained" if normalized["execution_mode"]["require_strong_self_contained"] else "upstream_follow_allowed"
    impl_exec = int(dimension_reviews["implementation_executability"]["score"])
    testability = int(dimension_reviews["testability"]["score"])
    coverage_status = str(review_coverage.get("status") or "insufficient")
    self_contained_readiness = "sufficient"
    if blocking or high or coverage_status != "sufficient" or (self_contained_mode == "strong_self_contained" and not normalized.get("testset_docs")):
        self_contained_readiness = "insufficient"
    verdict = "pass"
    if blocking:
        verdict = "block"
    elif impl_exec < 6 or testability < 6 or coverage_status != "sufficient" or len({item.get("dimension") for item in high if item.get("dimension")}) >= 2:
        verdict = "pass_with_revisions"
    elif self_contained_readiness == "insufficient" and self_contained_mode == "strong_self_contained":
        verdict = "pass_with_revisions"
    return {
        "verdict": verdict,
        "implementation_readiness": {"pass": "ready", "pass_with_revisions": "partial", "block": "not_ready"}[verdict],
        "self_contained_readiness": self_contained_readiness,
        "self_contained_evaluation_mode": self_contained_mode,
        "recommended_next_action": {"pass": "proceed_to_gate", "pass_with_revisions": "revise_impl", "block": "rederive_upstream"}[verdict],
        "recommended_actor": {"pass": "human_gate", "pass_with_revisions": "impl_author", "block": "upstream_owner"}[verdict],
        "repair_target_artifact": _repair_target(blocking, high),
        "run_status": {"pass": "completed", "pass_with_revisions": "completed_with_findings", "block": "completed_with_blockers"}[verdict],
    }


def execute_impl_spec_test_skill(workspace_root: Path, trace: dict[str, Any], request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    for field in ("impl_ref", "impl_package_ref", "feat_ref", "tech_ref"):
        ensure(str(payload.get(field) or "").strip(), "INVALID_REQUEST", f"missing skill field: {field}")
    execution_mode, deep_triggers = _normalize_execution_mode(payload)
    normalized = {
        "impl_ref": str(payload["impl_ref"]).strip(),
        "impl_package_ref": str(payload["impl_package_ref"]).strip(),
        "feat_ref": str(payload["feat_ref"]).strip(),
        "tech_ref": str(payload["tech_ref"]).strip(),
        "arch_ref": str(payload.get("arch_ref") or "").strip(),
        "api_ref": str(payload.get("api_ref") or "").strip(),
        "ui_refs": as_list(payload.get("ui_refs") or payload.get("ui_ref")),
        "testset_refs": as_list(payload.get("testset_refs") or payload.get("testset_ref")),
        "source_refs": as_list(payload.get("source_refs")),
        "repo_context": _normalize_repo_context(payload),
        "risk_profile": _normalize_risk_profile(payload),
        "execution_mode": execution_mode,
        "deep_mode_triggers": deep_triggers,
        "migration_required": bool(payload.get("migration_required")),
    }
    normalized["impl"] = load_document(normalized["impl_ref"], workspace_root, expected_type="IMPL")
    normalized["impl_package"] = load_document(normalized["impl_package_ref"], workspace_root)
    normalized["feat"] = load_document(normalized["feat_ref"], workspace_root, expected_type="FEAT")
    normalized["tech"] = load_document(normalized["tech_ref"], workspace_root, expected_type="TECH")
    normalized["arch"] = load_document(normalized["arch_ref"], workspace_root, expected_type="ARCH") if normalized["arch_ref"] else None
    normalized["api"] = load_document(normalized["api_ref"], workspace_root, expected_type="API") if normalized["api_ref"] else None
    normalized["ui_docs"] = load_optional_documents(normalized["ui_refs"], workspace_root) if normalized["ui_refs"] else []
    normalized["testset_docs"] = load_optional_documents(normalized["testset_refs"], workspace_root, expected_type="TESTSET") if normalized["testset_refs"] else []
    normalized["resolved_refs"] = {
        "impl_ref": normalized["impl"]["_source_ref"],
        "impl_package_ref": normalized["impl_package"]["_source_ref"],
        "feat_ref": normalized["feat"]["_source_ref"],
        "tech_ref": normalized["tech"]["_source_ref"],
        "arch_ref": normalized["arch"]["_source_ref"] if normalized.get("arch") else "",
        "api_ref": normalized["api"]["_source_ref"] if normalized.get("api") else "",
        "ui_refs": [doc["_source_ref"] for doc in normalized["ui_docs"]],
        "testset_refs": [doc["_source_ref"] for doc in normalized["testset_docs"]],
    }

    bindings = _binding_rows(normalized)
    a_blocking, a_high, a_normal, missing_information = _derive_authority_findings(normalized, deep_triggers)
    semantic_review = build_semantic_review(normalized)
    system_views = build_system_views(semantic_review)
    cross_artifact_trace = build_cross_artifact_trace(normalized, semantic_review, system_views)
    state_invariant_check = build_state_invariant_check(normalized, semantic_review, system_views)
    s_blocking, s_high, s_normal, s_missing = derive_semantic_findings(normalized, semantic_review, system_views)
    logic_findings, open_questions = build_logic_risk_inventory(normalized, semantic_review, system_views, cross_artifact_trace, state_invariant_check)
    journey_simulation = build_journey_simulation(normalized, semantic_review, system_views)
    ux_risks, ux_improvements = build_ux_review(normalized, semantic_review, system_views, journey_simulation)

    blocking, high, normal = split_risk_findings(a_blocking + a_high + a_normal + s_blocking + s_high + s_normal + logic_findings + ux_risks)
    missing_information = list(dict.fromkeys(missing_information + s_missing + open_questions))
    dimension_reviews = build_dimension_reviews(semantic_review, system_views, blocking, high, normal, missing_information)
    counterexample_result = build_counterexample_result(normalized, semantic_review, system_views, dimension_reviews, blocking, high)
    false_negative_challenge = build_false_negative_challenge(normalized, semantic_review, dimension_reviews, blocking + high + normal + logic_findings, ux_risks, open_questions)
    review_coverage = derive_review_coverage(
        mode=normalized["execution_mode"]["mode"],
        dimension_reviews=dimension_reviews,
        counterexample_gap_dimensions=counterexample_result.get("required_gap_dimensions", []),
        open_questions=open_questions,
        false_negative_challenge=false_negative_challenge,
    )
    readiness_summary = _build_summary(normalized, dimension_reviews, blocking, high, review_coverage)

    phase2_review = {
        "logic_risk_inventory": {
            "summary": {"blocking": len([item for item in logic_findings if item["severity"] == "blocker"]), "high": len([item for item in logic_findings if item["severity"] == "high"]), "normal": len([item for item in logic_findings if item["severity"] in {"medium", "low"}])},
            "findings": logic_findings,
        },
        "ux_risk_inventory": {"summary": {"risks": len(ux_risks)}, "findings": ux_risks},
        "ux_improvement_inventory": {"summary": {"improvements": len(ux_improvements)}, "findings": ux_improvements},
        "journey_simulation": {"summary": _journey_summary(journey_simulation), **journey_simulation},
        "state_invariant_check": {"status": "conflicted" if state_invariant_check["conflicted_invariants"] else ("partial" if state_invariant_check["unclear_invariants"] else "supported"), **state_invariant_check},
        "cross_artifact_trace": cross_artifact_trace,
        "open_questions": open_questions,
        "false_negative_challenge": {"status": "raised" if false_negative_challenge.get("findings") else "clear", **false_negative_challenge},
    }
    repair_plan = {
        "immediate": [item["suggested_fix"] for item in blocking] or ["confirm verdict package and gate routing"],
        "before_coding": [item["suggested_fix"] for item in high] or ["retain the frozen IMPL boundary and linked authority refs"],
        "during_coding": ["Preserve authority non-override and keep downstream handoff aligned to the verdict package."],
    }
    issue_inventory = {"summary": {"blocking": len(blocking), "high_priority": len(high), "normal": len(normal)}, "blocking_issues": blocking, "high_priority_issues": high, "normal_issues": normal}
    intake_result = {
        "main_test_object_ref": normalized["impl"]["_source_ref"],
        "authority_bindings": bindings,
        "execution_mode": normalized["execution_mode"],
        "deep_mode_triggers": deep_triggers,
        "repo_context": normalized["repo_context"],
        "risk_profile": normalized["risk_profile"],
    }
    candidate = {
        "trace": trace,
        "readiness_summary": {
            "dimension_scores": {name: int(review["score"]) for name, review in dimension_reviews.items()},
            **readiness_summary,
            "missing_information": missing_information,
            "repair_plan": repair_plan,
            "counterexample_gap_dimensions": counterexample_result.get("required_gap_dimensions", []),
            "review_coverage_status": review_coverage.get("status"),
        },
        "blocking_issues": blocking,
        "high_priority_issues": high,
        "normal_issues": normal,
        "missing_information": missing_information,
        "repair_plan": repair_plan,
        "counterexample_result": counterexample_result,
        "intake_result": intake_result,
        "issue_inventory": issue_inventory,
        "execution_mode": normalized["execution_mode"],
        "resolved_refs": normalized["resolved_refs"],
        "semantic_review": semantic_review,
        "system_views": system_views,
        "dimension_reviews": dimension_reviews,
        "review_coverage": review_coverage,
        "phase2_review": phase2_review,
    }
    refs = write_candidate_package(workspace_root, request_id, normalized, candidate)
    candidate_ref = f"candidate.{safe_name(f'impl-spec-test-{request_id}')}"
    staging_ref = f".workflow/runs/{trace.get('run_ref', request_id)}/generated/{safe_name(candidate_ref)}.json"
    write_json(workspace_root / staging_ref, build_candidate_payload(request_id, normalized, candidate, refs, skill_ref=SKILL_REF, runner_skill_ref=RUNNER_SKILL_REF))
    gateway_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=request_id,
        artifact_ref=candidate_ref,
        workspace_path=f"artifacts/active/qa/impl-spec-test-candidates/{safe_name(candidate_ref)}.json",
        requested_mode="write",
        content_ref=staging_ref,
        overwrite=True,
    )
    handoff_result = submit_handoff(
        workspace_root,
        trace=trace,
        producer_ref=SKILL_REF,
        proposal_ref=str(payload.get("proposal_ref") or request_id),
        payload_ref=gateway_result["managed_artifact_ref"],
        pending_state="gate_pending",
        trace_context_ref=str(trace.get("run_ref") or request_id),
    )
    return {
        "skill_ref": SKILL_REF,
        "runner_skill_ref": RUNNER_SKILL_REF,
        "candidate_artifact_ref": candidate_ref,
        "candidate_managed_artifact_ref": gateway_result["managed_artifact_ref"],
        "candidate_receipt_ref": gateway_result["receipt_ref"],
        "candidate_registry_record_ref": gateway_result["registry_record_ref"],
        "handoff_ref": handoff_result["handoff_ref"],
        "gate_pending_ref": handoff_result["gate_pending_ref"],
        "run_status": readiness_summary["run_status"],
        "verdict": readiness_summary["verdict"],
        "implementation_readiness": readiness_summary["implementation_readiness"],
        "self_contained_readiness": readiness_summary["self_contained_readiness"],
        "self_contained_evaluation_mode": readiness_summary["self_contained_evaluation_mode"],
        "recommended_next_action": readiness_summary["recommended_next_action"],
        "recommended_actor": readiness_summary["recommended_actor"],
        "repair_target_artifact": readiness_summary["repair_target_artifact"],
        "execution_mode": normalized["execution_mode"]["mode"],
        "report_package_ref": refs["package_manifest_ref"],
        "report_json_ref": refs["report_json_ref"],
        "report_markdown_ref": refs["report_md_ref"],
        "phase2_review_ref": refs["phase2_review_ref"],
        "semantic_review_ref": refs["semantic_review_ref"],
        "system_views_ref": refs["system_views_ref"],
        "dimension_reviews_ref": refs["dimension_reviews_ref"],
        "review_coverage_ref": refs["review_coverage_ref"],
        "logic_risk_inventory_ref": refs["logic_risk_inventory_ref"],
        "ux_risk_inventory_ref": refs["ux_risk_inventory_ref"],
        "ux_improvement_inventory_ref": refs["ux_improvement_inventory_ref"],
        "journey_simulation_ref": refs["journey_simulation_ref"],
        "state_invariant_check_ref": refs["state_invariant_check_ref"],
        "cross_artifact_trace_ref": refs["cross_artifact_trace_ref"],
        "open_questions_ref": refs["open_questions_ref"],
        "false_negative_challenge_ref": refs["false_negative_challenge_ref"],
        "defects_ref": refs["defects_ref"],
        "counterexample_result_ref": refs["counterexamples_ref"],
        "gate_subject_ref": refs["gate_subject_ref"],
        "intake_result_ref": refs["intake_ref"],
        "issue_inventory_ref": refs["issue_inventory_ref"],
        "readiness_verdict_ref": refs["verdict_ref"],
        "repair_suggestions_ref": refs["repair_ref"],
        "execution_evidence_ref": refs["execution_evidence_ref"],
        "supervision_evidence_ref": refs["supervision_evidence_ref"],
    }

