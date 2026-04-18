"""Unit tests for FRZ schema and MSC validation.

Tests cover: FRZPackage construction, frozen dataclass enforcement,
MSC validator pass/fail cases, file validation, ID format validation,
status enum handling, and YAML parsing.
"""

import tempfile

import pytest
import yaml

from cli.lib.frz_schema import (
    AcceptanceContract,
    CoreJourney,
    DomainEntity,
    FRZEvidence,
    FRZPackage,
    FRZSchemaError,
    FRZStatus,
    KnownUnknown,
    MSCValidator,
    ProductBoundary,
    StateMachine,
    _parse_frz_dict,
)


# ---------------------------------------------------------------------------
# FRZPackage structure tests
# ---------------------------------------------------------------------------


def test_frz_package_structure():
    """FRZPackage with minimal valid data — all 5 MSC dimensions populated."""
    pkg = FRZPackage(
        frz_id="FRZ-001",
        status=FRZStatus.draft,
        product_boundary=ProductBoundary(in_scope=["feature X"], out_of_scope=["feature Y"]),
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["enter creds", "verify"])],
        domain_model=[DomainEntity(id="ENT-001", name="User", contract={"email": "required"})],
        state_machine=[StateMachine(id="SM-001", name="Order", states=["created", "shipped"], transitions=[])],
        acceptance_contract=AcceptanceContract(expected_outcomes=["user can login"], acceptance_impact=["security"]),
    )

    assert pkg.artifact_type == "frz_package"
    assert pkg.status == FRZStatus.draft
    assert pkg.version == "1.0"

    # Verify default values
    default_pkg = FRZPackage()
    assert default_pkg.frz_id is None
    assert default_pkg.status == FRZStatus.draft
    assert default_pkg.version == "1.0"
    assert default_pkg.core_journeys == []
    assert default_pkg.domain_model == []
    assert default_pkg.state_machine == []
    assert default_pkg.constraints == []
    assert default_pkg.derived_allowed == []
    assert default_pkg.known_unknowns == []
    assert default_pkg.enums == []

    # Verify frozen
    with pytest.raises(Exception):  # FrozenInstanceError
        pkg.status = FRZStatus.frozen  # type: ignore[misc]


def test_frz_package_status_is_enum():
    """FRZPackage.status must be FRZStatus enum, not bare string."""
    pkg = FRZPackage()
    assert pkg.status is FRZStatus.draft
    assert isinstance(pkg.status, FRZStatus)

    # Parsing dict with status string returns enum
    parsed = _parse_frz_dict({"frz_id": "FRZ-001", "status": "frozen"})
    assert parsed.status == FRZStatus.frozen
    assert isinstance(parsed.status, FRZStatus)


# ---------------------------------------------------------------------------
# MSC Validator — valid package
# ---------------------------------------------------------------------------


def test_msc_validator_valid_package():
    """All 5 MSC dimensions populated with minimum content → msc_valid=True."""
    pkg = FRZPackage(
        product_boundary=ProductBoundary(in_scope=["feature X"], out_of_scope=[]),
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["step1", "step2"])],
        domain_model=[DomainEntity(id="ENT-001", name="User", contract={"email": "required"})],
        state_machine=[StateMachine(id="SM-001", name="Order", states=["created", "shipped"], transitions=[])],
        acceptance_contract=AcceptanceContract(expected_outcomes=["user can login"], acceptance_impact=[]),
    )

    result = MSCValidator.validate(pkg)

    assert result["msc_valid"] is True
    assert result["status"] == "frozen"
    assert result["missing"] == []
    assert len(result["present"]) == 5


# ---------------------------------------------------------------------------
# MSC Validator — missing dimensions
# ---------------------------------------------------------------------------


def test_msc_validator_missing_all_dims():
    """Default (empty) FRZPackage → all 5 dimensions missing."""
    pkg = FRZPackage()
    result = MSCValidator.validate(pkg)

    assert result["msc_valid"] is False
    assert result["status"] == "blocked"
    assert len(result["missing"]) == 5
    assert "product_boundary" in result["missing"]
    assert "core_journeys" in result["missing"]
    assert "domain_model" in result["missing"]
    assert "state_machine" in result["missing"]
    assert "acceptance_contract" in result["missing"]


