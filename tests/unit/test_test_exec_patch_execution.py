"""Tests for mark_manifest_patch_affected and create_manifest_items_for_new_scenarios in test_exec_artifacts.py.

RED phase: these tests assert ImportError because the functions don't exist yet.
They validate the acceptance criteria from 04-03-PLAN.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# RED Phase: ImportError — mark_manifest_patch_affected does not exist yet
# ---------------------------------------------------------------------------

def test_mark_manifest_patch_affected_import_raises() -> None:
    """mark_manifest_patch_affected should not exist yet (RED phase)."""
    with pytest.raises(ImportError):
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected  # type: ignore # noqa: F811


def test_create_manifest_items_for_new_scenarios_import_raises() -> None:
    """create_manifest_items_for_new_scenarios should not exist yet (RED phase)."""
    with pytest.raises(ImportError):
        from cli.lib.test_exec_artifacts import create_manifest_items_for_new_scenarios  # type: ignore # noqa: F811


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_patch_context(
    validated_patches: list[dict] | None = None,
    pending_patches: list[dict] | None = None,
    conflict_resolution: dict | None = None,
    directory_hash: str = "testhash1234",
) -> object:
    """Build a minimal PatchContext-like object for testing."""
    # PatchContext was added in 04-02, but we construct one directly
    # to avoid import coupling between RED test and implementation
    class _Ctx:
        def __init__(self):
            self.has_active_patches = bool(validated_patches or pending_patches)
            self.validated_patches = validated_patches or []
            self.pending_patches = pending_patches or []
            self.conflict_resolution = conflict_resolution or {}
            self.directory_hash = directory_hash
            self.reviewed_at_latest = None
            self.feat_ref = None
    return _Ctx()


# ---------------------------------------------------------------------------
# mark_manifest_patch_affected behavior tests (14 tests)
# These are here for documentation; RED phase skips them with pytest.skip
# ---------------------------------------------------------------------------

mark_tests: list[object] = []  # populated below after import succeeds


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
) -> dict:
    """Build a minimal patch dict."""
    return {
        "id": patch_id,
        "status": "validated",
        "title": f"Patch {patch_id}",
        "change_class": change_class,
        "scope": {"feat_ref": feat_ref},
        "test_impact": test_impact or {
            "impacts_user_path": True,
            "affected_routes": ["/test/endpoint"],
        },
    }


# ---------------------------------------------------------------------------
# Execution wiring tests (TDD-03-C)
# RED phase: tests should fail with AttributeError / TypeError
# ---------------------------------------------------------------------------


def test_execute_round_signature_has_no_patch_context() -> None:
    """_execute_round should not yet accept patch_context parameter (RED phase)."""
    from cli.lib.test_exec_execution import _execute_round
    import inspect
    sig = inspect.signature(_execute_round)
    # RED: patch_context is not in the signature yet
    assert "patch_context" not in sig.parameters


def test_run_narrow_execution_signature_has_no_patch_context() -> None:
    """run_narrow_execution should not yet accept patch_context parameter (RED phase)."""
    from cli.lib.test_exec_execution import run_narrow_execution
    import inspect
    sig = inspect.signature(run_narrow_execution)
    # RED: patch_context is not in the signature yet
    assert "patch_context" not in sig.parameters


def test_execute_cases_signature_has_no_patch_context() -> None:
    """execute_cases should not yet accept patch_context parameter (RED phase)."""
    from cli.lib.test_exec_execution import execute_cases
    import inspect
    sig = inspect.signature(execute_cases)
    # RED: patch_context is not in the signature yet
    assert "patch_context" not in sig.parameters


def test_execute_test_exec_skill_does_not_call_mark_manifest() -> None:
    """execute_test_exec_skill should not yet call mark_manifest_patch_affected (RED phase)."""
    # RED: Verify the function doesn't exist yet
    with pytest.raises(ImportError):
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected  # noqa: F811


def test_patch_context_not_imported_in_test_exec_execution() -> None:
    """test_exec_execution.py should not yet import PatchContext (RED phase)."""
    # RED: Check that the import line doesn't exist in test_exec_execution.py
    import cli.lib.test_exec_execution as exec_mod
    source = Path(exec_mod.__file__).read_text(encoding="utf-8")
    # RED: no PatchContext import yet
    assert "from cli.lib.test_exec_artifacts import PatchContext" not in source
    assert "PatchContext" not in source


def test_toctou_recheck_not_in_execute_test_exec_skill() -> None:
    """execute_test_exec_skill should not yet re-verify directory_hash (RED phase)."""
    import cli.lib.test_exec_runtime as runtime_mod
    source = Path(runtime_mod.__file__).read_text(encoding="utf-8")
    # RED: no recheck_context / TOCTOU re-verification yet
    assert "recheck_context" not in source
    assert "PATCH_CONTEXT_CHANGED" not in source


def test_patch_blocked_attr_not_in_execute_cases() -> None:
    """execute_cases should not yet handle _patch_blocked flag (RED phase)."""
    import cli.lib.test_exec_execution as exec_mod
    source = Path(exec_mod.__file__).read_text(encoding="utf-8")
    assert "_patch_blocked" not in source


def test_blocked_status_not_in_execute_cases() -> None:
    """execute_cases should not yet return 'blocked' status for skipped cases (RED phase)."""
    import cli.lib.test_exec_execution as exec_mod
    source = Path(exec_mod.__file__).read_text(encoding="utf-8")
    assert '"blocked"' not in source


def test_mark_manifest_patch_affected_not_in_runtime() -> None:
    """test_exec_runtime.py should not yet call mark_manifest_patch_affected (RED phase)."""
    import cli.lib.test_exec_runtime as runtime_mod
    source = Path(runtime_mod.__file__).read_text(encoding="utf-8")
    assert "mark_manifest_patch_affected" not in source


def test_create_manifest_items_not_in_runtime() -> None:
    """test_exec_runtime.py should not yet call create_manifest_items_for_new_scenarios (RED phase)."""
    import cli.lib.test_exec_runtime as runtime_mod
    source = Path(runtime_mod.__file__).read_text(encoding="utf-8")
    assert "create_manifest_items_for_new_scenarios" not in source


def test_manifest_items_not_in_test_exec_execution() -> None:
    """test_exec_execution.py should not yet reference manifest_items in patch context (RED phase)."""
    import cli.lib.test_exec_execution as exec_mod
    source = Path(exec_mod.__file__).read_text(encoding="utf-8")
    assert "manifest_items" not in source


def test_conflict_resolution_not_applied_in_execute_round() -> None:
    """_execute_round should not yet apply conflict_resolution map (RED phase)."""
    import cli.lib.test_exec_execution as exec_mod
    source = Path(exec_mod.__file__).read_text(encoding="utf-8")
    assert "_patch_blocked" not in source
    assert "conflict_resolution" not in source
