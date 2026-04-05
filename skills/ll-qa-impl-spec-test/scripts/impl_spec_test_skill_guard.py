#!/usr/bin/env python3
"""Validation helpers for impl-spec-test skill envelopes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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
    for field in ("journey_personas", "counterexample_families", "review_focus", "source_refs", "ui_refs", "testset_refs"):
        if body.get(field) is not None and not isinstance(body.get(field), list):
            raise ValueError(f"request payload.{field} must be an array when provided")
    if body.get("false_negative_challenge") is not None and not isinstance(body.get("false_negative_challenge"), bool):
        raise ValueError("request payload.false_negative_challenge must be a boolean when provided")
    print("[OK] Input request is valid for skill.impl-spec-test")
    return 0


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
    }
    if set(dimension_reviews.keys()) != expected_dimensions:
        raise ValueError("dimension reviews must contain all 8 ADR-036 dimensions")
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
