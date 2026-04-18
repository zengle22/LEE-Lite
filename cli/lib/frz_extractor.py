"""FRZ→SRC rule-template projection — deterministic extraction per D-01.

Transforms a frozen FRZ package into an SRC candidate package using
predefined mapping rules. Registers anchors with projection_path=SRC,
runs projection guard and drift detection, and writes output files.

Pure library module — no CLI entry point.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from cli.lib.anchor_registry import ANCHOR_ID_PATTERN, AnchorRegistry
from cli.lib.drift_detector import check_drift
from cli.lib.errors import CommandError, ensure
from cli.lib.fs import ensure_parent, write_text
from cli.lib.frz_schema import (
    FRZPackage,
    FRZ_ID_PATTERN,
    _parse_frz_dict,
)
from cli.lib.frz_registry import get_frz
from cli.lib.projection_guard import GUARD_INTRINSIC_KEYS, guard_projection


# ---------------------------------------------------------------------------
# ExtractResult — immutable extraction result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractResult:
    """Result of FRZ→SRC extraction."""

    ok: bool
    output_dir: str
    anchors_registered: list[str]
    drift_results: list[dict]
    guard_verdict: str  # "pass" | "block"
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# EXTRACT_RULES — FRZ dimension → SRC section mapping
# ---------------------------------------------------------------------------

EXTRACT_RULES: dict[str, dict[str, Any]] = {
    "product_boundary": {"target": "scope", "transform": "identity"},
    "core_journeys": {"target": "user_journeys", "transform": "map_journeys"},
    "domain_model": {"target": "entities", "transform": "map_entities"},
    "state_machine": {"target": "state_transitions", "transform": "map_state_machines"},
    "acceptance_contract": {"target": "acceptance_criteria", "transform": "map_acceptance"},
    "constraints": {"target": "constraints", "transform": "identity"},
    "known_unknowns": {"target": "open_questions", "transform": "map_unknowns"},
}


# ---------------------------------------------------------------------------
# Internal transform helpers
# ---------------------------------------------------------------------------


def _transform_identity(value: Any, _frz: FRZPackage) -> Any:
    """Pass-through transform."""
    return value


def _transform_product_boundary(frz: FRZPackage) -> dict[str, Any]:
    """Map product_boundary to scope section."""
    if frz.product_boundary is None:
        return {"in_scope": [], "out_of_scope": []}
    return {
        "in_scope": list(frz.product_boundary.in_scope),
        "out_of_scope": list(frz.product_boundary.out_of_scope),
    }


def _transform_core_journeys(frz: FRZPackage) -> list[dict[str, Any]]:
    """Map core_journeys to user_journeys (preserve JRN-xxx IDs)."""
    return [
        {
            "id": j.id,
            "name": j.name,
            "steps": list(j.steps),
        }
        for j in frz.core_journeys
    ]


def _transform_domain_model(frz: FRZPackage) -> list[dict[str, Any]]:
    """Map domain_model to entities (preserve ENT-xxx IDs)."""
    return [
        {
            "id": e.id,
            "name": e.name,
            "contract": dict(e.contract),
        }
        for e in frz.domain_model
    ]


def _transform_state_machine(frz: FRZPackage) -> list[dict[str, Any]]:
    """Map state_machine to state_transitions (preserve SM-xxx IDs)."""
    return [
        {
            "id": sm.id,
            "name": sm.name,
            "states": list(sm.states),
            "transitions": [dict(t) for t in sm.transitions],
        }
        for sm in frz.state_machine
    ]


def _transform_acceptance_contract(frz: FRZPackage) -> dict[str, Any]:
    """Map acceptance_contract to acceptance_criteria (preserve FC-xxx refs)."""
    if frz.acceptance_contract is None:
        return {"expected_outcomes": [], "acceptance_impact": []}
    return {
        "expected_outcomes": list(frz.acceptance_contract.expected_outcomes),
        "acceptance_impact": list(frz.acceptance_contract.acceptance_impact),
    }


def _transform_known_unknowns(frz: FRZPackage) -> list[dict[str, Any]]:
    """Map known_unknowns to open_questions (with owner + expires_in)."""
    return [
        {
            "id": ku.id,
            "topic": ku.topic,
            "status": ku.status,
            "owner": ku.owner,
            "expires_in": ku.expires_in,
        }
        for ku in frz.known_unknowns
    ]


TRANSFORM_FNS: dict[str, Any] = {
    "product_boundary": _transform_product_boundary,
    "core_journeys": _transform_core_journeys,
    "domain_model": _transform_domain_model,
    "state_machine": _transform_state_machine,
    "acceptance_contract": _transform_acceptance_contract,
    "constraints": _transform_identity,
    "known_unknowns": _transform_known_unknowns,
}


# ---------------------------------------------------------------------------
# Anchor extraction from FRZ
# ---------------------------------------------------------------------------


def _collect_anchor_ids(frz: FRZPackage) -> list[str]:
    """Collect all anchor IDs from FRZ MSC dimensions."""
    ids: list[str] = []
    for journey in frz.core_journeys:
        ids.append(journey.id)
    for entity in frz.domain_model:
        ids.append(entity.id)
    for sm in frz.state_machine:
        ids.append(sm.id)
    for ku in frz.known_unknowns:
        ids.append(ku.id)
    # Acceptance contract FC-xxx refs are in expected_outcomes text
    if frz.acceptance_contract is not None:
        for outcome in frz.acceptance_contract.expected_outcomes:
            # Look for FC-xxx patterns
            for part in outcome.split():
                if part.startswith("FC-") and part[3:].isdigit():
                    ids.append(part)
    return ids


def _build_target_data(frz: FRZPackage, src_output: dict[str, Any]) -> dict[str, Any]:
    """Build target_data dict for drift detection, keyed by anchor_id."""
    target: dict[str, Any] = {}
    for journey in frz.core_journeys:
        target[journey.id] = {"name": journey.name, "id": journey.id, "steps": journey.steps}
    for entity in frz.domain_model:
        target[entity.id] = {"name": entity.name, "id": entity.id, "contract": entity.contract}
    for sm in frz.state_machine:
        target[sm.id] = {"name": sm.name, "id": sm.id, "states": sm.states}
    for ku in frz.known_unknowns:
        target[ku.id] = {"name": ku.topic, "id": ku.id, "status": ku.status}
    if frz.acceptance_contract is not None:
        for outcome in frz.acceptance_contract.expected_outcomes:
            for part in outcome.split():
                if part.startswith("FC-") and part[3:].isdigit():
                    target[part] = {"name": outcome, "id": part, "outcomes": frz.acceptance_contract.expected_outcomes}
    return target


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_src_from_frz(
    frz_id: str,
    workspace_root: Path,
    output_dir: Path | None = None,
) -> ExtractResult:
    """Extract SRC candidate package from a frozen FRZ package.

    Per D-01: deterministic rule-template projection, not LLM.

    Args:
        frz_id: FRZ identifier (e.g., FRZ-001).
        workspace_root: Root of the workspace (for registry access).
        output_dir: Output directory. Defaults to
            artifacts/frz-extract/{frz_id}/src/.

    Returns:
        ExtractResult with ok status, registered anchors, drift results,
        and guard verdict.
    """
    # Validate FRZ ID format
    ensure(
        isinstance(frz_id, str) and re.match(FRZ_ID_PATTERN.pattern, frz_id),
        "INVALID_REQUEST",
        f"Invalid FRZ ID format: {frz_id}",
    )

    # Load FRZ from registry
    frz_record = get_frz(workspace_root, frz_id)
    if frz_record is None:
        raise CommandError(
            "REGISTRY_MISS",
            f"FRZ not found in registry: {frz_id}",
        )

    # Check FRZ is frozen
    frz_status = frz_record.get("status", "draft")
    ensure(
        frz_status == "frozen",
        "POLICY_DENIED",
        f"FRZ not frozen: {frz_id} (status={frz_status})",
    )

    # Load FRZ YAML
    package_ref = frz_record.get("package_ref", "")
    ensure(
        package_ref,
        "INVALID_REQUEST",
        f"FRZ has no package_ref: {frz_id}",
    )
    frz_path = Path(package_ref)
    ensure(
        frz_path.exists(),
        "INVALID_REQUEST",
        f"FRZ package file not found: {package_ref}",
    )

    frz_raw = yaml.safe_load(frz_path.read_text(encoding="utf-8"))
    inner = frz_raw.get("frz_package", frz_raw)
    frz_pkg = _parse_frz_dict(inner)

    # Apply EXTRACT_RULES to build SRC output
    src_output: dict[str, Any] = {}
    for dimension, rule in EXTRACT_RULES.items():
        transform_fn = TRANSFORM_FNS[dimension]
        if dimension == "product_boundary":
            src_output[rule["target"]] = transform_fn(frz_pkg)
        elif dimension == "acceptance_contract":
            src_output[rule["target"]] = transform_fn(frz_pkg)
        elif dimension == "constraints":
            src_output[rule["target"]] = list(frz_pkg.constraints)
        else:
            src_output[rule["target"]] = transform_fn(frz_pkg)

    # Collect and register anchors
    anchor_ids = _collect_anchor_ids(frz_pkg)
    registered: list[str] = []
    registry = AnchorRegistry(workspace_root)
    for aid in anchor_ids:
        try:
            registry.register(
                anchor_id=aid,
                frz_ref=frz_id,
                projection_path="SRC",
                metadata={"source": "extract_src_from_frz"},
            )
            registered.append(aid)
        except CommandError:
            # Already registered — acceptable in idempotent re-runs
            registered.append(aid)

    # Run projection guard
    guard_result = guard_projection(frz_pkg, src_output)
    guard_verdict = guard_result.verdict

    # Run drift detection for each anchor
    target_data = _build_target_data(frz_pkg, src_output)
    drift_results: list[dict] = []
    for aid in anchor_ids:
        dr = check_drift(aid, frz_pkg, target_data)
        drift_results.append({
            "anchor_id": dr.anchor_id,
            "has_drift": dr.has_drift,
            "drift_type": dr.drift_type,
            "detail": dr.detail,
        })

    # Determine overall ok status
    ok = guard_verdict == "pass"

    # Set default output dir
    if output_dir is None:
        output_dir = workspace_root / "artifacts" / "frz-extract" / frz_id / "src"

    # Write output files
    ensure_parent(output_dir)
    write_text(
        output_dir / "src-package.json",
        json.dumps(src_output, ensure_ascii=False, indent=2) + "\n",
    )

    yaml_output = {"artifact_type": "src_package", "frz_ref": frz_id, **src_output}
    write_text(
        output_dir / "src-package.yaml",
        yaml.dump(yaml_output, default_flow_style=False, allow_unicode=True, sort_keys=False),
    )

    report = {
        "frz_id": frz_id,
        "anchors_registered": registered,
        "drift_results": drift_results,
        "guard_verdict": guard_verdict,
        "warnings": [],
    }
    write_text(
        output_dir / "extraction-report.json",
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
    )

    warnings: list[str] = []

    return ExtractResult(
        ok=ok,
        output_dir=str(output_dir),
        anchors_registered=registered,
        drift_results=drift_results,
        guard_verdict=guard_verdict,
        warnings=warnings,
    )


def check_frz_coverage(frz_package: FRZPackage, target_layer: str) -> list[str]:
    """Check if FRZ has relevant content for a given SSOT layer.

    Per D-08: returns warnings for missing content but does not block.

    Args:
        frz_package: The FRZ package to check.
        target_layer: One of TECH, UI, TEST, IMPL.

    Returns:
        List of warning strings for missing layer-specific content.
    """
    warnings: list[str] = []

    if target_layer == "TECH":
        has_tech = any(
            any(kw in c.lower() for kw in ["https", "api", "response", "bcrypt", "hash", "encrypt", "timeout", "latency", "performance"])
            for c in frz_package.constraints
        )
        if not has_tech:
            warnings.append(
                f"WARNING: FRZ {frz_package.frz_id} lacks technical constraints for TECH layer extraction"
            )

    elif target_layer == "UI":
        has_ui = any(
            any(
                kw in step.lower() or kw in j.name.lower()
                for kw in ["click", "button", "enter", "select", "display", "show", "page", "screen", "form", "input", "modal", "dialog", "menu"]
            )
            for j in frz_package.core_journeys
            for step in j.steps
        )
        if not has_ui:
            warnings.append(
                f"WARNING: FRZ {frz_package.frz_id} lacks UI-related journey steps for UI layer extraction"
            )

    elif target_layer == "TEST":
        has_test = (
            frz_package.acceptance_contract is not None
            and len(frz_package.acceptance_contract.expected_outcomes) > 0
        )
        if not has_test:
            warnings.append(
                f"WARNING: FRZ {frz_package.frz_id} lacks testable acceptance outcomes for TEST layer extraction"
            )

    elif target_layer == "IMPL":
        has_impl = any(
            len(e.contract) > 0 for e in frz_package.domain_model
        )
        if not has_impl:
            warnings.append(
                f"WARNING: FRZ {frz_package.frz_id} lacks domain model contracts for IMPL layer extraction"
            )

    return warnings
