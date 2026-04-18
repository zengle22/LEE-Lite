"""FRZ schema validation — dataclass definitions + YAML validators.

Truth source: ADR-050 §3 (FRZ definition, MSC 5 dimensions) + ADR-045.
FRZ packages must conform to these schemas before entering frozen state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import CommandError


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class FRZStatus(str, Enum):
    """Lifecycle states for an FRZ package."""

    draft = "draft"
    freeze_ready = "freeze_ready"
    frozen = "frozen"
    blocked = "blocked"
    revised = "revised"
    superseded = "superseded"


# ---------------------------------------------------------------------------
# MSC dimension constants
# ---------------------------------------------------------------------------

MSC_DIMENSIONS = [
    "product_boundary",
    "core_journeys",
    "domain_model",
    "state_machine",
    "acceptance_contract",
]

# ID format patterns
FRZ_ID_PATTERN = re.compile(r"^FRZ-\d{3,}$")
JOURNEY_ID_PATTERN = re.compile(r"^JRN-\d{3,}$")
ENTITY_ID_PATTERN = re.compile(r"^ENT-\d{3,}$")
STATE_MACHINE_ID_PATTERN = re.compile(r"^SM-\d{3,}$")
UNKNOWN_ID_PATTERN = re.compile(r"^UNK-\d{3,}$")


# ---------------------------------------------------------------------------
# Sub-entity frozen dataclasses (ADR-050 §3.2.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProductBoundary:
    """Product scope definition."""

    in_scope: list[str]
    out_of_scope: list[str]


@dataclass(frozen=True)
class CoreJourney:
    """Core user journey definition."""

    id: str
    name: str
    steps: list[str]


@dataclass(frozen=True)
class DomainEntity:
    """Domain entity definition."""

    id: str
    name: str
    contract: dict[str, Any]


@dataclass(frozen=True)
class StateMachine:
    """State machine definition."""

    id: str
    name: str
    states: list[str]
    transitions: list[dict[str, Any]]


@dataclass(frozen=True)
class AcceptanceContract:
    """Acceptance criteria definition."""

    expected_outcomes: list[str]
    acceptance_impact: list[str]


@dataclass(frozen=True)
class KnownUnknown:
    """Unresolved item requiring owner and expiry."""

    id: str
    topic: str
    status: str = "open"
    owner: str | None = None
    expires_in: str = "2 cycles"


@dataclass(frozen=True)
class FRZEvidence:
    """Evidence source references."""

    source_refs: list[str]
    raw_path: str | None = None


# ---------------------------------------------------------------------------
# FRZPackage frozen dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FRZPackage:
    """FRZ freeze package with all 5 MSC dimension fields.

    ADR-050 §3.2.3: FRZ must contain product_boundary, core_journeys,
    domain_model, state_machine, and acceptance_contract.
    """

    artifact_type: str = "frz_package"
    frz_id: str | None = None
    version: str = "1.0"
    status: FRZStatus = FRZStatus.draft
    created_at: str | None = None
    frozen_at: str | None = None
    product_boundary: ProductBoundary | None = None
    core_journeys: list[CoreJourney] = field(default_factory=list)
    domain_model: list[DomainEntity] = field(default_factory=list)
    state_machine: list[StateMachine] = field(default_factory=list)
    acceptance_contract: AcceptanceContract | None = None
    constraints: list[str] = field(default_factory=list)
    derived_allowed: list[str] = field(default_factory=list)
    known_unknowns: list[KnownUnknown] = field(default_factory=list)
    enums: list[dict[str, Any]] = field(default_factory=list)
    evidence: FRZEvidence | None = None


# ---------------------------------------------------------------------------
# Error class
# ---------------------------------------------------------------------------


class FRZSchemaError(ValueError):
    """Raised when an FRZ asset file does not conform to its schema."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise FRZSchemaError(f"{label}: required field '{key}' is missing")


