"""Support helpers for the governed implementation spec test runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, read_text, to_canonical_path, write_json, write_text
from cli.lib.registry_store import slugify


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value).strip()]


def safe_name(value: str) -> str:
    return slugify(value) or "impl-spec-test"


def _parse_markdown_document(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    frontmatter = yaml.safe_load(text[4:end]) or {}
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    return frontmatter, text[end + 5 :]


def _resolve_document_path(ref_value: str, workspace_root: Path) -> Path:
    candidate = canonical_to_path(ref_value, workspace_root)
    if candidate.exists():
        return candidate.resolve()
    ssot_root = workspace_root / "ssot"
    ensure(ssot_root.exists(), "PRECONDITION_FAILED", "ssot root missing")
    matches = sorted(path for path in ssot_root.rglob("*") if path.is_file() and path.stem.startswith(ref_value))
    ensure(matches, "PRECONDITION_FAILED", f"document not found: {ref_value}")
    ensure(len(matches) == 1, "PRECONDITION_FAILED", f"document ref is ambiguous: {ref_value}")
    return matches[0].resolve()


def load_document(ref_value: str, workspace_root: Path, *, expected_type: str | None = None) -> dict[str, Any]:
    path = _resolve_document_path(ref_value, workspace_root)
    text = read_text(path)
    suffix = path.suffix.lower()
    payload: dict[str, Any]
    body = ""
    if suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(text) or {}
        ensure(isinstance(payload, dict), "INVALID_REQUEST", f"yaml document must be an object: {ref_value}")
    elif suffix == ".json":
        payload = json.loads(text)
        ensure(isinstance(payload, dict), "INVALID_REQUEST", f"json document must be an object: {ref_value}")
    else:
        payload, body = _parse_markdown_document(text)
    payload["_path"] = path.as_posix()
    payload["_source_ref"] = to_canonical_path(path, workspace_root)
    payload["_body"] = body
    if expected_type:
        actual = str(payload.get("ssot_type") or "").strip()
        ensure(actual == expected_type, "PRECONDITION_FAILED", f"{ref_value} must resolve to {expected_type}")
    return payload


def load_optional_documents(refs: list[str], workspace_root: Path, *, expected_type: str | None = None) -> list[dict[str, Any]]:
    return [load_document(ref_value, workspace_root, expected_type=expected_type) for ref_value in refs]


def _report_markdown(candidate: dict[str, Any]) -> str:
    payload = candidate["readiness_summary"]
    bindings = candidate["intake_result"]["authority_bindings"]
    dimension_reviews = candidate.get("dimension_reviews", {})
    phase2_review = candidate.get("phase2_review", {})
    logic_risks = phase2_review.get("logic_risk_inventory", {})
    ux_risks = phase2_review.get("ux_risk_inventory", {})
    journey_simulation = phase2_review.get("journey_simulation", {})
    state_check = phase2_review.get("state_invariant_check", {})
    false_negative = phase2_review.get("false_negative_challenge", {})
    lines = [
        "# Impl Spec Test Report",
        "",
        f"- verdict: {payload['verdict']}",
        f"- implementation_readiness: {payload['implementation_readiness']}",
        f"- self_contained_readiness: {payload['self_contained_readiness']}",
        f"- execution_mode: {candidate['execution_mode']['mode']}",
        f"- recommended_next_action: {payload['recommended_next_action']}",
        f"- recommended_actor: {payload['recommended_actor']}",
        f"- repair_target_artifact: {payload['repair_target_artifact']}",
        "",
        "## Dimension Reviews",
        "",
    ]
    for name, review in dimension_reviews.items():
        lines.append(f"- {name}: score={review.get('score')} coverage_confidence={review.get('coverage_confidence')}")
    lines.extend(
        [
            "",
        "## Authority Bindings",
        "",
        ]
    )
    lines.extend(f"- {item['authority']}: {item['status']} ({item['ref'] or 'n/a'})" for item in bindings)
    lines.extend(["", "## Missing Information", ""])
    if candidate["missing_information"]:
        lines.extend(f"- {item}" for item in candidate["missing_information"])
    else:
        lines.append("- none")
    lines.extend(["", "## Counterexample Coverage", ""])
    coverage = candidate.get("review_coverage", {})
    lines.append(f"- status: {coverage.get('status', 'unknown')}")
    gap_dimensions = coverage.get("counterexample_gap_dimensions", [])
    lines.append(f"- counterexample_gap_dimensions: {', '.join(gap_dimensions) if gap_dimensions else 'none'}")
    if phase2_review:
        lines.extend(["", "## Phase 2 Review", ""])
        lines.append(f"- logic_risks: {logic_risks.get('summary', {}).get('blocking', 0)} blocker / {logic_risks.get('summary', {}).get('high', 0)} high")
        lines.append(f"- ux_risks: {ux_risks.get('summary', {}).get('risks', 0)}")
        lines.append(f"- ux_improvements: {ux_risks.get('summary', {}).get('improvements', 0)}")
        lines.append(f"- journey_scenarios: {journey_simulation.get('summary', {}).get('covered', 0)} covered")
        lines.append(f"- state_invariant_check: {state_check.get('status', 'unknown')}")
        lines.append(f"- false_negative_challenge: {false_negative.get('status', 'unknown')}")
    return "\n".join(lines) + "\n"


def write_candidate_package(workspace_root: Path, request_id: str, normalized: dict[str, Any], candidate: dict[str, Any]) -> dict[str, str]:
    report_slug = safe_name(f"{request_id}-{normalized['impl_ref']}")
    base_ref = f"artifacts/active/qa/impl-spec-tests/{report_slug}"
    base_path = workspace_root / base_ref
    refs = {
        "package_manifest_ref": f"{base_ref}/package-manifest.json",
        "report_json_ref": f"{base_ref}/impl-spec-test-report.json",
        "report_md_ref": f"{base_ref}/impl-spec-test-report.md",
        "phase2_review_ref": f"{base_ref}/phase2-review.json",
        "semantic_review_ref": f"{base_ref}/semantic-review.json",
        "system_views_ref": f"{base_ref}/system-views.json",
        "dimension_reviews_ref": f"{base_ref}/dimension-reviews.json",
        "review_coverage_ref": f"{base_ref}/review-coverage.json",
        "logic_risk_inventory_ref": f"{base_ref}/logic-risk-inventory.json",
        "ux_risk_inventory_ref": f"{base_ref}/ux-risk-inventory.json",
        "ux_improvement_inventory_ref": f"{base_ref}/ux-improvement-inventory.json",
        "journey_simulation_ref": f"{base_ref}/journey-simulation.json",
        "state_invariant_check_ref": f"{base_ref}/state-invariant-check.json",
        "cross_artifact_trace_ref": f"{base_ref}/cross-artifact-trace.json",
        "open_questions_ref": f"{base_ref}/open-questions.json",
        "false_negative_challenge_ref": f"{base_ref}/false-negative-challenge.json",
        "defects_ref": f"{base_ref}/impl-spec-test-defects.json",
        "counterexamples_ref": f"{base_ref}/impl-spec-test-counterexamples.json",
        "gate_subject_ref": f"{base_ref}/impl-spec-test-gate-subject.json",
        "repair_ref": f"{base_ref}/repair-patch-suggestions.md",
        "intake_ref": f"{base_ref}/implementation-readiness-intake.json",
        "issue_inventory_ref": f"{base_ref}/cross-artifact-issue-inventory.json",
        "verdict_ref": f"{base_ref}/implementation-readiness-verdict.json",
        "execution_evidence_ref": f"{base_ref}/execution-evidence.json",
        "supervision_evidence_ref": f"{base_ref}/supervision-evidence.json",
    }
    defects_payload = {
        "blocking_issues": candidate["blocking_issues"],
        "high_priority_issues": candidate["high_priority_issues"],
        "normal_issues": candidate["normal_issues"],
    }
    gate_subject_payload = {
        "artifact_type": "implementation_readiness_gate_subject",
        "impl_ref": normalized["impl"]["_source_ref"],
        "verdict": candidate["readiness_summary"]["verdict"],
        "implementation_readiness": candidate["readiness_summary"]["implementation_readiness"],
        "repair_target_artifact": candidate["readiness_summary"]["repair_target_artifact"],
        "recommended_next_action": candidate["readiness_summary"]["recommended_next_action"],
        "blocking_issue_count": len(candidate["blocking_issues"]),
        "high_priority_issue_count": len(candidate["high_priority_issues"]),
    }
    repair_markdown = "\n".join(
        [
            "# Repair Suggestions",
            "",
            "## Immediate",
            *(f"- {item}" for item in candidate["repair_plan"]["immediate"]),
            "",
            "## Before Coding",
            *(f"- {item}" for item in candidate["repair_plan"]["before_coding"]),
            "",
            "## During Coding",
            *(f"- {item}" for item in candidate["repair_plan"]["during_coding"]),
            "",
        ]
    )
    write_json(base_path / "package-manifest.json", {"artifact_type": "impl_spec_test_report_package", **candidate, "package_manifest_ref": refs["package_manifest_ref"]})
    write_json(base_path / "impl-spec-test-report.json", candidate)
    write_text(base_path / "impl-spec-test-report.md", _report_markdown(candidate))
    phase2_review = candidate.get("phase2_review", {})
    write_json(base_path / "phase2-review.json", phase2_review)
    write_json(base_path / "semantic-review.json", candidate.get("semantic_review", {}))
    write_json(base_path / "system-views.json", candidate.get("system_views", {}))
    write_json(base_path / "dimension-reviews.json", candidate.get("dimension_reviews", {}))
    write_json(base_path / "review-coverage.json", candidate.get("review_coverage", {}))
    write_json(base_path / "logic-risk-inventory.json", phase2_review.get("logic_risk_inventory", {}))
    write_json(base_path / "ux-risk-inventory.json", phase2_review.get("ux_risk_inventory", {}))
    write_json(base_path / "ux-improvement-inventory.json", phase2_review.get("ux_improvement_inventory", {}))
    write_json(base_path / "journey-simulation.json", phase2_review.get("journey_simulation", {}))
    write_json(base_path / "state-invariant-check.json", phase2_review.get("state_invariant_check", {}))
    write_json(base_path / "cross-artifact-trace.json", phase2_review.get("cross_artifact_trace", {}))
    write_json(base_path / "open-questions.json", phase2_review.get("open_questions", []))
    write_json(base_path / "false-negative-challenge.json", phase2_review.get("false_negative_challenge", {}))
    write_json(base_path / "impl-spec-test-defects.json", defects_payload)
    write_json(base_path / "impl-spec-test-counterexamples.json", candidate["counterexample_result"])
    write_json(base_path / "impl-spec-test-gate-subject.json", gate_subject_payload)
    write_text(base_path / "repair-patch-suggestions.md", repair_markdown)
    write_json(base_path / "implementation-readiness-intake.json", candidate["intake_result"])
    write_json(base_path / "cross-artifact-issue-inventory.json", candidate["issue_inventory"])
    write_json(base_path / "implementation-readiness-verdict.json", candidate["readiness_summary"])
    write_json(
        base_path / "execution-evidence.json",
        {
            "request_id": request_id,
            "execution_mode": normalized["execution_mode"],
            "repo_context": normalized.get("repo_context", {}),
            "risk_profile": normalized.get("risk_profile", {}),
            "refs": normalized["resolved_refs"],
            "phase2_review": {
                "logic_risk_inventory": refs["logic_risk_inventory_ref"],
                "ux_risk_inventory": refs["ux_risk_inventory_ref"],
                "ux_improvement_inventory": refs["ux_improvement_inventory_ref"],
                "journey_simulation": refs["journey_simulation_ref"],
                "state_invariant_check": refs["state_invariant_check_ref"],
                "cross_artifact_trace": refs["cross_artifact_trace_ref"],
                "open_questions": refs["open_questions_ref"],
                "false_negative_challenge": refs["false_negative_challenge_ref"],
            },
        },
    )
    write_json(
        base_path / "supervision-evidence.json",
        {
            "authority_bindings": candidate["intake_result"]["authority_bindings"],
            "issue_counts": candidate["issue_inventory"]["summary"],
            "review_coverage": candidate.get("review_coverage", {}),
            "dimension_reviews": candidate.get("dimension_reviews", {}),
            "phase2_review": {
                "logic_risk_inventory": phase2_review.get("logic_risk_inventory", {}),
                "ux_risk_inventory": phase2_review.get("ux_risk_inventory", {}),
                "journey_simulation": phase2_review.get("journey_simulation", {}),
                "state_invariant_check": phase2_review.get("state_invariant_check", {}),
                "false_negative_challenge": phase2_review.get("false_negative_challenge", {}),
            },
        },
    )
    return refs


def build_candidate_payload(
    request_id: str,
    normalized: dict[str, Any],
    candidate: dict[str, Any],
    refs: dict[str, str],
    *,
    skill_ref: str,
    runner_skill_ref: str,
) -> dict[str, Any]:
    return {
        "artifact_type": "governed_impl_spec_test_candidate",
        "request_id": request_id,
        "skill_ref": skill_ref,
        "runner_skill_ref": runner_skill_ref,
        "impl_ref": normalized["impl"]["_source_ref"],
        "impl_package_ref": normalized["impl_package"]["_source_ref"],
        "feat_ref": normalized["feat"]["_source_ref"],
        "tech_ref": normalized["tech"]["_source_ref"],
        "arch_ref": normalized["arch"]["_source_ref"] if normalized.get("arch") else "",
        "api_ref": normalized["api"]["_source_ref"] if normalized.get("api") else "",
        "ui_refs": [doc["_source_ref"] for doc in normalized.get("ui_docs", [])],
        "testset_refs": [doc["_source_ref"] for doc in normalized.get("testset_docs", [])],
        "execution_mode": normalized["execution_mode"]["mode"],
        "deep_mode_triggers": normalized["deep_mode_triggers"],
        "run_status": candidate["readiness_summary"]["run_status"],
        "verdict": candidate["readiness_summary"]["verdict"],
        "implementation_readiness": candidate["readiness_summary"]["implementation_readiness"],
        "repair_target_artifact": candidate["readiness_summary"]["repair_target_artifact"],
        **refs,
    }
