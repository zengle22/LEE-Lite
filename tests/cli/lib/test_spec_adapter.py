"""Unit tests for cli/lib/spec_adapter.py."""

import pytest
from pathlib import Path
from cli.lib.spec_adapter import spec_to_testset, SpecAdapterInput


class TestApiSpecParsing:
    def test_api_spec_to_spec_adapter_compat(self, tmp_path):
        # Create a minimal API spec file matching the expected format
        spec_content = """# API Test Spec

## Case Metadata
| case_id | SPEC-001 |
| capability | CAND-SUBMIT |
| scenario_type | happy-path |
| coverage_id | CAND-SUBMIT-001 |
| priority | P0 |

## Request
```json
{"name": "test", "email": "test@example.com"}
```

## Preconditions
- Candidate package exists

## Response Assertions
- status_code == 201
- response.id exists
"""
        spec_dir = tmp_path / "api-test-spec"
        spec_dir.mkdir()
        spec_file = spec_dir / "SPEC-001.md"
        spec_file.write_text(spec_content)

        input = SpecAdapterInput(
            spec_files=[spec_file],
            feat_ref="FEAT-001",
            modality="api",
        )
        result = spec_to_testset(tmp_path, input)

        assert result["ssot_type"] == "SPEC_ADAPTER_COMPAT"
        assert result["feat_ref"] == "FEAT-001"
        assert result["source_chain"] == "api"
        assert len(result["test_units"]) == 1
        unit = result["test_units"][0]
        assert unit["unit_ref"] == "SPEC-001"
        assert "_source_coverage_id" in unit
        assert unit["_source_coverage_id"] == "CAND-SUBMIT-001"
        assert "_api_extension" in unit
        assert unit["_api_extension"]["scenario_type"] == "happy-path"


class TestE2ESpecParsing:
    def test_e2e_spec_to_spec_adapter_compat(self, tmp_path):
        # Create a minimal E2E spec file matching the expected format
        spec_content = """# E2E Journey Spec

## Case Metadata
| spec_id | JOURNEY-001 |
| title | Submit Candidate Package |
| priority | P0 |
| entry_point | /packages/new |
| coverage_id | JOURNEY-MAIN-001 |

## User Steps
1. Action: fill_form -> .package-form (css_selector)
2. Action: submit -> button[type=submit] (css_selector)

## Expected UI States
- Form submitted successfully
- Redirect to package list
"""
        spec_dir = tmp_path / "e2e-journey-spec"
        spec_dir.mkdir()
        spec_file = spec_dir / "JOURNEY-001.md"
        spec_file.write_text(spec_content)

        input = SpecAdapterInput(
            spec_files=[spec_file],
            proto_ref="PROTO-001",
            modality="web_e2e",
        )
        result = spec_to_testset(tmp_path, input)

        assert result["ssot_type"] == "SPEC_ADAPTER_COMPAT"
        assert result["prototype_ref"] == "PROTO-001"
        assert result["source_chain"] == "spec_e2e"
        assert len(result["test_units"]) == 1
        unit = result["test_units"][0]
        assert unit["unit_ref"] == "JOURNEY-001"
        assert "_source_coverage_id" in unit
        assert unit["_source_coverage_id"] == "JOURNEY-MAIN-001"
        assert "_e2e_extension" in unit


class TestTargetFormatResolution:
    def test_css_selector_format(self, tmp_path):
        """Verify css_selector target_format uses target directly."""
        from cli.lib.spec_adapter import _resolve_selector

        step = {"target": ".package-form", "target_format": "css_selector"}
        result = _resolve_selector("fill_form", step)
        assert result == ".package-form"

    def test_semantic_format(self, tmp_path):
        """Verify semantic format produces [data-action=action_name]."""
        from cli.lib.spec_adapter import _resolve_selector

        step = {"target": "submit_btn", "target_format": "semantic"}
        result = _resolve_selector("submit_form", step)
        assert result == "[data-action=submit_form]"

    def test_text_format(self, tmp_path):
        """Verify text format produces text=target."""
        from cli.lib.spec_adapter import _resolve_selector

        step = {"target": "Submit", "target_format": "text"}
        result = _resolve_selector("click", step)
        assert result == "text=Submit"

    def test_xpath_format(self, tmp_path):
        """Verify xpath format uses target directly."""
        from cli.lib.spec_adapter import _resolve_selector

        step = {"target": "//button[@type='submit']", "target_format": "xpath"}
        result = _resolve_selector("click", step)
        assert result == "//button[@type='submit']"