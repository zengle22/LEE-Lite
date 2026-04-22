"""Environment schema validation — dataclass definitions + YAML validators.

Truth source: ADR-052 (test governance dual-axis), Phase 12.
Environment YAML files must conform to the schema defined in ssot/schemas/qa/environment.yaml.
Required fields: base_url, browser, timeout, headless.
Forbidden fields: embedded_in_testset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Error class
# ---------------------------------------------------------------------------


class EnvironmentSchemaError(ValueError):
    """Raised when an Environment YAML does not conform to its schema."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa"


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise EnvironmentSchemaError(f"{label}: required field '{key}' is missing")


def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise EnvironmentSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )


# ---------------------------------------------------------------------------
# Browser enum
# ---------------------------------------------------------------------------


class Browser(str, Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


# ---------------------------------------------------------------------------
# Environment frozen dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Environment:
    """Test environment definition (ADR-052, Phase 12).

    Required: base_url, browser, timeout, headless.
    Forbidden: embedded_in_testset.
    """

    artifact_type: str = "environment"
    env_id: str | None = None
    base_url: str = ""
    browser: Browser | None = None
    timeout: int = 30000
    headless: bool = True
    viewport: dict[str, int] | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_environment_dict(data: dict) -> Environment:
    """Convert a raw YAML dict to an Environment instance."""
    env_id = data.get("env_id")
    base_url = data.get("base_url", "")
    timeout = data.get("timeout", 30000)
    headless = data.get("headless", True)
    viewport = data.get("viewport")
    notes = data.get("notes")

    # Parse browser to enum
    browser_raw = data.get("browser")
    browser = None
    if browser_raw is not None:
        if isinstance(browser_raw, str):
            try:
                browser = Browser(browser_raw)
            except ValueError:
                raise EnvironmentSchemaError(
                    f"Environment '{env_id or 'env'}': browser must be one of "
                    f"{[e.value for e in Browser]}, got '{browser_raw}'"
                )
        elif isinstance(browser_raw, Browser):
            browser = browser_raw

    return Environment(
        artifact_type=data.get("artifact_type", "environment"),
        env_id=env_id,
        base_url=base_url,
        browser=browser,
        timeout=int(timeout),
        headless=bool(headless),
        viewport=viewport,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# validate() — dict-level validation
# ---------------------------------------------------------------------------


def validate(data: dict) -> Environment:
    """Validate a raw Environment YAML dict and return an Environment instance.

    Enforces:
    - Required fields: base_url, browser, timeout, headless
    - Forbidden field: embedded_in_testset
    - Type checks: timeout must be int, headless must be bool

    Args:
        data: Raw dict from YAML parsing.

    Returns:
        Validated Environment instance.

    Raises:
        EnvironmentSchemaError: If validation fails.
    """
    if "environment" in data:
        inner = data["environment"]
    else:
        inner = data

    label = inner.get("env_id", "environment")

    # Forbidden field
    if "embedded_in_testset" in inner:
        raise EnvironmentSchemaError(
            f"{label}: forbidden field 'embedded_in_testset' is not allowed in Environment"
        )

    # Required fields
    _require(inner, "base_url", label)
    _require(inner, "browser", label)
    _require(inner, "timeout", label)
    _require(inner, "headless", label)

    # Browser enum check
    if isinstance(inner.get("browser"), str):
        _enum_check(inner["browser"], Browser, label, "browser")

    # Type checks
    if not isinstance(inner["timeout"], (int, float)):
        raise EnvironmentSchemaError(f"{label}: timeout must be a number, got {type(inner['timeout']).__name__}")
    if not isinstance(inner["headless"], bool):
        raise EnvironmentSchemaError(f"{label}: headless must be a boolean")

    return _parse_environment_dict(inner)


# ---------------------------------------------------------------------------
# YAML loading helper
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# File-level validation entry point
# ---------------------------------------------------------------------------

_VALIDATORS = {"environment": ("environment", _parse_environment_dict)}


def _detect_schema_type(data: dict) -> str | None:
    for stype, (top_key, _) in _VALIDATORS.items():
        if top_key in data:
            return stype
    return None


def validate_file(path: str | Path, schema_type: str | None = None) -> Environment:
    """Load a YAML file and validate it as an Environment.

    Args:
        path: Path to the YAML file.
        schema_type: 'environment' or None for auto-detect.

    Returns:
        The validated Environment instance.

    Raises:
        EnvironmentSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Environment file not found: {p}")

    data = _load_yaml(p)

    if schema_type is None:
        schema_type = _detect_schema_type(data)
        if schema_type is None:
            # Fall back to flat-dict validation
            return validate(data)

    if schema_type != "environment":
        raise EnvironmentSchemaError(
            f"Unknown schema type '{schema_type}'. Must be 'environment'."
        )

    top_key, parser_fn = _VALIDATORS[schema_type]

    if top_key not in data:
        # Flat form — delegate to validate()
        return validate(data)

    return validate(data)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Validate one or more Environment YAML files from the command line.

    Usage:
        python -m cli.lib.environment_schema <file1.yaml> [file2.yaml ...]
        python -m cli.lib.environment_schema --type environment <file.yaml>
    """
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.environment_schema [--type <type>] <file.yaml> ...")
        sys.exit(1)

    schema_type: str | None = None
    files: list[str] = []

    i = 0
    while i < len(args):
        if args[i] == "--type":
            i += 1
            if i >= len(args):
                print("Error: --type requires a value")
                sys.exit(1)
            schema_type = args[i]
        else:
            files.append(args[i])
        i += 1

    if not files:
        print("Error: no files specified")
        sys.exit(1)

    exit_code = 0
    for f in files:
        try:
            result = validate_file(f, schema_type)
            print(f"  OK: {f} — env_id={result.env_id}, browser={result.browser}")
        except (EnvironmentSchemaError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:  # noqa: BLE001
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
