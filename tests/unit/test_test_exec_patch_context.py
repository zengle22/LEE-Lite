"""Tests for PatchContext and resolve_patch_context() in test_exec_artifacts.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def test_patch_context_importable() -> None:
    """PatchContext should be importable from test_exec_artifacts."""
    from cli.lib.test_exec_artifacts import PatchContext  # noqa: F401


def test_resolve_patch_context_importable() -> None:
    """resolve_patch_context should be importable from test_exec_artifacts."""
    from cli.lib.test_exec_artifacts import resolve_patch_context  # noqa: F401


def test_patch_context_is_frozen() -> None:
    """PatchContext should be a frozen dataclass."""
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=False,
        validated_patches=[],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    # Frozen dataclass cannot be modified
    with pytest.raises(AttributeError):
        ctx.has_active_patches = True  # type: ignore


def test_patch_context_has_seven_fields() -> None:
    """PatchContext should have exactly 7 fields."""
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=False,
        validated_patches=[],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    assert not ctx.has_active_patches
    assert ctx.validated_patches == []
    assert ctx.pending_patches == []
    assert ctx.conflict_resolution == {}
    assert ctx.directory_hash == ""
    assert ctx.reviewed_at_latest is None
    assert ctx.feat_ref is None


def _write_patch_file(parent: Path, feat_id: str, patch_id: str, status: str, change_class: str = "interaction") -> Path:
    """Helper to write a UXPATCH YAML file."""
    patch_dir = parent / "ssot" / "experience-patches" / feat_id
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch_file = patch_dir / f"{patch_id}.yaml"
    data = {
        "experience_patch": {
            "id": patch_id,
            "type": "experience_patch",
            "status": status,
            "created_at": "2026-04-15T10:00:00Z",
            "updated_at": "2026-04-15T10:00:00Z",
            "title": f"Test patch {patch_id}",
            "summary": "Test summary",
            "source": {
                "from": "test",
                "actor": "human",
                "session": "test-session",
                "prompt_ref": "test://prompt",
                "human_confirmed_class": change_class,
                "reviewed_at": "2026-04-16T10:00:00Z",
            },
            "scope": {
                "feat_ref": feat_id,
                "page": "test-page",
                "module": "test-module",
            },
            "change_class": change_class,
            "test_impact": {
                "impacts_user_path": True,
                "affected_routes": ["test.route"],
            } if change_class in ("interaction", "semantic") else None,
        }
    }
    patch_file.write_text(yaml.safe_dump(data), encoding="utf-8")
    return patch_file


def test_resolve_patch_context_no_patches_dir_returns_empty_context(tmp_path: Path) -> None:
    """When ssot/experience-patches/ does not exist, return empty PatchContext."""
    from cli.lib.test_exec_artifacts import PatchContext, resolve_patch_context

    ctx = resolve_patch_context(tmp_path)
    assert isinstance(ctx, PatchContext)
    assert not ctx.has_active_patches
    assert ctx.validated_patches == []
    assert ctx.pending_patches == []
    assert ctx.directory_hash == ""


def test_resolve_patch_context_no_patches_has_active_false(tmp_path: Path) -> None:
    """When no patches exist, has_active_patches should be False."""
    from cli.lib.test_exec_artifacts import resolve_patch_context

    ctx = resolve_patch_context(tmp_path)
    assert not ctx.has_active_patches


def test_resolve_patch_context_with_validated_patch(tmp_path: Path) -> None:
    """Validated patch should appear in validated_patches list."""
    from cli.lib.test_exec_artifacts import resolve_patch_context

    _write_patch_file(tmp_path, "FEAT-ABC", "UXPATCH-0001", "validated")
    ctx = resolve_patch_context(tmp_path)

    assert ctx.has_active_patches
    assert len(ctx.validated_patches) == 1
    assert ctx.validated_patches[0]["id"] == "UXPATCH-0001"
    assert ctx.pending_patches == []


def test_resolve_patch_context_with_pending_patch(tmp_path: Path) -> None:
    """pending_backwrite patch should appear in pending_patches list."""
    from cli.lib.test_exec_artifacts import resolve_patch_context

    _write_patch_file(tmp_path, "FEAT-ABC", "UXPATCH-0002", "pending_backwrite")
    ctx = resolve_patch_context(tmp_path)

    assert ctx.has_active_patches
    assert ctx.validated_patches == []
    assert len(ctx.pending_patches) == 1
    assert ctx.pending_patches[0]["id"] == "UXPATCH-0002"


def test_resolve_patch_context_computes_directory_hash(tmp_path: Path) -> None:
    """directory_hash should be a non-empty string when patches exist."""
    from cli.lib.test_exec_artifacts import resolve_patch_context

    _write_patch_file(tmp_path, "FEAT-ABC", "UXPATCH-0001", "validated")
    ctx = resolve_patch_context(tmp_path)

    assert isinstance(ctx.directory_hash, str)
    assert len(ctx.directory_hash) > 0


def test_resolve_patch_context_empty_dir_hash_empty_string(tmp_path: Path) -> None:
    """Empty directory should have empty string for directory_hash."""
    from cli.lib.test_exec_artifacts import resolve_patch_context

    # Create empty patches dir
    (tmp_path / "ssot" / "experience-patches").mkdir(parents=True)
    ctx = resolve_patch_context(tmp_path)

    assert ctx.directory_hash == ""


def test_resolve_patch_context_filters_by_feat_ref(tmp_path: Path) -> None:
    """When feat_ref is provided, only patches from that feat are returned."""
    from cli.lib.test_exec_artifacts import resolve_patch_context

    _write_patch_file(tmp_path, "FEAT-ABC", "UXPATCH-0001", "validated")
    _write_patch_file(tmp_path, "FEAT-XYZ", "UXPATCH-0002", "validated")

    ctx = resolve_patch_context(tmp_path, feat_ref="FEAT-ABC")

    assert len(ctx.validated_patches) == 1
    assert ctx.validated_patches[0]["id"] == "UXPATCH-0001"


def test_resolve_patch_context_feat_ref_mismatch_returns_empty(tmp_path: Path) -> None:
    """When feat_ref doesn't match any patches, validated_patches is empty."""
    from cli.lib.test_exec_artifacts import resolve_patch_context

    _write_patch_file(tmp_path, "FEAT-ABC", "UXPATCH-0001", "validated")
    ctx = resolve_patch_context(tmp_path, feat_ref="FEAT-NOMATCH")

    assert ctx.validated_patches == []


