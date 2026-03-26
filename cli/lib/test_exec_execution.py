"""Narrow execution loop for governed test execution skills."""

from __future__ import annotations

import io
import json
import os
import shlex
import subprocess
from pathlib import PurePath
from pathlib import Path
from typing import Any

import yaml
from coverage import Coverage

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, read_text, to_canonical_path, write_json, write_text
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
from cli.lib.test_exec_ui_sources import collect_ui_source_context
from cli.lib.test_exec_ui_resolution import apply_ui_binding, derive_ui_intent, resolve_ui_binding


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]

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


def execute_case(
    workspace_root: Path,
    command_entry: str,
    case: dict[str, Any],
    environment: dict[str, Any],
    evidence_root: Path,
) -> dict[str, Any]:
    case_dir = evidence_root / _case_slug(str(case["case_id"]))
    refs = _write_case_manifests(workspace_root, case, command_entry, environment, case_dir)
    refs["coverage_data_ref"] = to_canonical_path(
        evidence_root.parent / "coverage-raw" / f"{slugify(case['case_id'])[-24:]}.cov",
        workspace_root,
    )
    workdir = canonical_to_path(str(environment.get("workdir", ".")), workspace_root)
    timeout = int(environment.get("timeout_seconds", 30))
    stdout_text = ""
    stderr_text = ""
    exit_code: int | None = None
    raw_status = "runner_error"
    diagnostics: list[str] = []
    coverage_status = "disabled"
    coverage_reason = ""
    run_command: str | list[str] = command_entry
    run_with_shell = True
    coverage_enabled = bool(environment.get("coverage_enabled"))
    if coverage_enabled:
        try:
            tokens = shlex.split(command_entry, posix=False)
        except ValueError:
            tokens = []
        tokens = [token.strip('"') for token in tokens if token]
        if tokens and PurePath(tokens[0].strip('"')).name.lower().startswith("python"):
            coverage_data_path = workspace_root / refs["coverage_data_ref"]
            coverage_data_path.parent.mkdir(parents=True, exist_ok=True)
            run_command = [tokens[0], "-m", "coverage", "run", f"--data-file={coverage_data_path}", *tokens[1:]]
            run_with_shell = False
            coverage_status = "enabled"
        else:
            coverage_status = "unsupported"
            coverage_reason = "coverage instrumentation requires a Python script/module command entry"
            diagnostics.append(coverage_reason)
    try:
        result = subprocess.run(
            run_command,
            shell=run_with_shell,
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
    coverage_data_path = workspace_root / refs["coverage_data_ref"]
    if coverage_enabled and coverage_status == "enabled" and coverage_data_path.exists():
        payload["coverage_data_ref"] = refs["coverage_data_ref"]
        payload["coverage_status"] = "collected"
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


def _derive_actual_message(workspace_root: Path, run: dict[str, Any] | None, status: str) -> str:
    if run is None:
        return "case did not execute"
    stdout_ref = run.get("stdout_ref")
    if isinstance(stdout_ref, str) and stdout_ref:
        stdout_path = canonical_to_path(stdout_ref, workspace_root)
    else:
        stdout_path = None
    if stdout_path and stdout_path.exists():
        lines = [line.strip() for line in read_text(stdout_path).splitlines() if line.strip()]
        if lines:
            first = lines[0]
            if len(first) > 220:
                first = first[:217] + "..."
            return first
    if status == "blocked":
        return "command timed out"
    if status == "invalid":
        return "required evidence missing" if run.get("raw_status") != "runner_error" else "runner error"
    if status == "failed":
        return f"command exited with {run.get('exit_code')}"
    return "command exited with 0"


def build_results_summary(
    case_results: list[dict[str, Any]],
    compliance: dict[str, Any],
    output_ok: bool,
    coverage_summary: dict[str, Any],
) -> dict[str, Any]:
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
    return {
        "artifact_type": "results_summary",
        **counts,
        "run_status": run_status,
        "coverage": {
            "status": coverage_summary.get("status"),
            "line_rate_percent": coverage_summary.get("line_rate_percent"),
            "covered_lines": coverage_summary.get("covered_lines"),
            "num_statements": coverage_summary.get("num_statements"),
            "scope": coverage_summary.get("scope"),
            "scope_origin": coverage_summary.get("scope_origin"),
        },
    }


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


def collect_coverage(
    workspace_root: Path,
    output_root: Path,
    refs: dict[str, str],
    case_runs: list[dict[str, Any]],
    environment: dict[str, Any],
) -> dict[str, Any]:
    summary = {
        "artifact_type": "coverage_summary",
        "status": "disabled",
        "scope": _as_list(environment.get("coverage_scope_name")) or ["cli execution"],
        "include": _as_list(environment.get("coverage_include")),
        "source": _as_list(environment.get("coverage_source")),
        "omit": _as_list(environment.get("coverage_omit")),
        "scope_origin": str(environment.get("coverage_scope_origin", "environment")),
        "raw_data_count": 0,
        "measured_files": 0,
        "covered_lines": 0,
        "num_statements": 0,
        "missing_lines": 0,
        "line_rate_percent": None,
        "notes": [],
    }
    if not environment.get("coverage_enabled"):
        write_json(workspace_root / refs["coverage_summary_ref"], summary)
        write_json(workspace_root / refs["coverage_details_ref"], {"meta": summary, "files": {}})
        write_text(workspace_root / refs["coverage_report_ref"], "# Coverage Report\n\n- status: disabled\n")
        return summary

    data_refs = [run.get("coverage_data_ref", "") for run in case_runs if run.get("coverage_status") == "collected"]
    summary["raw_data_count"] = len(data_refs)
    if not data_refs:
        summary["status"] = "unavailable"
        summary["notes"].append("coverage was enabled but no compatible Python coverage data files were produced")
        write_json(workspace_root / refs["coverage_summary_ref"], summary)
        write_json(workspace_root / refs["coverage_details_ref"], {"meta": summary, "files": {}})
        write_text(workspace_root / refs["coverage_report_ref"], "# Coverage Report\n\n- status: unavailable\n- note: coverage was enabled but no compatible Python coverage data files were produced\n")
        return summary

    coverage_dir = output_root / "coverage"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    combined_data_file = coverage_dir / ".coverage"
    cov = Coverage(data_file=str(combined_data_file))
    raw_paths = [str(canonical_to_path(str(ref), workspace_root)) for ref in data_refs]
    cov.combine(data_paths=raw_paths, strict=False, keep=True)
    cov.save()
    include = _as_list(environment.get("coverage_include")) or None
    omit = _as_list(environment.get("coverage_omit")) or None
    report_buffer = io.StringIO()
    line_rate = cov.report(file=report_buffer, ignore_errors=True, include=include, omit=omit)
    cov.json_report(outfile=str(workspace_root / refs["coverage_details_ref"]), pretty_print=True, include=include, omit=omit)
    details = json.loads((workspace_root / refs["coverage_details_ref"]).read_text(encoding="utf-8"))
    totals = details.get("totals", {})
    summary.update(
        {
            "status": "collected",
            "measured_files": len(details.get("files", {})),
            "covered_lines": totals.get("covered_lines"),
            "num_statements": totals.get("num_statements"),
            "missing_lines": totals.get("missing_lines"),
            "line_rate_percent": round(float(line_rate), 2),
        }
    )
    report_lines = [
        "# Coverage Report",
        "",
        f"- status: {summary['status']}",
        f"- line_rate_percent: {summary['line_rate_percent']}",
        f"- covered_lines: {summary['covered_lines']}",
        f"- num_statements: {summary['num_statements']}",
        f"- measured_files: {summary['measured_files']}",
        f"- scope: {', '.join(summary['scope'])}",
    ]
    if summary["include"]:
        report_lines.append(f"- include: {', '.join(summary['include'])}")
    if summary["source"]:
        report_lines.append(f"- source: {', '.join(summary['source'])}")
    report_lines.extend(["", "## coverage report", "", report_buffer.getvalue().strip()])
    write_json(workspace_root / refs["coverage_summary_ref"], summary)
    write_text(workspace_root / refs["coverage_report_ref"], "\n".join(report_lines).strip() + "\n")
    return summary


def _build_execution_refs(output_root: Path, workspace_root: Path) -> dict[str, str]:
    return {
        "resolved_ssot_context_ref": to_canonical_path(output_root / "resolved-ssot-context.yaml", workspace_root),
        "ui_intent_ref": to_canonical_path(output_root / "ui-intent.json", workspace_root),
        "ui_source_context_ref": to_canonical_path(output_root / "ui-source-context.json", workspace_root),
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
        "coverage_summary_ref": to_canonical_path(output_root / "coverage-summary.json", workspace_root),
        "coverage_details_ref": to_canonical_path(output_root / "coverage-details.json", workspace_root),
        "coverage_report_ref": to_canonical_path(output_root / "coverage-report.md", workspace_root),
        "output_validation_ref": to_canonical_path(output_root / "output-validation.json", workspace_root),
        "tse_ref": to_canonical_path(output_root / "tse.json", workspace_root),
    }


def _write_pre_execution_artifacts(
    workspace_root: Path,
    refs: dict[str, str],
    context: dict[str, Any],
    ui_intent: dict[str, Any],
    ui_source_context: dict[str, Any],
    ui_binding_map: dict[str, Any],
    case_pack: dict[str, Any],
    case_meta: dict[str, Any],
) -> None:
    (workspace_root / refs["test_case_pack_ref"]).parent.mkdir(parents=True, exist_ok=True)
    _write_yaml(workspace_root / refs["resolved_ssot_context_ref"], context)
    write_json(workspace_root / refs["ui_intent_ref"], ui_intent)
    write_json(workspace_root / refs["ui_source_context_ref"], ui_source_context)
    write_json(workspace_root / refs["ui_binding_map_ref"], ui_binding_map)
    _write_yaml(workspace_root / refs["test_case_pack_ref"], case_pack)
    write_json(workspace_root / refs["test_case_pack_meta_ref"], case_meta)


def _finalize_execution_outputs(
    workspace_root: Path,
    output_root: Path,
    refs: dict[str, str],
    trace: dict[str, Any],
    case_pack: dict[str, Any],
    script_pack: dict[str, Any],
    environment: dict[str, Any],
    case_runs: list[dict[str, Any]],
    raw_output: dict[str, Any],
) -> dict[str, str]:
    script_meta = build_freeze_meta("script_pack", script_pack)
    write_json(workspace_root / refs["script_pack_ref"], script_pack)
    write_json(workspace_root / refs["script_pack_meta_ref"], script_meta)
    write_json(workspace_root / refs["raw_runner_output_ref"], {"trace": trace, **raw_output, "results": case_runs})
    compliance = evaluate_compliance(case_pack, str(environment.get("execution_modality", "")), case_runs, workspace_root)
    write_json(workspace_root / refs["compliance_result_ref"], compliance)
    case_results = judge_case_results(case_pack, case_runs, compliance)
    for item, run in zip(case_results, case_runs):
        item["actual"] = _derive_actual_message(workspace_root, run, item["status"])
    write_json(workspace_root / refs["case_results_ref"], {"trace": trace, "results": case_results})
    write_json(workspace_root / refs["evidence_bundle_ref"], {"trace": trace, "cases": case_runs, "compliance_status": compliance["status"]})
    refs["bug_bundle_ref"] = build_bug_bundle(case_results, output_root, workspace_root)
    coverage_summary = collect_coverage(workspace_root, output_root, refs, case_runs, environment)
    provisional = build_results_summary(case_results, compliance, output_ok=True, coverage_summary=coverage_summary)
    write_json(workspace_root / refs["results_summary_ref"], provisional)
    write_text(workspace_root / refs["test_report_ref"], render_report(provisional, compliance, case_results))
    output_validation = validate_outputs(workspace_root, case_pack, case_results, refs)
    write_json(workspace_root / refs["output_validation_ref"], output_validation)
    summary = build_results_summary(case_results, compliance, output_ok=output_validation["status"] == "pass", coverage_summary=coverage_summary)
    write_json(workspace_root / refs["results_summary_ref"], summary)
    write_text(workspace_root / refs["test_report_ref"], render_report(summary, compliance, case_results))
    write_json(workspace_root / refs["tse_ref"], _build_tse_payload(trace, refs, summary["run_status"]))
    return {"bug_bundle_ref": refs["bug_bundle_ref"], "run_status": summary["run_status"]}


def _build_tse_payload(trace: dict[str, Any], refs: dict[str, str], run_status: str) -> dict[str, Any]:
    return {
        "trace": trace,
        "run_status": run_status,
        "acceptance_status": "not_reviewed",
        "resolved_ssot_context_ref": refs["resolved_ssot_context_ref"],
        "ui_intent_ref": refs["ui_intent_ref"],
        "ui_source_context_ref": refs["ui_source_context_ref"],
        "ui_binding_map_ref": refs["ui_binding_map_ref"],
        "test_case_pack_ref": refs["test_case_pack_ref"],
        "script_pack_ref": refs["script_pack_ref"],
        "compliance_result_ref": refs["compliance_result_ref"],
        "case_results_ref": refs["case_results_ref"],
        "results_summary_ref": refs["results_summary_ref"],
        "evidence_bundle_ref": refs["evidence_bundle_ref"],
        "bug_bundle_ref": refs["bug_bundle_ref"],
        "test_report_ref": refs["test_report_ref"],
        "coverage_summary_ref": refs["coverage_summary_ref"],
        "coverage_details_ref": refs["coverage_details_ref"],
        "coverage_report_ref": refs["coverage_report_ref"],
        "output_validation_ref": refs["output_validation_ref"],
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
    ui_source_context = collect_ui_source_context(workspace_root, ui_source_spec, environment, raw_case_pack)
    ui_binding_map = resolve_ui_binding(raw_case_pack, ui_intent, ui_source_spec, ui_source_context)
    case_pack = apply_ui_binding(raw_case_pack, ui_binding_map)
    script_pack = build_script_pack(action, environment, case_pack, ui_source_spec)
    case_meta = build_freeze_meta("test_case_pack", case_pack)
    refs = _build_execution_refs(output_root, workspace_root)
    _write_pre_execution_artifacts(
        workspace_root,
        refs,
        context,
        ui_intent,
        ui_source_context,
        ui_binding_map,
        case_pack,
        case_meta,
    )
    case_runs, raw_output = execute_cases(workspace_root, output_root, action, case_pack, script_pack, environment, evidence_root)
    outcome = _finalize_execution_outputs(
        workspace_root,
        output_root,
        refs,
        trace,
        case_pack,
        script_pack,
        environment,
        case_runs,
        raw_output,
    )
    return {**refs, **outcome}
