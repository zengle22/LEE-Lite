"""Unit tests for cli.lib.qa_schemas validators.

Fixtures live in tests/qa_schema/fixtures/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.lib.qa_schemas import (
    ApiCoverageManifest,
    ApiTestPlan,
    ApiTestSpec,
    EvidenceCompleteness,
    GateEvaluation,
    ManifestItem,
    QaSchemaError,
    SettlementReport,
    Summary,
    Verdict,
    validate_file,
    validate_manifest,
    validate_plan,
    validate_settlement,
    validate_spec,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ===========================================================================
# validate_plan
# ===========================================================================


class TestValidatePlan:
    def test_valid_plan_from_file(self) -> None:
        result = validate_file(FIXTURES / "valid_plan.yaml", "plan")
        assert isinstance(result, ApiTestPlan)
        assert result.feature_id == "feat.training-plan"
        assert len(result.source_feat_refs) == 2
        assert len(result.api_objects) == 2
        assert result.api_objects[0].name == "training_plan"
        assert "create_plan" in result.api_objects[0].capabilities
        assert "create_plan" in result.priorities.p0
        assert "get_plan" in result.priorities.p1
        assert len(result.cut_records) == 1

    def test_missing_feature_id(self) -> None:
        with pytest.raises(QaSchemaError, match="feature_id"):
            validate_plan({"source_feat_refs": ["x"], "api_objects": [], "priorities": {}})

    def test_empty_source_feat_refs(self) -> None:
        with pytest.raises(QaSchemaError, match="source_feat_refs"):
            validate_plan(
                {"feature_id": "x", "source_feat_refs": [], "api_objects": [], "priorities": {}}
            )

    def test_empty_api_objects(self) -> None:
        plan = validate_plan(
            {
                "feature_id": "x",
                "source_feat_refs": ["a"],
                "api_objects": [],
                "priorities": {"p0": ["cap"]},
            }
        )
        assert plan.api_objects == []

    def test_api_object_without_capabilities(self) -> None:
        with pytest.raises(QaSchemaError, match="capabilities"):
            validate_plan(
                {
                    "feature_id": "x",
                    "source_feat_refs": ["a"],
                    "api_objects": [{"name": "obj", "capabilities": []}],
                    "priorities": {"p0": []},
                }
            )

    def test_no_priorities_at_all(self) -> None:
        with pytest.raises(QaSchemaError, match="at least one of priorities.p0 or p1"):
            validate_plan(
                {
                    "feature_id": "x",
                    "source_feat_refs": ["a"],
                    "api_objects": [{"name": "o", "capabilities": ["c"]}],
                    "priorities": {},
                }
            )

    def test_cut_records_optional(self) -> None:
        plan = validate_plan(
            {
                "feature_id": "x",
                "source_feat_refs": ["a"],
                "api_objects": [{"name": "o", "capabilities": ["c"]}],
                "priorities": {"p0": ["c"]},
            }
        )
        assert plan.cut_records == []


# ===========================================================================
# validate_manifest
# ===========================================================================


class TestValidateManifest:
    def test_valid_manifest_from_file(self) -> None:
        result = validate_file(FIXTURES / "valid_manifest.yaml", "manifest")
        assert isinstance(result, ApiCoverageManifest)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.coverage_id == "api.plan.create.happy"
        assert item.lifecycle_status == "designed"
        assert item.mapping_status == "unmapped"
        assert item.evidence_status == "missing"
        assert item.waiver_status == "none"

    def test_invalid_priority(self) -> None:
        with pytest.raises(QaSchemaError, match="priority"):
            validate_manifest(
                {
                    "items": [
                        {
                            "coverage_id": "x",
                            "feature_id": "f",
                            "capability": "c",
                            "endpoint": "GET /x",
                            "scenario_type": "happy",
                            "priority": "P99",
                            "source_feat_ref": "r",
                        }
                    ]
                }
            )

    def test_invalid_lifecycle_status(self) -> None:
        with pytest.raises(QaSchemaError, match="lifecycle_status"):
            validate_manifest(
                {
                    "items": [
                        {
                            "coverage_id": "x",
                            "feature_id": "f",
                            "capability": "c",
                            "endpoint": "GET /x",
                            "scenario_type": "happy",
                            "priority": "P0",
                            "source_feat_ref": "r",
                            "lifecycle_status": "invalid_status",
                        }
                    ]
                }
            )

    def test_empty_manifest_is_valid(self) -> None:
        result = validate_manifest({"items": []})
        assert result.items == []

    def test_defaults_applied(self) -> None:
        result = validate_manifest(
            {
                "items": [
                    {
                        "coverage_id": "x",
                        "feature_id": "f",
                        "capability": "c",
                        "endpoint": "GET /x",
                        "scenario_type": "happy",
                        "priority": "P0",
                        "source_feat_ref": "r",
                    }
                ]
            }
        )
        item = result.items[0]
        assert item.lifecycle_status == "designed"
        assert item.mapping_status == "unmapped"
        assert item.evidence_status == "missing"
        assert item.waiver_status == "none"
        assert item.rerun_count == 0
        assert item.obsolete is False


# ===========================================================================
# validate_spec
# ===========================================================================


class TestValidateSpec:
    def test_valid_spec_from_file(self) -> None:
        result = validate_file(FIXTURES / "valid_spec.yaml", "spec")
        assert isinstance(result, ApiTestSpec)
        assert result.case_id == "api_case.plan.create.invalid-date-range"
        assert result.expected is not None
        assert result.expected.status_code == 400
        assert len(result.expected.response_assertions) == 2
        assert result.request is not None
        assert result.request.body is not None
        assert result.request.body["start_date"] == "2026-04-10"

    def test_missing_case_id(self) -> None:
        with pytest.raises(QaSchemaError, match="case_id"):
            validate_spec({"coverage_id": "x", "endpoint": "GET /x", "capability": "c"})

    def test_missing_expected(self) -> None:
        with pytest.raises(QaSchemaError, match="expected"):
            validate_spec(
                {"case_id": "x", "coverage_id": "x", "endpoint": "GET /x", "capability": "c"}
            )

    def test_status_code_must_be_int(self) -> None:
        with pytest.raises(QaSchemaError, match="status_code"):
            validate_spec(
                {
                    "case_id": "x",
                    "coverage_id": "x",
                    "endpoint": "GET /x",
                    "capability": "c",
                    "expected": {"status_code": "400"},
                }
            )

    def test_request_optional(self) -> None:
        result = validate_spec(
            {
                "case_id": "x",
                "coverage_id": "x",
                "endpoint": "GET /x",
                "capability": "c",
                "expected": {"status_code": 200},
            }
        )
        assert result.request is None

    def test_evidence_required_defaults(self) -> None:
        result = validate_spec(
            {
                "case_id": "x",
                "coverage_id": "x",
                "endpoint": "GET /x",
                "capability": "c",
                "expected": {"status_code": 200},
            }
        )
        assert result.evidence_required == []


# ===========================================================================
# validate_settlement
# ===========================================================================


class TestValidateSettlement:
    def test_valid_settlement_from_file(self) -> None:
        result = validate_file(FIXTURES / "valid_settlement.yaml", "settlement")
        assert isinstance(result, SettlementReport)
        assert result.chain == "api"
        assert result.summary.total_coverage_item_count == 8
        assert result.summary.passed_count == 6
        assert result.verdict is not None
        assert result.verdict.conclusion == "conditional_pass"
        assert result.gate_evaluation is not None
        assert result.gate_evaluation.gate_result == "conditional_pass"
        assert len(result.gap_list) == 1

    def test_invalid_chain(self) -> None:
        with pytest.raises(QaSchemaError, match="chain"):
            validate_settlement(
                {
                    "chain": "invalid",
                    "summary": {
                        "total_capability_count": 0,
                        "total_coverage_item_count": 0,
                        "mapped_count": 0,
                        "generated_count": 0,
                        "executed_count": 0,
                        "passed_count": 0,
                        "failed_count": 0,
                        "blocked_count": 0,
                        "uncovered_count": 0,
                    },
                }
            )

    def test_missing_summary(self) -> None:
        with pytest.raises(QaSchemaError, match="summary"):
            validate_settlement({"chain": "api"})

    def test_summary_counts_must_be_int(self) -> None:
        with pytest.raises(QaSchemaError, match="total_capability_count"):
            validate_settlement(
                {
                    "chain": "api",
                    "summary": {"total_capability_count": "not_an_int"},
                }
            )

    def test_minimal_settlement(self) -> None:
        result = validate_settlement(
            {
                "chain": "api",
                "summary": {
                    "total_capability_count": 0,
                    "total_coverage_item_count": 0,
                    "mapped_count": 0,
                    "generated_count": 0,
                    "executed_count": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "blocked_count": 0,
                    "uncovered_count": 0,
                },
            }
        )
        assert result.by_capability == []
        assert result.verdict is None
        assert result.gate_evaluation is None


# ===========================================================================
# validate_file auto-detection
# ===========================================================================


class TestAutoDetect:
    def test_detects_plan(self) -> None:
        result = validate_file(FIXTURES / "valid_plan.yaml")
        assert isinstance(result, ApiTestPlan)

    def test_detects_manifest(self) -> None:
        result = validate_file(FIXTURES / "valid_manifest.yaml")
        assert isinstance(result, ApiCoverageManifest)

    def test_detects_spec(self) -> None:
        result = validate_file(FIXTURES / "valid_spec.yaml")
        assert isinstance(result, ApiTestSpec)

    def test_detects_settlement(self) -> None:
        result = validate_file(FIXTURES / "valid_settlement.yaml")
        assert isinstance(result, SettlementReport)

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            validate_file(FIXTURES / "nonexistent.yaml")

    def test_unknown_schema(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("unknown_key: value\n")
            path = Path(f.name)
        with pytest.raises(QaSchemaError, match="Cannot detect schema type"):
            validate_file(path)
