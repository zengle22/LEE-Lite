"""Artifact builders for governed test execution."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
import json
from pathlib import Path
from typing import Any

import yaml

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
from .patch_schema import resolve_patch_conflicts

def _checksum(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return sha1(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Patch context (D-10, D-11, D-20, D-22)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PatchContext:
    """Strict typed struct for Patch context injection (D-20)."""
    has_active_patches: bool
    validated_patches: list[dict[str, Any]]
    pending_patches: list[dict[str, Any]]
    conflict_resolution: dict[str, str]  # {coverage_id: "skip" | "warn" | "use_patch"}
    directory_hash: str  # TOCTOU protection (D-22)
    reviewed_at_latest: str | None  # Latest reviewed_at (D-21)
    feat_ref: str | None  # Associated FEAT reference


def _compute_patch_dir_hash(patches_dir: Path) -> str:
    """Compute deterministic SHA1 hash of Patch directory contents (D-22)."""
    files_data = []
    for patch_file in sorted(patches_dir.rglob("UXPATCH-*.yaml")):
        files_data.append((str(patch_file.relative_to(patches_dir)), patch_file.read_text(encoding="utf-8")))
    if not files_data:
        return ""
    return _checksum({"files": files_data})


def _latest_reviewed_at(patches: list[dict[str, Any]]) -> str | None:
    """Find the latest reviewed_at timestamp across all patches (D-21)."""
    timestamps = []
    for p in patches:
        reviewed_at = p.get("source", {}).get("reviewed_at")
        if reviewed_at:
            timestamps.append(reviewed_at)
    return max(timestamps) if timestamps else None


def _load_and_validate_patch(patch_file: Path) -> dict[str, Any] | None:
    """Load and validate a single Patch YAML file."""
    try:
        with open(patch_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None
        patch = data.get("experience_patch", data)
        if not isinstance(patch, dict):
            return None
        return patch
    except Exception:
        return None


def _build_conflict_resolution_map(patches: list[dict[str, Any]]) -> dict[str, str]:
    """Build per-coverage_id conflict resolution map from patches."""
    resolution: dict[str, str] = {}
    for patch in patches:
        test_impact = patch.get("test_impact", {})
        if test_impact:
            affected_routes = test_impact.get("affected_routes", [])
            for route in affected_routes:
                coverage_id = route.replace("/", ".")
                if patch.get("change_class") == "visual":
                    resolution[coverage_id] = "warn"
                else:
                    resolution[coverage_id] = "use_patch"
    return resolution


def resolve_patch_context(
    workspace_root: Path,
    feat_ref: str | None = None,
) -> PatchContext:
    """Scan experience-patches for active/resolved Patches (D-10, D-11).

    Mirrors resolve_ssot_context() pattern. Returns typed PatchContext
    suitable for injection into test execution runtime.

    TOCTOU protection: computes sha1 hash of Patch directory contents.
    """
    patches_dir = workspace_root / "ssot" / "experience-patches"
    if not patches_dir.exists():
        return PatchContext(
            has_active_patches=False,
            validated_patches=[],
            pending_patches=[],
            conflict_resolution={},
            directory_hash="",
            reviewed_at_latest=None,
            feat_ref=feat_ref,
        )

    validated: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    all_patches: list[dict[str, Any]] = []

    for feat_dir in sorted(patches_dir.iterdir()):
        if not feat_dir.is_dir():
            continue
        if feat_ref and feat_dir.name != feat_ref:
            continue
        for patch_file in sorted(feat_dir.glob("UXPATCH-*.yaml")):
            patch = _load_and_validate_patch(patch_file)
            if patch is None:
                continue
            all_patches.append(patch)
            status = patch.get("status", "")
            if status == "validated":
                validated.append(patch)
            elif status == "pending_backwrite":
                pending.append(patch)

    # D-22: TOCTOU hash
    dir_hash = _compute_patch_dir_hash(patches_dir)

    # D-15/D-16: Conflict resolution
    conflict_resolution = _build_conflict_resolution_map(all_patches)

    # D-21: Latest reviewed_at
    reviewed_at_latest = _latest_reviewed_at(all_patches)

    return PatchContext(
        has_active_patches=bool(all_patches),
        validated_patches=validated,
        pending_patches=pending,
        conflict_resolution=conflict_resolution,
        directory_hash=dir_hash,
        reviewed_at_latest=reviewed_at_latest,
        feat_ref=feat_ref,
    )


def mark_manifest_patch_affected(
    manifest_items: list[dict[str, Any]],
    patch_context: PatchContext,
) -> list[dict[str, Any]]:
    """Mark manifest items affected by Patches with test_impact (D-07, D-08).

    Per-item marking only — does NOT modify lifecycle_status state machine (D-06).
    Acceptance refs preserved (D-19): evidence_refs and mapped_case_ids are
    only appended to, never replaced.

    Args:
        manifest_items: List of manifest item dicts (from loaded manifest YAML)
        patch_context: Resolved PatchContext from resolve_patch_context()

    Returns:
        Updated list of manifest item dicts with patch_affected and patch_refs set.
    """
    # Collect patch IDs that have meaningful test_impact
    relevant_patch_ids: list[str] = []
    feat_ref_by_patch: dict[str, str] = {}

    for patch in patch_context.validated_patches + patch_context.pending_patches:
        test_impact = patch.get("test_impact")
        if not test_impact:
            continue
        # Skip visual Patches with no affected_routes
        if patch.get("change_class") == "visual" and not test_impact.get("affected_routes"):
            continue

        patch_id = patch["id"]
        relevant_patch_ids.append(patch_id)
        feat_ref_by_patch[patch_id] = patch.get("scope", {}).get("feat_ref", "")

    # Mark matching manifest items
    result: list[dict[str, Any]] = []
    for item in manifest_items:
        item_copy = dict(item)
        item_feat_ref = item.get("source_feat_ref", "")

        # Match on feat_ref (scope.feat_ref == item.source_feat_ref)
        matching_patches = [
            pid for pid, fr in feat_ref_by_patch.items()
            if fr == item_feat_ref
        ]

        if matching_patches:
            item_copy["patch_affected"] = True
            existing_refs = set(item_copy.get("patch_refs") or [])
            existing_refs.update(matching_patches)
            item_copy["patch_refs"] = sorted(existing_refs)

            # D-19: Preserve existing acceptance refs (only append, never replace)
            if "evidence_refs" in item:
                item_copy["evidence_refs"] = list(item["evidence_refs"])
            if "mapped_case_ids" in item:
                item_copy["mapped_case_ids"] = list(item["mapped_case_ids"])

        result.append(item_copy)

    return result


def create_manifest_items_for_new_scenarios(
    patch_context: PatchContext,
    manifest_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create new manifest items for new test case scenarios (D-09).

    When a Patch's test_impact indicates impacts_existing_testcases == false
    or test_targets contains new entries not already in manifest, create
    new manifest items with lifecycle_status: drafted.

    Args:
        patch_context: Resolved PatchContext from resolve_patch_context()
        manifest_items: Existing manifest item list (will be appended to)

    Returns:
        Updated manifest item list with new drafted items.
    """
    new_items: list[dict[str, Any]] = []

    for patch in patch_context.validated_patches + patch_context.pending_patches:
        test_impact = patch.get("test_impact")
        if not test_impact:
            continue

        # D-09: Check if new test scenarios are needed
        impacts_existing = test_impact.get("impacts_existing_testcases", True)
        test_targets = test_impact.get("test_targets", [])

        # New scenarios needed when:
        # 1. impacts_existing_testcases is false (new behavior not covered)
        # 2. test_targets has entries that don't map to existing manifest items
        if impacts_existing and not test_targets:
            continue  # Existing coverage sufficient, no new items needed

        # Determine feat_ref for the new item
        feat_ref = patch.get("scope", {}).get("feat_ref", "")

        # Build new manifest item(s) for each target
        for target in (test_targets or [feat_ref]):
            # Check if item already exists for this target
            existing_ids = {item.get("source_feat_ref") for item in manifest_items}
            if target in existing_ids and impacts_existing:
                continue  # Already covered

            patch_id = patch.get("id", "UNKNOWN")
            new_item: dict[str, Any] = {
                # Core identity (minimal for drafted item)
                "coverage_id": f"{patch_id}-{target}",
                "feature_id": feat_ref,
                "capability": patch.get("title", ""),
                "endpoint": target,
                "scenario_type": patch.get("change_class", "interaction"),
                "priority": "P2",  # Drafted items default to P2
                "source_feat_ref": feat_ref,
                # Coverage and mapping
                "dimensions_covered": [],
                "mapped_case_ids": [],
                # Lifecycle (D-09: new items start as drafted)
                "lifecycle_status": "drafted",
                "mapping_status": "pending",
                "evidence_status": "none",
                "waiver_status": "none",
                # Patch markers
                "patch_affected": True,
                "patch_refs": [patch_id],
                # Evidence and rerun tracking
                "evidence_refs": [],
                "rerun_count": 0,
                "last_run_id": None,
                "obsolete": False,
                "superseded_by": None,
            }
            new_items.append(new_item)

    # Append new items to the manifest list
    manifest_items.extend(new_items)
    return manifest_items


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
