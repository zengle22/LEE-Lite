"""Tests for cli.lib.gate_integration.

Truth table tests for evaluate_gate function based on settlement verdicts.

Gate Truth Table:
+-------------------+-------------------+------------------------+
| API Verdict       | E2E Verdict       | Result                 |
+-------------------+-------------------+------------------------+
| PASS              | PASS              | PASS                   |
| PASS              | FAIL              | FAIL                   |
| FAIL              | PASS              | FAIL                   |
| FAIL              | FAIL              | FAIL                   |
| PASS              | None              | PASS                   |
| FAIL              | None              | FAIL                   |
| PASS              | CONDITIONAL_PASS  | CONDITIONAL_PASS       |
| CONDITIONAL_PASS  | PASS              | CONDITIONAL_PASS       |
| CONDITIONAL_PASS  | CONDITIONAL_PASS  | CONDITIONAL_PASS       |
| FAIL              | CONDITIONAL_PASS  | FAIL                   |
| CONDITIONAL_PASS  | FAIL              | FAIL                   |
| PASS              | PROVISIONAL_PASS  | CONDITIONAL_PASS       |
| PROVISIONAL_PASS  | PASS              | CONDITIONAL_PASS       |
| FAIL              | PROVISIONAL_PASS  | FAIL                   |
| PROVISIONAL_PASS  | FAIL              | FAIL                   |
+-------------------+-------------------+------------------------+
"""

import pytest

from cli.lib.gate_integration import (
    GateInput,
    _derive_gate_decision,
    evaluate_gate,
    write_gate_output,
)
from cli.lib.gate_schema import GateVerdict


class TestDeriveGateDecision:
    """Unit tests for _derive_gate_decision function."""

    # Truth table: Both PASS → PASS
    def test_both_pass(self):
        result = _derive_gate_decision("pass", 0.95, "pass", 0.90)
        assert result == GateVerdict.PASS

    # Truth table: Any FAIL → FAIL
    def test_api_fail_e2e_pass(self):
        result = _derive_gate_decision("fail", 0.95, "pass", 0.90)
        assert result == GateVerdict.FAIL

    def test_api_pass_e2e_fail(self):
        result = _derive_gate_decision("pass", 0.95, "fail", 0.90)
        assert result == GateVerdict.FAIL

    def test_both_fail(self):
        result = _derive_gate_decision("fail", 0.95, "fail", 0.90)
        assert result == GateVerdict.FAIL

    # Truth table: Missing E2E → API verdict only
    def test_api_pass_no_e2e(self):
        result = _derive_gate_decision("pass", 0.95, None, None)
        assert result == GateVerdict.PASS

    def test_api_fail_no_e2e(self):
        result = _derive_gate_decision("fail", 0.95, None, None)
        assert result == GateVerdict.FAIL

    def test_api_conditional_pass_no_e2e(self):
        result = _derive_gate_decision("conditional_pass", 0.95, None, None)
        assert result == GateVerdict.CONDITIONAL_PASS

    def test_api_provisional_pass_no_e2e(self):
        result = _derive_gate_decision("provisional_pass", 0.95, None, None)
        assert result == GateVerdict.CONDITIONAL_PASS

    # Truth table: Mixed pass/conditional → CONDITIONAL_PASS
    def test_api_pass_e2e_conditional(self):
        result = _derive_gate_decision("pass", 0.95, "conditional_pass", 0.90)
        assert result == GateVerdict.CONDITIONAL_PASS

    def test_api_conditional_e2e_pass(self):
        result = _derive_gate_decision("conditional_pass", 0.95, "pass", 0.90)
        assert result == GateVerdict.CONDITIONAL_PASS

    def test_both_conditional(self):
        result = _derive_gate_decision("conditional_pass", 0.95, "conditional_pass", 0.90)
        assert result == GateVerdict.CONDITIONAL_PASS

    # Truth table: FAIL overrides conditional
    def test_api_fail_e2e_conditional(self):
        result = _derive_gate_decision("fail", 0.95, "conditional_pass", 0.90)
        assert result == GateVerdict.FAIL

    def test_api_conditional_e2e_fail(self):
        result = _derive_gate_decision("conditional_pass", 0.95, "fail", 0.90)
        assert result == GateVerdict.FAIL

    # Truth table: Mixed provisional_pass
    def test_api_pass_e2e_provisional(self):
        result = _derive_gate_decision("pass", 0.95, "provisional_pass", 0.90)
        assert result == GateVerdict.CONDITIONAL_PASS

    def test_api_provisional_e2e_pass(self):
        result = _derive_gate_decision("provisional_pass", 0.95, "pass", 0.90)
        assert result == GateVerdict.CONDITIONAL_PASS

    def test_api_fail_e2e_provisional(self):
        result = _derive_gate_decision("fail", 0.95, "provisional_pass", 0.90)
        assert result == GateVerdict.FAIL

    def test_api_provisional_e2e_fail(self):
        result = _derive_gate_decision("provisional_pass", 0.95, "fail", 0.90)
        assert result == GateVerdict.FAIL

    # Edge cases
    def test_no_verdicts(self):
        result = _derive_gate_decision(None, None, None, None)
        assert result == GateVerdict.FAIL

    def test_api_none_e2e_pass(self):
        result = _derive_gate_decision(None, None, "pass", 0.90)
        assert result == GateVerdict.PASS

    def test_api_none_e2e_fail(self):
        result = _derive_gate_decision(None, None, "fail", 0.90)
        assert result == GateVerdict.FAIL

    def test_api_none_e2e_conditional(self):
        result = _derive_gate_decision(None, None, "conditional_pass", 0.90)
        assert result == GateVerdict.CONDITIONAL_PASS


