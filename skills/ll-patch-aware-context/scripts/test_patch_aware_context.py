"""Tests for patch_aware_context.py — grade_level awareness."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the skill scripts directory is importable
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# Ensure the project root is on sys.path for cli.lib imports
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from patch_aware_context import summarize_patch


# ---------------------------------------------------------------------------
# Test 1: summarize_patch output includes grade_level key
# ---------------------------------------------------------------------------

def test_summarize_includes_grade_level():
    """summarize_patch() output dict must include 'grade_level' key."""
    p = {"file_path": "a.py", "change_class": "interaction", "patch_status": "pending"}
    s = summarize_patch(p)
    assert "grade_level" in s
    assert "grade_derived_from" in s


# ---------------------------------------------------------------------------
# Test 2: semantic change_class -> grade_level = "major"
# ---------------------------------------------------------------------------

def test_semantic_is_major():
    """For change_class=semantic, grade_level should be 'major'."""
    p = {"file_path": "a.py", "change_class": "semantic", "patch_status": "pending"}
    s = summarize_patch(p)
    assert s["grade_level"] == "major"
    assert s["grade_derived_from"] == "patch_schema.derive_grade"


# ---------------------------------------------------------------------------
# Test 3: interaction change_class -> grade_level = "minor"
# ---------------------------------------------------------------------------

def test_interaction_is_minor():
    """For change_class=interaction, grade_level should be 'minor'."""
    p = {"file_path": "b.py", "change_class": "interaction", "patch_status": "pending"}
    s = summarize_patch(p)
    assert s["grade_level"] == "minor"


# ---------------------------------------------------------------------------
# Test 4: visual change_class -> grade_level = "minor"
# ---------------------------------------------------------------------------

def test_visual_is_minor():
    """For change_class=visual, grade_level should be 'minor'."""
    p = {"file_path": "c.py", "change_class": "visual", "patch_status": "pending"}
    s = summarize_patch(p)
    assert s["grade_level"] == "minor"


# ---------------------------------------------------------------------------
# Test 5: missing change_class defaults via derive_grade (MAJOR with warning)
# ---------------------------------------------------------------------------

def test_missing_change_class_defaults_to_major():
    """When change_class is missing, summarize_patch defaults to 'other' which
    maps to MINOR. For truly unknown change_class values, derive_grade returns MAJOR."""
    # Missing key -> defaults to "other" -> MINOR
    p = {"file_path": "c.py", "patch_status": "pending"}
    s = summarize_patch(p)
    assert "grade_level" in s
    # "other" maps to MINOR per the design (with human escalation path)
    assert s["grade_level"] == "minor"

    # Truly unknown change_class value -> derive_grade fail-safe returns MAJOR
    from cli.lib.patch_schema import derive_grade
    unknown_grade = derive_grade("nonexistent_class")
    assert unknown_grade.value == "major"


# ---------------------------------------------------------------------------
# Test 6: CROSS-CALLER CONSISTENCY
# ---------------------------------------------------------------------------

def test_derive_grade_consistency_across_callers():
    """Assert that _load_patch_yaml, summarize_patch_for_context, and
    patch_aware_context.py's summarize_patch all produce the SAME grade
    for the same change_class."""
    from cli.lib.patch_schema import derive_grade
    from cli.lib.patch_context_injector import (
        summarize_patch_for_context,
        _load_patch_yaml,
    )

    test_cases = ["semantic", "interaction", "visual", "ui_flow", "copy_text", "other"]

    for change_class in test_cases:
        expected_grade = derive_grade(change_class).value

        # Check _load_patch_yaml
        tf = tempfile.mktemp(suffix=".yaml")
        try:
            with open(tf, "w", encoding="utf-8") as f:
                f.write(f"id: TEST\nchange_class: {change_class}\nstatus: draft\n")
            loaded = _load_patch_yaml(tf)
            assert loaded is not None
            assert loaded.get("grade_level") == expected_grade, (
                f"_load_patch_yaml: expected {expected_grade} for {change_class}, got {loaded.get('grade_level')}"
            )
        finally:
            try:
                os.unlink(tf)
            except OSError:
                pass

        # Check summarize_patch_for_context
        ctx_sum = summarize_patch_for_context({
            "id": "x",
            "change_class": change_class,
            "scope": "",
            "changed_files": [],
            "status": "approved",
        })
        assert expected_grade in ctx_sum, (
            f"summarize_patch_for_context: expected {expected_grade} in output for {change_class}"
        )

        # Check patch_aware_context.py summarize_patch
        aware_sum = summarize_patch({
            "file_path": "a.py",
            "change_class": change_class,
            "patch_status": "pending",
        })
        assert aware_sum.get("grade_level") == expected_grade, (
            f"awareness summarize_patch: expected {expected_grade} for {change_class}, got {aware_sum.get('grade_level')}"
        )


# ---------------------------------------------------------------------------
# Test 7: write_awareness_recording includes grade_level in patches_found
# ---------------------------------------------------------------------------

def test_write_awareness_recording_includes_grade_level():
    """write_awareness_recording() YAML must contain grade_level in patches_found."""
    from cli.lib.patch_awareness import PatchContext
    from patch_aware_context import write_awareness_recording

    out_dir = tempfile.mkdtemp()
    try:
        ctx = PatchContext(
            patches_found=[
                {"file_path": "a.py", "change_class": "semantic", "patch_status": "pending"},
            ],
            scan_path="/test",
            scan_ref="FEAT-001",
            total_count=1,
        )
        output_path = write_awareness_recording(ctx, Path(out_dir), ai_reasoning="test")
        assert output_path.exists()

        import yaml
        with open(output_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        patches = data["patch_awareness"]["patch_scan_status"]["patches_found"]
        assert len(patches) == 1
        assert "grade_level" in patches[0]
        assert patches[0]["grade_level"] == "major"
        assert patches[0]["grade_derived_from"] == "patch_schema.derive_grade"
    finally:
        try:
            import shutil
            shutil.rmtree(out_dir)
        except OSError:
            pass
