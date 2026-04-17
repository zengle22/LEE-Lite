"""Narrow execution loop for governed test execution skills."""

from __future__ import annotations

import os
import json
import shutil
import shlex
import subprocess
from pathlib import Path, PurePath
from typing import Any

import yaml

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, to_canonical_path, write_json, write_text
from cli.lib.registry_store import slugify
from cli.lib.test_exec_artifacts import (
    PatchContext,
    build_freeze_meta,
    build_script_pack,
    build_test_case_pack,
    mark_manifest_patch_affected,
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


def _qualification_goal_percent(test_set: dict[str, Any]) -> float | None:
    goal = test_set.get("coverage_goal")
    if isinstance(goal, dict):
        value = goal.get("line_rate_percent")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    try:
        return float(goal) if goal is not None else None
    except (TypeError, ValueError):
        return None


def _qualification_budget(test_set: dict[str, Any], environment: dict[str, Any]) -> int:
    raw_budget = environment.get("qualification_budget", test_set.get("qualification_budget", 1))
    try:
        return max(0, int(raw_budget))
    except (TypeError, ValueError):
        return 1


def _qualification_max_rounds(test_set: dict[str, Any], environment: dict[str, Any]) -> int:
    raw_value = environment.get("max_expansion_rounds", test_set.get("max_expansion_rounds", 1))
    try:
        return max(0, int(raw_value))
    except (TypeError, ValueError):
        return 1


def _qualification_stop_reason(
    test_set: dict[str, Any],
    coverage_summary: dict[str, Any],
    budget: int,
) -> str:
    status = str(coverage_summary.get("status", "")).strip().lower()
    if status != "collected":
        return "coverage_unavailable" if status in {"disabled", "unavailable"} else f"coverage_{status or 'unknown'}"
    goal = _qualification_goal_percent(test_set)
    line_rate = coverage_summary.get("line_rate_percent")
    if goal is None:
        return "no_coverage_goal"
    try:
        if float(line_rate or 0.0) >= goal:
            return "coverage_goal_reached"
    except (TypeError, ValueError):
        return "coverage_goal_unknown"
    if not bool(test_set.get("branch_families") or test_set.get("expansion_hints")):
        return "no_expansion_hints"
    return "qualification_budget_exhausted" if budget <= 0 else "coverage_below_goal"


def _should_expand_qualification(
    test_set: dict[str, Any],
    coverage_summary: dict[str, Any],
    budget: int,
    round_index: int,
    max_rounds: int,
) -> bool:
    if budget <= 0 or round_index >= max_rounds:
        return False
    if not bool(test_set.get("branch_families") or test_set.get("expansion_hints")):
        return False
    if str(coverage_summary.get("status", "")).strip().lower() != "collected":
        return False
    goal = _qualification_goal_percent(test_set)
    if goal is None:
        return False
    try:
        return float(coverage_summary.get("line_rate_percent") or 0.0) < goal
    except (TypeError, ValueError):
        return False
def _qualification_lineage_entry(
    round_index: int,
    case_pack: dict[str, Any],
    coverage_summary: dict[str, Any],
    stop_reason: str,
) -> dict[str, Any]:
    return {
        "round": round_index,
        "projection_mode": case_pack.get("projection_mode", "minimal_projection"),
        "generation_mode": case_pack.get("generation_mode", case_pack.get("projection_mode", "minimal_projection")),
        "expansion_round": int(case_pack.get("expansion_round", 0) or 0),
        "stop_reason": stop_reason,
        "coverage_status": coverage_summary.get("status"),
        "coverage_line_rate_percent": coverage_summary.get("line_rate_percent"),
        "coverage_scope": coverage_summary.get("scope", []),
    }


def _coverage_expansion_targets(workspace_root: Path, refs: dict[str, str]) -> list[str]:
    details_ref = refs.get("coverage_details_ref", "")
    summary_ref = refs.get("coverage_summary_ref", "")
    if not details_ref:
        return []
    details_path = canonical_to_path(details_ref, workspace_root)
    if not details_path.exists():
        return []
    try:
        payload = json.loads(details_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    branch_coverage_enabled = bool(payload.get("meta", {}).get("branch_coverage"))
    files = payload.get("files", {})
    if not isinstance(files, dict):
        return []
    include_order: list[str] = []
    if summary_ref:
        summary_path = canonical_to_path(summary_ref, workspace_root)
        if summary_path.exists():
            try:
                summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                summary_payload = {}
            include = summary_payload.get("include", [])
            if isinstance(include, list):
                for item in include:
                    text = str(item).strip().lower()
                    if text:
                        include_order.append(text)

    def _variants(value: str) -> list[str]:
        path = Path(str(value))
        raw = str(value).strip().lower().replace("\\", "/")
        variants = [raw, path.as_posix().lower(), path.name.lower(), path.stem.lower()]
        seen: list[str] = []
        for item in variants:
            if item and item not in seen:
                seen.append(item)
        return seen

    def _priority_index(file_name: str) -> int:
        variants = _variants(file_name)
        for index, include_item in enumerate(include_order):
            if any(variant == include_item or variant.endswith(include_item) or include_item.endswith(variant) for variant in variants):
                return index
        return len(include_order)

    ranked_files: list[tuple[int, float, int, str, dict[str, Any]]] = []
    for file_name, file_payload in files.items():
        if not isinstance(file_payload, dict):
            continue
        missing_lines = file_payload.get("missing_lines", [])
        if not isinstance(missing_lines, list):
            continue
        missing_branches = file_payload.get("missing_branches", [])
        if not isinstance(missing_branches, list):
            missing_branches = []
        summary = file_payload.get("summary", {})
        covered_ratio = 0.0
        if isinstance(summary, dict):
            try:
                covered_ratio = float(summary.get("percent_covered", 0.0))
            except (TypeError, ValueError):
                covered_ratio = 0.0
        ranked_files.append(
            (
                len(missing_lines) + len(missing_branches),
                100.0 - covered_ratio,
                _priority_index(str(file_name)),
                str(file_name),
                {
                    "file_name": str(file_name),
                    "missing_lines": sorted(
                        {
                            int(line)
                            for line in missing_lines
                            if not isinstance(line, bool)
                            and str(line).strip().lstrip("-").isdigit()
                        }
                    ),
                    "missing_branches": [str(item).strip() for item in missing_branches if str(item).strip()],
                },
            )
        )
    ranked_files.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
    targets: list[str] = []
    for _, _, _, _, file_info in ranked_files:
        file_slug = slugify(Path(file_info["file_name"]).stem) or "coverage-file"
        if branch_coverage_enabled:
            for branch in file_info["missing_branches"][:2]:
                branch_slug = slugify(branch.replace("->", " to ")) or "branch"
                targets.append(f"{file_slug}-missing-branch-{branch_slug}")
        for line in file_info["missing_lines"][:3]:
            targets.append(f"{file_slug}-missing-line-{line}")
        if not branch_coverage_enabled:
            for branch in file_info["missing_branches"][:2]:
                branch_slug = slugify(branch.replace("->", " to ")) or "branch"
                targets.append(f"{file_slug}-missing-branch-{branch_slug}")
    return targets


def _execute_round(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    action: str,
    test_set: dict[str, Any],
    environment: dict[str, Any],
    payload: dict[str, Any],
    case_pack: dict[str, Any],
    output_root: Path,
    patch_context: PatchContext | None = None,
) -> dict[str, Any]:
    evidence_root = output_root / "evidence"
    ui_source_spec = normalize_ui_source_spec(payload)
    context = resolve_ssot_context(test_set, environment, ui_source_spec)

    # D-17: Apply conflict resolution to case pack (mark blocked cases)
    if patch_context and patch_context.conflict_resolution:
        skip_ids = {cid for cid, resolution in patch_context.conflict_resolution.items() if resolution == "skip"}
        for case in case_pack.get("cases", []):
            coverage_id = case.get("coverage_id", "")
            # Build coverage_id from route pattern (same logic as _build_conflict_resolution_map)
            route_key = coverage_id.replace(".", "/")
            if coverage_id in skip_ids or route_key in skip_ids:
                case["_patch_blocked"] = True
                case["_patch_block_reason"] = "TEST_BLOCKED: irreconcilable conflict"
    runtime_probe_root: Path | None = None
    if action == "test-exec-web-e2e":
        write_playwright_project(workspace_root, output_root, case_pack, environment)
        ensure_playwright_project(output_root / "playwright-project", environment)
        runtime_probe_root = output_root / "playwright-project"
    ui_intent = derive_ui_intent(case_pack, ui_source_spec)
    ui_source_context = collect_ui_source_context(
        workspace_root,
        ui_source_spec,
        environment,
        case_pack,
        project_root=runtime_probe_root,
    )
    ui_binding_map = resolve_ui_binding(case_pack, ui_intent, ui_source_spec, ui_source_context)
    ui_flow_plan = derive_ui_flow_plan(case_pack, ui_binding_map)
    case_pack = apply_ui_binding(case_pack, ui_binding_map)
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
    case_runs, raw_output = execute_cases(workspace_root, output_root, action, case_pack, script_pack, environment, evidence_root, patch_context)
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
    return {
        "refs": refs,
        "case_pack": case_pack,
        "script_pack": script_pack,
        "case_runs": case_runs,
        "raw_output": raw_output,
        "context": context,
        "ui_intent": ui_intent,
        "ui_source_context": ui_source_context,
        "ui_binding_map": ui_binding_map,
        "ui_flow_plan": ui_flow_plan,
        "case_meta": case_meta,
        "outcome": outcome,
        "coverage_summary": outcome.get("coverage_summary", {}),
    }


def _promote_round_artifacts(workspace_root: Path, source_refs: dict[str, str], target_refs: dict[str, str]) -> None:
    for key in (
        "resolved_ssot_context_ref",
        "ui_intent_ref",
        "ui_source_context_ref",
        "ui_binding_map_ref",
        "ui_flow_plan_ref",
        "test_case_pack_ref",
        "test_case_pack_meta_ref",
    ):
        source_ref = source_refs.get(key, "")
        target_ref = target_refs.get(key, "")
        if not source_ref or not target_ref:
            continue
        source_path = canonical_to_path(source_ref, workspace_root)
        target_path = canonical_to_path(target_ref, workspace_root)
        if not source_path.exists():
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


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
        if len(tokens) > 1 and tokens[1] in {"-c", "/c"}:
            return command_entry, True, "unsupported", "coverage-enabled execution does not support python -c; use a script or module entry"
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
        if isinstance(run_command, list) and bool(environment.get("coverage_branch_enabled")):
            run_command = [*run_command[:4], "--branch", *run_command[4:]]
        ensure(not coverage_reason, "PRECONDITION_FAILED", coverage_reason)
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
    patch_context: PatchContext | None = None,
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
    case_runs: list[dict[str, Any]] = []
    for case, item in zip(case_pack["cases"], bindings):
        if case.get("_patch_blocked"):
            # D-17: Skip blocked items, set status to blocked
            case_runs.append({
                "case_id": case["case_id"],
                "status": "blocked",
                "block_reason": case.get("_patch_block_reason", "TEST_BLOCKED"),
                "actual": "not_executed",
                "stdout_ref": "",
                "stderr_ref": "",
                "coverage_status": "disabled",
                "diagnostics": [case.get("_patch_block_reason", "")],
            })
            continue
        case_runs.append(execute_case(workspace_root, item["command_entry"], case, environment, evidence_root))
    return case_runs, {"framework": "shell", "results": case_runs}


def run_narrow_execution(
    workspace_root: Path,
    trace: dict[str, Any],
    request_id: str,
    action: str,
    test_set: dict[str, Any],
    environment: dict[str, Any],
    payload: dict[str, Any] | None = None,
    patch_context: PatchContext | None = None,
) -> dict[str, str]:
    payload = payload or {}
    command_entry = str(environment.get("command_entry", environment.get("runner_command", "")))
    if action != "test-exec-web-e2e":
        ensure(command_entry, "PRECONDITION_FAILED", "execution command is required")
    run_slug = slugify(f"{action}-{request_id}")
    output_root = workspace_root / "artifacts" / "active" / "qa" / "executions" / run_slug
    coverage_mode = str(environment.get("coverage_mode", "")).strip().lower()
    qualification_budget = _qualification_budget(test_set, environment)
    max_expansion_rounds = _qualification_max_rounds(test_set, environment)
    if coverage_mode != "qualification":
        case_pack = build_test_case_pack(test_set, environment)
        round_result = _execute_round(workspace_root, trace, request_id, action, test_set, environment, payload, case_pack, output_root, patch_context)
        return {**round_result["refs"], **round_result["outcome"]}

    round0_root = output_root / "qualification-rounds" / "round-0"
    round0_pack = build_test_case_pack(
        test_set,
        environment,
        projection_mode="minimal_projection",
        qualification_budget=qualification_budget,
        max_expansion_rounds=max_expansion_rounds,
        qualification_stop_reason="minimal_projection_only",
        expansion_round=0,
    )
    round0_result = _execute_round(workspace_root, trace, request_id, action, test_set, environment, payload, round0_pack, round0_root, patch_context)
    stop_reason = _qualification_stop_reason(test_set, round0_result["coverage_summary"], qualification_budget)
    lineage = [_qualification_lineage_entry(0, round0_pack, round0_result["coverage_summary"], stop_reason)]
    final_result = round0_result
    final_pack = dict(round0_pack)
    stable_expansion_targets: list[str] = []
    round_index = 0

    while _should_expand_qualification(
        test_set,
        final_result["coverage_summary"],
        max(0, qualification_budget - round_index),
        round_index,
        max_expansion_rounds,
    ):
        round_index += 1
        round_root = output_root / "qualification-rounds" / f"round-{round_index}"
        expansion_targets = _coverage_expansion_targets(workspace_root, final_result["refs"])
        if expansion_targets:
            stable_expansion_targets = expansion_targets
        elif stable_expansion_targets:
            expansion_targets = stable_expansion_targets
        round_pack = build_test_case_pack(
            test_set,
            environment,
            projection_mode="qualification_expansion",
            qualification_lineage=lineage,
            qualification_budget=qualification_budget,
            qualification_round=round_index,
            qualification_revision=round_index,
            max_expansion_rounds=max_expansion_rounds,
            qualification_stop_reason="coverage_feedback_applied",
            expansion_round=round_index,
            expansion_targets=expansion_targets,
        )
        round_result = _execute_round(workspace_root, trace, request_id, action, test_set, environment, payload, round_pack, round_root, patch_context)
        stop_reason = _qualification_stop_reason(
            test_set,
            round_result["coverage_summary"],
            max(0, qualification_budget - round_index),
        )
        lineage = lineage + [_qualification_lineage_entry(round_index, round_pack, round_result["coverage_summary"], stop_reason)]
        final_result = round_result
        final_pack = dict(round_pack)

    final_pack["qualification_lineage"] = lineage
    final_pack["expansion_stop_reason"] = stop_reason
    final_pack["qualification_max_expansion_rounds"] = max_expansion_rounds

    if round_index == 0:
        final_refs = build_execution_refs(output_root, workspace_root)
        _promote_round_artifacts(workspace_root, round0_result["refs"], final_refs)
        _write_yaml(workspace_root / final_refs["test_case_pack_ref"], final_pack)
        write_json(workspace_root / final_refs["test_case_pack_meta_ref"], build_freeze_meta("test_case_pack", final_pack))
        final_outcome = finalize_execution_outputs(
            workspace_root,
            output_root,
            final_refs,
            trace,
            final_pack,
            round0_result["script_pack"],
            environment,
            round0_result["case_runs"],
            round0_result["raw_output"],
            build_freeze_meta,
        )
        return {**final_refs, **final_outcome}

    final_refs = build_execution_refs(output_root, workspace_root)
    _promote_round_artifacts(workspace_root, final_result["refs"], final_refs)
    _write_yaml(workspace_root / final_refs["test_case_pack_ref"], final_pack)
    write_json(workspace_root / final_refs["test_case_pack_meta_ref"], build_freeze_meta("test_case_pack", final_pack))
    final_outcome = finalize_execution_outputs(
        workspace_root,
        output_root,
        final_refs,
        trace,
        final_pack,
        final_result["script_pack"],
        environment,
        final_result["case_runs"],
        final_result["raw_output"],
        build_freeze_meta,
    )
    return {**final_refs, **final_outcome}
