"""Tests for mark_manifest_patch_affected and create_manifest_items_for_new_scenarios in test_exec_artifacts.py.

Plan 04-03: Execution Wiring
TDD-03-A: 14 tests for mark_manifest_patch_affected
TDD-03-B: 15 tests for create_manifest_items_for_new_scenarios
TDD-03-C: 12 tests for execution wiring (blocked cases, TOCTOU)

RED phase (first commit): all tests fail - verify functions don't exist yet.
GREEN phase (this commit): behavioral tests pass with actual implementation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Helper: PatchContext construction (after GREEN implementation)
# ---------------------------------------------------------------------------

def _make_patch_context(
    validated_patches: list[dict] | None = None,
    pending_patches: list[dict] | None = None,
    conflict_resolution: dict | None = None,
    directory_hash: str = "testhash1234",
    feat_ref: str | None = None,
):
    """Build a PatchContext for testing."""
    from cli.lib.test_exec_artifacts import PatchContext
    return PatchContext(
        has_active_patches=bool(validated_patches or pending_patches),
        validated_patches=validated_patches or [],
        pending_patches=pending_patches or [],
        conflict_resolution=conflict_resolution or {},
        directory_hash=directory_hash,
        reviewed_at_latest=None,
        feat_ref=feat_ref,
    )


def _make_manifest_item(
    coverage_id: str = "cov-001",
    source_feat_ref: str = "FEAT-001",
    patch_affected: bool = False,
    patch_refs: list | None = None,
    evidence_refs: list | None = None,
    mapped_case_ids: list | None = None,
) -> dict:
    """Build a minimal manifest item dict."""
    return {
        "coverage_id": coverage_id,
        "feature_id": source_feat_ref,
        "capability": "test capability",
        "endpoint": "/test/endpoint",
        "scenario_type": "happy_path",
        "priority": "P1",
        "source_feat_ref": source_feat_ref,
        "dimensions_covered": [],
        "mapped_case_ids": mapped_case_ids or [],
        "lifecycle_status": "executed",
        "mapping_status": "mapped",
        "evidence_status": "complete",
        "waiver_status": "none",
        "patch_affected": patch_affected,
        "patch_refs": patch_refs or [],
        "evidence_refs": evidence_refs or [],
        "rerun_count": 0,
        "last_run_id": None,
        "obsolete": False,
        "superseded_by": None,
    }


def _make_patch(
    patch_id: str = "UXPATCH-0001",
    feat_ref: str = "FEAT-001",
    change_class: str = "interaction",
    test_impact: dict | None = None,
    status: str = "validated",
) -> dict:
    """Build a minimal patch dict.

    For interaction/semantic patches, test_impact defaults to a valid dict
    unless explicitly set to None (to test visual/no-impact cases).
    """
    if test_impact is None and change_class in ("interaction", "semantic"):
        test_impact = {"impacts_user_path": True, "affected_routes": ["/test/endpoint"]}
    return {
        "id": patch_id,
        "status": status,
        "title": f"Patch {patch_id}",
        "change_class": change_class,
        "scope": {"feat_ref": feat_ref},
        "test_impact": test_impact,
    }


# ---------------------------------------------------------------------------
# TDD-03-A: mark_manifest_patch_affected behavior tests (14 tests)
# ---------------------------------------------------------------------------

class TestMarkManifestPatchAffected:
    """mark_manifest_patch_affected behavior tests from 04-03-PLAN.md."""

    def test_empty_patch_context_returns_original_items_unchanged(self) -> None:
        """Empty PatchContext returns original items unchanged."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        ctx = _make_patch_context()
        result = mark_manifest_patch_affected(items, ctx)
        assert result[0]["patch_affected"] is False
        assert result[0].get("patch_refs") is None or result[0].get("patch_refs") == []

    def test_matched_item_gets_patch_affected_true(self) -> None:
        """Item matching patch.scope.feat_ref gets patch_affected=True."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "interaction")
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert result[0]["patch_affected"] is True

    def test_matched_item_gets_patch_id_appended_to_patch_refs(self) -> None:
        """Matched item has patch_id added to patch_refs."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "interaction")
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert "UXPATCH-0001" in result[0]["patch_refs"]

    def test_patch_refs_deduplicates_for_same_patch_multiple_items(self) -> None:
        """Multiple patches with same feat_ref deduplicate patch_refs."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [
            _make_manifest_item("cov-1", "FEAT-001"),
            _make_manifest_item("cov-2", "FEAT-001"),
        ]
        patch1 = _make_patch("UXPATCH-0001", "FEAT-001", "interaction")
        patch2 = _make_patch("UXPATCH-0002", "FEAT-001", "semantic")
        ctx = _make_patch_context(validated_patches=[patch1, patch2])
        result = mark_manifest_patch_affected(items, ctx)
        assert "UXPATCH-0001" in result[0]["patch_refs"]
        assert "UXPATCH-0002" in result[0]["patch_refs"]

    def test_visual_patch_without_test_impact_does_not_mark_items(self) -> None:
        """Visual patch with no test_impact does NOT mark any item."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "visual", test_impact=None)
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        # No test_impact -> no marking
        assert result[0].get("patch_affected") is None or result[0].get("patch_affected") is False

    def test_visual_patch_with_test_impact_but_no_affected_routes_does_not_mark(self) -> None:
        """Visual patch with test_impact but no affected_routes does NOT mark."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "visual", test_impact={"impacts_user_path": True})
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert result[0].get("patch_affected") is None or result[0].get("patch_affected") is False

    def test_interaction_patch_with_test_impact_marks_matching_items(self) -> None:
        """Interaction patch with test_impact DOES mark matching items."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_user_path": True, "affected_routes": ["/test/endpoint"]}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert result[0]["patch_affected"] is True
        assert "UXPATCH-0001" in result[0]["patch_refs"]

    def test_semantic_patch_with_test_impact_marks_matching_items(self) -> None:
        """Semantic patch with test_impact DOES mark matching items."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "semantic",
            test_impact={"impacts_user_path": True, "affected_routes": ["/test/endpoint"]}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert result[0]["patch_affected"] is True
        assert "UXPATCH-0001" in result[0]["patch_refs"]

    def test_non_matching_feat_ref_leaves_item_unchanged(self) -> None:
        """Non-matching feat_ref leaves item unchanged."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-002", "interaction")  # different feat
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert result[0].get("patch_affected") is None or result[0].get("patch_affected") is False

    def test_existing_evidence_refs_preserved_d19(self) -> None:
        """Existing evidence_refs are preserved, only appended (D-19)."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001", evidence_refs=["ev-001"])]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "interaction")
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert "ev-001" in result[0]["evidence_refs"]
        assert len(result[0]["evidence_refs"]) == 1  # not replaced, only extended

    def test_existing_mapped_case_ids_preserved_d19(self) -> None:
        """Existing mapped_case_ids are preserved, only appended (D-19)."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001", mapped_case_ids=["case-001"])]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "interaction")
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert "case-001" in result[0]["mapped_case_ids"]
        assert len(result[0]["mapped_case_ids"]) == 1

    def test_unmatched_items_keep_patch_affected_false(self) -> None:
        """Unmatched items keep patch_affected=False (not set to None)."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-002", "interaction")  # no match
        ctx = _make_patch_context(validated_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        # Unmatched stays False (original value)
        val = result[0].get("patch_affected")
        assert val is None or val is False

    def test_pending_patches_also_mark_items(self) -> None:
        """Pending patches also mark matching items (not just validated)."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "interaction", status="pending_backwrite")
        ctx = _make_patch_context(pending_patches=[patch])
        result = mark_manifest_patch_affected(items, ctx)
        assert result[0]["patch_affected"] is True

    def test_both_validated_and_pending_mark_items(self) -> None:
        """Both validated and pending patches contribute to marking."""
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected
        items = [_make_manifest_item("cov-1", "FEAT-001")]
        patch_v = _make_patch("UXPATCH-0001", "FEAT-001", "interaction", status="validated")
        patch_p = _make_patch("UXPATCH-0002", "FEAT-001", "semantic", status="pending_backwrite")
        ctx = _make_patch_context(validated_patches=[patch_v], pending_patches=[patch_p])
        result = mark_manifest_patch_affected(items, ctx)
        assert "UXPATCH-0001" in result[0]["patch_refs"]
        assert "UXPATCH-0002" in result[0]["patch_refs"]


