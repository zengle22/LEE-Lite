"""Unit tests for cli.lib.bug_phase_generator."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cli.lib.bug_phase_generator import generate_bug_phase, generate_batch_phase
from cli.lib.errors import CommandError


@pytest.fixture
def tmp_workspace() -> Path:
    """Create a temporary workspace directory."""
    return Path(tempfile.mkdtemp())


def _sample_bug(bug_id_suffix: str = "ABC123") -> dict:
    """Return a minimal bug record for testing."""
    return {
        "bug_id": f"BUG-test-{bug_id_suffix}",
        "case_id": "test.case",
        "title": "Test Bug",
        "status": "open",
        "severity": "medium",
        "gap_type": "code_defect",
        "actual": "bad",
        "expected": "good",
        "diagnostics": ["err"],
        "run_id": "RUN-001",
    }


@pytest.mark.unit
def test_phase_dir_structure(tmp_workspace: Path) -> None:
    """Single bug mode creates directory with all 4 files."""
    bug = _sample_bug()
    phase_dir = generate_bug_phase(tmp_workspace, bug, 25)

    assert phase_dir.exists(), "Phase directory should exist"
    assert phase_dir.name == "025-bug-fix-BUG-test-ABC123"

    for fname in ("CONTEXT.md", "PLAN.md", "DISCUSSION-LOG.md", "SUMMARY.md"):
        assert (phase_dir / fname).exists(), f"{fname} should exist"

    context = (phase_dir / "CONTEXT.md").read_text()
    assert "BUG-test-ABC123" in context

    plan = (phase_dir / "PLAN.md").read_text()
    assert "Root Cause Analysis" in plan
    assert "autonomous: false" in plan


@pytest.mark.unit
def test_plan_md_contains_6_tasks(tmp_workspace: Path) -> None:
    """PLAN.md contains all 6 standard task names."""
    bug = _sample_bug()
    phase_dir = generate_bug_phase(tmp_workspace, bug, 25)
    plan = (phase_dir / "PLAN.md").read_text()

    expected_tasks = [
        "Root Cause Analysis",
        "Implement Fix",
        "Update Bug Status",
        "Verify Fix",
        "Review & Close",
        "Update Failure Case",
    ]
    for task_name in expected_tasks:
        assert task_name in plan, f"PLAN.md should contain '{task_name}'"


@pytest.mark.unit
def test_batch_creates_single_dir(tmp_workspace: Path) -> None:
    """Batch mode creates single directory with both bug IDs in PLAN.md."""
    bugs = [_sample_bug("B1"), _sample_bug("B2")]
    phase_dir = generate_batch_phase(tmp_workspace, bugs, 26)

    assert phase_dir.exists()
    assert "batch" in phase_dir.name

    plan = (phase_dir / "PLAN.md").read_text()
    assert "BUG-test-B1" in plan
    assert "BUG-test-B2" in plan


@pytest.mark.unit
def test_batch_max_3(tmp_workspace: Path) -> None:
    """Batch mode raises CommandError when more than 3 bugs provided."""
    bugs = [_sample_bug(f"D{i}") for i in range(4)]
    with pytest.raises(CommandError) as exc_info:
        generate_batch_phase(tmp_workspace, bugs, 27)
    assert exc_info.value.status_code == "INVALID_REQUEST"


@pytest.mark.unit
def test_batch_single_file_set(tmp_workspace: Path) -> None:
    """Batch phase directory has exactly 4 files."""
    bugs = [_sample_bug("E1"), _sample_bug("E2")]
    phase_dir = generate_batch_phase(tmp_workspace, bugs, 28)

    files = sorted(f.name for f in phase_dir.iterdir() if f.is_file())
    assert files == ["CONTEXT.md", "DISCUSSION-LOG.md", "PLAN.md", "SUMMARY.md"]
