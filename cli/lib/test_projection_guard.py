"""Unit tests for cli.lib.projection_guard."""

from __future__ import annotations

import pytest

from cli.lib.projection_guard import (
    GuardResult,
    guard_projection,
    check_derived_allowed_fields,
)
from cli.lib.frz_schema import FRZPackage


def _make_frz(
    derived_allowed=None,
    constraints=None,
) -> FRZPackage:
    """Helper to create FRZPackage with optional overrides."""
    return FRZPackage(
        frz_id="FRZ-001",
        derived_allowed=derived_allowed or [],
        constraints=constraints or [],
    )


# --- guard_projection ---


def test_guard_pass_when_all_allowed() -> None:
    """All output fields are in derived_allowed whitelist."""
    frz = _make_frz(derived_allowed=["ui_layout", "tech_details"])
    output_data = {"ui_layout": [], "tech_details": []}
    result = guard_projection(frz, output_data)
    assert result.passed is True
    assert result.verdict == "pass"
    assert result.violations == []


def test_guard_block_when_non_allowed_field() -> None:
    """Output contains field not in derived_allowed."""
    frz = _make_frz(derived_allowed=["ui_layout"])
    output_data = {"ui_layout": [], "tech_details": []}
    result = guard_projection(frz, output_data)
    assert result.passed is False
    assert result.verdict == "block"
    assert any("tech_details" in v for v in result.violations)


def test_guard_pass_with_intrinsic_keys() -> None:
    """Only intrinsic keys in output passes even with empty derived_allowed."""
    frz = _make_frz(derived_allowed=[])
    output_data = {
        "artifact_type": "test",
        "schema_version": "1.0",
        "metadata": {},
        "created_at": "2024-01-01",
        "status": "draft",
        "version": "1.0",
    }
    result = guard_projection(frz, output_data)
    assert result.passed is True
    assert result.verdict == "pass"


def test_guard_block_on_constraint_violation() -> None:
    """Constraint not present in output_data keys causes block."""
    frz = _make_frz(derived_allowed=["ui_layout"], constraints=["must_have_auth"])
    output_data = {"ui_layout": []}
    result = guard_projection(frz, output_data)
    assert result.passed is False
    assert result.verdict == "block"
    assert any("must_have_auth" in v for v in result.violations)


def test_guard_combined_violations() -> None:
    """Both field and constraint violations appear in result."""
    frz = _make_frz(
        derived_allowed=["ui_layout"],
        constraints=["must_have_auth"],
    )
    output_data = {"tech_details": []}
    result = guard_projection(frz, output_data)
    assert result.passed is False
    assert result.verdict == "block"
    assert any("tech_details" in v for v in result.violations)
    assert any("must_have_auth" in v for v in result.violations)


def test_guard_empty_output_passes() -> None:
    """Empty output data always passes."""
    frz = _make_frz(derived_allowed=["ui_layout"], constraints=["must_have_auth"])
    result = guard_projection(frz, {})
    assert result.passed is True
    assert result.verdict == "pass"
    assert result.violations == []


# --- check_derived_allowed_fields ---


def test_check_derived_allowed_fields_basic() -> None:
    """Non-allowed fields returned sorted."""
    frz = _make_frz(derived_allowed=["ui_layout"])
    violations = check_derived_allowed_fields(frz, {"ui_layout", "tech_details"})
    assert violations == ["tech_details"]


def test_check_derived_allowed_fields_all_intrinsic() -> None:
    """Intrinsic keys are never flagged."""
    frz = _make_frz(derived_allowed=[])
    violations = check_derived_allowed_fields(frz, {"artifact_type", "metadata", "version"})
    assert violations == []


def test_check_derived_allowed_fields_mixed() -> None:
    """Mix of allowed and non-allowed fields."""
    frz = _make_frz(derived_allowed=["ui_layout"])
    violations = check_derived_allowed_fields(
        frz, {"ui_layout", "tech_details", "artifact_type", "secret_field"}
    )
    assert violations == ["secret_field", "tech_details"]