def test_compute_patch_dir_hash_consistent(tmp_path: Path) -> None:
    """_compute_patch_dir_hash returns consistent sha1 for same contents."""
    from cli.lib.test_exec_artifacts import _compute_patch_dir_hash

    patches_dir = tmp_path / "patches"
    patches_dir.mkdir()
    (patches_dir / "UXPATCH-0001.yaml").write_text("key: value", encoding="utf-8")

    hash1 = _compute_patch_dir_hash(patches_dir)
    hash2 = _compute_patch_dir_hash(patches_dir)

    assert hash1 == hash2


def test_compute_patch_dir_hash_differs_on_change(tmp_path: Path) -> None:
    """_compute_patch_dir_hash returns different hash when contents change."""
    from cli.lib.test_exec_artifacts import _compute_patch_dir_hash

    patches_dir = tmp_path / "patches"
    patches_dir.mkdir()
    (patches_dir / "UXPATCH-0001.yaml").write_text("key: value1", encoding="utf-8")

    hash1 = _compute_patch_dir_hash(patches_dir)

    (patches_dir / "UXPATCH-0001.yaml").write_text("key: value2", encoding="utf-8")
    hash2 = _compute_patch_dir_hash(patches_dir)

    assert hash1 != hash2


def test_latest_reviewed_at_returns_none_when_no_patches() -> None:
    """_latest_reviewed_at returns None when no patches have reviewed_at."""
    from cli.lib.test_exec_artifacts import _latest_reviewed_at

    result = _latest_reviewed_at([])
    assert result is None


def test_latest_reviewed_at_returns_max_timestamp() -> None:
    """_latest_reviewed_at returns the maximum timestamp across patches."""
    from cli.lib.test_exec_artifacts import _latest_reviewed_at

    patches = [
        {"source": {"reviewed_at": "2026-04-15T10:00:00Z"}},
        {"source": {"reviewed_at": "2026-04-17T10:00:00Z"}},
        {"source": {"reviewed_at": "2026-04-16T10:00:00Z"}},
    ]
    result = _latest_reviewed_at(patches)
    assert result == "2026-04-17T10:00:00Z"


def test_load_and_validate_patch_returns_none_for_malformed_yaml(tmp_path: Path) -> None:
    """_load_and_validate_patch returns None for malformed YAML."""
    from cli.lib.test_exec_artifacts import _load_and_validate_patch

    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("  invalid: yaml: content:", encoding="utf-8")

    result = _load_and_validate_patch(bad_file)
    assert result is None


def test_load_and_validate_patch_returns_none_for_non_dict(tmp_path: Path) -> None:
    """_load_and_validate_patch returns None when YAML parses to non-dict."""
    from cli.lib.test_exec_artifacts import _load_and_validate_patch

    bad_file = tmp_path / "list.yaml"
    bad_file.write_text("- item1\n- item2", encoding="utf-8")

    result = _load_and_validate_patch(bad_file)
    assert result is None


def test_load_and_validate_patch_extracts_experience_patch_key(tmp_path: Path) -> None:
    """_load_and_validate_patch extracts experience_patch from wrapper dict."""
    from cli.lib.test_exec_artifacts import _load_and_validate_patch

    patch_file = tmp_path / "UXPATCH-0001.yaml"
    data = {"experience_patch": {"id": "UXPATCH-0001", "title": "Test"}}
    patch_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    result = _load_and_validate_patch(patch_file)
    assert result is not None
    assert result["id"] == "UXPATCH-0001"


def test_build_conflict_resolution_map_returns_warn_for_visual() -> None:
    """_build_conflict_resolution_map returns 'warn' for visual patches."""
    from cli.lib.test_exec_artifacts import _build_conflict_resolution_map

    patches = [
        {
            "id": "UXPATCH-0001",
            "change_class": "visual",
            "test_impact": {"affected_routes": ["route.one"]},
        }
    ]
    result = _build_conflict_resolution_map(patches)
    assert result.get("route.one") == "warn"


def test_build_conflict_resolution_map_returns_use_patch_for_interaction() -> None:
    """_build_conflict_resolution_map returns 'use_patch' for interaction patches."""
    from cli.lib.test_exec_artifacts import _build_conflict_resolution_map

    patches = [
        {
            "id": "UXPATCH-0001",
            "change_class": "interaction",
            "test_impact": {"affected_routes": ["route.two"]},
        }
    ]
    result = _build_conflict_resolution_map(patches)
    assert result.get("route.two") == "use_patch"
