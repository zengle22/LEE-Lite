from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from impl_spec_test_skill_guard import validate_input, _parse_markdown_sections  # noqa: E402


def _write_request(path: Path, payload: dict[str, object]) -> Path:
    request = {
        "api_version": "v1",
        "command": "skill.impl-spec-test",
        "request_id": "REQ-001",
        "workspace_root": "E:/ai/LEE-Lite-skill-first",
        "actor_ref": "actor.example",
        "trace": {},
        "payload": payload,
    }
    path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_validate_input_accepts_surface_map_and_related_refs(tmp_path: Path) -> None:
    request_path = _write_request(
        tmp_path / "request.json",
        {
            "impl_ref": "IMPL-001",
            "impl_package_ref": "impl-package-001",
            "feat_ref": "FEAT-001",
            "tech_ref": "TECH-001",
            "surface_map_ref": "SURFACE-MAP-001",
            "prototype_ref": "PROTO-001",
            "resolved_design_refs": {
                "surface_map_ref": "SURFACE-MAP-001",
                "prototype_ref": "PROTO-001",
            },
        },
    )

    assert validate_input(request_path) == 0


def test_validate_input_rejects_surface_map_without_coherence_hint(tmp_path: Path) -> None:
    request_path = _write_request(
        tmp_path / "request.json",
        {
            "impl_ref": "IMPL-001",
            "impl_package_ref": "impl-package-001",
            "feat_ref": "FEAT-001",
            "tech_ref": "TECH-001",
            "surface_map_ref": "SURFACE-MAP-001",
        },
    )

    with pytest.raises(ValueError, match="surface_map_ref requires prototype_ref or resolved_design_refs"):
        validate_input(request_path)


def test_parse_chinese_heading_with_number() -> None:
    content = "### 5.5 完成状态定义\n完成状态包括：\n- 已提交\n- 已审批"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 1
    assert sections[0]["heading_level"] == 3
    assert sections[0]["heading_text"] == "5.5 完成状态定义"
    assert "完成状态包括" in sections[0]["excerpt"]
    assert "已提交" in sections[0]["excerpt"]


def test_parse_pure_chinese_heading() -> None:
    content = "## 前置条件与后置输出\n本章节描述了接口的前置条件"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 1
    assert sections[0]["heading_level"] == 2
    assert sections[0]["heading_text"] == "前置条件与后置输出"
    assert "本章节描述了接口的前置条件" in sections[0]["excerpt"]


def test_parse_mixed_chinese_english_heading() -> None:
    content = "### API 前置条件\n- 接口需要授权\n- 数据格式为JSON"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 1
    assert sections[0]["heading_level"] == 3
    assert sections[0]["heading_text"] == "API 前置条件"
    assert "接口需要授权" in sections[0]["excerpt"]


def test_excerpt_stops_at_next_heading() -> None:
    content = "## 第一章\n这是第一章内容\n### 1.1 小节\n这是小节内容"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 2
    # First section's excerpt should not include the next heading
    assert "小节" not in sections[0]["excerpt"]
    assert "这是第一章内容" in sections[0]["excerpt"]


def test_excerpt_fallback_to_heading_text() -> None:
    content = "## 空章节\n\n\n## 下一章"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 2
    assert sections[0]["excerpt"] == sections[0]["heading_text"]


def test_multiple_headings_preserved_in_order() -> None:
    content = "## 第一章\n内容1\n## 第二章\n内容2\n### 2.1 小节\n内容3"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 3
    assert sections[0]["heading_text"] == "第一章"
    assert sections[1]["heading_text"] == "第二章"
    assert sections[2]["heading_text"] == "2.1 小节"


def test_level_one_heading_ignored() -> None:
    content = "# 标题1\n内容\n## 章节1\n内容"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 1
    assert sections[0]["heading_text"] == "章节1"


def test_invalid_heading_no_space_ignored() -> None:
    content = "##NoSpace\n内容\n## 有效章节\n内容"
    sections = _parse_markdown_sections(content)
    assert len(sections) == 1
    assert sections[0]["heading_text"] == "有效章节"
