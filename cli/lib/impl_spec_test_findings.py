"""Common finding helpers for impl spec deep review."""

from __future__ import annotations

from typing import Any


SEVERITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3, "opportunity": 4}


def text(value: Any) -> str:
    return str(value or "").strip()


def make_evidence(ref: str, *, section: str = "", excerpt: str = "", line_hint: str = "") -> dict[str, str]:
    return {
        "ref": text(ref),
        "section": text(section),
        "excerpt": text(excerpt),
        "line_hint": text(line_hint),
    }


def make_finding(
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
    dimension: str,
) -> dict[str, Any]:
    return {
        "id": text(finding_id),
        "category": text(category),
        "severity": text(severity),
        "confidence": round(float(confidence), 2),
        "title": text(title),
        "problem": text(problem),
        "why_it_matters": text(why_it_matters),
        "user_impact": text(user_impact),
        "counterexample": text(counterexample),
        "evidence": [item for item in evidence if text(item.get("ref"))],
        "repair_target_artifact": text(repair_target_artifact),
        "suggested_fix": text(suggested_fix),
        "dimension": text(dimension),
    }


def sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(findings, key=lambda item: (SEVERITY_ORDER.get(str(item.get("severity")), 99), str(item.get("id"))))


def split_risk_findings(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    blocking = [item for item in findings if item.get("severity") == "blocker"]
    high = [item for item in findings if item.get("severity") == "high"]
    normal = [item for item in findings if item.get("severity") in {"medium", "low"}]
    return sort_findings(blocking), sort_findings(high), sort_findings(normal)

