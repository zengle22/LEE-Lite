from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src_to_epic_review_phase1 import build_src_to_epic_document_test_report
from src_to_epic_runtime import REQUIRED_OUTPUT_FILES, validate_output_package


class _Generated:
    def __init__(self) -> None:
        self.json_payload = {
            "source_refs": ["product.raw-to-src::run-1", "SRC-1"],
            "traceability": {"upstream": ["SRC-1"]},
            "revision_context": {},
        }
        self.defect_list: list[dict[str, str]] = []
        self.frontmatter = {"workflow_run_id": "run-1"}
        self.acceptance_report = {"created_at": "2026-04-03T00:00:00Z"}
        self.semantic_drift_check = {"verdict": "pass", "semantic_lock_preserved": True}
        self.review_report = {"risks": []}


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _markdown_with_required_headings() -> str:
    headings = (
        "Epic Intent",
        "Business Goal",
        "Business Value and Problem",
        "Product Positioning",
        "Actors and Roles",
        "Capability Scope",
        "Upstream and Downstream",
        "Epic Success Criteria",
        "Non-Goals",
        "Decomposition Rules",
        "Rollout and Adoption",
        "Constraints and Dependencies",
        "Acceptance and Review",
        "Downstream Handoff",
        "Traceability",
    )
    body = "\n\n".join(f"## {heading}\ncontent" for heading in headings)
    return f"---\nstatus: accepted\n---\n\n{body}\n"


def _minimal_epic_freeze_json() -> dict[str, object]:
    return {
        "artifact_type": "epic_freeze_package",
        "workflow_key": "product.src-to-epic",
        "downstream_workflow": "product.epic-to-feat",
        "epic_freeze_ref": "EPIC-1",
        "src_root_id": "SRC-1",
        "source_refs": ["product.raw-to-src::run-1", "SRC-1"],
        "rollout_requirement": {"required": False},
        "rollout_plan": {"required_feat_tracks": []},
        "constraint_groups": [
            {"name": "Epic-level constraints", "items": ["Keep the EPIC at capability boundary level."]},
            {"name": "Authoritative inherited constraints", "items": ["Preserve upstream SRC constraints."]},
            {"name": "Downstream preservation rules", "items": ["Keep the output decomposable to FEATs."]},
        ],
        "decomposition_rules": [
            "产品行为切片 are the primary FEAT decomposition unit.",
            "Capability axes remain cross-cutting constraints instead of direct FEATs.",
            "Rollout families remain mandatory overlays for downstream FEAT planning.",
        ],
        "product_behavior_slices": [{"name": "slice-1", "goal": "support decomposition"}],
        "business_value_problem": ["Clarify the product problem and value."],
        "product_positioning": "A capability-boundary EPIC.",
        "actors_and_roles": [{"actor": "Operator", "role": "owns rollout"}],
        "upstream_and_downstream": ["Upstream SRC package", "Downstream FEAT workflow"],
        "epic_success_criteria": ["The EPIC stays decomposable to FEAT packages."],
        "success_metrics": [
            "producer -> consumer -> audit -> gate",
            "formal publish",
            "adoption / cutover / fallback",
        ],
        "constraints_and_dependencies": [],
        "semantic_lock": {},
    }


def _write_minimal_output_package(artifacts_dir: Path, *, document_test_report: dict[str, object]) -> None:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for filename in REQUIRED_OUTPUT_FILES:
        path = artifacts_dir / filename
        if filename.endswith(".md"):
            path.write_text(_markdown_with_required_headings(), encoding="utf-8")
        else:
            _write_json(path, {})

    _write_json(artifacts_dir / "epic-freeze.json", _minimal_epic_freeze_json())
    _write_json(artifacts_dir / "epic-review-report.json", {"risks": []})
    _write_json(artifacts_dir / "epic-acceptance-report.json", {"decision": "approve"})
    _write_json(artifacts_dir / "epic-defect-list.json", [])
    _write_json(artifacts_dir / "document-test-report.json", document_test_report)
    _write_json(artifacts_dir / "handoff-to-epic-to-feat.json", {"to_skill": "product.epic-to-feat"})
    _write_json(artifacts_dir / "semantic-drift-check.json", {"semantic_lock_present": False, "semantic_lock_preserved": True})
    _write_json(artifacts_dir / "epic-freeze-gate.json", {"epic_freeze_ref": "EPIC-1", "checks": {"review_phase1_ready": True}})
    _write_json(artifacts_dir / "execution-evidence.json", {"run_id": "run-1"})
    _write_json(artifacts_dir / "supervision-evidence.json", {"decision": "pass"})


def test_build_src_to_epic_document_test_report_emits_phase1_fields() -> None:
    report = build_src_to_epic_document_test_report(_Generated())

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
    report = build_src_to_epic_document_test_report(_Generated())
    report.pop("coverage", None)
    _write_minimal_output_package(tmp_path, document_test_report=report)

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("missing review phase-1 coverage object" in error for error in errors)


def test_validate_output_package_rejects_phase1_not_checked(tmp_path: Path) -> None:
    report = build_src_to_epic_document_test_report(_Generated())
    report["coverage"]["failure_path"] = "not_checked"
    _write_minimal_output_package(tmp_path, document_test_report=report)

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("coverage marks required dimension as not_checked: failure_path" in error for error in errors)


def test_validate_output_package_rejects_positive_phase1_blocker_count(tmp_path: Path) -> None:
    report = build_src_to_epic_document_test_report(_Generated())
    report["blocker_count"] = 1
    _write_minimal_output_package(tmp_path, document_test_report=report)

    errors, result = validate_output_package(tmp_path)

    assert result["valid"] is False
    assert any("blocker_count must be 0 for freeze-ready handoff" in error for error in errors)
