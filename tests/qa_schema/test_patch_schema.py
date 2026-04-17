"""Tests for patch_schema.py — PatchExperience schema validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.lib.patch_schema import (
    ChangeClass,
    PatchSchemaError,
    PatchSource,
    PatchStatus,
    validate_file,
    validate_patch,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    import yaml

    with open(FIXTURE_DIR / name, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("experience_patch", data)


# ---------------------------------------------------------------------------
# PatchSource dataclass tests
# ---------------------------------------------------------------------------


class TestPatchSource:
    def test_has_reviewed_at_field(self):
        source = PatchSource(
            actor="ai_suggested",
            human_confirmed_class="ui_flow",
            reviewed_at="2026-04-16T10:05:00Z",
        )
        assert source.reviewed_at == "2026-04-16T10:05:00Z"

    def test_reviewed_at_defaults_to_none(self):
        source = PatchSource(actor="ai_suggested")
        assert source.reviewed_at is None


# ---------------------------------------------------------------------------
# validate_patch — test_impact enforcement (D-04)
# ---------------------------------------------------------------------------


class TestValidatePatchTestImpact:
    def test_interaction_patch_without_test_impact_raises(self):
        data = _load_fixture("valid_patch.yaml")
        data["change_class"] = "interaction"
        data["test_impact"] = None

        with pytest.raises(PatchSchemaError, match="missing test_impact"):
            validate_patch(data)

    def test_visual_patch_without_test_impact_passes(self):
        """Visual (non-interaction) patches don't require test_impact."""
        data = _load_fixture("valid_patch.yaml")
        data["change_class"] = "layout"
        data["test_impact"] = None

        result = validate_patch(data)
        assert result is not None

    def test_interaction_patch_with_valid_test_impact_passes(self):
        data = _load_fixture("valid_patch.yaml")
        data["change_class"] = "interaction"
        data["test_impact"] = {
            "impacts_user_path": True,
            "impacts_acceptance": False,
            "affected_routes": ["training-plan"],
            "test_changes_required": [],
        }

        result = validate_patch(data)
        assert result is not None

    def test_reviewed_at_before_created_at_raises(self):
        data = _load_fixture("valid_patch.yaml")
        data["source"]["reviewed_at"] = "2026-04-15T10:00:00Z"  # before created_at

        with pytest.raises(PatchSchemaError, match="reviewed_at.*must be >= created_at"):
            validate_patch(data)

    def test_patch_without_reviewed_at_passes(self):
        data = _load_fixture("valid_patch.yaml")
        data["source"]["reviewed_at"] = None

        result = validate_patch(data)
        assert result is not None


# ---------------------------------------------------------------------------
# validate_patch — basic validation
# ---------------------------------------------------------------------------


class TestValidatePatchBasic:
    def test_valid_patch_passes(self):
        data = _load_fixture("valid_patch.yaml")
        result = validate_patch(data)
        assert result["id"] == "UXPATCH-0001"

    def test_missing_id_raises(self):
        data = _load_fixture("valid_patch.yaml")
        del data["id"]
        with pytest.raises(PatchSchemaError, match="required field 'id'"):
            validate_patch(data)

    def test_invalid_change_class_raises(self):
        data = _load_fixture("valid_patch.yaml")
        data["change_class"] = "invalid_class"
        with pytest.raises(PatchSchemaError, match="change_class must be one of"):
            validate_patch(data)

    def test_invalid_status_raises(self):
        data = _load_fixture("valid_patch.yaml")
        data["status"] = "bogus"
        with pytest.raises(PatchSchemaError, match="status must be one of"):
            validate_patch(data)


# ---------------------------------------------------------------------------
# validate_file entry point
# ---------------------------------------------------------------------------


class TestValidateFile:
    def test_valid_patch_file(self):
        path = FIXTURE_DIR / "valid_patch.yaml"
        result = validate_file(path, "patch")
        assert result["id"] == "UXPATCH-0001"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_file("/nonexistent/path.yaml", "patch")
