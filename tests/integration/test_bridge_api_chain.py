"""Integration test for API chain bridge (TEST-01).

This test verifies the end-to-end flow for the bridge API chain.
Tests manifest update with executed status and resume mechanism filtering.

Per ADR-054 §5.1 R-5, R-7, R-9.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from cli.lib.test_orchestrator import update_manifest, _get_failed_coverage_ids


class TestManifestUpdate:
    """Tests for manifest update functionality."""

    def test_update_manifest_with_executed_status(self, tmp_path):
        """Test that manifest is updated with executed status after test run."""
        # Create a mock manifest with designed status
        manifest = {
            "_version": "1",
            "items": [
                {
                    "coverage_id": "CAND-SUBMIT-001",
                    "lifecycle_status": "designed",
                    "evidence_refs": [],
                },
            ],
        }
        manifest_dir = tmp_path / "ssot" / "tests" / "api" / "FEAT-001"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "api-coverage-manifest.yaml"
        manifest_path.write_text(yaml.dump(manifest))

        # Update manifest with executed status
        manifest_items = [
            {
                "coverage_id": "CAND-SUBMIT-001",
                "status": "executed",
                "run_status": "passed",
                "evidence_ref": "candidate.test.001",
                "feat_ref": "FEAT-001",
            },
        ]

        update_manifest(tmp_path, manifest_items, "TEST-RUN-001")

        # Verify manifest was updated
        updated = yaml.safe_load(manifest_path.read_text())
        item = updated["items"][0]
        assert item["lifecycle_status"] == "executed"
        assert item["last_run_id"] == "TEST-RUN-001"
        assert item["last_run_status"] == "passed"
        assert "candidate.test.001" in item["evidence_refs"]

    def test_update_manifest_with_failed_status(self, tmp_path):
        """Test that manifest correctly records failed status."""
        manifest = {
            "_version": "1",
            "items": [
                {
                    "coverage_id": "CAND-SUBMIT-002",
                    "lifecycle_status": "designed",
                    "evidence_refs": [],
                },
            ],
        }
        manifest_dir = tmp_path / "ssot" / "tests" / "api" / "FEAT-001"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "api-coverage-manifest.yaml"
        manifest_path.write_text(yaml.dump(manifest))

        manifest_items = [
            {
                "coverage_id": "CAND-SUBMIT-002",
                "status": "executed",
                "run_status": "failed",
                "evidence_ref": "candidate.test.002",
                "feat_ref": "FEAT-001",
            },
        ]

        update_manifest(tmp_path, manifest_items, "TEST-RUN-002")

        updated = yaml.safe_load(manifest_path.read_text())
        item = updated["items"][0]
        assert item["lifecycle_status"] == "executed"
        assert item["last_run_status"] == "failed"

    def test_update_manifest_multiple_items(self, tmp_path):
        """Test that manifest correctly updates multiple items."""
        manifest = {
            "_version": "1",
            "items": [
                {"coverage_id": "CAND-SUBMIT-001", "lifecycle_status": "designed", "evidence_refs": []},
                {"coverage_id": "CAND-SUBMIT-002", "lifecycle_status": "designed", "evidence_refs": []},
            ],
        }
        manifest_dir = tmp_path / "ssot" / "tests" / "api" / "FEAT-001"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "api-coverage-manifest.yaml"
        manifest_path.write_text(yaml.dump(manifest))

        manifest_items = [
            {
                "coverage_id": "CAND-SUBMIT-001",
                "status": "executed",
                "run_status": "passed",
                "evidence_ref": "candidate.001",
                "feat_ref": "FEAT-001",
            },
            {
                "coverage_id": "CAND-SUBMIT-002",
                "status": "executed",
                "run_status": "failed",
                "evidence_ref": "candidate.002",
                "feat_ref": "FEAT-001",
            },
        ]

        update_manifest(tmp_path, manifest_items, "TEST-RUN-003")

        updated = yaml.safe_load(manifest_path.read_text())
        assert updated["items"][0]["last_run_status"] == "passed"
        assert updated["items"][1]["last_run_status"] == "failed"
        assert "candidate.001" in updated["items"][0]["evidence_refs"]
        assert "candidate.002" in updated["items"][1]["evidence_refs"]


class TestResumeMechanism:
    """Tests for --resume functionality per ADR-054 §5.1 R-7."""

    def test_get_failed_coverage_ids_filters_passed(self, tmp_path):
        """Test that --resume filters to only failed coverage_ids."""
        manifest = {
            "items": [
                {"coverage_id": "CAND-SUBMIT-001", "last_run_status": "passed"},
                {"coverage_id": "CAND-SUBMIT-002", "last_run_status": "failed"},
                {"coverage_id": "CAND-SUBMIT-003", "last_run_status": "failed"},
            ],
        }
        manifest_dir = tmp_path / "ssot" / "tests" / "api" / "FEAT-001"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "api-coverage-manifest.yaml"
        manifest_path.write_text(yaml.dump(manifest))

        failed_ids = _get_failed_coverage_ids(tmp_path, "FEAT-001", None)

        assert len(failed_ids) == 2
        assert "CAND-SUBMIT-002" in failed_ids
        assert "CAND-SUBMIT-003" in failed_ids
        assert "CAND-SUBMIT-001" not in failed_ids

    def test_get_failed_coverage_ids_empty_manifest(self, tmp_path):
        """Test that empty manifest returns empty list."""
        failed_ids = _get_failed_coverage_ids(tmp_path, "FEAT-999", None)
        assert failed_ids == []

    def test_get_failed_coverage_ids_no_failed(self, tmp_path):
        """Test that manifest with no failures returns empty list."""
        manifest = {
            "items": [
                {"coverage_id": "CAND-SUBMIT-001", "last_run_status": "passed"},
                {"coverage_id": "CAND-SUBMIT-002", "last_run_status": "passed"},
            ],
        }
        manifest_dir = tmp_path / "ssot" / "tests" / "api" / "FEAT-001"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "api-coverage-manifest.yaml"
        manifest_path.write_text(yaml.dump(manifest))

        failed_ids = _get_failed_coverage_ids(tmp_path, "FEAT-001", None)
        assert failed_ids == []

    def test_e2e_manifest_resume(self, tmp_path):
        """Test resume mechanism for E2E chain."""
        manifest = {
            "items": [
                {"coverage_id": "JOURNEY-001", "last_run_status": "passed"},
                {"coverage_id": "JOURNEY-002", "last_run_status": "failed"},
            ],
        }
        manifest_dir = tmp_path / "ssot" / "tests" / "e2e" / "PROTO-001"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "e2e-coverage-manifest.yaml"
        manifest_path.write_text(yaml.dump(manifest))

        failed_ids = _get_failed_coverage_ids(tmp_path, None, "PROTO-001")

        assert len(failed_ids) == 1
        assert "JOURNEY-002" in failed_ids


class TestChainIntegration:
    """Integration tests verifying the full chain orchestration."""

    def test_spec_adapter_compat_output_structure(self, tmp_path):
        """Test that SPEC_ADAPTER_COMPAT has correct structure for API chain."""
        from cli.lib.spec_adapter import spec_to_testset, SpecAdapterInput

        # Create minimal API spec
        spec_content = """## Case Metadata
| case_id | SPEC-API-001 |
| capability | API-TEST |
| scenario_type | smoke |
| coverage_id | API-COV-001 |
| priority | P0 |

## Request
```json
{}
```

## Response Assertions
- status_code == 200
"""
        spec_dir = tmp_path / "api-test-spec"
        spec_dir.mkdir()
        spec_file = spec_dir / "SPEC-API-001.md"
        spec_file.write_text(spec_content)

        input = SpecAdapterInput(
            spec_files=[spec_file],
            feat_ref="FEAT-API-001",
            modality="api",
        )
        result = spec_to_testset(tmp_path, input)

        # Verify SPEC_ADAPTER_COMPAT structure
        assert result["ssot_type"] == "SPEC_ADAPTER_COMPAT"
        assert result["feat_ref"] == "FEAT-API-001"
        assert result["source_chain"] == "api"
        assert len(result["test_units"]) == 1
        unit = result["test_units"][0]
        assert unit["unit_ref"] == "SPEC-API-001"
        assert "_source_coverage_id" in unit
        assert unit["_source_coverage_id"] == "API-COV-001"
        assert "_api_extension" in unit
        assert unit["_api_extension"]["scenario_type"] == "smoke"