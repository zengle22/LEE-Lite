"""Reporting and validation helpers for test execution runtime."""

from __future__ import annotations

import io
import hashlib
import json
from pathlib import Path
from typing import Any

from coverage import Coverage

from cli.lib.fs import canonical_to_path, read_text, to_canonical_path, write_json, write_text
from cli.lib.registry_store import slugify
from cli.lib.test_exec_artifacts import render_report


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


def _minimum_evidence(case: dict[str, Any], execution_modality: str) -> list[str]:
    required = ["result_ref", "command_manifest_ref", "env_snapshot_ref"]
    if case.get("priority", "P1") in {"P0", "P1"}:
        required.extend(["stdout_ref", "stderr_ref"])
    if execution_modality == "web_e2e":
        required.append("result_ref")
    return required


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


def _derive_actual_message(workspace_root: Path, run: dict[str, Any] | None, status: str) -> str:
    if run is None:
        return "case did not execute"
    stdout_ref = run.get("stdout_ref")
    stdout_path = canonical_to_path(stdout_ref, workspace_root) if isinstance(stdout_ref, str) and stdout_ref else None
    if stdout_path and stdout_path.exists():
        lines = [line.strip() for line in read_text(stdout_path).splitlines() if line.strip()]
        if lines:
            first = lines[0]
            return first if len(first) <= 220 else first[:217] + "..."
    if status == "blocked":
        return "command timed out"
    if status == "invalid":
        return "required evidence missing" if run.get("raw_status") != "runner_error" else "runner error"
    if status == "failed":
        return f"command exited with {run.get('exit_code')}"
    return "command exited with 0"


