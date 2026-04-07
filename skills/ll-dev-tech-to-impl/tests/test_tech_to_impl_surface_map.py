from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from tech_to_impl_common import load_tech_package  # noqa: E402
from tech_to_impl_derivation import build_refs  # noqa: E402
from tech_to_impl_validation import validate_input_package  # noqa: E402


def _write_required_file(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_minimal_package(root: Path, *, surface_map_ref: str | None) -> Path:
    pkg = root / "tech-package"
    pkg.mkdir(parents=True, exist_ok=True)
    selected_feat = {
        "feat_ref": "FEAT-001",
        "title": "Daily adjustment",
        "goal": "Keep the plan fresh.",
        "scope": ["adjustment"],
        "constraints": ["freeze boundary"],
        "design_impact_required": True,
    }
    if surface_map_ref:
        selected_feat["surface_map_ref"] = surface_map_ref
    bundle = {
        "artifact_type": "tech_design_package",
        "workflow_key": "dev.feat-to-tech",
        "workflow_run_id": "tech-run-1",
        "status": "accepted",
        "schema_version": "1.0.0",
        "feat_ref": "FEAT-001",
        "tech_ref": "TECH-001",
        "surface_map_ref": surface_map_ref,
        "selected_feat": selected_feat,
        "need_assessment": {
            "integration_context_sufficient": True,
            "stateful_design_present": True,
        },
        "integration_sufficiency_check": {"passed": True},
        "downstream_handoff": {
            "integration_context_ref": "INTEGRATION-CTX-001",
            "canonical_owner_refs": ["OWNER-001"],
            "state_machine_ref": "STATE-001",
            "nfr_constraints_ref": "NFR-001",
            "migration_constraints_ref": "MIG-001",
            "algorithm_constraint_refs": ["ALG-001"],
        },
        "source_refs": ["FEAT-001", "TECH-001", "EPIC-001", "SRC-001"],
    }
    _write_required_file(pkg / "package-manifest.json", {})
    (pkg / "tech-design-bundle.md").write_text("---\nkind: tech\n---\n# Tech\n", encoding="utf-8")
    _write_required_file(pkg / "tech-design-bundle.json", bundle)
    _write_required_file(pkg / "tech-spec.md", {"sections": []})
    _write_required_file(pkg / "integration-context.json", {"context": "stub"})
    _write_required_file(pkg / "tech-review-report.json", {})
    _write_required_file(pkg / "tech-acceptance-report.json", {})
    _write_required_file(pkg / "tech-defect-list.json", {})
    _write_required_file(pkg / "tech-freeze-gate.json", {"freeze_ready": True})
    _write_required_file(
        pkg / "handoff-to-tech-impl.json",
        {
            "target_workflow": "workflow.dev.tech_to_impl",
            "integration_context_ref": "INTEGRATION-CTX-001",
            "canonical_owner_refs": ["OWNER-001"],
            "state_machine_ref": "STATE-001",
            "nfr_constraints_ref": "NFR-001",
            "migration_constraints_ref": "MIG-001",
            "algorithm_constraint_refs": ["ALG-001"],
        },
    )
    _write_required_file(pkg / "execution-evidence.json", {"ok": True})
    _write_required_file(pkg / "supervision-evidence.json", {"ok": True})
    return pkg


def test_validate_input_requires_surface_map_for_design_impact(tmp_path: Path) -> None:
    pkg = _write_minimal_package(tmp_path, surface_map_ref=None)

    errors, result = validate_input_package(pkg, "FEAT-001", "TECH-001", tmp_path)

    assert errors
    assert "surface_map_ref is required" in errors[0]
    assert result["valid"] is False


def test_validate_input_exposes_surface_map_ref_when_present(tmp_path: Path) -> None:
    pkg = _write_minimal_package(tmp_path, surface_map_ref="SURFACE-MAP-001")

    errors, result = validate_input_package(pkg, "FEAT-001", "TECH-001", tmp_path)
    package = load_tech_package(pkg)
    refs = build_refs(package)

    assert not errors
    assert result["surface_map_ref"] == "SURFACE-MAP-001"
    assert refs["surface_map_ref"] == "SURFACE-MAP-001"