def test_msc_validator_partial_package():
    """Only product_boundary populated → 4 missing."""
    pkg = FRZPackage(
        product_boundary=ProductBoundary(in_scope=["feature X"], out_of_scope=[]),
    )

    result = MSCValidator.validate(pkg)

    assert result["msc_valid"] is False
    assert len(result["missing"]) == 4
    assert "product_boundary" in result["present"]


# ---------------------------------------------------------------------------
# MSC Validator — minimum content rules
# ---------------------------------------------------------------------------


def test_msc_validator_empty_boundary_rejected():
    """ProductBoundary with empty in_scope and out_of_scope → rejected."""
    pkg = FRZPackage(
        product_boundary=ProductBoundary(in_scope=[], out_of_scope=[]),
    )

    result = MSCValidator.validate(pkg)

    assert "product_boundary" in result["missing"]


def test_msc_validator_single_step_journey_rejected():
    """CoreJourney with only 1 step → rejected."""
    pkg = FRZPackage(
        core_journeys=[CoreJourney(id="JRN-001", name="Login", steps=["only one"])],
    )

    result = MSCValidator.validate(pkg)

    assert "core_journeys" in result["missing"]


def test_msc_validator_empty_contract_entity_rejected():
    """DomainEntity with empty contract dict → rejected."""
    pkg = FRZPackage(
        domain_model=[DomainEntity(id="ENT-001", name="User", contract={})],
    )

    result = MSCValidator.validate(pkg)

    assert "domain_model" in result["missing"]


def test_msc_validator_single_state_machine_rejected():
    """StateMachine with only 1 state → rejected."""
    pkg = FRZPackage(
        state_machine=[StateMachine(id="SM-001", name="Order", states=["only"], transitions=[])],
    )

    result = MSCValidator.validate(pkg)

    assert "state_machine" in result["missing"]


def test_msc_validator_empty_acceptance_contract_rejected():
    """AcceptanceContract with empty expected_outcomes → rejected."""
    pkg = FRZPackage(
        acceptance_contract=AcceptanceContract(expected_outcomes=[], acceptance_impact=[]),
    )

    result = MSCValidator.validate(pkg)

    assert "acceptance_contract" in result["missing"]


# ---------------------------------------------------------------------------
# File validation tests
# ---------------------------------------------------------------------------


def test_validate_file_not_found():
    """Nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        MSCValidator.validate_file("/nonexistent/path.yaml")


def test_validate_file_valid_yaml():
    """Valid FRZ YAML file validates successfully."""
    valid_frz = {
        "frz_package": {
            "frz_id": "FRZ-001",
            "product_boundary": {"in_scope": ["feature X"], "out_of_scope": []},
            "core_journeys": [{"id": "JRN-001", "name": "Login", "steps": ["a", "b"]}],
            "domain_model": [{"id": "ENT-001", "name": "User", "contract": {"email": "required"}}],
            "state_machine": [{"id": "SM-001", "name": "Order", "states": ["new", "done"], "transitions": []}],
            "acceptance_contract": {"expected_outcomes": ["works"], "acceptance_impact": []},
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(valid_frz, f)
        f.flush()

        result = MSCValidator.validate_file(f.name)
        assert result["msc_valid"] is True


def test_validate_file_malformed_yaml():
    """Malformed YAML raises yaml.YAMLError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("{{{{")
        f.flush()

        with pytest.raises(yaml.YAMLError):
            MSCValidator.validate_file(f.name)


