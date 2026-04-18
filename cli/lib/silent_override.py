"""Silent override detection — compares output against FRZ anchor semantics.

Detects when a dev skill output silently rewrites FRZ semantics without
triggering the FRZ revision workflow (D-01, D-02).

Pure library module with CLI entry point.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# When run directly as script, ensure `cli.lib` imports resolve
if __name__ == "__main__":
    _project_root = Path(__file__).resolve().parent.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

import yaml

from cli.lib.drift_detector import (
    DriftResult,
    check_constraints,
    check_derived_allowed,
    check_drift,
    check_known_unknowns,
)
from cli.lib.errors import CommandError, ensure
from cli.lib.frz_registry import get_frz
from cli.lib.frz_schema import FRZPackage, _parse_frz_dict


# ---------------------------------------------------------------------------
# OverrideResult — immutable verdict
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OverrideResult:
    """Result of silent override check."""

    passed: bool
    classification: str  # "ok" | "clarification" | "semantic_change"
    semantic_drift: dict
    block_reasons: list[str]
    pass_with_revisions: list[str]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_frz_ref(output_data: dict[str, Any], frz_id: str | None) -> str:
    """Extract FRZ reference from parameter or output data."""
    if frz_id is not None:
        return frz_id
    frz_ref = output_data.get("frz_ref")
    if frz_ref:
        return str(frz_ref)
    raise CommandError(
        "INVALID_REQUEST",
        "No FRZ reference found in output or parameters",
    )


def _load_frz_package(workspace_root: Path, frz_id: str) -> FRZPackage:
    """Load FRZ package from registry."""
    record = get_frz(workspace_root, frz_id)
    ensure(record is not None, "REGISTRY_MISS", f"FRZ not found in registry: {frz_id}")
    ensure(
        record.get("status") == "frozen",
        "POLICY_DENIED",
        f"FRZ status is '{record.get('status')}', must be 'frozen': {frz_id}",
    )
    package_ref = record.get("package_ref", "")
    ensure(package_ref, "INVALID_REQUEST", f"FRZ has no package_ref: {frz_id}")
    frz_path = Path(package_ref)
    ensure(frz_path.exists(), "INVALID_REQUEST", f"FRZ file not found: {package_ref}")
    raw = yaml.safe_load(frz_path.read_text(encoding="utf-8"))
    inner = raw.get("frz_package", raw)
    return _parse_frz_dict(inner)


def _extract_anchor_ids(frz_package: FRZPackage) -> set[str]:
    """Extract all anchor IDs from FRZ package dimensions."""
    ids: set[str] = set()
    for journey in frz_package.core_journeys:
        ids.add(journey.id)
    for entity in frz_package.domain_model:
        ids.add(entity.id)
    for sm in frz_package.state_machine:
        ids.add(sm.id)
    for ku in frz_package.known_unknowns:
        ids.add(ku.id)
    return ids


def _filter_anchor_ids(
    anchor_ids: set[str], anchor_filter: set[str] | None
) -> set[str]:
    """Filter anchor IDs by prefix set."""
    if anchor_filter is None or len(anchor_filter) == 0:
        return anchor_ids if anchor_filter is None else set()
    return {
        aid for aid in anchor_ids
        if aid.split("-")[0] in anchor_filter
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_change(
    drift_results: list[DriftResult],
    disallowed_fields: list[str],
) -> str:
    """Rule-based classification (D-08, D-09). No LLM.

    Args:
        drift_results: List of anchor-level drift results.
        disallowed_fields: Field names outside derived_allowed whitelist.

    Returns:
        "ok", "clarification", or "semantic_change".
    """
    disallowed_set = set(disallowed_fields)

    for dr in drift_results:
        if dr.drift_type == "missing":
            return "semantic_change"
        if dr.drift_type == "tampered":
            return "semantic_change"
        if dr.drift_type == "constraint_violation":
            return "semantic_change"

    if disallowed_set:
        return "semantic_change"

    has_new_field_in_allowed = False
    for dr in drift_results:
        if dr.drift_type == "new_field":
            has_new_field_in_allowed = True

    if has_new_field_in_allowed:
        return "clarification"

    return "ok"


def check_silent_override(
    frz_package: FRZPackage,
    output_data: dict[str, Any],
    anchor_filter: set[str] | None = None,
) -> OverrideResult:
    """Check if output silently overrides FRZ semantics.

    Args:
        frz_package: FRZ package with anchor semantics.
        output_data: Output artifact data (keyed by anchor_id or flat dict).
        anchor_filter: If set, only check anchors whose ID prefix is in the set.
            None = all anchors, empty set = skip anchor checks.

    Returns:
        OverrideResult with classification and verdict details.
    """
    block_reasons: list[str] = []
    pass_with_revisions: list[str] = []
    drift_results: list[DriftResult] = []

    # Extract and filter anchor IDs
    all_anchor_ids = _extract_anchor_ids(frz_package)
    check_ids = _filter_anchor_ids(all_anchor_ids, anchor_filter)

    # Anchor-level drift checks
    for anchor_id in sorted(check_ids):
        dr = check_drift(anchor_id, frz_package, output_data)
        drift_results.append(dr)

        if dr.drift_type == "tampered":
            block_reasons.append(
                f"tampered: {anchor_id} - {dr.detail}"
            )
        elif dr.drift_type == "missing":
            block_reasons.append(
                f"anchor_missing: {anchor_id} - {dr.detail}"
            )
        elif dr.drift_type == "new_field":
            # Extract extra field names from detail
            extra_fields = _parse_extra_fields(dr.detail)
            for ef in extra_fields:
                if ef in frz_package.derived_allowed:
                    pass_with_revisions.append(
                        f"allowed_new_field: {ef} in {anchor_id}"
                    )
                else:
                    block_reasons.append(
                        f"new_field outside derived_allowed: {ef} in {anchor_id}"
                    )

    # Field-level: derived_allowed check
    # Filter out anchor ID keys — they are content, not derived metadata fields
    anchor_pattern_ids = all_anchor_ids
    metadata_data = {
        k: v for k, v in output_data.items()
        if k not in anchor_pattern_ids
    }
    disallowed_fields = check_derived_allowed(frz_package, metadata_data)
    for af in disallowed_fields:
        block_reasons.append(
            f"new_field outside derived_allowed: {af}"
        )

    # Check for allowed extra metadata fields (clarification)
    allowed_metadata_fields = [
        k for k in metadata_data
        if k in set(frz_package.derived_allowed)
    ]
    for amf in allowed_metadata_fields:
        pass_with_revisions.append(
            f"allowed_new_field: {amf} (metadata)"
        )

    # Constraint check
    constraint_violations = check_constraints(frz_package, metadata_data)
    for cv in constraint_violations:
        block_reasons.append(f"constraint_violation: {cv}")
        drift_results.append(
            DriftResult(
                anchor_id="CONSTRAINT",
                frz_ref=frz_package.frz_id or "",
                has_drift=True,
                drift_type="constraint_violation",
                detail=cv,
            )
        )

    # Known unknowns check
    expired_kus = check_known_unknowns(frz_package, output_data)
    for ku in expired_kus:
        pass_with_revisions.append(
            f"expired_known_unknown: {ku['id']} ({ku['topic']})"
        )

    # Classification
    classification = classify_change(drift_results, disallowed_fields)

    # If pass_with_revisions is non-empty but classification is "ok",
    # upgrade to "clarification" (metadata-level allowed changes)
    if pass_with_revisions and classification == "ok":
        classification = "clarification"

    # Semantic drift envelope (D-06)
    any_drift = any(dr.has_drift for dr in drift_results)
    semantic_drift = {
        "has_drift": any_drift,
        "drift_results": [
            {
                "anchor_id": dr.anchor_id,
                "frz_ref": dr.frz_ref,
                "has_drift": dr.has_drift,
                "drift_type": dr.drift_type,
                "detail": dr.detail,
            }
            for dr in drift_results
        ],
        "classification": classification,
    }

    return OverrideResult(
        passed=len(block_reasons) == 0,
        classification=classification,
        semantic_drift=semantic_drift,
        block_reasons=block_reasons,
        pass_with_revisions=pass_with_revisions,
    )


def _parse_extra_fields(detail: str) -> list[str]:
    """Extract extra field names from check_drift detail string.

    Format: 'Anchor X has extra fields: field1, field2'
    """
    if "extra fields:" not in detail:
        return []
    fields_part = detail.split("extra fields:")[1].strip()
    return [f.strip() for f in fields_part.split(",") if f.strip()]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for silent override check.

    Usage:
        python cli/lib/silent_override.py check \
            --output <artifacts-dir> --frz <frz-id> \
            [--workspace <workspace-root>] \
            [--mode full|journey_sm|product_boundary]
    """
    parser = argparse.ArgumentParser(
        description="Silent override detection — compares output against FRZ anchor semantics"
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Run silent override check")
    check_parser.add_argument(
        "--output", required=True, help="Path to artifacts directory"
    )
    check_parser.add_argument(
        "--frz", required=True, help="FRZ package ID"
    )
    check_parser.add_argument(
        "--workspace", default=".", help="Workspace root directory"
    )
    check_parser.add_argument(
        "--mode",
        choices=["full", "journey_sm", "product_boundary"],
        default="full",
        help="Layered baseline mode",
    )

    args = parser.parse_args()

    if args.command != "check":
        parser.print_help()
        sys.exit(1)

    workspace_root = Path(args.workspace)
    output_dir = Path(args.output)

    # Load FRZ package from registry
    record = get_frz(workspace_root, args.frz)
    ensure(record is not None, "REGISTRY_MISS", f"FRZ not found: {args.frz}")
    ensure(
        record.get("status") == "frozen",
        "POLICY_DENIED",
        f"FRZ not frozen: {args.frz} (status={record.get('status')})",
    )
    frz_path = Path(record["package_ref"])
    ensure(frz_path.exists(), "INVALID_REQUEST", f"FRZ file not found: {frz_path}")
    raw = yaml.safe_load(frz_path.read_text(encoding="utf-8"))
    inner = raw.get("frz_package", raw)
    frz_package = _parse_frz_dict(inner)

    # Build output_data from artifacts
    output_data: dict[str, Any] = {"frz_ref": args.frz}

    if output_dir.is_dir():
        for f in sorted(output_dir.iterdir()):
            if f.suffix in (".json", ".yaml", ".yml"):
                content = f.read_text(encoding="utf-8")
                if f.suffix == ".json":
                    data = json.loads(content)
                else:
                    data = yaml.safe_load(content)
                if isinstance(data, dict):
                    output_data.update(data)
    elif output_dir.is_file():
        content = output_dir.read_text(encoding="utf-8")
        if output_dir.suffix == ".json":
            data = json.loads(content)
        else:
            data = yaml.safe_load(content)
        if isinstance(data, dict):
            output_data.update(data)

    ensure(
        len(output_data) > 1,  # >1 because frz_ref is always present
        "INVALID_REQUEST",
        f"No output artifacts found in {output_dir}",
    )

    # Map mode to anchor_filter (D-07)
    mode_anchor_filters = {
        "full": None,  # all anchors
        "journey_sm": {"JRN", "SM"},  # journey + state machine only
        "product_boundary": set(),  # skip anchor checks
    }
    anchor_filter = mode_anchor_filters.get(args.mode)

    result = check_silent_override(frz_package, output_data, anchor_filter)

    # Print result as JSON
    result_dict = {
        "passed": result.passed,
        "classification": result.classification,
        "semantic_drift": result.semantic_drift,
        "block_reasons": result.block_reasons,
        "pass_with_revisions": result.pass_with_revisions,
    }
    print(json.dumps(result_dict, indent=2))

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
