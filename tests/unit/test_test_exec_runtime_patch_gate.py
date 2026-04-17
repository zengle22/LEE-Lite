"""Tests for _check_patch_test_impact gate in test_exec_runtime.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


def test_check_patch_test_impact_empty_patch_context_returns_empty_list() -> None:
    """_check_patch_test_impact with empty patch_context returns []"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
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
    result = _check_patch_test_impact(ctx, Path("."))
    assert result == []


def test_check_patch_test_impact_no_active_patches_returns_empty_list() -> None:
    """_check_patch_test_impact with has_active_patches=False returns []"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
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
    result = _check_patch_test_impact(ctx, Path("."))
    assert result == []


def test_check_patch_test_impact_visual_patch_without_test_impact_returns_empty() -> None:
    """visual patch without test_impact returns [] (D-05)"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=True,
        validated_patches=[
            {
                "id": "UXPATCH-0001",
                "change_class": "visual",
                "test_impact": None,
            }
        ],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="abc123",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    result = _check_patch_test_impact(ctx, Path("."))
    assert result == []


def test_check_patch_test_impact_visual_patch_with_empty_affected_routes_returns_warn() -> None:
    """visual patch with test_impact but no affected_routes returns WARN"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=True,
        validated_patches=[
            {
                "id": "UXPATCH-0001",
                "change_class": "visual",
                "test_impact": {
                    "impacts_user_path": True,
                    "affected_routes": [],
                },
            }
        ],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="abc123",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    result = _check_patch_test_impact(ctx, Path("."))
    assert len(result) == 1
    assert result[0].startswith("WARN")
    assert "affected_routes" in result[0]


def test_check_patch_test_impact_interaction_patch_without_test_impact_returns_error() -> None:
    """interaction patch without test_impact returns ERROR (D-04)"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=True,
        validated_patches=[
            {
                "id": "UXPATCH-0001",
                "change_class": "interaction",
                "test_impact": None,
            }
        ],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="abc123",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    result = _check_patch_test_impact(ctx, Path("."))
    assert len(result) == 1
    assert result[0].startswith("ERROR")
    assert "missing test_impact" in result[0]


def test_check_patch_test_impact_semantic_patch_without_test_impact_returns_error() -> None:
    """semantic patch without test_impact returns ERROR (D-04)"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=True,
        validated_patches=[
            {
                "id": "UXPATCH-0001",
                "change_class": "semantic",
                "test_impact": None,
            }
        ],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="abc123",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    result = _check_patch_test_impact(ctx, Path("."))
    assert len(result) == 1
    assert result[0].startswith("ERROR")
    assert "missing test_impact" in result[0]


def test_check_patch_test_impact_interaction_patch_with_empty_affected_routes_returns_error() -> None:
    """interaction patch with empty affected_routes returns ERROR"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=True,
        validated_patches=[
            {
                "id": "UXPATCH-0001",
                "change_class": "interaction",
                "test_impact": {
                    "impacts_user_path": True,
                    "affected_routes": [],
                },
            }
        ],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="abc123",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    result = _check_patch_test_impact(ctx, Path("."))
    assert len(result) == 1
    assert result[0].startswith("ERROR")
    assert "empty affected_routes" in result[0]


def test_check_patch_test_impact_interaction_patch_with_valid_test_impact_returns_empty() -> None:
    """interaction patch with valid test_impact returns []"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=True,
        validated_patches=[
            {
                "id": "UXPATCH-0001",
                "change_class": "interaction",
                "test_impact": {
                    "impacts_user_path": True,
                    "affected_routes": ["api.users"],
                },
            }
        ],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="abc123",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    result = _check_patch_test_impact(ctx, Path("."))
    assert result == []


def test_check_patch_test_impact_semantic_patch_with_valid_test_impact_returns_empty() -> None:
    """semantic patch with valid test_impact returns []"""
    from cli.lib.test_exec_runtime import _check_patch_test_impact
    from cli.lib.test_exec_artifacts import PatchContext

    ctx = PatchContext(
        has_active_patches=True,
        validated_patches=[
            {
                "id": "UXPATCH-0001",
                "change_class": "semantic",
                "test_impact": {
                    "impacts_acceptance": True,
                    "affected_routes": ["api.orders"],
                },
            }
        ],
        pending_patches=[],
        conflict_resolution={},
        directory_hash="abc123",
        reviewed_at_latest=None,
        feat_ref=None,
    )
    result = _check_patch_test_impact(ctx, Path("."))
    assert result == []
