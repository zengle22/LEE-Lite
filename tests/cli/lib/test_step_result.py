"""Unit tests for cli/lib/contracts.py StepResult and EnvConfig dataclasses."""

import pytest
from cli.lib.contracts import StepResult, EnvConfig


class TestStepResult:
    def test_create_with_all_fields(self):
        result = StepResult(
            run_id="RUN-001",
            execution_refs={"candidate_artifact_ref": "candidate.123"},
            candidate_path="artifacts/active/qa/candidates/candidate.123.json",
            case_results=[
                {"coverage_id": "CAND-SUBMIT-001", "case_id": "SPEC-001", "status": "passed"},
            ],
            manifest_items=[
                {"coverage_id": "CAND-SUBMIT-001", "status": "executed", "evidence_ref": "candidate.123"},
            ],
            execution_output_dir="playwright-output/",
        )
        assert result.run_id == "RUN-001"
        assert result.execution_refs["candidate_artifact_ref"] == "candidate.123"
        assert len(result.case_results) == 1
        assert len(result.manifest_items) == 1

    def test_create_with_required_only(self):
        result = StepResult(run_id="RUN-002")
        assert result.run_id == "RUN-002"
        assert result.execution_refs == {}
        assert result.candidate_path == ""
        assert result.case_results == []
        assert result.manifest_items == []
        assert result.execution_output_dir == ""

    def test_manifest_items_for_update(self):
        result = StepResult(
            run_id="RUN-003",
            manifest_items=[
                {"coverage_id": "CAND-SUBMIT-001", "status": "executed", "evidence_ref": "cand.001"},
                {"coverage_id": "CAND-SUBMIT-002", "status": "executed", "evidence_ref": "cand.002"},
            ],
        )
        assert len(result.manifest_items) == 2
        assert result.manifest_items[0]["coverage_id"] == "CAND-SUBMIT-001"


class TestEnvConfig:
    def test_create_api_config(self):
        config = EnvConfig(
            feat_ref="FEAT-001",
            modality="api",
            base_url="http://localhost:8000",
            api_url="http://localhost:8000",
        )
        assert config.feat_ref == "FEAT-001"
        assert config.modality == "api"
        assert config.base_url == "http://localhost:8000"
        assert config.api_url == "http://localhost:8000"

    def test_create_e2e_config(self):
        config = EnvConfig(
            proto_ref="PROTO-001",
            modality="web_e2e",
            app_url="http://localhost:3000",
            api_url="http://localhost:8000",
            browser="chromium",
        )
        assert config.proto_ref == "PROTO-001"
        assert config.modality == "web_e2e"
        assert config.app_url == "http://localhost:3000"
        assert config.api_url == "http://localhost:8000"
        assert config.browser == "chromium"