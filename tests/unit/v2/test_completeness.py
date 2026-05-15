"""Unit tests for completeness check (tasks 2.1–2.5)."""

from __future__ import annotations

import pytest

from cli.lib.v2.completeness import check_completeness
from cli.lib.v2.models import CompletenessVerdict


def _make_full_package() -> dict:
    return {
        "business_design": {
            "product_vision": "Build a compiler",
            "scope_declaration": {"in_scope": ["freeze"], "out_of_scope": ["analysis"]},
            "source_path": "biz/",
        },
        "product_design": {
            "prd": "PRD content",
            "user_journey_map": [{"name": "j1", "steps": ["s1", "s2"]}],
            "acceptance_criteria": ["AC1: given x when y then z"],
            "source_path": "prd/",
        },
        "architecture_design": {
            "tech_stack": {"language": "Python"},
            "api_contract": [{"path": "/api"}],
            "source_path": "arch/",
        },
        "engineering_design": {
            "implementation_scope": {"directories": ["src/"]},
            "key_decisions": ["use dataclasses"],
            "source_path": "eng/",
        },
        "test_design": {
            "test_strategy": "unit + integration",
            "source_path": "test/",
        },
    }


class TestCheckCompleteness:
    def test_full_package_pass(self) -> None:
        dp = _make_full_package()
        result = check_completeness(dp)
        assert isinstance(result, CompletenessVerdict)
        assert result.verdict == "pass"
        assert result.missing_items == []

    def test_missing_required_dimension_blocked(self) -> None:
        dp = _make_full_package()
        del dp["business_design"]
        result = check_completeness(dp)
        assert result.verdict == "blocked"
        assert any(i["dimension"] == "business_design" for i in result.missing_items)

    def test_conditional_ux_required_when_ui_detected(self) -> None:
        dp = _make_full_package()
        dp["product_design"]["prd"] = "Build a frontend UI"
        result = check_completeness(dp)
        assert result.verdict == "blocked"
        assert any(i["dimension"] == "ux_design" for i in result.missing_items)

    def test_optional_test_design_missing_warning_only(self) -> None:
        dp = _make_full_package()
        del dp["test_design"]
        result = check_completeness(dp)
        # test_design optional; missing produces warning, verdict partial
        assert result.verdict == "partial"
        assert any(w["dimension"] == "test_design" for w in result.warnings)

    def test_q1_fail_empty_product_vision(self) -> None:
        dp = _make_full_package()
        dp["business_design"]["product_vision"] = ""
        result = check_completeness(dp)
        assert result.verdict == "blocked"
        assert any("Q1" in i.get("reason", "") for i in result.missing_items)

    def test_q2_fail_no_journeys(self) -> None:
        dp = _make_full_package()
        dp["product_design"]["user_journey_map"] = []
        result = check_completeness(dp)
        assert result.verdict == "blocked"
        assert any("Q2" in i.get("reason", "") for i in result.missing_items)

    def test_q3_fail_no_ac(self) -> None:
        dp = _make_full_package()
        dp["product_design"]["acceptance_criteria"] = []
        result = check_completeness(dp)
        assert result.verdict == "blocked"
        assert any("Q3" in i.get("reason", "") for i in result.missing_items)

    def test_q4_fail_empty_tech_stack(self) -> None:
        dp = _make_full_package()
        dp["architecture_design"]["tech_stack"] = {}
        result = check_completeness(dp)
        assert result.verdict == "blocked"
        assert any("Q4" in i.get("reason", "") for i in result.missing_items)