class TestEvaluateGate:
    """Integration tests for evaluate_gate function."""

    def test_evaluate_gate_both_pass(self, tmp_path):
        api_settle = {"verdict": "pass", "confidence": 0.95}
        e2e_settle = {"verdict": "pass", "confidence": 0.90}

        api_path = tmp_path / "api_settlement.yaml"
        e2e_path = tmp_path / "e2e_settlement.yaml"

        import yaml
        api_path.write_text(yaml.safe_dump(api_settle))
        e2e_path.write_text(yaml.safe_dump(e2e_settle))

        gate = evaluate_gate(api_path, e2e_path, "FEAT-001")

        assert gate.verdict == GateVerdict.PASS
        assert gate.feature_id == "FEAT-001"
        assert "pass" in gate.reason
        assert "Final decision: pass" in gate.reason

    def test_evaluate_gate_api_only_pass(self, tmp_path):
        api_settle = {"verdict": "pass", "confidence": 0.95}
        api_path = tmp_path / "api_settlement.yaml"

        import yaml
        api_path.write_text(yaml.safe_dump(api_settle))

        gate = evaluate_gate(api_path, None, "FEAT-002")

        assert gate.verdict == GateVerdict.PASS
        assert gate.feature_id == "FEAT-002"

    def test_evaluate_gate_any_fail_is_fail(self, tmp_path):
        api_settle = {"verdict": "pass", "confidence": 0.95}
        e2e_settle = {"verdict": "fail", "confidence": 0.90}

        api_path = tmp_path / "api_settlement.yaml"
        e2e_path = tmp_path / "e2e_settlement.yaml"

        import yaml
        api_path.write_text(yaml.safe_dump(api_settle))
        e2e_path.write_text(yaml.safe_dump(e2e_settle))

        gate = evaluate_gate(api_path, e2e_path, "FEAT-003")

        assert gate.verdict == GateVerdict.FAIL
        assert "fail" in gate.reason
        assert "Final decision: fail" in gate.reason

    def test_evaluate_gate_wrapped_dict(self, tmp_path):
        """Test with dict wrapped in chain key."""
        api_settle = {"api_settlement": {"verdict": "conditional_pass", "confidence": 0.90}}
        api_path = tmp_path / "api_settlement.yaml"

        import yaml
        api_path.write_text(yaml.safe_dump(api_settle))

        gate = evaluate_gate(api_path, None, "FEAT-004")

        assert gate.verdict == GateVerdict.CONDITIONAL_PASS

    def test_evaluate_gate_derives_feature_id_from_settlement(self, tmp_path):
        api_settle = {"verdict": "pass", "confidence": 0.95, "feature_id": "FEAT-AUTO"}
        api_path = tmp_path / "api_settlement.yaml"

        import yaml
        api_path.write_text(yaml.safe_dump(api_settle))

        gate = evaluate_gate(api_path, None, "")

        assert gate.feature_id == "FEAT-AUTO"


