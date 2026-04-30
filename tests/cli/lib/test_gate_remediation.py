"""Tests for gate_remediation.py module."""
from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from cli.lib.bug_registry import (
    _build_bug_record,
    _save_registry,
    load_or_create_registry,
    registry_path,
)
from cli.lib.bug_registry import _write_audit_log
from cli.lib.gate_remediation import (
    _get_coverage_ids_from_gap_list,
    archive_detected_not_in_gap_list,
    promote_detected_to_open,
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_gap_list():
    """Sample gap_list from settlement."""
    return [
        {"coverage_id": "case-001", "case_id": "case-001", "title": "Test failed 1"},
        {"coverage_id": "case-002", "case_id": "case-002", "title": "Test failed 2"},
    ]


@pytest.fixture
def sample_bug_records():
    """Sample bug records for testing."""
    run_id = "RUN-TEST-001"
    return [
        _build_bug_record("case-001", run_id, {"coverage_id": "case-001", "title": "Test 1", "status": "failed"}, "FEAT-001", None),
        _build_bug_record("case-002", run_id, {"coverage_id": "case-002", "title": "Test 2", "status": "failed"}, "FEAT-001", None),
        _build_bug_record("case-003", run_id, {"coverage_id": "case-003", "title": "Test 3", "status": "failed"}, "FEAT-001", None),
    ]


def test_get_coverage_ids_from_gap_list(sample_gap_list):
    """Test extraction of coverage_ids from gap_list."""
    result = _get_coverage_ids_from_gap_list(sample_gap_list)
    assert result == {"case-001", "case-002"}


def test_get_coverage_ids_from_gap_list_empty():
    """Test with empty gap_list."""
    result = _get_coverage_ids_from_gap_list([])
    assert result == set()


def test_promote_detected_to_open(temp_workspace, sample_gap_list, sample_bug_records):
    """Test promoting detected bugs to open."""
    feat_ref = "FEAT-001"
    run_id = "RUN-TEST-002"

    # Setup registry with detected bugs
    registry = load_or_create_registry(temp_workspace, feat_ref)
    registry["bugs"] = sample_bug_records
    path = registry_path(temp_workspace, feat_ref)
    _save_registry(path, registry)

    # Test promotion
    result = promote_detected_to_open(temp_workspace, feat_ref, sample_gap_list, run_id)

    # Check result
    assert result["promoted_count"] == 2
    assert result["already_open_count"] == 0

    # Verify registry was updated
    updated_registry = load_or_create_registry(temp_workspace, feat_ref)
    assert len(updated_registry["bugs"]) == 3

    # Check statuses
    bug1 = next(b for b in updated_registry["bugs"] if b["case_id"] == "case-001")
    bug2 = next(b for b in updated_registry["bugs"] if b["case_id"] == "case-002")
    bug3 = next(b for b in updated_registry["bugs"] if b["case_id"] == "case-003")

    assert bug1["status"] == "open"
    assert bug2["status"] == "open"
    assert bug3["status"] == "detected"  # Not in gap_list

    # Check trace was added
    assert len(bug1["trace"]) >= 2
    assert bug1["trace"][-1]["event"] == "status_changed"
    assert bug1["trace"][-1]["from"] == "detected"
    assert bug1["trace"][-1]["to"] == "open"


def test_promote_detected_to_open_idempotent(temp_workspace, sample_gap_list, sample_bug_records):
    """Test idempotency - calling again doesn't change already-open bugs."""
    feat_ref = "FEAT-001"
    run_id = "RUN-TEST-003"

    # Setup registry
    registry = load_or_create_registry(temp_workspace, feat_ref)
    registry["bugs"] = sample_bug_records
    path = registry_path(temp_workspace, feat_ref)
    _save_registry(path, registry)

    # First call
    result1 = promote_detected_to_open(temp_workspace, feat_ref, sample_gap_list, run_id)
    assert result1["promoted_count"] == 2
    assert result1["already_open_count"] == 0

    # Second call
    result2 = promote_detected_to_open(temp_workspace, feat_ref, sample_gap_list, run_id)
    assert result2["promoted_count"] == 0  # No new promotions
    assert result2["already_open_count"] == 2  # These are now open


def test_archive_detected_not_in_gap_list(temp_workspace, sample_gap_list, sample_bug_records):
    """Test archiving detected bugs not in gap_list."""
    feat_ref = "FEAT-001"
    run_id = "RUN-TEST-004"

    # Setup registry
    registry = load_or_create_registry(temp_workspace, feat_ref)
    registry["bugs"] = sample_bug_records
    path = registry_path(temp_workspace, feat_ref)
    _save_registry(path, registry)

    # Test archiving
    result = archive_detected_not_in_gap_list(temp_workspace, feat_ref, sample_gap_list, run_id)

    assert result["archived_count"] == 1  # case-003 is not in gap_list
    assert result["preserved_count"] == 2

    # Verify
    updated_registry = load_or_create_registry(temp_workspace, feat_ref)
    bug3 = next(b for b in updated_registry["bugs"] if b["case_id"] == "case-003")
    assert bug3["status"] == "archived"


def test_audit_log_written(temp_workspace, sample_gap_list, sample_bug_records):
    """Test that audit log is written during promotion."""
    feat_ref = "FEAT-001"
    run_id = "RUN-TEST-005"

    # Setup registry
    registry = load_or_create_registry(temp_workspace, feat_ref)
    registry["bugs"] = sample_bug_records
    path = registry_path(temp_workspace, feat_ref)
    _save_registry(path, registry)

    # Trigger promotion
    promote_detected_to_open(temp_workspace, feat_ref, sample_gap_list, run_id)

    # Check audit log exists
    audit_path = temp_workspace / "artifacts" / "bugs" / feat_ref / "audit.log"
    assert audit_path.exists()

    # Read and verify
    content = audit_path.read_text(encoding="utf-8")
    assert "case-001" in content
    assert "case-002" in content
    assert "open" in content
    assert "detected" in content


def test_version_increments(temp_workspace, sample_gap_list, sample_bug_records):
    """Test that optimistic lock version increments on each change."""
    feat_ref = "FEAT-001"
    run_id = "RUN-TEST-006"

    # Setup registry
    registry = load_or_create_registry(temp_workspace, feat_ref)
    registry["bugs"] = sample_bug_records
    path = registry_path(temp_workspace, feat_ref)
    _save_registry(path, registry)

    # Get initial version
    initial_registry = load_or_create_registry(temp_workspace, feat_ref)
    initial_version = initial_registry["version"]

    # Trigger promotion
    promote_detected_to_open(temp_workspace, feat_ref, sample_gap_list, run_id)

    # Check version changed
    updated_registry = load_or_create_registry(temp_workspace, feat_ref)
    assert updated_registry["version"] != initial_version
