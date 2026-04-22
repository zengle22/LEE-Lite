"""Tests for cli.lib.enum_guard."""

import pytest

from cli.lib.enum_guard import (
    AssertionLayer,
    ENUM_REGISTRY,
    EnumGuardError,
    EnumGuardViolation,
    FailureClass,
    FORBIDDEN_SEMANTICS,
    ModuleId,
    PhaseId,
    SkillId,
    check_field,
    validate_enums,
    validate_field,
)
from cli.lib.gate_schema import GateVerdict


class TestEnumDefinitions:
    def test_skill_id_count(self):
        assert len(SkillId) == 2

    def test_skill_id_values(self):
        assert SkillId.QA_TEST_PLAN.value == "qa.test-plan"
        assert SkillId.QA_TEST_RUN.value == "qa.test-run"

    def test_module_id_count(self):
        assert len(ModuleId) == 21

    def test_module_id_values(self):
        expected = [
            "feat-to-testset", "api-plan-compile", "api-manifest-compile",
            "api-spec-compile", "e2e-plan-compile", "e2e-manifest-compile",
            "e2e-spec-compile", "environment-provision", "run-manifest-gen",
            "scenario-spec-compile", "state-machine-executor", "bypass-detector",
            "independent-verifier", "accident-package", "failure-classifier",
            "test-data-provision", "l0-smoke-check", "test-exec-web-e2e",
            "test-exec-cli", "settlement", "gate-evaluation",
        ]
        assert sorted(e.value for e in ModuleId) == sorted(expected)

    def test_assertion_layer_count(self):
        assert len(AssertionLayer) == 3

    def test_assertion_layer_values(self):
        assert AssertionLayer.A.value == "A"
        assert AssertionLayer.B.value == "B"
        assert AssertionLayer.C.value == "C"

    def test_failure_class_count(self):
        assert len(FailureClass) == 8

    def test_failure_class_values(self):
        expected = ["ENV", "DATA", "SCRIPT", "ORACLE", "BYPASS", "PRODUCT", "FLAKY", "TIMEOUT"]
        assert sorted(e.value for e in FailureClass) == sorted(expected)

    def test_gate_verdict_count(self):
        assert len(GateVerdict) == 4

    def test_gate_verdict_values(self):
        assert GateVerdict.PASS.value == "pass"
        assert GateVerdict.CONDITIONAL_PASS.value == "conditional_pass"
        assert GateVerdict.FAIL.value == "fail"
        assert GateVerdict.PROVISIONAL_PASS.value == "provisional_pass"

    def test_phase_id_count(self):
        assert len(PhaseId) == 5

    def test_phase_id_values(self):
        assert PhaseId.PHASE_1A.value == "1a"
        assert PhaseId.PHASE_1B.value == "1b"
        assert PhaseId.PHASE_2.value == "2"
        assert PhaseId.PHASE_3.value == "3"
        assert PhaseId.PHASE_4.value == "4"

    def test_gate_verdict_imported_not_redefined(self):
        """GateVerdict comes from gate_schema, not enum_guard."""
        from cli.lib.gate_schema import GateVerdict as GateVerdictOrig
        assert GateVerdict is GateVerdictOrig


class TestValidateField:
    def test_valid_skill_id(self):
        result = validate_field("skill_id", "qa.test-plan", "test")
        assert result == []

    def test_invalid_skill_id(self):
        result = validate_field("skill_id", "bad_value", "test")
        assert len(result) == 1
        assert result[0].field == "skill_id"
        assert result[0].value == "bad_value"

    def test_valid_module_id(self):
        result = validate_field("module_id", "feat-to-testset", "test")
        assert result == []

    def test_invalid_module_id_lists_all_allowed(self):
        result = validate_field("module_id", "unknown-module", "test")
        assert len(result) == 1
        assert len(result[0].allowed) == 21
        assert "feat-to-testset" in result[0].allowed

    def test_valid_assertion_layer(self):
        result = validate_field("assertion_layer", "A", "test")
        assert result == []

    def test_invalid_assertion_layer(self):
        result = validate_field("assertion_layer", "D", "test")
        assert len(result) == 1

    def test_valid_failure_class(self):
        result = validate_field("failure_class", "ENV", "test")
        assert result == []

    def test_invalid_failure_class(self):
        result = validate_field("failure_class", "UNKNOWN", "test")
        assert len(result) == 1

    def test_valid_gate_verdict(self):
        result = validate_field("gate_verdict", "pass", "test")
        assert result == []

    def test_invalid_gate_verdict(self):
        result = validate_field("gate_verdict", "custom_verdict", "test")
        assert len(result) == 1

    def test_valid_phase(self):
        result = validate_field("phase", "1a", "test")
        assert result == []

    def test_invalid_phase(self):
        result = validate_field("phase", "5", "test")
        assert len(result) == 1

    def test_unknown_field(self):
        result = validate_field("nonexistent_field", "any", "test")
        assert len(result) == 1
        assert result[0].field == "nonexistent_field"


