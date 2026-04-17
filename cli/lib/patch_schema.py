"""Experience Patch schema validation — dataclass definitions + YAML validators.

Truth source: ADR-049 §5.3 (Patch YAML schema).
All experience patches must conform to these schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Enumerations (ADR-049 §5.3)
# ---------------------------------------------------------------------------


class PatchStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    VALIDATED = "validated"
    PENDING_BACKWRITE = "pending_backwrite"
    BACKWRITTEN = "backwritten"
    RETAIN_IN_CODE = "retain_in_code"
    UPGRADED_TO_SRC = "upgraded_to_src"
    SUPERSEDED = "superseded"
    DISCARDED = "discarded"
    ARCHIVED = "archived"


class ChangeClass(str, Enum):
    VISUAL = "visual"
    INTERACTION = "interaction"
    SEMANTIC = "semantic"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SourceActor(str, Enum):
    HUMAN = "human"
    AI_SUGGESTED = "ai_suggested"


class BackwriteStatus(str, Enum):
    PENDING = "pending"
    BACKWRITTEN = "backwritten"
    DISCARDED = "discarded"
    UPGRADED_TO_SRC = "upgraded_to_src"
    SUPERSEDED = "superseded"


# ---------------------------------------------------------------------------
# Nested dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PatchSource:
    _from: str
    actor: str
    session: str
    prompt_ref: str
    ai_suggested_class: str | None = None
    human_confirmed_class: str | None = None
    reviewed_at: str | None = None


@dataclass(frozen=True)
class PatchScope:
    feat_ref: str
    page: str
    module: str
    ui_ref: str | None = None
    tech_ref: str | None = None


@dataclass(frozen=True)
class PatchTestImpact:
    impacts_user_path: bool = False
    impacts_acceptance: bool = False
    impacts_existing_testcases: bool = False
    affected_routes: list[str] = field(default_factory=list)
    test_targets: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PatchProblem:
    user_issue: str | None = None
    evidence: str | None = None


@dataclass(frozen=True)
class PatchDecision:
    code_hotfix_allowed: bool = False
    must_backwrite_ssot: bool = False
    backwrite_targets: list[str] = field(default_factory=list)
    backwrite_deadline: str | None = None


@dataclass(frozen=True)
class PatchImplementation:
    code_changed: bool = False
    changed_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PatchConflictDetails:
    with_patch_id: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class PatchResolution:
    backwrite_status: str | None = None
    merged_into_ssot_at: str | None = None
    src_created: str | None = None
    closed_at: str | None = None


# ---------------------------------------------------------------------------
# Conflict resolution (D-13/D-14/D-16)
# ---------------------------------------------------------------------------


def _resolve_conflict_winner(patch_a: dict[str, Any], patch_b: dict[str, Any]) -> str:
    """Determine winner between two conflicting patches (D-16).

    Latest validated wins. Tie-break: larger patch_id sequence number.
    """
    def _seq(p: dict[str, Any]) -> int:
        pid = p.get("id", "UXPATCH-0000")
        try:
            return int(pid.split("-")[1])
        except (IndexError, ValueError):
            return 0

    status_a = patch_a.get("status", "")
    status_b = patch_b.get("status", "")

    # Validated beats non-validated
    if status_a == "validated" and status_b != "validated":
        return patch_a["id"]
    if status_b == "validated" and status_a != "validated":
        return patch_b["id"]

    # Tie-break: larger patch_id wins
    return patch_a["id"] if _seq(patch_a) > _seq(patch_b) else patch_b["id"]


def resolve_patch_conflicts(
    feat_dir: Path,
    patch_ids: list[str] | None = None,
    *,
    include_active: bool = True,
    include_validated: bool = True,
    include_pending: bool = False,
) -> list[dict[str, Any]]:
    """Unified conflict detection for experience patches (D-13, D-14).

    Replaces detect_conflicts() in patch_capture_runtime.py and
    detect_settlement_conflicts() in settle_runtime.py.

    Args:
        feat_dir: ssot/experience-patches/{FEAT-ID}/ directory
        patch_ids: If provided, only check these IDs
        include_active: Include 'active' status patches
        include_validated: Include 'validated' status patches
        include_pending: Include 'pending_backwrite' status patches
    """
    valid_statuses: set[str] = set()
    if include_active:
        valid_statuses.add("active")
    if include_validated:
        valid_statuses.add("validated")
    if include_pending:
        valid_statuses.add("pending_backwrite")

    patches: list[dict[str, Any]] = []
    for patch_file in sorted(feat_dir.glob("UXPATCH-*.yaml")):
        try:
            with open(patch_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            patch = data.get("experience_patch", data) if isinstance(data, dict) else {}
        except Exception:
            continue
        if patch.get("status") not in valid_statuses:
            continue
        if patch_ids and patch.get("id") not in patch_ids:
            continue
        patches.append(patch)

    conflicts: list[dict[str, Any]] = []
    for i in range(len(patches)):
        for j in range(i + 1, len(patches)):
            files_a = set(patches[i].get("implementation", {}).get("changed_files", []))
            files_b = set(patches[j].get("implementation", {}).get("changed_files", []))
            overlap = files_a & files_b
            if overlap:
                winner = _resolve_conflict_winner(patches[i], patches[j])
                conflicts.append({
                    "patch_a": patches[i]["id"],
                    "patch_b": patches[j]["id"],
                    "overlapping_files": sorted(overlap),
                    "winner": winner,
                    "resolution": "superseded" if winner != patches[i]["id"] else None,
                })
    return conflicts


# ---------------------------------------------------------------------------
# Root dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PatchExperience:
    id: str
    type: str
    status: str
    created_at: str
    updated_at: str
    title: str
    summary: str
    source: PatchSource
    scope: PatchScope
    change_class: str
    severity: str | None = None
    conflict: bool = False
    conflict_details: PatchConflictDetails | None = None
    problem: PatchProblem | None = None
    decision: PatchDecision | None = None
    implementation: PatchImplementation | None = None
    test_impact: PatchTestImpact | None = None
    related_ids: list[str] = field(default_factory=list)
    resolution: PatchResolution | None = None


# ---------------------------------------------------------------------------
# Error class
# ---------------------------------------------------------------------------


class PatchSchemaError(ValueError):
    """Raised when a patch asset file does not conform to its schema."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise PatchSchemaError(f"{label}: required field '{key}' is missing")


