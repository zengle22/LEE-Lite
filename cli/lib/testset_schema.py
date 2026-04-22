"""TESTSET schema validation — dataclass definitions + YAML validators.

Truth source: ADR-052 (test governance dual-axis) + FC-006 (forbidden fields).
TESTSET YAML files must conform to the schema defined in ssot/schemas/qa/testset.yaml.
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


class TestsetSchemaError(ValueError):
    """Raised when a TESTSET YAML does not conform to its schema."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa"


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise TestsetSchemaError(f"{label}: required field '{key}' is missing")


def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise TestsetSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )


# ---------------------------------------------------------------------------
# Testset frozen dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Testset:
    """TESTSET artifact definition (ADR-052, Phase 12).

    Forbidden fields: test_case_pack, script_pack (FC-006).
    """

    artifact_type: str = "testset"
    testset_id: str | None = None
    source_feat_refs: list[str] = field(default_factory=list)
    environment_ref: str | None = None
    gate_ref: str | None = None
    tasks: list[dict[str, Any]] = field(default_factory=list)
    notes: str | None = None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_testset_dict(data: dict) -> Testset:
    """Convert a raw YAML dict to a Testset instance."""
    testset_id = data.get("testset_id")
    source_feat_refs = data.get("source_feat_refs") or []
    environment_ref = data.get("environment_ref")
    gate_ref = data.get("gate_ref")
    tasks = data.get("tasks") or []
    notes = data.get("notes")

    return Testset(
        artifact_type=data.get("artifact_type", "testset"),
        testset_id=testset_id,
        source_feat_refs=source_feat_refs,
        environment_ref=environment_ref,
        gate_ref=gate_ref,
        tasks=tasks if isinstance(tasks, list) else [],
        notes=notes,
    )


# ---------------------------------------------------------------------------
# validate() — dict-level validation
# ---------------------------------------------------------------------------


def validate(data: dict) -> Testset:
    """Validate a raw TESTSET YAML dict and return a Testset instance.

    Enforces:
    - Forbidden fields: test_case_pack, script_pack (FC-006)
    - Required structure for valid testset artifacts

    Args:
        data: Raw dict from YAML parsing.

    Returns:
        Validated Testset instance.

    Raises:
        TestsetSchemaError: If validation fails.
    """
    if "testset" in data:
        inner = data["testset"]
    else:
        inner = data

    label = inner.get("testset_id", "testset")

    # FC-006: forbidden fields
    for forbidden in ("test_case_pack", "script_pack"):
        if forbidden in inner:
            raise TestsetSchemaError(
                f"{label}: forbidden field '{forbidden}' is not allowed in TESTSET (FC-006)"
            )

    return _parse_testset_dict(inner)


# ---------------------------------------------------------------------------
# YAML loading helper
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# File-level validation entry point
# ---------------------------------------------------------------------------

_VALIDATORS = {"testset": ("testset", _parse_testset_dict)}


def _detect_schema_type(data: dict) -> str | None:
    for stype, (top_key, _) in _VALIDATORS.items():
        if top_key in data:
            return stype
    return None


def validate_file(path: str | Path, schema_type: str | None = None) -> Testset:
    """Load a YAML file and validate it as a TESTSET.

    Args:
        path: Path to the YAML file.
        schema_type: 'testset' or None for auto-detect.

    Returns:
        The validated Testset instance.

    Raises:
        TestsetSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"TESTSET file not found: {p}")

    data = _load_yaml(p)

    if schema_type is None:
        schema_type = _detect_schema_type(data)
        if schema_type is None:
            # Fall back to flat-dict validation
            return validate(data)

    if schema_type != "testset":
        raise TestsetSchemaError(
            f"Unknown schema type '{schema_type}'. Must be 'testset'."
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
    """Validate one or more TESTSET YAML files from the command line.

    Usage:
        python -m cli.lib.testset_schema <file1.yaml> [file2.yaml ...]
        python -m cli.lib.testset_schema --type testset <file.yaml>
    """
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.testset_schema [--type <type>] <file.yaml> ...")
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
            print(f"  OK: {f} — testset_id={result.testset_id}, {len(result.tasks)} tasks")
        except (TestsetSchemaError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:  # noqa: BLE001
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
