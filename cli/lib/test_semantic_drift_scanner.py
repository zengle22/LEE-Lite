"""Unit tests for cli.lib.semantic_drift_scanner."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cli.lib.semantic_drift_scanner import (
    ViolationType,
    Violation,
    ScanResult,
    scan_overlay_elevation,
    scan_api_duplicates,
    scan_ssot,
    main,
)


def _make_ssot_dir(tmp_path: Path) -> Path:
    """Helper to create a test SSOT directory structure."""
    ssot_dir = tmp_path / "ssot"
    (ssot_dir / "epic").mkdir(parents=True)
    (ssot_dir / "feat").mkdir(parents=True)
    (ssot_dir / "api").mkdir(parents=True)
    return ssot_dir


# --- scan_overlay_elevation ---


def test_overlay_elevation_positive_governance() -> None:
    """Governance in primary topic is detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        feat_dir = ssot_dir / "feat"
        feat_dir.mkdir(parents=True)

        feat_file = feat_dir / "FEAT-001.md"
        feat_file.write_text("""# Governance Framework

## Primary Object: Governance

This feature defines the governance structure.
""")

        violations = scan_overlay_elevation(ssot_dir)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.OVERLAY_ELEVATION
        assert violations[0].severity == "blocker"
        assert "governance" in violations[0].detail.lower()


def test_overlay_elevation_positive_gate() -> None:
    """Gate in primary topic is detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        epic_dir = ssot_dir / "epic"
        epic_dir.mkdir(parents=True)

        epic_file = epic_dir / "EPIC-001.md"
        epic_file.write_text("""# Gate Management System

The primary object here is the Gate mechanism.
""")

        violations = scan_overlay_elevation(ssot_dir)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.OVERLAY_ELEVATION


def test_overlay_elevation_positive_handoff() -> None:
    """Handoff in primary topic is detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        feat_dir = ssot_dir / "feat"
        feat_dir.mkdir(parents=True)

        feat_file = feat_dir / "FEAT-001.md"
        feat_file.write_text("""# Handoff Orchestration

## Primary Object: Handoff

Handles handoff between different services.
""")

        violations = scan_overlay_elevation(ssot_dir)
        assert len(violations) == 1


def test_overlay_elevation_negative() -> None:
    """Normal feature is not flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        feat_dir = ssot_dir / "feat"
        feat_dir.mkdir(parents=True)

        feat_file = feat_dir / "FEAT-001.md"
        feat_file.write_text("""# User Authentication

## Primary Object: User

This feature handles user login and registration.
""")

        violations = scan_overlay_elevation(ssot_dir)
        assert len(violations) == 0


def test_overlay_elevation_multiple_files() -> None:
    """Multiple violations from different files are all detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        epic_dir = ssot_dir / "epic"
        feat_dir = ssot_dir / "feat"
        epic_dir.mkdir(parents=True)
        feat_dir.mkdir(parents=True)

        (epic_dir / "EPIC-001.md").write_text("""# Governance Framework
## Primary Object: Governance
""")
        (feat_dir / "FEAT-001.md").write_text("""# Gate Management
## Primary Object: Gate
""")
        (feat_dir / "FEAT-002.md").write_text("""# User Profile
## Primary Object: User
""")

        violations = scan_overlay_elevation(ssot_dir)
        assert len(violations) == 2


# --- scan_api_duplicates ---


def test_api_duplicates_positive() -> None:
    """Same endpoint in multiple files is detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        api_dir = ssot_dir / "api"
        api_dir.mkdir(parents=True)

        (api_dir / "API-001.md").write_text("""# User API
GET /api/v1/users
""")
        (api_dir / "API-002.md").write_text("""# User Management
GET /api/v1/users
""")

        violations = scan_api_duplicates(ssot_dir)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.API_DUPLICATE
        assert violations[0].severity == "blocker"
        assert "/api/v1/users" in violations[0].detail


def test_api_duplicates_negative() -> None:
    """Different endpoints are not flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        api_dir = ssot_dir / "api"
        api_dir.mkdir(parents=True)

        (api_dir / "API-001.md").write_text("""# User API
GET /api/v1/users
""")
        (api_dir / "API-002.md").write_text("""# Product API
POST /api/v1/products
""")

        violations = scan_api_duplicates(ssot_dir)
        assert len(violations) == 0


