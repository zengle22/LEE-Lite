"""Unit tests for settle_runtime.py — Minor patch backwrite-as-records logic."""

import sys
import os
import tempfile
import textwrap
from pathlib import Path
from datetime import datetime, timezone
from unittest import mock

import pytest

# Add project root to path so we can import cli.lib
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # skills/ll-experience-patch-settle -> project root
sys.path.insert(0, str(PROJECT_ROOT))

# Add the scripts directory to path for direct import of settle_runtime
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))


def _make_patch(
    change_class="interaction",
    grade_level="minor",
    status="approved",
    feat_ref="FEAT-001",
    extra=None,
):
    """Create a minimal Patch YAML dict for testing."""
    patch = {
        "id": "UXPATCH-0001",
        "type": "experience_patch",
        "status": status,
        "change_class": change_class,
        "grade_level": grade_level,
        "scope": {"feat_ref": feat_ref},
        "changed_files": ["src/components/Button.tsx"],
        "test_impact": {
            "impacts_user_path": True,
            "impacts_acceptance": False,
            "affected_routes": ["/user-flow"],
            "test_changes_required": ["test_button.py"],
        },
        "source": {
            "actor": "human",
            "ai_suggested_class": change_class,
            "human_confirmed_class": change_class,
        },
        "created_at": "2026-04-19T09:00:00Z",
    }
    if extra:
        patch.update(extra)
    return patch


def _write_patch(tmp_path, patch_dict):
    """Write a patch dict to a temporary YAML file."""
    import yaml
    patch_path = tmp_path / "ssot" / "experience-patches" / "FEAT-001"
    patch_path.mkdir(parents=True, exist_ok=True)
    yaml_path = patch_path / "UXPATCH-0001.yaml"
    with open(yaml_path, "w") as f:
        yaml.safe_dump({"experience_patch": patch_dict}, f, default_flow_style=False)
    return yaml_path


@pytest.fixture
def workspace(tmp_path):
    """Create a temporary workspace with proper directory structure."""
    ssot_dir = tmp_path / "ssot" / "experience-patches"
    ssot_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


# ---------------------------------------------------------------------------
# Import settle_runtime under test (direct import from scripts dir)
# ---------------------------------------------------------------------------

def _import_settle_runtime():
    """Import settle_runtime module directly from the scripts directory."""
    import importlib
    import settle_runtime as mod
    importlib.reload(mod)
    return mod


# ---------------------------------------------------------------------------
# Test 1: interaction change_class creates 3 backwrite records
# ---------------------------------------------------------------------------

def test_interaction_creates_three_backwrite_records(workspace):
    """settle_minor_patch with change_class=interaction creates ui_spec, flow_spec, testset records."""
    settle = _import_settle_runtime()
    patch = _make_patch(change_class="interaction")
    result = settle.settle_minor_patch(patch, workspace)

    assert result["status"] == "applied"
    backwrite_dir = workspace / "ssot" / "experience-patches" / "FEAT-001" / "backwrites"
    assert backwrite_dir.exists(), "backwrites/ directory should be created"

    # interaction -> ui_spec, flow_spec, testset
    files = list(backwrite_dir.glob("*.yaml"))
    assert len(files) == 3, f"Expected 3 backwrite files, got {len(files)}"

    filenames = {f.name for f in files}
    assert "ui_spec_updates.yaml" in filenames
    assert "flow_spec_updates.yaml" in filenames
    assert "testset_updates.yaml" in filenames


# ---------------------------------------------------------------------------
# Test 2: visual change_class creates 1 backwrite record
# ---------------------------------------------------------------------------

def test_visual_creates_one_backwrite_record(workspace):
    """settle_minor_patch with change_class=visual creates ui_spec_optional record."""
    settle = _import_settle_runtime()
    patch = _make_patch(change_class="visual")
    result = settle.settle_minor_patch(patch, workspace)

    assert result["status"] == "applied"
    backwrite_dir = workspace / "ssot" / "experience-patches" / "FEAT-001" / "backwrites"
    files = list(backwrite_dir.glob("*.yaml"))
    assert len(files) == 1, f"Expected 1 backwrite file, got {len(files)}"
    assert files[0].name == "ui_spec_optional_updates.yaml"


# ---------------------------------------------------------------------------
# Test 3: copy_text change_class creates 0 backwrite records
# ---------------------------------------------------------------------------

def test_copy_text_creates_zero_backwrite_records(workspace):
    """settle_minor_patch with change_class=copy_text creates no backwrite records."""
    settle = _import_settle_runtime()
    patch = _make_patch(change_class="copy_text")
    result = settle.settle_minor_patch(patch, workspace)

    assert result["status"] == "applied"
    assert result["backwrite_targets"] == []
    assert result["files_written"] == []


# ---------------------------------------------------------------------------
# Test 4: Major grade_level is rejected
# ---------------------------------------------------------------------------

def test_major_patch_rejected(workspace):
    """settle_minor_patch with grade_level=major raises error referencing ll-frz-manage."""
    settle = _import_settle_runtime()
    patch = _make_patch(grade_level="major")

    with pytest.raises(settle.CommandError) as exc_info:
        settle.settle_minor_patch(patch, workspace)

    assert "ll-frz-manage" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test 5: Patch status updated from approved to applied
# ---------------------------------------------------------------------------

def test_status_updated_to_applied(workspace):
    """settle_minor_patch updates patch status to 'applied' and sets settled_at."""
    settle = _import_settle_runtime()
    patch = _make_patch()
    result = settle.settle_minor_patch(patch, workspace)

    assert patch["status"] == "applied"
    assert "settled_at" in patch
    assert result["status"] == "applied"


# ---------------------------------------------------------------------------
# Test 6: Idempotency — running twice returns already_applied
# ---------------------------------------------------------------------------

def test_idempotent_second_run_returns_already_applied(workspace):
    """Running settle on an already-applied patch returns early without error."""
    settle = _import_settle_runtime()
    patch = _make_patch()

    # First run
    result1 = settle.settle_minor_patch(patch, workspace)
    assert result1["status"] == "applied"

    # Second run — should be idempotent
    result2 = settle.settle_minor_patch(patch, workspace)
    assert result2["status"] == "already_applied"
    assert "already settled" in result2.get("message", "").lower()


# ---------------------------------------------------------------------------
# Test 7: CLI process subcommand
# ---------------------------------------------------------------------------

def test_cli_process_subcommand(workspace):
    """CLI `python settle_runtime.py process --patch <yaml> --workspace-root <root>` works."""
    import yaml
    settle = _import_settle_runtime()

    # Write patch YAML
    patch_path = _write_patch(workspace, _make_patch())

    # Run CLI
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        settle.main([
            "process",
            "--patch", str(patch_path),
            "--workspace-root", str(workspace),
        ])
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    # Verify patch was updated
    with open(patch_path) as f:
        data = yaml.safe_load(f)
    assert data["experience_patch"]["status"] == "applied"


# ---------------------------------------------------------------------------
# Test 8: --apply flag shows stub warning
# ---------------------------------------------------------------------------

def test_apply_flag_shows_stub_warning(workspace):
    """CLI `settle --patch <yaml> --apply` shows warning that --apply is not implemented."""
    import yaml
    settle = _import_settle_runtime()

    patch_path = _write_patch(workspace, _make_patch())

    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        settle.main([
            "settle",
            "--patch", str(patch_path),
            "--workspace-root", str(workspace),
            "--apply",
        ])
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert "WARNING" in output or "warning" in output.lower()
    assert "--apply" in output or "not yet implemented" in output.lower()
