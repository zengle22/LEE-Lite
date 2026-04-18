"""Tests for semantic_stability dimension validation in impl_spec_test_skill_guard."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

# Add project root to sys.path for cli.lib imports (if needed)
def _find_project_root() -> Path:
    """Find project root by searching upward for .planning/ directory."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".planning").exists():
            return parent
    raise RuntimeError("Cannot find project root (no .planning/ directory found)")

try:
    PROJECT_ROOT = _find_project_root()
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
except RuntimeError:
    pass  # cli.lib imports handled by try/except in impl_spec_test_skill_guard.py

# Ensure scripts dir is also in path
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
SCRIPTS_DIR_STR = str(SCRIPTS_DIR)
if SCRIPTS_DIR_STR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR_STR)

from impl_spec_test_skill_guard import validate_output  # noqa: E402


def _create_minimal_output_dir(tmp_path: Path, dimension_reviews: dict, verdict: str = "pass",
                                semantic_stability_verdict: str = "pass") -> Path:
    """Create a minimal valid output JSON with all required _ref files."""
    # Write dimension_reviews.json
    dim_reviews_path = tmp_path / "dimension_reviews.json"
    dim_reviews_path.write_text(json.dumps(dimension_reviews, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write review_coverage.json
    review_coverage_path = tmp_path / "review_coverage.json"
    review_coverage_path.write_text(json.dumps({"status": "sufficient"}), encoding="utf-8")

    # Create all other _ref files as empty JSON objects
    for ref_name in [
        "semantic_review", "system_views", "logic_risk_inventory",
        "ux_risk_inventory", "ux_improvement_inventory", "journey_simulation",
        "state_invariant_check", "cross_artifact_trace", "open_questions",
        "false_negative_challenge", "defects",
        "gate_subject", "intake_result", "issue_inventory",
        "counterexample_result", "readiness_verdict", "repair_suggestions",
        "execution_evidence", "supervision_evidence", "skill_ref",
        "runner_skill_ref", "candidate_artifact", "candidate_managed_artifact",
        "candidate_receipt", "candidate_registry_record", "handoff",
        "gate_pending", "report_package", "report_json", "report_markdown",
    ]:
        ref_path = tmp_path / f"{ref_name}.json"
        ref_path.write_text("{}", encoding="utf-8")

    # Build the output JSON
    output = {
        "api_version": "v1",
        "command": "skill.impl-spec-test",
        "request_id": "REQ-001",
        "result_status": "success",
        "status_code": 200,
        "exit_code": 0,
        "message": "OK",
        "data": {
            "skill_ref": "skill.qa.impl_spec_test",
            "runner_skill_ref": "skill.runner.impl_spec_test",
            "candidate_artifact_ref": f"{tmp_path / 'candidate_artifact.json'}",
            "candidate_managed_artifact_ref": f"{tmp_path / 'candidate_managed_artifact.json'}",
            "candidate_receipt_ref": f"{tmp_path / 'candidate_receipt.json'}",
            "candidate_registry_record_ref": f"{tmp_path / 'candidate_registry_record.json'}",
            "handoff_ref": f"{tmp_path / 'handoff.json'}",
            "gate_pending_ref": f"{tmp_path / 'gate_pending.json'}",
            "run_status": "completed",
            "verdict": verdict,
            "implementation_readiness": "ready",
            "self_contained_readiness": "sufficient",
            "self_contained_evaluation_mode": "full",
            "recommended_next_action": "proceed_to_coding",
            "recommended_actor": "coder",
            "repair_target_artifact": None,
            "execution_mode": "standard",
            "report_package_ref": f"{tmp_path / 'report_package.json'}",
            "report_json_ref": f"{tmp_path / 'report_json.json'}",
            "report_markdown_ref": f"{tmp_path / 'report_markdown.json'}",
            "semantic_review_ref": f"{tmp_path / 'semantic_review.json'}",
            "system_views_ref": f"{tmp_path / 'system_views.json'}",
            "logic_risk_inventory_ref": f"{tmp_path / 'logic_risk_inventory.json'}",
            "ux_risk_inventory_ref": f"{tmp_path / 'ux_risk_inventory.json'}",
            "ux_improvement_inventory_ref": f"{tmp_path / 'ux_improvement_inventory.json'}",
            "journey_simulation_ref": f"{tmp_path / 'journey_simulation.json'}",
            "state_invariant_check_ref": f"{tmp_path / 'state_invariant_check.json'}",
            "cross_artifact_trace_ref": f"{tmp_path / 'cross_artifact_trace.json'}",
            "open_questions_ref": f"{tmp_path / 'open_questions.json'}",
            "false_negative_challenge_ref": f"{tmp_path / 'false_negative_challenge.json'}",
            "dimension_reviews_ref": str(dim_reviews_path),
            "review_coverage_ref": str(review_coverage_path),
            "defects_ref": f"{tmp_path / 'defects.json'}",
            "gate_subject_ref": f"{tmp_path / 'gate_subject.json'}",
            "intake_result_ref": f"{tmp_path / 'intake_result.json'}",
            "issue_inventory_ref": f"{tmp_path / 'issue_inventory.json'}",
            "counterexample_result_ref": f"{tmp_path / 'counterexample_result.json'}",
            "readiness_verdict_ref": f"{tmp_path / 'readiness_verdict.json'}",
            "repair_suggestions_ref": f"{tmp_path / 'repair_suggestions.json'}",
            "execution_evidence_ref": f"{tmp_path / 'execution_evidence.json'}",
            "supervision_evidence_ref": f"{tmp_path / 'supervision_evidence.json'}",
        },
    }

    output_path = tmp_path / "output.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


_VALID_DIMENSION_REVIEWS = {
    "functional_logic": {"verdict": "pass", "checked": True},
    "data_modeling": {"verdict": "pass", "checked": True},
    "user_journey": {"verdict": "pass", "checked": True},
    "ui_usability": {"verdict": "pass", "checked": True},
    "api_contract": {"verdict": "pass", "checked": True},
    "implementation_executability": {"verdict": "pass", "checked": True},
    "testability": {"verdict": "pass", "checked": True},
    "migration_compatibility": {"verdict": "pass", "checked": True},
    "semantic_stability": {
        "checked": True,
        "frz_refs": ["FRZ-001"],
        "anchors_checked": ["JRN-001", "ENT-001", "SM-001"],
        "semantic_drift": {
            "has_drift": False,
            "drift_results": [],
            "classification": "ok",
        },
        "verdict": "pass",
    },
}


def test_valid_9_dimension_passes(tmp_path: Path) -> None:
    """All 9 dimensions present, semantic_stability verdict pass, has_drift=False --> validate_output returns 0."""
    output_path = _create_minimal_output_dir(tmp_path, _VALID_DIMENSION_REVIEWS, verdict="pass")
    assert validate_output(output_path) == 0


def test_missing_semantic_stability_raises(tmp_path: Path) -> None:
    """dimension_reviews.json missing 'semantic_stability' key --> ValueError with '9 dimensions' in message."""
    dim_reviews = {k: v for k, v in _VALID_DIMENSION_REVIEWS.items() if k != "semantic_stability"}
    output_path = _create_minimal_output_dir(tmp_path, dim_reviews)
    with pytest.raises(ValueError, match="9 dimensions"):
        validate_output(output_path)


def test_missing_semantic_drift_field_raises(tmp_path: Path) -> None:
    """semantic_stability present but missing 'semantic_drift' --> ValueError."""
    dim_reviews = deepcopy(_VALID_DIMENSION_REVIEWS)
    dim_reviews["semantic_stability"] = {
        "checked": True,
        "frz_refs": ["FRZ-001"],
        "verdict": "pass",
    }
    output_path = _create_minimal_output_dir(tmp_path, dim_reviews)
    with pytest.raises(ValueError, match="semantic_stability.*semantic_drift"):
        validate_output(output_path)


def test_missing_has_drift_field_raises(tmp_path: Path) -> None:
    """semantic_drift present but missing 'has_drift' --> ValueError."""
    dim_reviews = deepcopy(_VALID_DIMENSION_REVIEWS)
    dim_reviews["semantic_stability"]["semantic_drift"] = {
        "drift_results": [],
        "classification": "ok",
    }
    output_path = _create_minimal_output_dir(tmp_path, dim_reviews)
    with pytest.raises(ValueError, match="has_drift"):
        validate_output(output_path)


def test_drift_without_block_verdict_raises(tmp_path: Path) -> None:
    """has_drift=True but verdict='pass' --> ValueError."""
    dim_reviews = deepcopy(_VALID_DIMENSION_REVIEWS)
    dim_reviews["semantic_stability"]["semantic_drift"]["has_drift"] = True
    dim_reviews["semantic_stability"]["semantic_drift"]["drift_results"] = [
        {"anchor_id": "JRN-001", "drift_type": "tampered", "detail": "changed semantics"}
    ]
    dim_reviews["semantic_stability"]["verdict"] = "pass"
    output_path = _create_minimal_output_dir(tmp_path, dim_reviews)
    with pytest.raises(ValueError, match="semantic_stability verdict.*block"):
        validate_output(output_path)


def test_overall_pass_with_semantic_block_raises(tmp_path: Path) -> None:
    """overall verdict='pass' but semantic_stability verdict='block' --> ValueError."""
    dim_reviews = deepcopy(_VALID_DIMENSION_REVIEWS)
    dim_reviews["semantic_stability"]["verdict"] = "block"
    dim_reviews["semantic_stability"]["semantic_drift"]["has_drift"] = True
    output_path = _create_minimal_output_dir(tmp_path, dim_reviews, verdict="pass")
    with pytest.raises(ValueError, match="overall verdict.*pass.*semantic_stability.*block"):
        validate_output(output_path)


def test_pass_with_revisions_allowed(tmp_path: Path) -> None:
    """overall verdict='pass_with_revisions' and semantic_stability verdict='pass' --> passes."""
    dim_reviews = deepcopy(_VALID_DIMENSION_REVIEWS)
    dim_reviews["semantic_stability"]["verdict"] = "pass"
    output_path = _create_minimal_output_dir(tmp_path, dim_reviews, verdict="pass_with_revisions")
    assert validate_output(output_path) == 0
