"""FRZ-based FEAT extraction logic — stub.

This module will be implemented in Plan 08-04 Task 2 (TDD).
Provides the core FRZ→FEAT extraction logic, separated from the runtime
for testability.

Exported:
- FeatExtractResult (dataclass)
- build_feat_from_frz() — rule-template mapping FRZ→FEAT
- extract_feat_from_frz_logic() — full extraction with guard/drift
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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


def build_feat_from_frz(
    frz_package: Any,
    epic_package: dict[str, Any],
    frz_id: str,
) -> dict[str, Any]:
    """Build FEAT payload from FRZ package via rule-template mapping (D-01).

    STUB — to be implemented in Plan 08-04 Task 2.
    """
    return {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat.extract",
        "workflow_run_id": f"extract-{frz_id}",
        "title": f"FEAT extracted from {frz_id}",
        "status": "extracted",
        "schema_version": "1.0.0",
        "epic_freeze_ref": epic_package.get("epic_freeze_ref", frz_id),
        "src_root_id": epic_package.get("src_root_id", ""),
        "source_refs": [f"frz::{frz_id}"],
        "bundle_intent": f"FEAT bundle extracted from FRZ {frz_id}",
        "features": [],
        "product_behavior_slices": [],
        "constraints_and_dependencies": [],
        "bundle_shared_non_goals": [],
        "traceability": [],
    }


def extract_feat_from_frz_logic(
    frz_package: Any,
    epic_package: dict[str, Any],
    frz_id: str,
    repo_root: Any,
) -> FeatExtractResult:
    """Run full FRZ→FEAT extraction with anchor registration, guard, drift.

    STUB — to be implemented in Plan 08-04 Task 2.
    """
    payload = build_feat_from_frz(frz_package, epic_package, frz_id)
    return FeatExtractResult(
        ok=True,
        frz_id=frz_id,
        feat_payload=payload,
        anchors_registered=[],
        drift_results=[],
        guard_verdict="pass",
        warnings=[],
    )