class TestValidateEnums:
    def test_all_valid(self):
        data = {"skill_id": "qa.test-plan", "phase": "2"}
        result = validate_enums(data, "test")
        assert result == []

    def test_multiple_invalid_collects_all_errors(self):
        data = {"skill_id": "bad", "phase": "x"}
        result = validate_enums(data, "test")
        assert len(result) == 2

    def test_mixed_valid_and_invalid(self):
        data = {"skill_id": "qa.test-plan", "phase": "x"}
        result = validate_enums(data, "test")
        assert len(result) == 1
        assert result[0].field == "phase"

    def test_empty_dict(self):
        result = validate_enums({}, "test")
        assert result == []

    def test_unknown_keys_ignored(self):
        data = {"unknown_key": "value", "skill_id": "qa.test-plan"}
        result = validate_enums(data, "test")
        assert result == []


class TestEnumGuardError:
    def test_is_value_error_subclass(self):
        assert issubclass(EnumGuardError, ValueError)

    def test_error_from_check_field(self):
        """EnumGuardError raised by check_field includes field name, value, and allowed list."""
        with pytest.raises(EnumGuardError) as exc_info:
            check_field("skill_id", "bad_value", "test")
        msg = str(exc_info.value)
        assert "skill_id" in msg
        assert "bad_value" in msg
        assert "qa.test-plan" in msg


class TestEnumGuardViolation:
    def test_violation_str_enum_03_format(self):
        """Error message format must include field name, allowed values, and invalid value."""
        v = EnumGuardViolation(
            field="skill_id",
            value="bad_value",
            allowed=["qa.test-plan", "qa.test-run"],
            label="test",
        )
        msg = str(v)
        assert "skill_id must be one of" in msg
        assert "qa.test-plan" in msg
        assert "qa.test-run" in msg
        assert "bad_value" in msg

    def test_violation_is_frozen(self):
        v = EnumGuardViolation(
            field="phase",
            value="5",
            allowed=["1a", "1b", "2", "3", "4"],
            label="test",
        )
        with pytest.raises(Exception):
            v.field = "changed"


class TestRegistry:
    def test_enum_registry_has_all_6_fields(self):
        # Base 6 fields + 2 aliases (verdict, failure_classification) for SRC-009
        assert len(ENUM_REGISTRY) >= 6
        assert "skill_id" in ENUM_REGISTRY
        assert "module_id" in ENUM_REGISTRY
        assert "assertion_layer" in ENUM_REGISTRY
        assert "failure_class" in ENUM_REGISTRY
        assert "gate_verdict" in ENUM_REGISTRY
        assert "phase" in ENUM_REGISTRY
        # Aliases for SRC-009 compatibility
        assert "verdict" in ENUM_REGISTRY
        assert "failure_classification" in ENUM_REGISTRY

    def test_enum_registry_maps_correct_types(self):
        assert ENUM_REGISTRY["skill_id"] is SkillId
        assert ENUM_REGISTRY["module_id"] is ModuleId
        assert ENUM_REGISTRY["assertion_layer"] is AssertionLayer
        assert ENUM_REGISTRY["failure_class"] is FailureClass
        assert ENUM_REGISTRY["gate_verdict"] is GateVerdict
        assert ENUM_REGISTRY["phase"] is PhaseId
        # Aliases
        assert ENUM_REGISTRY["verdict"] is GateVerdict
        assert ENUM_REGISTRY["failure_classification"] is FailureClass

    def test_forbidden_semantics_has_all_6_fields(self):
        # Base 6 + 2 aliases for SRC-009 compatibility
        assert len(FORBIDDEN_SEMANTICS) >= 6
        for field in ENUM_REGISTRY:
            assert field in FORBIDDEN_SEMANTICS, f"Missing forbidden_semantics for {field}"


class TestCheckField:
    def test_valid_value_does_not_raise(self):
        check_field("skill_id", "qa.test-plan", "test")

    def test_invalid_value_raises_enum_guard_error(self):
        with pytest.raises(EnumGuardError, match="skill_id"):
            check_field("skill_id", "bad_value", "test")

    def test_check_field_error_message_complies_enum_03(self):
        """Error message must include field name, invalid value, and allowed values list."""
        with pytest.raises(EnumGuardError) as exc_info:
            check_field("skill_id", "bad_value", "test")
        msg = str(exc_info.value)
        assert "skill_id" in msg
        assert "bad_value" in msg
        assert "qa.test-plan" in msg
