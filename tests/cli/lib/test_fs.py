"""Integration tests for enum_guard SSOT write path in cli.lib.fs."""

import json
import pytest
from pathlib import Path

from cli.lib.errors import CommandError
from cli.lib.fs import _is_ssot_path, _inject_fc_refs, write_json


class TestIsSsotPath:
    def test_ssot_yaml_returns_true(self, tmp_path):
        p = tmp_path / "ssot" / "test.yaml"
        p.parent.mkdir(parents=True)
        p.touch()
        assert _is_ssot_path(p) is True

    def test_ssot_nested_json_returns_true(self, tmp_path):
        p = tmp_path / "ssot" / "sub" / "test.json"
        p.parent.mkdir(parents=True)
        p.touch()
        assert _is_ssot_path(p) is True

    def test_frz_yaml_returns_false(self, tmp_path):
        p = tmp_path / "frz" / "test.yaml"
        p.parent.mkdir(parents=True)
        p.touch()
        assert _is_ssot_path(p) is False

    def test_frz_nested_returns_false(self, tmp_path):
        p = tmp_path / "frz" / "sub" / "test.yaml"
        p.parent.mkdir(parents=True)
        p.touch()
        assert _is_ssot_path(p) is False

    def test_tmp_path_returns_false(self, tmp_path):
        p = tmp_path / "tmp" / "data.json"
        p.parent.mkdir(parents=True)
        p.touch()
        assert _is_ssot_path(p) is False

    def test_absolute_ssot_path_returns_true(self, tmp_path):
        p = tmp_path / "ssot" / "absolute" / "test.json"
        p.parent.mkdir(parents=True)
        p.touch()
        assert p.is_absolute()
        assert _is_ssot_path(p) is True


class TestInjectFcRefs:
    def test_adds_fc_refs_to_empty_dict(self):
        result = _inject_fc_refs({})
        assert "fc_refs" in result
        assert len(result["fc_refs"]) == 7

    def test_adds_fc_refs_to_existing_data(self):
        data = {"key": "val"}
        result = _inject_fc_refs(data)
        assert "key" in result
        assert result["key"] == "val"
        assert "fc_refs" in result
        assert data == {"key": "val"}

    def test_does_not_overwrite_existing_fc_refs(self):
        data = {"fc_refs": ["custom"]}
        result = _inject_fc_refs(data)
        assert result["fc_refs"] == ["custom"]
        assert result is data

    def test_fc_refs_contains_all_seven(self):
        result = _inject_fc_refs({})
        expected = ["FC-001", "FC-002", "FC-003", "FC-004", "FC-005", "FC-006", "FC-007"]
        assert result["fc_refs"] == expected

    def test_original_not_mutated(self):
        data = {"key": "value"}
        _inject_fc_refs(data)
        assert "fc_refs" not in data


class TestWriteJsonSsotIntegration:
    def test_ssot_write_adds_fc_refs_to_file(self, tmp_path):
        ssot = tmp_path / "ssot"
        ssot.mkdir()
        f = ssot / "test.json"
        write_json(f, {"data": "value"})
        written = json.loads(f.read_text())
        assert "fc_refs" in written
        assert "FC-001" in written["fc_refs"]

    def test_ssot_write_valid_enums_succeeds(self, tmp_path):
        ssot = tmp_path / "ssot"
        ssot.mkdir()
        f = ssot / "test.json"
        write_json(f, {"skill_id": "qa.test-plan"})
        written = json.loads(f.read_text())
        assert "fc_refs" in written

    def test_ssot_write_invalid_enum_raises_command_error(self, tmp_path):
        ssot = tmp_path / "ssot"
        ssot.mkdir()
        f = ssot / "test.json"
        with pytest.raises(CommandError) as exc_info:
            write_json(f, {"skill_id": "invalid_skill"})
        assert exc_info.value.status_code == "INVARIANT_VIOLATION"

    def test_ssot_write_invalid_enum_error_message_includes_field_value_allowed(self, tmp_path):
        ssot = tmp_path / "ssot"
        ssot.mkdir()
        f = ssot / "test.json"
        with pytest.raises(CommandError) as exc_info:
            write_json(f, {"skill_id": "invalid_skill"})
        msg = exc_info.value.message
        assert "skill_id" in msg
        assert "invalid_skill" in msg
        assert "qa.test-plan" in msg

    def test_non_ssot_write_skips_enum_guard(self, tmp_path):
        f = tmp_path / "test.json"
        write_json(f, {"skill_id": "anything_goes"})
        written = json.loads(f.read_text())
        assert "fc_refs" not in written
        assert written["skill_id"] == "anything_goes"

    def test_frz_write_skips_enum_guard(self, tmp_path):
        frz = tmp_path / "frz"
        frz.mkdir()
        f = frz / "test.json"
        write_json(f, {"skill_id": "invalid"})
        written = json.loads(f.read_text())
        assert "fc_refs" not in written
        assert written["skill_id"] == "invalid"

    def test_ssot_write_multiple_enum_fields_all_validated(self, tmp_path):
        ssot = tmp_path / "ssot"
        ssot.mkdir()
        f = ssot / "test.json"
        with pytest.raises(CommandError) as exc_info:
            write_json(f, {"skill_id": "invalid", "phase": "99"})
        assert exc_info.value.status_code == "INVARIANT_VIOLATION"
        assert len(exc_info.value.diagnostics) >= 2
