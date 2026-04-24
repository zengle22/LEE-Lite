"""Tests for cli.lib.independent_verifier — ADR-054 Phase 3 verdict engine.

Boundary conditions from cross-AI review:
- Main flow coverage <100% → FAIL
- Non-core flow coverage <80% → conditional_pass or FAIL
- Zero executed items → confidence = 0.0
- Unknown scenario_type → non_core_flow + warning
- Empty manifest_items → confidence = 0.0, verdict = PASS (no flows to fail)

Per D-01 through D-05.
"""

import pytest

from cli.lib.gate_schema import GateVerdict
from cli.lib.independent_verifier import (
    FlowMetrics,
    VerdictReport,
    _categorize_items,
    _compute_confidence,
    _compute_flow_metrics,
    _determine_flow_verdict,
    verify,
)


class TestDetermineFlowVerdict:
    """Test _determine_flow_verdict per D-01 (main) and D-02 (non-core)."""

    def test_main_flow_full_coverage_zero_failures(self):
        # D-01: main flow requires 100% coverage, 0 failures → PASS
        result = _determine_flow_verdict(coverage=1.0, failures=0, is_main=True)
        assert result == GateVerdict.PASS

    def test_main_flow_full_coverage_with_failures(self):
        # D-01: main flow allows 0 failures → FAIL even with 100% coverage
        result = _determine_flow_verdict(coverage=1.0, failures=1, is_main=True)
        assert result == GateVerdict.FAIL

    def test_main_flow_partial_coverage(self):
        # D-01: main flow requires 100% coverage → FAIL
        result = _determine_flow_verdict(coverage=0.95, failures=0, is_main=True)
        assert result == GateVerdict.FAIL

    def test_main_flow_boundary_coverage_below_one(self):
        # D-01: coverage must be >= 1.0 (100%), not just close
        result = _determine_flow_verdict(coverage=0.999, failures=0, is_main=True)
        assert result == GateVerdict.FAIL

    def test_non_core_flow_full_coverage_zero_failures(self):
        # D-02: non-core flow with >=80% coverage and <=5 failures → PASS
        result = _determine_flow_verdict(coverage=1.0, failures=0, is_main=False)
        assert result == GateVerdict.PASS

    def test_non_core_flow_80_percent_coverage_zero_failures(self):
        # D-02: boundary case — exactly 80% coverage → PASS
        result = _determine_flow_verdict(coverage=0.80, failures=0, is_main=False)
        assert result == GateVerdict.PASS

    def test_non_core_flow_79_percent_coverage(self):
        # D-02: below 80% coverage → FAIL
        result = _determine_flow_verdict(coverage=0.79, failures=0, is_main=False)
        assert result == GateVerdict.FAIL

    def test_non_core_flow_6_failures_at_100_percent_coverage(self):
        # D-02: >5 failures even with 100% coverage → FAIL
        result = _determine_flow_verdict(coverage=1.0, failures=6, is_main=False)
        assert result == GateVerdict.FAIL

    def test_non_core_flow_5_failures_at_100_percent_coverage(self):
        # D-02: exactly 5 failures at 100% coverage → PASS (tolerance boundary)
        result = _determine_flow_verdict(coverage=1.0, failures=5, is_main=False)
        assert result == GateVerdict.PASS

    def test_non_core_flow_zero_coverage(self):
        # D-02: 0% coverage → FAIL
        result = _determine_flow_verdict(coverage=0.0, failures=0, is_main=False)
        assert result == GateVerdict.FAIL