def test_validate_file_empty_yaml():
    """Empty YAML file raises FRZSchemaError."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("# just a comment\n")
        f.flush()

        with pytest.raises(FRZSchemaError):
            MSCValidator.validate_file(f.name)


# ---------------------------------------------------------------------------
# FRZSchemaError tests
# ---------------------------------------------------------------------------


def test_frz_schema_error():
    """FRZSchemaError is a subclass of ValueError."""
    assert issubclass(FRZSchemaError, ValueError)
    with pytest.raises(FRZSchemaError):
        raise FRZSchemaError("test error")


# ---------------------------------------------------------------------------
# _parse_frz_dict tests
# ---------------------------------------------------------------------------


def test_parse_frz_dict_minimal():
    """Minimal dict → FRZPackage with defaults."""
    pkg = _parse_frz_dict({"frz_id": "FRZ-001"})

    assert pkg.frz_id == "FRZ-001"
    assert pkg.artifact_type == "frz_package"
    assert pkg.version == "1.0"
    assert pkg.status == FRZStatus.draft
    assert pkg.core_journeys == []
    assert pkg.domain_model == []
    assert pkg.state_machine == []
    assert pkg.constraints == []
    assert pkg.derived_allowed == []
    assert pkg.known_unknowns == []
    assert pkg.enums == []
    assert pkg.product_boundary is None
    assert pkg.acceptance_contract is None
    assert pkg.evidence is None
    assert pkg.created_at is None
    assert pkg.frozen_at is None


def test_parse_frz_dict_full():
    """Complete FRZ dict → fully typed FRZPackage."""
    data = {
        "frz_id": "FRZ-001",
        "status": "freeze_ready",
        "version": "1.0",
        "created_at": "2026-04-18T00:00:00Z",
        "product_boundary": {"in_scope": ["feature A"], "out_of_scope": ["feature B"]},
        "core_journeys": [{"id": "JRN-001", "name": "Login", "steps": ["enter", "verify"]}],
        "domain_model": [{"id": "ENT-001", "name": "User", "contract": {"email": "required"}}],
        "state_machine": [{"id": "SM-001", "name": "Order", "states": ["new", "done"], "transitions": [{"from": "new", "to": "done"}]}],
        "acceptance_contract": {"expected_outcomes": ["user logs in"], "acceptance_impact": ["security"]},
        "known_unknowns": [{"id": "UNK-001", "topic": "TBD", "owner": "alice"}],
        "evidence": {"source_refs": ["prd.md"], "raw_path": "artifacts/"},
        "constraints": ["must be fast"],
        "derived_allowed": ["ui"],
        "enums": [{"name": "Color", "values": ["red", "green"]}],
    }

    pkg = _parse_frz_dict(data)

    assert pkg.frz_id == "FRZ-001"
    assert pkg.status == FRZStatus.freeze_ready
    assert len(pkg.core_journeys) == 1
    assert len(pkg.domain_model) == 1
    assert len(pkg.state_machine) == 1
    assert len(pkg.known_unknowns) == 1
    assert len(pkg.constraints) == 1
    assert len(pkg.derived_allowed) == 1
    assert len(pkg.enums) == 1

    # Verify sub-entity types
    assert isinstance(pkg.product_boundary, ProductBoundary)
    assert isinstance(pkg.core_journeys[0], CoreJourney)
    assert isinstance(pkg.domain_model[0], DomainEntity)
    assert isinstance(pkg.state_machine[0], StateMachine)
    assert isinstance(pkg.acceptance_contract, AcceptanceContract)
    assert isinstance(pkg.known_unknowns[0], KnownUnknown)
    assert isinstance(pkg.evidence, FRZEvidence)


def test_parse_frz_dict_invalid_frz_id_format():
    """Invalid FRZ ID formats raise FRZSchemaError."""
    with pytest.raises(FRZSchemaError):
        _parse_frz_dict({"frz_id": "invalid-id"})

    with pytest.raises(FRZSchemaError):
        _parse_frz_dict({"frz_id": "frz-001"})

    # Valid format succeeds
    pkg = _parse_frz_dict({"frz_id": "FRZ-001"})
    assert pkg.frz_id == "FRZ-001"


def test_parse_frz_dict_invalid_subentity_id():
    """Invalid sub-entity IDs raise FRZSchemaError."""
    with pytest.raises(FRZSchemaError):
        _parse_frz_dict({
            "core_journeys": [{"id": "bad-id", "name": "Test", "steps": ["a", "b"]}]
        })


def test_parse_frz_dict_unknown_keys_ignored():
    """Unknown fields are silently ignored."""
    pkg = _parse_frz_dict({"frz_id": "FRZ-001", "unknown_field": 42})
    assert pkg.frz_id == "FRZ-001"


# ---------------------------------------------------------------------------
# FRZStatus enum tests
# ---------------------------------------------------------------------------


def test_frz_status_enum_values():
    """FRZStatus enum has correct values."""
    assert FRZStatus.frozen.value == "frozen"
    assert FRZStatus.draft.value == "draft"
    assert FRZStatus.blocked.value == "blocked"
    assert FRZStatus.freeze_ready.value == "freeze_ready"
    assert FRZStatus.revised.value == "revised"
    assert FRZStatus.superseded.value == "superseded"
