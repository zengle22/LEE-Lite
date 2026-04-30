"""Tests for bug_registry.py verification and audit functionality."""
from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from cli.lib.bug_registry import (
    _build_bug_record,
    _save_registry,
    _write_audit_log,
    auto_close_bug,
    check_auto_close_conditions,
    get_bugs_by_coverage_ids,
    get_fixed_bugs,
    load_or_create_registry,
    registry_path,
    set_fix_commit,
    transition_after_verify,
    transition_bug_status,
    transition_bug_status_with_audit,
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_bug_records():
    """Sample bug records for testing."""
    run_id = "RUN-TEST-001"
    return [
        _build_bug_record("case-001", run_id, {"coverage_id": "case-001", "title": "Test 1", "status": "failed"}, "FEAT-001", None),
        _build_bug_record("case-002", run_id, {"coverage_id": "case-002", "title": "Test 2", "status": "failed"}, "FEAT-001", None),
        _build_bug_record("case-003", run_id, {"coverage_id": "case-003", "title": "Test 3", "status": "failed"}, "FEAT-001", None),
    ]


def test_write_audit_log(temp_workspace):
    """Test writing audit log entries."""
    feat_ref = "FEAT-001"
    entries = [
        {
            "timestamp": "2026-04-30T10:00:00Z",
            "bug_id": "BUG-001",
            "from": "detected",
            "to": "open",
            "actor": "system:test",
            "run_id": "RUN-TEST-001",
            "reason": "test",
        }
    ]

    _write_audit_log(temp_workspace, feat_ref, entries)

    audit_path = temp_workspace / "artifacts" / "bugs" / feat_ref / "audit.log"
    assert audit_path.exists()

    content = yaml.safe_load(audit_path.read_text(encoding="utf-8"))
    assert len(content) == 1
    assert content[0]["bug_id"] == "BUG-001"


def test_transition_bug_status_with_audit(temp_workspace, sample_bug_records):
    """Test transition with audit logging."""
    feat_ref = "FEAT-001"
    bug = sample_bug_records[0]

    new_bug = transition_bug_status_with_audit(
        temp_workspace,
        feat_ref,
        bug,
        "open",
        reason="test",
        actor="system:test",
        run_id="RUN-TEST-001",
    )

    assert new_bug["status"] == "open"
    assert new_bug["resolution_reason"] == "test"

    audit_path = temp_workspace / "artifacts" / "bugs" / feat_ref / "audit.log"
    assert audit_path.exists()


def test_timestamp_updates(temp_workspace, sample_bug_records):
    """Test that timestamps are updated on relevant transitions."""
    feat_ref = "FEAT-001"
    bug = sample_bug_records[0]

    # Transition to open (no timestamp update)
    bug_open = transition_bug_status(bug, "open", reason="test")
    assert bug_open["fixed_at"] is None
    assert bug_open["verified_at"] is None
    assert bug_open["closed_at"] is None

    # Transition to fixing first, then to fixed
    bug_fixing = transition_bug_status(bug_open, "fixing")
    bug_fixed = transition_bug_status_with_audit(temp_workspace, feat_ref, bug_fixing, "fixed", reason="fixed")
    assert bug_fixed["fixed_at"] is not None

    # Transition to re_verify_passed
    bug_verified = transition_bug_status_with_audit(temp_workspace, feat_ref, bug_fixed, "re_verify_passed", reason="passed")
    assert bug_verified["verified_at"] is not None

    # Transition to closed
    bug_closed = transition_bug_status_with_audit(temp_workspace, feat_ref, bug_verified, "closed", reason="done")
    assert bug_closed["closed_at"] is not None


def test_get_fixed_bugs(temp_workspace, sample_bug_records):
    """Test getting fixed bugs from registry."""
    feat_ref = "FEAT-001"

    # Setup registry with mixed statuses
    registry = load_or_create_registry(temp_workspace, feat_ref)
    bug1, bug2, bug3 = sample_bug_records
    bug1_open = transition_bug_status(bug1, "open", reason="test")
    bug2_fixing = transition_bug_status(bug2, "open", reason="test")
    bug2_fixing = transition_bug_status(bug2_fixing, "fixing")
    bug2_fixed = transition_bug_status(bug2_fixing, "fixed", reason="fixed")
    bug3_fixed = transition_bug_status(bug3, "open", reason="test")
    bug3_fixed = transition_bug_status(bug3_fixed, "fixing")
    bug3_fixed = transition_bug_status(bug3_fixed, "fixed", reason="fixed")
    registry["bugs"] = [bug1_open, bug2_fixed, bug3_fixed]
    _save_registry(registry_path(temp_workspace, feat_ref), registry)

    fixed = get_fixed_bugs(temp_workspace, feat_ref)
    assert len(fixed) == 2
    assert all(b["status"] == "fixed" for b in fixed)


def test_get_bugs_by_coverage_ids(sample_bug_records):
    """Test mapping coverage_ids to bugs."""
    result = get_bugs_by_coverage_ids(sample_bug_records, ["case-001", "case-003"])
    assert len(result) == 2
    assert "case-001" in result
    assert "case-003" in result
    assert result["case-001"]["case_id"] == "case-001"


def test_transition_after_verify(temp_workspace, sample_bug_records):
    """Test transition after verification."""
    feat_ref = "FEAT-001"

    # Create a fixed bug
    bug = sample_bug_records[0]
    bug = transition_bug_status(bug, "open", reason="test")
    bug = transition_bug_status(bug, "fixing")
    bug_fixed = transition_bug_status_with_audit(temp_workspace, feat_ref, bug, "fixed", reason="fixed")

    # Test passed verification
    bug_passed = transition_after_verify(temp_workspace, feat_ref, bug_fixed, True, "RUN-VERIFY-001")
    assert bug_passed["status"] == "re_verify_passed"

    # Test failed verification on another fixed bug
    bug2 = sample_bug_records[1]
    bug2 = transition_bug_status(bug2, "open", reason="test")
    bug2 = transition_bug_status(bug2, "fixing")
    bug2_fixed = transition_bug_status_with_audit(temp_workspace, feat_ref, bug2, "fixed", reason="fixed")
    bug_failed = transition_after_verify(temp_workspace, feat_ref, bug2_fixed, False, "RUN-VERIFY-002")
    assert bug_failed["status"] == "open"


def test_set_fix_commit(sample_bug_records):
    """Test setting fix_commit field."""
    bug = sample_bug_records[0]
    assert bug["fix_commit"] is None

    bug_with_commit = set_fix_commit(bug, "abc123")
    assert bug_with_commit["fix_commit"] == "abc123"

    # Original unchanged
    assert bug["fix_commit"] is None


def test_check_auto_close_conditions(sample_bug_records):
    """Test auto-close conditions check."""
    bug = sample_bug_records[0]

    # Not re_verify_passed - condition fails
    assert check_auto_close_conditions(bug) is False

    # Make it re_verify_passed
    bug = transition_bug_status(bug, "open", reason="test")
    bug = transition_bug_status(bug, "fixing")
    bug = transition_bug_status(bug, "fixed", reason="fixed")
    bug = transition_bug_status(bug, "re_verify_passed", reason="passed")

    # Condition passes
    assert check_auto_close_conditions(bug) is True


def test_auto_close_bug(temp_workspace, sample_bug_records):
    """Test auto-closing a bug."""
    feat_ref = "FEAT-001"

    # Create a re_verify_passed bug
    bug = sample_bug_records[0]
    bug = transition_bug_status(bug, "open", reason="test")
    bug = transition_bug_status(bug, "fixing")
    bug = transition_bug_status(bug, "fixed", reason="fixed")
    bug_verified = transition_bug_status_with_audit(temp_workspace, feat_ref, bug, "re_verify_passed", reason="passed")

    # Auto-close
    bug_closed = auto_close_bug(temp_workspace, feat_ref, bug_verified, "RUN-AUTO-001")
    assert bug_closed["status"] == "closed"

    # Check audit log
    audit_path = temp_workspace / "artifacts" / "bugs" / feat_ref / "audit.log"
    assert audit_path.exists()
    assert "auto-close" in audit_path.read_text(encoding="utf-8")
