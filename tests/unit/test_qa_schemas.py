"""Unit tests for cli.lib.qa_schemas — QA schema validation.

Tests cover:
- Dataclass definitions (frozen=True, enum values)
- Validation functions (plan, manifest, spec, settlement, gate)
- Error conditions (missing fields, invalid enums, type mismatches)
- File-level validation (validate_file, auto-detect)
- CLI entry point (main)

Fixtures: ssot/schemas/qa/fixtures/
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from cli.lib.qa_schemas import (
    ApiCoverageManifest,
    ApiObject,
    ApiTestPlan,
    ApiTestSpec,
    CutRecord,
    EvidenceCompleteness,
    GateEvaluation,
    LifecycleStatus,
    ManifestItem,
    Priority,
    QaSchemaError,
    ScenarioType,
    SettlementReport,
    SpecExpected,
    SpecRequest,
    Summary,
    Verdict,
    WaiverEntry,
    WaiverStatus,
    validate_file,
    validate_gate,
    validate_manifest,
    validate_plan,
    validate_settlement,
    validate_spec,
)


FIXTURE_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa" / "fixtures"


def _load_fixture(name: str) -> dict:
    import yaml
    path = FIXTURE_DIR / name
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Plan validation
# ---------------------------------------------------------------------------


class PlanValidationTests(unittest.TestCase):
    def test_valid_plan(self):
        data = _load_fixture("sample_plan.yaml")
        result = validate_plan(data["api_test_plan"])
        self.assertIsInstance(result, ApiTestPlan)
        self.assertEqual(result.feature_id, "feat.sample.001")
        self.assertEqual(len(result.api_objects), 1)
        self.assertEqual(result.api_objects[0].name, "sample_resource")

    def test_plan_missing_feature_id(self):
        data = _load_fixture("sample_plan.yaml")
        del data["api_test_plan"]["feature_id"]
        with self.assertRaises(QaSchemaError) as ctx:
            validate_plan(data["api_test_plan"])
        self.assertIn("feature_id", str(ctx.exception))

    def test_plan_empty_source_feat_refs(self):
        data = _load_fixture("sample_plan.yaml")
        data["api_test_plan"]["source_feat_refs"] = []
        with self.assertRaises(QaSchemaError) as ctx:
            validate_plan(data["api_test_plan"])
        self.assertIn("non-empty list", str(ctx.exception))

    def test_plan_api_object_missing_name(self):
        data = _load_fixture("sample_plan.yaml")
        data["api_test_plan"]["api_objects"][0] = {"capabilities": ["create"]}
        with self.assertRaises(QaSchemaError) as ctx:
            validate_plan(data["api_test_plan"])
        self.assertIn("name", str(ctx.exception))

    def test_plan_no_priorities(self):
        data = _load_fixture("sample_plan.yaml")
        data["api_test_plan"]["priorities"] = {"p0": [], "p1": [], "p2": []}
        with self.assertRaises(QaSchemaError) as ctx:
            validate_plan(data["api_test_plan"])
        self.assertIn("at least one", str(ctx.exception))

    def test_plan_with_cut_records(self):
        data = _load_fixture("sample_plan.yaml")
        data["api_test_plan"]["cut_records"] = [
            {
                "capability": "delete",
                "dimension": "permission",
                "cut_reason": "Out of scope for v1",
                "source_ref": "feat.sample.001",
                "approver": "alice",
                "approved_at": "2026-04-01",
            }
        ]
        result = validate_plan(data["api_test_plan"])
        self.assertEqual(len(result.cut_records), 1)
        self.assertIsInstance(result.cut_records[0], CutRecord)


# ---------------------------------------------------------------------------
# Manifest validation
# ---------------------------------------------------------------------------


class ManifestValidationTests(unittest.TestCase):
    def test_valid_manifest(self):
        data = _load_fixture("sample_manifest.yaml")
        result = validate_manifest(data["api_coverage_manifest"])
        self.assertIsInstance(result, ApiCoverageManifest)
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.items[0].priority, "P0")

    def test_manifest_missing_coverage_id(self):
        data = _load_fixture("sample_manifest.yaml")
        del data["api_coverage_manifest"]["items"][0]["coverage_id"]
        with self.assertRaises(QaSchemaError) as ctx:
            validate_manifest(data["api_coverage_manifest"])
        self.assertIn("coverage_id", str(ctx.exception))

    def test_manifest_invalid_priority(self):
        data = _load_fixture("sample_manifest.yaml")
        data["api_coverage_manifest"]["items"][0]["priority"] = "P3"
        with self.assertRaises(QaSchemaError) as ctx:
            validate_manifest(data["api_coverage_manifest"])
        self.assertIn("P3", str(ctx.exception))

    def test_manifest_invalid_lifecycle_status(self):
        data = _load_fixture("sample_manifest.yaml")
        data["api_coverage_manifest"]["items"][0]["lifecycle_status"] = "unknown"
        with self.assertRaises(QaSchemaError) as ctx:
            validate_manifest(data["api_coverage_manifest"])
        self.assertIn("unknown", str(ctx.exception))

    def test_manifest_empty_items(self):
        data = _load_fixture("sample_manifest.yaml")
        data["api_coverage_manifest"]["items"] = []
        result = validate_manifest(data["api_coverage_manifest"])
        self.assertEqual(len(result.items), 0)


# ---------------------------------------------------------------------------
# Spec validation
# ---------------------------------------------------------------------------


class SpecValidationTests(unittest.TestCase):
    def test_valid_spec(self):
        data = _load_fixture("sample_spec.yaml")
        result = validate_spec(data["api_test_spec"])
        self.assertIsInstance(result, ApiTestSpec)
        self.assertEqual(result.case_id, "api_case.sample_resource.create.happy")
        self.assertIsNotNone(result.request)
        self.assertIsInstance(result.request, SpecRequest)
        self.assertEqual(result.expected.status_code, 201)

    def test_spec_missing_case_id(self):
        data = _load_fixture("sample_spec.yaml")
        del data["api_test_spec"]["case_id"]
        with self.assertRaises(QaSchemaError) as ctx:
            validate_spec(data["api_test_spec"])
        self.assertIn("case_id", str(ctx.exception))

    def test_spec_missing_expected(self):
        data = _load_fixture("sample_spec.yaml")
        del data["api_test_spec"]["expected"]
        with self.assertRaises(QaSchemaError) as ctx:
            validate_spec(data["api_test_spec"])
        self.assertIn("expected", str(ctx.exception))

    def test_spec_status_code_not_int(self):
        data = _load_fixture("sample_spec.yaml")
        data["api_test_spec"]["expected"]["status_code"] = "200"
        with self.assertRaises(QaSchemaError) as ctx:
            validate_spec(data["api_test_spec"])
        self.assertIn("integer", str(ctx.exception))

    def test_spec_with_null_request(self):
        data = _load_fixture("sample_spec.yaml")
        data["api_test_spec"]["request"] = None
        result = validate_spec(data["api_test_spec"])
        self.assertIsNone(result.request)


# ---------------------------------------------------------------------------
# Settlement validation
# ---------------------------------------------------------------------------


class SettlementValidationTests(unittest.TestCase):
    def test_valid_settlement(self):
        data = _load_fixture("sample_settlement.yaml")
        result = validate_settlement(data["settlement_report"])
        self.assertIsInstance(result, SettlementReport)
        self.assertEqual(result.chain, "api")
        self.assertEqual(result.summary.passed_count, 2)
        self.assertEqual(len(result.by_capability), 2)
        self.assertIsNotNone(result.gate_evaluation)
        self.assertEqual(result.gate_evaluation.gate_result, "pass")

    def test_settlement_missing_chain(self):
        data = _load_fixture("sample_settlement.yaml")
        del data["settlement_report"]["chain"]
        with self.assertRaises(QaSchemaError) as ctx:
            validate_settlement(data["settlement_report"])
        self.assertIn("chain", str(ctx.exception))

    def test_settlement_invalid_chain(self):
        data = _load_fixture("sample_settlement.yaml")
        data["settlement_report"]["chain"] = "integration"
        with self.assertRaises(QaSchemaError) as ctx:
            validate_settlement(data["settlement_report"])
        self.assertIn("integration", str(ctx.exception))

    def test_settlement_summary_non_int(self):
        data = _load_fixture("sample_settlement.yaml")
        data["settlement_report"]["summary"]["passed_count"] = "2"
        with self.assertRaises(QaSchemaError) as ctx:
            validate_settlement(data["settlement_report"])
        self.assertIn("must be an integer", str(ctx.exception))

    def test_settlement_with_gap(self):
        data = _load_fixture("sample_settlement.yaml")
        data["settlement_report"]["gap_list"] = [
            {
                "coverage_id": "api.sample_resource.create.validation",
                "capability": "create",
                "lifecycle_status": "failed",
                "failure_reason": "Parameter validation missing",
                "blocker_reason": None,
            }
        ]
        result = validate_settlement(data["settlement_report"])
        self.assertEqual(len(result.gap_list), 1)

    def test_settlement_with_waiver(self):
        data = _load_fixture("sample_settlement.yaml")
        data["settlement_report"]["waiver_list"] = [
            {
                "coverage_id": "api.sample_resource.create.validation",
                "waiver_status": "pending",
                "waiver_reason": "Under investigation",
                "approver": None,
                "approved_at": None,
            }
        ]
        result = validate_settlement(data["settlement_report"])
        self.assertEqual(len(result.waiver_list), 1)
        self.assertEqual(result.waiver_list[0].waiver_status, "pending")

    def test_settlement_invalid_waiver_status(self):
        data = _load_fixture("sample_settlement.yaml")
        data["settlement_report"]["waiver_list"] = [
            {
                "coverage_id": "api.sample_resource.create.validation",
                "waiver_status": "unknown",
                "waiver_reason": "test",
                "approver": None,
                "approved_at": None,
            }
        ]
        with self.assertRaises(QaSchemaError) as ctx:
            validate_settlement(data["settlement_report"])
        self.assertIn("unknown", str(ctx.exception))

    def test_settlement_invalid_gate_result(self):
        data = _load_fixture("sample_settlement.yaml")
        data["settlement_report"]["gate_evaluation"]["gate_result"] = "unknown"
        with self.assertRaises(QaSchemaError) as ctx:
            validate_settlement(data["settlement_report"])
        self.assertIn("unknown", str(ctx.exception))

    def test_settlement_by_capability_invalid_status(self):
        data = _load_fixture("sample_settlement.yaml")
        data["settlement_report"]["by_capability"][0]["status"] = "unknown"
        with self.assertRaises(QaSchemaError) as ctx:
            validate_settlement(data["settlement_report"])
        self.assertIn("unknown", str(ctx.exception))


# ---------------------------------------------------------------------------
# Gate validation
# ---------------------------------------------------------------------------


class GateValidationTests(unittest.TestCase):
    def test_valid_gate(self):
        data = {
            "evaluated_at": "2026-04-15T12:00:00Z",
            "feature_id": "feat.sample.001",
            "source_manifest_ref": "ssot/tests/sample.yaml",
            "source_settlement_ref": "ssot/tests/sample-settlement.yaml",
            "evidence_hash": "a" * 64,
            "final_decision": "pass",
            "anti_laziness_checks": {
                "manifest_frozen": True,
                "cut_records_valid": True,
                "pending_waivers_counted": True,
                "evidence_consistent": True,
                "min_exception_coverage": True,
                "no_evidence_not_executed": True,
                "evidence_hash_binding": True,
            },
            "api_chain": {
                "total": 2,
                "passed": 2,
                "failed": 0,
                "blocked": 0,
                "uncovered": 0,
                "pass_rate": 1.0,
                "evidence_status": "complete",
            },
            "e2e_chain": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "blocked": 0,
                "uncovered": 0,
                "pass_rate": 1.0,
                "evidence_status": "complete",
                "exception_journeys_executed": 0,
            },
            "decision_reason": "All checks passed",
        }
        result = validate_gate(data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["final_decision"], "pass")

    def test_gate_invalid_final_decision(self):
        data = {
            "evaluated_at": "2026-04-15T12:00:00Z",
            "feature_id": "feat.sample.001",
            "evidence_hash": "a" * 64,
            "final_decision": "unknown",
            "anti_laziness_checks": {
                "manifest_frozen": True,
                "cut_records_valid": True,
                "pending_waivers_counted": True,
                "evidence_consistent": True,
                "min_exception_coverage": True,
                "no_evidence_not_executed": True,
                "evidence_hash_binding": True,
            },
            "api_chain": {
                "total": 2, "passed": 2, "failed": 0, "blocked": 0, "uncovered": 0,
                "pass_rate": 1.0, "evidence_status": "complete",
            },
            "e2e_chain": {
                "total": 0, "passed": 0, "failed": 0, "blocked": 0, "uncovered": 0,
                "pass_rate": 1.0, "evidence_status": "complete",
                "exception_journeys_executed": 0,
            },
            "decision_reason": "test",
        }
        with self.assertRaises(QaSchemaError) as ctx:
            validate_gate(data)
        self.assertIn("unknown", str(ctx.exception))

    def test_gate_invalid_hash(self):
        data = {
            "evaluated_at": "2026-04-15T12:00:00Z",
            "feature_id": "feat.sample.001",
            "evidence_hash": "not-a-valid-hash",
            "final_decision": "pass",
            "anti_laziness_checks": {
                "manifest_frozen": True,
                "cut_records_valid": True,
                "pending_waivers_counted": True,
                "evidence_consistent": True,
                "min_exception_coverage": True,
                "no_evidence_not_executed": True,
                "evidence_hash_binding": True,
            },
            "api_chain": {
                "total": 2, "passed": 2, "failed": 0, "blocked": 0, "uncovered": 0,
                "pass_rate": 1.0, "evidence_status": "complete",
            },
            "e2e_chain": {
                "total": 0, "passed": 0, "failed": 0, "blocked": 0, "uncovered": 0,
                "pass_rate": 1.0, "evidence_status": "complete",
                "exception_journeys_executed": 0,
            },
            "decision_reason": "test",
        }
        with self.assertRaises(QaSchemaError) as ctx:
            validate_gate(data)
        self.assertIn("64-char", str(ctx.exception))


# ---------------------------------------------------------------------------
# File-level validation
# ---------------------------------------------------------------------------


class FileValidationTests(unittest.TestCase):
    def test_validate_file_plan(self):
        path = FIXTURE_DIR / "sample_plan.yaml"
        result = validate_file(path, "plan")
        self.assertIsInstance(result, ApiTestPlan)

    def test_validate_file_manifest(self):
        path = FIXTURE_DIR / "sample_manifest.yaml"
        result = validate_file(path, "manifest")
        self.assertIsInstance(result, ApiCoverageManifest)

    def test_validate_file_spec(self):
        path = FIXTURE_DIR / "sample_spec.yaml"
        result = validate_file(path, "spec")
        self.assertIsInstance(result, ApiTestSpec)

    def test_validate_file_settlement(self):
        path = FIXTURE_DIR / "sample_settlement.yaml"
        result = validate_file(path, "settlement")
        self.assertIsInstance(result, SettlementReport)

    def test_validate_file_auto_detect(self):
        """Auto-detect schema type from file content."""
        path = FIXTURE_DIR / "sample_plan.yaml"
        result = validate_file(path)
        self.assertIsInstance(result, ApiTestPlan)

    def test_validate_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            validate_file("nonexistent.yaml", "plan")

    def test_validate_file_unknown_type(self):
        with self.assertRaises(QaSchemaError) as ctx:
            validate_file(FIXTURE_DIR / "sample_plan.yaml", "unknown")
        self.assertIn("unknown", str(ctx.exception))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


class CliTests(unittest.TestCase):
    def test_cli_valid_file(self):
        from cli.lib.qa_schemas import main
        argv = ["python", "--type", "plan", str(FIXTURE_DIR / "sample_plan.yaml")]
        with patch.object(sys, "argv", argv):
            buf = io.StringIO()
            with redirect_stdout(buf):
                try:
                    main()
                except SystemExit as e:
                    self.assertEqual(e.code, 0)
        output = buf.getvalue()
        self.assertIn("OK", output)

    def test_cli_no_args(self):
        from cli.lib.qa_schemas import main
        argv = ["python"]
        with patch.object(sys, "argv", argv):
            buf = io.StringIO()
            with redirect_stdout(buf):
                with self.assertRaises(SystemExit) as ctx:
                    main()
                self.assertEqual(ctx.exception.code, 1)
        output = buf.getvalue()
        self.assertIn("Usage", output)


# ---------------------------------------------------------------------------
# Enum validation
# ---------------------------------------------------------------------------


class EnumTests(unittest.TestCase):
    def test_lifecycle_status_values(self):
        values = [e.value for e in LifecycleStatus]
        self.assertIn("drafted", values)
        self.assertIn("designed", values)
        self.assertIn("generated", values)
        self.assertIn("executed", values)
        self.assertIn("passed", values)
        self.assertIn("failed", values)
        self.assertIn("blocked", values)
        self.assertIn("waived", values)

    def test_priority_values(self):
        values = [e.value for e in Priority]
        self.assertEqual(values, ["P0", "P1", "P2"])

    def test_scenario_type_values(self):
        values = [e.value for e in ScenarioType]
        self.assertIn("happy_path", values)
        self.assertIn("validation", values)
        self.assertIn("boundary", values)
        self.assertIn("permission", values)
        self.assertIn("error", values)

    def test_waiver_status_values(self):
        values = [e.value for e in WaiverStatus]
        self.assertIn("none", values)
        self.assertIn("pending", values)
        self.assertIn("approved", values)
        self.assertIn("rejected", values)


if __name__ == "__main__":
    unittest.main()
