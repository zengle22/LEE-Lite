"""Unit tests for cli.lib.patch_schema validators.

Fixtures live in tests/qa_schema/fixtures/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.lib.patch_schema import (
    PatchExperience,
    PatchSchemaError,
    validate_file,
    validate_patch,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestValidatePatch:
    def test_valid_patch_from_file(self) -> None:
        result = validate_file(FIXTURES / "valid_patch.yaml", "patch")
        assert isinstance(result, PatchExperience)
        assert result.id == "UXPATCH-0001"
        assert result.type == "experience_patch"
        assert result.status == "active"
        assert result.change_class == "visual"
        assert result.source is not None
        assert result.source.human_confirmed_class == "visual"
        assert result.source.actor == "human"
        assert result.scope is not None
        assert result.scope.feat_ref == "feat.training-plan"

    def test_missing_id(self) -> None:
        with pytest.raises(PatchSchemaError, match="id"):
            validate_patch({
                "type": "experience_patch", "status": "draft",
                "created_at": "2026-04-16T10:00:00Z", "updated_at": "2026-04-16T10:00:00Z",
                "title": "x", "summary": "x",
                "source": {"from": "product_experience", "actor": "human", "session": "s", "prompt_ref": "p", "human_confirmed_class": "visual"},
                "scope": {"feat_ref": "f", "page": "p", "module": "m"},
                "change_class": "visual",
            })

    def test_missing_status(self) -> None:
        with pytest.raises(PatchSchemaError, match="status"):
            validate_patch({
                "id": "UXPATCH-0001", "type": "experience_patch",
                "created_at": "2026-04-16T10:00:00Z", "updated_at": "2026-04-16T10:00:00Z",
                "title": "x", "summary": "x",
                "source": {"from": "product_experience", "actor": "human", "session": "s", "prompt_ref": "p", "human_confirmed_class": "visual"},
                "scope": {"feat_ref": "f", "page": "p", "module": "m"},
                "change_class": "visual",
            })

    def test_invalid_status_enum(self) -> None:
        with pytest.raises(PatchSchemaError, match="status"):
            validate_patch({
                "id": "UXPATCH-0001", "type": "experience_patch",
                "status": "invalid_status",
                "created_at": "2026-04-16T10:00:00Z", "updated_at": "2026-04-16T10:00:00Z",
                "title": "x", "summary": "x",
                "source": {"from": "product_experience", "actor": "human", "session": "s", "prompt_ref": "p", "human_confirmed_class": "visual"},
                "scope": {"feat_ref": "f", "page": "p", "module": "m"},
                "change_class": "visual",
            })

    def test_invalid_change_class(self) -> None:
        with pytest.raises(PatchSchemaError, match="change_class"):
            validate_patch({
                "id": "UXPATCH-0001", "type": "experience_patch",
                "status": "draft",
                "created_at": "2026-04-16T10:00:00Z", "updated_at": "2026-04-16T10:00:00Z",
                "title": "x", "summary": "x",
                "source": {"from": "product_experience", "actor": "human", "session": "s", "prompt_ref": "p", "human_confirmed_class": "visual"},
                "scope": {"feat_ref": "f", "page": "p", "module": "m"},
                "change_class": "invalid_value",
            })

    def test_missing_source(self) -> None:
        with pytest.raises(PatchSchemaError, match="source"):
            validate_patch({
                "id": "UXPATCH-0001", "type": "experience_patch",
                "status": "draft",
                "created_at": "2026-04-16T10:00:00Z", "updated_at": "2026-04-16T10:00:00Z",
                "title": "x", "summary": "x",
                "scope": {"feat_ref": "f", "page": "p", "module": "m"},
                "change_class": "visual",
            })

    def test_missing_human_confirmed_class(self) -> None:
        with pytest.raises(PatchSchemaError, match="human_confirmed_class"):
            validate_patch({
                "id": "UXPATCH-0001", "type": "experience_patch",
                "status": "draft",
                "created_at": "2026-04-16T10:00:00Z", "updated_at": "2026-04-16T10:00:00Z",
                "title": "x", "summary": "x",
                "source": {"from": "product_experience", "actor": "human", "session": "s", "prompt_ref": "p"},
                "scope": {"feat_ref": "f", "page": "p", "module": "m"},
                "change_class": "visual",
            })

    def test_optional_fields_defaulted(self) -> None:
        result = validate_patch({
            "id": "UXPATCH-0001", "type": "experience_patch",
            "status": "draft",
            "created_at": "2026-04-16T10:00:00Z", "updated_at": "2026-04-16T10:00:00Z",
            "title": "x", "summary": "x",
            "source": {"from": "product_experience", "actor": "human", "session": "s", "prompt_ref": "p", "human_confirmed_class": "visual"},
            "scope": {"feat_ref": "f", "page": "p", "module": "m"},
            "change_class": "visual",
        })
        assert result.severity is None
        assert result.conflict is False
        assert result.test_impact is None
        assert result.resolution is None
