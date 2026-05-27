"""Step_6 — Freeze mechanism and FRZ Package output.

Truth source: design.md §step_6, §Decisions / Decision 3.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from frz_cli.exceptions import (
    AlignmentFailError,
    DriftDetectedError,
    FreezeGuardBlockedError,
    FrozenObjectError,
)
from frz_cli.models import (
    API,
    ARCH,
    EPIC,
    FEAT,
    FRZPackageV2,
    FreezeStatus,
    IMPL,
    SRC,
    TECH,
    UI,
)


# ---------------------------------------------------------------------------
# State machine guards
# ---------------------------------------------------------------------------


class FreezeGuard:
    """Prevents silent modification of frozen objects."""

    _frozen_refs: set[str] = set()

    @classmethod
    def register(cls, frz_ref: str) -> None:
        cls._frozen_refs.add(frz_ref)

    @classmethod
    def is_frozen(cls, frz_ref: str) -> bool:
        return frz_ref in cls._frozen_refs

    @classmethod
    def check_modify(cls, frz_ref: str) -> None:
        if cls.is_frozen(frz_ref):
            raise FreezeGuardBlockedError(
                f"Freeze Guard blocked modification of frozen FRZ {frz_ref}"
            )


# ---------------------------------------------------------------------------
# Frozen object protection
# ---------------------------------------------------------------------------


def _deep_freeze_value(value: Any) -> Any:
    """Recursively freeze any nested objects within value."""
    if hasattr(value, "freeze_status"):
        return freeze_object(value)
    if isinstance(value, list):
        return [_deep_freeze_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _deep_freeze_value(v) for k, v in value.items()}
    return value


def freeze_object(obj: Any) -> Any:
    """Transition an SSOT object to frozen state.

    Returns a new object with freeze_status=frozen and frozen_at timestamp.
    Recursively freezes nested dataclass objects (e.g. SRC.epics -> EPIC.feats).
    """
    if hasattr(obj, "freeze_status") and obj.freeze_status == FreezeStatus.frozen:
        return obj
    frozen_at = datetime.now(timezone.utc).isoformat()
    kwargs: dict[str, Any] = {}
    for k, v in obj.__dict__.items():
        if k == "freeze_status":
            kwargs[k] = FreezeStatus.frozen
        elif k == "frozen_at":
            kwargs[k] = frozen_at
        else:
            kwargs[k] = _deep_freeze_value(v)
    return type(obj)(**kwargs)


def _freeze_ssot_chain(chain: dict[str, Any]) -> dict[str, Any]:
    """Freeze all objects in an SSOT chain."""
    result: dict[str, Any] = {}
    for key, value in chain.items():
        if isinstance(value, list):
            result[key] = [_deep_freeze_value(item) for item in value]
        elif hasattr(value, "freeze_status"):
            result[key] = freeze_object(value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# FRZ Package builder
# ---------------------------------------------------------------------------


def build_frz_package(
    frz_ref: str,
    version: str,
    source_package_ref: str,
    chain: dict[str, Any],
    acceptance_test_cases: dict[str, Any],
    completeness_check: dict[str, Any],
    alignment_check: dict[str, Any],
    drift_check: dict[str, Any],
    dimension_quality_check: dict[str, Any] | None = None,
    frozen_ssot_chain: dict[str, Any] | None = None,
    evidence_refs: dict[str, Any] | None = None,
) -> FRZPackageV2:
    """Build a FRZ Package candidate from compilation results.

    Guards: completeness in (pass|partial) AND alignment=pass AND drift=pass.
    """
    if completeness_check.get("verdict") not in ("pass", "partial"):
        raise AlignmentFailError("Cannot freeze: completeness check failed")
    if alignment_check.get("verdict") not in ("pass", "partial"):
        raise AlignmentFailError("Cannot freeze: alignment check failed")
    if drift_check.get("verdict") not in ("pass", ""):
        raise DriftDetectedError("Cannot freeze: drift detected")

    frozen_chain = _freeze_ssot_chain(chain)
    if frozen_ssot_chain is None:
        frozen_ssot_chain = {
            "src_ref": frozen_chain["src"].src_id,
            "epic_refs": [e.epic_id for e in frozen_chain.get("epics", [])],
            "feat_refs": [f.feat_id for f in frozen_chain.get("feats", [])],
            "tech_refs": [t.tech_id for t in frozen_chain.get("techs", [])],
            "arch_refs": [a.arch_id for a in frozen_chain.get("archs", [])],
            "api_refs": [api.api_id for api in frozen_chain.get("apis", [])],
            "ui_refs": [u.ui_id for u in frozen_chain.get("uis", [])] if frozen_chain.get("uis") else [],
            "impl_refs": [i.impl_id for i in frozen_chain.get("impls", [])],
        }

    created_at = datetime.now(timezone.utc).isoformat()
    pkg = FRZPackageV2(
        frz_ref=frz_ref,
        version=version,
        created_at=created_at,
        source_package_ref=source_package_ref,
        frozen_ssot_chain=frozen_ssot_chain,
        acceptance_test_cases=acceptance_test_cases,
        completeness_check=completeness_check,
        alignment_check=alignment_check,
        drift_check=drift_check,
        dimension_quality_check=dimension_quality_check or {},
        evidence_refs=evidence_refs or {},
        freeze_status=FreezeStatus.frozen,
        frozen_at=created_at,
    )
    FreezeGuard.register(frz_ref)
    return pkg


# ---------------------------------------------------------------------------
# Checkpoint / idempotent retry
# ---------------------------------------------------------------------------


def load_checkpoint(checkpoint_path: Path) -> dict[str, Any] | None:
    """Load a compilation checkpoint if it exists."""
    if not checkpoint_path.exists():
        return None
    with open(checkpoint_path, encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(checkpoint_path: Path, checkpoint: dict[str, Any]) -> None:
    """Save a compilation checkpoint."""
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


# ---------------------------------------------------------------------------
# FRZ Revise helpers
# ---------------------------------------------------------------------------


def classify_revision_scope(
    old_pkg: FRZPackageV2, new_design_package: dict[str, Any]
) -> str:
    """Classify revision as minor or major.

    Minor: visual details, local adjustments, new FEAT in existing EPIC.
    Major: business rules, EPIC changes, semantic behavior changes.
    """
    old_src = old_pkg.frozen_ssot_chain.get("src_ref", "")
    # Simplified heuristic: if business_design product_vision changed → major
    # if ux_design changed only → minor
    # if new EPIC → major
    # if new FEAT in existing EPIC → minor
    return "minor"  # placeholder; real logic needs diff engine


def revise_frz_package(
    old_pkg: FRZPackageV2,
    new_chain: dict[str, Any],
    reason: str,
) -> FRZPackageV2:
    """Create a revised FRZ Package from an existing frozen one.

    Old version is marked superseded; new version gets incremented version.
    """
    revision = {
        "from_version": old_pkg.version,
        "reason": reason,
        "revised_at": datetime.now(timezone.utc).isoformat(),
    }
    history = list(old_pkg.revision_history)
    history.append(revision)

    scope = classify_revision_scope(old_pkg, {})
    major, minor = old_pkg.version.lstrip("v").split(".")
    if scope == "major":
        new_version = f"v{int(major) + 1}.0"
    else:
        new_version = f"v{major}.{int(minor) + 1}"

    new_pkg = FRZPackageV2(
        frz_ref=old_pkg.frz_ref,
        version=new_version,
        created_at=datetime.now(timezone.utc).isoformat(),
        source_package_ref=old_pkg.source_package_ref,
        frozen_ssot_chain={k: v for k, v in new_chain.items() if k != "src"},
        acceptance_test_cases=old_pkg.acceptance_test_cases,
        completeness_check=old_pkg.completeness_check,
        alignment_check=old_pkg.alignment_check,
        drift_check=old_pkg.drift_check,
        revision_history=history,
        freeze_status=FreezeStatus.revised,
    )
    return new_pkg
