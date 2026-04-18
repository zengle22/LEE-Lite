"""Unit tests for cli.lib.frz_extractor — FRZ→SRC rule-template projection."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from cli.lib.frz_extractor import (
    ExtractResult,
    EXTRACT_RULES,
    extract_src_from_frz,
    check_frz_coverage,
)
from cli.lib.errors import CommandError


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_workspace() -> Path:
    return Path(tempfile.mkdtemp())


@pytest.fixture
def frozen_frz_yaml(tmp_workspace: Path) -> Path:
    """Create a valid frozen FRZ package YAML and register it."""
    frz_dir = tmp_workspace / "artifacts" / "frz-input" / "FRZ-001"
    frz_dir.mkdir(parents=True)
    frz_data = {
        "frz_package": {
            "artifact_type": "frz_package",
            "frz_id": "FRZ-001",
            "version": "1.0",
            "status": "frozen",
            "product_boundary": {
                "in_scope": ["User authentication", "Password reset"],
                "out_of_scope": ["OAuth integration"],
            },
            "core_journeys": [
                {
                    "id": "JRN-001",
                    "name": "Login flow",
                    "steps": ["Enter credentials", "Submit form", "Verify token"],
                },
                {
                    "id": "JRN-002",
                    "name": "Password reset",
                    "steps": ["Request reset", "Enter code", "Set new password"],
                },
            ],
            "domain_model": [
                {
                    "id": "ENT-001",
                    "name": "User",
                    "contract": {"email": "string", "password_hash": "string"},
                },
            ],
            "state_machine": [
                {
                    "id": "SM-001",
                    "name": "Account status",
                    "states": ["pending", "active", "suspended"],
                    "transitions": [
                        {"from": "pending", "to": "active", "event": "verify_email"}
                    ],
                },
            ],
            "acceptance_contract": {
                "expected_outcomes": [
                    "User can log in with valid credentials",
                    "User sees error on invalid credentials",
                ],
                "acceptance_impact": ["Login UX", "Security audit trail"],
            },
            "constraints": [
                "Must use HTTPS for all endpoints",
                "Password must be hashed with bcrypt",
            ],
            "derived_allowed": ["scope", "user_journeys", "entities", "state_transitions", "acceptance_criteria", "constraints", "open_questions"],
            "known_unknowns": [
                {
                    "id": "UNK-001",
                    "topic": "OAuth integration timeline",
                    "status": "open",
                    "owner": "team-lead",
                    "expires_in": "2 cycles",
                },
            ],
        }
    }
    yaml_path = frz_dir / "freeze.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(frz_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Register in FRZ registry
    reg_dir = tmp_workspace / "ssot" / "registry"
    reg_dir.mkdir(parents=True)
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
    return yaml_path


# ---------------------------------------------------------------------------
# EXTRACT_RULES
# ---------------------------------------------------------------------------


def test_extract_rules_maps_all_msc_dimensions() -> None:
    """EXTRACT_RULES should cover all 5 MSC dimensions plus constraints/known_unknowns."""
    expected_keys = {
        "product_boundary", "core_journeys", "domain_model",
        "state_machine", "acceptance_contract", "constraints", "known_unknowns",
    }
    assert set(EXTRACT_RULES.keys()) == expected_keys


def test_extract_rules_has_correct_targets() -> None:
    """Each FRZ dimension should map to a specific SRC section."""
    assert EXTRACT_RULES["product_boundary"]["target"] == "scope"
    assert EXTRACT_RULES["core_journeys"]["target"] == "user_journeys"
    assert EXTRACT_RULES["domain_model"]["target"] == "entities"
    assert EXTRACT_RULES["state_machine"]["target"] == "state_transitions"
    assert EXTRACT_RULES["acceptance_contract"]["target"] == "acceptance_criteria"
    assert EXTRACT_RULES["constraints"]["target"] == "constraints"
    assert EXTRACT_RULES["known_unknowns"]["target"] == "open_questions"


# ---------------------------------------------------------------------------
# ExtractResult dataclass
# ---------------------------------------------------------------------------


def test_extract_result_is_frozen() -> None:
    """ExtractResult should be immutable."""
    result = ExtractResult(
        ok=True,
        output_dir="/tmp",
        anchors_registered=["JRN-001"],
        drift_results=[],
        guard_verdict="pass",
        warnings=[],
    )
    with pytest.raises(Exception):
        result.ok = False  # type: ignore[misc]


# ---------------------------------------------------------------------------
# extract_src_from_frz
# ---------------------------------------------------------------------------


def test_extract_valid_frozen_frz(tmp_workspace: Path, frozen_frz_yaml: Path) -> None:
    """extract_src_from_frz with valid frozen FRZ should return ok=True."""
    output_dir = tmp_workspace / "output"
    result = extract_src_from_frz("FRZ-001", tmp_workspace, output_dir)

    assert result.ok is True
    assert result.guard_verdict == "pass"
    assert "JRN-001" in result.anchors_registered
    assert "JRN-002" in result.anchors_registered
    assert "ENT-001" in result.anchors_registered
    assert "SM-001" in result.anchors_registered


def test_extract_creates_output_files(tmp_workspace: Path, frozen_frz_yaml: Path) -> None:
    """extract_src_from_frz should create src-package.json and src-package.yaml."""
    output_dir = tmp_workspace / "output"
    result = extract_src_from_frz("FRZ-001", tmp_workspace, output_dir)

    assert result.ok is True
    json_path = output_dir / "src-package.json"
    yaml_path = output_dir / "src-package.yaml"
    report_path = output_dir / "extraction-report.json"

    assert json_path.exists()
    assert yaml_path.exists()
    assert report_path.exists()

    # Verify JSON is valid
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "scope" in data
    assert "user_journeys" in data
    assert "entities" in data


def test_extract_frz_not_found(tmp_workspace: Path) -> None:
    """extract_src_from_frz with non-existent FRZ should raise REGISTRY_MISS."""
    # Create empty registry
    reg_dir = tmp_workspace / "ssot" / "registry"
    reg_dir.mkdir(parents=True)
    (reg_dir / "frz-registry.yaml").write_text("frz_registry: []\n", encoding="utf-8")

    with pytest.raises(CommandError) as exc_info:
        extract_src_from_frz("FRZ-999", tmp_workspace)
    assert exc_info.value.status_code == "REGISTRY_MISS"


def test_extract_frz_not_frozen(tmp_workspace: Path) -> None:
    """extract_src_from_frz with non-frozen FRZ should raise POLICY_DENIED."""
    reg_dir = tmp_workspace / "ssot" / "registry"
    reg_dir.mkdir(parents=True)
    reg_data = {
        "frz_registry": [
            {
                "frz_id": "FRZ-002",
                "status": "draft",
                "package_ref": "/tmp/placeholder",
                "msc_valid": False,
            }
        ]
    }
    (reg_dir / "frz-registry.yaml").write_text(
        yaml.dump(reg_data, default_flow_style=False), encoding="utf-8"
    )

    with pytest.raises(CommandError) as exc_info:
        extract_src_from_frz("FRZ-002", tmp_workspace)
    assert exc_info.value.status_code == "POLICY_DENIED"


def test_extract_invalid_frz_id(tmp_workspace: Path) -> None:
    """extract_src_from_frz with invalid FRZ ID should raise INVALID_REQUEST."""
    with pytest.raises(CommandError) as exc_info:
        extract_src_from_frz("INVALID", tmp_workspace)
    assert exc_info.value.status_code == "INVALID_REQUEST"


def test_extract_anchors_registered_with_src_projection(tmp_workspace: Path, frozen_frz_yaml: Path) -> None:
    """extract_src_from_frz should register anchors with projection_path=SRC."""
    from cli.lib.anchor_registry import AnchorRegistry

    output_dir = tmp_workspace / "output"
    result = extract_src_from_frz("FRZ-001", tmp_workspace, output_dir)

    assert result.ok is True

    registry = AnchorRegistry(tmp_workspace)
    jrn_entry = registry.resolve("JRN-001", projection_path="SRC")
    assert jrn_entry is not None
    assert jrn_entry.frz_ref == "FRZ-001"


def test_extract_guard_blocks_on_violation(tmp_workspace: Path) -> None:
    """If guard_projection blocks, extract result should have ok=False."""
    # Create FRZ with strict derived_allowed (empty whitelist)
    frz_dir = tmp_workspace / "artifacts" / "frz-input" / "FRZ-003"
    frz_dir.mkdir(parents=True)
    frz_data = {
        "frz_package": {
            "frz_id": "FRZ-003",
            "status": "frozen",
            "product_boundary": {"in_scope": ["A"], "out_of_scope": []},
            "core_journeys": [],
            "domain_model": [],
            "state_machine": [],
            "acceptance_contract": {"expected_outcomes": ["OK"], "acceptance_impact": []},
            "constraints": [],
            "derived_allowed": [],  # Empty whitelist — any output should block
            "known_unknowns": [],
        }
    }
    yaml_path = frz_dir / "freeze.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(frz_data, f, default_flow_style=False)

    reg_dir = tmp_workspace / "ssot" / "registry"
    reg_dir.mkdir(parents=True)
    reg_data = {
        "frz_registry": [
            {
                "frz_id": "FRZ-003",
                "status": "frozen",
                "package_ref": str(yaml_path),
                "msc_valid": True,
            }
        ]
    }
    (reg_dir / "frz-registry.yaml").write_text(
        yaml.dump(reg_data, default_flow_style=False), encoding="utf-8"
    )

    output_dir = tmp_workspace / "output"
    result = extract_src_from_frz("FRZ-003", tmp_workspace, output_dir)

    assert result.guard_verdict == "block"
    assert result.ok is False


# ---------------------------------------------------------------------------
# check_frz_coverage
# ---------------------------------------------------------------------------


def test_check_frz_coverage_tech_with_constraints() -> None:
    """TECH layer with technical constraints should have no warnings."""
    # Mock a FRZ package with technical constraints
    mock_frz = MagicMock()
    mock_frz.constraints = [
        "Must use HTTPS for all endpoints",
        "API must respond within 200ms",
    ]
    mock_frz.core_journeys = [
        MagicMock(id="JRN-001", name="Login", steps=["Enter credentials"])
    ]
    mock_frz.acceptance_contract = MagicMock(
        expected_outcomes=["User can log in"],
        acceptance_impact=["Login UX"],
    )
    mock_frz.domain_model = [
        MagicMock(id="ENT-001", name="User", contract={"email": "string"})
    ]

    warnings = check_frz_coverage(mock_frz, "TECH")
    assert len(warnings) == 0


def test_check_frz_coverage_tech_no_constraints() -> None:
    """TECH layer with no constraints should emit warning."""
    mock_frz = MagicMock()
    mock_frz.constraints = []
    warnings = check_frz_coverage(mock_frz, "TECH")
    assert any("TECH" in w for w in warnings)


def test_check_frz_coverage_ui_with_ui_steps() -> None:
    """UI layer with UI-related journey steps should have no warnings."""
    mock_frz = MagicMock()
    mock_frz.core_journeys = [
        MagicMock(id="JRN-001", name="Login", steps=["Click login button", "Enter password"])
    ]
    warnings = check_frz_coverage(mock_frz, "UI")
    assert len(warnings) == 0


def test_check_frz_coverage_ui_no_ui_steps() -> None:
    """UI layer with no UI-related steps should emit warning."""
    mock_frz = MagicMock()
    mock_frz.core_journeys = [
        MagicMock(id="JRN-001", name="Backend sync", steps=["Process data"])
    ]
    warnings = check_frz_coverage(mock_frz, "UI")
    assert any("UI" in w for w in warnings)


def test_check_frz_coverage_test_with_outcomes() -> None:
    """TEST layer with testable acceptance outcomes should have no warnings."""
    mock_frz = MagicMock()
    mock_frz.acceptance_contract = MagicMock(
        expected_outcomes=["User can log in with valid credentials"],
        acceptance_impact=[],
    )
    warnings = check_frz_coverage(mock_frz, "TEST")
    assert len(warnings) == 0


def test_check_frz_coverage_impl_with_domain() -> None:
    """IMPL layer with domain model contracts should have no warnings."""
    mock_frz = MagicMock()
    mock_frz.domain_model = [
        MagicMock(id="ENT-001", name="User", contract={"email": "string", "id": "uuid"})
    ]
    warnings = check_frz_coverage(mock_frz, "IMPL")
    assert len(warnings) == 0
