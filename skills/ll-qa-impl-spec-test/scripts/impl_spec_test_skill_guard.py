#!/usr/bin/env python3
"""Validation helpers for impl-spec-test skill envelopes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from cli.lib.silent_override import OverrideResult  # type reference for semantic_stability dimension
except ImportError:
    OverrideResult = None  # type: ignore[misc]  # available when run from project root


# Markdown parsing constants
_HEADING_RE = re.compile(r'^(#{2,4})\s+(.+)$', re.MULTILINE)
_MAX_EXCERPT_LINES = 3

def _parse_markdown_sections(content: str) -> list[dict[str, Any]]:
    sections = []
    lines = content.split('\n')
    for line_number, line in enumerate(lines, 1):
        match = _HEADING_RE.match(line)
        if match:
            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()
            collected_lines = []
            # Collect up to _MAX_EXCERPT_LINES non-empty lines after the heading
            i = line_number  # line_number is 1-based
            while len(collected_lines) < _MAX_EXCERPT_LINES and i < len(lines):
                next_line = lines[i]
                # Stop if we encounter another heading
                if _HEADING_RE.match(next_line):
                    break
                stripped_line = next_line.strip()
                if stripped_line:
                    collected_lines.append(stripped_line)
                # Continue searching for non-empty lines even if we encounter empty ones
                i += 1
            excerpt = "\n".join(collected_lines) if collected_lines else heading_text
            sections.append({
                "heading_level": heading_level,
                "heading_text": heading_text,
                "excerpt": excerpt,
                "line_number": line_number
            })
    return sections

def validate_markdown_sections(path: Path) -> list[dict[str, str]]:
    content = path.read_text(encoding="utf-8")
    sections = _parse_markdown_sections(content)
    if not sections:
        return [{"severity": "warning", "title": "No markdown sections detected", "detail": f"File {path.name} contains no recognizable headings."}]
    return []

ALLOWED_VERDICTS = {"pass", "pass_with_revisions", "block"}
ALLOWED_RUN_STATUSES = {"completed", "completed_with_findings", "completed_with_blockers"}
ALLOWED_REVIEW_COVERAGE_STATUSES = {"sufficient", "partial", "insufficient"}
DEEP_REVIEW_REF_FIELDS = {
    "semantic_review_ref",
    "system_views_ref",
    "logic_risk_inventory_ref",
    "ux_risk_inventory_ref",
    "ux_improvement_inventory_ref",
    "journey_simulation_ref",
    "state_invariant_check_ref",
    "cross_artifact_trace_ref",
    "open_questions_ref",
    "false_negative_challenge_ref",
    "dimension_reviews_ref",
    "review_coverage_ref",
    "defects_ref",
}

# Recovery handling fields - required for features that involve state changes or external operations
RECOVERY_HANDLING_REF_FIELDS = {
    "recovery_behavior_ref",
    "rollback_strategy_ref",
    "degraded_mode_ref",
    "retry_logic_ref",
}

# Features that require recovery handling validation
RECOVERY_REQUIRED_AXIS_PATTERNS = {
    "formalization",
    "materialization",
    "state_change",
    "external_operation",
    "db_operation",
    "file_operation",
    "api_call",
    "engineering_baseline",
}


def _fail(message: str) -> int:
    print(f"[ERROR] {message}", file=sys.stderr)
    return 1


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return payload


def _load_json_any(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_ref(base_path: Path, ref_value: str) -> Path:
    ref_path = Path(ref_value)
    if ref_path.is_absolute():
        return ref_path
    if ref_path.parts and ref_path.parts[0] == "artifacts":
        for parent in [base_path.parent, *base_path.parents]:
            artifacts_dir = parent / "artifacts"
            if artifacts_dir.exists():
                workspace_candidate = parent / ref_path
                if workspace_candidate.exists():
                    return workspace_candidate
    local_candidate = base_path.parent / ref_path
    if local_candidate.exists():
        return local_candidate
    workspace_root = base_path.parent
    if workspace_root.name == "active" and workspace_root.parent.name == "artifacts":
        workspace_root = workspace_root.parent.parent
    workspace_candidate = workspace_root / ref_path
    return workspace_candidate if workspace_candidate.exists() else local_candidate


def _ensure_fields(payload: dict, fields: list[str], label: str) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")


def validate_input(path: Path) -> int:
    payload = _load_json(path)
    _ensure_fields(payload, ["api_version", "command", "request_id", "workspace_root", "actor_ref", "trace", "payload"], "request")
    if payload["api_version"] != "v1":
        raise ValueError("request api_version must be v1")
    if payload["command"] != "skill.impl-spec-test":
        raise ValueError("request command must be skill.impl-spec-test")
    body = payload["payload"]
    if not isinstance(body, dict):
        raise ValueError("request payload must be an object")
    _ensure_fields(body, ["impl_ref", "impl_package_ref", "feat_ref", "tech_ref"], "payload")
    if body.get("repo_context") is not None and not isinstance(body.get("repo_context"), dict):
        raise ValueError("request payload.repo_context must be an object when provided")
    if body.get("execution_mode") is not None and not isinstance(body.get("execution_mode"), dict):
        raise ValueError("request payload.execution_mode must be an object when provided")
    if body.get("risk_profile") is not None and not isinstance(body.get("risk_profile"), dict):
        raise ValueError("request payload.risk_profile must be an object when provided")
    if body.get("review_profile") is not None and not isinstance(body.get("review_profile"), dict):
        raise ValueError("request payload.review_profile must be an object when provided")
    if body.get("surface_map_ref") is not None and not isinstance(body.get("surface_map_ref"), str):
        raise ValueError("request payload.surface_map_ref must be a string when provided")
    if body.get("prototype_ref") is not None and not isinstance(body.get("prototype_ref"), str):
        raise ValueError("request payload.prototype_ref must be a string when provided")
    if body.get("resolved_design_refs") is not None and not isinstance(body.get("resolved_design_refs"), dict):
        raise ValueError("request payload.resolved_design_refs must be an object when provided")
    for field in ("journey_personas", "counterexample_families", "review_focus", "source_refs", "ui_refs", "testset_refs"):
        if body.get(field) is not None and not isinstance(body.get(field), list):
            raise ValueError(f"request payload.{field} must be an array when provided")
    if body.get("false_negative_challenge") is not None and not isinstance(body.get("false_negative_challenge"), bool):
        raise ValueError("request payload.false_negative_challenge must be a boolean when provided")
    if body.get("surface_map_ref"):
        resolved_design_refs = body.get("resolved_design_refs")
        prototype_ref = body.get("prototype_ref")
        if not prototype_ref and not resolved_design_refs:
            raise ValueError("surface_map_ref requires prototype_ref or resolved_design_refs to establish a coherence check")
        if isinstance(resolved_design_refs, dict):
            surface_map_ref = str(resolved_design_refs.get("surface_map_ref") or "").strip()
            if surface_map_ref and surface_map_ref != str(body.get("surface_map_ref") or "").strip():
                raise ValueError("request payload.surface_map_ref must match resolved_design_refs.surface_map_ref when both are provided")
    resolved_design_refs = body.get("resolved_design_refs")
    if body.get("prototype_ref") and isinstance(resolved_design_refs, dict):
        resolved_prototype_ref = str(resolved_design_refs.get("prototype_ref") or "").strip()
        if resolved_prototype_ref and resolved_prototype_ref != str(body.get("prototype_ref") or "").strip():
            raise ValueError("request payload.prototype_ref must match resolved_design_refs.prototype_ref when both are provided")
    print("[OK] Input request is valid for skill.impl-spec-test")
    return 0


def _is_recovery_handling_required(feature: dict[str, Any]) -> bool:
    """Check if recovery handling validation is required for this feature."""
    axis = str(feature.get("axis_id") or feature.get("derived_axis") or "").lower()
    title = str(feature.get("title") or "").lower()
    src_ref = str(feature.get("src_root_id") or feature.get("src_ref") or "")

    # Check axis patterns
    if any(pattern in axis for pattern in RECOVERY_REQUIRED_AXIS_PATTERNS):
        return True

    # Check for SRC-003 engineering baseline (requires recovery for db migrations, etc.)
    if "SRC-003" in src_ref or "SRC003" in src_ref:
        return True

    # Check title patterns
    recovery_keywords = ["migration", "rollback", "recovery", "degraded", "retry", "fallback"]
    if any(keyword in title for keyword in recovery_keywords):
        return True

    return False


def _validate_recovery_handling(data: dict, base_path: Path) -> list[str]:
    """Validate recovery handling fields when required."""
    errors = []
    feature = data.get("feature_snapshot") or {}

    if not _is_recovery_handling_required(feature):
        return errors

    # Check for recovery handling refs
    missing_refs = []
    for ref_field in RECOVERY_HANDLING_REF_FIELDS:
        if ref_field not in data:
            missing_refs.append(ref_field)

    # If recovery is required but refs are missing, check if there's explicit waiver
    if missing_refs:
        waiver = data.get("recovery_handling_waiver")
        if not waiver:
            errors.append(
                f"Recovery handling required for this feature but missing refs: {', '.join(missing_refs)}. "
                "Either provide recovery_behavior_ref, rollback_strategy_ref, degraded_mode_ref, retry_logic_ref, "
                "or provide recovery_handling_waiver with justification."
            )
        elif not isinstance(waiver, dict) or "reason" not in waiver:
            errors.append("recovery_handling_waiver must be an object with 'reason' field")

    # Validate recovery handling refs exist
    for ref_field in RECOVERY_HANDLING_REF_FIELDS:
        ref_value = data.get(ref_field)
        if ref_value:
            ref_path = _resolve_ref(base_path, str(ref_value))
            if not ref_path.exists():
                errors.append(f"response.data.{ref_field} does not exist: {ref_path}")

    return errors


def validate_output(path: Path) -> int:
    payload = _load_json(path)
    _ensure_fields(payload, ["api_version", "command", "request_id", "result_status", "status_code", "exit_code", "message", "data"], "response")
    if payload["api_version"] != "v1":
        raise ValueError("response api_version must be v1")
    if payload["command"] != "skill.impl-spec-test":
        raise ValueError("response command must be skill.impl-spec-test")
    data = payload["data"]
    if not isinstance(data, dict):
        raise ValueError("response data must be an object")
    _ensure_fields(
        data,
        [
            "skill_ref",
            "runner_skill_ref",
            "candidate_artifact_ref",
            "candidate_managed_artifact_ref",
            "candidate_receipt_ref",
            "candidate_registry_record_ref",
            "handoff_ref",
            "gate_pending_ref",
            "run_status",
            "verdict",
            "implementation_readiness",
            "self_contained_readiness",
            "self_contained_evaluation_mode",
            "recommended_next_action",
            "recommended_actor",
            "repair_target_artifact",
            "execution_mode",
            "report_package_ref",
            "report_json_ref",
            "report_markdown_ref",
            "semantic_review_ref",
            "system_views_ref",
            "logic_risk_inventory_ref",
            "ux_risk_inventory_ref",
            "ux_improvement_inventory_ref",
            "journey_simulation_ref",
            "state_invariant_check_ref",
            "cross_artifact_trace_ref",
            "open_questions_ref",
            "false_negative_challenge_ref",
            "dimension_reviews_ref",
            "review_coverage_ref",
            "defects_ref",
            "gate_subject_ref",
            "intake_result_ref",
            "issue_inventory_ref",
            "counterexample_result_ref",
            "readiness_verdict_ref",
            "repair_suggestions_ref",
            "execution_evidence_ref",
            "supervision_evidence_ref",
        ],
        "response.data",
    )
    if data["skill_ref"] != "skill.qa.impl_spec_test":
        raise ValueError("response.data.skill_ref must be skill.qa.impl_spec_test")
    if data["runner_skill_ref"] != "skill.runner.impl_spec_test":
        raise ValueError("response.data.runner_skill_ref must be skill.runner.impl_spec_test")
    if data["run_status"] not in ALLOWED_RUN_STATUSES:
        raise ValueError("response.data.run_status is not recognized")
    if data["verdict"] not in ALLOWED_VERDICTS:
        raise ValueError("response.data.verdict is not recognized")
    if data.get("recommended_next_action") not in {"revise_impl", "rederive_upstream", "proceed_to_gate", "proceed_to_coding"}:
        raise ValueError("response.data.recommended_next_action is not recognized")
    if data.get("recommended_actor") not in {"impl_author", "upstream_owner", "human_gate", "coder"}:
        raise ValueError("response.data.recommended_actor is not recognized")
    review_coverage = _load_json(_resolve_ref(path, str(data["review_coverage_ref"])))
    review_status = str(review_coverage.get("status") or "").strip()
    if review_status not in ALLOWED_REVIEW_COVERAGE_STATUSES:
        raise ValueError("response.data.review_coverage.status is not recognized")
    if data["verdict"] == "pass" and review_status != "sufficient":
        raise ValueError("response.data.verdict cannot be pass unless review coverage is sufficient")
    dimension_reviews = _load_json(_resolve_ref(path, str(data["dimension_reviews_ref"])))
    expected_dimensions = {
        "functional_logic",
        "data_modeling",
        "user_journey",
        "ui_usability",
        "api_contract",
        "implementation_executability",
        "testability",
        "migration_compatibility",
        "semantic_stability",  # 9th dimension — Phase 9 addition
    }
    if set(dimension_reviews.keys()) != expected_dimensions:
        raise ValueError("dimension reviews must contain all 9 dimensions (8 ADR-036 + semantic_stability)")

    # Validate semantic_stability dimension structure
    semantic_stability = dimension_reviews.get("semantic_stability", {})
    _semantic_stability_required_fields = ["checked", "frz_refs", "semantic_drift", "verdict"]
    for field in _semantic_stability_required_fields:
        if field not in semantic_stability:
            raise ValueError(f"semantic_stability dimension missing required field: {field}")

    # Validate semantic_drift sub-structure (D-06)
    semantic_drift = semantic_stability.get("semantic_drift", {})
    _semantic_drift_required_fields = ["has_drift", "drift_results", "classification"]
    for field in _semantic_drift_required_fields:
        if field not in semantic_drift:
            raise ValueError(f"semantic_stability.semantic_drift missing required field: {field}")

    # Validate semantic_drift consistency
    if semantic_drift.get("has_drift") is True:
        if semantic_stability.get("verdict") != "block":
            raise ValueError("semantic_stability verdict must be 'block' when semantic_drift.has_drift is True")

    # Validate overall verdict consistency with semantic_stability
    if data["verdict"] == "pass" and semantic_stability.get("verdict") == "block":
        raise ValueError("overall verdict cannot be 'pass' when semantic_stability verdict is 'block'")

    # Validate recovery handling when required
    recovery_errors = _validate_recovery_handling(data, path)
    if recovery_errors:
        for error in recovery_errors:
            print(f"[WARNING] Recovery handling: {error}", file=sys.stderr)
        # For now, log warnings but don't block - recovery handling is a quality improvement
        # In strict mode, this could be made into a blocking error

    present_deep_fields = [field for field in DEEP_REVIEW_REF_FIELDS if field in data]
    if present_deep_fields:
        missing_deep_fields = [field for field in DEEP_REVIEW_REF_FIELDS if field not in data]
        if missing_deep_fields:
            raise ValueError(f"response.data is missing deep-review fields: {', '.join(missing_deep_fields)}")
        for ref_field in DEEP_REVIEW_REF_FIELDS:
            ref_path = _resolve_ref(path, str(data[ref_field]))
            if not ref_path.exists():
                raise ValueError(f"response.data.{ref_field} does not exist")
            payload = _load_json_any(ref_path)
            if not isinstance(payload, (dict, list)):
                raise ValueError(f"response.data.{ref_field} must be JSON object or array")
    print("[OK] Output response is valid for skill.impl-spec-test")
    return 0


def collect_evidence(path: Path) -> int:
    payload = _load_json(path)
    refs = {key: value for key, value in payload.get("data", {}).items() if key.endswith("_ref")}
    print(json.dumps({"evidence_refs": refs}, ensure_ascii=False, indent=2))
    return 0


def freeze_guard(path: Path) -> int:
    validate_output(path)
    payload = _load_json(path)
    verdict = payload["data"]["verdict"]
    review_coverage = _load_json(_resolve_ref(path, str(payload["data"]["review_coverage_ref"])))
    if verdict != "pass":
        raise ValueError("freeze guard requires verdict=pass")
    if str(payload["data"].get("self_contained_readiness") or "").strip() != "sufficient":
        raise ValueError("freeze guard requires self_contained_readiness=sufficient")
    if str(payload["data"].get("implementation_readiness") or "").strip() != "ready":
        raise ValueError("freeze guard requires implementation_readiness=ready")
    if str(review_coverage.get("status") or "").strip() != "sufficient":
        raise ValueError("freeze guard requires review coverage to be sufficient")
    print(f"[OK] Freeze guard passed with verdict={verdict}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate impl-spec-test skill requests and responses.")
    parser.add_argument("mode", choices=("validate-input", "validate-output", "collect-evidence", "freeze-guard"))
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path).resolve()
    if not path.exists():
        return _fail(f"file not found: {path}")
    try:
        if args.mode == "validate-input":
            return validate_input(path)
        if args.mode == "validate-output":
            return validate_output(path)
        if args.mode == "collect-evidence":
            return collect_evidence(path)
        return freeze_guard(path)
    except Exception as exc:  # noqa: BLE001
        return _fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