class TestGateInput:
    """Tests for GateInput dataclass."""

    def test_gate_input_defaults(self):
        inp = GateInput(api_settlement_path="/path/to/api.yaml")
        assert inp.api_settlement_path == "/path/to/api.yaml"
        assert inp.e2e_settlement_path is None

    def test_gate_input_full(self):
        inp = GateInput(
            api_settlement_path="/api.yaml",
            e2e_settlement_path="/e2e.yaml",
        )
        assert inp.e2e_settlement_path == "/e2e.yaml"


class TestWriteGateOutput:
    """Tests for write_gate_output function."""

    def test_write_gate_output(self, tmp_path):
        from cli.lib.gate_schema import Gate
        import yaml

        gate = Gate(
            artifact_type="gate",
            gate_id="GATE-001",
            verdict=GateVerdict.PASS,
            feature_id="FEAT-001",
            evaluated_at="2026-04-24T00:00:00Z",
            reason="All verdicts passed",
            notes=None,
        )

        output_path = tmp_path / "release_gate_input.yaml"
        write_gate_output(gate, output_path)

        assert output_path.exists()

        data = yaml.safe_load(output_path.read_text())
        assert data["gate"]["gate_id"] == "GATE-001"
        assert data["gate"]["verdict"] == "pass"
        assert data["gate"]["feature_id"] == "FEAT-001"
        assert data["gate"]["reason"] == "All verdicts passed"


class TestFullTruthTable:
    """Comprehensive tests covering all rows of the truth table."""

    @pytest.mark.parametrize("api_verdict,e2e_verdict,expected", [
        # Both PASS
        ("pass", "pass", GateVerdict.PASS),
        # Any FAIL
        ("fail", "pass", GateVerdict.FAIL),
        ("pass", "fail", GateVerdict.FAIL),
        ("fail", "fail", GateVerdict.FAIL),
        # Missing E2E
        ("pass", None, GateVerdict.PASS),
        ("fail", None, GateVerdict.FAIL),
        ("conditional_pass", None, GateVerdict.CONDITIONAL_PASS),
        ("provisional_pass", None, GateVerdict.CONDITIONAL_PASS),
        # Mixed PASS/CONDITIONAL
        ("pass", "conditional_pass", GateVerdict.CONDITIONAL_PASS),
        ("conditional_pass", "pass", GateVerdict.CONDITIONAL_PASS),
        ("conditional_pass", "conditional_pass", GateVerdict.CONDITIONAL_PASS),
        # FAIL overrides conditional
        ("fail", "conditional_pass", GateVerdict.FAIL),
        ("conditional_pass", "fail", GateVerdict.FAIL),
        # Mixed PASS/PROVISIONAL
        ("pass", "provisional_pass", GateVerdict.CONDITIONAL_PASS),
        ("provisional_pass", "pass", GateVerdict.CONDITIONAL_PASS),
        # FAIL overrides provisional
        ("fail", "provisional_pass", GateVerdict.FAIL),
        ("provisional_pass", "fail", GateVerdict.FAIL),
        # Missing API (E2E only)
        (None, "pass", GateVerdict.PASS),
        (None, "fail", GateVerdict.FAIL),
        (None, "conditional_pass", GateVerdict.CONDITIONAL_PASS),
        # Neither available
        (None, None, GateVerdict.FAIL),
    ])
    def test_truth_table_row(self, api_verdict, e2e_verdict, expected):
        result = _derive_gate_decision(
            api_verdict, 0.95 if api_verdict else None,
            e2e_verdict, 0.90 if e2e_verdict else None,
        )
        assert result == expected, f"Failed for API={api_verdict}, E2E={e2e_verdict}"
