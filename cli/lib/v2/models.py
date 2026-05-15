"""SSOT v2 data models.

All dataclasses are frozen (immutable) per project coding style.
Truth source: design.md §Data Model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FreezeStatus(str, Enum):
    """Lifecycle states for SSOT objects."""

    draft = "draft"
    frozen = "frozen"
    revised = "revised"
    superseded = "superseded"


# ---------------------------------------------------------------------------
# Base mixin fields (not a real mixin — included explicitly for frozen=True)
# ---------------------------------------------------------------------------

SSOT_BASE_FIELDS = {"format_version", "source_refs", "freeze_status"}

# ---------------------------------------------------------------------------
# SRC (container)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SRC:
    """Top-level source container."""

    src_id: str
    title: str
    version: str
    problem_domain: str
    business_goal: str
    target_users: list[str]
    triggering_scenarios: list[str]
    scope_boundaries: list[str]
    non_goals: list[str]
    global_constraints: list[str]
    open_questions: list[str] = field(default_factory=list)
    epics: list[EPIC] = field(default_factory=list)
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# EPIC (SRC chapter)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EPIC:
    """Capability chapter within SRC."""

    epic_id: str
    capability_name: str
    user_value: str
    business_closure: str
    priority: str
    included_scenarios: list[str]
    excluded_scenarios: list[str] = field(default_factory=list)
    acceptance_theme: str = ""
    cross_axis_refs: dict[str, list[str]] = field(default_factory=dict)
    feats: list[FEAT] = field(default_factory=list)
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# FEAT (EPIC chapter)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FEAT:
    """Acceptance slice chapter within EPIC."""

    feat_id: str
    title: str
    user_value: str
    trigger: str
    main_flow: list[str]
    acceptance_criteria: list[str]
    alternative_flows: list[str] = field(default_factory=list)
    state_changes: list[str] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    exception_flows: list[str] = field(default_factory=list)
    uat_scenarios: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    cross_axis_refs: dict[str, list[str]] = field(default_factory=dict)
    gsd_phase_hint: dict[str, Any] = field(default_factory=dict)
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# TECH
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TECH:
    """Technical design object."""

    tech_id: str
    tech_stack: dict[str, Any]
    sync_async: dict[str, Any]
    non_functional: dict[str, Any]
    constraints: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    feat_ref: str = ""
    src_ref: str = ""
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# ARCH
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ARCH:
    """Architecture design object."""

    arch_id: str
    layering: dict[str, Any]
    data_flow: dict[str, Any]
    storage: dict[str, Any]
    integration: dict[str, Any]
    target_architecture: str = ""
    frozen_contracts: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    feat_ref: str = ""
    src_ref: str = ""
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class API:
    """API contract object."""

    api_id: str
    endpoints: list[dict[str, Any]]
    sequence_diagrams: list[dict[str, Any]] = field(default_factory=list)
    version_strategy: str = "semver"
    feat_ref: str = ""
    src_ref: str = ""
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UI:
    """UI design object."""

    ui_id: str
    design_principles: list[str]
    interaction_flow: dict[str, Any]
    state_expression: dict[str, Any]
    design_tokens: dict[str, Any]
    copy_style: dict[str, Any]
    platform_strategy: dict[str, Any]
    error_state_ux: dict[str, Any]
    prototype: str = ""
    feat_ref: str = ""
    src_ref: str = ""
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# IMPL
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IMPL:
    """Self-contained implementation task package."""

    impl_id: str
    requirement_context: dict[str, Any]
    tech_context: dict[str, Any]
    arch_context: dict[str, Any]
    api_context: dict[str, Any]
    allowed_scope: dict[str, list[str]]
    forbidden_scope: dict[str, list[str]] = field(default_factory=dict)
    test_guidance: dict[str, Any] = field(default_factory=dict)
    feat_ref: str = ""
    src_ref: str = ""
    format_version: str = "2.0"
    source_refs: list[str] = field(default_factory=list)
    freeze_status: FreezeStatus = FreezeStatus.draft


# ---------------------------------------------------------------------------
# FRZ Package
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FRZPackageV2:
    """Frozen SSOT chain package (v2 format).

    Physical file view: references to SSOT objects via refs, not inline.
    """

    frz_ref: str
    version: str
    created_at: str
    source_package_ref: str
    frozen_ssot_chain: dict[str, Any]
    acceptance_test_cases: dict[str, Any] = field(default_factory=dict)
    completeness_check: dict[str, Any] = field(default_factory=dict)
    alignment_check: dict[str, Any] = field(default_factory=dict)
    drift_check: dict[str, Any] = field(default_factory=dict)
    dimension_quality_check: dict[str, Any] = field(default_factory=dict)
    evidence_refs: dict[str, Any] = field(default_factory=dict)
    revision_history: list[dict[str, Any]] = field(default_factory=list)
    format_version: str = "2.0"
    freeze_status: FreezeStatus = FreezeStatus.draft
    frozen_at: str | None = None


# ---------------------------------------------------------------------------
# Design Package input structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompletenessVerdict:
    """Output of step_1 completeness check."""

    verdict: str  # pass | blocked | partial
    missing_items: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AlignmentVerdict:
    """Output of step_3 alignment check."""

    verdict: str  # pass | fail
    issues: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class DriftVerdict:
    """Output of step_4 drift detection."""

    verdict: str  # pass | drift_found
    drift_items: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class VerificationReport:
    """Output of impl-verify step_5."""

    final_verdict: str  # pass | fail | conditional_pass
    verdict_reason: str = ""
    blocking_issues: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    conditions: list[dict[str, Any]] = field(default_factory=list)
    task_completion: dict[str, Any] = field(default_factory=dict)
    scope_compliance: dict[str, Any] = field(default_factory=dict)
    engineering_docs: dict[str, Any] = field(default_factory=dict)
    traceability: dict[str, Any] = field(default_factory=dict)
    unauthorized_features: list[dict[str, Any]] = field(default_factory=list)
    semantic_changes: list[dict[str, Any]] = field(default_factory=list)
    convergence: dict[str, Any] = field(default_factory=dict)
    feedback_items: list[dict[str, Any]] = field(default_factory=list)
