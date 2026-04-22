"""Tests for cli.lib.gate_schema."""

import pytest

from cli.lib.gate_schema import (
    Gate,
    GateSchemaError,
    GateVerdict,
    validate,
    validate_file,
)


class TestValidate:
    def test_valid_pass(self):
        result = validate({"gate_id": "GATE-001", "verdict": "pass"})
        assert result.gate_id == "GATE-001"
        assert result.verdict == GateVerdict.PASS

    def test_valid_conditional_pass(self):
        result = validate({"gate_id": "GATE-002", "verdict": "conditional_pass"})
        assert result.verdict == GateVerdict.CONDITIONAL_PASS

    def test_valid_fail(self):
        result = validate({"gate_id": "GATE-003", "verdict": "fail"})
        assert result.verdict == GateVerdict.FAIL

    def test_valid_provisional_pass(self):
        result = validate({"gate_id": "GATE-004", "verdict": "provisional_pass"})
        assert result.verdict == GateVerdict.PROVISIONAL_PASS

    def test_valid_full_dict(self):
        data = {
            "gate_id": "GATE-005",
            "verdict": "pass",
            "feature_id": "FEAT-001",
            "evaluated_at": "2026-04-22",
            "reason": "All tests passed",
            "notes": "no issues",
        }
        result = validate(data)
        assert result.feature_id == "FEAT-001"
        assert result.reason == "All tests passed"

    def test_wrapped_in_gate_key(self):
        data = {"gate": {"gate_id": "GATE-006", "verdict": "pass"}}
        result = validate(data)
        assert result.gate_id == "GATE-006"

    def test_unknown_verdict(self):
        with pytest.raises(GateSchemaError, match="verdict must be one of"):
            validate({"gate_id": "GATE-BAD", "verdict": "unknown_value"})

    def test_skip_verdict(self):
        with pytest.raises(GateSchemaError, match="verdict must be one of"):
            validate({"gate_id": "GATE-BAD", "verdict": "skip"})

    def test_missing_verdict(self):
        with pytest.raises(GateSchemaError, match="required field 'verdict'"):
            validate({"gate_id": "GATE-BAD"})

    def test_forbidden_hidden_verifier_failure(self):
        with pytest.raises(GateSchemaError, match="forbidden field 'hidden_verifier_failure'"):
            validate({"gate_id": "GATE-BAD", "verdict": "pass", "hidden_verifier_failure": True})


class TestValidateFile:
    def test_valid_yaml_file(self, tmp_path):
        f = tmp_path / "gate.yaml"
        f.write_text("gate_id: GATE-FILE\nverdict: pass\n")
        result = validate_file(str(f))
        assert result.gate_id == "GATE-FILE"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Gate file not found"):
            validate_file("/nonexistent/file.yaml")

    def test_forbidden_field_in_file(self, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("gate_id: GATE-BAD\nverdict: pass\nhidden_verifier_failure: true\n")
        with pytest.raises(GateSchemaError, match="forbidden field 'hidden_verifier_failure'"):
            validate_file(str(f))

    def test_auto_detect_schema_type(self, tmp_path):
        f = tmp_path / "detect.yaml"
        f.write_text("gate:\n  gate_id: GATE-AUTO\n  verdict: fail\n")
        result = validate_file(str(f))
        assert result.gate_id == "GATE-AUTO"

    def test_invalid_verdict_in_file(self, tmp_path):
        f = tmp_path / "bad_verdict.yaml"
        f.write_text("gate_id: GATE-BAD\nverdict: unknown\n")
        with pytest.raises(GateSchemaError, match="verdict must be one of"):
            validate_file(str(f))


class TestGateDataclass:
    def test_defaults(self):
        g = Gate()
        assert g.artifact_type == "gate"
        assert g.gate_id is None
        assert g.verdict is None
        assert g.feature_id is None
        assert g.evaluated_at is None
        assert g.reason is None
        assert g.notes is None

    def test_frozen(self):
        g = Gate(gate_id="GATE-F")
        with pytest.raises(Exception):
            g.gate_id = "CHANGED"


class TestGateVerdictEnum:
    def test_values(self):
        assert GateVerdict.PASS.value == "pass"
        assert GateVerdict.CONDITIONAL_PASS.value == "conditional_pass"
        assert GateVerdict.FAIL.value == "fail"
        assert GateVerdict.PROVISIONAL_PASS.value == "provisional_pass"

    def test_count(self):
        assert len(GateVerdict) == 4