class TestCategorizeItems:
    """Test _categorize_items per D-03: scenario_type classification."""

    def test_main_scenario_type_goes_to_main_flow(self):
        items = [{"coverage_id": "c1", "scenario_type": "main"}]
        main, non_core = _categorize_items(items)
        assert len(main) == 1
        assert len(non_core) == 0

    def test_exception_scenario_type_goes_to_non_core_flow(self):
        items = [{"coverage_id": "c1", "scenario_type": "exception"}]
        main, non_core = _categorize_items(items)
        assert len(main) == 0
        assert len(non_core) == 1

    def test_branch_scenario_type_goes_to_non_core_flow(self):
        items = [{"coverage_id": "c1", "scenario_type": "branch"}]
        main, non_core = _categorize_items(items)
        assert len(main) == 0
        assert len(non_core) == 1

    def test_retry_scenario_type_goes_to_non_core_flow(self):
        items = [{"coverage_id": "c1", "scenario_type": "retry"}]
        main, non_core = _categorize_items(items)
        assert len(main) == 0
        assert len(non_core) == 1

    def test_state_scenario_type_goes_to_non_core_flow(self):
        items = [{"coverage_id": "c1", "scenario_type": "state"}]
        main, non_core = _categorize_items(items)
        assert len(main) == 0
        assert len(non_core) == 1

    def test_unknown_scenario_type_defaults_to_non_core_flow(self):
        # Per cross-review consensus: unknown → non_core with warning
        items = [{"coverage_id": "c1", "scenario_type": "unknown_type"}]
        main, non_core = _categorize_items(items)
        assert len(main) == 0
        assert len(non_core) == 1

    def test_missing_scenario_type_goes_to_main_flow(self):
        # Implementation uses item.get("scenario_type", "main") — missing key defaults to "main"
        items = [{"coverage_id": "c1"}]
        main, non_core = _categorize_items(items)
        assert len(main) == 1
        assert len(non_core) == 0

    def test_empty_scenario_type_defaults_to_non_core_flow(self):
        items = [{"coverage_id": "c1", "scenario_type": ""}]
        main, non_core = _categorize_items(items)
        assert len(main) == 0
        assert len(non_core) == 1

    def test_mixed_main_and_non_core_flows(self):
        items = [
            {"coverage_id": "m1", "scenario_type": "main"},
            {"coverage_id": "e1", "scenario_type": "exception"},
            {"coverage_id": "m2", "scenario_type": "main"},
            {"coverage_id": "b1", "scenario_type": "branch"},
        ]
        main, non_core = _categorize_items(items)
        assert len(main) == 2
        assert len(non_core) == 2

    def test_empty_list(self):
        main, non_core = _categorize_items([])
        assert main == []
        assert non_core == []


class TestComputeConfidence:
    """Test _compute_confidence per D-04: evidence_refs coverage."""

    def test_all_executed_have_evidence_refs(self):
        # D-04: confidence = items with evidence_refs / executed items
        items = [
            {"lifecycle_status": "passed", "evidence_refs": ["ref1"]},
            {"lifecycle_status": "failed", "evidence_refs": ["ref2"]},
            {"lifecycle_status": "blocked", "evidence_refs": ["ref3"]},
        ]
        result = _compute_confidence(items)
        assert result == 1.0

    def test_none_executed_have_evidence_refs(self):
        items = [
            {"lifecycle_status": "passed", "evidence_refs": []},
            {"lifecycle_status": "failed"},
        ]
        result = _compute_confidence(items)
        assert result == 0.0

    def test_partial_executed_have_evidence_refs(self):
        items = [
            {"lifecycle_status": "passed", "evidence_refs": ["ref1"]},
            {"lifecycle_status": "failed", "evidence_refs": []},
            {"lifecycle_status": "passed", "evidence_refs": ["ref2"]},
            {"lifecycle_status": "blocked", "evidence_refs": []},
        ]
        result = _compute_confidence(items)
        assert result == 0.5

    def test_zero_executed_items_returns_zero(self):
        # Per cross-review: guard against zero-division → 0.0
        items = [
            {"lifecycle_status": "designed"},
            {"lifecycle_status": "designed"},
        ]
        result = _compute_confidence(items)
        assert result == 0.0

    def test_empty_list_returns_zero(self):
        result = _compute_confidence([])
        assert result == 0.0

    def test_only_designed_status_not_counted_as_executed(self):
        # Only lifecycle_status in (passed, failed, blocked) counts as executed
        items = [
            {"lifecycle_status": "designed", "evidence_refs": ["ref1"]},
            {"lifecycle_status": "designed", "evidence_refs": ["ref2"]},
        ]
        result = _compute_confidence(items)
        assert result == 0.0

    def test_evidence_ref_single_string_not_counted(self):
        # evidence_ref (single string) is not evidence_refs (list)
        items = [
            {"lifecycle_status": "passed", "evidence_ref": "ref1"},  # singular
        ]
        result = _compute_confidence(items)
        assert result == 0.0


