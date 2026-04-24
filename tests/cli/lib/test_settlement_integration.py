"""Tests for cli.lib.settlement_integration — verdict/confidence passthrough.

Per D-06/D-07: settlement consumes verdict + confidence from independent_verifier.
Per cross-AI review: test verdict/confidence passthrough and statistics computation.
"""

import pytest

from cli.lib.gate_schema import GateVerdict
from cli.lib.independent_verifier import VerdictReport
from cli.lib.settlement_integration import (
    SettlementInput,
    _build_gap_list,
    _build_waiver_list,
    _compute_statistics,
    _load_manifest,
    generate_settlement,
    generate_settlement_from_manifest,
)


class TestComputeStatistics:
    """Test _compute_statistics — settlement statistics from manifest items."""

    def test_all_passed(self):
        items = [
            {"lifecycle_status": "passed"},
            {"lifecycle_status": "passed"},
        ]
        stats = _compute_statistics(items)
        assert stats["total"] == 2
        assert stats["executed"] == 2
        assert stats["passed"] == 2
        assert stats["failed"] == 0
        assert stats["blocked"] == 0
        assert stats["designed"] == 0
        assert stats["uncovered"] == 0
        assert stats["pass_rate"] == 1.0

    def test_mixed_results(self):
        items = [
            {"lifecycle_status": "passed"},
            {"lifecycle_status": "failed"},
            {"lifecycle_status": "blocked"},
            {"lifecycle_status": "designed"},
        ]
        stats = _compute_statistics(items)
        assert stats["total"] == 4
        assert stats["executed"] == 3  # passed, failed, blocked
        assert stats["passed"] == 1
        assert stats["failed"] == 1
        assert stats["blocked"] == 1
        assert stats["designed"] == 1
        assert stats["uncovered"] == 1
        assert stats["pass_rate"] == round(1 / 3, 3)

    def test_zero_executed_pass_rate_is_zero(self):
        items = [
            {"lifecycle_status": "designed"},
            {"lifecycle_status": "designed"},
        ]
        stats = _compute_statistics(items)
        assert stats["executed"] == 0
        assert stats["pass_rate"] == 0.0

    def test_empty_list(self):
        stats = _compute_statistics([])
        assert stats["total"] == 0
        assert stats["executed"] == 0
        assert stats["pass_rate"] == 0.0

    def test_cut_and_obsolete_counted(self):
        items = [
            {"lifecycle_status": "cut"},
            {"lifecycle_status": "cut"},
            {"obsolete": True},
        ]
        stats = _compute_statistics(items)
        assert stats["cut"] == 2
        assert stats["obsolete"] == 1

    def test_pass_rate_rounding(self):
        items = [
            {"lifecycle_status": "passed"},
            {"lifecycle_status": "failed"},
            {"lifecycle_status": "failed"},
        ]
        stats = _compute_statistics(items)
        assert stats["pass_rate"] == pytest.approx(round(1 / 3, 3))


class TestBuildGapList:
    """Test _build_gap_list — failed/blocked items become gaps."""

    def test_failed_items_appear_in_gap_list(self):
        items = [
            {"coverage_id": "c1", "capability": "CAP-A", "lifecycle_status": "failed"},
        ]
        gaps = _build_gap_list(items)
        assert len(gaps) == 1
        assert gaps[0].coverage_id == "c1"
        assert gaps[0].capability == "CAP-A"
        assert gaps[0].lifecycle_status == "failed"

    def test_blocked_items_appear_in_gap_list(self):
        items = [
            {"coverage_id": "c1", "capability": "CAP-B", "lifecycle_status": "blocked"},
        ]
        gaps = _build_gap_list(items)
        assert len(gaps) == 1
        assert gaps[0].lifecycle_status == "blocked"

    def test_designed_items_appear_in_gap_list(self):
        items = [
            {"coverage_id": "c1", "capability": "CAP-C", "lifecycle_status": "designed"},
        ]
        gaps = _build_gap_list(items)
        assert len(gaps) == 1
        assert gaps[0].lifecycle_status == "designed"

    def test_passed_items_not_in_gap_list(self):
        items = [
            {"coverage_id": "c1", "capability": "CAP", "lifecycle_status": "passed"},
        ]
        gaps = _build_gap_list(items)
        assert len(gaps) == 0

    def test_multiple_gaps(self):
        items = [
            {"coverage_id": "c1", "capability": "CAP", "lifecycle_status": "failed"},
            {"coverage_id": "c2", "capability": "CAP", "lifecycle_status": "blocked"},
            {"coverage_id": "c3", "capability": "CAP", "lifecycle_status": "passed"},
        ]
        gaps = _build_gap_list(items)
        assert len(gaps) == 2


class TestBuildWaiverList:
    """Test _build_waiver_list — items with waiver_status become waivers."""

    def test_waived_items_appear_in_waiver_list(self):
        items = [
            {
                "coverage_id": "c1",
                "waiver_status": "approved",
                "waiver_reason": "known limitation",
            },
        ]
        waivers = _build_waiver_list(items)
        assert len(waivers) == 1
        assert waivers[0].coverage_id == "c1"
        assert waivers[0].waiver_status == "approved"

    def test_non_waived_items_not_in_list(self):
        items = [
            {"coverage_id": "c1", "waiver_status": "none"},
        ]
        waivers = _build_waiver_list(items)
        assert len(waivers) == 0

    def test_no_waiver_status_field_not_in_list(self):
        items = [
            {"coverage_id": "c1"},  # no waiver_status field
        ]
        waivers = _build_waiver_list(items)
        assert len(waivers) == 0


