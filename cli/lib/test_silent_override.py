"""Unit tests for cli.lib.silent_override — RED phase (Task 1)."""

from __future__ import annotations

import pytest

from cli.lib.drift_detector import DriftResult
from cli.lib.errors import CommandError
from cli.lib.frz_schema import (
    FRZPackage,
    CoreJourney,
    DomainEntity,
    StateMachine,
    KnownUnknown,
    AcceptanceContract,
    ProductBoundary,
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


# --- RED: This import should fail until silent_override.py exists ---

def test_import_silent_override() -> None:
    """Module should be importable with expected exports."""
    from cli.lib.silent_override import (
        check_silent_override,
        OverrideResult,
        classify_change,
    )
    assert callable(check_silent_override)
    assert callable(classify_change)


def test_override_result_dataclass() -> None:
    """OverrideResult should be a frozen dataclass with required fields."""
    from cli.lib.silent_override import OverrideResult

    result = OverrideResult(
        passed=True,
        classification="ok",
        semantic_drift={"has_drift": False, "drift_results": [], "classification": "ok"},
        block_reasons=[],
        pass_with_revisions=[],
    )
    assert result.passed is True
    assert result.classification == "ok"
    assert result.semantic_drift["has_drift"] is False
    assert result.block_reasons == []
    assert result.pass_with_revisions == []


def test_classify_change_no_drift() -> None:
    """No drift + no disallowed fields → classification = 'ok'."""
    from cli.lib.silent_override import classify_change

    drift_results = [
        DriftResult(anchor_id="JRN-001", frz_ref="FRZ-001", has_drift=False, drift_type="none", detail="OK"),
    ]
    classification = classify_change(drift_results, disallowed_fields=[])
    assert classification == "ok"


def test_classify_change_new_field_in_derived_allowed() -> None:
    """New field within derived_allowed → classification = 'clarification'."""
    from cli.lib.silent_override import classify_change

    drift_results = [
        DriftResult(anchor_id="JRN-001", frz_ref="FRZ-001", has_drift=True, drift_type="new_field", detail="extra: tech_detail"),
    ]
    classification = classify_change(drift_results, disallowed_fields=[])
    assert classification == "clarification"


def test_classify_change_new_field_outside_derived_allowed() -> None:
    """New field outside derived_allowed → classification = 'semantic_change'."""
    from cli.lib.silent_override import classify_change

    drift_results = [
        DriftResult(anchor_id="JRN-001", frz_ref="FRZ-001", has_drift=True, drift_type="new_field", detail="extra: tech_detail"),
    ]
    classification = classify_change(drift_results, disallowed_fields=["tech_detail"])
    assert classification == "semantic_change"


def test_classify_change_tampered() -> None:
    """Tampered anchor → classification = 'semantic_change'."""
    from cli.lib.silent_override import classify_change

    drift_results = [
        DriftResult(anchor_id="JRN-001", frz_ref="FRZ-001", has_drift=True, drift_type="tampered", detail="semantics differ"),
    ]
    classification = classify_change(drift_results, disallowed_fields=[])
    assert classification == "semantic_change"


def test_classify_change_missing() -> None:
    """Missing anchor → classification = 'semantic_change'."""
    from cli.lib.silent_override import classify_change

    drift_results = [
        DriftResult(anchor_id="JRN-001", frz_ref="FRZ-001", has_drift=True, drift_type="missing", detail="not found"),
    ]
    classification = classify_change(drift_results, disallowed_fields=[])
    assert classification == "semantic_change"


def test_classify_change_constraint_violation() -> None:
    """Constraint violation → classification = 'semantic_change'."""
    from cli.lib.silent_override import classify_change

    drift_results = [
        DriftResult(anchor_id="JRN-001", frz_ref="FRZ-001", has_drift=True, drift_type="constraint_violation", detail="constraint violated"),
    ]
    classification = classify_change(drift_results, disallowed_fields=[])
    assert classification == "semantic_change"


def test_check_silent_override_no_drift() -> None:
    """Full check with no drift → passed=True, classification='ok'."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        derived_allowed=["tech_detail"],
    )
    # Output must contain all anchor fields to avoid new_field drift
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
    }
    result = check_silent_override(frz, output_data)
    assert result.passed is True
    assert result.classification == "ok"
    assert result.block_reasons == []


def test_check_silent_override_constraint_violation_blocks() -> None:
    """Constraint violation → block with reason containing 'constraint_violation'."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        constraints=["must_have_auth"],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
    }
    result = check_silent_override(frz, output_data)
    assert result.passed is False
    assert any("constraint_violation" in r for r in result.block_reasons)


