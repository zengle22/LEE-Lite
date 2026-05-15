"""Adversarial tests for dimension quality gate.

These tests verify that the quality gate can detect specific defect patterns
identified in ARCHITECT-INVESTIGATION-QG-BLIND-SPOTS-001.

Each test constructs a minimal SSOT chain with a known defect and asserts
that the quality gate produces the expected verdict.
"""

from __future__ import annotations

import pytest

from cli.lib.v2.dimension_quality import (
    check_dimension_quality,
    _has_chapter_number_prefix,
    _has_duplicate_items,
    _has_flat_schema,
    _has_mixed_language_keys,
    _impl_redundancy_score,
    _is_truncated,
    _is_valid_url_path,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeObj:
    """Minimal stand-in for compiled SSOT dataclass objects."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _make_api_endpoint(
    path: str = "/v1/test",
    method: str = "GET",
    handler: str | None = "get_v1_test",
    priority: str | None = "P1",
    request_schema: dict | None = None,
    response_schema: dict | None = None,
    error_codes: dict | None = None,
    extra: dict | None = None,
) -> dict:
    ep: dict = {
        "path": path,
        "method": method,
    }
    if handler is not None:
        ep["handler"] = handler
    if priority is not None:
        ep["priority"] = priority
    if request_schema is not None:
        ep["request_schema"] = request_schema
    if response_schema is not None:
        ep["response_schema"] = response_schema
    if error_codes is not None:
        ep["error_codes"] = error_codes
    if extra:
        ep.update(extra)
    return ep


# ---------------------------------------------------------------------------
# Semantic correctness helpers
# ---------------------------------------------------------------------------

class TestSemanticHelpers:
    def test_is_truncated_ellipsis(self):
        assert _is_truncated("核心痛点是...") is True
        assert _is_truncated("核心痛点是") is False

    def test_is_truncated_short_title_ok(self):
        # Short captions should NOT be flagged as truncated
        assert _is_truncated("US-001: 跑步能力基线自动估算") is False

    def test_is_truncated_long_prose_no_punct(self):
        long_text = "这是一个很长的文本没有任何标点符号所以应该被视为截断因为它不完整" * 3
        assert _is_truncated(long_text) is True

    def test_chapter_number_prefix(self):
        assert _has_chapter_number_prefix("9.1 跑前流程改造") is True
        assert _has_chapter_number_prefix("跑前流程改造") is False

    def test_duplicate_items(self):
        assert _has_duplicate_items([{"id": "RISK-1"}, {"id": "RISK-1"}]) is True
        assert _has_duplicate_items([{"id": "RISK-1"}, {"id": "RISK-2"}]) is False

    def test_valid_url_path(self):
        assert _is_valid_url_path("/v1/decisions/today") is True
        assert _is_valid_url_path("/v1/decisions/today（再次调用）") is False
        assert _is_valid_url_path("/v1//decisions") is False
        assert _is_valid_url_path("/v1/decisions/") is False

    def test_mixed_language_keys(self):
        assert _has_mixed_language_keys({"path": "/v1", "路径": "/v1"}) is True
        assert _has_mixed_language_keys({"path": "/v1", "method": "POST"}) is False

    def test_flat_schema(self):
        assert _has_flat_schema({"session_id": "string"}) is True
        assert _has_flat_schema({"session_id": {"type": "string"}}) is False


# ---------------------------------------------------------------------------
# Defect 1: Semantic correctness — SRC epic chapter number drift
# ---------------------------------------------------------------------------

class TestDefect1SemanticCorrectness:
    def test_src_epic_chapter_number_blocked(self):
        """EPIC capability_name containing chapter number should lower score."""
        chain = {
            "src": _FakeObj(
                problem_domain="A" * 100 + "。",
                business_goal="B" * 100 + "。",
                target_users=["runner"],
                triggering_scenarios=["morning run"],
                scope_boundaries=["In: x", "Out: y", "In: z"],
                non_goals=["not x"],
                global_constraints=["c1"],
                epics=[
                    _FakeObj(
                        epic_id="EPIC-001",
                        capability_name="2. Happy Path — 晨间训练闭环",
                        feats=[_FakeObj(feat_id="FEAT-001-001")],
                    ),
                ],
            ),
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [],
            "uis": [],
            "impls": [],
        }
        verdicts = check_dimension_quality(chain)
        src_v = next(v for v in verdicts if v.dimension == "src")
        assert any("chapter number" in b.lower() for b in src_v.blockers), src_v.blockers

    def test_src_truncated_problem_domain_warning(self):
        """Truncated problem_domain should produce a warning."""
        chain = {
            "src": _FakeObj(
                problem_domain="核心痛点是...",
                business_goal="B" * 100 + "。",
                target_users=["runner"],
                triggering_scenarios=["morning run"],
                scope_boundaries=["In: x", "Out: y", "In: z"],
                non_goals=["not x"],
                global_constraints=["c1"],
                epics=[
                    _FakeObj(
                        epic_id="EPIC-001",
                        capability_name="US-001: 基线估算",
                        feats=[_FakeObj(feat_id="FEAT-001-001")],
                    ),
                ],
            ),
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [],
            "uis": [],
            "impls": [],
        }
        verdicts = check_dimension_quality(chain)
        src_v = next(v for v in verdicts if v.dimension == "src")
        assert any("truncated" in w.lower() for w in src_v.warnings), src_v.warnings


# ---------------------------------------------------------------------------
# Defect 2: Per-unit integrity — API shell endpoints
# ---------------------------------------------------------------------------

class TestDefect2PerUnitIntegrity:
    def test_api_shell_endpoint_blocked(self):
        """An endpoint with only error_codes (no handler/priority/schema) is a shell."""
        chain = {
            "src": None,
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [
                _FakeObj(
                    endpoints=[
                        _make_api_endpoint(),  # complete
                        {
                            "path": "/v1/decisions/pre-run-checkin",
                            "method": "POST",
                            "error_codes": {"MISSING_CHECKIN": "x"},
                        },  # shell
                    ],
                    version_strategy="url_path_versioning",
                    sequence_diagrams=["seq"],
                )
            ],
            "uis": [],
            "impls": [],
        }
        verdicts = check_dimension_quality(chain)
        api_v = next(v for v in verdicts if v.dimension == "api")
        assert any("pre-run-checkin" in b and "missing" in b.lower() for b in api_v.blockers), api_v.blockers

    def test_api_mixed_language_keys_blocked(self):
        """Endpoint with both Chinese and English keys should be blocked."""
        chain = {
            "src": None,
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [
                _FakeObj(
                    endpoints=[
                        {
                            "path": "/v1/test",
                            "方法": "POST",
                            "handler": "h",
                            "priority": "P1",
                            "request_schema": {},
                            "response_schema": {},
                            "error_codes": {},
                        }
                    ],
                    version_strategy="url_path_versioning",
                    sequence_diagrams=["seq"],
                )
            ],
            "uis": [],
            "impls": [],
        }
        verdicts = check_dimension_quality(chain)
        api_v = next(v for v in verdicts if v.dimension == "api")
        assert any("mixed" in b.lower() for b in api_v.blockers), api_v.blockers

    def test_api_flat_schema_warning(self):
        """Flat schema format should produce a warning."""
        chain = {
            "src": None,
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [
                _FakeObj(
                    endpoints=[
                        _make_api_endpoint(
                            request_schema={"session_id": "string"},  # flat
                            response_schema={"feedback_id": "string"},  # flat
                        )
                    ],
                    version_strategy="url_path_versioning",
                    sequence_diagrams=["seq"],
                )
            ],
            "uis": [],
            "impls": [],
        }
        verdicts = check_dimension_quality(chain)
        api_v = next(v for v in verdicts if v.dimension == "api")
        assert any("flat" in w.lower() for w in api_v.warnings), api_v.warnings


# ---------------------------------------------------------------------------
# Defect 3: Post-compilation validation — IMPL grouping
# ---------------------------------------------------------------------------

class TestDefect3ImplGrouping:
    def test_impl_duplicate_epic_key_blocked(self):
        """Duplicate epic_key across IMPL files should be blocked."""
        chain = {
            "src": None,
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [],
            "uis": [],
            "impls": [
                _FakeObj(
                    allowed_scope={"directories": ["src/"], "files": ["*.py"]},
                    forbidden_scope={"files": []},
                    test_guidance={"boundary_conditions": ["bc1"], "test_layering": ["tl1"]},
                    requirement_context={"epic_key": "EPIC-001", "trigger": "t1", "acceptance_criteria": ["AC-001"]},
                ),
                _FakeObj(
                    allowed_scope={"directories": ["src/"], "files": ["*.py"]},
                    forbidden_scope={"files": []},
                    test_guidance={"boundary_conditions": ["bc2"], "test_layering": ["tl2"]},
                    requirement_context={"epic_key": "EPIC-001", "trigger": "t2", "acceptance_criteria": ["AC-002"]},
                ),
            ],
        }
        verdicts = check_dimension_quality(chain)
        impl_v = next(v for v in verdicts if v.dimension == "impl")
        assert any("duplicate epic_key" in b.lower() for b in impl_v.blockers), impl_v.blockers

    def test_impl_redundancy_blocked(self):
        """100% identical tech/arch/api contexts across files should be blocked."""
        chain = {
            "src": None,
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [],
            "uis": [],
            "impls": [
                _FakeObj(
                    allowed_scope={"directories": ["src/"], "files": ["*.py"]},
                    forbidden_scope={"files": []},
                    test_guidance={"boundary_conditions": ["bc"], "test_layering": ["tl"]},
                    requirement_context={"epic_key": "EPIC-001", "trigger": "t", "acceptance_criteria": ["AC-001"]},
                    tech_context={"stack": "go"},
                    arch_context={"layering": "3-tier"},
                    api_context={"version": "v1"},
                ),
                _FakeObj(
                    allowed_scope={"directories": ["src/"], "files": ["*.py"]},
                    forbidden_scope={"files": []},
                    test_guidance={"boundary_conditions": ["bc"], "test_layering": ["tl"]},
                    requirement_context={"epic_key": "EPIC-002", "trigger": "t", "acceptance_criteria": ["AC-002"]},
                    tech_context={"stack": "go"},
                    arch_context={"layering": "3-tier"},
                    api_context={"version": "v1"},
                ),
            ],
        }
        verdicts = check_dimension_quality(chain)
        impl_v = next(v for v in verdicts if v.dimension == "impl")
        assert any("redundant" in b.lower() for b in impl_v.blockers), impl_v.blockers


# ---------------------------------------------------------------------------
# Defect 4: Cross-axis traceability
# ---------------------------------------------------------------------------

class TestDefect4CrossAxisTraceability:
    def test_frz_total_ac_zero_blocked(self):
        """FRZ total_ac=0 should be caught via cross-axis traceability."""
        chain = {
            "src": _FakeObj(epics=[_FakeObj(epic_id="E1")]),
            "epics": [_FakeObj(epic_id="E1")],
            "feats": [],
            "techs": [],
            "archs": [],
            "apis": [],
            "uis": [],
            "impls": [],
            "frz": _FakeObj(total_ac=0, covered_ac=0),
        }
        verdicts = check_dimension_quality(chain)
        impl_v = next(v for v in verdicts if v.dimension == "impl")
        assert any("total_ac" in b.lower() for b in impl_v.blockers), impl_v.blockers


# ---------------------------------------------------------------------------
# Defect 5: TECH / ARCH semantic drift
# ---------------------------------------------------------------------------

class TestDefect5TechArchSemantic:
    def test_tech_duplicate_risks_blocked(self):
        """Duplicate risks in TECH should be blocked."""
        chain = {
            "src": None,
            "epics": [],
            "feats": [],
            "techs": [
                _FakeObj(
                    tech_stack=["go"],
                    sync_async={"text": "async"},
                    non_functional=[{"title": "p99", "description": "<10s"}],
                    constraints=[{"title": "c1", "description": "d1"}],
                    risks=[
                        {"title": "RISK-1", "description": "d1"},
                        {"title": "RISK-2", "description": "d2"},
                        {"title": "RISK-1", "description": "d1"},  # duplicate
                    ],
                )
            ],
            "archs": [],
            "apis": [],
            "uis": [],
            "impls": [],
        }
        verdicts = check_dimension_quality(chain)
        tech_v = next(v for v in verdicts if v.dimension == "tech")
        assert any("duplicate" in b.lower() for b in tech_v.blockers), tech_v.blockers

    def test_arch_data_flow_chapter_number_blocked(self):
        """ARCH data_flow title with chapter number should be blocked."""
        chain = {
            "src": None,
            "epics": [],
            "feats": [],
            "techs": [],
            "archs": [
                _FakeObj(
                    target_architecture="microservices",
                    layering={"layers": ["transport", "handler", "service", "repository"]},
                    data_flow={"9.1 跑前流程改造": "details", "9.2 跑后流程改造": "details"},
                    storage={"tables": ["users"]},
                    integration={"deps": ["mysql"]},
                    frozen_contracts=["c1"],
                    constraints=[{"title": "c1", "description": "d1"}],
                )
            ],
            "apis": [],
            "uis": [],
            "impls": [],
        }
        verdicts = check_dimension_quality(chain)
        arch_v = next(v for v in verdicts if v.dimension == "arch")
        assert any("chapter number" in b.lower() for b in arch_v.blockers), arch_v.blockers
