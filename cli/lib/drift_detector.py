"""Semantic drift detection at anchor level.

Detects when extracted output diverges from FRZ baseline:
- Missing anchors (in FRZ but not extracted, or vice versa)
- Tampered semantics (name/title mismatch)
- New fields outside derived_allowed whitelist
- Constraint violations
- Expired known_unknowns still open

Used by extract modes (08-02, 08-03, 08-04) after extraction to verify
semantic integrity. Pure library module — no CLI entry point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cli.lib.errors import CommandError, ensure
from cli.lib.frz_schema import (
    FRZPackage,
    CoreJourney,
    DomainEntity,
    StateMachine,
    KnownUnknown,
)


# ---------------------------------------------------------------------------
# Intrinsic keys — always allowed regardless of derived_allowed
# ---------------------------------------------------------------------------

INTRINSIC_KEYS = frozenset({
    "artifact_type",
    "schema_version",
    "source_refs",
    "frz_ref",
    "traceability",
})


# ---------------------------------------------------------------------------
# DriftResult — immutable detection result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DriftResult:
    """Result of a single anchor drift check."""

    anchor_id: str
    frz_ref: str
    has_drift: bool
    drift_type: str  # "none" | "missing" | "tampered" | "new_field" | "constraint_violation" | "unknown_expired"
    detail: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_anchor_content(
    frz_package: FRZPackage, anchor_id: str
) -> dict[str, Any] | None:
    """Extract semantic content for a given anchor ID from FRZ dimensions.

    Scans all MSC dimensions:
    - core_journeys: match by id field (JRN-xxx)
    - domain_model: match by id field (ENT-xxx)
    - state_machine: match by id field (SM-xxx)
    - acceptance_contract: scan expected_outcomes for FC-xxx references
    - known_unknowns: match by id field (UNK-xxx)

    Returns a dict with the anchor's semantic fields, or None if not found.
    """
    # Check core_journeys
    for journey in frz_package.core_journeys:
        if journey.id == anchor_id:
            return {"name": journey.name, "id": journey.id, "steps": journey.steps}

    # Check domain_model
    for entity in frz_package.domain_model:
        if entity.id == anchor_id:
            return {"name": entity.name, "id": entity.id, "contract": entity.contract}

    # Check state_machine
    for sm in frz_package.state_machine:
        if sm.id == anchor_id:
            return {"name": sm.name, "id": sm.id, "states": sm.states}

    # Check acceptance_contract for FC-xxx references
    if frz_package.acceptance_contract is not None:
        for outcome in frz_package.acceptance_contract.expected_outcomes:
            if anchor_id in outcome:
                return {
                    "name": outcome,
                    "id": anchor_id,
                    "outcomes": frz_package.acceptance_contract.expected_outcomes,
                }

    # Check known_unknowns
    for ku in frz_package.known_unknowns:
        if ku.id == anchor_id:
            return {"name": ku.topic, "id": ku.id, "status": ku.status}

    return None


def _semantics_match(frz_content: dict[str, Any], target: dict[str, Any]) -> bool:
    """Compare structural semantics between FRZ content and extracted target.

    Compares name/title field (normalized to lowercase). Returns True if
    they match, False otherwise.
    """
    if not target:
        return False

    frz_name = frz_content.get("name", "")
    target_name = target.get("name", "")

    if isinstance(frz_name, str) and isinstance(target_name, str):
        return frz_name.lower() == target_name.lower()

    return frz_name == target_name


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_drift(
    anchor_id: str,
    frz_package: FRZPackage,
    target_data: dict[str, Any],
) -> DriftResult:
    """Check if an anchor's semantic content has drifted from FRZ baseline.

    Args:
        anchor_id: Anchor identifier (e.g., JRN-001, ENT-001).
        frz_package: FRZ package containing the baseline semantics.
        target_data: Dict keyed by anchor_id with extracted semantic content.
            Example: {"JRN-001": {"name": "Login", ...}, "ENT-001": {...}}

    Returns:
        DriftResult indicating drift status.
    """
    ensure(
        isinstance(target_data, dict),
        "INVALID_REQUEST",
        "target_data must be a dict keyed by anchor_id",
    )

    frz_ref = frz_package.frz_id or ""

    # Check if anchor exists in FRZ baseline
    frz_content = _extract_anchor_content(frz_package, anchor_id)
    if frz_content is None:
        return DriftResult(
            anchor_id=anchor_id,
            frz_ref=frz_ref,
            has_drift=True,
            drift_type="missing",
            detail=f"Anchor {anchor_id} not found in FRZ baseline",
        )

    # Check if anchor is present in extracted output
    extracted = target_data.get(anchor_id)
    if extracted is None:
        return DriftResult(
            anchor_id=anchor_id,
            frz_ref=frz_ref,
            has_drift=True,
            drift_type="missing",
            detail=f"Anchor {anchor_id} not present in extracted output",
        )

    # Check for extra fields in target not present in FRZ content
    frz_keys = set(frz_content.keys())
    target_keys = set(extracted.keys()) if isinstance(extracted, dict) else set()
    extra_keys = target_keys - frz_keys
    if extra_keys:
        return DriftResult(
            anchor_id=anchor_id,
            frz_ref=frz_ref,
            has_drift=True,
            drift_type="new_field",
            detail=f"Anchor {anchor_id} has extra fields: {', '.join(sorted(extra_keys))}",
        )

    # Compare semantic content
    if not _semantics_match(frz_content, extracted):
        return DriftResult(
            anchor_id=anchor_id,
            frz_ref=frz_ref,
            has_drift=True,
            drift_type="tampered",
            detail=f"Anchor {anchor_id} semantics differ from FRZ baseline",
        )

    return DriftResult(
        anchor_id=anchor_id,
        frz_ref=frz_ref,
        has_drift=False,
        drift_type="none",
        detail="OK",
    )


def check_derived_allowed(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> list[str]:
    """Return list of field names in output_data not in derived_allowed whitelist.

    Per D-04: only fields in derived_allowed or INTRINSIC_KEYS are permitted.

    Args:
        frz_package: FRZ package with derived_allowed whitelist.
        output_data: Extracted output dict to check.

    Returns:
        List of non-allowed field names.
    """
    ensure(
        isinstance(output_data, dict),
        "INVALID_REQUEST",
        "output_data must be a dict",
    )

    allowed = set(frz_package.derived_allowed) | INTRINSIC_KEYS
    return [key for key in output_data if key not in allowed]


def check_constraints(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> list[str]:
    """Return list of constraint strings violated by output_data.

    A constraint is violated if its text (or key portion before colon) is
    absent from output_data's keys.

    Args:
        frz_package: FRZ package with constraints list.
        output_data: Extracted output dict to check.

    Returns:
        List of violated constraint strings.
    """
    ensure(
        isinstance(output_data, dict),
        "INVALID_REQUEST",
        "output_data must be a dict",
    )

    violations: list[str] = []
    output_keys = set(output_data.keys())

    for constraint in frz_package.constraints:
        # Check if constraint text or key portion (before colon) is in output keys
        key_portion = constraint.split(":")[0].strip()
        if constraint not in output_keys and key_portion not in output_keys:
            violations.append(constraint)

    return violations


def check_known_unknowns(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
) -> list[dict[str, str]]:
    """Return list of known_unknowns that are open but have expired.

    A KnownUnknown is expired if:
    - status == "open"
    - expires_in contains "0" or "expired"

    Args:
        frz_package: FRZ package with known_unknowns list.
        output_data: Extracted output dict (not used, kept for API consistency).

    Returns:
        List of dicts with id, topic, and status="expired".
    """
    expired: list[dict[str, str]] = []

    for ku in frz_package.known_unknowns:
        if ku.status == "open":
            expires = (ku.expires_in or "").lower()
            if "0" in expires or "expired" in expires:
                expired.append({
                    "id": ku.id,
                    "topic": ku.topic,
                    "status": "expired",
                })

    return expired
