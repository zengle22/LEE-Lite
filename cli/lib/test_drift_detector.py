"""Unit tests for cli.lib.drift_detector."""

from __future__ import annotations

import pytest

from cli.lib.drift_detector import (
    DriftResult,
    check_drift,
    check_derived_allowed,
    check_constraints,
    check_known_unknowns,
)
from cli.lib.frz_schema import (
    FRZPackage,
    CoreJourney,
    DomainEntity,
    KnownUnknown,
)


def _make_frz(
    core_journeys=None,
    domain_model=None,
    state_machine=None,
    acceptance_contract=None,
    constraints=None,
    derived_allowed=None,
    known_unknowns=None,
) -> FRZPackage:
    """Helper to create FRZPackage with optional overrides."""
    return FRZPackage(
        frz_id="FRZ-001",
        core_journeys=core_journeys or [],
        domain_model=domain_model or [],
        state_machine=state_machine or [],
        acceptance_contract=acceptance_contract,
        constraints=constraints or [],
        derived_allowed=derived_allowed or [],
        known_unknowns=known_unknowns or [],
    )


# --- check_drift ---


def test_anchor_missing_from_extraction() -> None:
    """Anchor exists in FRZ but not in extracted output."""
    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1"])]
    )
    result = check_drift("JRN-001", frz, target_data={})
    assert result.drift_type == "missing"
    assert result.has_drift is True
    assert "not present in extracted output" in result.detail


def test_anchor_missing_from_frz() -> None:
    """Anchor not found in FRZ baseline at all."""
    frz = _make_frz(core_journeys=[])
    result = check_drift("JRN-001", frz, target_data={"JRN-001": {"name": "Login"}})
    assert result.drift_type == "missing"
    assert result.has_drift is True
    assert "not found in FRZ baseline" in result.detail


def test_anchor_semantic_tampering() -> None:
    """Anchor name differs between FRZ and extracted output."""
    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1"])]
    )
    target_data = {"JRN-001": {"name": "Logout"}}
    result = check_drift("JRN-001", frz, target_data)
    assert result.drift_type == "tampered"
    assert result.has_drift is True
    assert "semantics differ" in result.detail


def test_anchor_no_drift() -> None:
    """Anchor matches between FRZ and extracted output."""
    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1"])]
    )
    target_data = {"JRN-001": {"name": "Login"}}
    result = check_drift("JRN-001", frz, target_data)
    assert result.drift_type == "none"
    assert result.has_drift is False
    assert result.detail == "OK"


def test_anchor_drift_case_insensitive() -> None:
    """Name comparison is case-insensitive (normalize to lowercase)."""
    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1"])]
    )
    target_data = {"JRN-001": {"name": "login"}}
    result = check_drift("JRN-001", frz, target_data)
    assert result.drift_type == "none"
    assert result.has_drift is False


def test_new_field_drift() -> None:
    """Target data has extra key not in FRZ anchor content."""
    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1"])]
    )
    target_data = {"JRN-001": {"name": "Login", "unauthorized_field": "value"}}
    result = check_drift("JRN-001", frz, target_data)
    assert result.drift_type == "new_field"
    assert result.has_drift is True


# --- check_derived_allowed ---


def test_non_derived_field_flagged() -> None:
    """Field not in derived_allowed or intrinsic keys is flagged."""
    frz = _make_frz(derived_allowed=["ui_layout"])
    output_data = {"ui_layout": [], "tech_details": []}
    violations = check_derived_allowed(frz, output_data)
    assert "tech_details" in violations


def test_derived_field_allowed() -> None:
    """Field in derived_allowed is not flagged."""
    frz = _make_frz(derived_allowed=["ui_layout", "tech_details"])
    output_data = {"ui_layout": [], "tech_details": []}
    violations = check_derived_allowed(frz, output_data)
    assert violations == []


def test_empty_derived_allowed_with_only_intrinsic_keys() -> None:
    """When derived_allowed is empty, intrinsic keys are still allowed."""
    frz = _make_frz(derived_allowed=[])
    output_data = {
        "artifact_type": "test",
        "schema_version": "1.0",
        "source_refs": [],
        "frz_ref": "FRZ-001",
        "traceability": [],
    }
    violations = check_derived_allowed(frz, output_data)
    assert violations == []


def test_empty_output_data() -> None:
    """Empty output data produces no violations."""
    frz = _make_frz(derived_allowed=["ui_layout"])
    violations = check_derived_allowed(frz, {})
    assert violations == []


# --- check_constraints ---


def test_constraint_violation() -> None:
    """Constraint not present in output_data keys is violated."""
    frz = _make_frz(constraints=["must_have_auth"])
    output_data = {"ui_layout": []}
    violations = check_constraints(frz, output_data)
    assert "must_have_auth" in violations


def test_constraint_satisfied() -> None:
    """Constraint present as key in output_data is satisfied."""
    frz = _make_frz(constraints=["must_have_auth"])
    output_data = {"must_have_auth": True, "ui_layout": []}
    violations = check_constraints(frz, output_data)
    assert violations == []


def test_empty_constraints() -> None:
    """No constraints means no violations."""
    frz = _make_frz(constraints=[])
    output_data = {"ui_layout": []}
    violations = check_constraints(frz, output_data)
    assert violations == []


# --- check_known_unknowns ---


def test_expired_known_unknown() -> None:
    """KnownUnknown with status='open' and expires_in containing '0' is expired."""
    frz = _make_frz(
        known_unknowns=[
            KnownUnknown(id="UNK-001", topic="Performance", status="open", expires_in="0 cycles")
        ]
    )
    expired = check_known_unknowns(frz, {})
    assert len(expired) == 1
    assert expired[0]["id"] == "UNK-001"
    assert expired[0]["status"] == "expired"


def test_known_unknown_not_expired() -> None:
    """KnownUnknown with non-zero expiry is not expired."""
    frz = _make_frz(
        known_unknowns=[
            KnownUnknown(id="UNK-002", topic="Security", status="open", expires_in="3 cycles")
        ]
    )
    expired = check_known_unknowns(frz, {})
    assert expired == []


def test_known_unknown_closed() -> None:
    """KnownUnknown with status='closed' is not expired regardless of expires_in."""
    frz = _make_frz(
        known_unknowns=[
            KnownUnknown(id="UNK-003", topic="Done", status="closed", expires_in="0 cycles")
        ]
    )
    expired = check_known_unknowns(frz, {})
    assert expired == []


def test_expired_known_unknown_with_expired_text() -> None:
    """KnownUnknown with 'expired' in expires_in is expired."""
    frz = _make_frz(
        known_unknowns=[
            KnownUnknown(id="UNK-004", topic="Old", status="open", expires_in="expired")
        ]
    )
    expired = check_known_unknowns(frz, {})
    assert len(expired) == 1
    assert expired[0]["id"] == "UNK-004"
    assert expired[0]["topic"] == "Old"


# --- combined scenarios ---


def test_combined_violations() -> None:
    """Multiple violation types detected together."""
    frz = _make_frz(
        derived_allowed=["ui_layout"],
        constraints=["must_have_auth"],
    )
    output_data = {"tech_details": []}
    field_violations = check_derived_allowed(frz, output_data)
    constraint_violations = check_constraints(frz, output_data)
    assert "tech_details" in field_violations
    assert "must_have_auth" in constraint_violations
