"""Narrow execution loop for governed test execution skills."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path, PurePath
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
    resolve_ssot_context,
)
from cli.lib.test_exec_playwright import ensure_playwright_project, run_playwright_project, write_playwright_project
from cli.lib.test_exec_reporting import (
    build_execution_refs,
    finalize_execution_outputs,
    write_pre_execution_artifacts,
)
from cli.lib.test_exec_ui_flow import apply_ui_flow_plan, derive_ui_flow_plan
from cli.lib.test_exec_ui_resolution import apply_ui_binding, derive_ui_intent, resolve_ui_binding
from cli.lib.test_exec_ui_sources import collect_ui_source_context


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


def _case_slug(case_id: str) -> str:
    tail = slugify(case_id.split("-")[-1])[-12:] or "case"
    digest = slugify(case_id)[-10:]
    return f"{tail}-{digest}"


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


def _coverage_command(command_entry: str, workspace_root: Path, coverage_ref: str) -> tuple[str | list[str], bool, str, str]:
    try:
        tokens = shlex.split(command_entry, posix=False)
    except ValueError:
        tokens = []
    tokens = [token.strip('"') for token in tokens if token]
    if tokens and PurePath(tokens[0].strip('"')).name.lower().startswith("python"):
        coverage_data_path = workspace_root / coverage_ref
        coverage_data_path.parent.mkdir(parents=True, exist_ok=True)
        return [tokens[0], "-m", "coverage", "run", f"--data-file={coverage_data_path}", *tokens[1:]], False, "enabled", ""
    reason = "coverage instrumentation requires a Python script/module command entry"
    return command_entry, True, "unsupported", reason


def _run_subprocess(
    command: str | list[str],
    use_shell: bool,
    workdir: Path,
    env: dict[str, str],
    timeout: int,
) -> tuple[str, str, int | None, str, list[str]]:
    stdout_text = ""
    stderr_text = ""
    exit_code: int | None = None
    raw_status = "runner_error"
    diagnostics: list[str] = []
    try:
        result = subprocess.run(command, shell=use_shell, cwd=workdir, env=env, capture_output=True, text=True, timeout=timeout)
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
    return stdout_text, stderr_text, exit_code, raw_status, diagnostics


def execute_case(
    workspace_root: Path,
    command_entry: str,
    case: dict[str, Any],
    environment: dict[str, Any],
    evidence_root: Path,
) -> dict[str, Any]:
    case_dir = evidence_root / _case_slug(str(case["case_id"]))
    refs = _write_case_manifests(workspace_root, case, command_entry, environment, case_dir)
    refs["coverage_data_ref"] = to_canonical_path(evidence_root.parent / "coverage-raw" / f"{slugify(case['case_id'])[-24:]}.cov", workspace_root)
    timeout = int(environment.get("timeout_seconds", 30))
    workdir = canonical_to_path(str(environment.get("workdir", ".")), workspace_root)
    run_command: str | list[str] = command_entry
    run_with_shell = True
    coverage_enabled = bool(environment.get("coverage_enabled"))
    coverage_status = "disabled"
    coverage_reason = ""
    diagnostics: list[str] = []
    if coverage_enabled:
        run_command, run_with_shell, coverage_status, coverage_reason = _coverage_command(command_entry, workspace_root, refs["coverage_data_ref"])
        if coverage_reason:
            diagnostics.append(coverage_reason)
    stdout_text, stderr_text, exit_code, raw_status, run_diagnostics = _run_subprocess(
        run_command,
        run_with_shell,
        workdir,
        _execution_env(case, environment),
        timeout,
    )
    diagnostics.extend(run_diagnostics)
    write_text(workspace_root / refs["stdout_ref"], stdout_text)
    write_text(workspace_root / refs["stderr_ref"], stderr_text)
    payload = {
        "case_id": case["case_id"],
        "command_entry": command_entry,
        "executed_command": run_command if isinstance(run_command, str) else " ".join(run_command),
        "exit_code": exit_code,
        "raw_status": raw_status,
        "stdout_ref": refs["stdout_ref"],
        "stderr_ref": refs["stderr_ref"],
        "command_manifest_ref": refs["command_manifest_ref"],
        "env_snapshot_ref": refs["env_snapshot_ref"],
        "coverage_enabled": coverage_enabled,
        "coverage_status": coverage_status,
        "coverage_reason": coverage_reason,
        "diagnostics": diagnostics,
    }
    if coverage_enabled and coverage_status == "enabled" and (workspace_root / refs["coverage_data_ref"]).exists():
        payload["coverage_data_ref"] = refs["coverage_data_ref"]
        payload["coverage_status"] = "collected"
    write_json(workspace_root / refs["result_ref"], payload)
    payload["result_ref"] = refs["result_ref"]
    return payload


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
    runtime_probe_root: Path | None = None
    if action == "test-exec-web-e2e":
        write_playwright_project(workspace_root, output_root, raw_case_pack, environment)
        ensure_playwright_project(output_root / "playwright-project", environment)
        runtime_probe_root = output_root / "playwright-project"
    ui_intent = derive_ui_intent(raw_case_pack, ui_source_spec)
    ui_source_context = collect_ui_source_context(
        workspace_root,
        ui_source_spec,
        environment,
        raw_case_pack,
        project_root=runtime_probe_root,
    )
    ui_binding_map = resolve_ui_binding(raw_case_pack, ui_intent, ui_source_spec, ui_source_context)
    ui_flow_plan = derive_ui_flow_plan(raw_case_pack, ui_binding_map)
    case_pack = apply_ui_binding(raw_case_pack, ui_binding_map)
    case_pack = apply_ui_flow_plan(case_pack, ui_flow_plan)
    script_pack = build_script_pack(action, environment, case_pack, ui_source_spec)
    case_meta = build_freeze_meta("test_case_pack", case_pack)
    refs = build_execution_refs(output_root, workspace_root)
    write_pre_execution_artifacts(
        workspace_root,
        refs,
        _write_yaml,
        context,
        ui_intent,
        ui_source_context,
        ui_binding_map,
        ui_flow_plan,
        case_pack,
        case_meta,
    )
    case_runs, raw_output = execute_cases(workspace_root, output_root, action, case_pack, script_pack, environment, evidence_root)
    outcome = finalize_execution_outputs(
        workspace_root,
        output_root,
        refs,
        trace,
        case_pack,
        script_pack,
        environment,
        case_runs,
        raw_output,
        build_freeze_meta,
    )
    return {**refs, **outcome}
