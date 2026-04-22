"""Tests for cli.lib.environment_schema."""

import pytest

from cli.lib.environment_schema import (
    Browser,
    Environment,
    EnvironmentSchemaError,
    validate,
    validate_file,
)


class TestValidate:
    def test_valid_minimal_dict(self):
        data = {
            "env_id": "ENV-001",
            "base_url": "http://localhost:3000",
            "browser": "chromium",
            "timeout": 30000,
            "headless": True,
        }
        result = validate(data)
        assert result.env_id == "ENV-001"
        assert result.base_url == "http://localhost:3000"
        assert result.browser == Browser.CHROMIUM
        assert result.timeout == 30000
        assert result.headless is True

    def test_valid_all_fields(self):
        data = {
            "env_id": "ENV-002",
            "base_url": "https://example.com",
            "browser": "firefox",
            "timeout": 60000,
            "headless": False,
            "viewport": {"width": 1920, "height": 1080},
            "notes": "production env",
        }
        result = validate(data)
        assert result.browser == Browser.FIREFOX
        assert result.headless is False
        assert result.viewport == {"width": 1920, "height": 1080}

    def test_wrapped_in_environment_key(self):
        data = {"environment": {"env_id": "ENV-003", "base_url": "http://x", "browser": "chromium", "timeout": 1000, "headless": True}}
        result = validate(data)
        assert result.env_id == "ENV-003"

    def test_missing_base_url(self):
        with pytest.raises(EnvironmentSchemaError, match="required field 'base_url'"):
            validate({"env_id": "ENV-BAD", "browser": "chromium", "timeout": 1000, "headless": True})

    def test_missing_browser(self):
        with pytest.raises(EnvironmentSchemaError, match="required field 'browser'"):
            validate({"env_id": "ENV-BAD", "base_url": "http://x", "timeout": 1000, "headless": True})

    def test_missing_timeout(self):
        with pytest.raises(EnvironmentSchemaError, match="required field 'timeout'"):
            validate({"env_id": "ENV-BAD", "base_url": "http://x", "browser": "chromium", "headless": True})

    def test_missing_headless(self):
        with pytest.raises(EnvironmentSchemaError, match="required field 'headless'"):
            validate({"env_id": "ENV-BAD", "base_url": "http://x", "browser": "chromium", "timeout": 1000})

    def test_forbidden_embedded_in_testset(self):
        data = {
            "env_id": "ENV-BAD",
            "base_url": "http://x",
            "browser": "chromium",
            "timeout": 1000,
            "headless": True,
            "embedded_in_testset": True,
        }
        with pytest.raises(EnvironmentSchemaError, match="forbidden field 'embedded_in_testset'"):
            validate(data)

    def test_invalid_browser_value(self):
        data = {
            "env_id": "ENV-BAD",
            "base_url": "http://x",
            "browser": "safari",
            "timeout": 1000,
            "headless": True,
        }
        with pytest.raises(EnvironmentSchemaError, match="browser must be one of"):
            validate(data)

    def test_timeout_not_number(self):
        data = {
            "env_id": "ENV-BAD",
            "base_url": "http://x",
            "browser": "chromium",
            "timeout": "fast",
            "headless": True,
        }
        with pytest.raises(EnvironmentSchemaError, match="timeout must be a number"):
            validate(data)

    def test_headless_not_bool(self):
        data = {
            "env_id": "ENV-BAD",
            "base_url": "http://x",
            "browser": "chromium",
            "timeout": 1000,
            "headless": "yes",
        }
        with pytest.raises(EnvironmentSchemaError, match="headless must be a boolean"):
            validate(data)


class TestValidateFile:
    def test_valid_yaml_file(self, tmp_path):
        f = tmp_path / "env.yaml"
        f.write_text("env_id: ENV-FILE\nbase_url: http://x\nbrowser: chromium\ntimeout: 1000\nheadless: true\n")
        result = validate_file(str(f))
        assert result.env_id == "ENV-FILE"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            validate_file("/nonexistent/file.yaml")

    def test_forbidden_field_in_file(self, tmp_path):
        f = tmp_path / "bad.yaml"
        f.write_text("env_id: ENV-BAD\nbase_url: http://x\nbrowser: chromium\ntimeout: 1000\nheadless: true\nembedded_in_testset: true\n")
        with pytest.raises(EnvironmentSchemaError, match="forbidden field 'embedded_in_testset'"):
            validate_file(str(f))

    def test_auto_detect_schema_type(self, tmp_path):
        f = tmp_path / "detect.yaml"
        f.write_text("environment:\n  env_id: ENV-AUTO\n  base_url: http://x\n  browser: chromium\n  timeout: 1000\n  headless: true\n")
        result = validate_file(str(f))
        assert result.env_id == "ENV-AUTO"


class TestEnvironmentDataclass:
    def test_defaults(self):
        e = Environment()
        assert e.artifact_type == "environment"
        assert e.env_id is None
        assert e.base_url == ""
        assert e.browser is None
        assert e.timeout == 30000
        assert e.headless is True
        assert e.viewport is None
        assert e.notes is None

    def test_frozen(self):
        e = Environment(env_id="ENV-F")
        with pytest.raises(Exception):
            e.env_id = "CHANGED"


class TestBrowserEnum:
    def test_values(self):
        assert Browser.CHROMIUM.value == "chromium"
        assert Browser.FIREFOX.value == "firefox"
        assert Browser.WEBKIT.value == "webkit"
