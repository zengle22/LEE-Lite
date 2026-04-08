"""Policy helpers for ADR-044 spec reconcile enforcement."""

from __future__ import annotations

from typing import Any

CRITICAL_ASSUMPTION_IMPACT_AREAS = {
    "core_user_flow",
    "state_machine",
    "api_contract",
    "acceptance_testset",
}


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def compute_blocking_items(
    *,
    findings: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> list[str]:
    """Compute blocking_items for spec-reconcile-report.json (ADR-044 Phase 0/1)."""

    blocking: list[str] = []
    active_findings = [
        item
        for item in findings
        if isinstance(item, dict) and str(item.get("status") or "open").strip() not in {"closed", "superseded"}
    ]
    finding_by_id = {str(item.get("finding_id") or "").strip(): item for item in active_findings}
    decision_by_id = {str(item.get("finding_id") or "").strip(): item for item in decisions}

    missing_decisions = [finding_id for finding_id in finding_by_id if finding_id and finding_id not in decision_by_id]
    if missing_decisions:
        blocking.append(f"missing decisions for findings: {', '.join(sorted(missing_decisions))}")

    for finding_id, decision in decision_by_id.items():
        if not finding_id or finding_id not in finding_by_id:
            continue
        finding = finding_by_id[finding_id]
        finding_type = str(finding.get("type") or "").strip()
        outcome = str(decision.get("outcome") or "").strip()
        decided_by = decision.get("decided_by")
        if not isinstance(decided_by, dict) or not str(decided_by.get("role") or "").strip():
            blocking.append(f"{finding_id}: decided_by.role is required")

        if outcome == "recorded" and finding_type != "execution_decision":
            blocking.append(f"{finding_id}: recorded is only allowed for execution_decision")

        if outcome == "backported":
            patch_refs = _as_str_list(decision.get("ssot_patch_refs"))
            if not patch_refs:
                blocking.append(f"{finding_id}: backported requires ssot_patch_refs evidence")

        if finding_type != "execution_decision" and outcome == "deferred":
            owner = str(decision.get("owner") or "").strip()
            checkpoint = str(decision.get("next_checkpoint") or "").strip()
            if not owner or not checkpoint:
                blocking.append(f"{finding_id}: deferred requires owner + next_checkpoint")

        if finding_type != "execution_decision" and outcome == "rejected":
            rationale = str(decision.get("rationale") or "").strip()
            if not rationale:
                blocking.append(f"{finding_id}: rejected requires rationale")

        if finding_type == "scope_cut":
            scope_kind = str(decision.get("scope_kind") or "").strip()
            if scope_kind not in {"formal", "temporary"}:
                blocking.append(f"{finding_id}: scope_cut requires scope_kind=formal|temporary")
            affected_refs = _as_str_list(decision.get("affected_refs"))
            if not affected_refs:
                blocking.append(f"{finding_id}: scope_cut requires affected_refs")

        if finding_type == "local_assumption" and outcome == "deferred":
            impact_areas = set(_as_str_list(finding.get("impact_areas")))
            if impact_areas & CRITICAL_ASSUMPTION_IMPACT_AREAS:
                blocking.append(f"{finding_id}: local_assumption impacting critical areas cannot be deferred before dispatch")

    return blocking
