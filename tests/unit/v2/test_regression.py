"""Regression tests for SSOT compiler schema consistency and source tracing.

Covers:
- REG-001: decision field must expand to sub-fields (not regress to object placeholder)
- Source tracing: auto_generated/inferred fields detected by quality gate
- Trigger extraction: backtick cleanup and smart truncation
- No hallucination: endpoints from source docs must not have auto-generated schemas
"""

import pytest

from cli.lib.v2.compiler import (
    _expand_object_schema,
    _extract_ac_endpoints,
    _extract_trigger_from_ac,
    _is_object_type,
)
from cli.lib.v2.dimension_quality import _check_api


class TestDecisionFieldExpansion:
    """REG-001: decision field must not regress from sub-fields to object placeholder."""

    def test_expand_flat_string_object(self):
        """Legacy flat format: decision: object → expanded."""
        endpoints = [{"path": "/test", "method": "GET", "response_schema": {"decision": "object"}}]
        _expand_object_schema(endpoints)
        decision = endpoints[0]["response_schema"]["decision"]
        assert isinstance(decision, dict)
        assert "action" in decision
        assert "card_type" in decision

    def test_expand_nested_dict_object(self):
        """Nested dict format: decision: {type: object, ...} → expanded."""
        endpoints = [{
            "path": "/v1/training-plan/{id}/today",
            "method": "GET",
            "response_schema": {
                "decision": {"type": "object", "description": "decision", "required": True}
            }
        }]
        _expand_object_schema(endpoints)
        decision = endpoints[0]["response_schema"]["decision"]
        assert isinstance(decision, dict)
        assert "action" in decision
        assert "card_type" in decision
        assert "audit_id" in decision

    def test_expand_preserves_description(self):
        """Expansion should preserve source description in _description field."""
        endpoints = [{
            "path": "/test",
            "method": "GET",
            "response_schema": {
                "decision": {"type": "object", "description": "DecisionOutput", "required": True}
            }
        }]
        _expand_object_schema(endpoints)
        decision = endpoints[0]["response_schema"]["decision"]
        assert decision.get("_description") == "DecisionOutput"

    def test_no_expand_for_non_object(self):
        """Non-object fields should not be expanded."""
        endpoints = [{"path": "/test", "method": "GET", "response_schema": {"version": "string"}}]
        _expand_object_schema(endpoints)
        assert endpoints[0]["response_schema"]["version"] == "string"


class TestSourceTracing:
    """Quality gate must detect auto_generated and inferred fields."""

    def test_auto_generated_handler_is_blocker(self):
        """Handler marked auto_generated should be treated as missing."""
        api = type("API", (), {"endpoints": [{
            "path": "/v1/test",
            "method": "POST",
            "handler": "post_v1_test",
            "priority": "P1",
            "request_schema": {"id": "string"},
            "response_schema": {"id": "string"},
            "error_codes": {"400": "Bad"},
            "_source": {
                "handler": "auto_generated",
                "priority": "document",
                "request_schema": "document",
                "response_schema": "document",
                "error_codes": "document",
            }
        }]})()
        verdict = _check_api([api])
        assert any("auto_generated" in b for b in verdict.blockers)

    def test_inferred_field_is_warning(self):
        """Field marked inferred should trigger warning but not blocker."""
        api = type("API", (), {
            "endpoints": [{
                "path": "/v1/test",
                "method": "POST",
                "handler": "handler.go",
                "priority": "P1",
                "request_schema": {"id": "string"},
                "response_schema": {"id": "string"},
                "error_codes": {"400": "Bad"},
                "_source": {
                    "handler": "document",
                    "priority": "document",
                    "request_schema": "inferred",
                    "response_schema": "document",
                    "error_codes": "document",
                }
            }],
            "sequence_diagrams": ["sequenceDiagram\n  A->>B: test"],
            "version_strategy": "url_path_versioning",
        })()
        verdict = _check_api([api])
        assert not any("sequence_diagrams" in b for b in verdict.blockers)
        assert any("inferred" in w for w in verdict.warnings)

    def test_document_fields_pass_clean(self):
        """All fields from document should pass without source issues."""
        api = type("API", (), {
            "endpoints": [{
                "path": "/v1/test",
                "method": "POST",
                "handler": "handler.go",
                "priority": "P1",
                "request_schema": {"id": "string"},
                "response_schema": {"id": "string"},
                "error_codes": {"400": "Bad"},
                "_source": {
                    "handler": "document",
                    "priority": "document",
                    "request_schema": "document",
                    "response_schema": "document",
                    "error_codes": "document",
                }
            }],
            "sequence_diagrams": ["sequenceDiagram\n  A->>B: test"],
            "version_strategy": "url_path_versioning",
        })()
        verdict = _check_api([api])
        assert not any("sequence_diagrams" in b for b in verdict.blockers)
        assert not any("inferred" in w or "auto_generated" in w for w in verdict.warnings)


class TestNoHallucination:
    """AC-derived endpoints must NOT have auto-generated schemas."""

    def test_ac_endpoint_no_auto_handler(self):
        """Endpoints extracted from ACs should not have auto-generated handler."""
        acs = ["AC-007.3: Given user calls POST /v1/decisions/pre-run-checkin"]
        endpoints = _extract_ac_endpoints(acs)
        assert len(endpoints) == 1
        ep = endpoints[0]
        assert "handler" not in ep
        assert ep["_source"]["path"] == "document"
        assert ep["_source"]["method"] == "document"

    def test_ac_endpoint_error_code_from_ac(self):
        """Error codes extracted from AC text should be marked as document-sourced."""
        acs = ['AC-007.3: Given user calls POST /v1/test, Then returns HTTP 400, error_code="MISSING_CHECKIN"']
        endpoints = _extract_ac_endpoints(acs)
        assert len(endpoints) == 1
        ep = endpoints[0]
        assert ep.get("error_codes", {}).get("MISSING_CHECKIN") == "Defined in AC"
        assert ep["_source"].get("error_codes") == "document"


class TestTriggerExtraction:
    """Trigger extraction must clean backticks and avoid mid-word truncation."""

    def test_removes_backticks(self):
        """Backtick wrappers should be removed from trigger text."""
        ac = "Given user submits `BodyCheckin` with `sleep_quality=poor`, When API validates, Then returns 400"
        trigger = _extract_trigger_from_ac(ac)
        assert "`" not in trigger
        assert "BodyCheckin" in trigger
        assert "sleep_quality=poor" in trigger

    def test_smart_truncate_no_mid_word(self):
        """Truncation should not cut a word in half."""
        long_text = "Given " + "word " * 100 + "ends"
        trigger = _extract_trigger_from_ac(long_text)
        assert len(trigger) <= 200
        # Should not end with a partial word
        assert trigger[-1] != "w"  # Not mid-word

    def test_no_given_clause_fallback(self):
        """If no Given clause, fall back to first 100 chars of AC text."""
        ac = "When user clicks submit, Then system validates input"
        trigger = _extract_trigger_from_ac(ac)
        assert "When user clicks submit" in trigger


class TestIsObjectType:
    """_is_object_type must detect both string and dict object declarations."""

    def test_string_object(self):
        assert _is_object_type("object") is True

    def test_dict_object(self):
        assert _is_object_type({"type": "object", "description": "x"}) is True

    def test_string_non_object(self):
        assert _is_object_type("string") is False

    def test_dict_non_object(self):
        assert _is_object_type({"type": "string"}) is False

    def test_none(self):
        assert _is_object_type(None) is False
