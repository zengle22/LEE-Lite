from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from epic_to_feat_review_phase1 import build_epic_to_feat_document_test_report
from epic_to_feat_runtime import REQUIRED_OUTPUT_FILES, validate_output_package


class _Generated:
    def __init__(self) -> None:
        self.frontmatter = {"workflow_run_id": "run-1", "epic_freeze_ref": "EPIC-1", "src_root_id": "SRC-1", "feat_refs": ["FEAT-1", "FEAT-2"]}
        self.json_payload = {
            "source_refs": ["product.src-to-epic::run-1", "EPIC-1", "SRC-1"],
            "traceability": {"upstream": ["EPIC-1"]},
            "revision_context": {},
            "integration_context": {
                "artifact_type": "integration_context",
                "schema_version": "1.0.0",
                "context_ref": "integration-context.json",
                "workflow_inventory": ["workflow.dev.feat_to_tech"],
                "module_boundaries": ["ll-product-epic-to-feat owns FEAT decomposition"],
                "legacy_fields_states_interfaces": ["FEAT-1 authoritative artifact is feat-freeze-bundle.md"],
                "canonical_ownership": ["FEAT bundle owns product-slice semantics"],
                "compatibility_constraints": ["Downstream TECH must preserve glossary and dependency map semantics"],
                "migration_modes": ["extend"],
                "legacy_invariants": ["Preserve FEAT lineage across downstream derivation"],
                "gate_audit_evidence": ["feat-freeze-gate.json passes before downstream derivation"],
                "source_refs": ["product.src-to-epic::run-1", "EPIC-1", "SRC-1"],
            },
        }
        self.review_report = {"risks": []}
        self.acceptance_report = {"created_at": "2026-04-03T00:00:00Z"}
        self.defect_list: list[dict[str, str]] = []
        self.handoff = {
            "target_workflows": [
                {"workflow": "workflow.dev.feat_to_tech"},
                {"workflow": "workflow.qa.feat_to_testset"},
            ],
            "integration_context_ref": "integration-context.json",
            "design_gate_required": True,
        }
        self.semantic_drift_check = {"verdict": "pass", "semantic_lock_preserved": True}


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _feature(feat_ref: str, title: str) -> dict[str, object]:
    return {
        "feat_ref": feat_ref,
        "title": title,
        "slice_id": f"{feat_ref.lower()}-slice",
        "acceptance_checks": ["a", "b", "c"],
        "constraints": ["c1", "c2", "c3", "c4"],
        "scope": ["s1", "s2", "s3"],
        "upstream_feat": "",
        "downstream_feat": "",
        "consumes": [],
        "produces": [],
        "authoritative_artifact": "feat-freeze-bundle.md",
        "gate_decision_dependency_feat_refs": [],
        "gate_decision_dependency": "none",
        "admission_dependency_feat_refs": [],
        "admission_dependency": "none",
        "dependency_kinds": [],
        "design_impact_required": True,
        "candidate_design_surfaces": ["architecture", "tech"],
        "surface_map_required_reason": "This FEAT updates shared design assets and must resolve ownership before design derivation.",
        "design_surfaces": {
            "architecture": [
                {
                    "owner": "ARCH-SRC-1-CORE",
                    "action": "create",
                    "scope": ["boundary"],
                    "reason": "need a stable architecture owner",
                    "create_signals": ["new long-lived owner", "future multi-feat reuse"],
                }
            ],
            "tech": [
                {
                    "owner": "TECH-1",
                    "action": "update",
                    "scope": ["strategy"],
                    "reason": "existing tech package continues to own implementation strategy",
                }
            ],
        },
        "ui_required": False,
        "business_value": "business value",
        "identity_and_scenario": {
            "user_story": "As a user, I need this feat.",
            "trigger": "User starts the flow.",
            "product_interface": "Console",
            "completed_state": "Flow succeeds.",
        },
        "business_flow": {"main_flow": ["step1", "step2", "step3"]},
        "product_objects_and_deliverables": {
            "authoritative_output": "Output artifact",
            "business_deliverable": "Deliverable",
        },
        "collaboration_and_timeline": {
            "business_sequence": "Business sequence",
            "loop_gate_human_involvement": ["gate review"],
        },
        "acceptance_and_testability": {"test_dimensions": ["d1", "d2", "d3", "d4"]},
        "frozen_downstream_boundary": {
            "frozen_product_shape": ["shape"],
            "open_technical_decisions": ["decision"],
        },
    }


