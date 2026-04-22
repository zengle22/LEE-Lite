"""Governance object validator — field contracts for all 11 SRC-009 objects.

Truth source: SRC-009 (adr-052-ssot-semantic-governance-upgrade.md)
Decisions: D-01 Single file, D-02 Collect-all violations, D-03 Frozen dataclass,
D-04 --object CLI flag, D-05 enum_guard integration, D-06 Consistent error format,
D-07 All violations before raising.

Objects: Skill, Module, AssertionLayer, FailureClass, GoldenPath, Gate,
StateMachine, RunManifest, Environment, Accident, Verifier
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from cli.lib.enum_guard import ENUM_REGISTRY, validate_enums


# ---------------------------------------------------------------------------
# Error class
# ---------------------------------------------------------------------------


class GovernanceValidatorError(ValueError):
    """Raised after collecting ALL violations."""


# ---------------------------------------------------------------------------
# Violation dataclass
# ---------------------------------------------------------------------------


class ViolationType(str, Enum):
    REQUIRED_MISSING = "required_missing"
    FORBIDDEN_FIELD = "forbidden_field"
    EXTRA_FIELD = "extra_field"


@dataclass(frozen=True)
class GovernanceViolation:
    """Structured violation of a governance field contract."""

    field: str
    value: str | None
    expected: str
    label: str
    violation_type: ViolationType

    def __str__(self) -> str:
        type_map = {
            ViolationType.REQUIRED_MISSING: "required",
            ViolationType.FORBIDDEN_FIELD: "forbidden",
            ViolationType.EXTRA_FIELD: "extra",
        }
        return (
            f"{self.label}: field '{self.field}' is {type_map[self.violation_type]}"
        )


# ---------------------------------------------------------------------------
# Base helper functions (collect-all pattern, D-02)
# ---------------------------------------------------------------------------


def _require(
    data: dict[str, Any], required_fields: frozenset[str], label: str
) -> list[GovernanceViolation]:
    """Return violations for missing required fields."""
    violations: list[GovernanceViolation] = []
    for field in required_fields:
        if field not in data or data[field] is None:
            violations.append(
                GovernanceViolation(
                    field=field,
                    value=None,
                    expected="required field",
                    label=label,
                    violation_type=ViolationType.REQUIRED_MISSING,
                )
            )
    return violations


def _forbidden(
    data: dict[str, Any],
    forbidden_fields: frozenset[str],
    label: str,
) -> list[GovernanceViolation]:
    """Return violations for present forbidden fields."""
    violations: list[GovernanceViolation] = []
    for field in forbidden_fields:
        if field in data and data[field] is not None:
            violations.append(
                GovernanceViolation(
                    field=field,
                    value=str(data[field]),
                    expected="forbidden field",
                    label=label,
                    violation_type=ViolationType.FORBIDDEN_FIELD,
                )
            )
    return violations


def _extra_field(
    data: dict[str, Any],
    allowed_fields: frozenset[str],
    label: str,
) -> list[GovernanceViolation]:
    """Return violations for extra fields not in required+optional."""
    violations: list[GovernanceViolation] = []
    for field in data:
        if field not in allowed_fields and field not in (
            "artifact_type",
            "gate_id",
            "feature_id",
            "evaluated_at",
            "reason",
            "notes",
        ):
            violations.append(
                GovernanceViolation(
                    field=field,
                    value=str(data[field]),
                    expected=f"one of {sorted(allowed_fields)}",
                    label=label,
                    violation_type=ViolationType.EXTRA_FIELD,
                )
            )
    return violations


# ---------------------------------------------------------------------------
# Validator classes (D-03: frozen dataclass pattern)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SkillValidator:
    """Validate Skill governance object."""

    required_fields: frozenset[str] = frozenset(
        {"skill_id", "purpose", "orchestrates"}
    )
    optional_fields: frozenset[str] = frozenset({"modes", "interaction_options"})
    forbidden_fields: frozenset[str] = frozenset(
        {"internal_module_registration", "direct_implementation"}
    )
    enum_fields: frozenset[str] = frozenset({"skill_id"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


@dataclass(frozen=True)
class ModuleValidator:
    """Validate Module governance object."""

    required_fields: frozenset[str] = frozenset(
        {"module_id", "axis", "input", "output"}
    )
    optional_fields: frozenset[str] = frozenset(
        {"phase", "priority", "states", "code_location"}
    )
    forbidden_fields: frozenset[str] = frozenset({"skill_registration"})
    enum_fields: frozenset[str] = frozenset({"module_id"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


@dataclass(frozen=True)
class AssertionLayerValidator:
    """Validate AssertionLayer governance object."""

    required_fields: frozenset[str] = frozenset(
        {"layer_id", "name", "description", "verification_method"}
    )
    optional_fields: frozenset[str] = frozenset(
        {"phase_requirement", "verification_path"}
    )
    forbidden_fields: frozenset[str] = frozenset({"optional_for_golden_paths"})
    enum_fields: frozenset[str] = frozenset({"assertion_layer"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


@dataclass(frozen=True)
class FailureClassValidator:
    """Validate FailureClass governance object."""

    required_fields: frozenset[str] = frozenset(
        {"class_id", "name", "description", "common_manifestations"}
    )
    optional_fields: frozenset[str] = frozenset(
        {"post_classification_action", "confidence_threshold"}
    )
    forbidden_fields: frozenset[str] = frozenset({"ad_hoc_classification"})
    enum_fields: frozenset[str] = frozenset({"failure_class"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


@dataclass(frozen=True)
class GoldenPathValidator:
    """Validate GoldenPath governance object."""

    required_fields: frozenset[str] = frozenset(
        {"path_id", "priority", "description", "dependencies"}
    )
    optional_fields: frozenset[str] = frozenset(
        {"acceptance_criteria", "evidence_template"}
    )
    forbidden_fields: frozenset[str] = frozenset(
        {"undefined_environment", "undefined_data"}
    )
    enum_fields: frozenset[str] = frozenset()  # No enum fields

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        return violations


@dataclass(frozen=True)
class GateValidator:
    """Validate Gate governance object."""

    required_fields: frozenset[str] = frozenset(
        {
            "verdict",
            "case_pass_rate",
            "assertion_coverage",
            "bypass_violations",
            "verifier_verdict",
            "product_bugs",
            "env_consistency",
        }
    )
    optional_fields: frozenset[str] = frozenset({"phase", "provisional_notice"})
    forbidden_fields: frozenset[str] = frozenset({"hidden_verifier_failure"})
    enum_fields: frozenset[str] = frozenset({"verdict"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


@dataclass(frozen=True)
class StateMachineValidator:
    """Validate StateMachine governance object."""

    required_fields: frozenset[str] = frozenset(
        {"states", "transitions", "on_fail_behavior"}
    )
    optional_fields: frozenset[str] = frozenset({"skip_states", "phase_variant"})
    forbidden_fields: frozenset[str] = frozenset({"free_form_execution"})
    enum_fields: frozenset[str] = frozenset({"phase"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


@dataclass(frozen=True)
class RunManifestValidator:
    """Validate RunManifest governance object."""

    required_fields: frozenset[str] = frozenset(
        {"run_id", "app_commit", "base_url", "browser", "generated_at"}
    )
    optional_fields: frozenset[str] = frozenset(
        {
            "frontend_build",
            "backend_version",
            "feature_flags",
            "test_data_snapshot",
            "accounts",
        }
    )
    forbidden_fields: frozenset[str] = frozenset({"mutable_after_creation"})
    enum_fields: frozenset[str] = frozenset()  # No enum fields

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        return violations


@dataclass(frozen=True)
class EnvironmentValidator:
    """Validate Environment governance object."""

    required_fields: frozenset[str] = frozenset(
        {"base_url", "browser", "timeout", "headless"}
    )
    optional_fields: frozenset[str] = frozenset(
        {"account_runner", "account_verifier", "managed", "version"}
    )
    forbidden_fields: frozenset[str] = frozenset({"embedded_in_testset"})
    enum_fields: frozenset[str] = frozenset()  # No enum fields

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        return violations


@dataclass(frozen=True)
class AccidentValidator:
    """Validate Accident governance object."""

    required_fields: frozenset[str] = frozenset(
        {
            "case_id",
            "manifest",
            "screenshots",
            "traces",
            "network_log",
            "console_log",
            "failure_classification",
        }
    )
    optional_fields: frozenset[str] = frozenset(
        {"videos", "storage_state", "dom_snapshot", "entity_snapshot"}
    )
    forbidden_fields: frozenset[str] = frozenset({"ad_hoc_format"})
    enum_fields: frozenset[str] = frozenset({"failure_classification"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


@dataclass(frozen=True)
class VerifierValidator:
    """Validate Verifier governance object."""

    required_fields: frozenset[str] = frozenset(
        {"verdict", "confidence", "c_layer_verdict", "detail"}
    )
    optional_fields: frozenset[str] = frozenset({"query_path", "account_isolation"})
    forbidden_fields: frozenset[str] = frozenset({"shared_context_with_runner"})
    enum_fields: frozenset[str] = frozenset({"verdict"})

    @classmethod
    def validate(
        cls, data: dict[str, Any], label: str
    ) -> list[GovernanceViolation]:
        violations: list[GovernanceViolation] = []
        allowed = cls.required_fields | cls.optional_fields

        violations.extend(_require(data, cls.required_fields, label))
        violations.extend(_forbidden(data, cls.forbidden_fields, label))
        violations.extend(_extra_field(data, allowed, label))

        if cls.enum_fields:
            enum_violations = validate_enums(data, label)
            violations.extend(enum_violations)

        return violations


# ---------------------------------------------------------------------------
# Validators map (D-01: single registry)
# ---------------------------------------------------------------------------

VALIDATORS: dict[str, type] = {
    "skill": SkillValidator,
    "module": ModuleValidator,
    "assertion_layer": AssertionLayerValidator,
    "failure_class": FailureClassValidator,
    "golden_path": GoldenPathValidator,
    "gate": GateValidator,
    "state_machine": StateMachineValidator,
    "run_manifest": RunManifestValidator,
    "environment": EnvironmentValidator,
    "accident": AccidentValidator,
    "verifier": VerifierValidator,
}

OBJECT_TOP_KEYS: dict[str, str] = {
    "skill": "skill",
    "module": "module",
    "assertion_layer": "assertion_layer",
    "failure_class": "failure_class",
    "golden_path": "golden_path",
    "gate": "gate",
    "state_machine": "state_machine",
    "run_manifest": "run_manifest",
    "environment": "environment",
    "accident": "accident",
    "verifier": "verifier",
}


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------


def validate(
    data: dict[str, Any], object_type: str, label: str | None = None
) -> list[GovernanceViolation]:
    """Validate governance object data and return all violations.

    Args:
        data: Raw YAML dict (with or without top-level key).
        object_type: One of VALIDATORS keys.
        label: Human-readable label for error messages (defaults to object_type).

    Returns:
        List of all violations (collect-all, not fail-fast).
    """
    if label is None:
        label = object_type

    validator_cls = VALIDATORS.get(object_type)
    if validator_cls is None:
        return [
            GovernanceViolation(
                field="object_type",
                value=object_type,
                expected=f"one of {sorted(VALIDATORS.keys())}",
                label=label,
                violation_type=ViolationType.REQUIRED_MISSING,
            )
        ]

    inner = data
    top_key = OBJECT_TOP_KEYS.get(object_type, object_type)
    if top_key in data:
        inner = data[top_key]

    return validator_cls.validate(inner, label)


def validate_file(
    path: str | Path, object_type: str | None = None
) -> list[GovernanceViolation]:
    """Load a YAML file and validate it as a governance object.

    Args:
        path: Path to the YAML file.
        object_type: Object type or None for auto-detect from top-level key.

    Returns:
        List of all violations.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Auto-detect if object_type not provided
    if object_type is None:
        for obj_type, top_key in OBJECT_TOP_KEYS.items():
            if top_key in data:
                object_type = obj_type
                break
        if object_type is None:
            return [
                GovernanceViolation(
                    field="top_level_key",
                    value="none",
                    expected=f"one of {sorted(OBJECT_TOP_KEYS.values())}",
                    label="file",
                    violation_type=ViolationType.REQUIRED_MISSING,
                )
            ]

    return validate(data, object_type)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI for governance object validation.

    Usage:
        python -m cli.lib.governance_validator --object <type> <file.yaml>
        python -m cli.lib.governance_validator --object skill --check '{"skill_id": "qa.test-plan", ...}'
        python -m cli.lib.governance_validator --list-types
    """
    args = sys.argv[1:]
    if not args:
        print(
            "Usage: python -m cli.lib.governance_validator [--object <type>] "
            "[--check '<json>'] [--list-types] <file>"
        )
        print(f"  Valid types: {sorted(VALIDATORS.keys())}")
        sys.exit(1)

    if "--list-types" in args:
        print("Valid governance object types:")
        for obj_type in sorted(VALIDATORS.keys()):
            print(f"  - {obj_type}")
        sys.exit(0)

    object_type: str | None = None
    file_path: str | None = None
    check_json: dict[str, Any] | None = None

    if "--object" in args:
        idx = args.index("--object")
        object_type = args[idx + 1] if idx + 1 < len(args) else None
        if object_type is None:
            print("Error: --object requires a value", file=sys.stderr)
            sys.exit(1)

    if "--check" in args:
        idx = args.index("--check")
        raw = args[idx + 1] if idx + 1 < len(args) else "{}"
        check_json = json.loads(raw)
        if object_type is None:
            print("Error: --object required with --check", file=sys.stderr)
            sys.exit(1)
        violations = validate(check_json, object_type, label="cli")
        if violations:
            for v in violations:
                print(f"FAIL: {v}")
            sys.exit(1)
        else:
            print("OK: all fields valid")
        sys.exit(0)

    # File validation
    for arg in args:
        if not arg.startswith("--") and Path(arg).exists():
            file_path = arg
            break

    if file_path is None:
        print("Error: no file specified", file=sys.stderr)
        sys.exit(1)

    if object_type is None:
        print("Error: --object required for file validation", file=sys.stderr)
        sys.exit(1)

    violations = validate_file(file_path, object_type)
    if violations:
        for v in violations:
            print(f"FAIL: {v}")
        sys.exit(1)
    else:
        print(f"OK: {file_path} is valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
