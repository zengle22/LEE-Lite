"""Unit tests for cli.lib.run_manifest_gen."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cli.lib.run_manifest_gen import (
    RUN_ARTIFACTS_DIR,
    generate_run_manifest,
    get_run_id_from_manifest_path,
    list_run_manifests,
    load_run_manifest,
)


class TestGenerateRunManifest:
    """Tests for generate_run_manifest()."""

    def test_generates_unique_run_manifest(self, tmp_path: Path) -> None:
        """Verify manifest file is created with correct path."""
        run_id = "e2e.test-001"
        manifest_path = generate_run_manifest(
            tmp_path, run_id, app_url="http://localhost:3000"
        )
        assert manifest_path.exists()
        assert manifest_path.name == "run-manifest.yaml"
        assert run_id in str(manifest_path)

    def test_manifest_contains_git_sha(self, tmp_path: Path) -> None:
        """Verify git_sha field is present (may be 'unknown' in isolated env)."""
        manifest_path = generate_run_manifest(
            tmp_path, "e2e.test-git-sha", app_url="http://localhost:3000"
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert "git_sha" in data
        assert isinstance(data["git_sha"], str)

    def test_manifest_contains_build_versions(self, tmp_path: Path) -> None:
        """Verify frontend_build and backend_build fields are present."""
        manifest_path = generate_run_manifest(
            tmp_path, "e2e.test-build-versions", app_url="http://localhost:3000"
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert "frontend_build" in data
        assert "backend_build" in data
        assert isinstance(data["frontend_build"], str)
        assert isinstance(data["backend_build"], str)

    def test_manifest_contains_base_urls(self, tmp_path: Path) -> None:
        """Verify base_url.app and base_url.api match input parameters."""
        manifest_path = generate_run_manifest(
            tmp_path,
            "e2e.test-base-urls",
            app_url="http://localhost:3000",
            api_url="http://localhost:8000",
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert "base_url" in data
        assert data["base_url"]["app"] == "http://localhost:3000"
        assert data["base_url"]["api"] == "http://localhost:8000"

    def test_manifest_contains_browser(self, tmp_path: Path) -> None:
        """Verify browser field matches input (default 'chromium')."""
        manifest_path = generate_run_manifest(
            tmp_path, "e2e.test-browser", app_url="http://localhost:3000"
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert data["browser"] == "chromium"

    def test_manifest_browser_custom_value(self, tmp_path: Path) -> None:
        """Verify browser field accepts custom browser value."""
        manifest_path = generate_run_manifest(
            tmp_path,
            "e2e.test-browser-custom",
            app_url="http://localhost:3000",
            browser="firefox",
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert data["browser"] == "firefox"

    def test_manifest_contains_accounts_empty_by_default(self, tmp_path: Path) -> None:
        """Verify accounts field defaults to empty list when not provided."""
        manifest_path = generate_run_manifest(
            tmp_path, "e2e.test-accounts-empty", app_url="http://localhost:3000"
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert "accounts" in data
        assert data["accounts"] == []

    def test_manifest_contains_accounts_when_provided(self, tmp_path: Path) -> None:
        """Verify accounts field matches input list when provided."""
        accounts = ["alice@example.com", "bob@example.com"]
        manifest_path = generate_run_manifest(
            tmp_path,
            "e2e.test-accounts-provided",
            app_url="http://localhost:3000",
            accounts=accounts,
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert data["accounts"] == accounts

    def test_manifest_run_id_format(self, tmp_path: Path) -> None:
        """Verify run_id_format field is the expected format string."""
        manifest_path = generate_run_manifest(
            tmp_path, "e2e.test-run-id-format", app_url="http://localhost:3000"
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert data["run_id_format"] == "e2e.run-{timestamp}-{random}"

    def test_manifest_created_at_is_iso8601(self, tmp_path: Path) -> None:
        """Verify created_at field is a valid ISO8601 timestamp."""
        from datetime import datetime, timezone

        manifest_path = generate_run_manifest(
            tmp_path, "e2e.test-created-at", app_url="http://localhost:3000"
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert "created_at" in data
        # Should parse without error (may end in Z or +00:00)
        ts = data["created_at"]
        # Allow both Z-suffix and +00:00 suffix
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        datetime.fromisoformat(ts)  # raises if invalid

    def test_manifest_artifact_version(self, tmp_path: Path) -> None:
        """Verify artifact_version is '1.0'."""
        manifest_path = generate_run_manifest(
            tmp_path, "e2e.test-artifact-version", app_url="http://localhost:3000"
        )
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert data["artifact_version"] == "1.0"

    def test_stored_under_correct_directory(self, tmp_path: Path) -> None:
        """Verify manifest is stored in ssot/tests/.artifacts/runs/{run_id}/."""
        run_id = "e2e.test-dir-structure"
        manifest_path = generate_run_manifest(
            tmp_path, run_id, app_url="http://localhost:3000"
        )
        expected = tmp_path / RUN_ARTIFACTS_DIR / run_id / "run-manifest.yaml"
        assert manifest_path == expected

    def test_rejects_path_traversal_run_id(self, tmp_path: Path) -> None:
        """Per T-18-01: reject run_id containing '../'."""
        with pytest.raises(ValueError, match="invalid path characters"):
            generate_run_manifest(
                tmp_path, "../evil", app_url="http://localhost:3000"
            )

    def test_rejects_forward_slash_in_run_id(self, tmp_path: Path) -> None:
        """Per T-18-01: reject run_id containing '/'."""
        with pytest.raises(ValueError, match="invalid path characters"):
            generate_run_manifest(
                tmp_path, "evil/thing", app_url="http://localhost:3000"
            )

    def test_append_only_raises_on_existing(self, tmp_path: Path) -> None:
        """Per D-02: raising FileExistsError if manifest already exists."""
        generate_run_manifest(
            tmp_path, "e2e.test-append-only", app_url="http://localhost:3000"
        )
        with pytest.raises(FileExistsError, match="append-only"):
            generate_run_manifest(
                tmp_path, "e2e.test-append-only", app_url="http://localhost:3000"
            )


class TestLoadRunManifest:
    """Tests for load_run_manifest()."""

    def test_load_existing_manifest(self, tmp_path: Path) -> None:
        """Generate manifest then load and verify fields match."""
        generate_run_manifest(
            tmp_path,
            "e2e.test-load-existing",
            app_url="http://localhost:3000",
            api_url="http://localhost:8000",
            browser="chromium",
            accounts=["alice@example.com"],
        )
        data = load_run_manifest(tmp_path, "e2e.test-load-existing")
        assert data["run_id"] == "e2e.test-load-existing"
        assert data["base_url"]["app"] == "http://localhost:3000"
        assert data["base_url"]["api"] == "http://localhost:8000"
        assert data["browser"] == "chromium"
        assert data["accounts"] == ["alice@example.com"]

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        """Verify FileNotFoundError for invalid run_id."""
        with pytest.raises(FileNotFoundError):
            load_run_manifest(tmp_path, "e2e.nonexistent")

    def test_load_rejects_invalid_run_id(self, tmp_path: Path) -> None:
        """Per T-18-01: reject path traversal in run_id during load."""
        with pytest.raises(ValueError, match="invalid path characters"):
            load_run_manifest(tmp_path, "../forbidden")


class TestGetRunIdFromManifestPath:
    """Tests for get_run_id_from_manifest_path()."""

    def test_extracts_run_id(self) -> None:
        """Verify run_id is correctly extracted from manifest path."""
        path = Path(
            "/workspace/ssot/tests/.artifacts/runs/e2e.run-20260424-ABC12345/run-manifest.yaml"
        )
        assert get_run_id_from_manifest_path(path) == "e2e.run-20260424-ABC12345"

    def test_returns_none_for_invalid_path(self) -> None:
        """Verify None is returned when path does not contain runs/ segment."""
        assert get_run_id_from_manifest_path(Path("/other/path/manifest.yaml")) is None

    def test_returns_none_for_traversal_attempt(self) -> None:
        """Verify None is returned for path with traversal."""
        path = Path("/workspace/ssot/tests/.artifacts/runs/../etc/passwd")
        assert get_run_id_from_manifest_path(path) is None


class TestListRunManifests:
    """Tests for list_run_manifests()."""

    def test_lists_all_run_ids(self, tmp_path: Path) -> None:
        """Generate 3 manifests, verify list_run_manifests returns all 3."""
        run_ids = ["e2e.run-001", "e2e.run-002", "e2e.run-003"]
        for rid in run_ids:
            generate_run_manifest(tmp_path, rid, app_url="http://localhost:3000")
        found = list_run_manifests(tmp_path)
        assert found == sorted(run_ids)

    def test_returns_empty_for_empty_directory(self, tmp_path: Path) -> None:
        """Verify empty list when no runs exist."""
        assert list_run_manifests(tmp_path) == []

    def test_ignores_directories_without_manifest(self, tmp_path: Path) -> None:
        """Verify directories without run-manifest.yaml are ignored."""
        runs_dir = tmp_path / RUN_ARTIFACTS_DIR
        runs_dir.mkdir(parents=True)
        (runs_dir / "no-manifest").mkdir()
        (runs_dir / "e2e.valid").mkdir()
        (runs_dir / "e2e.valid" / "run-manifest.yaml").write_text("{}", encoding="utf-8")
        found = list_run_manifests(tmp_path)
        assert found == ["e2e.valid"]