def _markdown_with_required_headings() -> str:
    headings = (
        "FEAT Bundle Intent",
        "EPIC Context",
        "Canonical Glossary",
        "Boundary Matrix",
        "FEAT Inventory",
        "Prohibited Inference Rules",
        "Acceptance and Review",
        "Downstream Handoff",
        "Traceability",
    )
    parts = [f"## {heading}\ncontent" for heading in headings]
    parts.extend(
        [
            "#### Identity and Scenario\ncontent",
            "#### Business Flow\ncontent",
            "#### Product Objects and Deliverables\ncontent",
            "#### Collaboration and Timeline\ncontent",
            "#### Acceptance and Testability\ncontent",
            "#### Frozen Downstream Boundary\ncontent",
        ]
    )
    return "---\nstatus: accepted\n---\n\n" + "\n\n".join(parts) + "\n"


def _minimal_feat_bundle_json() -> dict[str, object]:
    features = [_feature("FEAT-1", "Feature one"), _feature("FEAT-2", "Feature two")]
    return {
        "artifact_type": "feat_freeze_package",
        "workflow_key": "product.epic-to-feat",
        "epic_freeze_ref": "EPIC-1",
        "src_root_id": "SRC-1",
        "feat_refs": ["FEAT-1", "FEAT-2"],
        "source_refs": ["product.src-to-epic::run-1", "EPIC-1", "SRC-1"],
        "downstream_workflows": ["workflow.dev.feat_to_tech", "workflow.qa.feat_to_testset"],
        "features": features,
        "boundary_matrix": [{"feat_ref": "FEAT-1"}, {"feat_ref": "FEAT-2"}],
        "bundle_shared_non_goals": ["non-goal"],
        "bundle_acceptance_conventions": ["convention"],
        "glossary": [{"term": "EPIC", "definition": "epic"}],
        "prohibited_inference_rules": ["rule"],
        "integration_context": {
            "artifact_type": "integration_context",
            "schema_version": "1.0.0",
            "context_ref": "integration-context.json",
            "workflow_inventory": ["workflow.dev.feat_to_tech"],
            "module_boundaries": ["ll-product-epic-to-feat owns FEAT decomposition"],
            "legacy_fields_states_interfaces": ["FEAT-1 authoritative artifact is feat-freeze-bundle.md"],
            "canonical_ownership": ["FEAT bundle owns product-slice semantics"],
            "compatibility_constraints": ["Downstream TECH must preserve glossary and dependency map semantics"],
            "migration_modes": ["extend"],
            "legacy_invariants": ["Preserve FEAT lineage across downstream derivation"],
            "gate_audit_evidence": ["feat-freeze-gate.json passes before downstream derivation"],
            "source_refs": ["product.src-to-epic::run-1", "EPIC-1", "SRC-1"],
        },
    }


def _minimal_handoff() -> dict[str, object]:
    return {
        "glossary": [{"term": "EPIC", "definition": "epic"}],
        "prohibited_inference_rules": ["rule"],
        "authoritative_artifact_map": [{"feat_ref": "FEAT-1", "artifact": "feat-freeze-bundle.md"}],
        "feature_dependency_map": [{"feat_ref": "FEAT-1", "upstream_feat": "", "downstream_feat": ""}],
        "target_workflows": [
            {"workflow": "workflow.dev.feat_to_tech"},
            {"workflow": "workflow.qa.feat_to_testset"},
        ],
        "integration_context_ref": "integration-context.json",
        "design_gate_required": True,
    }


