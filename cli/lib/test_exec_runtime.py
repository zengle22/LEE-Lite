"""Runtime skeleton for governed QA test execution skills."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, to_canonical_path, write_json
from cli.lib.mainline_runtime import submit_handoff
from cli.lib.managed_gateway import governed_write
from cli.lib.registry_store import slugify
from cli.lib.test_exec_artifacts import normalize_ui_source_spec
from cli.lib.test_exec_execution import run_narrow_execution


SKILL_CONFIG = {
    "test-exec-web-e2e": {
        "skill_ref": "skill.qa.test_exec_web_e2e",
        "runner_skill_ref": "skill.runner.test_e2e",
        "execution_modality": "web_e2e",
        "required_env_fields": ("base_url", "browser"),
    },
    "test-exec-cli": {
        "skill_ref": "skill.qa.test_exec_cli",
        "runner_skill_ref": "skill.runner.test_cli",
        "execution_modality": "cli",
        "required_env_fields": (),
    },
}

_COVERAGE_MODES = {"auto", "smoke", "qualification", "off"}


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


def _coverage_mode(environment: dict[str, Any]) -> str:
    mode = str(environment.get("coverage_mode") or "auto").strip().lower()
    return mode if mode in _COVERAGE_MODES else "auto"


def load_yaml_document(ref_value: str, workspace_root: Path) -> dict[str, Any]:
    path = canonical_to_path(ref_value, workspace_root)
    ensure(path.exists(), "PRECONDITION_FAILED", f"yaml file not found: {ref_value}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ensure(isinstance(payload, dict), "INVALID_REQUEST", "yaml document must be an object")
    payload["_source_ref"] = to_canonical_path(path, workspace_root)
    return payload


def build_candidate_package(
    action: str,
    request_id: str,
    test_set: dict[str, Any],
    environment: dict[str, Any],
    payload: dict[str, Any],
    execution_result: dict[str, str],
) -> tuple[str, dict[str, Any]]:
    config = SKILL_CONFIG[action]
    slug = slugify(f"{config['skill_ref']}-{request_id}")
    artifact_ref = f"candidate.{slug}"
    ui_source_spec = normalize_ui_source_spec(payload)
    candidate = {
        "artifact_type": "governed_test_exec_candidate",
        "request_id": request_id,
        "skill_ref": config["skill_ref"],
        "runner_skill_ref": config["runner_skill_ref"],
        "execution_modality": config["execution_modality"],
        "test_set_ref": test_set["_source_ref"],
        "test_set_id": test_set.get("test_set_id", test_set.get("id", "")),
        "test_environment_ref": environment["_source_ref"],
        "ui_source_spec": ui_source_spec,
        "proposal_ref": str(payload.get("proposal_ref", request_id)),
        "status": "candidate_executed",
        "run_status": execution_result["run_status"],
        "acceptance_status": "not_reviewed",
        "source_refs": [item for item in (test_set.get("feat_ref"), test_set.get("epic_ref"), test_set.get("src_ref")) if item],
    }
    for key, value in execution_result.items():
        if key.endswith("_ref"):
            candidate[key] = value
    return artifact_ref, candidate


def _validate_environment(action: str, environment: dict[str, Any]) -> None:
    config = SKILL_CONFIG[action]
    ensure(
        environment.get("execution_modality") == config["execution_modality"],
        "PRECONDITION_FAILED",
        "execution modality mismatch",
    )
    for field in config["required_env_fields"]:
        ensure(field in environment, "PRECONDITION_FAILED", f"missing environment field: {field}")
    if action == "test-exec-cli":
        ensure(
            environment.get("command_entry") or environment.get("runner_command"),
            "PRECONDITION_FAILED",
            "missing environment field: command_entry or runner_command",
        )


def _apply_testset_coverage_defaults(test_set: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(environment)
    mode = _coverage_mode(environment)
    feature_owned = _as_list(test_set.get("feature_owned_code_paths"))
    recommended_scope = _as_list(test_set.get("recommended_coverage_scope_name"))
    explicit_scope = bool(_as_list(environment.get("coverage_include")) or _as_list(environment.get("coverage_source")))
    if mode == "off":
        resolved["coverage_mode"] = "off"
        resolved["coverage_enabled"] = False
        resolved["coverage_scope_origin"] = "coverage_mode:off"
        return resolved
    if mode == "smoke":
        resolved["coverage_mode"] = "smoke"
        resolved["coverage_enabled"] = False
        resolved["coverage_scope_origin"] = "coverage_mode:smoke"
        return resolved
    if mode == "qualification":
        resolved["coverage_mode"] = "qualification"
        resolved["coverage_enabled"] = True
        if explicit_scope:
            resolved["coverage_scope_origin"] = "environment"
            return resolved
        if feature_owned:
            resolved["coverage_include"] = feature_owned
            resolved["coverage_scope_name"] = recommended_scope or [str(test_set.get("title") or "feature coverage")]
            resolved["coverage_scope_origin"] = "test_set.feature_owned_code_paths"
            return resolved
        ensure(
            False,
            "PRECONDITION_FAILED",
            "coverage qualification requires coverage_include, coverage_source, or feature_owned_code_paths",
        )
    if feature_owned and not explicit_scope:
        resolved["coverage_enabled"] = bool(environment.get("coverage_enabled", True))
        resolved["coverage_include"] = feature_owned
        resolved["coverage_scope_name"] = recommended_scope or [str(test_set.get("title") or "feature coverage")]
        resolved["coverage_scope_origin"] = "test_set.feature_owned_code_paths"
    else:
        resolved["coverage_scope_origin"] = "environment"
    resolved["coverage_mode"] = "qualification" if resolved.get("coverage_enabled") else "smoke"
    return resolved


def execute_test_exec_skill(
    workspace_root: Path,
    trace: dict[str, Any],
    action: str,
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    test_set = load_yaml_document(str(payload.get("test_set_ref", "")), workspace_root)
    environment = load_yaml_document(str(payload.get("test_environment_ref", "")), workspace_root)
    ensure(test_set.get("ssot_type") == "TESTSET", "PRECONDITION_FAILED", "test_set_ref must resolve to a TESTSET")
    environment = _apply_testset_coverage_defaults(test_set, environment)
    _validate_environment(action, environment)
    execution_result = run_narrow_execution(workspace_root, trace, request_id, action, test_set, environment, payload)

    artifact_ref, candidate = build_candidate_package(action, request_id, test_set, environment, payload, execution_result)
    staging_ref = f".workflow/runs/{trace.get('run_ref', request_id)}/generated/{slugify(artifact_ref)}.json"
    write_json(workspace_root / staging_ref, candidate)
    gateway_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=request_id,
        artifact_ref=artifact_ref,
        workspace_path=f"artifacts/active/qa/candidates/{slugify(artifact_ref)}.json",
        requested_mode="write",
        content_ref=staging_ref,
        overwrite=True,
    )
    config = SKILL_CONFIG[action]
    handoff_result = submit_handoff(
        workspace_root,
        trace=trace,
        producer_ref=config["skill_ref"],
        proposal_ref=str(payload.get("proposal_ref", request_id)),
        payload_ref=gateway_result["managed_artifact_ref"],
        pending_state="gate_pending",
        trace_context_ref=str(payload.get("trace_context_ref", trace.get("run_ref", ""))),
    )
    return {
        "skill_ref": config["skill_ref"],
        "runner_skill_ref": config["runner_skill_ref"],
        "candidate_artifact_ref": artifact_ref,
        "candidate_managed_artifact_ref": gateway_result["managed_artifact_ref"],
        "candidate_receipt_ref": gateway_result["receipt_ref"],
        "candidate_registry_record_ref": gateway_result["registry_record_ref"],
        **execution_result,
        **handoff_result,
    }
