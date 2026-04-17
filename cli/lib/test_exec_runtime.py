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
from cli.lib.test_exec_artifacts import (
    normalize_ui_source_spec,
    PatchContext,
    resolve_patch_context,
)
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
        resolved["qualification_budget"] = environment.get("qualification_budget", test_set.get("qualification_budget", 1))
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


def _validate_testset_execution_boundary(test_set: dict[str, Any]) -> None:
    ensure(test_set.get("ssot_type") == "TESTSET", "PRECONDITION_FAILED", "test_set_ref must resolve to a TESTSET")
    ensure(isinstance(test_set.get("test_units", []), list), "PRECONDITION_FAILED", "TESTSET must define test_units as strategy anchors")
    ensure(
        not bool(test_set.get("test_case_pack") or test_set.get("script_pack")),
        "PRECONDITION_FAILED",
        "TESTSET must not embed execution artifacts such as test_case_pack or script_pack",
    )


def _check_patch_test_impact(
    patch_context: PatchContext,
    workspace_root: Path,
) -> list[str]:
    """Verify test_impact declarations before execution (D-18).

    Returns list of warnings/errors. Empty list = proceed.
    """
    messages: list[str] = []
    for patch in patch_context.validated_patches + patch_context.pending_patches:
        change_class = patch.get("change_class", "visual")
        test_impact = patch.get("test_impact")

        if change_class == "visual":
            # D-05: optional, WARN only if present but incomplete
            if test_impact and not test_impact.get("affected_routes"):
                messages.append(
                    f"WARN: Patch {patch['id']} (visual) has test_impact "
                    f"but no affected_routes listed"
                )
            continue

        # D-04: interaction/semantic must have test_impact
        if not test_impact:
            messages.append(
                f"ERROR: Patch {patch['id']} ({change_class}) missing test_impact"
            )
            continue

        if not test_impact.get("affected_routes"):
            messages.append(
                f"ERROR: Patch {patch['id']} ({change_class}) has empty affected_routes"
            )

    return messages


def execute_test_exec_skill(
    workspace_root: Path,
    trace: dict[str, Any],
    action: str,
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    test_set = load_yaml_document(str(payload.get("test_set_ref", "")), workspace_root)
    environment = load_yaml_document(str(payload.get("test_environment_ref", "")), workspace_root)
    _validate_testset_execution_boundary(test_set)
    environment = _apply_testset_coverage_defaults(test_set, environment)
    _validate_environment(action, environment)

    # D-11: Inject patch context + pre-sync check
    patch_context = resolve_patch_context(workspace_root)
    if patch_context.has_active_patches:
        impact_messages = _check_patch_test_impact(patch_context, workspace_root)
        errors = [m for m in impact_messages if m.startswith("ERROR")]
        if errors:
            ensure(False, "PATCH_TEST_IMPACT_VIOLATION", "; ".join(errors))
        # Warnings are logged but execution continues

        # D-22: TOCTOU re-verification before execution
        recheck_context = resolve_patch_context(workspace_root)
        if recheck_context.directory_hash != patch_context.directory_hash:
            ensure(False, "PATCH_CONTEXT_CHANGED",
                f"Patch directory changed between context resolution and execution. "
                f"Initial hash: {patch_context.directory_hash[:12]}..., "
                f"Current hash: {recheck_context.directory_hash[:12]}...")

        # D-07/D-08: Mark manifest items affected by patches (in-memory only, no persistent write-back for this phase)
        from cli.lib.test_exec_artifacts import mark_manifest_patch_affected, create_manifest_items_for_new_scenarios
        # Note: manifest_items modification happens in-memory within the execution context
        # D-09: Create new manifest items for new test scenarios
        # (wired for future use when manifest_items are available in execution flow)

    execution_result = run_narrow_execution(workspace_root, trace, request_id, action, test_set, environment, payload, patch_context)

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
