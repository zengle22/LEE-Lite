"""Unit tests for impl-verify modules (tasks 7.1–10.7)."""

from __future__ import annotations

import pytest

from cli.lib.v2.convergence import compute_final_verdict, converge_and_gate
from cli.lib.v2.delivery_parser import parse_gsd_delivery
from cli.lib.v2.engineering_docs import check_engineering_docs
from cli.lib.v2.feedback import classify_issue, route_issues
from cli.lib.v2.scope_compliance import check_feature_scope
from cli.lib.v2.task_completion import check_task_completion
from cli.lib.v2.traceability import verify_traceability
from cli.lib.v2.models import FEAT, IMPL, UI


class TestTaskCompletion:
    def test_scope_pass(self) -> None:
        impl = IMPL(
            impl_id="IMPL-001",
            requirement_context={},
            tech_context={},
            arch_context={},
            api_context={},
            allowed_scope={"directories": ["src/"], "files": []},
            source_refs=[],
        )
        gsd = {
            "code": {
                "files_changed": ["src/main.py"],
                "files_added": [],
            }
        }
        result = check_task_completion(impl, gsd)
        assert result["scope_compliance"] == "pass"
        assert result["out_of_scope_files"] == []

    def test_scope_fail_out_of_scope(self) -> None:
        impl = IMPL(
            impl_id="IMPL-001",
            requirement_context={},
            tech_context={},
            arch_context={},
            api_context={},
            allowed_scope={"directories": ["src/"], "files": []},
            source_refs=[],
        )
        gsd = {
            "code": {
                "files_changed": ["other/file.py"],
                "files_added": [],
            }
        }
        result = check_task_completion(impl, gsd)
        assert result["scope_compliance"] == "fail"
        assert result["out_of_scope_files"] == ["other/file.py"]


class TestEngineeringDocs:
    def test_complete_docs_pass(self) -> None:
        gsd = {
            "engineering_artifacts": {
                "change_description": "This is a detailed change description that is definitely longer than fifty characters.",
                "rollback_plan": "Rollback by reverting commit",
                "key_decisions": "This is a key decision with rationale that exceeds twenty chars.",
                "dependency_changes": "Updated pytest",
                "known_issues": "None",
            }
        }
        result = check_engineering_docs(gsd)
        assert result["engineering_docs"] == "pass"

    def test_missing_rollback_fail(self) -> None:
        gsd = {
            "engineering_artifacts": {
                "change_description": "Short description that is definitely longer than fifty characters.",
            }
        }
        result = check_engineering_docs(gsd)
        assert result["engineering_docs"] == "fail"
        assert any(m["doc_type"] == "rollback_plan" for m in result["missing_docs"])


class TestFeatureScope:
    def test_no_unauthorized_features(self) -> None:
        gsd = {"code": {"git_diff": "+def existing(): pass"}}
        api_specs = [{"path": "/api/v1"}]
        result = check_feature_scope(gsd, api_specs)
        assert result["scope_compliance"] == "pass"


class TestTraceability:
    def test_exempt_files(self) -> None:
        gsd = {"code": {"git_diff": "+++ b/README.md\n+ updated"}}
        feats = [FEAT(feat_id="FEAT-001", title="Test", user_value="uv", trigger="t", main_flow=["m"], acceptance_criteria=["AC1"], source_refs=[])]
        result = verify_traceability(gsd, feats)
        assert result["traceability"] == "pass"
        assert len(result["exempt_items"]) == 1


class TestConvergence:
    def test_both_pass(self) -> None:
        line1 = {"verdict": "pass", "issues": []}
        line2 = {"verdict": "pass", "issues": []}
        result = converge_and_gate(line1, line2)
        assert result["convergence"] == "pass"
        assert result["release_ready"] is True

    def test_line2_fail(self) -> None:
        line1 = {"verdict": "pass", "issues": []}
        line2 = {"verdict": "fail", "issues": [{"reason": "bug"}]}
        result = converge_and_gate(line1, line2)
        assert result["convergence"] == "fail"
        assert result["blocking_line"] == "line_2"

    def test_timeout(self) -> None:
        line1 = {"verdict": "pass", "issues": []}
        line2 = {"verdict": "pass", "issues": []}
        result = converge_and_gate(line1, line2, timeout=True)
        assert result["convergence"] == "fail"
        assert result["blocking_line"] == "timeout"

    def test_compute_verdict_pass(self) -> None:
        task = {"task_completion": "pass", "scope_compliance": "pass"}
        eng = {"engineering_docs": "pass", "missing_docs": [], "doc_quality_warnings": []}
        scope = {"scope_compliance": "pass", "unauthorized_features": [], "semantic_changes": []}
        trace = {"traceability": "pass", "full_traces": [], "partial_traces": [], "no_trace_items": [], "exempt_items": []}
        result = compute_final_verdict(task, eng, scope, trace)
        assert result["final_verdict"] == "pass"


class TestFeedback:
    def test_classify_bug_fix(self) -> None:
        feat = FEAT(feat_id="FEAT-001", title="T", user_value="uv", trigger="t", main_flow=["m"], acceptance_criteria=["AC1"], source_refs=[])
        result = classify_issue("ac_mismatch", "Does not match AC", feat=feat)
        assert result["type"] == "bug_fix"
        assert result["linked_feat"] == "FEAT-001"

    def test_classify_frz_revise(self) -> None:
        result = classify_issue("unauthorized_feature", "New endpoint added")
        assert result["type"] == "frz_revise"

    def test_route_issues(self) -> None:
        findings = [{"type": "unauthorized_feature", "description": "new api"}]
        routed = route_issues(findings, [], [])
        assert routed[0]["type"] == "frz_revise"
