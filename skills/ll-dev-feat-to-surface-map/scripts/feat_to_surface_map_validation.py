from __future__ import annotations

from pathlib import Path
from typing import Any

from feat_to_surface_map_common import ensure_list, load_json, validate_surface_entries

REQUIRED_INPUT_FILES = [
    "package-manifest.json",
    "feat-freeze-bundle.md",
    "feat-freeze-bundle.json",
    "feat-review-report.json",
    "feat-acceptance-report.json",
    "feat-defect-list.json",
    "feat-freeze-gate.json",
    "handoff-to-feat-downstreams.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]

REQUIRED_OUTPUT_FILES = [
    "package-manifest.json",
    "surface-map-bundle.md",
    "surface-map-bundle.json",
    "surface-map-review-report.json",
    "surface-map-defect-list.json",
    "surface-map-freeze-gate.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]


def validate_input_package(input_dir: str | Path, feat_ref: str) -> tuple[list[str], dict[str, Any]]:
    artifacts_dir = Path(input_dir).resolve()
    errors = [f"Missing required input artifact: {name}" for name in REQUIRED_INPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {"valid": False}

    bundle = load_json(artifacts_dir / "feat-freeze-bundle.json")
    gate = load_json(artifacts_dir / "feat-freeze-gate.json")
    feature = next((item for item in ensure_list(bundle.get("features")) if isinstance(item, dict) and str(item.get("feat_ref") or "").strip() == feat_ref), None)
    if bundle.get("artifact_type") != "feat_freeze_package":
        errors.append("artifact_type must be feat_freeze_package.")
    if bundle.get("workflow_key") != "product.epic-to-feat":
        errors.append("workflow_key must be product.epic-to-feat.")
    if str(bundle.get("status") or "") not in {"accepted", "frozen"}:
        errors.append("status must be accepted or frozen.")
    if not gate.get("freeze_ready"):
        errors.append("feat-freeze-gate.json freeze_ready must be true.")
    if feature is None:
        errors.append(f"selected feat_ref not found in bundle: {feat_ref}")
        return errors, {"valid": False}
    for field in ("feat_ref", "title", "goal", "scope", "constraints", "acceptance_checks", "source_refs"):
        if feature.get(field) in (None, "", []):
            errors.append(f"selected FEAT is missing required field: {field}")
    return errors, {
        "valid": not errors,
        "bundle": bundle,
        "feature": dict(feature),
        "feat_ref": feat_ref,
        "selected_feat_ref": feat_ref,
    }


def validate_output_package(artifacts_dir: str | Path) -> tuple[list[str], dict[str, Any]]:
    artifacts_dir = Path(artifacts_dir).resolve()
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Output package not found: {artifacts_dir}"], {"valid": False}

    errors = [f"Missing required output artifact: {name}" for name in REQUIRED_OUTPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {"valid": False}

    bundle = load_json(artifacts_dir / "surface-map-bundle.json")
    review = load_json(artifacts_dir / "surface-map-review-report.json")
    gate = load_json(artifacts_dir / "surface-map-freeze-gate.json")
    validate_bundle_identity(errors, bundle)
    validate_bundle_refs(errors, bundle)
    validate_bundle_payload(errors, bundle)
    validate_review(errors, review)
    validate_gate(errors, gate)
    return errors, {
        "valid": not errors,
        "bundle": bundle,
        "freeze_ready": bool(gate.get("freeze_ready")),
    }


def validate_bundle_identity(errors: list[str], bundle: dict[str, Any]) -> None:
    if bundle.get("artifact_type") != "surface_map_package":
        errors.append("surface-map-bundle.json artifact_type must be surface_map_package.")
    if bundle.get("workflow_key") != "dev.feat-to-surface-map":
        errors.append("surface-map-bundle.json workflow_key must be dev.feat-to-surface-map.")
    if not str(bundle.get("feat_ref") or "").strip():
        errors.append("surface-map-bundle.json must include feat_ref.")
    if not str(bundle.get("surface_map_ref") or "").strip():
        errors.append("surface-map-bundle.json must include surface_map_ref.")


def validate_bundle_refs(errors: list[str], bundle: dict[str, Any]) -> None:
    source_refs = ensure_list(bundle.get("source_refs"))
    if not any(str(ref).startswith("product.epic-to-feat::") for ref in source_refs):
        errors.append("surface-map-bundle.json source_refs must include product.epic-to-feat::<run_id>.")
    if not any(str(ref).startswith("FEAT-") for ref in source_refs):
        errors.append("surface-map-bundle.json source_refs must include FEAT-*.")
    downstream = bundle.get("downstream_handoff") or {}
    if downstream.get("surface_map_ref") != bundle.get("surface_map_ref"):
        errors.append("downstream_handoff.surface_map_ref must match surface_map_ref.")
    if downstream.get("feat_ref") != bundle.get("feat_ref"):
        errors.append("downstream_handoff.feat_ref must match feat_ref.")


def validate_surface_map(errors: list[str], bundle: dict[str, Any]) -> None:
    surface_map = bundle.get("surface_map") or {}
    if not isinstance(surface_map, dict):
        errors.append("surface_map must be an object.")
        return
    for field in ("design_surfaces", "ownership_summary", "create_justification_summary", "owner_binding_status"):
        if field not in surface_map:
            errors.append(f"surface_map is missing required field: {field}")
    design_impact_required = bool(bundle.get("design_impact_required"))
    design_surfaces = surface_map.get("design_surfaces") or {}
    if not isinstance(design_surfaces, dict):
        errors.append("surface_map.design_surfaces must be an object.")
        return
    for surface_name in ("architecture", "api", "ui", "prototype", "tech"):
        entries = design_surfaces.get(surface_name, [])
        if not isinstance(entries, list):
            errors.append(f"surface_map.design_surfaces.{surface_name} must be a list.")
            continue
        validate_surface_entries(errors, {surface_name: entries})
    has_any_entry = any(bool(design_surfaces.get(surface_name)) for surface_name in ("architecture", "api", "ui", "prototype", "tech"))
    if design_impact_required and not has_any_entry:
        errors.append("design_impact_required=true requires at least one design surface entry.")
    if not design_impact_required and not str(surface_map.get("bypass_rationale") or "").strip():
        errors.append("design_impact_required=false requires bypass_rationale.")
    for entry in ensure_list(surface_map.get("create_justification_summary")):
        if not str(entry).strip():
            errors.append("create_justification_summary entries must be non-empty.")


def validate_bundle_payload(errors: list[str], bundle: dict[str, Any]) -> None:
    validate_surface_map(errors, bundle)


def validate_review(errors: list[str], review: dict[str, Any]) -> None:
    if review.get("verdict") not in {"approved", "revise"}:
        errors.append("surface-map-review-report.json verdict must be approved or revise.")
    if review.get("verdict") == "approved" and review.get("blocking_points"):
        errors.append("approved review must not contain blocking_points.")


def validate_gate(errors: list[str], gate: dict[str, Any]) -> None:
    if gate.get("workflow_key") != "dev.feat-to-surface-map":
        errors.append("surface-map-freeze-gate.json workflow_key must be dev.feat-to-surface-map.")
    if not gate.get("freeze_ready"):
        errors.append("surface-map-freeze-gate.json freeze_ready must be true.")
