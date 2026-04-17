"""QA schema validation — dataclass definitions + YAML validators.

Truth source: ADR-047 §4 (detailed design) + §15 (manifest state machine).
All 11 QA skills must produce/consume data conforming to these schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Enumerations (ADR-047 §15 A.1)
# ---------------------------------------------------------------------------


class LifecycleStatus(str, Enum):
    DRAFTED = "drafted"
    DESIGNED = "designed"
    GENERATED = "generated"
    EXECUTABLE = "executable"
    EXECUTED = "executed"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    WAIVED = "waived"


class MappingStatus(str, Enum):
    UNMAPPED = "unmapped"
    MAPPED = "mapped"
    SUPERSEDED = "superseded"


class EvidenceStatus(str, Enum):
    MISSING = "missing"
    PARTIAL = "partial"
    COMPLETE = "complete"


class WaiverStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class ScenarioType(str, Enum):
    HAPPY_PATH = "happy_path"
    VALIDATION = "validation"
    BOUNDARY = "boundary"
    PERMISSION = "permission"
    ERROR = "error"
    IDEMPOTENT = "idempotent"
    STATE_CONSTRAINT = "state_constraint"
    CONCURRENCY = "concurrency"
    DATA_SIDEEFFECT = "data_sideeffect"


class ChainType(str, Enum):
    API = "api"
    E2E = "e2e"


class VerdictConclusion(str, Enum):
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"


class ReleaseRecommendation(str, Enum):
    RELEASE = "release"
    CONDITIONAL_RELEASE = "conditional_release"
    BLOCK = "block"


class CapStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    UNCOVERED = "uncovered"


class GateResult(str, Enum):
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"


# ---------------------------------------------------------------------------
# Schema A: API Test Plan (ADR-047 §4.1.5 A)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CutRecord:
    capability: str
    dimension: str
    cut_reason: str
    source_ref: str
    approver: str | None = None
    approved_at: str | None = None


@dataclass(frozen=True)
class ApiObject:
    name: str
    capabilities: list[str]


@dataclass(frozen=True)
class Priorities:
    p0: list[str] = field(default_factory=list)
    p1: list[str] = field(default_factory=list)
    p2: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ApiTestPlan:
    feature_id: str
    source_feat_refs: list[str]
    api_objects: list[ApiObject]
    priorities: Priorities
    cut_records: list[CutRecord] = field(default_factory=list)
    notes: str | None = None


# ---------------------------------------------------------------------------
# Schema B: API Coverage Manifest (ADR-047 §4.1.5 B + §15)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ManifestItem:
    coverage_id: str
    feature_id: str
    capability: str
    endpoint: str
    scenario_type: str
    priority: str
    source_feat_ref: str
    dimensions_covered: list[str] = field(default_factory=list)
    mapped_case_ids: list[str] = field(default_factory=list)
    lifecycle_status: str = "designed"
    mapping_status: str = "unmapped"
    evidence_status: str = "missing"
    waiver_status: str = "none"
    evidence_refs: list[str] = field(default_factory=list)
    rerun_count: int = 0
    last_run_id: str | None = None
    obsolete: bool = False
    superseded_by: str | None = None
    patch_affected: bool = False
    patch_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ApiCoverageManifest:
    items: list[ManifestItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Schema C: API Test Spec (ADR-047 §4.1.5 C)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecRequest:
    method: str | None = None
    path_params: dict[str, Any] | None = None
    query_params: dict[str, Any] | None = None
    headers: dict[str, Any] | None = None
    body: dict[str, Any] | None = None


@dataclass(frozen=True)
class SpecExpected:
    status_code: int
    response_assertions: list[str] = field(default_factory=list)
    side_effect_assertions: list[str] = field(default_factory=list)
    response_schema: dict[str, Any] | None = None


@dataclass(frozen=True)
class ApiTestSpec:
    case_id: str
    coverage_id: str
    endpoint: str
    capability: str
    preconditions: list[str] = field(default_factory=list)
    request: SpecRequest | None = None
    expected: SpecExpected | None = None
    cleanup: list[str] = field(default_factory=list)
    evidence_required: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Schema E: Evidence Record (ADR-047 §6.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceRecord:
    case_id: str
    coverage_id: str
    executed_at: str
    run_id: str
    evidence: dict[str, Any]
    side_effects: list[str] = field(default_factory=list)
    execution_status: str = "success"


# ---------------------------------------------------------------------------
# Schema F: E2E Journey Spec (ADR-047 §4.2.5 C)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class E2EUserStep:
    step_number: int
    action: str
    target: str
    data: dict[str, Any] | None = None
    expected_result: str | None = None


@dataclass(frozen=True)
class E2EJourneySpec:
    case_id: str
    coverage_id: str
    journey_id: str
    entry_point: str
    preconditions: list[str] = field(default_factory=list)
    user_steps: list[E2EUserStep] = field(default_factory=list)
    expected_ui_states: list[dict[str, Any]] = field(default_factory=list)
    expected_network_events: list[dict[str, Any]] = field(default_factory=list)
    expected_persistence: list[dict[str, Any]] = field(default_factory=list)
    anti_false_pass_checks: list[str] = field(default_factory=list)
    evidence_required: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Schema D: Settlement Report (ADR-047 §10 + §9)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ByCapability:
    capability: str
    coverage_item_count: int
    mapped_count: int
    executed_count: int
    passed_count: int
    failed_count: int
    status: str


@dataclass(frozen=True)
class ByFeatureRef:
    feature_ref: str
    coverage_item_count: int
    passed_count: int
    failed_count: int
    uncovered_count: int


@dataclass(frozen=True)
class EvidenceCompleteness:
    total_evidence_required: int
    evidence_provided: int
    missing_evidence_count: int
    completeness_pct: float


@dataclass(frozen=True)
class GapEntry:
    coverage_id: str
    capability: str
    lifecycle_status: str
    failure_reason: str | None = None
    blocker_reason: str | None = None


@dataclass(frozen=True)
class WaiverEntry:
    coverage_id: str
    waiver_status: str
    waiver_reason: str | None = None
    approver: str | None = None
    approved_at: str | None = None


@dataclass(frozen=True)
class Verdict:
    conclusion: str
    release_recommendation: str
    notes: str | None = None


@dataclass(frozen=True)
class GateEvaluation:
    all_p0_mapped: bool
    all_p1_mapped: bool
    all_p0_executed: bool
    all_p1_executed: bool
    evidence_for_all_executed: bool
    unwaived_failed_count: int
    unwaived_blocked_count: int
    unwaived_p0_uncovered_count: int
    gate_result: str


@dataclass(frozen=True)
class Summary:
    total_capability_count: int
    total_coverage_item_count: int
    mapped_count: int
    generated_count: int
    executed_count: int
    passed_count: int
    failed_count: int
    blocked_count: int
    uncovered_count: int


@dataclass(frozen=True)
class SettlementReport:
    chain: str
    summary: Summary
    by_capability: list[ByCapability] = field(default_factory=list)
    by_feature_ref: list[ByFeatureRef] = field(default_factory=list)
    evidence_completeness: EvidenceCompleteness | None = None
    gap_list: list[GapEntry] = field(default_factory=list)
    waiver_list: list[WaiverEntry] = field(default_factory=list)
    verdict: Verdict | None = None
    gate_evaluation: GateEvaluation | None = None


# ---------------------------------------------------------------------------
# YAML loading helpers
# ---------------------------------------------------------------------------

_SCHEMA_DIR = Path(__file__).parent.parent.parent / "ssot" / "schemas" / "qa"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------


def _require(data: dict, key: str, label: str) -> None:
    if key not in data or data[key] is None:
        raise QaSchemaError(f"{label}: required field '{key}' is missing")


def _enum_check(value: str, enum_cls: type[Enum], label: str, field_name: str) -> None:
    valid = [e.value for e in enum_cls]
    if value not in valid:
        raise QaSchemaError(
            f"{label}: {field_name} must be one of {valid}, got '{value}'"
        )


class QaSchemaError(ValueError):
    """Raised when a QA asset file does not conform to its schema."""


def validate_plan(data: dict) -> ApiTestPlan:
    """Validate and return an ApiTestPlan from raw YAML dict."""
    label = "api_test_plan"
    _require(data, "feature_id", label)
    _require(data, "source_feat_refs", label)
    _require(data, "api_objects", label)
    _require(data, "priorities", label)

    # source_feat_refs must be non-empty list
    refs = data["source_feat_refs"]
    if not isinstance(refs, list) or len(refs) == 0:
        raise QaSchemaError(f"{label}: source_feat_refs must be a non-empty list")

    # api_objects
    api_objects: list[ApiObject] = []
    for i, obj in enumerate(data["api_objects"]):
        _require(obj, "name", f"{label}.api_objects[{i}]")
        _require(obj, "capabilities", f"{label}.api_objects[{i}]")
        if not isinstance(obj["capabilities"], list) or len(obj["capabilities"]) == 0:
            raise QaSchemaError(
                f"{label}.api_objects[{i}].capabilities must be a non-empty list"
            )
        api_objects.append(ApiObject(name=obj["name"], capabilities=obj["capabilities"]))

    # priorities
    pri = data["priorities"]
    priorities = Priorities(
        p0=pri.get("p0") or [],
        p1=pri.get("p1") or [],
        p2=pri.get("p2") or [],
    )
    if not priorities.p0 and not priorities.p1:
        raise QaSchemaError(f"{label}: at least one of priorities.p0 or p1 must be non-empty")

    # cut_records (optional)
    cut_records: list[CutRecord] = []
    for rec in data.get("cut_records") or []:
        _require(rec, "capability", f"{label}.cut_records")
        _require(rec, "dimension", f"{label}.cut_records")
        _require(rec, "cut_reason", f"{label}.cut_records")
        _require(rec, "source_ref", f"{label}.cut_records")
        cut_records.append(
            CutRecord(
                capability=rec["capability"],
                dimension=rec["dimension"],
                cut_reason=rec["cut_reason"],
                source_ref=rec["source_ref"],
                approver=rec.get("approver"),
                approved_at=rec.get("approved_at"),
            )
        )

    return ApiTestPlan(
        feature_id=data["feature_id"],
        source_feat_refs=refs,
        api_objects=api_objects,
        priorities=priorities,
        cut_records=cut_records,
        notes=data.get("notes"),
    )


def validate_manifest(data: dict) -> ApiCoverageManifest:
    """Validate and return an ApiCoverageManifest from raw YAML dict."""
    label = "api_coverage_manifest"
    items_raw = data.get("items") or []

    items: list[ManifestItem] = []
    for i, raw in enumerate(items_raw):
        _require(raw, "coverage_id", f"{label}.items[{i}]")
        _require(raw, "feature_id", f"{label}.items[{i}]")
        _require(raw, "capability", f"{label}.items[{i}]")
        _require(raw, "endpoint", f"{label}.items[{i}]")
        _require(raw, "scenario_type", f"{label}.items[{i}]")
        _require(raw, "priority", f"{label}.items[{i}]")
        _require(raw, "source_feat_ref", f"{label}.items[{i}]")

        _enum_check(raw["priority"], Priority, f"{label}.items[{i}]", "priority")
        _enum_check(
            raw.get("lifecycle_status", "designed"),
            LifecycleStatus,
            f"{label}.items[{i}]",
            "lifecycle_status",
        )
        _enum_check(
            raw.get("mapping_status", "unmapped"),
            MappingStatus,
            f"{label}.items[{i}]",
            "mapping_status",
        )
        _enum_check(
            raw.get("evidence_status", "missing"),
            EvidenceStatus,
            f"{label}.items[{i}]",
            "evidence_status",
        )
        _enum_check(
            raw.get("waiver_status", "none"),
            WaiverStatus,
            f"{label}.items[{i}]",
            "waiver_status",
        )

        items.append(
            ManifestItem(
                coverage_id=raw["coverage_id"],
                feature_id=raw["feature_id"],
                capability=raw["capability"],
                endpoint=raw["endpoint"],
                scenario_type=raw["scenario_type"],
                priority=raw["priority"],
                source_feat_ref=raw["source_feat_ref"],
                dimensions_covered=raw.get("dimensions_covered") or [],
                mapped_case_ids=raw.get("mapped_case_ids") or [],
                lifecycle_status=raw.get("lifecycle_status", "designed"),
                mapping_status=raw.get("mapping_status", "unmapped"),
                evidence_status=raw.get("evidence_status", "missing"),
                waiver_status=raw.get("waiver_status", "none"),
                evidence_refs=raw.get("evidence_refs") or [],
                rerun_count=raw.get("rerun_count", 0),
                last_run_id=raw.get("last_run_id"),
                obsolete=raw.get("obsolete", False),
                superseded_by=raw.get("superseded_by"),
                patch_affected=raw.get("patch_affected", False),
                patch_refs=raw.get("patch_refs") or [],
            )
        )

    return ApiCoverageManifest(items=items)


def validate_spec(data: dict) -> ApiTestSpec:
    """Validate and return an ApiTestSpec from raw YAML dict."""
    label = "api_test_spec"
    _require(data, "case_id", label)
    _require(data, "coverage_id", label)
    _require(data, "endpoint", label)
    _require(data, "capability", label)

    # request (optional but must be dict if present)
    request = None
    if data.get("request") is not None:
        req = data["request"]
        if not isinstance(req, dict):
            raise QaSchemaError(f"{label}: request must be a mapping")
        request = SpecRequest(
            method=req.get("method"),
            path_params=req.get("path_params"),
            query_params=req.get("query_params"),
            headers=req.get("headers"),
            body=req.get("body"),
        )

    # expected (required)
    _require(data, "expected", label)
    exp = data["expected"]
    _require(exp, "status_code", f"{label}.expected")
    if not isinstance(exp["status_code"], int):
        raise QaSchemaError(f"{label}.expected.status_code must be an integer")

    expected = SpecExpected(
        status_code=exp["status_code"],
        response_assertions=exp.get("response_assertions") or [],
        side_effect_assertions=exp.get("side_effect_assertions") or [],
        response_schema=exp.get("response_schema"),
    )

    return ApiTestSpec(
        case_id=data["case_id"],
        coverage_id=data["coverage_id"],
        endpoint=data["endpoint"],
        capability=data["capability"],
        preconditions=data.get("preconditions") or [],
        request=request,
        expected=expected,
        cleanup=data.get("cleanup") or [],
        evidence_required=data.get("evidence_required") or [],
    )


def validate_evidence(data: dict) -> EvidenceRecord:
    """Validate and return an EvidenceRecord from raw YAML dict."""
    label = "evidence_record"
    _require(data, "case_id", label)
    _require(data, "coverage_id", label)
    _require(data, "executed_at", label)
    _require(data, "run_id", label)
    _require(data, "evidence", label)
    _require(data, "execution_status", label)

    valid_statuses = {"success", "failed", "error", "simulated"}
    if data["execution_status"] not in valid_statuses:
        raise QaSchemaError(
            f"{label}: execution_status must be one of {valid_statuses}, "
            f"got '{data['execution_status']}'"
        )

    if not isinstance(data["evidence"], dict):
        raise QaSchemaError(f"{label}: evidence must be a mapping")

    return EvidenceRecord(
        case_id=data["case_id"],
        coverage_id=data["coverage_id"],
        executed_at=data["executed_at"],
        run_id=data["run_id"],
        evidence=data["evidence"],
        side_effects=data.get("side_effects") or [],
        execution_status=data["execution_status"],
    )


def validate_e2e_spec(data: dict) -> E2EJourneySpec:
    """Validate and return an E2EJourneySpec from raw YAML dict."""
    label = "e2e_journey_spec"
    _require(data, "case_id", label)
    _require(data, "coverage_id", label)
    _require(data, "journey_id", label)
    _require(data, "entry_point", label)

    # user_steps validation
    steps_raw = data.get("user_steps") or []
    if not isinstance(steps_raw, list) or len(steps_raw) == 0:
        raise QaSchemaError(f"{label}: user_steps must be a non-empty list")

    user_steps: list[E2EUserStep] = []
    for i, step in enumerate(steps_raw):
        _require(step, "step_number", f"{label}.user_steps[{i}]")
        _require(step, "action", f"{label}.user_steps[{i}]")
        _require(step, "target", f"{label}.user_steps[{i}]")
        user_steps.append(
            E2EUserStep(
                step_number=step["step_number"],
                action=step["action"],
                target=step["target"],
                data=step.get("data"),
                expected_result=step.get("expected_result"),
            )
        )

    return E2EJourneySpec(
        case_id=data["case_id"],
        coverage_id=data["coverage_id"],
        journey_id=data["journey_id"],
        entry_point=data["entry_point"],
        preconditions=data.get("preconditions") or [],
        user_steps=user_steps,
        expected_ui_states=data.get("expected_ui_states") or [],
        expected_network_events=data.get("expected_network_events") or [],
        expected_persistence=data.get("expected_persistence") or [],
        anti_false_pass_checks=data.get("anti_false_pass_checks") or [],
        evidence_required=data.get("evidence_required") or [],
    )


def validate_settlement(data: dict) -> SettlementReport:
    """Validate and return a SettlementReport from raw YAML dict."""
    label = "settlement_report"
    _require(data, "chain", label)
    _require(data, "summary", label)

    _enum_check(data["chain"], ChainType, label, "chain")

    # summary
    s = data["summary"]
    for key in (
        "total_capability_count",
        "total_coverage_item_count",
        "mapped_count",
        "generated_count",
        "executed_count",
        "passed_count",
        "failed_count",
        "blocked_count",
        "uncovered_count",
    ):
        _require(s, key, f"{label}.summary")
        if not isinstance(s[key], int):
            raise QaSchemaError(f"{label}.summary.{key} must be an integer")

    summary = Summary(**s)

    # by_capability (optional)
    by_cap: list[ByCapability] = []
    for bc in data.get("by_capability") or []:
        _require(bc, "capability", f"{label}.by_capability")
        _require(bc, "status", f"{label}.by_capability")
        _enum_check(bc["status"], CapStatus, f"{label}.by_capability", "status")
        by_cap.append(ByCapability(**bc))

    # by_feature_ref (optional)
    by_feat: list[ByFeatureRef] = []
    for bf in data.get("by_feature_ref") or []:
        _require(bf, "feature_ref", f"{label}.by_feature_ref")
        by_feat.append(ByFeatureRef(**bf))

    # evidence_completeness (optional)
    ec = None
    if data.get("evidence_completeness"):
        ec_raw = data["evidence_completeness"]
        _require(ec_raw, "total_evidence_required", f"{label}.evidence_completeness")
        _require(ec_raw, "evidence_provided", f"{label}.evidence_completeness")
        _require(ec_raw, "missing_evidence_count", f"{label}.evidence_completeness")
        _require(ec_raw, "completeness_pct", f"{label}.evidence_completeness")
        ec = EvidenceCompleteness(**ec_raw)

    # gap_list (optional)
    gaps: list[GapEntry] = []
    for g in data.get("gap_list") or []:
        _require(g, "coverage_id", f"{label}.gap_list")
        _require(g, "capability", f"{label}.gap_list")
        _require(g, "lifecycle_status", f"{label}.gap_list")
        gaps.append(GapEntry(**g))

    # waiver_list (optional)
    waivers: list[WaiverEntry] = []
    for w in data.get("waiver_list") or []:
        _require(w, "coverage_id", f"{label}.waiver_list")
        _require(w, "waiver_status", f"{label}.waiver_list")
        _enum_check(
            w["waiver_status"],
            WaiverStatus,
            f"{label}.waiver_list",
            "waiver_status",
        )
        waivers.append(WaiverEntry(**w))

    # verdict (optional)
    verdict = None
    if data.get("verdict"):
        v = data["verdict"]
        _require(v, "conclusion", f"{label}.verdict")
        _require(v, "release_recommendation", f"{label}.verdict")
        _enum_check(v["conclusion"], VerdictConclusion, f"{label}.verdict", "conclusion")
        _enum_check(
            v["release_recommendation"],
            ReleaseRecommendation,
            f"{label}.verdict",
            "release_recommendation",
        )
        verdict = Verdict(**v)

    # gate_evaluation (optional)
    gate = None
    if data.get("gate_evaluation"):
        g = data["gate_evaluation"]
        for key in (
            "all_p0_mapped",
            "all_p1_mapped",
            "all_p0_executed",
            "all_p1_executed",
            "evidence_for_all_executed",
        ):
            _require(g, key, f"{label}.gate_evaluation")
            if not isinstance(g[key], bool):
                raise QaSchemaError(f"{label}.gate_evaluation.{key} must be a boolean")
        _require(g, "gate_result", f"{label}.gate_evaluation")
        _enum_check(g["gate_result"], GateResult, f"{label}.gate_evaluation", "gate_result")
        gate = GateEvaluation(**g)

    return SettlementReport(
        chain=data["chain"],
        summary=summary,
        by_capability=by_cap,
        by_feature_ref=by_feat,
        evidence_completeness=ec,
        gap_list=gaps,
        waiver_list=waivers,
        verdict=verdict,
        gate_evaluation=gate,
    )


def validate_gate(data: dict) -> dict:
    """Validate a release gate input (release_gate_input.yaml) structure.

    Args:
        data: Raw YAML dict under the 'gate_evaluation' top-level key.

    Returns:
        The validated data dict.

    Raises:
        QaSchemaError: If the gate input does not conform to the expected structure.
    """
    label = "gate_evaluation"

    # Top-level required fields
    _require(data, "evaluated_at", label)
    _require(data, "feature_id", label)
    _require(data, "final_decision", label)
    _enum_check(data["final_decision"], GateResult, label, "final_decision")

    # api_chain (required)
    _require(data, "api_chain", label)
    api_chain = data["api_chain"]
    for key in ("total", "passed", "failed", "blocked", "uncovered"):
        _require(api_chain, key, f"{label}.api_chain")
        if not isinstance(api_chain[key], int):
            raise QaSchemaError(f"{label}.api_chain.{key} must be an integer")
    _require(api_chain, "pass_rate", f"{label}.api_chain")
    if not isinstance(api_chain["pass_rate"], (int, float)):
        raise QaSchemaError(f"{label}.api_chain.pass_rate must be a number")
    _require(api_chain, "evidence_status", f"{label}.api_chain")
    _enum_check(api_chain["evidence_status"], EvidenceStatus, f"{label}.api_chain", "evidence_status")

    # e2e_chain (required, same as api_chain plus exception_journeys_executed)
    _require(data, "e2e_chain", label)
    e2e_chain = data["e2e_chain"]
    for key in ("total", "passed", "failed", "blocked", "uncovered"):
        _require(e2e_chain, key, f"{label}.e2e_chain")
        if not isinstance(e2e_chain[key], int):
            raise QaSchemaError(f"{label}.e2e_chain.{key} must be an integer")
    _require(e2e_chain, "pass_rate", f"{label}.e2e_chain")
    if not isinstance(e2e_chain["pass_rate"], (int, float)):
        raise QaSchemaError(f"{label}.e2e_chain.pass_rate must be a number")
    _require(e2e_chain, "evidence_status", f"{label}.e2e_chain")
    _enum_check(e2e_chain["evidence_status"], EvidenceStatus, f"{label}.e2e_chain", "evidence_status")
    _require(e2e_chain, "exception_journeys_executed", f"{label}.e2e_chain")
    if not isinstance(e2e_chain["exception_journeys_executed"], int):
        raise QaSchemaError(f"{label}.e2e_chain.exception_journeys_executed must be an integer")

    # anti_laziness_checks (required, 7 booleans)
    _require(data, "anti_laziness_checks", label)
    alc = data["anti_laziness_checks"]
    for key in (
        "manifest_frozen",
        "cut_records_valid",
        "pending_waivers_counted",
        "evidence_consistent",
        "min_exception_coverage",
        "no_evidence_not_executed",
        "evidence_hash_binding",
    ):
        _require(alc, key, f"{label}.anti_laziness_checks")
        if not isinstance(alc[key], bool):
            raise QaSchemaError(f"{label}.anti_laziness_checks.{key} must be a boolean")

    # evidence_hash (required, 64-char lowercase hex)
    _require(data, "evidence_hash", label)
    import re
    if not re.match(r"^[a-f0-9]{64}$", data["evidence_hash"]):
        raise QaSchemaError(
            f"{label}.evidence_hash must be a 64-char lowercase hex string"
        )

    # decision_reason (required non-empty string)
    _require(data, "decision_reason", label)
    if not isinstance(data["decision_reason"], str) or not data["decision_reason"].strip():
        raise QaSchemaError(f"{label}.decision_reason must be a non-empty string")

    return data


# ---------------------------------------------------------------------------
# File-level validation entry points
# ---------------------------------------------------------------------------

_VALIDATORS = {
    "plan": ("api_test_plan", validate_plan),
    "manifest": ("api_coverage_manifest", validate_manifest),
    "spec": ("api_test_spec", validate_spec),
    "settlement": ("settlement_report", validate_settlement),
    "gate": ("gate_evaluation", validate_gate),
    "evidence": ("evidence_record", validate_evidence),
    "e2e_spec": ("e2e_journey_spec", validate_e2e_spec),
}


def validate_file(path: str | Path, schema_type: str | None = None) -> Any:
    """Load a YAML file and validate it against the specified schema.

    Args:
        path: Path to the YAML file.
        schema_type: One of 'plan', 'manifest', 'spec', 'settlement'.
                     If None, auto-detects from file content.

    Returns:
        The validated dataclass instance.

    Raises:
        QaSchemaError: If the file does not conform to the schema.
        FileNotFoundError: If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Schema file not found: {p}")

    data = _load_yaml(p)

    if schema_type is None:
        schema_type = _detect_schema_type(data)
        if schema_type is None:
            raise QaSchemaError(
                f"Cannot detect schema type from {p}. "
                f"Expected one of top-level keys: {list(_VALIDATORS.keys())}"
            )

    if schema_type not in _VALIDATORS:
        raise QaSchemaError(
            f"Unknown schema type '{schema_type}'. "
            f"Must be one of: {list(_VALIDATORS.keys())}"
        )

    top_key, validator_fn = _VALIDATORS[schema_type]

    if top_key not in data:
        raise QaSchemaError(
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
    """Validate one or more QA asset files from the command line.

    Usage:
        python -m cli.lib.qa_schemas <file1.yaml> [file2.yaml ...]
        python -m cli.lib.qa_schemas --type plan <file.yaml>
    """
    import sys

    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cli.lib.qa_schemas [--type <type>] <file.yaml> ...")
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
        except (QaSchemaError, FileNotFoundError) as e:
            print(f"FAIL: {f} — {e}")
            exit_code = 1
        except Exception as e:  # noqa: BLE001
            print(f"ERR : {f} — unexpected: {e}")
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
