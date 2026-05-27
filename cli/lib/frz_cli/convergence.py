"""Step_5 — Comprehensive verdict engine and dual-line AND gate convergence.

Truth source: design.md §impl-verify step_5, §AND gate.
"""

from __future__ import annotations

from typing import Any

from frz_cli.models import VerificationReport


def compute_final_verdict(
    task_completion: dict[str, Any],
    engineering_docs: dict[str, Any],
    feature_scope: dict[str, Any],
    traceability: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute comprehensive verdict from all sub-checks.

    Returns dict with final_verdict, verdict_reason, blocking_issues, warnings, conditions.
    """
    cfg = config or {}
    allow_partial_trace = cfg.get("allow_partial_trace", True)
    allow_partial_engineering_docs = cfg.get("allow_partial_engineering_docs", False)
    fail_on_warning = cfg.get("fail_on_warning", False)

    blocking_issues: list[dict[str, Any]] = []
    warnings_list: list[dict[str, Any]] = []
    conditions: list[dict[str, Any]] = []

    # Task completion
    if task_completion.get("task_completion") == "fail":
        blocking_issues.append({"check": "task_completion", "reason": "Tasks incomplete"})
    if task_completion.get("scope_compliance") == "fail":
        blocking_issues.append({"check": "scope_compliance", "reason": "Files out of scope"})

    # Engineering docs
    eng = engineering_docs.get("engineering_docs", "pass")
    if eng == "fail":
        blocking_issues.append({"check": "engineering_docs", "reason": "Missing required docs"})
    elif eng == "partial":
        if allow_partial_engineering_docs:
            conditions.append({"check": "engineering_docs", "action": "Complete missing docs"})
        else:
            blocking_issues.append({"check": "engineering_docs", "reason": "Partial docs not allowed"})

    # Feature scope
    if feature_scope.get("scope_compliance") == "fail":
        blocking_issues.append({"check": "feature_scope", "reason": "Unauthorized features detected"})
    for uf in feature_scope.get("unauthorized_features", []):
        blocking_issues.append({"check": "unauthorized_feature", "detail": uf})

    # Traceability
    tr = traceability.get("traceability", "pass")
    if tr == "fail":
        blocking_issues.append({"check": "traceability", "reason": "Untraceable changes"})
    elif tr == "conditional_pass":
        if allow_partial_trace:
            conditions.append({"check": "traceability", "action": "Add traceability for partial items"})
        else:
            blocking_issues.append({"check": "traceability", "reason": "Partial trace not allowed"})

    # Warnings
    for w in engineering_docs.get("doc_quality_warnings", []):
        warnings_list.append(w)

    if blocking_issues:
        final_verdict = "fail"
        verdict_reason = f"{len(blocking_issues)} blocking issue(s) found"
    elif conditions:
        final_verdict = "conditional_pass"
        verdict_reason = "All checks pass with conditions"
    else:
        final_verdict = "pass"
        verdict_reason = "All checks passed"

    return {
        "final_verdict": final_verdict,
        "verdict_reason": verdict_reason,
        "blocking_issues": blocking_issues,
        "warnings": warnings_list,
        "conditions": conditions,
    }


def converge_and_gate(
    line_1_result: dict[str, Any],
    line_2_result: dict[str, Any],
    timeout: bool = False,
) -> dict[str, Any]:
    """AND gate convergence for dual-line verification.

    Line 1: v1 test_execution
    Line 2: impl-verify
    """
    if timeout:
        return {
            "convergence": "fail",
            "release_ready": False,
            "blocking_line": "timeout",
            "line_1_verdict": line_1_result.get("verdict", "unknown"),
            "line_2_verdict": line_2_result.get("verdict", "unknown"),
            "line_1_issues": line_1_result.get("issues", []),
            "line_2_issues": line_2_result.get("issues", []),
            "conditions": [{"check": "convergence", "action": "Re-run after timeout resolution"}],
        }

    v1 = line_1_result.get("verdict", "fail")
    v2 = line_2_result.get("verdict", "fail")

    if v1 == "pass" and v2 == "pass":
        convergence = "pass"
        release_ready = True
        blocking_line = None
    elif v1 == "pass" and v2 == "conditional_pass":
        convergence = "conditional_pass"
        release_ready = False
        blocking_line = "line_2"
    else:
        convergence = "fail"
        release_ready = False
        blocking_line = "line_1" if v1 != "pass" else "line_2"

    return {
        "convergence": convergence,
        "release_ready": release_ready,
        "blocking_line": blocking_line,
        "line_1_verdict": v1,
        "line_2_verdict": v2,
        "line_1_issues": line_1_result.get("issues", []),
        "line_2_issues": line_2_result.get("issues", []),
        "conditions": line_2_result.get("conditions", []),
    }
