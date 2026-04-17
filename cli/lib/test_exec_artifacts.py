"""Artifact builders for governed test execution."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .patch_awareness import PatchAwarenessStatus, PatchContext

from .test_exec_case_expander import expand_requirement_cases
from .test_exec_fixture_planner import plan_fixtures
from .test_exec_script_mapper import map_scripts
from .test_exec_traceability import (
    normalize_coverage_matrix,
    normalize_functional_areas,
    normalize_logic_dimensions,
    normalize_state_model,
    summarize_case_traceability,
)

def _checksum(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def normalize_ui_source_spec(payload: dict[str, Any]) -> dict[str, Any]:
    explicit = payload.get("ui_source_spec", {})
    if not isinstance(explicit, dict):
        explicit = {}
    spec = {
        "codebase_ref": explicit.get("codebase_ref", payload.get("frontend_code_ref", "")),
        "runtime_ref": explicit.get("runtime_ref", payload.get("ui_runtime_ref", "")),
        "prototype_ref": explicit.get("prototype_ref", payload.get("ui_prototype_ref", "")),
    }
    return spec


def resolve_ssot_context(test_set: dict[str, Any], environment: dict[str, Any], ui_source_spec: dict[str, Any]) -> dict[str, Any]:
    functional_areas = normalize_functional_areas(test_set)
    logic_dimensions = normalize_logic_dimensions(test_set)
    state_model = normalize_state_model(test_set)
    coverage_matrix = normalize_coverage_matrix(test_set)
    return {
        "artifact_type": "resolved_ssot_context",
        "test_set_id": test_set.get("test_set_id", test_set.get("id", "")),
        "execution_modality": environment.get("execution_modality", ""),
        "title": test_set.get("title", ""),
        "source_refs": test_set.get("source_refs", []),
        "governing_adrs": test_set.get("governing_adrs", []),
        "environment_assumptions": test_set.get("environment_assumptions", []),
        "coverage_scope": test_set.get("coverage_scope", []),
        "recommended_coverage_scope_name": test_set.get("recommended_coverage_scope_name", []),
        "functional_areas": functional_areas,
        "logic_dimensions": logic_dimensions,
        "state_model": state_model,
        "coverage_matrix": coverage_matrix,
        "feature_owned_code_paths": test_set.get("feature_owned_code_paths", []),
        "coverage_goal": test_set.get("coverage_goal", {}),
        "branch_families": test_set.get("branch_families", []),
        "expansion_hints": test_set.get("expansion_hints", []),
        "qualification_budget": test_set.get("qualification_budget", environment.get("qualification_budget")),
        "max_expansion_rounds": test_set.get("max_expansion_rounds", environment.get("max_expansion_rounds")),
        "qualification_expectation": test_set.get("qualification_expectation", ""),
        "risk_focus": test_set.get("risk_focus", []),
        "ui_source_spec": ui_source_spec,
        "environment_contract": {
            "execution_modality": environment.get("execution_modality", ""),
            "workdir": environment.get("workdir", "."),
            "timeout_seconds": int(environment.get("timeout_seconds", 30)),
            "base_url": environment.get("base_url"),
            "browser": environment.get("browser"),
            "headless": environment.get("headless"),
            "has_command_entry": bool(environment.get("command_entry") or environment.get("runner_command")),
            "coverage_enabled": bool(environment.get("coverage_enabled")),
            "coverage_scope_name": environment.get("coverage_scope_name", []),
            "coverage_include": environment.get("coverage_include", []),
            "coverage_scope_origin": environment.get("coverage_scope_origin", "environment"),
        },
    }


def _qualification_plan(test_set: dict[str, Any], environment: dict[str, Any] | None = None) -> dict[str, Any]:
    environment = environment or {}
    qualification_budget = environment.get("qualification_budget", test_set.get("qualification_budget"))
    return {
        "coverage_goal": test_set.get("coverage_goal", {}),
        "branch_families": test_set.get("branch_families", []),
        "expansion_hints": test_set.get("expansion_hints", []),
        "qualification_budget": qualification_budget,
        "max_expansion_rounds": environment.get("max_expansion_rounds", test_set.get("max_expansion_rounds")),
        "qualification_expectation": test_set.get("qualification_expectation", ""),
        "coverage_mode": environment.get("coverage_mode", ""),
        "coverage_branch_enabled": bool(environment.get("coverage_branch_enabled")),
    }


def build_test_case_pack(
    test_set: dict[str, Any],
    environment: dict[str, Any] | None = None,
    *,
    projection_mode: str | None = None,
    qualification_lineage: list[dict[str, Any]] | None = None,
    qualification_budget: int | None = None,
    qualification_round: int = 0,
    qualification_revision: int = 0,
    max_expansion_rounds: int | None = None,
    qualification_stop_reason: str | None = None,
    expansion_round: int = 0,
    expansion_targets: list[str] | None = None,
) -> dict[str, Any]:
    environment = environment or {}
    environment_mode = str(environment.get("coverage_mode", "")).strip().lower()
    projection_mode = projection_mode or ("qualification_expansion" if environment_mode == "qualification" else "minimal_projection")
    lineage = qualification_lineage or []
    budget = qualification_budget if qualification_budget is not None else environment.get("qualification_budget", test_set.get("qualification_budget", 1))
    max_rounds = max_expansion_rounds if max_expansion_rounds is not None else environment.get("max_expansion_rounds", test_set.get("max_expansion_rounds"))
    case_pack = expand_requirement_cases(
        test_set,
        environment,
        projection_mode=projection_mode,
        qualification_round=max(1, expansion_round or 1),
        qualification_lineage=lineage,
        qualification_budget=budget,
        max_expansion_rounds=max_rounds,
        expansion_targets=expansion_targets,
    )
    stop_reason = qualification_stop_reason
    if stop_reason is None:
        stop_reason = (
            "branch_families_exhausted"
            if projection_mode == "qualification_expansion" and len(case_pack.get("cases", [])) > len(test_set.get("test_units", []))
            else "minimal_projection_only"
        )
    case_pack["qualification_lineage"] = lineage
    case_pack["qualification_budget"] = budget
    case_pack["qualification_max_expansion_rounds"] = max_rounds
    case_pack["qualification_revision"] = qualification_revision if projection_mode == "qualification_expansion" else 0
    case_pack["expansion_round"] = expansion_round if projection_mode == "qualification_expansion" else 0
    case_pack["expansion_stop_reason"] = stop_reason
    case_pack["traceability_summary"] = summarize_case_traceability(case_pack.get("cases", []))
    return case_pack


def build_script_pack(action: str, environment: dict[str, Any], case_pack: dict[str, Any], ui_source_spec: dict[str, Any]) -> dict[str, Any]:
    test_set_proxy = {
        "test_set_id": case_pack.get("source_test_set_id", ""),
        "execution_modality": case_pack.get("execution_modality", ""),
        "state_model": case_pack.get("state_model", []),
    }
    fixture_plan = plan_fixtures(test_set_proxy, case_pack, environment)
    script_pack = map_scripts(test_set_proxy, case_pack, environment)
    script_pack["runner_config"]["ui_source_spec"] = ui_source_spec
    script_pack["fixture_plan"] = fixture_plan
    for binding in script_pack.get("bindings", []):
        binding["page_path"] = next((case.get("page_path", "") for case in case_pack.get("cases", []) if case.get("case_id") == binding.get("case_id")), "")
        binding["expected_url"] = next((case.get("expected_url", "") for case in case_pack.get("cases", []) if case.get("case_id") == binding.get("case_id")), "")
        binding["expected_text"] = next((case.get("expected_text", "") for case in case_pack.get("cases", []) if case.get("case_id") == binding.get("case_id")), "")
        binding["ui_step_count"] = next((len(case.get("ui_steps", [])) for case in case_pack.get("cases", []) if case.get("case_id") == binding.get("case_id")), 0)
    return script_pack


def build_freeze_meta(artifact_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    count = len(payload.get("cases", payload.get("bindings", [])))
    return {
        "artifact_type": f"{artifact_type}_meta",
        "status": "frozen",
        "item_count": count,
        "checksum": _checksum(payload),
    }


def render_report(summary: dict[str, Any], compliance: dict[str, Any], case_results: list[dict[str, Any]]) -> str:
    lines = [
        "# Test Report",
        "",
        f"- run_status: {summary['run_status']}",
        f"- compliance_status: {compliance['status']}",
        f"- passed: {summary['passed']}",
        f"- failed: {summary['failed']}",
        f"- blocked: {summary['blocked']}",
        f"- invalid: {summary['invalid']}",
        f"- not_executed: {summary['not_executed']}",
    ]
    coverage = summary.get("coverage") or {}
    if coverage:
        lines.extend(
            [
                f"- coverage_status: {coverage.get('status')}",
                f"- coverage_line_rate_percent: {coverage.get('line_rate_percent')}",
                f"- coverage_covered_lines: {coverage.get('covered_lines')}",
                f"- coverage_num_statements: {coverage.get('num_statements')}",
                f"- coverage_scope: {', '.join(coverage.get('scope') or [])}",
                f"- coverage_scope_origin: {coverage.get('scope_origin')}",
            ]
        )
    if summary.get("projection_mode"):
        lines.append(f"- projection_mode: {summary.get('projection_mode')}")
    if summary.get("generation_mode"):
        lines.append(f"- generation_mode: {summary.get('generation_mode')}")
    if "expansion_round" in summary:
        lines.append(f"- expansion_round: {summary.get('expansion_round')}")
    if "qualification_budget" in summary:
        lines.append(f"- qualification_budget: {summary.get('qualification_budget')}")
    if summary.get("expansion_stop_reason"):
        lines.append(f"- expansion_stop_reason: {summary.get('expansion_stop_reason')}")
    traceability = summary.get("traceability") or {}
    if traceability:
        lines.extend(
            [
                f"- functional_areas_covered: {len(traceability.get('functional_area_traceability', []))}",
                f"- acceptances_covered: {len(traceability.get('acceptance_traceability', []))}",
                f"- risks_covered: {len(traceability.get('risk_traceability', []))}",
            ]
        )
    lines.extend(
        [
            "",
            "## Traceability",
        ]
    )
    for item in traceability.get("functional_area_traceability", []):
        lines.append(f"- area {item['key']}: {len(item.get('case_ids', []))} cases")
    if traceability:
        lines.extend(["", "## Case Results"])
    else:
        lines.extend(["", "## Case Results"])
    for item in case_results:
        lines.append(f"- {item['case_id']}: {item['status']} ({item['actual']})")
    return "\n".join(lines) + "\n"


def resolve_patch_context(
    workspace_root: Path | str,
    feat_ref: str = "",
    *,
    summary_budget: int = 5,
) -> PatchContext:
    """Scan workspace for patch-related artifacts and return a minimal PatchContext.

    Uses ``git diff`` / ``git log`` to identify patches applied since the last
    known baseline, falling back to file-system markers when git history is
    unavailable.

    Parameters
    ----------
    workspace_root : Path | str
        Root of the workspace to scan.
    feat_ref : str
        Optional feature reference to scope the scan.
    summary_budget : int
        Maximum number of patches to return with full detail (default 5).
        Beyond this budget only index-level summaries are included.

    Returns
    -------
    PatchContext
        Frozen dataclass containing patch discovery results.
    """
    root = Path(str(workspace_root)).resolve()

    patches: list[dict[str, Any]] = []
    none_found = False

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--name-status", "-n", str(summary_budget + 5)],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=10,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            current_hash: str | None = None
            for line in result.stdout.splitlines():
                stripped = line.strip()
                if not stripped:
                    current_hash = None
                    continue
                parts = stripped.split(None, 1)
                if len(parts) == 1 and len(parts[0]) >= 7:
                    current_hash = parts[0]
                    continue
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[1]
                    patch_entry: dict[str, Any] = {
                        "status": status,
                        "file_path": file_path,
                        "change_class": _classify_change(file_path),
                        "patch_status": PatchAwarenessStatus.APPLIED.value,
                    }
                    if current_hash:
                        patch_entry["commit"] = current_hash
                    patches.append(patch_entry)
        else:
            none_found = True
    except (subprocess.TimeoutExpired, OSError):
        none_found = True

    if not patches and not none_found:
        none_found = True

    budgeted_patches = patches[:summary_budget]
    if len(patches) > summary_budget:
        budgeted_patches.append({"truncated": True, "remaining_count": len(patches) - summary_budget})

    return PatchContext(
        patches_found=budgeted_patches,
        none_found=none_found,
        scan_path=str(root),
        scan_ref=feat_ref,
        total_count=len(patches),
        summary_budget=summary_budget,
    )


def _classify_change(file_path: str) -> str:
    """Classify a changed file into a ChangeClass bucket."""
    fp = file_path.lower()
    if any(fp.startswith(prefix) for prefix in ("cli/lib/patch_schema", "cli/lib/patch_context", "cli/lib/patch_")):
        return "schema"
    if any(prefix in fp for prefix in ("api", "endpoint", "route")):
        return "api"
    if any(prefix in fp for prefix in ("ui", "frontend", "component")):
        return "ui"
    if any(prefix in fp for prefix in ("config", "settings", "env")):
        return "config"
    if any(prefix in fp for prefix in ("infra", "docker", "deploy")):
        return "infra"
    if fp.endswith((".md", ".txt", ".rst")):
        return "doc"
    if any(prefix in fp for prefix in ("test", "spec")):
        return "test"
    return "other"