def _parse_frz_dict(data: dict) -> FRZPackage:
    """Convert a raw YAML dict to an FRZPackage instance.

    Recursively converts nested dicts to their respective frozen dataclass
    instances. Validates ID formats for FRZ ID and all sub-entity IDs.
    """
    # Validate FRZ ID format if present
    frz_id = data.get("frz_id")
    if frz_id is not None and not FRZ_ID_PATTERN.match(frz_id):
        raise FRZSchemaError(f"Invalid FRZ ID format: {frz_id}")

    # Parse status to enum
    status_raw = data.get("status", "draft")
    if isinstance(status_raw, str):
        try:
            status = FRZStatus(status_raw)
        except ValueError:
            raise FRZSchemaError(f"Invalid FRZ status: {status_raw}")
    elif isinstance(status_raw, FRZStatus):
        status = status_raw
    else:
        raise FRZSchemaError(f"Invalid FRZ status type: {type(status_raw)}")

    # Parse product_boundary
    product_boundary = None
    if data.get("product_boundary") is not None:
        pb = data["product_boundary"]
        if isinstance(pb, dict):
            product_boundary = ProductBoundary(
                in_scope=pb.get("in_scope") or [],
                out_of_scope=pb.get("out_of_scope") or [],
            )
        elif isinstance(pb, ProductBoundary):
            product_boundary = pb

    # Parse core_journeys
    core_journeys: list[CoreJourney] = []
    for item in data.get("core_journeys") or []:
        if isinstance(item, dict):
            cj_id = item.get("id", "")
            if not JOURNEY_ID_PATTERN.match(cj_id):
                raise FRZSchemaError(f"Invalid CoreJourney ID format: {cj_id}")
            core_journeys.append(
                CoreJourney(
                    id=cj_id,
                    name=item.get("name", ""),
                    steps=item.get("steps") or [],
                )
            )
        elif isinstance(item, CoreJourney):
            core_journeys.append(item)

    # Parse domain_model
    domain_model: list[DomainEntity] = []
    for item in data.get("domain_model") or []:
        if isinstance(item, dict):
            ent_id = item.get("id", "")
            if not ENTITY_ID_PATTERN.match(ent_id):
                raise FRZSchemaError(f"Invalid DomainEntity ID format: {ent_id}")
            domain_model.append(
                DomainEntity(
                    id=ent_id,
                    name=item.get("name", ""),
                    contract=item.get("contract") or {},
                )
            )
        elif isinstance(item, DomainEntity):
            domain_model.append(item)

    # Parse state_machine
    state_machine: list[StateMachine] = []
    for item in data.get("state_machine") or []:
        if isinstance(item, dict):
            sm_id = item.get("id", "")
            if not STATE_MACHINE_ID_PATTERN.match(sm_id):
                raise FRZSchemaError(f"Invalid StateMachine ID format: {sm_id}")
            state_machine.append(
                StateMachine(
                    id=sm_id,
                    name=item.get("name", ""),
                    states=item.get("states") or [],
                    transitions=item.get("transitions") or [],
                )
            )
        elif isinstance(item, StateMachine):
            state_machine.append(item)

    # Parse acceptance_contract
    acceptance_contract = None
    if data.get("acceptance_contract") is not None:
        ac = data["acceptance_contract"]
        if isinstance(ac, dict):
            acceptance_contract = AcceptanceContract(
                expected_outcomes=ac.get("expected_outcomes") or [],
                acceptance_impact=ac.get("acceptance_impact") or [],
            )
        elif isinstance(ac, AcceptanceContract):
            acceptance_contract = ac

    # Parse known_unknowns
    known_unknowns: list[KnownUnknown] = []
    for item in data.get("known_unknowns") or []:
        if isinstance(item, dict):
            ku_id = item.get("id", "")
            if not UNKNOWN_ID_PATTERN.match(ku_id):
                raise FRZSchemaError(f"Invalid KnownUnknown ID format: {ku_id}")
            known_unknowns.append(
                KnownUnknown(
                    id=ku_id,
                    topic=item.get("topic", ""),
                    status=item.get("status", "open"),
                    owner=item.get("owner"),
                    expires_in=item.get("expires_in", "2 cycles"),
                )
            )
        elif isinstance(item, KnownUnknown):
            known_unknowns.append(item)

    # Parse evidence
    evidence = None
    if data.get("evidence") is not None:
        ev = data["evidence"]
        if isinstance(ev, dict):
            evidence = FRZEvidence(
                source_refs=ev.get("source_refs") or [],
                raw_path=ev.get("raw_path"),
            )
        elif isinstance(ev, FRZEvidence):
            evidence = ev

    return FRZPackage(
        artifact_type=data.get("artifact_type", "frz_package"),
        frz_id=frz_id,
        version=data.get("version", "1.0"),
        status=status,
        created_at=data.get("created_at"),
        frozen_at=data.get("frozen_at"),
        product_boundary=product_boundary,
        core_journeys=core_journeys,
        domain_model=domain_model,
        state_machine=state_machine,
        acceptance_contract=acceptance_contract,
        constraints=data.get("constraints") or [],
        derived_allowed=data.get("derived_allowed") or [],
        known_unknowns=known_unknowns,
        enums=data.get("enums") or [],
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# YAML loading helper
# ---------------------------------------------------------------------------

_FRZ_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "frz"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# MSCValidator
# ---------------------------------------------------------------------------


class MSCValidator:
    """Validates FRZ packages against MSC (Minimum Semantic Completeness) rules.

    ADR-050 §3.3: FRZ must pass MSC validation on all 5 dimensions before
    entering frozen state.
    """

    @staticmethod
    def validate(pkg: FRZPackage) -> dict[str, Any]:
        """Check all 5 MSC dimensions for minimum content.

        Args:
            pkg: FRZPackage instance to validate.

        Returns:
            Dict with keys: frz_id, msc_valid (bool), present (list),
            missing (list), status ("frozen" or "blocked").
        """
        present: list[str] = []
        missing: list[str] = []

        # product_boundary: at least 1 item in in_scope OR out_of_scope
        if pkg.product_boundary is not None and (
            len(pkg.product_boundary.in_scope) > 0
            or len(pkg.product_boundary.out_of_scope) > 0
        ):
            present.append("product_boundary")
        else:
            missing.append("product_boundary")

        # core_journeys: >= 1 journey with >= 2 steps
        has_valid_journey = any(
            len(j.steps) >= 2 for j in pkg.core_journeys
        )
        if has_valid_journey:
            present.append("core_journeys")
        else:
            missing.append("core_journeys")

        # domain_model: >= 1 entity with non-empty contract dict
        has_valid_entity = any(
            len(e.contract) > 0 for e in pkg.domain_model
        )
        if has_valid_entity:
            present.append("domain_model")
        else:
            missing.append("domain_model")

        # state_machine: >= 1 machine with >= 2 states
        has_valid_sm = any(
            len(sm.states) >= 2 for sm in pkg.state_machine
        )
        if has_valid_sm:
            present.append("state_machine")
        else:
            missing.append("state_machine")

        # acceptance_contract: >= 1 expected_outcome
        if pkg.acceptance_contract is not None and (
            len(pkg.acceptance_contract.expected_outcomes) > 0
        ):
            present.append("acceptance_contract")
        else:
            missing.append("acceptance_contract")

        msc_valid = len(missing) == 0
        status = "frozen" if msc_valid else "blocked"

        return {
            "frz_id": pkg.frz_id,
            "msc_valid": msc_valid,
            "present": present,
            "missing": missing,
            "status": status,
        }

    @staticmethod
    def validate_file(path: str | Path) -> dict[str, Any]:
        """Load a YAML file, parse to FRZPackage, and validate.

        Args:
            path: Path to the FRZ YAML file.

        Returns:
            Validation result dict from validate().

        Raises:
            FileNotFoundError: If the file does not exist.
            FRZSchemaError: If the file cannot be parsed or is invalid.
            yaml.YAMLError: If the YAML is malformed.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"FRZ file not found: {p}")

        data = _load_yaml(p)
        if not data:
            raise FRZSchemaError(f"FRZ file is empty or contains no valid data: {p}")

        # Extract the frz_package content if present as top-level key
        inner = data.get("frz_package", data)
        pkg = _parse_frz_dict(inner)
        return MSCValidator.validate(pkg)


# ---------------------------------------------------------------------------
# File-level validation entry point
# ---------------------------------------------------------------------------

_VALIDATORS = {
    "frz": ("frz_package", _parse_frz_dict),
}


def validate_file(path: str | Path, schema_type: str | None = None) -> FRZPackage:
    """Load a YAML file and validate it as an FRZ package.

    Args:
        path: Path to the YAML file.
        schema_type: 'frz' or None for auto-detect.

    Returns:
        The validated FRZPackage instance.

    Raises:
        FRZSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"FRZ file not found: {p}")

    data = _load_yaml(p)

    if schema_type is None:
        schema_type = _detect_schema_type(data)
        if schema_type is None:
            raise FRZSchemaError(
                f"Cannot detect FRZ schema from {p}. "
                f"Expected top-level key: frz_package"
            )

    if schema_type != "frz":
        raise FRZSchemaError(
            f"Unknown schema type '{schema_type}'. Must be 'frz'."
        )

    top_key, parser_fn = _VALIDATORS[schema_type]

    if top_key not in data:
        raise FRZSchemaError(
            f"Expected top-level key '{top_key}' in {p}. "
            f"File may not be a valid FRZ package."
        )

    return parser_fn(data[top_key])


def _detect_schema_type(data: dict) -> str | None:
    for stype, (top_key, _) in _VALIDATORS.items():
        if top_key in data:
            return stype
    return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Validate one or more FRZ YAML files from the command line.

    Usage:
        python -m cli.lib.frz_schema <file1.yaml> [file2.yaml ...]
        python -m cli.lib.frz_schema --type frz <file.yaml>
    """
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.frz_schema [--type <type>] <file.yaml> ...")
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
            result = MSCValidator.validate_file(f)
            if result["msc_valid"]:
                print(f"  OK: {f}")
            else:
                print(f"FAIL: {f} — missing MSC dimensions: {result['missing']}")
                exit_code = 1
        except (FRZSchemaError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:  # noqa: BLE001
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
