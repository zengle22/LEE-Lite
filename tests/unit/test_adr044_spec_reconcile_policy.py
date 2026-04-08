from __future__ import annotations

from cli.lib.spec_reconcile_policy import compute_blocking_items


def test_policy_blocks_backported_without_patch_refs() -> None:
    findings = [
        {
            "finding_id": "GAP-001",
            "type": "spec_gap",
            "title": "Missing error code semantics",
            "description": "error_code semantics not defined",
            "affects_future_work": True,
            "must_backport": True,
            "status": "open",
        }
    ]
    decisions = [
        {
            "finding_id": "GAP-001",
            "type": "spec_gap",
            "outcome": "backported",
            "decided_by": {"role": "ssot_owner"},
            "ssot_patch_refs": [],
        }
    ]
    blocking = compute_blocking_items(findings=findings, decisions=decisions)
    assert any("requires ssot_patch_refs" in item for item in blocking)


def test_policy_blocks_scope_cut_without_structure() -> None:
    findings = [
        {
            "finding_id": "CUT-001",
            "type": "scope_cut",
            "title": "Temporarily skip batch mode",
            "description": "skip batch mode this round",
            "affects_future_work": True,
            "must_backport": True,
            "status": "open",
        }
    ]
    decisions = [
        {
            "finding_id": "CUT-001",
            "type": "scope_cut",
            "outcome": "deferred",
            "decided_by": {"role": "feat_owner"},
            "owner": "feat_owner",
            "next_checkpoint": "next_freeze",
            "scope_kind": "temporary",
            "affected_refs": [],
        }
    ]
    blocking = compute_blocking_items(findings=findings, decisions=decisions)
    assert any("requires affected_refs" in item for item in blocking)


def test_policy_blocks_critical_local_assumption_deferred() -> None:
    findings = [
        {
            "finding_id": "ASM-001",
            "type": "local_assumption",
            "title": "Treat empty feedback as ok",
            "description": "MVP: empty feedback -> ok",
            "affects_future_work": True,
            "must_backport": False,
            "status": "open",
            "impact_areas": ["core_user_flow"],
        }
    ]
    decisions = [
        {
            "finding_id": "ASM-001",
            "type": "local_assumption",
            "outcome": "deferred",
            "decided_by": {"role": "feat_owner"},
            "owner": "feat_owner",
            "next_checkpoint": "feat_freeze_v2",
        }
    ]
    blocking = compute_blocking_items(findings=findings, decisions=decisions)
    assert any("cannot be deferred" in item for item in blocking)


def test_policy_allows_execution_decision_recorded() -> None:
    findings = [
        {
            "finding_id": "DEC-001",
            "type": "execution_decision",
            "title": "Mock before backend",
            "description": "use mocked data first",
            "affects_future_work": False,
            "must_backport": False,
            "status": "recorded",
        }
    ]
    decisions = [
        {
            "finding_id": "DEC-001",
            "type": "execution_decision",
            "outcome": "recorded",
            "decided_by": {"role": "executor"},
        }
    ]
    blocking = compute_blocking_items(findings=findings, decisions=decisions)
    assert blocking == []


def test_policy_blocks_executor_deciding_spec_gap() -> None:
    findings = [
        {
            "finding_id": "GAP-002",
            "type": "spec_gap",
            "title": "Missing status branch",
            "description": "status branch missing",
            "affects_future_work": True,
            "must_backport": True,
            "status": "open",
        }
    ]
    decisions = [
        {
            "finding_id": "GAP-002",
            "type": "spec_gap",
            "outcome": "deferred",
            "decided_by": {"role": "executor"},
            "owner": "feat_owner",
            "next_checkpoint": "feat_freeze_v2",
        }
    ]
    blocking = compute_blocking_items(findings=findings, decisions=decisions)
    assert any("not authorized" in item for item in blocking)


def test_policy_blocks_formal_scope_cut_without_product_or_ssot_owner() -> None:
    findings = [
        {
            "finding_id": "CUT-002",
            "type": "scope_cut",
            "title": "Drop offline mode",
            "description": "drop offline mode",
            "affects_future_work": True,
            "must_backport": True,
            "status": "open",
            "scope_kind": "formal",
            "affected_refs": ["ACCEPT-001"],
        }
    ]
    decisions = [
        {
            "finding_id": "CUT-002",
            "type": "scope_cut",
            "outcome": "deferred",
            "decided_by": {"role": "feat_owner"},
            "owner": "feat_owner",
            "next_checkpoint": "next_release",
            "scope_kind": "formal",
            "affected_refs": ["ACCEPT-001"],
        }
    ]
    blocking = compute_blocking_items(findings=findings, decisions=decisions)
    assert any("not authorized" in item for item in blocking)


def test_policy_infers_must_backport_from_impact_areas() -> None:
    findings = [
        {
            "finding_id": "ASM-002",
            "type": "local_assumption",
            "title": "Assume default error mapping",
            "description": "treat missing error_code as default",
            "affects_future_work": True,
            "must_backport": False,
            "status": "open",
            "impact_areas": ["api_semantics"],
        }
    ]
    decisions = [
        {
            "finding_id": "ASM-002",
            "type": "local_assumption",
            "outcome": "pending",
            "decided_by": {"role": "feat_owner"},
        }
    ]
    blocking = compute_blocking_items(findings=findings, decisions=decisions)
    assert any("must_backport" in item for item in blocking)

