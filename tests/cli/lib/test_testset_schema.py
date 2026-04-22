"""Tests for cli.lib.testset_schema."""

import pytest

from cli.lib.testset_schema import (
    Testset,
    TestsetSchemaError,
    validate,
    validate_file,
)


class TestValidate:
    def test_valid_minimal_dict(self):
        result = validate({"testset_id": "TS-001"})
        assert result.testset_id == "TS-001"
        assert result.artifact_type == "testset"
        assert result.source_feat_refs == []
        assert result.tasks == []

    def test_valid_full_dict(self):
        data = {
            "testset_id": "TS-002",
            "source_feat_refs": ["FEAT-001"],
            "environment_ref": "ENV-001",
            "gate_ref": "GATE-001",
            "tasks": [{"task_id": "TASK-001", "type": "impl"}],
            "notes": "test notes",
        }
        result = validate(data)
        assert result.testset_id == "TS-002"
        assert result.source_feat_refs == ["FEAT-001"]
        assert result.environment_ref == "ENV-001"
        assert result.gate_ref == "GATE-001"
        assert len(result.tasks) == 1
        assert result.notes == "test notes"

    def test_wrapped_in_testset_key(self):
        data = {"testset": {"testset_id": "TS-003", "tasks": []}}
        result = validate(data)
        assert result.testset_id == "TS-003"

    def test_forbidden_test_case_pack(self):
        with pytest.raises(TestsetSchemaError, match="forbidden field 'test_case_pack'"):
            validate({"testset_id": "TS-001", "test_case_pack": []})

    def test_forbidden_script_pack(self):
        with pytest.raises(TestsetSchemaError, match="forbidden field 'script_pack'"):
            validate({"testset_id": "TS-001", "script_pack": []})


class TestValidateFile:
    def test_valid_yaml_file(self, tmp_path):
        f = tmp_path / "valid.yaml"
        f.write_text("testset_id: TS-FILE\n")
        result = validate_file(str(f))
        assert result.testset_id == "TS-FILE"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="TESTSET file not found"):
            validate_file("/nonexistent/file.yaml")

    def test_forbidden_field_in_file(self, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("testset_id: TS-BAD\ntest_case_pack: []\n")
        with pytest.raises(TestsetSchemaError, match="forbidden field 'test_case_pack'"):
            validate_file(str(f))

    def test_auto_detect_schema_type(self, tmp_path):
        f = tmp_path / "detect.yaml"
        f.write_text("testset:\n  testset_id: TS-AUTO\n")
        result = validate_file(str(f))
        assert result.testset_id == "TS-AUTO"

    def test_invalid_schema_type(self, tmp_path):
        f = tmp_path / "wrong.yaml"
        f.write_text("other_key: value\n")
        # Falls through to flat-dict validate — no required fields, so parses as valid
        result = validate_file(str(f))
        assert result.artifact_type == "testset"


class TestTestsetDataclass:
    def test_frozen(self):
        t = Testset(testset_id="TS-F")
        with pytest.raises(Exception):  # frozen=True raises various exception types
            t.testset_id = "CHANGED"

    def test_defaults(self):
        t = Testset()
        assert t.artifact_type == "testset"
        assert t.testset_id is None
        assert t.source_feat_refs == []
        assert t.environment_ref is None
        assert t.gate_ref is None
        assert t.tasks == []
        assert t.notes is None
