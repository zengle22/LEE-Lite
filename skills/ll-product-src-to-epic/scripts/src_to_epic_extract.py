"""FRZ-based EPIC extraction logic — rule-template projection (D-01).

Separated from the runtime for testability. This module maps FRZ MSC
dimensions to EPIC sections and handles anchor registration, guard
projection, and drift detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cli.lib.anchor_registry import AnchorRegistry
from cli.lib.drift_detector import check_drift
from cli.lib.errors import CommandError, ensure
from cli.lib.frz_schema import FRZPackage
from cli.lib.projection_guard import guard_projection


# ---------------------------------------------------------------------------
# EpicExtractResult — immutable extraction result DTO
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpicExtractResult:
    """Result of FRZ-to-EPIC extraction."""

    ok: bool
    frz_id: str
    epic_payload: dict[str, Any]
    anchors_registered: list[str]
    drift_results: list[dict]
    guard_verdict: str
    warnings: list[str]


# ---------------------------------------------------------------------------
# Rule-template mapping (D-01): FRZ MSC dimensions -> EPIC sections
# ---------------------------------------------------------------------------


def build_epic_from_frz(
    frz_package: FRZPackage,
    src_package: dict[str, Any],
    frz_id: str,
) -> dict[str, Any]:
    """Map FRZ MSC dimensions to EPIC structure via rule-template projection.

    FRZ-to-EPIC mapping rules (D-01):
    - core_journeys (JRN-xxx) -> EPIC scope / capability_axes
    - domain_model (ENT-xxx) -> EPIC actors_and_roles + entities
    - state_machine (SM-xxx) -> EPIC product_behavior_slices
    - acceptance_contract (FC-xxx) -> EPIC epic_success_criteria
    - constraints -> EPIC constraints_and_dependencies (verbatim)
    - derived_allowed -> EPIC decomposition_rules
    - known_unknowns (open) -> EPIC non_goals
    - evidence.source_refs -> EPIC source_refs (add frz::{frz_id})

    Args:
        frz_package: Frozen FRZ package with all MSC dimensions.
        src_package: SRC package dict (anchor source, provides src_root_id).
        frz_id: FRZ identifier for traceability.

    Returns:
        EPIC JSON payload dict matching GeneratedEpic.json_payload structure.
    """
    ensure(
        isinstance(frz_package, FRZPackage),
        "INVALID_REQUEST",
        "frz_package must be an FRZPackage instance",
    )
    ensure(
        isinstance(src_package, dict),
        "INVALID_REQUEST",
        "src_package must be a dict",
    )

    # FRZ core_journeys -> EPIC scope / capability_axes
    scope: list[str] = []
    for journey in frz_package.core_journeys:
        steps_preview = " -> ".join(journey.steps[:3])
        scope.append(f"Journey {journey.id}: {journey.name} -- {steps_preview}")

    # FRZ domain_model -> EPIC actors_and_roles
    actors: list[dict[str, str]] = []
    for entity in frz_package.domain_model:
        actors.append({
            "role": entity.name,
            "responsibility": str(entity.contract.get("purpose", "")),
        })

    # FRZ state_machine -> EPIC product_behavior_slices
    behavior_slices: list[dict[str, Any]] = []
    for sm in frz_package.state_machine:
        behavior_slices.append({
            "name": sm.name,
            "states": sm.states,
            "transitions": sm.transitions,
        })

    # FRZ acceptance_contract -> EPIC epic_success_criteria
    success_criteria: list[str] = []
    if frz_package.acceptance_contract is not None:
        success_criteria = list(frz_package.acceptance_contract.expected_outcomes)

    # FRZ constraints -> EPIC constraints_and_dependencies
    constraints = list(frz_package.constraints)

    # FRZ known_unknowns (open) -> EPIC non_goals
    non_goals: list[str] = []
    for ku in frz_package.known_unknowns:
        if ku.status == "open":
            owner = ku.owner or "unassigned"
            non_goals.append(f"Unresolved: {ku.topic} (owner: {owner})")

    # FRZ evidence.source_refs -> EPIC source_refs
    source_refs: list[str] = []
    if frz_package.evidence is not None:
        source_refs = list(frz_package.evidence.source_refs)
    source_refs.append(f"frz::{frz_id}")

    # Build traceability mapping
    traceability: list[dict[str, Any]] = []
    if frz_package.core_journeys:
        traceability.append({
            "section": "scope",
            "frz_source": "core_journeys",
            "anchors": [j.id for j in frz_package.core_journeys],
        })
    if frz_package.domain_model:
        traceability.append({
            "section": "actors_and_roles",
            "frz_source": "domain_model",
            "anchors": [e.id for e in frz_package.domain_model],
        })
    if frz_package.state_machine:
        traceability.append({
            "section": "product_behavior_slices",
            "frz_source": "state_machine",
            "anchors": [s.id for s in frz_package.state_machine],
        })

    return {
        "artifact_type": "epic_freeze_package",
        "workflow_key": "product.src-to-epic.extract",
        "workflow_run_id": f"extract-{frz_id}",
        "title": f"EPIC extracted from {frz_id}",
        "status": "extracted",
        "schema_version": "1.0.0",
        "epic_freeze_ref": frz_id,
        "src_root_id": src_package.get("src_root_id", ""),
        "source_refs": source_refs,
        "epic_intent": f"EPIC extracted from FRZ {frz_id} via rule-template projection",
        "business_goal": "",
        "scope": scope,
        "non_goals": non_goals,
        "epic_success_criteria": success_criteria,
        "decomposition_rules": list(frz_package.derived_allowed),
        "capability_axes": scope,
        "product_behavior_slices": behavior_slices,
        "actors_and_roles": actors,
        "constraints_and_dependencies": constraints,
        "traceability": traceability,
    }


# ---------------------------------------------------------------------------
# Extraction logic: anchor registration, guard, drift
# ---------------------------------------------------------------------------


def _collect_anchor_ids(frz_package: FRZPackage) -> list[tuple[str, str]]:
    """Collect all anchor IDs from FRZ dimensions with their dimension label.

    Returns list of (anchor_id, dimension) tuples.
    """
    anchors: list[tuple[str, str]] = []
    for journey in frz_package.core_journeys:
        anchors.append((journey.id, "core_journeys"))
    for entity in frz_package.domain_model:
        anchors.append((entity.id, "domain_model"))
    for sm in frz_package.state_machine:
        anchors.append((sm.id, "state_machine"))
    if frz_package.acceptance_contract is not None:
        for i, outcome in enumerate(frz_package.acceptance_contract.expected_outcomes):
            # Acceptance contract outcomes don't have explicit IDs; derive FC-xxx
            anchors.append((f"FC-{i + 1:03d}", "acceptance_contract"))
    return anchors


def extract_epic_from_frz_logic(
    frz_package: FRZPackage,
    src_package: dict[str, Any],
    frz_id: str,
    repo_root: Path,
) -> EpicExtractResult:
    """Full extraction logic: build EPIC, register anchors, guard, drift.

    Args:
        frz_package: FRZ package with frozen semantics.
        src_package: SRC package dict (anchor source).
        frz_id: FRZ identifier.
        repo_root: Workspace root for anchor registry.

    Returns:
        EpicExtractResult with payload, anchors, drift, and guard verdict.
    """
    ensure(
        isinstance(repo_root, Path),
        "INVALID_REQUEST",
        "repo_root must be a Path",
    )

    warnings: list[str] = []

    # Warnings for empty dimensions
    if not frz_package.core_journeys:
        warnings.append("No core_journeys in FRZ")
    if not frz_package.domain_model:
        warnings.append("No domain_model in FRZ")
    if not frz_package.state_machine:
        warnings.append("No state_machine in FRZ")
    if frz_package.acceptance_contract is None or not frz_package.acceptance_contract.expected_outcomes:
        warnings.append("No acceptance_contract in FRZ")

    # Build EPIC payload
    epic_payload = build_epic_from_frz(frz_package, src_package, frz_id)

    # Register anchors
    registry = AnchorRegistry(repo_root)
    anchors_registered: list[str] = []
    anchor_target_data: dict[str, Any] = {}

    for anchor_id, dimension in _collect_anchor_ids(frz_package):
        registry.register_projection(
            anchor_id=anchor_id,
            frz_ref=frz_id,
            projection_path="EPIC",
            metadata={"dimension": dimension, "src_anchor": True},
        )
        anchors_registered.append(anchor_id)
        # Build target data for drift detection
        anchor_content = _extract_anchor_content_for_drift(frz_package, anchor_id)
        anchor_target_data[anchor_id] = anchor_content

    # Guard projection
    guard_result = guard_projection(frz_package, epic_payload)
    guard_verdict = guard_result.verdict

    # Drift detection for each anchor
    drift_results: list[dict] = []
    for anchor_id in anchors_registered:
        result = check_drift(anchor_id, frz_package, anchor_target_data)
        drift_results.append({
            "anchor_id": result.anchor_id,
            "has_drift": result.has_drift,
            "drift_type": result.drift_type,
            "detail": result.detail,
        })

    ok = guard_verdict == "pass" and not any(d["has_drift"] for d in drift_results)

    return EpicExtractResult(
        ok=ok,
        frz_id=frz_id,
        epic_payload=epic_payload,
        anchors_registered=anchors_registered,
        drift_results=drift_results,
        guard_verdict=guard_verdict,
        warnings=warnings,
    )


def _extract_anchor_content_for_drift(
    frz_package: FRZPackage, anchor_id: str
) -> dict[str, Any]:
    """Extract semantic content for a given anchor ID for drift comparison."""
    for journey in frz_package.core_journeys:
        if journey.id == anchor_id:
            return {"name": journey.name, "id": journey.id, "steps": journey.steps}
    for entity in frz_package.domain_model:
        if entity.id == anchor_id:
            return {"name": entity.name, "id": entity.id, "contract": entity.contract}
    for sm in frz_package.state_machine:
        if sm.id == anchor_id:
            return {"name": sm.name, "id": sm.id, "states": sm.states}
    # Acceptance contract anchors (FC-xxx) are derived
    if anchor_id.startswith("FC-"):
        if frz_package.acceptance_contract is not None:
            return {
                "name": f"Acceptance Contract",
                "id": anchor_id,
                "outcomes": frz_package.acceptance_contract.expected_outcomes,
            }
    return {"name": anchor_id, "id": anchor_id}
