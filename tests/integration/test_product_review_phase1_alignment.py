from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_REVIEW_PHASE1 = {
    "artifact_family": "src_or_feat",
    "risk_profiles": ["default"],
    "coverage_dimensions": [
        "ssot_alignment",
        "object_completeness",
        "contract_completeness",
        "state_transition_closure",
        "failure_path",
        "testability",
    ],
    "required_checks": [
        "ssot_alignment",
        "object_completeness",
        "contract_completeness",
        "state_transition_closure",
        "failure_path",
        "testability",
    ],
    "gate_block_conditions": [
        "missing_coverage",
        "required_check_not_checked",
        "blocker_count_gt_zero",
    ],
}
PHASE1_HELPERS = (
    (
        "raw_to_src_review_phase1",
        REPO_ROOT / "skills" / "ll-product-raw-to-src" / "scripts" / "raw_to_src_review_phase1.py",
        REPO_ROOT / "skills" / "ll-product-raw-to-src" / "ll.contract.yaml",
    ),
    (
        "src_to_epic_review_phase1",
        REPO_ROOT / "skills" / "ll-product-src-to-epic" / "scripts" / "src_to_epic_review_phase1.py",
        REPO_ROOT / "skills" / "ll-product-src-to-epic" / "ll.contract.yaml",
    ),
    (
        "epic_to_feat_review_phase1",
        REPO_ROOT / "skills" / "ll-product-epic-to-feat" / "scripts" / "epic_to_feat_review_phase1.py",
        REPO_ROOT / "skills" / "ll-product-epic-to-feat" / "ll.contract.yaml",
    ),
)


def _load_helper(module_name: str, helper_path: Path):
    script_dir = str(helper_path.parent)
    repo_root = str(REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(module_name, helper_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contract_review_phase1(contract_path: Path) -> dict[str, object]:
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    assert isinstance(contract, dict)
    review_phase1 = contract.get("review_phase1")
    assert isinstance(review_phase1, dict)
    return review_phase1


def _valid_report() -> dict[str, object]:
    return {
        "coverage": {
            "ssot_alignment": "checked",
            "object_completeness": "checked",
            "contract_completeness": "checked",
            "state_transition_closure": "partial",
            "failure_path": "partial",
            "testability": "partial",
        },
        "required_checks": list(EXPECTED_REVIEW_PHASE1["required_checks"]),
        "blocker_count": 0,
    }


class _SrcToEpicGenerated:
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


class _EpicToFeatGenerated:
    def __init__(self) -> None:
        self.frontmatter = {
            "workflow_run_id": "run-1",
            "epic_freeze_ref": "EPIC-1",
            "src_root_id": "SRC-1",
            "feat_refs": ["FEAT-1", "FEAT-2"],
        }
        self.json_payload = {
            "source_refs": ["product.src-to-epic::run-1", "EPIC-1", "SRC-1"],
            "traceability": {"upstream": ["EPIC-1"]},
            "revision_context": {},
        }
        self.review_report = {"risks": []}
        self.acceptance_report = {"created_at": "2026-04-03T00:00:00Z"}
        self.defect_list: list[dict[str, str]] = []
        self.handoff = {
            "target_workflows": [
                {"workflow": "workflow.dev.feat_to_tech"},
                {"workflow": "workflow.qa.feat_to_testset"},
            ]
        }
        self.semantic_drift_check = {"verdict": "pass", "semantic_lock_preserved": True}


def _assert_default_builder_shape(report: dict[str, object]) -> None:
    assert report["coverage"] == _valid_report()["coverage"]
    assert report["required_checks"] == EXPECTED_REVIEW_PHASE1["required_checks"]
    assert report["blocker_count"] == 0
    assert report["review_phase1"] == EXPECTED_REVIEW_PHASE1


def test_product_review_phase1_contracts_stay_aligned() -> None:
    for _, _, contract_path in PHASE1_HELPERS:
        assert _contract_review_phase1(contract_path) == EXPECTED_REVIEW_PHASE1


def test_product_review_phase1_helpers_stay_aligned() -> None:
    for module_name, helper_path, _ in PHASE1_HELPERS:
        helper = _load_helper(module_name, helper_path)
        assert helper.review_phase1_contract_metadata() == EXPECTED_REVIEW_PHASE1


def test_product_review_phase1_builders_emit_shared_default_shape() -> None:
    raw_helper = _load_helper(PHASE1_HELPERS[0][0], PHASE1_HELPERS[0][1])
    raw_report = raw_helper.build_raw_to_src_document_test_report(
        run_id="run-1",
        candidate={"source_refs": ["ADR-1"], "source_provenance_map": {"ADR-1": "source"}, "revision_context": {}},
        structural_report={"input_valid": True, "intake_valid": True, "issues": []},
        defects=[],
        acceptance_report={"created_at": "2026-04-03T00:00:00Z", "acceptance_findings": []},
        action="next_skill",
        revision_request_ref="",
    )
    _assert_default_builder_shape(raw_report)

    src_helper = _load_helper(PHASE1_HELPERS[1][0], PHASE1_HELPERS[1][1])
    _assert_default_builder_shape(src_helper.build_src_to_epic_document_test_report(_SrcToEpicGenerated()))

    feat_helper = _load_helper(PHASE1_HELPERS[2][0], PHASE1_HELPERS[2][1])
    _assert_default_builder_shape(feat_helper.build_epic_to_feat_document_test_report(_EpicToFeatGenerated()))


def test_product_review_phase1_validators_accept_shared_shape() -> None:
    for module_name, helper_path, _ in PHASE1_HELPERS:
        helper = _load_helper(module_name, helper_path)
        assert helper.validate_review_phase1_fields(_valid_report()) == []


def test_product_review_phase1_validators_reject_missing_coverage() -> None:
    for module_name, helper_path, _ in PHASE1_HELPERS:
        helper = _load_helper(module_name, helper_path)
        errors = helper.validate_review_phase1_fields({"required_checks": list(EXPECTED_REVIEW_PHASE1["required_checks"]), "blocker_count": 0})
        assert any("missing review phase-1 coverage object" in error for error in errors)


def test_product_review_phase1_validators_reject_not_checked() -> None:
    report = _valid_report()
    report["coverage"]["failure_path"] = "not_checked"
    for module_name, helper_path, _ in PHASE1_HELPERS:
        helper = _load_helper(module_name, helper_path)
        errors = helper.validate_review_phase1_fields(report)
        assert any("coverage marks required dimension as not_checked: failure_path" in error for error in errors)


def test_product_review_phase1_validators_reject_positive_blockers() -> None:
    report = _valid_report()
    report["blocker_count"] = 1
    for module_name, helper_path, _ in PHASE1_HELPERS:
        helper = _load_helper(module_name, helper_path)
        errors = helper.validate_review_phase1_fields(report)
        assert any("blocker_count must be 0 for freeze-ready handoff" in error for error in errors)
