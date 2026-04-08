"""Policy helpers for ADR-044 spec reconcile enforcement."""

from __future__ import annotations

from typing import Any

CRITICAL_ASSUMPTION_IMPACT_AREAS = {
    "core_user_flow",
    "state_machine",
    "api_contract",
    "acceptance_testset",
}

DEFAULT_MUST_BACKPORT_IMPACT_AREAS = {
    "state_machine",
    "api_contract",
    "api_semantics",
    "ui_failure_path",
    "acceptance_testset",
    "cross_module_boundary",
    "owner_binding",
}

OWNER_DECISION_ROLES = {"feat_owner", "ssot_owner"}
SCOPE_FORMAL_DECISION_ROLES = {"product_owner", "ssot_owner"}


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def infer_must_backport(finding: dict[str, Any]) -> bool:
    """Infer must_backport with ADR-044 defaults."""

    if str(finding.get("type") or "").strip() == "execution_decision":
        return False
    if bool(finding.get("must_backport")):
        return True
    impact_areas = set(_as_str_list(finding.get("impact_areas")))
    return bool(impact_areas & DEFAULT_MUST_BACKPORT_IMPACT_AREAS)


def _role_allowed_for_decision(*, role: str, finding_type: str, outcome: str, decision: dict[str, Any]) -> bool:
    if finding_type == "execution_decision":
        return role == "executor" and outcome == "recorded"
    if finding_type in {"spec_gap", "local_assumption"}:
        return role in OWNER_DECISION_ROLES
    if finding_type == "scope_cut":
        scope_kind = str(decision.get("scope_kind") or "").strip()
        if scope_kind == "formal":
            return role in SCOPE_FORMAL_DECISION_ROLES
        if scope_kind == "temporary":
            return role in OWNER_DECISION_ROLES
        return False
    return False


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
        role = str(decided_by.get("role") or "").strip() if isinstance(decided_by, dict) else ""
        if not role:
            blocking.append(f"{finding_id}: decided_by.role is required")
        elif not _role_allowed_for_decision(role=role, finding_type=finding_type, outcome=outcome, decision=decision):
            blocking.append(f"{finding_id}: decided_by.role={role} is not authorized for {finding_type}/{outcome}")

        if outcome == "recorded" and finding_type != "execution_decision":
            blocking.append(f"{finding_id}: recorded is only allowed for execution_decision")

        if outcome == "backported":
            patch_refs = _as_str_list(decision.get("ssot_patch_refs"))
            if not patch_refs:
                blocking.append(f"{finding_id}: backported requires ssot_patch_refs evidence")

        must_backport = infer_must_backport(finding)
        if must_backport and finding_type != "execution_decision" and outcome not in {"backported", "deferred", "rejected"}:
            blocking.append(f"{finding_id}: must_backport findings must be backported or deferred before dispatch")

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
