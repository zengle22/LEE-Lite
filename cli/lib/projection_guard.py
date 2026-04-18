"""Projection invariance guard — enforces derived_allowed whitelist.

Runs AFTER extraction (D-03) to verify output does not exceed the
derived_allowed whitelist defined in the FRZ package (D-04).

Pure library module — no CLI entry point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cli.lib.drift_detector import check_derived_allowed, check_constraints
from cli.lib.errors import CommandError, ensure
from cli.lib.frz_schema import FRZPackage


# ---------------------------------------------------------------------------
# Extended intrinsic keys — broader set for projection guard context
# ---------------------------------------------------------------------------

GUARD_INTRINSIC_KEYS = frozenset({
    "artifact_type",
    "schema_version",
    "source_refs",
    "frz_ref",
    "traceability",
    "metadata",
    "created_at",
    "status",
    "version",
})


# ---------------------------------------------------------------------------
# GuardResult — immutable guard verdict
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GuardResult:
    """Result of projection guard check."""

    passed: bool
    violations: list[str]
    verdict: str  # "pass" | "block"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_derived_allowed_fields(
    frz_package: FRZPackage,
    output_fields: set[str],
) -> list[str]:
    """Return sorted list of output fields not in derived_allowed or intrinsic keys.

    Args:
        frz_package: FRZ package with derived_allowed whitelist.
        output_fields: Set of field names to check.

    Returns:
        Sorted list of non-allowed field names.
    """
    ensure(
        isinstance(output_fields, set),
        "INVALID_REQUEST",
        "output_fields must be a set",
    )

    allowed = set(frz_package.derived_allowed) | GUARD_INTRINSIC_KEYS
    return sorted(output_fields - allowed)


def guard_projection(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> GuardResult:
    """Verify output does not exceed derived_allowed whitelist and satisfies constraints.

    Post-extraction check (D-03): runs AFTER extraction to verify
    semantic integrity.

    Args:
        frz_package: FRZ package with derived_allowed and constraints.
        output_data: Extracted output dict to guard.

    Returns:
        GuardResult with pass/block verdict and violation details.
    """
    ensure(
        isinstance(output_data, dict),
        "INVALID_REQUEST",
        "output_data must be a dict",
    )

    if not output_data:
        return GuardResult(passed=True, violations=[], verdict="pass")

    violations: list[str] = []

    # Check derived_allowed fields using extended GUARD_INTRINSIC_KEYS
    # (broader than drift_detector's INTRINSIC_KEYS)
    allowed = set(frz_package.derived_allowed) | GUARD_INTRINSIC_KEYS
    for key in output_data:
        if key not in allowed:
            violations.append(f"field '{key}' not allowed")

    # Check constraints using drift_detector's check_constraints
    constraint_violations = check_constraints(frz_package, output_data)
    for constraint in constraint_violations:
        violations.append(f"constraint violation: {constraint}")

    passed = len(violations) == 0
    return GuardResult(
        passed=passed,
        violations=violations,
        verdict="pass" if passed else "block",
    )
