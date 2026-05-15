"""Unit tests for design package parser (including Markdown extraction)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from cli.lib.v2.parser import (
    _extract_markdown_sections,
    _extract_structured_fields,
    parse_design_package,
)


class TestExtractMarkdownSections:
    def test_extracts_level2_sections(self) -> None:
        raw = "# Title\n\n## Section A\n\nBody A\n\n## Section B\n\nBody B\n"
        sections = _extract_markdown_sections(raw, level=2)
        assert len(sections) == 2
        assert sections[0]["title"] == "Section A"
        assert "Body A" in sections[0]["body"]
        assert sections[1]["title"] == "Section B"

    def test_empty_raw_returns_empty(self) -> None:
        assert _extract_markdown_sections("", level=2) == []


class TestExtractStructuredFields:
    def test_extracts_acceptance_criteria(self) -> None:
        raw = """
## P0 用户故事

### US-001: 示例故事

#### Acceptance Criteria
- **AC-001.1**: Given X When Y Then Z.
- **AC-001.2**: Given A When B Then C.
"""
        data = {"__raw__": raw, "__source_file__": "09_user_stories_and_acceptance_criteria.md"}
        result = _extract_structured_fields(data)
        assert "acceptance_criteria" in result
        acs = result["acceptance_criteria"]
        assert len(acs) == 2
        assert "AC-001.1:" in acs[0]
        assert "Given X" in acs[0]
        assert "AC-001.2:" in acs[1]

    def test_extracts_user_journey_map_from_story_file(self) -> None:
        raw = """
## P0 用户故事

### US-001: 能力基线

**As a** 用户
**I want** 功能
**So that** 价值

#### Acceptance Criteria
- **AC-001.1**: Given X When Y Then Z.

### US-002: 风险评估

**As a** 用户
**I want** 功能

#### Acceptance Criteria
- **AC-002.1**: Given A When B Then C.
"""
        data = {"__raw__": raw, "__source_file__": "09_user_stories_and_acceptance_criteria.md"}
        result = _extract_structured_fields(data)
        assert "user_journey_map" in result
        ujm = result["user_journey_map"]
        assert len(ujm) == 2
        assert "US-001" in ujm[0]["name"]
        assert len(ujm[0]["steps"]) == 1
        assert "AC-001.1:" in ujm[0]["steps"][0]

    def test_extracts_user_journey_map_from_journey_file(self) -> None:
        raw = """
## 目录

1. [总览](#1-总览)

## 1. 旅程总览

Overview text.

## 2. Happy Path

> **场景**：用户完成一次闭环。

### Step 1: 打开 App

Detail.

### Step 2: 提交反馈

Detail.

## 3. 分支流程

> 基于决策动作。

### 3.1 KEEP

Detail.

## 8. 附录：枚举表

Appendix.
"""
        data = {"__raw__": raw, "__source_file__": "10_user_journey_map.md"}
        result = _extract_structured_fields(data)
        assert "user_journey_map" in result
        ujm = result["user_journey_map"]
        # Should skip 目录, 旅程总览, 附录
        assert len(ujm) == 2
        assert "Happy Path" in ujm[0]["name"]
        assert ujm[0]["value"] == "**场景**：用户完成一次闭环。"
        assert len(ujm[0]["steps"]) == 2
        assert "Step 1: 打开 App" in ujm[0]["steps"]
        assert "分支流程" in ujm[1]["name"]

    def test_extracts_product_vision(self) -> None:
        raw = "# Product Vision Doc\n\n## Section 1: Product Vision\n\n**One-line vision.**\n\n## Scope\n\nIn scope.\n"
        data = {"__raw__": raw, "__source_file__": "08_product_vision_and_success_metrics.md"}
        result = _extract_structured_fields(data)
        assert result.get("product_vision") == "One-line vision."

    def test_extracts_scope_declaration(self) -> None:
        raw = """
## Scope

### In Scope
- Feature A
- Feature B

### Out of Scope
- Feature C
"""
        data = {"__raw__": raw, "__source_file__": "00_blueprint.md"}
        result = _extract_structured_fields(data)
        scope = result.get("scope_declaration")
        assert scope is not None
        assert scope["in_scope"] == ["Feature A", "Feature B"]
        assert scope["out_of_scope"] == ["Feature C"]

    def test_no_raw_returns_empty(self) -> None:
        assert _extract_structured_fields({}) == {}


class TestParseDesignPackage:
    def test_flat_directory_maps_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "08_vision.md").write_text("# Vision\n\nVision text.\n", encoding="utf-8")
            (root / "10_user_journey_map.md").write_text(
                "# Journey\n\n## Happy Path\n\n> Scenario.\n\n### Step 1\n\nDetail.\n",
                encoding="utf-8",
            )
            (root / "09_user_stories.md").write_text(
                "# Stories\n\n## P0\n\n### US-001: Story\n\nAC.\n\n#### Acceptance Criteria\n- **AC-001.1**: Given X When Y Then Z.\n",
                encoding="utf-8",
            )

            result = parse_design_package(root)

        product = result.get("product_design", {})
        assert "__raw__" in product
        # Raw should contain both files (appended, not overwritten)
        assert "Journey" in product["__raw__"]
        assert "Stories" in product["__raw__"]
        assert "__source_files__" in product
        assert len(product["__source_files__"]) == 2

        # Structured fields should be merged
        assert "user_journey_map" in product
        assert "acceptance_criteria" in product
        assert len(product["acceptance_criteria"]) == 1
        assert "AC-001.1:" in product["acceptance_criteria"][0]

        business = result.get("business_design", {})
        assert "product_vision" in business
        assert "__raw__" in business

    def test_structured_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "product_design").mkdir()
            (root / "product_design" / "journey.md").write_text(
                "# J\n\n## Path A\n\nBody.\n", encoding="utf-8"
            )
            (root / "product_design" / "stories.md").write_text(
                "# S\n\n## P0\n\n### US-001: X\n\n#### AC\n- **AC-1.1**: G W T.\n",
                encoding="utf-8",
            )

            result = parse_design_package(root)

        product = result["product_design"]
        assert "user_journey_map" in product
        assert "acceptance_criteria" in product
        assert len(product["acceptance_criteria"]) == 1

    def test_missing_directory_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_design_package("/nonexistent/path")
