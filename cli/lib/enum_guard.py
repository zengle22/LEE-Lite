"""Centralized enum definitions and validation for 6 governance enums.

Truth sources:
- SRC-009 lines 190-224 (frozen enum values)
- ADR-052 (test governance dual-axis)

Fields: skill_id, module_id, assertion_layer, failure_class, gate_verdict, phase
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

from cli.lib.gate_schema import GateVerdict


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class EnumGuardError(ValueError):
    """Raised when a value fails enum governance validation."""


@dataclass(frozen=True)
class EnumGuardViolation:
    """Structured violation of an enum governance constraint."""

    field: str
    value: str
    allowed: list[str]
    label: str

    def __str__(self) -> str:
        return (
            f"{self.label}: {self.field} must be one of {self.allowed}, "
            f"got '{self.value}'"
        )


# ---------------------------------------------------------------------------
# Six governance enums (SRC-009 lines 190-224, frozen)
# ---------------------------------------------------------------------------


class SkillId(str, Enum):
    QA_TEST_PLAN = "qa.test-plan"
    QA_TEST_RUN = "qa.test-run"


class ModuleId(str, Enum):
    FEAT_TO_TESTSET = "feat-to-testset"
    API_PLAN_COMPILE = "api-plan-compile"
    API_MANIFEST_COMPILE = "api-manifest-compile"
    API_SPEC_COMPILE = "api-spec-compile"
    E2E_PLAN_COMPILE = "e2e-plan-compile"
    E2E_MANIFEST_COMPILE = "e2e-manifest-compile"
    E2E_SPEC_COMPILE = "e2e-spec-compile"
    ENVIRONMENT_PROVISION = "environment-provision"
    RUN_MANIFEST_GEN = "run-manifest-gen"
    SCENARIO_SPEC_COMPILE = "scenario-spec-compile"
    STATE_MACHINE_EXECUTOR = "state-machine-executor"
    BYPASS_DETECTOR = "bypass-detector"
    INDEPENDENT_VERIFIER = "independent-verifier"
    ACCIDENT_PACKAGE = "accident-package"
    FAILURE_CLASSIFIER = "failure-classifier"
    TEST_DATA_PROVISION = "test-data-provision"
    L0_SMOKE_CHECK = "l0-smoke-check"
    TEST_EXEC_WEB_E2E = "test-exec-web-e2e"
    TEST_EXEC_CLI = "test-exec-cli"
    SETTLEMENT = "settlement"
    GATE_EVALUATION = "gate-evaluation"


class AssertionLayer(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class FailureClass(str, Enum):
    ENV = "ENV"
    DATA = "DATA"
    SCRIPT = "SCRIPT"
    ORACLE = "ORACLE"
    BYPASS = "BYPASS"
    PRODUCT = "PRODUCT"
    FLAKY = "FLAKY"
    TIMEOUT = "TIMEOUT"


# Not "Phase" to avoid confusion with planning phases
class PhaseId(str, Enum):
    PHASE_1A = "1a"
    PHASE_1B = "1b"
    PHASE_2 = "2"
    PHASE_3 = "3"
    PHASE_4 = "4"


# ---------------------------------------------------------------------------
# Registry and forbidden semantics metadata
# ---------------------------------------------------------------------------

ENUM_REGISTRY: dict[str, type[Enum]] = {
    "skill_id": SkillId,
    "module_id": ModuleId,
    "assertion_layer": AssertionLayer,
    "failure_class": FailureClass,  # SRC-009: FailureClass.failure_classification
    "failure_classification": FailureClass,  # Alias for SRC-009 Accident.failure_classification
    "gate_verdict": GateVerdict,  # SRC-009: Gate.verdict
    "verdict": GateVerdict,  # Alias for SRC-009 Gate.verdict and Verifier.verdict
    "phase": PhaseId,
}

FORBIDDEN_SEMANTICS: dict[str, str] = {
    "skill_id": "Internal modules registered as Skill",
    "module_id": "Direct user invocation",
    "assertion_layer": "Skip A or B layer, go directly to C",
    "failure_class": "New undefined categories, ad-hoc classification",
    "failure_classification": "New undefined categories, ad-hoc classification",
    "gate_verdict": "Custom verdict types",
    "verdict": "Custom verdict types",
    "phase": "Skip phases, go directly to production",
}


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------


def validate_field(
    field_name: str, value: str, label: str
) -> list[EnumGuardViolation]:
    """Validate a single field value against its enum whitelist.

    Returns [] if valid, or a list with one EnumGuardViolation if invalid.
    """
    enum_cls = ENUM_REGISTRY.get(field_name)
    if enum_cls is None:
        return [
            EnumGuardViolation(
                field=field_name,
                value=value,
                allowed=[],
                label=label,
            )
        ]
    allowed = [e.value for e in enum_cls]
    if value not in allowed:
        return [
            EnumGuardViolation(
                field=field_name,
                value=value,
                allowed=allowed,
                label=label,
            )
        ]
    return []


def validate_enums(data: dict[str, Any], label: str) -> list[EnumGuardViolation]:
    """Validate all keys in *data* against the enum registry.

    Collects ALL violations (NOT fail-fast). Unknown keys in *data*
    are silently ignored.
    """
    violations: list[EnumGuardViolation] = []
    for key, val in data.items():
        if key in ENUM_REGISTRY:
            violations.extend(validate_field(key, str(val), label))
    return violations


def check_field(field_name: str, value: str, label: str) -> None:
    """Convenience: raise EnumGuardError on first violation."""
    violations = validate_field(field_name, value, label)
    if violations:
        raise EnumGuardError(str(violations[0]))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI for manual enum validation.

    Usage:
        python -m cli.lib.enum_guard --field skill_id qa.test-plan
        python -m cli.lib.enum_guard --check '{"skill_id": "bad"}'
    """
    args = sys.argv[1:]
    if "--check" in args:
        idx = args.index("--check")
        raw = args[idx + 1] if idx + 1 < len(args) else "{}"
        data = json.loads(raw)
        violations = validate_enums(data, label="cli")
        if violations:
            for v in violations:
                print(f"FAIL: {v}")
            sys.exit(1)
        else:
            print("OK: all values valid")
    elif "--field" in args:
        idx = args.index("--field")
        if idx + 2 >= len(args):
            print("Usage: --field <field_name> <value>", file=sys.stderr)
            sys.exit(1)
        field_name = args[idx + 1]
        value = args[idx + 2]
        violations = validate_field(field_name, value, label="cli")
        if violations:
            print(f"FAIL: {violations[0]}")
            sys.exit(1)
        else:
            print("OK")
    else:
        print("Usage: python -m cli.lib.enum_guard --field <name> <value> | --check '<json>'")
        sys.exit(1)


if __name__ == "__main__":
    main()