class TestComputeFlowMetrics:
    """Test _compute_flow_metrics: coverage and failure count per flow."""

    def test_empty_items_treated_as_full_coverage(self):
        # Per Phase 19-01 decision: empty category = 100% coverage = PASS
        metrics = _compute_flow_metrics([], is_main=True)
        assert metrics.coverage == 1.0
        assert metrics.failures == 0
        assert metrics.status == GateVerdict.PASS

    def test_all_executed_no_failures(self):
        items = [
            {"lifecycle_status": "passed"},
            {"lifecycle_status": "passed"},
        ]
        metrics = _compute_flow_metrics(items, is_main=True)
        assert metrics.coverage == 1.0
        assert metrics.failures == 0

    def test_partial_execution(self):
        items = [
            {"lifecycle_status": "passed"},
            {"lifecycle_status": "designed"},  # not executed
        ]
        metrics = _compute_flow_metrics(items, is_main=True)
        assert metrics.coverage == 0.5

    def test_blocked_counts_as_executed(self):
        # Blocked items are executed (for coverage) but not failures
        items = [
            {"lifecycle_status": "passed"},
            {"lifecycle_status": "blocked"},
        ]
        metrics = _compute_flow_metrics(items, is_main=True)
        assert metrics.coverage == 1.0
        assert metrics.failures == 0

    def test_failed_items_counted_as_failures(self):
        items = [
            {"lifecycle_status": "passed"},
            {"lifecycle_status": "failed"},
        ]
        metrics = _compute_flow_metrics(items, is_main=True)
        assert metrics.coverage == 1.0
        assert metrics.failures == 1

    def test_to_dict_converts_coverage_to_percentage(self):
        metrics = FlowMetrics(coverage=0.95, failures=2, status=GateVerdict.FAIL)
        d = metrics.to_dict()
        assert d["coverage"] == 95
        assert d["failures"] == 2
        assert d["status"] == "fail"


