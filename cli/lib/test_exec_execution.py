"""Narrow execution loop for governed test execution skills."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, to_canonical_path, write_json, write_text
from cli.lib.registry_store import slugify
from cli.lib.test_exec_artifacts import (
    build_freeze_meta,
    build_script_pack,
    build_test_case_pack,
    normalize_ui_source_spec,
    render_report,
    resolve_ssot_context,
)
from cli.lib.test_exec_playwright import run_playwright_project, write_playwright_project
from cli.lib.test_exec_ui_resolution import apply_ui_binding, derive_ui_intent, resolve_ui_binding


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))




def _execution_env(case: dict[str, Any], environment: dict[str, Any]) -> dict[str, str]:
    extra = os.environ.copy()
    extra.update(
        {
            "LEE_TEST_CASE_ID": str(case["case_id"]),
            "LEE_TEST_CASE_TITLE": str(case["title"]),
            "LEE_TEST_PRIORITY": str(case["priority"]),
            "LEE_TRIGGER_ACTION": str(case.get("trigger_action", "")),
            "LEE_EXECUTION_MODALITY": str(environment.get("execution_modality", "")),
        }
    )
    if environment.get("base_url"):
        extra["LEE_BASE_URL"] = str(environment["base_url"])
    if environment.get("browser"):
        extra["LEE_BROWSER"] = str(environment["browser"])
    return extra


def _evidence_refs(case_dir: Path, workspace_root: Path) -> dict[str, str]:
    return {
        "stdout_ref": to_canonical_path(case_dir / "stdout.txt", workspace_root),
        "stderr_ref": to_canonical_path(case_dir / "stderr.txt", workspace_root),
        "result_ref": to_canonical_path(case_dir / "result.json", workspace_root),
        "command_manifest_ref": to_canonical_path(case_dir / "command.json", workspace_root),
        "env_snapshot_ref": to_canonical_path(case_dir / "env.json", workspace_root),
    }


def _write_case_manifests(
    workspace_root: Path,
    case: dict[str, Any],
    command_entry: str,
    environment: dict[str, Any],
    case_dir: Path,
) -> dict[str, str]:
    refs = _evidence_refs(case_dir, workspace_root)
    write_json(
        workspace_root / refs["command_manifest_ref"],
        {
            "case_id": case["case_id"],
            "command_entry": command_entry,
            "workdir": str(environment.get("workdir", ".")),
            "timeout_seconds": int(environment.get("timeout_seconds", 30)),
        },
    )
    write_json(
        workspace_root / refs["env_snapshot_ref"],
        {
            "case_id": case["case_id"],
            "execution_modality": environment.get("execution_modality", ""),
            "base_url": environment.get("base_url"),
            "browser": environment.get("browser"),
            "workdir": str(environment.get("workdir", ".")),
        },
    )
    return refs


def execute_case(
    workspace_root: Path,
    command_entry: str,
    case: dict[str, Any],
    environment: dict[str, Any],
    evidence_root: Path,
) -> dict[str, Any]:
    case_dir = evidence_root / slugify(case["case_id"])
    refs = _write_case_manifests(workspace_root, case, command_entry, environment, case_dir)
    workdir = canonical_to_path(str(environment.get("workdir", ".")), workspace_root)
    timeout = int(environment.get("timeout_seconds", 30))
    stdout_text = ""
    stderr_text = ""
    exit_code: int | None = None
    raw_status = "runner_error"
    diagnostics: list[str] = []
    try:
        result = subprocess.run(
            command_entry,
            shell=True,
            cwd=workdir,
            env=_execution_env(case, environment),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout_text = result.stdout
        stderr_text = result.stderr
        exit_code = result.returncode
        raw_status = "passed" if result.returncode == 0 else "failed"
    except subprocess.TimeoutExpired as exc:
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or ""
        raw_status = "timeout"
        diagnostics.append(f"command timed out after {timeout}s")
    except OSError as exc:
        stderr_text = str(exc)
        diagnostics.append(f"runner error: {exc}")
    write_text(workspace_root / refs["stdout_ref"], stdout_text)
    write_text(workspace_root / refs["stderr_ref"], stderr_text)
    payload = {
        "case_id": case["case_id"],
        "command_entry": command_entry,
        "exit_code": exit_code,
        "raw_status": raw_status,
        "stdout_ref": refs["stdout_ref"],
        "stderr_ref": refs["stderr_ref"],
        "command_manifest_ref": refs["command_manifest_ref"],
        "env_snapshot_ref": refs["env_snapshot_ref"],
        "diagnostics": diagnostics,
    }
    write_json(workspace_root / refs["result_ref"], payload)
    payload["result_ref"] = refs["result_ref"]
    return payload


def _minimum_evidence(case: dict[str, Any], execution_modality: str) -> list[str]:
    required = ["result_ref", "command_manifest_ref", "env_snapshot_ref"]
    if case.get("priority", "P1") in {"P0", "P1"}:
        required.extend(["stdout_ref", "stderr_ref"])
    if execution_modality == "web_e2e":
        required.append("result_ref")
    return required


def execute_cases(
    workspace_root: Path,
    output_root: Path,
    action: str,
    case_pack: dict[str, Any],
    script_pack: dict[str, Any],
    environment: dict[str, Any],
    evidence_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if action == "test-exec-web-e2e":
        project_refs = write_playwright_project(workspace_root, output_root, case_pack, environment)
        script_pack["project_refs"] = project_refs
        web_run = run_playwright_project(workspace_root, output_root, environment)
        raw_output = {
            "framework": "playwright",
            "exit_code": web_run["exit_code"],
            "stdout_ref": web_run["stdout_ref"],
            "stderr_ref": web_run["stderr_ref"],
            "report_ref": web_run["report_ref"],
        }
        return web_run["case_runs"], raw_output
    bindings = script_pack["bindings"]
    case_runs = [execute_case(workspace_root, item["command_entry"], case, environment, evidence_root) for case, item in zip(case_pack["cases"], bindings)]
    return case_runs, {"framework": "shell", "results": case_runs}


def evaluate_compliance(
    case_pack: dict[str, Any],
    execution_modality: str,
    case_runs: list[dict[str, Any]],
    workspace_root: Path,
) -> dict[str, Any]:
    run_map = {item["case_id"]: item for item in case_runs}
    case_checks = []
    issues = []
    for case in case_pack["cases"]:
        run = run_map.get(case["case_id"])
        missing = []
        if not run:
            missing.append("result_ref")
        else:
            for field in _minimum_evidence(case, execution_modality):
                ref_value = run.get(field)
                if not ref_value or not canonical_to_path(str(ref_value), workspace_root).exists():
                    missing.append(field)
        compliant = not missing
        if not compliant:
            issues.append({"case_id": case["case_id"], "missing_evidence": missing})
        case_checks.append(
            {
                "case_id": case["case_id"],
                "priority": case.get("priority", "P1"),
                "compliant": compliant,
                "missing_evidence": missing,
            }
        )
    return {
        "artifact_type": "compliance_result",
        "execution_modality": execution_modality,
        "status": "pass" if not issues else "invalid_run",
        "case_checks": case_checks,
        "issues": issues,
    }


def judge_case_results(
    case_pack: dict[str, Any],
    case_runs: list[dict[str, Any]],
    compliance: dict[str, Any],
) -> list[dict[str, Any]]:
    run_map = {item["case_id"]: item for item in case_runs}
    compliance_map = {item["case_id"]: item for item in compliance["case_checks"]}
    results = []
    for case in case_pack["cases"]:
        run = run_map.get(case["case_id"])
        check = compliance_map[case["case_id"]]
        if run is None:
            status = "not_executed"
            actual = "case did not execute"
        elif not check["compliant"]:
            status = "invalid"
            actual = "required evidence missing"
        elif run["raw_status"] == "timeout":
            status = "blocked"
            actual = "command timed out"
        elif run["raw_status"] == "runner_error":
            status = "invalid"
            actual = "runner error"
        elif run["raw_status"] == "failed":
            status = "failed"
            actual = f"command exited with {run['exit_code']}"
        else:
            status = "passed"
            actual = "command exited with 0"
        results.append(
            {
                "case_id": case["case_id"],
                "title": case["title"],
                "priority": case["priority"],
                "status": status,
                "expected": case.get("pass_conditions", []),
                "actual": actual,
                "evidence_ref": run.get("result_ref", "") if run else "",
                "stdout_ref": run.get("stdout_ref", "") if run else "",
                "stderr_ref": run.get("stderr_ref", "") if run else "",
                "diagnostics": run.get("diagnostics", []) if run else [],
            }
        )
    return results


def build_results_summary(case_results: list[dict[str, Any]], compliance: dict[str, Any], output_ok: bool) -> dict[str, Any]:
    counts = {key: 0 for key in ("passed", "failed", "blocked", "invalid", "not_executed")}
    for item in case_results:
        counts[item["status"]] += 1
    if not output_ok:
        run_status = "failed"
    elif compliance["status"] != "pass":
        run_status = "invalid_run"
    elif counts["failed"] > 0:
        run_status = "completed_with_failures"
    elif counts["blocked"] > 0 or counts["invalid"] > 0 or counts["not_executed"] > 0:
        run_status = "completed_with_warnings"
    else:
        run_status = "completed"
    return {"artifact_type": "results_summary", **counts, "run_status": run_status}


def build_bug_bundle(case_results: list[dict[str, Any]], output_root: Path, workspace_root: Path) -> str:
    bug_root = output_root / "bugs"
    bugs = []
    for item in case_results:
        if item["status"] != "failed":
            continue
        bug_id = f"BUG-{slugify(item['case_id'])}"
        bug_ref = to_canonical_path(bug_root / f"{bug_id}.json", workspace_root)
        write_json(
            workspace_root / bug_ref,
            {
                "bug_id": bug_id,
                "case_id": item["case_id"],
                "title": item["title"],
                "actual": item["actual"],
                "expected": item["expected"],
                "evidence_ref": item["evidence_ref"],
            },
        )
        bugs.append({"bug_id": bug_id, "bug_ref": bug_ref, "case_id": item["case_id"]})
    index_ref = to_canonical_path(bug_root / "index.json", workspace_root)
    write_json(workspace_root / index_ref, {"bugs": bugs})
    return index_ref


def validate_outputs(
    workspace_root: Path,
    case_pack: dict[str, Any],
    case_results: list[dict[str, Any]],
    refs: dict[str, str],
) -> dict[str, Any]:
    errors = []
    deferred_refs = {"output_validation_ref", "tse_ref"}
    if len(case_results) != len(case_pack["cases"]):
        errors.append("case_results count mismatch")
    for name, ref_value in refs.items():
        if name in deferred_refs:
            continue
        if not canonical_to_path(ref_value, workspace_root).exists():
            errors.append(f"missing artifact: {name}")
    return {
        "artifact_type": "output_validation",
        "status": "pass" if not errors else "failed",
        "errors": errors,
    }


def run_narrow_execution(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    action: str,
    test_set: dict[str, Any],
    environment: dict[str, Any],
    payload: dict[str, Any] | None = None,
) -> dict[str, str]:
    payload = payload or {}
    command_entry = str(environment.get("command_entry", environment.get("runner_command", "")))
    if action != "test-exec-web-e2e":
        ensure(command_entry, "PRECONDITION_FAILED", "execution command is required")
    run_slug = slugify(f"{action}-{request_id}")
    output_root = workspace_root / "artifacts" / "active" / "qa" / "executions" / run_slug
    evidence_root = output_root / "evidence"
    ui_source_spec = normalize_ui_source_spec(payload)
    context = resolve_ssot_context(test_set, environment, ui_source_spec)
    raw_case_pack = build_test_case_pack(test_set)
    ui_intent = derive_ui_intent(raw_case_pack, ui_source_spec)
    ui_binding_map = resolve_ui_binding(raw_case_pack, ui_intent, ui_source_spec)
    case_pack = apply_ui_binding(raw_case_pack, ui_binding_map)
    script_pack = build_script_pack(action, environment, case_pack, ui_source_spec)
    case_meta = build_freeze_meta("test_case_pack", case_pack)

    refs = {
        "resolved_ssot_context_ref": to_canonical_path(output_root / "resolved-ssot-context.yaml", workspace_root),
        "ui_intent_ref": to_canonical_path(output_root / "ui-intent.json", workspace_root),
        "ui_binding_map_ref": to_canonical_path(output_root / "ui-binding-map.json", workspace_root),
        "test_case_pack_ref": to_canonical_path(output_root / "test-case-pack.yaml", workspace_root),
        "test_case_pack_meta_ref": to_canonical_path(output_root / "test-case-pack.meta.json", workspace_root),
        "script_pack_ref": to_canonical_path(output_root / "script-pack.json", workspace_root),
        "script_pack_meta_ref": to_canonical_path(output_root / "script-pack.meta.json", workspace_root),
        "raw_runner_output_ref": to_canonical_path(output_root / "raw-runner-output.json", workspace_root),
        "compliance_result_ref": to_canonical_path(output_root / "compliance-result.json", workspace_root),
        "case_results_ref": to_canonical_path(output_root / "case-results.json", workspace_root),
        "results_summary_ref": to_canonical_path(output_root / "results-summary.json", workspace_root),
        "evidence_bundle_ref": to_canonical_path(output_root / "evidence" / "index.json", workspace_root),
        "test_report_ref": to_canonical_path(output_root / "test-report.md", workspace_root),
        "output_validation_ref": to_canonical_path(output_root / "output-validation.json", workspace_root),
        "tse_ref": to_canonical_path(output_root / "tse.json", workspace_root),
    }
    (workspace_root / refs["test_case_pack_ref"]).parent.mkdir(parents=True, exist_ok=True)
    _write_yaml(workspace_root / refs["resolved_ssot_context_ref"], context)
    write_json(workspace_root / refs["ui_intent_ref"], ui_intent)
    write_json(workspace_root / refs["ui_binding_map_ref"], ui_binding_map)
    _write_yaml(workspace_root / refs["test_case_pack_ref"], case_pack)
    write_json(workspace_root / refs["test_case_pack_meta_ref"], case_meta)
    case_runs, raw_output = execute_cases(workspace_root, output_root, action, case_pack, script_pack, environment, evidence_root)
    script_meta = build_freeze_meta("script_pack", script_pack)
    write_json(workspace_root / refs["script_pack_ref"], script_pack)
    write_json(workspace_root / refs["script_pack_meta_ref"], script_meta)
    write_json(workspace_root / refs["raw_runner_output_ref"], {"trace": trace, **raw_output, "results": case_runs})
    compliance = evaluate_compliance(case_pack, str(environment.get("execution_modality", "")), case_runs, workspace_root)
    write_json(workspace_root / refs["compliance_result_ref"], compliance)
    case_results = judge_case_results(case_pack, case_runs, compliance)
    write_json(workspace_root / refs["case_results_ref"], {"trace": trace, "results": case_results})
    write_json(workspace_root / refs["evidence_bundle_ref"], {"trace": trace, "cases": case_runs, "compliance_status": compliance["status"]})
    bug_bundle_ref = build_bug_bundle(case_results, output_root, workspace_root)
    refs["bug_bundle_ref"] = bug_bundle_ref

    provisional_summary = build_results_summary(case_results, compliance, output_ok=True)
    write_json(workspace_root / refs["results_summary_ref"], provisional_summary)
    write_text(workspace_root / refs["test_report_ref"], render_report(provisional_summary, compliance, case_results))
    output_validation = validate_outputs(workspace_root, case_pack, case_results, refs)
    write_json(workspace_root / refs["output_validation_ref"], output_validation)
    summary = build_results_summary(case_results, compliance, output_ok=output_validation["status"] == "pass")
    write_json(workspace_root / refs["results_summary_ref"], summary)
    write_text(workspace_root / refs["test_report_ref"], render_report(summary, compliance, case_results))
    write_json(
        workspace_root / refs["tse_ref"],
        {
            "trace": trace,
            "run_status": summary["run_status"],
            "acceptance_status": "not_reviewed",
            "resolved_ssot_context_ref": refs["resolved_ssot_context_ref"],
            "ui_intent_ref": refs["ui_intent_ref"],
            "ui_binding_map_ref": refs["ui_binding_map_ref"],
            "test_case_pack_ref": refs["test_case_pack_ref"],
            "script_pack_ref": refs["script_pack_ref"],
            "compliance_result_ref": refs["compliance_result_ref"],
            "case_results_ref": refs["case_results_ref"],
            "results_summary_ref": refs["results_summary_ref"],
            "evidence_bundle_ref": refs["evidence_bundle_ref"],
            "bug_bundle_ref": refs["bug_bundle_ref"],
            "test_report_ref": refs["test_report_ref"],
            "output_validation_ref": refs["output_validation_ref"],
        },
    )
    return {
        **refs,
        "bug_bundle_ref": refs["bug_bundle_ref"],
        "run_status": summary["run_status"],
    }