def _write_minimal_output_package(artifacts_dir: Path, *, document_test_report: dict[str, object]) -> None:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for filename in REQUIRED_OUTPUT_FILES:
        path = artifacts_dir / filename
        if filename.endswith(".md"):
            path.write_text(_markdown_with_required_headings(), encoding="utf-8")
        else:
            _write_json(path, {})

    _write_json(artifacts_dir / "feat-freeze-bundle.json", _minimal_feat_bundle_json())
    _write_json(artifacts_dir / "integration-context.json", _minimal_feat_bundle_json()["integration_context"])
    _write_json(artifacts_dir / "feat-review-report.json", {"risks": []})
    _write_json(artifacts_dir / "feat-acceptance-report.json", {"decision": "approve"})
    _write_json(artifacts_dir / "feat-defect-list.json", [])
    _write_json(artifacts_dir / "document-test-report.json", document_test_report)
    _write_json(artifacts_dir / "handoff-to-feat-downstreams.json", _minimal_handoff())
    _write_json(artifacts_dir / "semantic-drift-check.json", {"semantic_lock_present": False, "semantic_lock_preserved": True})
    _write_json(artifacts_dir / "feat-freeze-gate.json", {"epic_freeze_ref": "EPIC-1", "checks": {"review_phase1_ready": True}})
    _write_json(artifacts_dir / "execution-evidence.json", {"run_id": "run-1"})
    _write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})

    surface_map_ref = "SURFACE-MAP-FEAT-1"
    bundle_ref = f"surface-map-bundle__{surface_map_ref}.json"
    _write_json(
        artifacts_dir / bundle_ref,
        {
            "artifact_type": "surface_map_package",
            "schema_version": "1.0.0",
            "workflow_key": "dev.feat-to-surface-map",
            "workflow_run_id": "run-1",
            "status": "accepted",
            "feat_ref": "FEAT-1",
            "surface_map_ref": surface_map_ref,
        },
    )
    _write_json(
        artifacts_dir / "surface-map-index.json",
        {
            "artifact_type": "surface_map_index",
            "schema_version": "1.0.0",
            "surface_map_ref": surface_map_ref,
            "entries": [{"feat_ref": "FEAT-1", "surface_map_ref": surface_map_ref, "bundle_ref": bundle_ref}],
        },
    )


def test_build_epic_to_feat_document_test_report_emits_phase1_fields() -> None:
    report = build_epic_to_feat_document_test_report(_Generated())

    assert report["coverage"] == {
        "ssot_alignment": "checked",
        "object_completeness": "checked",
        "contract_completeness": "checked",
        "state_transition_closure": "partial",
        "failure_path": "partial",
        "testability": "partial",
    }
    assert report["required_checks"] == [
        "ssot_alignment",
        "object_completeness",
        "contract_completeness",
        "state_transition_closure",
        "failure_path",
        "testability",
    ]
    assert report["blocker_count"] == 0
    assert report["review_phase1"]["artifact_family"] == "src_or_feat"


def test_validate_output_package_rejects_missing_phase1_coverage(tmp_path: Path) -> None:
    report = build_epic_to_feat_document_test_report(_Generated())
    report.pop("coverage", None)
    _write_minimal_output_package(tmp_path, document_test_report=report)

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("missing review phase-1 coverage object" in error for error in errors)


def test_validate_output_package_rejects_phase1_not_checked(tmp_path: Path) -> None:
    report = build_epic_to_feat_document_test_report(_Generated())
    report["coverage"]["failure_path"] = "not_checked"
    _write_minimal_output_package(tmp_path, document_test_report=report)

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("coverage marks required dimension as not_checked: failure_path" in error for error in errors)


def test_validate_output_package_rejects_positive_phase1_blocker_count(tmp_path: Path) -> None:
    report = build_epic_to_feat_document_test_report(_Generated())
    report["blocker_count"] = 1
    _write_minimal_output_package(tmp_path, document_test_report=report)

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("blocker_count must be 0 for freeze-ready handoff" in error for error in errors)


def test_validate_output_package_requires_design_surface_signals(tmp_path: Path) -> None:
    report = build_epic_to_feat_document_test_report(_Generated())
    _write_minimal_output_package(tmp_path, document_test_report=report)
    bundle_path = tmp_path / "feat-freeze-bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["features"][0].pop("design_impact_required", None)
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("must include design_impact_required" in error for error in errors)


def test_validate_output_package_rejects_create_without_two_signals(tmp_path: Path) -> None:
    report = build_epic_to_feat_document_test_report(_Generated())
    _write_minimal_output_package(tmp_path, document_test_report=report)
    bundle_path = tmp_path / "feat-freeze-bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["features"][0]["design_surfaces"]["architecture"][0]["create_signals"] = ["new long-lived owner"]
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("create requires at least two create_signals" in error for error in errors)
