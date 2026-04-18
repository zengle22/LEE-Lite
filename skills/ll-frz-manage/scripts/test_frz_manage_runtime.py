"""Integration tests for frz_manage_runtime.py CLI commands.

Tests use temporary directories for workspace isolation. Each test creates
a temp workspace with ssot/registry/ directory and optional FRZ YAML files.
"""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the script directory and workspace root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent.parent

if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import yaml

from cli.lib.frz_registry import _load_registry, registry_path
from cli.lib.errors import CommandError
from frz_manage_runtime import (
    _find_workspace_root,
    build_parser,
    extract_frz,
    freeze_frz,
    list_frz,
    main,
    run_cascade,
    validate_frz,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _make_valid_frz_yaml() -> dict:
    """Return a valid FRZ package dict with all 5 MSC dimensions."""
    return {
        "artifact_type": "frz_package",
        "frz_id": "FRZ-001",
        "version": "1.0",
        "status": "draft",
        "product_boundary": {
            "in_scope": ["User authentication", "Password reset"],
            "out_of_scope": ["OAuth integration"],
        },
        "core_journeys": [
            {
                "id": "JRN-001",
                "name": "Login flow",
                "steps": ["Enter credentials", "Submit form", "Verify token"],
            }
        ],
        "domain_model": [
            {
                "id": "ENT-001",
                "name": "User",
                "contract": {"email": "string", "password_hash": "string"},
            }
        ],
        "state_machine": [
            {
                "id": "SM-001",
                "name": "Account status",
                "states": ["pending", "active", "suspended"],
                "transitions": [
                    {"from": "pending", "to": "active", "event": "verify_email"}
                ],
            }
        ],
        "acceptance_contract": {
            "expected_outcomes": [
                "User can log in with valid credentials",
                "User sees error on invalid credentials",
            ],
            "acceptance_impact": ["Login UX", "Security audit trail"],
        },
    }


def _make_incomplete_frz_yaml() -> dict:
    """Return an FRZ package dict missing core_journeys dimension."""
    return {
        "artifact_type": "frz_package",
        "frz_id": "FRZ-002",
        "version": "1.0",
        "status": "draft",
        "product_boundary": {
            "in_scope": ["Feature A"],
            "out_of_scope": ["Feature B"],
        },
        "core_journeys": [],  # Empty — missing dimension
        "domain_model": [
            {
                "id": "ENT-002",
                "name": "Item",
                "contract": {"name": "string"},
            }
        ],
        "state_machine": [
            {
                "id": "SM-002",
                "name": "Item state",
                "states": ["new", "active"],
                "transitions": [],
            }
        ],
        "acceptance_contract": {
            "expected_outcomes": ["Item can be created"],
            "acceptance_impact": ["Item management"],
        },
    }


def _setup_workspace(tmp_path: Path, registry_content: str | None = None) -> Path:
    """Create a temp workspace with ssot/registry directory.

    Args:
        tmp_path: pytest tmp_path fixture.
        registry_content: Optional initial registry YAML content.

    Returns:
        Path to the workspace root.
    """
    workspace = tmp_path / "workspace"
    (workspace / ".planning").mkdir(parents=True)
    reg_dir = workspace / "ssot" / "registry"
    reg_dir.mkdir(parents=True)
    if registry_content is not None:
        (reg_dir / "frz-registry.yaml").write_text(
            registry_content, encoding="utf-8"
        )
    return workspace


def _write_frz_yaml(dir_path: Path, data: dict, filename: str = "frz-package.yaml") -> Path:
    """Write a FRZ package dict to a YAML file.

    Args:
        dir_path: Directory to write into.
        data: FRZ package dict.
        filename: Name of the YAML file.

    Returns:
        Path to the written file.
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    import yaml

    yaml_path = dir_path / filename
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return yaml_path


# ---------------------------------------------------------------------------
# Test 1: Validate a valid FRZ package
# ---------------------------------------------------------------------------


def test_validate_valid_frz_package(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Valid FRZ package with all 5 MSC dimensions should pass validation."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())

    args = argparse.Namespace(input=str(input_dir))
    result = validate_frz(args)

    assert result == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "msc_valid" in captured.out.lower() or "all 5 MSC dimensions satisfied" in captured.out


# ---------------------------------------------------------------------------
# Test 2: Validate missing dimension
# ---------------------------------------------------------------------------


def test_validate_missing_dimension(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """FRZ package with missing core_journeys should fail validation."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_incomplete_frz_yaml())

    args = argparse.Namespace(input=str(input_dir))
    result = validate_frz(args)

    assert result == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out
    assert "missing" in captured.out.lower()


# ---------------------------------------------------------------------------
# Test 3: Validate with nonexistent input directory
# ---------------------------------------------------------------------------


def test_validate_file_not_found(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Nonexistent input directory should return non-zero exit code."""
    nonexistent = tmp_path / "nonexistent"
    args = argparse.Namespace(input=str(nonexistent))
    result = validate_frz(args)

    assert result != 0
    captured = capsys.readouterr()
    assert "not a directory" in captured.err.lower() or "not found" in captured.err.lower()


# ---------------------------------------------------------------------------
# Test 4: Freeze a valid FRZ package
# ---------------------------------------------------------------------------


def test_freeze_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Valid FRZ package should be frozen successfully."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())

    # Override cwd to workspace for workspace root discovery
    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(input=str(input_dir), id="FRZ-001")
        result = freeze_frz(args)

    assert result == 0
    captured = capsys.readouterr()
    assert "FRZ-001 registered" in captured.out
    assert "frozen" in captured.out

    # Verify registry file contains the FRZ
    reg_path = registry_path(workspace)
    assert reg_path.exists()
    records = _load_registry(reg_path)
    assert any(r["frz_id"] == "FRZ-001" for r in records)


# ---------------------------------------------------------------------------
# Test 5: Freeze rejects invalid MSC
# ---------------------------------------------------------------------------


def test_freeze_rejects_invalid_msc(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """FRZ package that fails MSC validation should not be frozen."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_incomplete_frz_yaml())

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(input=str(input_dir), id="FRZ-002")
        result = freeze_frz(args)

    assert result == 1
    captured = capsys.readouterr()
    assert "Cannot freeze" in captured.err or "MSC validation failed" in captured.err


# ---------------------------------------------------------------------------
# Test 6: Freeze rejects duplicate ID
# ---------------------------------------------------------------------------


def test_freeze_rejects_duplicate_id(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Attempting to freeze the same FRZ ID twice should fail."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        # First freeze
        args1 = argparse.Namespace(input=str(input_dir), id="FRZ-001")
        result1 = freeze_frz(args1)
        assert result1 == 0

        # Second freeze with same ID should fail
        input_dir2 = workspace / "input2"
        _write_frz_yaml(input_dir2, _make_valid_frz_yaml())
        args2 = argparse.Namespace(input=str(input_dir2), id="FRZ-001")

        with pytest.raises(CommandError, match="already registered"):
            freeze_frz(args2)


# ---------------------------------------------------------------------------
# Test 7: Freeze invalid FRZ ID
# ---------------------------------------------------------------------------


def test_freeze_invalid_frz_id(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Invalid FRZ ID format should be rejected."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(input=str(input_dir), id="INVALID-ID")
        result = freeze_frz(args)

    assert result != 0


# ---------------------------------------------------------------------------
# Test 8: List empty registry
# ---------------------------------------------------------------------------


def test_list_empty_registry(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Empty registry should display 'No FRZ packages registered'."""
    workspace = _setup_workspace(tmp_path, registry_content="frz_registry: []\n")

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace()
        result = list_frz(args)

    assert result == 0
    captured = capsys.readouterr()
    assert "No FRZ packages registered" in captured.out


# ---------------------------------------------------------------------------
# Test 9: List with registered FRZ
# ---------------------------------------------------------------------------


def test_list_with_registered_frz(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """List should show registered FRZ packages."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        # Freeze first
        freeze_args = argparse.Namespace(input=str(input_dir), id="FRZ-001")
        freeze_frz(freeze_args)

        # Then list
        list_args = argparse.Namespace()
        list_frz(list_args)

    captured = capsys.readouterr()
    assert "FRZ-001" in captured.out
    assert "frozen" in captured.out


# ---------------------------------------------------------------------------
# Test 10: List filter by status
# ---------------------------------------------------------------------------


def test_list_filter_by_status(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """List with status filter should only show matching entries."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        # Freeze FRZ-001 (status=frozen)
        freeze_args = argparse.Namespace(input=str(input_dir), id="FRZ-001")
        freeze_frz(freeze_args)

        # Reset captured output before list call
        capsys.readouterr()

        # List with status=blocked (should not show FRZ-001)
        list_args = argparse.Namespace(status="blocked")
        list_frz(list_args)

    captured = capsys.readouterr()
    assert "FRZ-001" not in captured.out


# ---------------------------------------------------------------------------
# Test 11: Build parser has all subcommands
# ---------------------------------------------------------------------------


def test_build_parser_has_all_subcommands() -> None:
    """Parser should define validate, freeze, and list subcommands."""
    parser = build_parser()

    # validate
    args = parser.parse_args(["validate", "--input", "/tmp"])
    assert args.command == "validate"

    # freeze
    args = parser.parse_args(["freeze", "--input", "/tmp", "--id", "FRZ-001"])
    assert args.command == "freeze"
    assert args.id == "FRZ-001"

    # list
    args = parser.parse_args(["list"])
    assert args.command == "list"


# ---------------------------------------------------------------------------
# Test 12: Main dispatch validate
# ---------------------------------------------------------------------------


def test_main_dispatch_validate() -> None:
    """main() with nonexistent input directory should return non-zero."""
    result = main(["validate", "--input", "/nonexistent"])
    assert result != 0


# ---------------------------------------------------------------------------
# Test 13: Freeze with revision type
# ---------------------------------------------------------------------------


def test_freeze_with_revision_type(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Freeze with --type revise should record revision metadata."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        # First freeze
        args1 = argparse.Namespace(input=str(input_dir), id="FRZ-001")
        result1 = freeze_frz(args1)
        assert result1 == 0

        # Create revised FRZ
        input_dir2 = workspace / "input_revise"
        revised = _make_valid_frz_yaml()
        revised["frz_id"] = "FRZ-002"
        _write_frz_yaml(input_dir2, revised)

        # Freeze with revision
        args2 = argparse.Namespace(
            input=str(input_dir2),
            id="FRZ-002",
            type="revise",
            reason="scope change",
            previous_frz="FRZ-001",
        )
        result2 = freeze_frz(args2)
        assert result2 == 0

    # Verify registry contains revision metadata
    reg_path = registry_path(workspace)
    records = _load_registry(reg_path)
    frz002 = next(r for r in records if r["frz_id"] == "FRZ-002")
    assert frz002["revision_type"] == "revise"
    assert frz002.get("previous_frz_ref") == "FRZ-001"


# ---------------------------------------------------------------------------
# Test 14: Validate input is file not dir
# ---------------------------------------------------------------------------


def test_validate_input_is_file_not_dir(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Validate with a file path instead of directory should return non-zero."""
    workspace = _setup_workspace(tmp_path)
    input_file = workspace / "frz-package.yaml"
    _write_frz_yaml(workspace / "tmp", _make_valid_frz_yaml())
    # Move the file to be at workspace root (it's a file, not a dir)
    src = workspace / "tmp" / "frz-package.yaml"
    src.rename(input_file)

    args = argparse.Namespace(input=str(input_file))
    result = validate_frz(args)

    assert result != 0
    captured = capsys.readouterr()
    assert "not a directory" in captured.err.lower()


# ---------------------------------------------------------------------------
# Test 15: Validate no YAML files in directory
# ---------------------------------------------------------------------------


def test_validate_no_yaml_files_in_dir(tmp_path: Path) -> None:
    """Directory with no YAML files should raise CommandError."""
    workspace = _setup_workspace(tmp_path)
    empty_dir = workspace / "empty"
    empty_dir.mkdir(parents=True)
    # Add a non-YAML file
    (empty_dir / "readme.txt").write_text("No FRZ data here", encoding="utf-8")

    args = argparse.Namespace(input=str(empty_dir))
    with pytest.raises(CommandError, match="No FRZ YAML found"):
        validate_frz(args)


# ---------------------------------------------------------------------------
# Test 16: Find workspace root not found
# ---------------------------------------------------------------------------


def test_find_workspace_root_not_found(tmp_path: Path) -> None:
    """Workspace root discovery in a clean temp dir should fail."""
    from frz_manage_runtime import _find_workspace_root

    # Create a temp dir with no .planning or ssot anywhere
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir(parents=True)

    with patch("frz_manage_runtime.Path.cwd", return_value=clean_dir):
        with pytest.raises(CommandError, match="Workspace root not found"):
            _find_workspace_root()


# ---------------------------------------------------------------------------
# Test 17: Freeze creates source snapshot
# ---------------------------------------------------------------------------


def test_freeze_creates_source_snapshot(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Freeze should create artifact directory with freeze.yaml and input/ snapshot."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    _write_frz_yaml(input_dir, _make_valid_frz_yaml())
    # Add an extra file for evidence trail
    (input_dir / "notes.md").write_text("Test notes", encoding="utf-8")

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(input=str(input_dir), id="FRZ-001")
        result = freeze_frz(args)
        assert result == 0

    # Verify artifacts
    artifact_dir = workspace / "artifacts" / "frz-input" / "FRZ-001"
    freeze_yaml = artifact_dir / "freeze.yaml"
    assert freeze_yaml.exists(), f"freeze.yaml should exist at {freeze_yaml}"

    input_snapshot = artifact_dir / "input"
    assert input_snapshot.exists()
    assert (input_snapshot / "frz-package.yaml").exists()
    assert (input_snapshot / "notes.md").exists()


# ---------------------------------------------------------------------------
# Test 18: Extract mode returns not implemented
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Test 18: Extract with valid frozen FRZ
# ---------------------------------------------------------------------------


def _setup_frozen_frz_workspace(tmp_path: Path) -> Path:
    """Create a workspace with a registered frozen FRZ package."""
    workspace = _setup_workspace(tmp_path)

    frz_dir = workspace / "artifacts" / "frz-input" / "FRZ-001"
    frz_dir.mkdir(parents=True)
    frz_data = {
        "frz_package": {
            "frz_id": "FRZ-001",
            "status": "frozen",
            "product_boundary": {"in_scope": ["A"], "out_of_scope": []},
            "core_journeys": [
                {"id": "JRN-001", "name": "Login", "steps": ["Enter credentials", "Submit form"]},
            ],
            "domain_model": [
                {"id": "ENT-001", "name": "User", "contract": {"email": "string"}},
            ],
            "state_machine": [
                {"id": "SM-001", "name": "Status", "states": ["active", "inactive"], "transitions": []},
            ],
            "acceptance_contract": {
                "expected_outcomes": ["User can log in"],
                "acceptance_impact": ["UX"],
            },
            "constraints": [],
            "derived_allowed": ["scope", "user_journeys", "entities", "state_transitions", "acceptance_criteria", "constraints", "open_questions"],
            "known_unknowns": [],
        }
    }
    yaml_path = frz_dir / "freeze.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(frz_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Register in FRZ registry
    reg_dir = workspace / "ssot" / "registry"
    reg_data = {
        "frz_registry": [
            {
                "frz_id": "FRZ-001",
                "status": "frozen",
                "created_at": "2026-01-01T00:00:00+00:00",
                "package_ref": str(yaml_path),
                "msc_valid": True,
                "version": "1.0",
            }
        ]
    }
    (reg_dir / "frz-registry.yaml").write_text(
        yaml.dump(reg_data, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return workspace


def test_extract_valid_frozen_frz(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """extract with valid frozen FRZ should return 0 with JSON result."""
    workspace = _setup_frozen_frz_workspace(tmp_path)
    output_dir = workspace / "output"

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(frz="FRZ-001", output=str(output_dir), cascade=False)
        result = extract_frz(args)

    assert result == 0
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "ok" in output
    assert "output_dir" in output
    assert "anchors" in output
    assert "guard" in output


def test_extract_invalid_frz_id(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """extract with invalid FRZ ID should return 2."""
    workspace = _setup_workspace(tmp_path)

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(frz="INVALID", output="/tmp/out", cascade=False)
        result = extract_frz(args)

    assert result == 2


def test_extract_frz_not_in_registry(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """extract with FRZ not in registry should return REGISTRY_MISS exit code."""
    workspace = _setup_workspace(tmp_path)

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(frz="FRZ-999", output="/tmp/out", cascade=False)
        result = extract_frz(args)

    assert result != 0
    captured = capsys.readouterr()
    assert "REGISTRY_MISS" in captured.err or "not found" in captured.err.lower()


def test_extract_output_files_exist(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """extract should create src-package.json and extraction-report.json."""
    workspace = _setup_frozen_frz_workspace(tmp_path)
    output_dir = workspace / "output"

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        args = argparse.Namespace(frz="FRZ-001", output=str(output_dir), cascade=False)
        result = extract_frz(args)

    assert result == 0
    assert (output_dir / "src-package.json").exists()
    assert (output_dir / "extraction-report.json").exists()


def test_build_parser_has_cascade_flag() -> None:
    """Parser should have --cascade flag for extract subcommand."""
    parser = build_parser()
    args = parser.parse_args(["extract", "--frz", "FRZ-001", "--output", "/tmp", "--cascade"])
    assert args.cascade is True

    args_no_cascade = parser.parse_args(["extract", "--frz", "FRZ-001", "--output", "/tmp"])
    assert args_no_cascade.cascade is False


def test_run_cascade_skips_missing_functions(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """run_cascade should skip layers where extract function doesn't exist."""
    workspace = _setup_frozen_frz_workspace(tmp_path)

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        result = run_cascade("FRZ-001", workspace)

    # EPIC/FEAT/TECH/UI/TEST/IMPL modules likely don't exist, so they should be skipped
    assert "results" in result
    skipped = [r for r in result["results"] if r.get("status") == "skipped"]
    assert len(skipped) >= 1  # At least EPIC should be skipped


def test_run_cascade_summary_has_counts(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """run_cascade should return summary with total/passed/blocked/skipped counts."""
    workspace = _setup_frozen_frz_workspace(tmp_path)

    with patch("frz_manage_runtime.Path.cwd", return_value=workspace):
        result = run_cascade("FRZ-001", workspace)

    # Even if all downstream layers are skipped, summary should exist
    if result.get("ok"):
        assert "summary" in result
        summary = result["summary"]
        assert "total" in summary
        assert "passed" in summary
        assert "blocked" in summary
        assert "skipped" in summary
        assert summary["total"] == 7  # All SSOT layers


# ---------------------------------------------------------------------------
# Test 19: Main dispatch with no args
# ---------------------------------------------------------------------------


def test_main_dispatch_with_no_args(capsys: pytest.CaptureFixture) -> None:
    """main() with no subcommand should return non-zero and print help."""
    result = main([])
    assert result != 0
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower() or "help" in captured.out.lower()


# ---------------------------------------------------------------------------
# Test 20: Validate malicious YAML rejected
# ---------------------------------------------------------------------------


def test_validate_malicious_yaml_rejected(tmp_path: Path) -> None:
    """YAML with !!python/object tag should be rejected by yaml.safe_load."""
    workspace = _setup_workspace(tmp_path)
    input_dir = workspace / "input"
    input_dir.mkdir(parents=True)

    # Create malicious YAML
    malicious_yaml_path = input_dir / "frz-package.yaml"
    malicious_yaml_path.write_text(
        "!!python/object/apply:os.system\n- 'echo pwned'",
        encoding="utf-8",
    )

    args = argparse.Namespace(input=str(input_dir))
    # yaml.safe_load raises ConstructorError for unregistered tags
    import yaml
    with pytest.raises(yaml.constructor.ConstructorError):
        validate_frz(args)
