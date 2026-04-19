"""Tests for patch_capture_runtime.py tri-classification."""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

from cli.lib.patch_schema import ChangeClass, GradeLevel

# Load the runtime module using importlib (hyphenated directory names)
_RUNTIME_PATH = Path(__file__).parent / "patch_capture_runtime.py"
_spec = importlib.util.spec_from_file_location(
    "patch_capture_runtime", str(_RUNTIME_PATH)
)
_runtime = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_runtime)

classify_change = _runtime.classify_change
CLASSIFICATION_RULES = _runtime.CLASSIFICATION_RULES
_has_negation = _runtime._has_negation
_scan_dimensions = _runtime._scan_dimensions
capture_prompt = _runtime.capture_prompt


class TestHasNegation:
    """Test negation detection."""

    def test_chinese_negation(self):
        assert _has_negation("不改语义，只调颜色") is True

    def test_english_negation(self):
        assert _has_negation("no change to semantics") is True

    def test_no_negation(self):
        assert _has_negation("修改按钮颜色") is False

    def test_keep_pattern(self):
        assert _has_negation("保持状态机不变") is True


class TestScanDimensions:
    """Test dimension scanning."""

    def test_semantic_match(self):
        dims = _scan_dimensions("新增用户状态机")
        assert "semantic" in dims

    def test_interaction_match(self):
        dims = _scan_dimensions("调整页面跳转顺序")
        assert "interaction" in dims

    def test_visual_match(self):
        dims = _scan_dimensions("修改按钮颜色")
        assert "visual" in dims

    def test_no_match(self):
        dims = _scan_dimensions("随便写点东西")
        assert dims == []

    def test_multiple_match(self):
        dims = _scan_dimensions("修改按钮颜色和跳转顺序")
        assert "visual" in dims
        assert "interaction" in dims


class TestClassifyChange:
    """Test full classification with all edge cases."""

    def test_visual_high_confidence(self):
        result = classify_change("修改按钮颜色")
        assert result["change_class"] in ("visual", "layout", "copy_text", "data_display")
        assert result["grade_level"] == "minor"
        assert result["confidence"] == "high"
        assert result["needs_human_review"] is False
        assert "visual" in result["dimensions_detected"]

    def test_interaction_high_confidence(self):
        result = classify_change("调整页面跳转顺序")
        assert result["change_class"] == "interaction"
        assert result["grade_level"] == "minor"
        assert result["confidence"] == "high"
        assert "interaction" in result["dimensions_detected"]

    def test_semantic_high_confidence(self):
        result = classify_change("新增用户状态机")
        assert result["change_class"] == "semantic"
        assert result["grade_level"] == "major"
        assert result["confidence"] == "high"
        assert "semantic" in result["dimensions_detected"]

    def test_copy_text_visual(self):
        result = classify_change("优化文案描述")
        assert result["grade_level"] == "minor"
        assert "visual" in result["dimensions_detected"]

    def test_negation_handling(self):
        """Negation: '不改语义，只调颜色' should NOT be semantic."""
        result = classify_change("不改语义，只调颜色")
        assert result["change_class"] != "semantic"
        assert result["grade_level"] == "minor"
        assert "semantic" not in result["dimensions_detected"]

    def test_no_indicators_fallback(self):
        """No keyword indicators -> fallback to other, needs_human_review."""
        result = classify_change("随便写点东西")
        assert result["needs_human_review"] is True
        assert result["confidence"] == "low"

    def test_mixed_input_semantic_dominates(self):
        """Mixed visual + semantic -> semantic dominates -> MAJOR."""
        result = classify_change("修改按钮颜色并新增用户状态机")
        assert result["change_class"] == "semantic"
        assert result["grade_level"] == "major"
        assert "visual" in result["dimensions_detected"]
        assert "semantic" in result["dimensions_detected"]
        assert result["confidence"] == "medium"

    def test_mixed_visual_interaction_no_semantic(self):
        """Mixed visual + interaction, no semantic -> interaction preferred."""
        result = classify_change("修改按钮颜色和调整页面跳转")
        assert result["grade_level"] == "minor"
        assert result["change_class"] == "interaction"
        assert result["confidence"] == "medium"

    def test_fallback_with_paths(self):
        """No indicators but paths provided -> fallback to path-based classification."""
        result = classify_change("random text", paths=["components/Button.html"])
        assert result["change_class"] == "ui_flow"
        assert result["grade_level"] == "minor"

    def test_dimensions_detected_is_list(self):
        result = classify_change("修改按钮颜色")
        assert isinstance(result["dimensions_detected"], list)
        assert len(result["dimensions_detected"]) > 0

    def test_all_required_fields_present(self):
        result = classify_change("修改按钮颜色")
        assert "change_class" in result
        assert "grade_level" in result
        assert "dimensions_detected" in result
        assert "confidence" in result
        assert "needs_human_review" in result


class TestClassifyChangeEnumValues:
    """Test that classification outputs valid enum values."""

    def test_visual_is_valid_enum(self):
        result = classify_change("修改按钮颜色")
        assert result["change_class"] in [e.value for e in ChangeClass]

    def test_semantic_is_valid_enum(self):
        result = classify_change("新增用户状态机")
        assert result["change_class"] in [e.value for e in ChangeClass]

    def test_grade_level_is_valid_enum(self):
        result = classify_change("修改按钮颜色")
        assert result["grade_level"] in [e.value for e in GradeLevel]

        result2 = classify_change("新增用户状态机")
        assert result2["grade_level"] in [e.value for e in GradeLevel]


class TestCapturePrompt:
    """Test the capture_prompt function."""

    def test_capture_creates_valid_patch(self, tmp_path):
        patch = capture_prompt("修改按钮颜色", "FEAT-001", output_dir=tmp_path)
        assert patch["change_class"] in ("visual", "layout", "copy_text", "data_display")
        assert patch["grade_level"] == "minor"
        assert patch["scope"]["feat_ref"] == "FEAT-001"
        assert patch["status"] == "draft"
        assert "dimensions_detected" in patch
        assert "confidence" in patch
        assert "needs_human_review" in patch

    def test_capture_semantic_patch(self, tmp_path):
        patch = capture_prompt("新增用户状态机", "FEAT-002", output_dir=tmp_path)
        assert patch["change_class"] == "semantic"
        assert patch["grade_level"] == "major"
        assert isinstance(patch["test_impact"], dict)
        assert "affected_routes" in patch["test_impact"]

    def test_capture_writes_yaml_file(self, tmp_path):
        capture_prompt("修改按钮颜色", "FEAT-003", output_dir=tmp_path)
        yaml_files = list(tmp_path.glob("UXPATCH-*.yaml"))
        assert len(yaml_files) == 1

    def test_capture_sequential_numbers(self, tmp_path):
        capture_prompt("修改按钮颜色", "FEAT-004", output_dir=tmp_path)
        capture_prompt("调整页面跳转", "FEAT-004", output_dir=tmp_path)
        yaml_files = sorted(tmp_path.glob("UXPATCH-*.yaml"))
        assert len(yaml_files) == 2
        assert "UXPATCH-0001" in yaml_files[0].name
        assert "UXPATCH-0002" in yaml_files[1].name
