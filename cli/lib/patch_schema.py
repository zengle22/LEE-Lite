"""Patch schema definitions for the Experience Patch Layer (ADR-049)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class PatchStatus(str, Enum):
    """Lifecycle states for an experience patch."""

    draft = "draft"
    proposed = "proposed"
    approved = "approved"
    applied = "applied"
    rejected = "rejected"
    superseded = "superseded"


class ChangeClass(str, Enum):
    """Classification of the change type."""

    ui_flow = "ui_flow"
    copy_text = "copy_text"
    validation = "validation"
    navigation = "navigation"
    layout = "layout"
    interaction = "interaction"
    performance = "performance"
    accessibility = "accessibility"
    error_handling = "error_handling"
    data_display = "data_display"
    visual = "visual"          # NEW: top-level tri-class value (ADR-050)
    semantic = "semantic"      # NEW: top-level tri-class value (ADR-050)
    other = "other"


class GradeLevel(str, Enum):
    """Two-tier change grading: Minor (Patch-level) vs Major (FRZ re-freeze)."""

    MINOR = "minor"
    MAJOR = "major"


CHANGE_CLASS_TO_GRADE: dict[str, GradeLevel] = {
    # visual sub-classes -> Minor
    ChangeClass.ui_flow.value: GradeLevel.MINOR,
    ChangeClass.copy_text.value: GradeLevel.MINOR,
    ChangeClass.layout.value: GradeLevel.MINOR,
    ChangeClass.navigation.value: GradeLevel.MINOR,
    ChangeClass.data_display.value: GradeLevel.MINOR,
    ChangeClass.accessibility.value: GradeLevel.MINOR,
    ChangeClass.visual.value: GradeLevel.MINOR,
    # interaction -> Minor
    ChangeClass.interaction.value: GradeLevel.MINOR,
    # error_handling, performance, validation -> Minor (UI-layer only)
    ChangeClass.error_handling.value: GradeLevel.MINOR,
    ChangeClass.performance.value: GradeLevel.MINOR,
    ChangeClass.validation.value: GradeLevel.MINOR,
    # semantic -> Major (triggers FRZ re-freeze)
    ChangeClass.semantic.value: GradeLevel.MAJOR,
    # other -> default Minor, human can escalate
    ChangeClass.other.value: GradeLevel.MINOR,
}


def derive_grade(change_class: str) -> GradeLevel:
    """Derive grade level from change_class deterministically.

    Fail-safe default: if change_class is missing/invalid, return MAJOR with warning.
    This is safer than MINOR -- an unknown classification should escalate to human review.
    """
    import warnings
    grade = CHANGE_CLASS_TO_GRADE.get(change_class)
    if grade is None:
        warnings.warn(
            f"Unknown change_class '{change_class}', defaulting to MAJOR for safety. "
            "Add this value to CHANGE_CLASS_TO_GRADE in patch_schema.py."
        )
        return GradeLevel.MAJOR
    return grade


# ---------------------------------------------------------------------------
# Patch dataclasses (ADR-049 §2.4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PatchSource:
    """Origin metadata for an experience patch."""

    actor: str
    session: str | None = None
    prompt_ref: str | None = None
    ai_suggested_class: str | None = None
    human_confirmed_class: str | None = None
    reviewed_at: str | None = None  # ISO 8601, when test_impact was human-reviewed (D-21)


@dataclass(frozen=True)
class PatchScope:
    """Scope of the patch within the product."""

    feat_ref: str
    page: str | None = None
    module: str | None = None


@dataclass(frozen=True)
class PatchTestImpact:
    """Test impact analysis for an experience patch."""

    impacts_user_path: bool = False
    impacts_acceptance: bool = False
    affected_routes: list[str] = field(default_factory=list)
    test_changes_required: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PatchImplementation:
    """Details about what files the patch changes."""

    changed_files: list[str] = field(default_factory=list)
    description: str | None = None


class PatchProblem(str, Enum):
    """Classification of issues found in a patch."""

    none = "none"
    conflict = "conflict"
    regression = "regression"
    incomplete = "incomplete"


class PatchDecision(str, Enum):
    """Human decision on a patch."""

    approved = "approved"
    rejected = "rejected"
    needs_revision = "needs_revision"
    superseded = "superseded"


@dataclass(frozen=True)
class PatchConflictDetails:
    """Details about a conflict between patches."""

    conflicting_patch_id: str
    overlapping_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PatchResolution:
    """Record of how a patch was resolved."""

    decision: str | None = None
    notes: str | None = None
    src_created: str | None = None


class PatchSchemaError(ValueError):
    """Raised when a Patch YAML does not conform to its schema."""


_PATCH_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa"


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise PatchSchemaError(f"{label}: required field '{key}' is missing")


def validate_patch(data: dict) -> dict:
    """Validate a raw Patch YAML dict and return the validated data.

    Enforces:
    - interaction/semantic patches must have test_impact with affected_routes (D-04)
    - reviewed_at >= created_at if both present (D-21)
    """
    label = data.get("id", "patch")

    # Required top-level fields
    _require(data, "id", label)
    _require(data, "type", label)
    _require(data, "status", label)
    _require(data, "change_class", label)
    _require(data, "created_at", label)

    # Validate change_class
    valid_classes = [e.value for e in ChangeClass]
    if data["change_class"] not in valid_classes:
        raise PatchSchemaError(
            f"{label}: change_class must be one of {valid_classes}, got '{data['change_class']}'"
        )

    # Validate status
    valid_statuses = [e.value for e in PatchStatus]
    if data["status"] not in valid_statuses:
        raise PatchSchemaError(
            f"{label}: status must be one of {valid_statuses}, got '{data['status']}'"
        )

    # Source sub-fields
    src = data.get("source", {})
    _require(src, "actor", f"{label}.source")

    # D-04: interaction/semantic must have test_impact
    if data["change_class"] in ("interaction", "semantic"):
        if not data.get("test_impact"):
            raise PatchSchemaError(
                f"{label}: missing test_impact for {data['change_class']} patch"
            )
        ti = data["test_impact"]
        if not isinstance(ti, dict) or not ti.get("affected_routes"):
            raise PatchSchemaError(
                f"{label}: missing test_impact.affected_routes for {data['change_class']} patch"
            )

    # D-21: reviewed_at must be >= created_at
    reviewed_at = src.get("reviewed_at")
    if reviewed_at is not None:
        from datetime import datetime

        created_dt = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        reviewed_dt = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
        if reviewed_dt < created_dt:
            raise PatchSchemaError(
                f"{label}: reviewed_at ({reviewed_at}) must be >= created_at ({data['created_at']})"
            )

    return data


def validate_file(path: str | Path, schema_type: str | None = None) -> Any:
    """Validate a Patch or QA asset YAML file.

    Args:
        path: Path to the YAML file.
        schema_type: 'patch', 'plan', 'manifest', 'spec', or 'settlement'.
                     If None, auto-detects from file content.

    Returns:
        The validated data.

    Raises:
        PatchSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Schema file not found: {p}")

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if schema_type is None:
        schema_type = _detect_schema_type(data)

    if schema_type == "patch":
        return validate_patch(data.get("experience_patch", data))

    # Delegate to QA schemas for other types
    from cli.lib.qa_schemas import validate_file as qa_validate_file

    return qa_validate_file(p, schema_type)


def _detect_schema_type(data: dict) -> str | None:
    if "experience_patch" in data:
        return "patch"
    # Try QA schema detection
    try:
        from cli.lib.qa_schemas import _detect_schema_type as qa_detect

        return qa_detect(data)
    except ImportError:
        return None
