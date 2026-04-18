"""FRZ-based FEAT extraction logic.

Provides the core FRZ→FEAT extraction logic, separated from the runtime
for testability. Implements rule-template mapping (D-01) from FRZ MSC
5 dimensions to FEAT sections.

Exported:
- FeatExtractResult (dataclass)
- build_feat_from_frz() — rule-template mapping FRZ→FEAT
- extract_feat_from_frz_logic() — full extraction with guard/drift
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FeatExtractResult:
    """Result of FRZ→FEAT extraction."""

    ok: bool
    frz_id: str
    feat_payload: dict[str, Any]
    anchors_registered: list[str]
    drift_results: list[dict]
    guard_verdict: str
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Rule-template mapping: FRZ MSC → FEAT sections (D-01)
# ---------------------------------------------------------------------------


def build_feat_from_frz(
    frz_package: Any,
    epic_package: dict[str, Any],
    frz_id: str,
) -> dict[str, Any]:
    """Build FEAT payload from FRZ package via rule-template mapping (D-01).

    Maps each FRZ MSC dimension to corresponding FEAT sections:
    - core_journeys → features (bundle_intent, identity_and_scenario)
    - domain_model → product_objects_and_deliverables
    - state_machine → product_behavior_slices (business_flow, frozen_downstream_boundary)
    - acceptance_contract → acceptance criteria
    - constraints → constraints_and_dependencies (verbatim)
    - known_unknowns → bundle_shared_non_goals (explicit_non_decisions)
    - evidence.source_refs → source_refs (with frz:: and epic:: prefix)

    Args:
        frz_package: FRZPackage with all MSC dimensions populated.
        epic_package: Dict with epic_freeze_ref and src_root_id.
        frz_id: FRZ identifier for traceability.

    Returns:
        FEAT JSON payload dict.
    """
    # a. core_journeys → features
    identity_and_scenario = []
    for journey in frz_package.core_journeys:
        identity_and_scenario.append({
            "product_interface": f"Journey {journey.id}: {journey.name}",
            "completed_state": f"All steps in journey completed successfully",
            "primary_actor": "User",
            "secondary_actors": [],
            "user_story": f"As a user, I want to complete {journey.name}",
            "trigger": f"Initiate {journey.name} journey",
            "preconditions": [],
            "postconditions": [f"Completed {journey.name}: {' → '.join(journey.steps)}"],
        })

    # b. domain_model → product_objects_and_deliverables
    product_objects = []
    for entity in frz_package.domain_model:
        product_objects.append({
            "name": entity.name,
            "id": entity.id,
            "contract": entity.contract,
        })

    # c. state_machine → business_flow / frozen_downstream_boundary
    business_flows = []
    frozen_boundaries = []
    for sm in frz_package.state_machine:
        business_flows.append({
            "id": sm.id,
            "name": sm.name,
            "main_flow": sm.transitions,
            "states": sm.states,
        })
        frozen_boundaries.append({
            "frozen_product_shape": [f"State machine {sm.id}: {sm.name}"],
            "open_technical_decisions": [],
        })

    # d. acceptance_contract → acceptance criteria
    acceptance_criteria = []
    if frz_package.acceptance_contract is not None:
        acceptance_criteria = list(frz_package.acceptance_contract.expected_outcomes)

    # e. constraints → FEAT constraints (verbatim)
    constraints = list(frz_package.constraints)

    # f. known_unknowns → explicit_non_decisions (open only)
    non_decisions = [
        f"Unresolved: {ku.topic} ({ku.id})"
        for ku in frz_package.known_unknowns
        if ku.status == "open"
    ]

    # g. evidence.source_refs → source_refs
    source_refs = list(frz_package.evidence.source_refs) if frz_package.evidence else []
    source_refs.append(f"frz::{frz_id}")
    epic_ref = epic_package.get("epic_freeze_ref", "")
    if epic_ref:
        source_refs.append(epic_ref)

    journey_ids = [j.id for j in frz_package.core_journeys]
    entity_ids = [e.id for e in frz_package.domain_model]
    sm_ids = [s.id for s in frz_package.state_machine]

    # h. Build FEAT JSON payload
    return {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat.extract",
        "workflow_run_id": f"extract-{frz_id}",
        "title": f"FEAT extracted from {frz_id}",
        "status": "extracted",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_package.get("epic_freeze_ref", frz_id),
        "src_root_id": epic_package.get("src_root_id", ""),
        "source_refs": source_refs,
        "bundle_intent": f"FEAT bundle extracted from FRZ {frz_id} covering {len(frz_package.core_journeys)} journeys",
        "features": identity_and_scenario,
        "product_objects_and_deliverables": product_objects,
        "product_behavior_slices": business_flows,
        "frozen_downstream_boundaries": frozen_boundaries,
        "acceptance_criteria": acceptance_criteria,
        "constraints_and_dependencies": constraints,
        "bundle_shared_non_goals": non_decisions,
        "traceability": [
            {"section": "features", "frz_source": "core_journeys", "anchors": journey_ids},
            {"section": "product_objects", "frz_source": "domain_model", "anchors": entity_ids},
            {"section": "business_flows", "frz_source": "state_machine", "anchors": sm_ids},
        ],
    }


# ---------------------------------------------------------------------------
# Full extraction with anchor registration, guard, drift
# ---------------------------------------------------------------------------


def extract_feat_from_frz_logic(
    frz_package: Any,
    epic_package: dict[str, Any],
    frz_id: str,
    repo_root: Any,
) -> FeatExtractResult:
    """Run full FRZ→FEAT extraction with anchor registration, guard, drift.

    Steps:
    1. Build FEAT payload from FRZ via rule-template mapping.
    2. Register all FRZ anchors with projection_path="FEAT".
    3. Run projection guard.
    4. Run drift detection for each anchor.
    5. Build and return FeatExtractResult.

    Args:
        frz_package: FRZPackage with all MSC dimensions.
        epic_package: Dict with epic_freeze_ref and src_root_id.
        frz_id: FRZ identifier.
        repo_root: Workspace root path.

    Returns:
        FeatExtractResult with all extraction outcomes.
    """
    from pathlib import Path

    from cli.lib.anchor_registry import AnchorRegistry
    from cli.lib.drift_detector import check_drift
    from cli.lib.errors import CommandError
    from cli.lib.projection_guard import guard_projection

    warnings: list[str] = []

    # Check for empty dimensions and warn
    if not frz_package.core_journeys:
        warnings.append("No core_journeys in FRZ")
    if not frz_package.domain_model:
        warnings.append("No domain_model in FRZ")
    if not frz_package.state_machine:
        warnings.append("No state_machine in FRZ")
    if frz_package.acceptance_contract is None:
        warnings.append("No acceptance_contract in FRZ")

    # Step 1: Build FEAT payload
    feat_payload = build_feat_from_frz(frz_package, epic_package, frz_id)

    # Step 2: Register all anchors from FRZ with projection_path="FEAT"
    frz_anchor_ids: list[str] = []
    for journey in frz_package.core_journeys:
        frz_anchor_ids.append(journey.id)
    for entity in frz_package.domain_model:
        frz_anchor_ids.append(entity.id)
    for sm in frz_package.state_machine:
        frz_anchor_ids.append(sm.id)
    if frz_package.acceptance_contract is not None:
        for outcome in frz_package.acceptance_contract.expected_outcomes:
            import re as _re
            fc_match = _re.search(r"FC-\d{3,}", outcome)
            if fc_match:
                frz_anchor_ids.append(fc_match.group(0))
    for ku in frz_package.known_unknowns:
        frz_anchor_ids.append(ku.id)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_anchor_ids: list[str] = []
    for aid in frz_anchor_ids:
        if aid not in seen:
            seen.add(aid)
            unique_anchor_ids.append(aid)

    registry = AnchorRegistry(Path(repo_root))
    registered_anchors: list[str] = []
    for anchor_id in unique_anchor_ids:
        try:
            registry.register_projection(
                anchor_id=anchor_id,
                frz_ref=frz_id,
                projection_path="FEAT",
                metadata={
                    "dimension": _anchor_dimension(anchor_id),
                    "epic_anchor": True,
                },
            )
            registered_anchors.append(anchor_id)
        except CommandError:
            # Already registered — skip duplicate
            pass

    # Step 3: Run projection guard
    guard_result = guard_projection(frz_package, feat_payload)

    # Step 4: Run drift detection for each anchor
    drift_results: list[dict] = []
    for anchor_id in registered_anchors:
        dr = check_drift(anchor_id, frz_package, {anchor_id: {"name": anchor_id}})
        drift_results.append({
            "anchor_id": dr.anchor_id,
            "has_drift": dr.has_drift,
            "drift_type": dr.drift_type,
            "detail": dr.detail,
        })

    # Step 5: Build result
    ok = guard_result.verdict == "pass" and not any(d["has_drift"] for d in drift_results)

    return FeatExtractResult(
        ok=ok,
        frz_id=frz_id,
        feat_payload=feat_payload,
        anchors_registered=registered_anchors,
        drift_results=drift_results,
        guard_verdict=guard_result.verdict,
        warnings=warnings,
    )


def _anchor_dimension(anchor_id: str) -> str:
    """Map anchor ID prefix to FRZ MSC dimension name."""
    if anchor_id.startswith("JRN-"):
        return "core_journeys"
    if anchor_id.startswith("ENT-"):
        return "domain_model"
    if anchor_id.startswith("SM-"):
        return "state_machine"
    if anchor_id.startswith("FC-"):
        return "acceptance_contract"
    if anchor_id.startswith("UNK-"):
        return "known_unknowns"
    return "unknown"