def test_check_silent_override_field_outside_derived_allowed_blocks() -> None:
    """New field outside derived_allowed → block."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        derived_allowed=["tech_detail"],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
        "forbidden_field": "value",
    }
    result = check_silent_override(frz, output_data)
    assert result.passed is False
    assert result.classification == "semantic_change"


def test_check_silent_override_anchor_filter_journey_only() -> None:
    """anchor_filter with JRN only → only JRN anchors checked."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        domain_model=[DomainEntity(id="ENT-001", name="User", contract={"email": "str"})],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
        # ENT-001 intentionally missing — should not block with JRN filter
    }
    result = check_silent_override(frz, output_data, anchor_filter={"JRN"})
    assert result.passed is True


def test_check_silent_override_expired_known_unknown_pass_with_revisions() -> None:
    """Expired known_unknown → pass_with_revisions not empty."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        known_unknowns=[
            KnownUnknown(id="UNK-001", topic="Performance", status="open", expires_in="0 cycles"),
        ],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
    }
    result = check_silent_override(frz, output_data)
    assert len(result.pass_with_revisions) > 0


def test_check_silent_override_semantic_drift_field_present() -> None:
    """OverrideResult must have semantic_drift with required sub-fields."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
    }
    result = check_silent_override(frz, output_data)
    sd = result.semantic_drift
    assert "has_drift" in sd
    assert "drift_results" in sd
    assert "classification" in sd
    assert isinstance(sd["has_drift"], bool)
    assert isinstance(sd["drift_results"], list)
    assert sd["classification"] == result.classification


# --- FRZ Loading Tests (mocked) ---


def test_extract_frz_ref_from_param() -> None:
    """FRZ ref from parameter takes priority."""
    from cli.lib.silent_override import _extract_frz_ref

    output = {"frz_ref": "FRZ-999"}
    result = _extract_frz_ref(output, frz_id="FRZ-123")
    assert result == "FRZ-123"


def test_extract_frz_ref_from_output() -> None:
    """FRZ ref extracted from output data when no param."""
    from cli.lib.silent_override import _extract_frz_ref

    output = {"frz_ref": "FRZ-456", "other": "data"}
    result = _extract_frz_ref(output, frz_id=None)
    assert result == "FRZ-456"


def test_extract_frz_ref_missing_raises_error() -> None:
    """No FRZ ref in output or params → CommandError."""
    from cli.lib.silent_override import _extract_frz_ref

    with pytest.raises(CommandError) as exc_info:
        _extract_frz_ref({"other": "data"}, frz_id=None)
    assert exc_info.value.status_code == "INVALID_REQUEST"
    assert "No FRZ reference found" in exc_info.value.message


def test_check_silent_override_anchor_tampered_blocks() -> None:
    """Anchor name differs → block with 'tampered' reason."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Logout", "id": "JRN-001", "steps": ["step1", "step2"]},
    }
    result = check_silent_override(frz, output_data)
    assert result.passed is False
    assert result.classification == "semantic_change"
    assert any("tampered" in r for r in result.block_reasons)


def test_check_silent_override_anchor_missing_blocks() -> None:
    """Anchor missing from output → block with 'anchor_missing' reason."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        domain_model=[DomainEntity(id="ENT-001", name="User", contract={"email": "str"})],
    )
    # JRN-001 present but ENT-001 missing
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
    }
    result = check_silent_override(frz, output_data)
    assert result.passed is False
    assert result.classification == "semantic_change"
    assert any("anchor_missing" in r for r in result.block_reasons)


def test_check_silent_override_mixed_ok_and_new_field() -> None:
    """All ok + new field in derived_allowed → classification='clarification', passed=True."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        derived_allowed=["tech_detail"],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        "JRN-001": {"name": "Login", "id": "JRN-001", "steps": ["step1", "step2"]},
        "tech_detail": "some implementation detail",
    }
    result = check_silent_override(frz, output_data)
    assert result.passed is True
    assert result.classification == "clarification"
    assert len(result.pass_with_revisions) > 0


def test_check_silent_override_product_boundary_mode() -> None:
    """mode=product_boundary → empty anchor_filter → skip anchor checks."""
    from cli.lib.silent_override import check_silent_override

    frz = _make_frz(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
    )
    output_data = {
        "frz_ref": "FRZ-001",
        # No JRN-001 content — should not block with empty anchor filter
    }
    result = check_silent_override(frz, output_data, anchor_filter=set())
    # No anchor checks, no constraints
    assert result.passed is True