class TestVerify:
    """Test the main verify() function — full integration per D-01 through D-05."""

    def test_all_main_flow_passed_no_non_core(self):
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed", "evidence_refs": ["r1"]},
        ]
        report = verify(items, run_id="RUN-TEST")
        assert report.run_id == "RUN-TEST"
        assert report.verdict == GateVerdict.PASS
        assert report.confidence == 1.0

    def test_main_flow_failed(self):
        # D-01: main flow failure → overall FAIL regardless of non-core
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "failed", "evidence_refs": []},
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.FAIL

    def test_main_flow_incomplete_coverage(self):
        # D-01: main flow needs 100% coverage
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"},
            {"coverage_id": "c2", "scenario_type": "main", "lifecycle_status": "designed"},
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.FAIL
        assert report.details["main_flow"]["coverage"] == 50

    def test_non_core_flow_below_80_percent(self):
        # D-02: non-core flow below 80% coverage → FAIL
        items = [
            {"coverage_id": "c1", "scenario_type": "exception", "lifecycle_status": "passed"},
            {"coverage_id": "c2", "scenario_type": "exception", "lifecycle_status": "designed"},
            {"coverage_id": "c3", "scenario_type": "exception", "lifecycle_status": "designed"},
            {"coverage_id": "c4", "scenario_type": "exception", "lifecycle_status": "designed"},
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.FAIL

    def test_non_core_flow_exactly_80_percent(self):
        # D-02: boundary — exactly 80% coverage → PASS for non-core
        items = [
            {"coverage_id": f"c{i}", "scenario_type": "exception", "lifecycle_status": "passed"}
            for i in range(4)
        ] + [
            {"coverage_id": "c5", "scenario_type": "exception", "lifecycle_status": "designed"}
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.PASS

    def test_empty_manifest_returns_pass(self):
        # Empty manifest: no flows to fail → PASS
        report = verify([])
        assert report.verdict == GateVerdict.PASS
        assert report.confidence == 0.0

    def test_only_non_core_items_all_passed(self):
        items = [
            {"coverage_id": "c1", "scenario_type": "exception", "lifecycle_status": "passed"},
            {"coverage_id": "c2", "scenario_type": "branch", "lifecycle_status": "passed"},
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.PASS

    def test_blocked_items_do_not_count_as_failures(self):
        # Blocked items: executed (for coverage) but not failures
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "blocked"},
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.PASS  # main with 100% coverage, 0 failures

    def test_run_id_auto_generated(self):
        items = [{"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"}]
        report = verify(items)
        assert report.run_id.startswith("RUN-")
        assert len(report.run_id) > 4

    def test_confidence_zero_when_no_evidence_refs(self):
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"},
        ]
        report = verify(items)
        assert report.confidence == 0.0

    def test_confidence_one_when_all_have_evidence_refs(self):
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed", "evidence_refs": ["r1"]},
            {"coverage_id": "c2", "scenario_type": "main", "lifecycle_status": "passed", "evidence_refs": ["r2"]},
        ]
        report = verify(items)
        assert report.confidence == 1.0

    def test_to_dict_contains_all_required_fields(self):
        items = [{"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"}]
        report = verify(items, run_id="RUN-001")
        d = report.to_dict()
        assert d["run_id"] == "RUN-001"
        assert d["verdict"] == "pass"
        assert "confidence" in d
        assert "details" in d
        assert "main_flow" in d["details"]
        assert "non_core_flow" in d["details"]

    def test_to_yaml_dict_wraps_under_verification_report(self):
        items = [{"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"}]
        report = verify(items, run_id="RUN-001")
        yd = report.to_yaml_dict()
        assert "verification_report" in yd
        assert yd["verification_report"]["run_id"] == "RUN-001"


class TestVerifyBoundaryConditions:
    """Boundary conditions from cross-AI review (HIGH priority)."""

    def test_zero_executed_items_confidence_is_zero(self):
        """Per Codex MEDIUM + Qwen MEDIUM: guard against zero-division."""
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "designed"},
            {"coverage_id": "c2", "scenario_type": "main", "lifecycle_status": "designed"},
        ]
        report = verify(items)
        assert report.confidence == 0.0

    def test_main_flow_zero_tolerance(self):
        """Per D-01: main flow has 0 failure tolerance."""
        # 100% coverage but 1 failure → FAIL
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"},
            {"coverage_id": "c2", "scenario_type": "main", "lifecycle_status": "failed"},
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.FAIL
        assert report.details["main_flow"]["failures"] == 1

    def test_non_core_flow_flexible_tolerance(self):
        """Per D-02: non-core flow has 5 failure tolerance."""
        # 100% coverage, 3 failures → PASS (within tolerance)
        items = [
            {"coverage_id": f"c{i}", "scenario_type": "exception", "lifecycle_status": "failed"}
            for i in range(3)
        ] + [
            {"coverage_id": f"p{i}", "scenario_type": "exception", "lifecycle_status": "passed"}
            for i in range(7)
        ]
        report = verify(items)
        assert report.verdict == GateVerdict.PASS

    def test_unknown_scenario_type_in_verdict(self):
        """Per cross-review: unknown scenario_type → non-core flow."""
        items = [
            {"coverage_id": "c1", "scenario_type": "foobar", "lifecycle_status": "passed"},
        ]
        report = verify(items)
        # Unknown → non-core → PASS (non-core with full coverage)
        assert report.verdict == GateVerdict.PASS
        assert report.details["non_core_flow"]["status"] == "pass"