class TestGenerateSettlement:
    """Test generate_settlement — verdict/confidence passthrough per D-07."""

    def test_settlement_contains_verdict_from_verdict_report(self):
        # Per D-07: settlement must contain verdict from independent_verifier
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"},
        ]
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.PASS,
            confidence=1.0,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api")

        assert settlement["api_settlement"]["verdict"] == "pass"
        assert settlement["api_settlement"]["confidence"] == 1.0

    def test_settlement_contains_confidence(self):
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"},
        ]
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.PASS,
            confidence=0.75,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api")
        assert settlement["api_settlement"]["confidence"] == 0.75

    def test_settlement_verdict_fail(self):
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "designed"},
        ]
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.FAIL,
            confidence=0.0,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api")
        assert settlement["api_settlement"]["verdict"] == "fail"

    def test_e2e_chain_key_is_e2e_settlement(self):
        items = []
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.PASS,
            confidence=1.0,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="e2e")
        assert "e2e_settlement" in settlement

    def test_settlement_contains_statistics(self):
        items = [
            {"coverage_id": "c1", "lifecycle_status": "passed"},
            {"coverage_id": "c2", "lifecycle_status": "failed"},
        ]
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.FAIL,
            confidence=0.5,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api")
        stats = settlement["api_settlement"]["statistics"]
        assert stats["total"] == 2
        assert stats["passed"] == 1
        assert stats["failed"] == 1

    def test_settlement_contains_gap_list(self):
        items = [
            {"coverage_id": "c1", "capability": "CAP", "lifecycle_status": "failed"},
        ]
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.FAIL,
            confidence=0.0,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api")
        gap_list = settlement["api_settlement"]["gap_list"]
        assert len(gap_list) == 1
        assert gap_list[0]["coverage_id"] == "c1"

    def test_settlement_contains_waiver_list(self):
        items = [
            {
                "coverage_id": "c1",
                "lifecycle_status": "failed",
                "waiver_status": "approved",
                "waiver_reason": "limitation",
            },
        ]
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.FAIL,
            confidence=0.0,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api")
        waiver_list = settlement["api_settlement"]["waiver_list"]
        assert len(waiver_list) == 1
        assert waiver_list[0]["coverage_id"] == "c1"

    def test_settlement_contains_feature_id(self):
        items = []
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.PASS,
            confidence=1.0,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api", feature_id="FEAT-001")
        assert settlement["api_settlement"]["feature_id"] == "FEAT-001"

    def test_settlement_generated_at_is_populated(self):
        items = []
        verdict_report = VerdictReport(
            run_id="RUN-001",
            generated_at="2026-04-24T00:00:00Z",
            verdict=GateVerdict.PASS,
            confidence=1.0,
            details={},
        )
        settlement = generate_settlement(items, verdict_report, chain="api")
        assert settlement["api_settlement"]["generated_at"] != ""

    def test_generates_verdict_when_not_provided(self):
        # If no verdict_report provided, generate_settlement calls verify()
        items = [
            {"coverage_id": "c1", "scenario_type": "main", "lifecycle_status": "passed"},
        ]
        settlement = generate_settlement(items, verdict_report=None, chain="api")
        assert "verdict" in settlement["api_settlement"]
        assert settlement["api_settlement"]["verdict"] == "pass"


class TestGenerateSettlementFromManifest:
    """Test generate_settlement_from_manifest — file-based integration."""

    def test_loads_manifest_and_generates_settlement(self, tmp_path):
        manifest_path = tmp_path / "manifest.yaml"
        manifest_path.write_text(
            "items:\n"
            "  - coverage_id: c1\n"
            "    lifecycle_status: passed\n"
            "    scenario_type: main\n",
            encoding="utf-8",
        )
        settlement = generate_settlement_from_manifest(manifest_path, chain="api")
        assert settlement["api_settlement"]["verdict"] == "pass"
        assert settlement["api_settlement"]["statistics"]["total"] == 1

    def test_writes_settlement_to_output_path(self, tmp_path):
        manifest_path = tmp_path / "manifest.yaml"
        manifest_path.write_text(
            "items:\n  - coverage_id: c1\n    lifecycle_status: passed\n    scenario_type: main\n",
            encoding="utf-8",
        )
        output_path = tmp_path / "settlement.yaml"
        generate_settlement_from_manifest(manifest_path, output_path=output_path, chain="api")
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "api_settlement" in content
        assert "verdict" in content


class TestSettlementInput:
    """Test SettlementInput dataclass."""

    def test_default_chain_is_api(self):
        inp = SettlementInput(manifest_path="manifest.yaml")
        assert inp.chain == "api"

    def test_e2e_chain(self):
        inp = SettlementInput(manifest_path="manifest.yaml", chain="e2e")
        assert inp.chain == "e2e"