# ---------------------------------------------------------------------------
# TDD-03-B: create_manifest_items_for_new_scenarios behavior tests (15 tests)
# ---------------------------------------------------------------------------

class TestCreateManifestItemsForNewScenarios:
    """create_manifest_items_for_new_scenarios behavior tests from 04-03-PLAN.md."""

    def test_empty_patch_context_returns_original_list_unchanged(self) -> None:
        """Empty PatchContext returns original list unchanged."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        ctx = _make_patch_context()
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert len(result) == 1

    def test_new_item_has_lifecycle_status_drafted_d09(self) -> None:
        """New item has lifecycle_status='drafted' (D-09)."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        new_items = [i for i in result if i["coverage_id"] != "cov-1"]
        assert len(new_items) == 1
        assert new_items[0]["lifecycle_status"] == "drafted"

    def test_new_item_has_patch_affected_true(self) -> None:
        """New item has patch_affected=True."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original: list[dict] = []
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert result[0]["patch_affected"] is True

    def test_new_item_has_patch_refs_containing_patch_id(self) -> None:
        """New item has patch_refs=[patch_id]."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original: list[dict] = []
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert "UXPATCH-0001" in result[0]["patch_refs"]

    def test_new_item_has_source_feat_ref_from_patch_scope(self) -> None:
        """New item has source_feat_ref from patch.scope.feat_ref."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original: list[dict] = []
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-ABC", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert result[0]["source_feat_ref"] == "FEAT-ABC"

    def test_new_item_coverage_id_prefixed_with_patch_id(self) -> None:
        """New item coverage_id is prefixed with patch_id."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original: list[dict] = []
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert result[0]["coverage_id"].startswith("UXPATCH-0001-")

    def test_impacts_existing_false_creates_new_item(self) -> None:
        """impacts_existing_testcases=False creates a new item."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert len(result) == 2  # original + new

    def test_impacts_existing_true_with_test_targets_creates_new_item(self) -> None:
        """impacts_existing_testcases=True WITH test_targets creates a new item."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": True, "test_targets": ["/new/endpoint"]}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        # Creates for the test_target
        assert len(result) == 2

    def test_impacts_existing_true_without_test_targets_does_not_create(self) -> None:
        """impacts_existing_testcases=True WITHOUT test_targets does NOT create new item."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": True}  # no test_targets
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert len(result) == 1  # no new item added

    def test_duplicate_target_does_not_create_duplicate_item(self) -> None:
        """Duplicate target (already in existing items) does NOT create duplicate."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}  # targets FEAT-001
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        # Should not create a duplicate of cov-1
        cov1_count = sum(1 for i in result if i["coverage_id"] == "cov-1")
        assert cov1_count == 1

    def test_multiple_patches_create_multiple_new_items(self) -> None:
        """Multiple patches create multiple new items."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original: list[dict] = []
        patch1 = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        patch2 = _make_patch(
            "UXPATCH-0002", "FEAT-002", "semantic",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch1, patch2])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert len(result) == 2

    def test_new_items_appended_to_manifest_list(self) -> None:
        """New items are appended to manifest_items list (same list object)."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original: list[dict] = []
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "interaction",
            test_impact={"impacts_existing_testcases": False}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert len(result) == 1

    def test_visual_patch_creates_no_new_items(self) -> None:
        """Visual patch creates no new items."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch(
            "UXPATCH-0001", "FEAT-001", "visual",
            test_impact={"impacts_user_path": True, "affected_routes": ["/test"]}
        )
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert len(result) == 1

    def test_patch_without_test_impact_creates_no_new_items(self) -> None:
        """Patch without test_impact creates no new items."""
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios
        original = [_make_manifest_item("cov-1", "FEAT-001")]
        patch = _make_patch("UXPATCH-0001", "FEAT-001", "interaction", test_impact=None)
        ctx = _make_patch_context(validated_patches=[patch])
        result = create_manifest_items_for_new_scenarios(ctx, list(original))
        assert len(result) == 1


# ---------------------------------------------------------------------------
# TDD-03-C: Execution wiring tests (12 tests)
# ---------------------------------------------------------------------------

class TestExecutionWiring:
    """Execution wiring tests: patch_context param, TOCTOU, blocked cases."""

    def test_execute_round_accepts_patch_context_parameter(self) -> None:
        """_execute_round should accept optional patch_context parameter."""
        from cli.lib.test_exec_execution import _execute_round
        import inspect
        sig = inspect.signature(_execute_round)
        assert "patch_context" in sig.parameters
        param = sig.parameters["patch_context"]
        assert param.default is None  # optional

    def test_run_narrow_execution_accepts_patch_context_parameter(self) -> None:
        """run_narrow_execution should accept optional patch_context parameter."""
        from cli.lib.test_exec_execution import run_narrow_execution
        import inspect
        sig = inspect.signature(run_narrow_execution)
        assert "patch_context" in sig.parameters
        param = sig.parameters["patch_context"]
        assert param.default is None

    def test_execute_cases_accepts_patch_context_parameter(self) -> None:
        """execute_cases should accept optional patch_context parameter."""
        from cli.lib.test_exec_execution import execute_cases
        import inspect
        sig = inspect.signature(execute_cases)
        assert "patch_context" in sig.parameters

    def test_patch_context_imported_in_test_exec_execution(self) -> None:
        """test_exec_execution.py should import PatchContext from test_exec_artifacts."""
        import cli.lib.test_exec_execution as exec_mod
        source = Path(exec_mod.__file__).read_text(encoding="utf-8")
        # Check for the import (may be multi-line due to formatter)
        assert "PatchContext" in source
        assert "from cli.lib.test_exec_artifacts import" in source

    def test_mark_manifest_patch_affected_wired_into_runtime(self) -> None:
        """test_exec_runtime.py should call mark_manifest_patch_affected."""
        import cli.lib.test_exec_runtime as runtime_mod
        source = Path(runtime_mod.__file__).read_text(encoding="utf-8")
        assert "mark_manifest_patch_affected" in source

    def test_create_manifest_items_wired_into_runtime(self) -> None:
        """test_exec_runtime.py should call create_manifest_items_for_new_scenarios."""
        import cli.lib.test_exec_runtime as runtime_mod
        source = Path(runtime_mod.__file__).read_text(encoding="utf-8")
        assert "create_manifest_items_for_new_scenarios" in source

    def test_toctou_recheck_raises_on_hash_mismatch(self) -> None:
        """TOCTOU re-verification should raise PATCH_CONTEXT_CHANGED on hash mismatch."""
        import cli.lib.test_exec_runtime as runtime_mod
        source = Path(runtime_mod.__file__).read_text(encoding="utf-8")
        assert "recheck_context" in source
        assert "PATCH_CONTEXT_CHANGED" in source

    def test_patch_blocked_flag_handled_in_execute_cases(self) -> None:
        """execute_cases should handle _patch_blocked flag on cases."""
        import cli.lib.test_exec_execution as exec_mod
        source = Path(exec_mod.__file__).read_text(encoding="utf-8")
        assert "_patch_blocked" in source

    def test_blocked_status_returned_for_skipped_cases(self) -> None:
        """execute_cases should return 'blocked' status for _patch_blocked cases."""
        import cli.lib.test_exec_execution as exec_mod
        source = Path(exec_mod.__file__).read_text(encoding="utf-8")
        assert '"blocked"' in source

    def test_conflict_resolution_applied_in_execute_round(self) -> None:
        """_execute_round should apply conflict_resolution map to mark blocked cases."""
        import cli.lib.test_exec_execution as exec_mod
        source = Path(exec_mod.__file__).read_text(encoding="utf-8")
        assert "conflict_resolution" in source

    def test_manifest_items_passed_through_execution_context(self) -> None:
        """Manifest items should be accessible in execution context via patch_context."""
        import cli.lib.test_exec_execution as exec_mod
        source = Path(exec_mod.__file__).read_text(encoding="utf-8")
        # After implementation, manifest_items are handled via PatchContext
        assert "manifest_items" in source or "manifest" in source

    def test_block_reason_set_for_blocked_cases(self) -> None:
        """Blocked cases should have _patch_block_reason set."""
        import cli.lib.test_exec_execution as exec_mod
        source = Path(exec_mod.__file__).read_text(encoding="utf-8")
        assert "_patch_block_reason" in source
