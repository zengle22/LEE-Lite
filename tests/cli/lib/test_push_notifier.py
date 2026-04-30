"""Tests for push_notifier.py module."""
from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

from cli.lib.push_notifier import (
    create_draft_phase_preview,
    get_next_phase_number,
    schedule_reminder,
    show_terminal_notification,
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_bugs():
    """Sample bug records for testing."""
    return [
        {
            "bug_id": "BUG-case-001-abc123",
            "case_id": "case-001",
            "coverage_id": "case-001",
            "title": "Test failed 1",
            "status": "open",
            "severity": "high",
            "gap_type": "code_defect",
            "manifest_ref": "ssot/tests/api/FEAT-001/api-coverage-manifest.yaml",
        },
        {
            "bug_id": "BUG-case-002-def456",
            "case_id": "case-002",
            "coverage_id": "case-002",
            "title": "Test failed 2",
            "status": "open",
            "severity": "medium",
            "gap_type": "code_defect",
            "manifest_ref": "",
        },
    ]


def test_show_terminal_notification_runs(capsys):
    """Test that show_terminal_notification runs without errors."""
    # Just verify it doesn't crash
    show_terminal_notification("FEAT-001", 2, "RUN-TEST-001")
    captured = capsys.readouterr()
    # Should output to stderr
    assert "GATE EVALUATION: FAIL" in captured.err


def test_create_draft_phase_preview(temp_workspace, sample_bugs):
    """Test creating draft phase preview."""
    feat_ref = "FEAT-001"
    run_id = "RUN-TEST-002"

    preview_path = create_draft_phase_preview(temp_workspace, feat_ref, sample_bugs, run_id)

    # Verify file exists
    assert preview_path.exists()
    assert preview_path.parent.name == "drafts"
    assert preview_path.parent.parent.name == ".planning"

    # Verify content
    content = preview_path.read_text(encoding="utf-8")
    assert feat_ref in content
    assert run_id in content
    assert "BUG-case-001-abc123" in content
    assert "BUG-case-002-def456" in content
    assert "Test failed 1" in content
    assert "Test failed 2" in content


def test_schedule_reminder(temp_workspace, sample_bugs):
    """Test scheduling a reminder."""
    feat_ref = "FEAT-001"
    trigger_at = datetime.utcnow() + timedelta(hours=4)

    schedule_reminder(temp_workspace, feat_ref, sample_bugs, trigger_at)

    # Verify file exists
    reminders_path = temp_workspace / "artifacts" / "bugs" / feat_ref / "reminders.yaml"
    assert reminders_path.exists()

    # Verify content
    with reminders_path.open("r", encoding="utf-8") as f:
        reminders = yaml.safe_load(f)

    assert len(reminders) == 1
    assert reminders[0]["bug_count"] == 2
    assert reminders[0]["reminder_type"] == "t4h"
    assert reminders[0]["acknowledged"] is False
    assert "BUG-case-001-abc123" in reminders[0]["bug_ids"]
    assert "BUG-case-002-def456" in reminders[0]["bug_ids"]


def test_get_next_phase_number_empty(temp_workspace):
    """Test get_next_phase_number with no existing phases."""
    # No .planning/phases directory
    assert get_next_phase_number(temp_workspace) == 1


def test_get_next_phase_number_with_phases(temp_workspace):
    """Test get_next_phase_number with existing phases."""
    # Create some phase directories
    phases_dir = temp_workspace / ".planning" / "phases"
    phases_dir.mkdir(parents=True)
    (phases_dir / "001-initial-setup").mkdir()
    (phases_dir / "015-bug-fix").mkdir()
    (phases_dir / "025-bug-registry").mkdir()

    assert get_next_phase_number(temp_workspace) == 26
