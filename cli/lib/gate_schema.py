"""Gate schema validation — dataclass definitions + YAML validators.

Truth source: ADR-052 (test governance dual-axis), Phase 12.
Gate verdict YAML schema with 4-verdict enum.
Allowed verdicts: pass, conditional_pass, fail, provisional_pass.
Forbidden fields: hidden_verifier_failure.
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


class GateSchemaError(ValueError):
    """Raised when a Gate YAML does not conform to its schema."""


# ---------------------------------------------------------------------------
# Gate verdict enum (4 values, Phase 12)
# ---------------------------------------------------------------------------


class GateVerdict(str, Enum):
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"
    PROVISIONAL_PASS = "provisional_pass"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa"


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise GateSchemaError(f"{label}: required field '{key}' is missing")


def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise GateSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )


# ---------------------------------------------------------------------------
# Gate frozen dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Gate:
    """Gate verdict definition (ADR-052, Phase 12).

    Verdict must be one of: pass, conditional_pass, fail, provisional_pass.
    Forbidden: hidden_verifier_failure.
    """

    artifact_type: str = "gate"
    gate_id: str | None = None
    verdict: GateVerdict | None = None
    feature_id: str | None = None
    evaluated_at: str | None = None
    reason: str | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_gate_dict(data: dict) -> Gate:
    """Convert a raw YAML dict to a Gate instance."""
    gate_id = data.get("gate_id")
    feature_id = data.get("feature_id")
    evaluated_at = data.get("evaluated_at")
    reason = data.get("reason")
    notes = data.get("notes")

    # Parse verdict to enum
    verdict_raw = data.get("verdict")
    verdict = None
    if verdict_raw is not None:
        if isinstance(verdict_raw, str):
            try:
                verdict = GateVerdict(verdict_raw)
            except ValueError:
                raise GateSchemaError(
                    f"Gate '{gate_id or 'gate'}': verdict must be one of "
                    f"{[e.value for e in GateVerdict]}, got '{verdict_raw}'"
                )
        elif isinstance(verdict_raw, GateVerdict):
            verdict = verdict_raw

    return Gate(
        artifact_type=data.get("artifact_type", "gate"),
        gate_id=gate_id,
        verdict=verdict,
        feature_id=feature_id,
        evaluated_at=evaluated_at,
        reason=reason,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# validate() — dict-level validation
# ---------------------------------------------------------------------------


def validate(data: dict) -> Gate:
    """Validate a raw Gate YAML dict and return a Gate instance.

    Enforces:
    - Required field: verdict
    - Verdict must be one of: pass, conditional_pass, fail, provisional_pass
    - Forbidden field: hidden_verifier_failure

    Args:
        data: Raw dict from YAML parsing.

    Returns:
        Validated Gate instance.

    Raises:
        GateSchemaError: If validation fails.
    """
    if "gate" in data:
        inner = data["gate"]
    else:
        inner = data

    label = inner.get("gate_id", "gate")

    # Forbidden field
    if "hidden_verifier_failure" in inner:
        raise GateSchemaError(
            f"{label}: forbidden field 'hidden_verifier_failure' is not allowed in Gate"
        )

    # Required field
    _require(inner, "verdict", label)

    # Verdict enum check
    if isinstance(inner["verdict"], str):
        _enum_check(inner["verdict"], GateVerdict, label, "verdict")

    return _parse_gate_dict(inner)


# ---------------------------------------------------------------------------
# YAML loading helper
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# File-level validation entry point
# ---------------------------------------------------------------------------

_VALIDATORS = {"gate": ("gate", _parse_gate_dict)}


def _detect_schema_type(data: dict) -> str | None:
    for stype, (top_key, _) in _VALIDATORS.items():
        if top_key in data:
            return stype
    return None


def validate_file(path: str | Path, schema_type: str | None = None) -> Gate:
    """Load a YAML file and validate it as a Gate.

    Args:
        path: Path to the YAML file.
        schema_type: 'gate' or None for auto-detect.

    Returns:
        The validated Gate instance.

    Raises:
        GateSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Gate file not found: {p}")

    data = _load_yaml(p)

    if schema_type is None:
        schema_type = _detect_schema_type(data)
        if schema_type is None:
            # Fall back to flat-dict validation
            return validate(data)

    if schema_type != "gate":
        raise GateSchemaError(
            f"Unknown schema type '{schema_type}'. Must be 'gate'."
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
    """Validate one or more Gate YAML files from the command line.

    Usage:
        python -m cli.lib.gate_schema <file1.yaml> [file2.yaml ...]
        python -m cli.lib.gate_schema --type gate <file.yaml>
    """
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.gate_schema [--type <type>] <file.yaml> ...")
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
            print(f"  OK: {f} — gate_id={result.gate_id}, verdict={result.verdict}")
        except (GateSchemaError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:  # noqa: BLE001
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
