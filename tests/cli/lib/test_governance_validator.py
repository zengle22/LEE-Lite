"""Comprehensive tests for governance_validator — all 11 SRC-009 objects.

Truth source: SRC-009 governance field contracts.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from cli.lib.governance_validator import (
    OBJECT_TOP_KEYS,
    VALIDATORS,
    GovernanceViolation,
    GovernanceValidatorError,
    ViolationType,
    validate,
    validate_file,
)


# ---------------------------------------------------------------------------
# TestGovernanceViolation — structure and types
# ---------------------------------------------------------------------------


class TestGovernanceViolation:
    """Test GovernanceViolation dataclass structure."""

    def test_violation_str_format_includes_label_field_type(self):
        """Violation __str__ includes label, field, and violation type."""
        v = GovernanceViolation(
            field="skill_id",
            value=None,
            expected="required field",
            label="my-skill",
            violation_type=ViolationType.REQUIRED_MISSING,
        )
        s = str(v)
        assert "my-skill" in s
        assert "skill_id" in s
        assert "required" in s

    def test_violation_is_frozen(self):
        """GovernanceViolation is a frozen dataclass."""
        v = GovernanceViolation(
            field="x",
            value="y",
            expected="z",
            label="t",
            violation_type=ViolationType.EXTRA_FIELD,
        )
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            v.field = "changed"  # type: ignore

    def test_violation_types_required_missing(self):
        """ViolationType.REQUIRED_MISSING is defined."""
        assert ViolationType.REQUIRED_MISSING.value == "required_missing"

    def test_violation_types_forbidden_field(self):
        """ViolationType.FORBIDDEN_FIELD is defined."""
        assert ViolationType.FORBIDDEN_FIELD.value == "forbidden_field"

    def test_violation_types_extra_field(self):
        """ViolationType.EXTRA_FIELD is defined."""
        assert ViolationType.EXTRA_FIELD.value == "extra_field"


# ---------------------------------------------------------------------------
# TestSkillValidator
# ---------------------------------------------------------------------------


class TestSkillValidator:
    """Test Skill governance object validation."""

    @pytest.fixture
    def valid_skill(self):
        return {
            "skill_id": "qa.test-plan",
            "purpose": "Plan test execution",
            "orchestrates": ["qa.test-run"],
        }

    def test_valid_skill_passes(self, valid_skill):
        """Valid Skill with all required fields passes."""
        from cli.lib.governance_validator import SkillValidator

        violations = SkillValidator.validate(valid_skill, "skill-test")
        assert violations == []

    def test_missing_required_field_skill_id(self, valid_skill):
        """Missing skill_id triggers violation."""
        from cli.lib.governance_validator import SkillValidator

        del valid_skill["skill_id"]
        violations = SkillValidator.validate(valid_skill, "skill-test")
        assert any(
            v.field == "skill_id" and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_purpose(self, valid_skill):
        """Missing purpose triggers violation."""
        from cli.lib.governance_validator import SkillValidator

        del valid_skill["purpose"]
        violations = SkillValidator.validate(valid_skill, "skill-test")
        assert any(
            v.field == "purpose"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_orchestrates(self, valid_skill):
        """Missing orchestrates triggers violation."""
        from cli.lib.governance_validator import SkillValidator

        del valid_skill["orchestrates"]
        violations = SkillValidator.validate(valid_skill, "skill-test")
        assert any(
            v.field == "orchestrates"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_internal_module_registration(self, valid_skill):
        """Forbidden field internal_module_registration triggers violation."""
        from cli.lib.governance_validator import SkillValidator

        valid_skill["internal_module_registration"] = True
        violations = SkillValidator.validate(valid_skill, "skill-test")
        assert any(
            v.field == "internal_module_registration"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_forbidden_field_direct_implementation(self, valid_skill):
        """Forbidden field direct_implementation triggers violation."""
        from cli.lib.governance_validator import SkillValidator

        valid_skill["direct_implementation"] = True
        violations = SkillValidator.validate(valid_skill, "skill-test")
        assert any(
            v.field == "direct_implementation"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_extra_field_triggers_error(self, valid_skill):
        """Extra field not in required|optional triggers violation."""
        from cli.lib.governance_validator import SkillValidator

        valid_skill["unknown_field"] = "value"
        violations = SkillValidator.validate(valid_skill, "skill-test")
        assert any(
            v.field == "unknown_field"
            and v.violation_type == ViolationType.EXTRA_FIELD
            for v in violations
        )

    def test_skill_id_enum_validated_via_enum_guard(self, valid_skill):
        """Invalid skill_id value triggers enum violation via enum_guard."""
        from cli.lib.governance_validator import SkillValidator

        valid_skill["skill_id"] = "invalid.skill.id"
        violations = SkillValidator.validate(valid_skill, "skill-test")
        # enum_guard should catch invalid skill_id
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestModuleValidator
# ---------------------------------------------------------------------------


class TestModuleValidator:
    """Test Module governance object validation."""

    @pytest.fixture
    def valid_module(self):
        return {
            "module_id": "feat-to-testset",
            "axis": "test-generation",
            "input": "feature.yaml",
            "output": "testset.yaml",
        }

    def test_valid_module_passes(self, valid_module):
        """Valid Module with all required fields passes."""
        from cli.lib.governance_validator import ModuleValidator

        violations = ModuleValidator.validate(valid_module, "module-test")
        assert violations == []

    def test_missing_required_field_module_id(self, valid_module):
        """Missing module_id triggers violation."""
        from cli.lib.governance_validator import ModuleValidator

        del valid_module["module_id"]
        violations = ModuleValidator.validate(valid_module, "module-test")
        assert any(
            v.field == "module_id"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_axis(self, valid_module):
        """Missing axis triggers violation."""
        from cli.lib.governance_validator import ModuleValidator

        del valid_module["axis"]
        violations = ModuleValidator.validate(valid_module, "module-test")
        assert any(
            v.field == "axis"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_input(self, valid_module):
        """Missing input triggers violation."""
        from cli.lib.governance_validator import ModuleValidator

        del valid_module["input"]
        violations = ModuleValidator.validate(valid_module, "module-test")
        assert any(
            v.field == "input"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_output(self, valid_module):
        """Missing output triggers violation."""
        from cli.lib.governance_validator import ModuleValidator

        del valid_module["output"]
        violations = ModuleValidator.validate(valid_module, "module-test")
        assert any(
            v.field == "output"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_present_skill_registration(self, valid_module):
        """Forbidden field skill_registration triggers violation."""
        from cli.lib.governance_validator import ModuleValidator

        valid_module["skill_registration"] = True
        violations = ModuleValidator.validate(valid_module, "module-test")
        assert any(
            v.field == "skill_registration"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_module_id_enum_validated(self, valid_module):
        """Invalid module_id value triggers enum violation."""
        from cli.lib.governance_validator import ModuleValidator

        valid_module["module_id"] = "invalid-module"
        violations = ModuleValidator.validate(valid_module, "module-test")
        # enum_guard should catch invalid module_id
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestAssertionLayerValidator
# ---------------------------------------------------------------------------


class TestAssertionLayerValidator:
    """Test AssertionLayer governance object validation."""

    @pytest.fixture
    def valid_assertion_layer(self):
        return {
            "layer_id": "A",
            "name": "Interface Layer",
            "description": "Validates interface contracts",
            "verification_method": "schema-validation",
        }

    def test_valid_assertion_layer_passes(self, valid_assertion_layer):
        """Valid AssertionLayer with all required fields passes."""
        from cli.lib.governance_validator import AssertionLayerValidator

        violations = AssertionLayerValidator.validate(
            valid_assertion_layer, "layer-test"
        )
        assert violations == []

    def test_missing_required_field_layer_id(self, valid_assertion_layer):
        """Missing layer_id triggers violation."""
        from cli.lib.governance_validator import AssertionLayerValidator

        del valid_assertion_layer["layer_id"]
        violations = AssertionLayerValidator.validate(
            valid_assertion_layer, "layer-test"
        )
        assert any(
            v.field == "layer_id"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_name(self, valid_assertion_layer):
        """Missing name triggers violation."""
        from cli.lib.governance_validator import AssertionLayerValidator

        del valid_assertion_layer["name"]
        violations = AssertionLayerValidator.validate(
            valid_assertion_layer, "layer-test"
        )
        assert any(
            v.field == "name"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_description(self, valid_assertion_layer):
        """Missing description triggers violation."""
        from cli.lib.governance_validator import AssertionLayerValidator

        del valid_assertion_layer["description"]
        violations = AssertionLayerValidator.validate(
            valid_assertion_layer, "layer-test"
        )
        assert any(
            v.field == "description"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_verification_method(
        self, valid_assertion_layer
    ):
        """Missing verification_method triggers violation."""
        from cli.lib.governance_validator import AssertionLayerValidator

        del valid_assertion_layer["verification_method"]
        violations = AssertionLayerValidator.validate(
            valid_assertion_layer, "layer-test"
        )
        assert any(
            v.field == "verification_method"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_optional_for_golden_paths(self, valid_assertion_layer):
        """Forbidden field optional_for_golden_paths triggers violation."""
        from cli.lib.governance_validator import AssertionLayerValidator

        valid_assertion_layer["optional_for_golden_paths"] = True
        violations = AssertionLayerValidator.validate(
            valid_assertion_layer, "layer-test"
        )
        assert any(
            v.field == "optional_for_golden_paths"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_assertion_layer_enum_validated(self, valid_assertion_layer):
        """assertion_layer enum field validated via enum_guard."""
        from cli.lib.governance_validator import AssertionLayerValidator

        valid_assertion_layer["assertion_layer"] = "X"  # Invalid - only A, B, C
        violations = AssertionLayerValidator.validate(
            valid_assertion_layer, "layer-test"
        )
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestFailureClassValidator
# ---------------------------------------------------------------------------


class TestFailureClassValidator:
    """Test FailureClass governance object validation."""

    @pytest.fixture
    def valid_failure_class(self):
        return {
            "class_id": "ENV",
            "name": "Environment Failure",
            "description": "Failure due to environment issues",
            "common_manifestations": ["timeout", "connection-refused"],
        }

    def test_valid_failure_class_passes(self, valid_failure_class):
        """Valid FailureClass with all required fields passes."""
        from cli.lib.governance_validator import FailureClassValidator

        violations = FailureClassValidator.validate(
            valid_failure_class, "fc-test"
        )
        assert violations == []

    def test_missing_required_field_class_id(self, valid_failure_class):
        """Missing class_id triggers violation."""
        from cli.lib.governance_validator import FailureClassValidator

        del valid_failure_class["class_id"]
        violations = FailureClassValidator.validate(
            valid_failure_class, "fc-test"
        )
        assert any(
            v.field == "class_id"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_name(self, valid_failure_class):
        """Missing name triggers violation."""
        from cli.lib.governance_validator import FailureClassValidator

        del valid_failure_class["name"]
        violations = FailureClassValidator.validate(
            valid_failure_class, "fc-test"
        )
        assert any(
            v.field == "name"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_description(self, valid_failure_class):
        """Missing description triggers violation."""
        from cli.lib.governance_validator import FailureClassValidator

        del valid_failure_class["description"]
        violations = FailureClassValidator.validate(
            valid_failure_class, "fc-test"
        )
        assert any(
            v.field == "description"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_common_manifestations(self, valid_failure_class):
        """Missing common_manifestations triggers violation."""
        from cli.lib.governance_validator import FailureClassValidator

        del valid_failure_class["common_manifestations"]
        violations = FailureClassValidator.validate(
            valid_failure_class, "fc-test"
        )
        assert any(
            v.field == "common_manifestations"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_ad_hoc_classification(self, valid_failure_class):
        """Forbidden field ad_hoc_classification triggers violation."""
        from cli.lib.governance_validator import FailureClassValidator

        valid_failure_class["ad_hoc_classification"] = True
        violations = FailureClassValidator.validate(
            valid_failure_class, "fc-test"
        )
        assert any(
            v.field == "ad_hoc_classification"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_failure_class_enum_validated(self, valid_failure_class):
        """failure_class enum field validated via enum_guard."""
        from cli.lib.governance_validator import FailureClassValidator

        valid_failure_class["failure_class"] = "INVALID"  # Invalid enum
        violations = FailureClassValidator.validate(
            valid_failure_class, "fc-test"
        )
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestGoldenPathValidator
# ---------------------------------------------------------------------------


class TestGoldenPathValidator:
    """Test GoldenPath governance object validation."""

    @pytest.fixture
    def valid_golden_path(self):
        return {
            "path_id": "happy-path-001",
            "priority": 1,
            "description": "Standard happy path flow",
            "dependencies": [],
        }

    def test_valid_golden_path_passes(self, valid_golden_path):
        """Valid GoldenPath with all required fields passes."""
        from cli.lib.governance_validator import GoldenPathValidator

        violations = GoldenPathValidator.validate(valid_golden_path, "gp-test")
        assert violations == []

    def test_missing_required_field_path_id(self, valid_golden_path):
        """Missing path_id triggers violation."""
        from cli.lib.governance_validator import GoldenPathValidator

        del valid_golden_path["path_id"]
        violations = GoldenPathValidator.validate(valid_golden_path, "gp-test")
        assert any(
            v.field == "path_id"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_priority(self, valid_golden_path):
        """Missing priority triggers violation."""
        from cli.lib.governance_validator import GoldenPathValidator

        del valid_golden_path["priority"]
        violations = GoldenPathValidator.validate(valid_golden_path, "gp-test")
        assert any(
            v.field == "priority"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_description(self, valid_golden_path):
        """Missing description triggers violation."""
        from cli.lib.governance_validator import GoldenPathValidator

        del valid_golden_path["description"]
        violations = GoldenPathValidator.validate(valid_golden_path, "gp-test")
        assert any(
            v.field == "description"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_dependencies(self, valid_golden_path):
        """Missing dependencies triggers violation."""
        from cli.lib.governance_validator import GoldenPathValidator

        del valid_golden_path["dependencies"]
        violations = GoldenPathValidator.validate(valid_golden_path, "gp-test")
        assert any(
            v.field == "dependencies"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_undefined_environment(self, valid_golden_path):
        """Forbidden field undefined_environment triggers violation."""
        from cli.lib.governance_validator import GoldenPathValidator

        valid_golden_path["undefined_environment"] = True
        violations = GoldenPathValidator.validate(valid_golden_path, "gp-test")
        assert any(
            v.field == "undefined_environment"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_forbidden_field_undefined_data(self, valid_golden_path):
        """Forbidden field undefined_data triggers violation."""
        from cli.lib.governance_validator import GoldenPathValidator

        valid_golden_path["undefined_data"] = True
        violations = GoldenPathValidator.validate(valid_golden_path, "gp-test")
        assert any(
            v.field == "undefined_data"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_no_enum_fields(self, valid_golden_path):
        """GoldenPath has no enum field validations."""
        from cli.lib.governance_validator import GoldenPathValidator

        assert GoldenPathValidator.enum_fields == frozenset()


# ---------------------------------------------------------------------------
# TestGateValidator
# ---------------------------------------------------------------------------


class TestGateValidator:
    """Test Gate governance object validation."""

    @pytest.fixture
    def valid_gate(self):
        return {
            "verdict": "pass",
            "case_pass_rate": 0.95,
            "assertion_coverage": 0.85,
            "bypass_violations": 0,
            "verifier_verdict": "pass",
            "product_bugs": 0,
            "env_consistency": "consistent",
        }

    def test_valid_gate_passes(self, valid_gate):
        """Valid Gate with all required fields passes."""
        from cli.lib.governance_validator import GateValidator

        violations = GateValidator.validate(valid_gate, "gate-test")
        assert violations == []

    def test_missing_required_field_verdict(self, valid_gate):
        """Missing verdict triggers violation."""
        from cli.lib.governance_validator import GateValidator

        del valid_gate["verdict"]
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "verdict"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_case_pass_rate(self, valid_gate):
        """Missing case_pass_rate triggers violation."""
        from cli.lib.governance_validator import GateValidator

        del valid_gate["case_pass_rate"]
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "case_pass_rate"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_assertion_coverage(self, valid_gate):
        """Missing assertion_coverage triggers violation."""
        from cli.lib.governance_validator import GateValidator

        del valid_gate["assertion_coverage"]
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "assertion_coverage"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_bypass_violations(self, valid_gate):
        """Missing bypass_violations triggers violation."""
        from cli.lib.governance_validator import GateValidator

        del valid_gate["bypass_violations"]
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "bypass_violations"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_verifier_verdict(self, valid_gate):
        """Missing verifier_verdict triggers violation."""
        from cli.lib.governance_validator import GateValidator

        del valid_gate["verifier_verdict"]
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "verifier_verdict"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_product_bugs(self, valid_gate):
        """Missing product_bugs triggers violation."""
        from cli.lib.governance_validator import GateValidator

        del valid_gate["product_bugs"]
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "product_bugs"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_env_consistency(self, valid_gate):
        """Missing env_consistency triggers violation."""
        from cli.lib.governance_validator import GateValidator

        del valid_gate["env_consistency"]
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "env_consistency"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_hidden_verifier_failure(self, valid_gate):
        """Forbidden field hidden_verifier_failure triggers violation."""
        from cli.lib.governance_validator import GateValidator

        valid_gate["hidden_verifier_failure"] = True
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "hidden_verifier_failure"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_gate_verdict_enum_validated(self, valid_gate):
        """Gate verdict enum validated via enum_guard."""
        from cli.lib.governance_validator import GateValidator

        valid_gate["verdict"] = "invalid-verdict"
        violations = GateValidator.validate(valid_gate, "gate-test")
        # enum_guard should catch invalid verdict
        assert len(violations) > 0

    def test_extra_field_triggers_error(self, valid_gate):
        """Extra field not in required|optional triggers violation."""
        from cli.lib.governance_validator import GateValidator

        valid_gate["unknown_field"] = "value"
        violations = GateValidator.validate(valid_gate, "gate-test")
        assert any(
            v.field == "unknown_field"
            and v.violation_type == ViolationType.EXTRA_FIELD
            for v in violations
        )


# ---------------------------------------------------------------------------
# TestStateMachineValidator
# ---------------------------------------------------------------------------


class TestStateMachineValidator:
    """Test StateMachine governance object validation."""

    @pytest.fixture
    def valid_state_machine(self):
        return {
            "states": ["idle", "running", "done"],
            "transitions": {"idle": "running", "running": "done"},
            "on_fail_behavior": "retry-3",
        }

    def test_valid_state_machine_passes(self, valid_state_machine):
        """Valid StateMachine with all required fields passes."""
        from cli.lib.governance_validator import StateMachineValidator

        violations = StateMachineValidator.validate(valid_state_machine, "sm-test")
        assert violations == []

    def test_missing_required_field_states(self, valid_state_machine):
        """Missing states triggers violation."""
        from cli.lib.governance_validator import StateMachineValidator

        del valid_state_machine["states"]
        violations = StateMachineValidator.validate(valid_state_machine, "sm-test")
        assert any(
            v.field == "states"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_transitions(self, valid_state_machine):
        """Missing transitions triggers violation."""
        from cli.lib.governance_validator import StateMachineValidator

        del valid_state_machine["transitions"]
        violations = StateMachineValidator.validate(valid_state_machine, "sm-test")
        assert any(
            v.field == "transitions"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_on_fail_behavior(self, valid_state_machine):
        """Missing on_fail_behavior triggers violation."""
        from cli.lib.governance_validator import StateMachineValidator

        del valid_state_machine["on_fail_behavior"]
        violations = StateMachineValidator.validate(valid_state_machine, "sm-test")
        assert any(
            v.field == "on_fail_behavior"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_free_form_execution(self, valid_state_machine):
        """Forbidden field free_form_execution triggers violation."""
        from cli.lib.governance_validator import StateMachineValidator

        valid_state_machine["free_form_execution"] = True
        violations = StateMachineValidator.validate(valid_state_machine, "sm-test")
        assert any(
            v.field == "free_form_execution"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_phase_enum_validated(self, valid_state_machine):
        """StateMachine phase enum validated via enum_guard."""
        from cli.lib.governance_validator import StateMachineValidator

        valid_state_machine["phase"] = "invalid-phase"
        violations = StateMachineValidator.validate(valid_state_machine, "sm-test")
        # enum_guard should catch invalid phase
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestRunManifestValidator
# ---------------------------------------------------------------------------


class TestRunManifestValidator:
    """Test RunManifest governance object validation."""

    @pytest.fixture
    def valid_run_manifest(self):
        return {
            "run_id": "run-001",
            "app_commit": "abc123",
            "base_url": "https://example.com",
            "browser": "chromium",
            "generated_at": "2026-04-22T00:00:00Z",
        }

    def test_valid_run_manifest_passes(self, valid_run_manifest):
        """Valid RunManifest with all required fields passes."""
        from cli.lib.governance_validator import RunManifestValidator

        violations = RunManifestValidator.validate(valid_run_manifest, "rm-test")
        assert violations == []

    def test_missing_required_field_run_id(self, valid_run_manifest):
        """Missing run_id triggers violation."""
        from cli.lib.governance_validator import RunManifestValidator

        del valid_run_manifest["run_id"]
        violations = RunManifestValidator.validate(valid_run_manifest, "rm-test")
        assert any(
            v.field == "run_id"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_app_commit(self, valid_run_manifest):
        """Missing app_commit triggers violation."""
        from cli.lib.governance_validator import RunManifestValidator

        del valid_run_manifest["app_commit"]
        violations = RunManifestValidator.validate(valid_run_manifest, "rm-test")
        assert any(
            v.field == "app_commit"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_base_url(self, valid_run_manifest):
        """Missing base_url triggers violation."""
        from cli.lib.governance_validator import RunManifestValidator

        del valid_run_manifest["base_url"]
        violations = RunManifestValidator.validate(valid_run_manifest, "rm-test")
        assert any(
            v.field == "base_url"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_browser(self, valid_run_manifest):
        """Missing browser triggers violation."""
        from cli.lib.governance_validator import RunManifestValidator

        del valid_run_manifest["browser"]
        violations = RunManifestValidator.validate(valid_run_manifest, "rm-test")
        assert any(
            v.field == "browser"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_generated_at(self, valid_run_manifest):
        """Missing generated_at triggers violation."""
        from cli.lib.governance_validator import RunManifestValidator

        del valid_run_manifest["generated_at"]
        violations = RunManifestValidator.validate(valid_run_manifest, "rm-test")
        assert any(
            v.field == "generated_at"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_mutable_after_creation(self, valid_run_manifest):
        """Forbidden field mutable_after_creation triggers violation."""
        from cli.lib.governance_validator import RunManifestValidator

        valid_run_manifest["mutable_after_creation"] = True
        violations = RunManifestValidator.validate(valid_run_manifest, "rm-test")
        assert any(
            v.field == "mutable_after_creation"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_no_enum_fields(self, valid_run_manifest):
        """RunManifest has no enum field validations."""
        from cli.lib.governance_validator import RunManifestValidator

        assert RunManifestValidator.enum_fields == frozenset()


# ---------------------------------------------------------------------------
# TestEnvironmentValidator
# ---------------------------------------------------------------------------


class TestEnvironmentValidator:
    """Test Environment governance object validation."""

    @pytest.fixture
    def valid_environment(self):
        return {
            "base_url": "https://example.com",
            "browser": "chromium",
            "timeout": 30,
            "headless": True,
        }

    def test_valid_environment_passes(self, valid_environment):
        """Valid Environment with all required fields passes."""
        from cli.lib.governance_validator import EnvironmentValidator

        violations = EnvironmentValidator.validate(valid_environment, "env-test")
        assert violations == []

    def test_missing_required_field_base_url(self, valid_environment):
        """Missing base_url triggers violation."""
        from cli.lib.governance_validator import EnvironmentValidator

        del valid_environment["base_url"]
        violations = EnvironmentValidator.validate(valid_environment, "env-test")
        assert any(
            v.field == "base_url"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_browser(self, valid_environment):
        """Missing browser triggers violation."""
        from cli.lib.governance_validator import EnvironmentValidator

        del valid_environment["browser"]
        violations = EnvironmentValidator.validate(valid_environment, "env-test")
        assert any(
            v.field == "browser"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_timeout(self, valid_environment):
        """Missing timeout triggers violation."""
        from cli.lib.governance_validator import EnvironmentValidator

        del valid_environment["timeout"]
        violations = EnvironmentValidator.validate(valid_environment, "env-test")
        assert any(
            v.field == "timeout"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_headless(self, valid_environment):
        """Missing headless triggers violation."""
        from cli.lib.governance_validator import EnvironmentValidator

        del valid_environment["headless"]
        violations = EnvironmentValidator.validate(valid_environment, "env-test")
        assert any(
            v.field == "headless"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_embedded_in_testset(self, valid_environment):
        """Forbidden field embedded_in_testset triggers violation."""
        from cli.lib.governance_validator import EnvironmentValidator

        valid_environment["embedded_in_testset"] = True
        violations = EnvironmentValidator.validate(valid_environment, "env-test")
        assert any(
            v.field == "embedded_in_testset"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_no_enum_fields(self, valid_environment):
        """Environment has no enum field validations."""
        from cli.lib.governance_validator import EnvironmentValidator

        assert EnvironmentValidator.enum_fields == frozenset()


# ---------------------------------------------------------------------------
# TestAccidentValidator
# ---------------------------------------------------------------------------


class TestAccidentValidator:
    """Test Accident governance object validation."""

    @pytest.fixture
    def valid_accident(self):
        return {
            "case_id": "ACC-001",
            "manifest": "manifest.yaml",
            "screenshots": ["screenshot1.png"],
            "traces": ["trace1.txt"],
            "network_log": "network.log",
            "console_log": "console.log",
            "failure_classification": "ENV",
        }

    def test_valid_accident_passes(self, valid_accident):
        """Valid Accident with all required fields passes."""
        from cli.lib.governance_validator import AccidentValidator

        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert violations == []

    def test_missing_required_field_case_id(self, valid_accident):
        """Missing case_id triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        del valid_accident["case_id"]
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "case_id"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_manifest(self, valid_accident):
        """Missing manifest triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        del valid_accident["manifest"]
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "manifest"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_screenshots(self, valid_accident):
        """Missing screenshots triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        del valid_accident["screenshots"]
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "screenshots"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_traces(self, valid_accident):
        """Missing traces triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        del valid_accident["traces"]
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "traces"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_network_log(self, valid_accident):
        """Missing network_log triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        del valid_accident["network_log"]
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "network_log"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_console_log(self, valid_accident):
        """Missing console_log triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        del valid_accident["console_log"]
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "console_log"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_failure_classification(self, valid_accident):
        """Missing failure_classification triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        del valid_accident["failure_classification"]
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "failure_classification"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_ad_hoc_format(self, valid_accident):
        """Forbidden field ad_hoc_format triggers violation."""
        from cli.lib.governance_validator import AccidentValidator

        valid_accident["ad_hoc_format"] = True
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        assert any(
            v.field == "ad_hoc_format"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_failure_classification_enum_validated(self, valid_accident):
        """Accident failure_classification enum validated via enum_guard."""
        from cli.lib.governance_validator import AccidentValidator

        valid_accident["failure_classification"] = "INVALID"
        violations = AccidentValidator.validate(valid_accident, "acc-test")
        # enum_guard should catch invalid failure_classification
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestVerifierValidator
# ---------------------------------------------------------------------------


class TestVerifierValidator:
    """Test Verifier governance object validation."""

    @pytest.fixture
    def valid_verifier(self):
        return {
            "verdict": "pass",
            "confidence": 0.95,
            "c_layer_verdict": "pass",
            "detail": "All assertions passed",
        }

    def test_valid_verifier_passes(self, valid_verifier):
        """Valid Verifier with all required fields passes."""
        from cli.lib.governance_validator import VerifierValidator

        violations = VerifierValidator.validate(valid_verifier, "ver-test")
        assert violations == []

    def test_missing_required_field_verdict(self, valid_verifier):
        """Missing verdict triggers violation."""
        from cli.lib.governance_validator import VerifierValidator

        del valid_verifier["verdict"]
        violations = VerifierValidator.validate(valid_verifier, "ver-test")
        assert any(
            v.field == "verdict"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_confidence(self, valid_verifier):
        """Missing confidence triggers violation."""
        from cli.lib.governance_validator import VerifierValidator

        del valid_verifier["confidence"]
        violations = VerifierValidator.validate(valid_verifier, "ver-test")
        assert any(
            v.field == "confidence"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_c_layer_verdict(self, valid_verifier):
        """Missing c_layer_verdict triggers violation."""
        from cli.lib.governance_validator import VerifierValidator

        del valid_verifier["c_layer_verdict"]
        violations = VerifierValidator.validate(valid_verifier, "ver-test")
        assert any(
            v.field == "c_layer_verdict"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_missing_required_field_detail(self, valid_verifier):
        """Missing detail triggers violation."""
        from cli.lib.governance_validator import VerifierValidator

        del valid_verifier["detail"]
        violations = VerifierValidator.validate(valid_verifier, "ver-test")
        assert any(
            v.field == "detail"
            and v.violation_type == ViolationType.REQUIRED_MISSING
            for v in violations
        )

    def test_forbidden_field_shared_context_with_runner(self, valid_verifier):
        """Forbidden field shared_context_with_runner triggers violation."""
        from cli.lib.governance_validator import VerifierValidator

        valid_verifier["shared_context_with_runner"] = True
        violations = VerifierValidator.validate(valid_verifier, "ver-test")
        assert any(
            v.field == "shared_context_with_runner"
            and v.violation_type == ViolationType.FORBIDDEN_FIELD
            for v in violations
        )

    def test_verdict_enum_validated(self, valid_verifier):
        """Verifier verdict enum validated via enum_guard."""
        from cli.lib.governance_validator import VerifierValidator

        valid_verifier["verdict"] = "invalid"
        violations = VerifierValidator.validate(valid_verifier, "ver-test")
        # enum_guard should catch invalid verdict
        assert len(violations) > 0


# ---------------------------------------------------------------------------
# TestCollectAllViolations
# ---------------------------------------------------------------------------


class TestCollectAllViolations:
    """Test collect-all violation pattern."""

    def test_returns_multiple_violations_for_missing_and_forbidden(self):
        """validate() returns all violations, not fail-fast."""
        # Missing required + forbidden field should return both
        data = {
            "purpose": "Test",  # Missing skill_id and orchestrates
            "internal_module_registration": True,  # Forbidden field
        }
        violations = validate(data, "skill", "test")
        violation_types = [v.violation_type for v in violations]
        assert ViolationType.REQUIRED_MISSING in violation_types
        assert ViolationType.FORBIDDEN_FIELD in violation_types

    def test_returns_empty_list_when_valid(self):
        """validate() returns empty list for valid object."""
        data = {
            "skill_id": "qa.test-plan",
            "purpose": "Plan tests",
            "orchestrates": ["qa.test-run"],
        }
        violations = validate(data, "skill")
        assert violations == []

    def test_validate_file_with_valid_object(self, tmp_path):
        """validate_file() loads YAML and validates successfully."""
        yaml_content = """
skill:
  skill_id: qa.test-plan
  purpose: Plan tests
  orchestrates:
    - qa.test-run
"""
        test_file = tmp_path / "test_skill.yaml"
        test_file.write_text(yaml_content)

        violations = validate_file(test_file, "skill")
        assert violations == []


# ---------------------------------------------------------------------------
# TestValidatorsMap
# ---------------------------------------------------------------------------


class TestValidatorsMap:
    """Test VALIDATORS registry."""

    def test_validators_map_has_11_entries(self):
        """VALIDATORS contains all 11 governance objects."""
        assert len(VALIDATORS) == 11

    def test_all_validators_are_frozen_dataclass(self):
        """All validators are frozen dataclasses."""
        for name, validator_cls in VALIDATORS.items():
            # Check class has frozen=True
            assert hasattr(validator_cls, "__dataclass_params__")
            assert validator_cls.__dataclass_params__.frozen is True  # type: ignore

    def test_all_object_types_covered(self):
        """All 11 SRC-009 objects are covered."""
        expected_types = {
            "skill",
            "module",
            "assertion_layer",
            "failure_class",
            "golden_path",
            "gate",
            "state_machine",
            "run_manifest",
            "environment",
            "accident",
            "verifier",
        }
        assert set(VALIDATORS.keys()) == expected_types


# ---------------------------------------------------------------------------
# TestCLI
# ---------------------------------------------------------------------------


class TestCLI:
    """Test CLI entry point."""

    def test_list_types_output(self):
        """--list-types shows all 11 object types."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.lib.governance_validator", "--list-types"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        for obj_type in VALIDATORS:
            assert obj_type in result.stdout

    def test_validate_invalid_returns_fail(self):
        """Invalid object returns FAIL output and non-zero exit."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.lib.governance_validator",
                "--object",
                "skill",
                "--check",
                '{"purpose": "Test only"}',
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "FAIL" in result.stdout
