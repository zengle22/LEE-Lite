"""Unit tests for cli/lib/environment_provision.py."""

import pytest
from pathlib import Path
from cli.lib.environment_provision import provision_environment
import yaml


class TestEnvironmentProvision:
    def test_api_chain_env_generation(self, tmp_path):
        env_path, env_config = provision_environment(
            workspace_root=tmp_path,
            feat_ref="FEAT-001",
            base_url="http://localhost:8000",
            modality="api",
            browser="chromium",
            timeout=30000,
            feat_assumptions=None,
        )

        assert env_path.exists()
        assert env_config["feat_ref"] == "FEAT-001"
        assert env_config["modality"] == "api"

        # Verify ENV file content
        with open(env_path, encoding="utf-8") as f:
            env_data = yaml.safe_load(f)

        assert env_data["ssot_type"] == "TEST_ENVIRONMENT_SPEC"
        assert env_data["source_feat_ref"] == "FEAT-001"
        assert env_data["execution_modality"] == "api"

    def test_e2e_chain_env_with_separated_urls(self, tmp_path):
        env_path, env_config = provision_environment(
            workspace_root=tmp_path,
            proto_ref="PROTO-001",
            app_url="http://localhost:3000",
            api_url="http://localhost:8000",
            modality="web_e2e",
            browser="chromium",
            timeout=30000,
            feat_assumptions=None,
        )

        assert env_path.exists()

        with open(env_path, encoding="utf-8") as f:
            env_data = yaml.safe_load(f)

        assert env_data["source_proto_ref"] == "PROTO-001"
        assert env_data["app_base_url"] == "http://localhost:3000"
        assert env_data["api_base_url"] == "http://localhost:8000"
        assert env_data["browser"] == "chromium"
        assert env_data["execution_modality"] == "web_e2e"

    def test_environments_directory_created(self, tmp_path):
        env_path, _ = provision_environment(
            workspace_root=tmp_path,
            feat_ref="FEAT-001",
            modality="api",
            browser="chromium",
            timeout=30000,
            feat_assumptions=None,
        )

        env_dir = tmp_path / "ssot" / "environments"
        assert env_dir.exists()
        assert env_dir.is_dir()

    def test_gitkeep_exists(self, tmp_path):
        provision_environment(
            workspace_root=tmp_path,
            feat_ref="FEAT-001",
            modality="api",
            browser="chromium",
            timeout=30000,
            feat_assumptions=None,
        )

        gitkeep = tmp_path / "ssot" / "environments" / ".gitkeep"
        assert gitkeep.exists()

    def test_generated_at_timestamp(self, tmp_path):
        env_path, _ = provision_environment(
            workspace_root=tmp_path,
            feat_ref="FEAT-001",
            modality="api",
            browser="chromium",
            timeout=30000,
            feat_assumptions=None,
        )

        with open(env_path, encoding="utf-8") as f:
            env_data = yaml.safe_load(f)

        assert "generated_at" in env_data
        # Verify it's a valid ISO timestamp (ends with Z)
        assert env_data["generated_at"].endswith("Z")