def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise PatchSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )


# ---------------------------------------------------------------------------
# validate_patch
# ---------------------------------------------------------------------------


def validate_patch(data: dict) -> PatchExperience:
    """Validate and return a PatchExperience from raw YAML dict."""
    label = "experience_patch"

    # Required top-level fields
    _require(data, "id", label)
    _require(data, "type", label)
    _require(data, "status", label)
    _require(data, "created_at", label)
    _require(data, "updated_at", label)
    _require(data, "title", label)
    _require(data, "summary", label)
    _require(data, "source", label)
    _require(data, "scope", label)
    _require(data, "change_class", label)

    # Enum checks
    _enum_check(data["status"], PatchStatus, label, "status")
    _enum_check(data["change_class"], ChangeClass, label, "change_class")

    # Severity (optional)
    severity = data.get("severity")
    if severity is not None:
        _enum_check(severity, Severity, label, "severity")

    # Source sub-fields
    src = data["source"]
    _require(src, "from", f"{label}.source")
    _require(src, "actor", f"{label}.source")
    _require(src, "session", f"{label}.source")
    _require(src, "prompt_ref", f"{label}.source")
    _require(src, "human_confirmed_class", f"{label}.source")

    _enum_check(src["actor"], SourceActor, f"{label}.source", "actor")
    _enum_check(src["human_confirmed_class"], ChangeClass, f"{label}.source", "human_confirmed_class")

    # D-21: reviewed_at timestamp (optional)
    reviewed_at = src.get("reviewed_at")

    # ai_suggested_class (optional within source)
    if src.get("ai_suggested_class") is not None:
        _enum_check(src["ai_suggested_class"], ChangeClass, f"{label}.source", "ai_suggested_class")

    # Scope sub-fields
    sc = data["scope"]
    _require(sc, "feat_ref", f"{label}.scope")
    _require(sc, "page", f"{label}.scope")
    _require(sc, "module", f"{label}.scope")

    # Optional objects
    conflict_details: PatchConflictDetails | None = None
    if data.get("conflict_details"):
        cd = data["conflict_details"]
        conflict_details = PatchConflictDetails(
            with_patch_id=cd.get("with_patch_id"),
            description=cd.get("description"),
        )

    problem: PatchProblem | None = None
    if data.get("problem"):
        pb = data["problem"]
        problem = PatchProblem(
            user_issue=pb.get("user_issue"),
            evidence=pb.get("evidence"),
        )

    decision: PatchDecision | None = None
    if data.get("decision"):
        dc = data["decision"]
        decision = PatchDecision(
            code_hotfix_allowed=dc.get("code_hotfix_allowed", False),
            must_backwrite_ssot=dc.get("must_backwrite_ssot", False),
            backwrite_targets=dc.get("backwrite_targets") or [],
            backwrite_deadline=dc.get("backwrite_deadline"),
        )

    implementation: PatchImplementation | None = None
    if data.get("implementation"):
        impl = data["implementation"]
        implementation = PatchImplementation(
            code_changed=impl.get("code_changed", False),
            changed_files=impl.get("changed_files") or [],
        )

    test_impact: PatchTestImpact | None = None
    if data.get("test_impact"):
        ti = data["test_impact"]
        test_impact = PatchTestImpact(
            impacts_user_path=ti.get("impacts_user_path", False),
            impacts_acceptance=ti.get("impacts_acceptance", False),
            impacts_existing_testcases=ti.get("impacts_existing_testcases", False),
            affected_routes=ti.get("affected_routes") or [],
            test_targets=ti.get("test_targets") or [],
        )

    # D-04/D-18: interaction/semantic patches require test_impact
    if data["change_class"] in ("interaction", "semantic"):
        if not test_impact:
            raise PatchSchemaError(
                f"{label}: {data['change_class']} patch requires test_impact field"
            )
        if not test_impact.affected_routes:
            raise PatchSchemaError(
                f"{label}: {data['change_class']} patch test_impact must include affected_routes"
            )

    # D-21: reviewed_at must be >= created_at
    if reviewed_at is not None:
        from datetime import datetime
        created_dt = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        reviewed_dt = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
        if reviewed_dt < created_dt:
            raise PatchSchemaError(
                f"{label}: reviewed_at ({reviewed_at}) must be >= created_at ({data['created_at']})"
            )

    resolution: PatchResolution | None = None
    if data.get("resolution"):
        res = data["resolution"]
        resolution = PatchResolution(
            backwrite_status=res.get("backwrite_status"),
            merged_into_ssot_at=res.get("merged_into_ssot_at"),
            src_created=res.get("src_created"),
            closed_at=res.get("closed_at"),
        )

    return PatchExperience(
        id=data["id"],
        type=data["type"],
        status=data["status"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        title=data["title"],
        summary=data["summary"],
        source=PatchSource(
            _from=src["from"],
            actor=src["actor"],
            session=src["session"],
            prompt_ref=src["prompt_ref"],
            ai_suggested_class=src.get("ai_suggested_class"),
            human_confirmed_class=src["human_confirmed_class"],
            reviewed_at=reviewed_at,
        ),
        scope=PatchScope(
            feat_ref=sc["feat_ref"],
            page=sc["page"],
            module=sc["module"],
            ui_ref=sc.get("ui_ref"),
            tech_ref=sc.get("tech_ref"),
        ),
        change_class=data["change_class"],
        severity=severity,
        conflict=data.get("conflict", False),
        conflict_details=conflict_details,
        problem=problem,
        decision=decision,
        implementation=implementation,
        test_impact=test_impact,
        related_ids=data.get("related_ids") or [],
        resolution=resolution,
    )


# ---------------------------------------------------------------------------
# YAML loading helpers
# ---------------------------------------------------------------------------

_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# File-level validation entry points
# ---------------------------------------------------------------------------

_VALIDATORS = {
    "plan": ("api_test_plan", None),  # from qa_schemas
    "manifest": ("api_coverage_manifest", None),
    "spec": ("api_test_spec", None),
    "settlement": ("settlement_report", None),
    "gate": ("gate_evaluation", None),
    "evidence": ("evidence_record", None),
    "e2e_spec": ("e2e_journey_spec", None),
    "patch": ("experience_patch", validate_patch),
}


def validate_file(path: str | Path, schema_type: str | None = None) -> Any:
    """Load a YAML file and validate it against the specified schema.

    Args:
        path: Path to the YAML file.
        schema_type: One of 'plan', 'manifest', 'spec', 'settlement', 'patch'.
                     If None, auto-detects from file content.

    Returns:
        The validated dataclass instance.

    Raises:
        PatchSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Schema file not found: {p}")

    data = _load_yaml(p)

    if schema_type is None:
        schema_type = _detect_schema_type(data)
        if schema_type is None:
            raise PatchSchemaError(
                f"Cannot detect schema type from {p}. "
                f"Expected one of top-level keys: {list(_VALIDATORS.keys())}"
            )

    if schema_type not in _VALIDATORS:
        raise PatchSchemaError(
            f"Unknown schema type '{schema_type}'. "
            f"Must be one of: {list(_VALIDATORS.keys())}"
        )

    top_key, validator_fn = _VALIDATORS[schema_type]

    if validator_fn is None:
        # Delegate to qa_schemas for non-patch types
        from cli.lib.qa_schemas import validate_file as _qa_validate_file
        return _qa_validate_file(path, schema_type)

    if top_key not in data:
        raise PatchSchemaError(
            f"Expected top-level key '{top_key}' in {p}. "
            f"File may not be a valid {schema_type} asset."
        )

    return validator_fn(data[top_key])


def _detect_schema_type(data: dict) -> str | None:
    for stype, (top_key, _) in _VALIDATORS.items():
        if top_key in data:
            return stype
    return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Validate one or more patch asset files from the command line.

    Usage:
        python -m cli.lib.patch_schema <file1.yaml> [file2.yaml ...]
        python -m cli.lib.patch_schema --type patch <file.yaml>
    """
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.patch_schema [--type <type>] <file.yaml> ...")
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
            validate_file(f, schema_type)
            print(f"  OK: {f}")
        except (PatchSchemaError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:  # noqa: BLE001
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