def judge_case_results(
    workspace_root: Path,
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
        elif not check["compliant"]:
            status = "invalid"
        elif run["raw_status"] == "timeout":
            status = "blocked"
        elif run["raw_status"] == "runner_error":
            status = "invalid"
        elif run["raw_status"] == "failed":
            status = "failed"
        else:
            status = "passed"
        results.append(
            {
                "case_id": case["case_id"],
                "title": case["title"],
                "priority": case["priority"],
                "status": status,
                "expected": case.get("pass_conditions", []),
                "actual": _derive_actual_message(workspace_root, run, status),
                "evidence_ref": run.get("result_ref", "") if run else "",
                "stdout_ref": run.get("stdout_ref", "") if run else "",
                "stderr_ref": run.get("stderr_ref", "") if run else "",
                "diagnostics": run.get("diagnostics", []) if run else [],
            }
        )
    return results


def build_results_summary(
    case_results: list[dict[str, Any]],
    compliance: dict[str, Any],
    output_ok: bool,
    coverage_summary: dict[str, Any],
    traceability: dict[str, Any] | None = None,
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
        "traceability": traceability or {},
        "coverage": {
            "status": coverage_summary.get("status"),
            "line_rate_percent": coverage_summary.get("line_rate_percent"),
            "branch_rate_percent": coverage_summary.get("branch_rate_percent"),
            "branch_coverage": coverage_summary.get("branch_coverage"),
            "covered_branches": coverage_summary.get("covered_branches"),
            "num_branches": coverage_summary.get("num_branches"),
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
        digest = hashlib.sha1(str(item["case_id"]).encode("utf-8")).hexdigest()[:10]
        bug_id = f"BUG-{slugify(item['case_id'])[:48]}-{digest}"
        bug_ref = to_canonical_path(bug_root / f"{bug_id}.json", workspace_root)
        bug_path = canonical_to_path(bug_ref, workspace_root)
        bug_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(
            bug_path,
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
    index_path = canonical_to_path(index_ref, workspace_root)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(index_path, {"bugs": bugs})
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
    return {"artifact_type": "output_validation", "status": "pass" if not errors else "failed", "errors": errors}


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
        "branch_coverage": bool(environment.get("coverage_branch_enabled")),
        "covered_branches": 0,
        "num_branches": 0,
        "missing_branches": 0,
        "branch_rate_percent": None,
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
    cov = Coverage(data_file=str(combined_data_file), branch=bool(environment.get("coverage_branch_enabled")))
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
            "branch_coverage": bool(details.get("meta", {}).get("branch_coverage", environment.get("coverage_branch_enabled"))),
            "covered_branches": totals.get("covered_branches", 0),
            "num_branches": totals.get("num_branches", 0),
            "missing_branches": totals.get("missing_branches", 0),
        }
    )
    if summary["num_branches"]:
        try:
            summary["branch_rate_percent"] = round((float(summary["covered_branches"]) / float(summary["num_branches"])) * 100.0, 2)
        except (TypeError, ValueError, ZeroDivisionError):
            summary["branch_rate_percent"] = None
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
    if summary["branch_coverage"]:
        report_lines.extend(
            [
                f"- branch_coverage: {summary['branch_coverage']}",
                f"- branch_rate_percent: {summary['branch_rate_percent']}",
                f"- covered_branches: {summary['covered_branches']}",
                f"- num_branches: {summary['num_branches']}",
            ]
        )
    if summary["include"]:
        report_lines.append(f"- include: {', '.join(summary['include'])}")
    if summary["source"]:
        report_lines.append(f"- source: {', '.join(summary['source'])}")
    report_lines.extend(["", "## coverage report", "", report_buffer.getvalue().strip()])
    write_json(workspace_root / refs["coverage_summary_ref"], summary)
    write_text(workspace_root / refs["coverage_report_ref"], "\n".join(report_lines).strip() + "\n")
    return summary


def build_execution_refs(output_root: Path, workspace_root: Path) -> dict[str, str]:
    return {
        "resolved_ssot_context_ref": to_canonical_path(output_root / "resolved-ssot-context.yaml", workspace_root),
        "ui_intent_ref": to_canonical_path(output_root / "ui-intent.json", workspace_root),
        "ui_source_context_ref": to_canonical_path(output_root / "ui-source-context.json", workspace_root),
        "ui_binding_map_ref": to_canonical_path(output_root / "ui-binding-map.json", workspace_root),
        "ui_flow_plan_ref": to_canonical_path(output_root / "ui-flow-plan.json", workspace_root),
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


def write_pre_execution_artifacts(
    workspace_root: Path,
    refs: dict[str, str],
    write_yaml_fn: Any,
    context: dict[str, Any],
    ui_intent: dict[str, Any],
    ui_source_context: dict[str, Any],
    ui_binding_map: dict[str, Any],
    ui_flow_plan: dict[str, Any],
    case_pack: dict[str, Any],
    case_meta: dict[str, Any],
) -> None:
    (workspace_root / refs["test_case_pack_ref"]).parent.mkdir(parents=True, exist_ok=True)
    write_yaml_fn(workspace_root / refs["resolved_ssot_context_ref"], context)
    write_json(workspace_root / refs["ui_intent_ref"], ui_intent)
    write_json(workspace_root / refs["ui_source_context_ref"], ui_source_context)
    write_json(workspace_root / refs["ui_binding_map_ref"], ui_binding_map)
    write_json(workspace_root / refs["ui_flow_plan_ref"], ui_flow_plan)
    write_yaml_fn(workspace_root / refs["test_case_pack_ref"], case_pack)
    write_json(workspace_root / refs["test_case_pack_meta_ref"], case_meta)


def build_tse_payload(trace: dict[str, Any], refs: dict[str, str], run_status: str) -> dict[str, Any]:
    return {
        "trace": trace,
        "run_status": run_status,
        "acceptance_status": "not_reviewed",
        "resolved_ssot_context_ref": refs["resolved_ssot_context_ref"],
        "ui_intent_ref": refs["ui_intent_ref"],
        "ui_source_context_ref": refs["ui_source_context_ref"],
        "ui_binding_map_ref": refs["ui_binding_map_ref"],
        "ui_flow_plan_ref": refs["ui_flow_plan_ref"],
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


def finalize_execution_outputs(
    workspace_root: Path,
    output_root: Path,
    refs: dict[str, str],
    trace: dict[str, Any],
    case_pack: dict[str, Any],
    script_pack: dict[str, Any],
    environment: dict[str, Any],
    case_runs: list[dict[str, Any]],
    raw_output: dict[str, Any],
    build_freeze_meta_fn: Any,
) -> dict[str, str]:
    script_meta = build_freeze_meta_fn("script_pack", script_pack)
    write_json(workspace_root / refs["script_pack_ref"], script_pack)
    write_json(workspace_root / refs["script_pack_meta_ref"], script_meta)
    write_json(workspace_root / refs["raw_runner_output_ref"], {"trace": trace, **raw_output, "results": case_runs})
    compliance = evaluate_compliance(case_pack, str(environment.get("execution_modality", "")), case_runs, workspace_root)
    write_json(workspace_root / refs["compliance_result_ref"], compliance)
    case_results = judge_case_results(workspace_root, case_pack, case_runs, compliance)
    write_json(workspace_root / refs["case_results_ref"], {"trace": trace, "results": case_results})
    write_json(workspace_root / refs["evidence_bundle_ref"], {"trace": trace, "cases": case_runs, "compliance_status": compliance["status"]})
    refs["bug_bundle_ref"] = build_bug_bundle(case_results, output_root, workspace_root)
    coverage_summary = collect_coverage(workspace_root, output_root, refs, case_runs, environment)
    traceability_summary = case_pack.get("traceability_summary", {})
    provisional = build_results_summary(
        case_results,
        compliance,
        output_ok=True,
        coverage_summary=coverage_summary,
        traceability=traceability_summary,
    )
    write_json(workspace_root / refs["results_summary_ref"], provisional)
    write_text(workspace_root / refs["test_report_ref"], render_report(provisional, compliance, case_results))
    output_validation = validate_outputs(workspace_root, case_pack, case_results, refs)
    write_json(workspace_root / refs["output_validation_ref"], output_validation)
    summary = build_results_summary(
        case_results,
        compliance,
        output_ok=output_validation["status"] == "pass",
        coverage_summary=coverage_summary,
        traceability=traceability_summary,
    )
    summary["projection_mode"] = case_pack.get("projection_mode", "minimal_projection")
    summary["generation_mode"] = case_pack.get("generation_mode", summary["projection_mode"])
    summary["expansion_round"] = int(case_pack.get("expansion_round", 0) or 0)
    summary["expansion_stop_reason"] = str(case_pack.get("expansion_stop_reason", ""))
    summary["qualification_budget"] = case_pack.get("qualification_budget")
    summary["qualification_lineage"] = case_pack.get("qualification_lineage", [])
    write_json(workspace_root / refs["results_summary_ref"], summary)
    write_text(workspace_root / refs["test_report_ref"], render_report(summary, compliance, case_results))
    write_json(workspace_root / refs["tse_ref"], build_tse_payload(trace, refs, summary["run_status"]))
    return {
        "bug_bundle_ref": refs["bug_bundle_ref"],
        "run_status": summary["run_status"],
        "coverage_summary": coverage_summary,
        "projection_mode": summary["projection_mode"],
        "generation_mode": summary["generation_mode"],
        "expansion_round": summary["expansion_round"],
        "qualification_budget": summary.get("qualification_budget"),
        "expansion_stop_reason": summary.get("expansion_stop_reason", ""),
        "qualification_lineage": summary.get("qualification_lineage", []),
    }