def test_api_duplicates_multiple_endpoints() -> None:
    """Multiple duplicate endpoints are detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        api_dir = ssot_dir / "api"
        api_dir.mkdir(parents=True)

        (api_dir / "API-001.md").write_text("""# API 1
GET /api/v1/users
POST /api/v1/products
""")
        (api_dir / "API-002.md").write_text("""# API 2
GET /api/v1/users
POST /api/v1/products
""")
        (api_dir / "API-003.md").write_text("""# API 3
GET /api/v1/orders
""")

        violations = scan_api_duplicates(ssot_dir)
        assert len(violations) == 2


def test_api_duplicates_yaml_files() -> None:
    """YAML files are also scanned for endpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        api_dir = ssot_dir / "api"
        api_dir.mkdir(parents=True)

        (api_dir / "API-001.yaml").write_text("""endpoint: /api/v1/users
method: GET
""")
        (api_dir / "API-002.yml").write_text("""path: /api/v1/users
method: GET
""")

        violations = scan_api_duplicates(ssot_dir)
        assert len(violations) == 1


# --- scan_ssot ---


def test_scan_ssot_combines_both_detectors() -> None:
    """scan_ssot returns violations from both detectors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        feat_dir = ssot_dir / "feat"
        api_dir = ssot_dir / "api"
        feat_dir.mkdir(parents=True)
        api_dir.mkdir(parents=True)

        (feat_dir / "FEAT-001.md").write_text("""# Governance Framework
## Primary Object: Governance
""")
        (api_dir / "API-001.md").write_text("GET /api/v1/users")
        (api_dir / "API-002.md").write_text("GET /api/v1/users")

        result = scan_ssot(ssot_dir)
        assert result.total_violations == 2
        assert result.blocker_count == 2
        assert result.warning_count == 0
        assert len(result.violations) == 2


def test_scan_ssot_no_violations() -> None:
    """scan_ssot returns clean result when no violations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        feat_dir = ssot_dir / "feat"
        api_dir = ssot_dir / "api"
        feat_dir.mkdir(parents=True)
        api_dir.mkdir(parents=True)

        (feat_dir / "FEAT-001.md").write_text("""# User Profile
## Primary Object: User
""")
        (api_dir / "API-001.md").write_text("GET /api/v1/users")
        (api_dir / "API-002.md").write_text("POST /api/v1/products")

        result = scan_ssot(ssot_dir)
        assert result.total_violations == 0
        assert result.blocker_count == 0
        assert result.warning_count == 0


# --- main / CLI ---


def test_cli_output_human(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI outputs human-readable format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        feat_dir = ssot_dir / "feat"
        feat_dir.mkdir(parents=True)

        (feat_dir / "FEAT-001.md").write_text("""# Governance Framework
## Primary Object: Governance
""")

        with patch("sys.argv", ["python -m cli.lib.semantic_drift_scanner", "--ssot-dir", str(ssot_dir), "--output", "human"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1  # blockers found

        captured = capsys.readouterr()
        assert "SSOT SEMANTIC DRIFT SCAN" in captured.out
        assert "Total violations: 1" in captured.out
        assert "Blockers: 1" in captured.out


def test_cli_output_json(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI outputs JSON format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ssot_dir = Path(tmpdir) / "ssot"
        feat_dir = ssot_dir / "feat"
        feat_dir.mkdir(parents=True)

        (feat_dir / "FEAT-001.md").write_text("""# Governance Framework
## Primary Object: Governance
""")

        with patch("sys.argv", ["python -m cli.lib.semantic_drift_scanner", "--ssot-dir", str(ssot_dir), "--output", "json"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1  # blockers found

        captured = capsys.readouterr()
        output_json = json.loads(captured.out)
        assert output_json["total_violations"] == 1
        assert output_json["blocker_count"] == 1
        assert len(output_json["violations"]) == 1


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI --help shows usage."""
    with patch("sys.argv", ["python -m cli.lib.semantic_drift_scanner", "--help"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert "--ssot-dir" in captured.out
    assert "--output" in captured.out
