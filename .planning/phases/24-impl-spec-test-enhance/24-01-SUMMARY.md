# Plan 24-01: Hybrid Markdown Section Parser with Chinese Heading Support

## Summary

Added hybrid markdown section parsing to the impl-spec-test skill guard that correctly handles Chinese headings, addressing FIX-P1-09. The parser uses regex-based extraction as the primary method (per D-01) and supports levels 2-4 headings.

## Changes Made

### 1. Updated `impl_spec_test_skill_guard.py`

- Added `_HEADING_RE` constant to match markdown headings (levels 2-4) with Chinese character support
- Added `_MAX_EXCERPT_LINES = 3` constant for excerpt extraction
- Implemented `_parse_markdown_sections()` function that:
  - Extracts headings with their level, text, and line number
  - Collects up to 3 lines of excerpt text after each heading
  - Handles Chinese headings like "### 5.5 完成状态定义" correctly
  - Skips empty lines and stops at the next heading
- Implemented `validate_markdown_sections()` function that validates and parses markdown files
- Added missing type annotations import (`from typing import Any`)

### 2. Updated `test_impl_spec_test_surface_map.py`

- Added import for `_parse_markdown_sections`
- Added 8 new test functions:
  - `test_parse_chinese_heading_with_number()` - tests numbered Chinese headings
  - `test_parse_pure_chinese_heading()` - tests headings with only Chinese characters
  - `test_parse_mixed_chinese_english_heading()` - tests mixed language headings
  - `test_excerpt_stops_at_next_heading()` - verifies excerpt extraction stops at next heading
  - `test_excerpt_fallback_to_heading_text()` - verifies fallback when no excerpt available
  - `test_multiple_headings_preserved_in_order()` - verifies correct order of sections
  - `test_level_one_heading_ignored()` - verifies level 1 headings are not parsed
  - `test_invalid_heading_no_space_ignored()` - verifies invalid headings are ignored

## Verification Results

All tests are passing:

```
tests/test_impl_spec_test_surface_map.py::test_validate_input_accepts_surface_map_and_related_refs PASSED [ 10%]
tests/test_impl_spec_test_surface_map.py::test_validate_input_rejects_surface_map_without_coherence_hint PASSED [ 20%]
tests/test_impl_spec_test_surface_map.py::test_parse_chinese_heading_with_number PASSED [ 30%]
tests/test_impl_spec_test_surface_map.py::test_parse_pure_chinese_heading PASSED [ 40%]
tests/test_impl_spec_test_surface_map.py::test_parse_mixed_chinese_english_heading PASSED [ 50%]
tests/test_impl_spec_test_surface_map.py::test_excerpt_stops_at_next_heading PASSED [ 60%]
tests/test_impl_spec_test_surface_map.py::test_excerpt_fallback_to_heading_text PASSED [ 70%]
tests/test_impl_spec_test_surface_map.py::test_multiple_headings_preserved_in_order PASSED [ 80%]
tests/test_impl_spec_test_surface_map.py::test_level_one_heading_ignored PASSED [ 90%]
tests/test_impl_spec_test_surface_map.py::test_invalid_heading_no_space_ignored PASSED [100%]
```

## Key Features

1. **Chinese Heading Support**: Handles headings with Chinese characters, including numbered headings like "### 5.5 完成状态定义"
2. **Excerpt Extraction**: Collects up to 3 lines of content after each heading, skipping empty lines
3. **Fallback Mechanism**: Uses heading text as excerpt if no content follows
4. **Multiple Heading Levels**: Supports levels 2-4 headings (##, ###, ####)
5. **Markdown Validation**: Checks if a file contains recognizable markdown sections
6. **Robust Parsing**: Handles various edge cases like missing content, invalid headings, and empty lines

## Usage

The new functionality is available through:
- `_parse_markdown_sections()` - low-level parsing
- `validate_markdown_sections()` - file validation and parsing

Both functions are importable from `impl_spec_test_skill_guard`.
