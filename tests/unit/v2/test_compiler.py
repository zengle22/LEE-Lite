"""Unit tests for SSOT chain compiler (tasks 3.1–3.10)."""

from __future__ import annotations

import pytest

from cli.lib.v2.compiler import (
    compile_api,
    compile_arch,
    compile_epics,
    compile_feats,
    compile_impls,
    compile_src,
    compile_ssot_chain,
    compile_tech,
    compile_ui,
)
from cli.lib.v2.exceptions import InventedSemanticsError
from cli.lib.v2.models import API, ARCH, EPIC, FEAT, IMPL, SRC, TECH, UI


def _make_design_package() -> dict:
    return {
        "business_design": {
            "product_vision": "Build a compiler",
            "scope_declaration": {"in_scope": ["freeze"], "out_of_scope": ["analysis"]},
            "target_users": ["devs"],
            "non_goals": ["no analysis"],
            "global_constraints": ["immutable"],
        },
        "product_design": {
            "prd": "PRD content here",
            "user_journey_map": [
                {"name": "Compile journey", "steps": ["input", "check", "output"]},
            ],
            "acceptance_criteria": ["AC1: given x when y then z"],
        },
        "architecture_design": {
            "tech_stack": {"language": "Python"},
            "api_contract": [{"path": "/api/v1"}],
            "layering": {"presentation": "API", "business": "Skill"},
            "data_flow": {"input": "Design Package", "output": "FRZ Package"},
            "storage_design": {"type": "file_system"},
            "integration_points": [{"service": "BMAD"}],
        },
        "engineering_design": {
            "implementation_scope": {"directories": ["src/"]},
            "key_decisions": ["use dataclasses"],
        },
        "ux_design": {
            "design_principles": ["consistency"],
            "interaction_flow": {},
            "state_expression": {},
            "design_tokens": {},
            "copy_style": {},
            "platform_strategy": {},
            "error_state_ux": {},
            "prototype": "proto.html",
        },
    }


class TestCompileSrc:
    def test_returns_src(self) -> None:
        dp = _make_design_package()
        src = compile_src(dp, "SRC-001")
        assert isinstance(src, SRC)
        assert src.src_id == "SRC-001"
        assert src.problem_domain == "Build a compiler"
        assert src.source_refs


class TestCompileEpics:
    def test_returns_epics(self) -> None:
        dp = _make_design_package()
        epics = compile_epics(dp, "SRC-001")
        assert len(epics) == 1
        assert epics[0].epic_id == "EPIC-SRC-001-001"
        assert epics[0].capability_name == "Compile journey"


class TestCompileFeats:
    def test_returns_feats_and_bound_epics(self) -> None:
        dp = _make_design_package()
        epics = compile_epics(dp, "SRC-001")
        feats, bound_epics = compile_feats(dp, epics, "SRC-001")
        assert len(feats) == 1
        assert feats[0].feat_id == "FEAT-SRC-001-001-001"
        assert bound_epics[0].feats[0].feat_id == feats[0].feat_id


class TestCompileTechArchApiUi:
    def test_tech(self) -> None:
        dp = _make_design_package()
        techs = compile_tech(dp, "SRC-001")
        assert len(techs) == 1
        assert isinstance(techs[0], TECH)

    def test_arch(self) -> None:
        dp = _make_design_package()
        archs = compile_arch(dp, "SRC-001")
        assert len(archs) == 1
        assert isinstance(archs[0], ARCH)

    def test_api(self) -> None:
        dp = _make_design_package()
        apis = compile_api(dp, "SRC-001")
        assert len(apis) == 1
        assert isinstance(apis[0], API)

    def test_ui(self) -> None:
        dp = _make_design_package()
        uis = compile_ui(dp, "SRC-001")
        assert len(uis) == 1
        assert isinstance(uis[0], UI)

    def test_ui_missing_returns_empty(self) -> None:
        dp = _make_design_package()
        del dp["ux_design"]
        uis = compile_ui(dp, "SRC-001")
        assert uis == []


class TestCompileImpls:
    def test_returns_impls(self) -> None:
        dp = _make_design_package()
        epics = compile_epics(dp, "SRC-001")
        feats, _ = compile_feats(dp, epics, "SRC-001")
        techs = compile_tech(dp, "SRC-001")
        archs = compile_arch(dp, "SRC-001")
        apis = compile_api(dp, "SRC-001")
        impls = compile_impls(feats, techs, archs, apis, dp, "SRC-001")
        assert len(impls) == 1
        assert isinstance(impls[0], IMPL)
        assert impls[0].requirement_context["feat_id"] == feats[0].feat_id


class TestCompileSsotChain:
    def test_full_chain(self) -> None:
        dp = _make_design_package()
        chain = compile_ssot_chain(dp, "SRC-001")
        assert "src" in chain
        assert "epics" in chain
        assert "feats" in chain
        assert "techs" in chain
        assert "archs" in chain
        assert "apis" in chain
        assert "uis" in chain
        assert "impls" in chain
        assert chain["src"].epics[0].feats[0].cross_axis_refs

    def test_source_refs_present(self) -> None:
        dp = _make_design_package()
        chain = compile_ssot_chain(dp, "SRC-001")
        assert chain["src"].source_refs
        assert chain["feats"][0].source_refs
        assert chain["techs"][0].source_refs


class TestInventedSemantics:
    def test_invented_field_raises(self) -> None:
        from dataclasses import dataclass
        from cli.lib.v2.compiler import _check_invented

        @dataclass
        class FakeObj:
            real_field: str = "from source"
            invented_field: str = "no source"

        with pytest.raises(InventedSemanticsError):
            _check_invented(FakeObj(), {"real_field": "from source"})
