#!/usr/bin/env python3
"""
Workstream helpers for tech-to-impl.
"""

from __future__ import annotations

from typing import Any

from tech_to_impl_common import ensure_list
from tech_to_impl_workstream_analysis import assess_workstreams, is_execution_runner_package


def _classify_unit_surface(path: str, detail: str, assessment: dict[str, Any]) -> str:
    text = f"{path} {detail}".lower()
    if any(marker in text for marker in ["migration", "cutover", "rollout", "rollback", "fallback", "compat", "迁移", "切换", "回滚", "灰度"]):
        return "migration"
    if any(marker in text for marker in ["ui", "frontend", "front-end", "page", "screen", "view", "panel", "home/", "页面", "前端", "交互"]):
        return "frontend"
    if assessment.get("frontend_required") and not assessment.get("backend_required"):
        return "frontend"
    return "backend"


def _acceptance_refs(checkpoints: list[dict[str, str]] | None, fallback: list[str]) -> list[str]:
    refs = [str(item.get("ref") or "").strip() for item in checkpoints or [] if str(item.get("ref") or "").strip()]
    return [ref for ref in fallback if ref in refs] or refs[:1] or fallback[:1]


def implementation_steps(
    feature: dict[str, Any],
    assessment: dict[str, Any],
    package: Any,
    checkpoints: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    runner_package = is_execution_runner_package(feature, package)
    units = package.tech_json.get("tech_design", {}).get("implementation_unit_mapping") or []
    unit_rows = []
    for raw in units:
        cleaned = str(raw).replace("`", "")
        if ":" in cleaned:
            left, detail = cleaned.split(":", 1)
        else:
            left, detail = cleaned, cleaned
        if "(" in left and ")" in left:
            path = left.split("(", 1)[0].strip()
        else:
            path = left.strip()
        unit_rows.append(
            {
                "path": path,
                "detail": detail.strip(),
                "surface": _classify_unit_surface(path, detail, assessment),
            }
        )
    unit_preview = ", ".join(units[:4]) or "the frozen TECH implementation units"
    interface_preview = "; ".join(ensure_list(package.tech_json.get("tech_design", {}).get("interface_contracts"))[:2])
    sequence_preview = "; ".join(ensure_list(package.tech_json.get("tech_design", {}).get("main_sequence"))[:3])
    integration_preview = "; ".join(ensure_list(package.tech_json.get("tech_design", {}).get("integration_points"))[:2])
    frontend_paths = [row["path"] for row in unit_rows if row["surface"] == "frontend"]
    backend_paths = [row["path"] for row in unit_rows if row["surface"] == "backend"]
    migration_paths = [row["path"] for row in unit_rows if row["surface"] == "migration"]

    steps: list[dict[str, Any]] = [
        {
            "task_id": "TASK-001",
            "title": "Freeze upstream refs, repo placement, and touch set",
            "workstream": "cross-cutting",
            "depends_on": [],
            "parallel_group": "setup",
            "outputs": ["frozen-upstream-refs", "touch-set-freeze", "execution-contract-snapshot"],
            "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001"]),
            "work": f"Lock feat_ref, tech_ref, optional arch/api refs, and the concrete touch set before coding: {unit_preview}.",
            "done_when": "The implementation entry references frozen upstream objects only, the concrete file/module touch set is explicit, and repo landing zones are frozen before coding starts.",
        }
    ]
    if assessment["frontend_required"]:
        steps.append(
            {
                "task_id": "TASK-002",
                "title": "Implement frozen frontend entry/exit surface",
                "workstream": "frontend",
                "depends_on": ["TASK-001"],
                "parallel_group": "frontend",
                "outputs": frontend_paths[:4] or ["frontend-surface"],
                "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                "work": "Apply the selected UI/page/component changes, wire entry/exit behavior, and keep interaction behavior aligned to the frozen TECH/API boundary.",
                "done_when": "Frontend changes are wired, bounded to the selected scope, and preserve the frozen UI entry/exit contract without bypassing state or guard rules.",
            }
        )
    if assessment["backend_required"]:
        steps.append(
            {
                "task_id": "TASK-003" if assessment["frontend_required"] else "TASK-002",
                "title": "Implement frozen runtime, state, and interface units",
                "workstream": "backend",
                "depends_on": ["TASK-001"],
                "parallel_group": "backend",
                "outputs": backend_paths[:4] or ["runtime-units", "interface-hooks"],
                "acceptance_refs": _acceptance_refs(checkpoints, ["AC-001", "AC-002"]),
                "work": (
                    f"Update only the declared runtime units: {unit_preview}. "
                    f"Honor the frozen contracts and sequence: {interface_preview or 'use upstream interface contracts'}."
                ),
                "done_when": "The listed runtime/state/interface units implement the upstream state transitions, contract hooks, and evidence points without redefining ownership or decision semantics.",
            }
        )
    if assessment["migration_required"]:
        migration_task_id = f"TASK-{len(steps) + 1:03d}"
        steps.append(
            {
                "task_id": migration_task_id,
                "title": "Implement migration, compat, and rollback controls",
                "workstream": "migration",
                "depends_on": ["TASK-001"] + ([steps[-1]["task_id"]] if steps else []),
                "parallel_group": "migration",
                "outputs": migration_paths[:4] or ["migration-cutover-plan", "rollback-guardrails"],
                "acceptance_refs": _acceptance_refs(checkpoints, ["AC-004", "AC-003"]),
                "work": integration_preview or "Define compat-mode, rollout, rollback, or cutover sequencing needed to land the change safely.",
                "done_when": "Migration prerequisites, guardrails, fallback actions, and rollback sequencing are explicit enough for downstream execution and are tied to named touch points.",
            }
        )
    integration_task_id = f"TASK-{len(steps) + 1:03d}"
    steps.append(
        {
            "task_id": integration_task_id,
            "title": "Integrate flow boundaries and collect acceptance evidence",
            "workstream": "integration",
            "depends_on": [step["task_id"] for step in steps if step["task_id"] != "TASK-001"],
            "parallel_group": "integration",
            "outputs": ["integration-hooks-wired", "acceptance-evidence", "smoke-gate-ready-inputs"],
            "acceptance_refs": _acceptance_refs(checkpoints, ["AC-002", "AC-003", "AC-004"]),
            "work": "Wire the concrete sequence, integration hooks, and acceptance evidence into the package handoff. " + (sequence_preview or "Follow the frozen upstream runtime sequence."),
            "done_when": (
                "The integrated flow preserves the frozen entry/exit sequence, exposes the required evidence for each acceptance check, and can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries."
                if not runner_package
                else "The package can enter template.dev.feature_delivery_l2 while preserving the frozen execution-runner lifecycle and operator/runtime boundary."
            ),
        }
    )
    handoff_task_id = f"TASK-{len(steps) + 1:03d}"
    steps.append(
        {
            "task_id": handoff_task_id,
            "title": "Assemble smoke gate input and downstream handoff",
            "workstream": "evidence",
            "depends_on": [integration_task_id],
            "parallel_group": "finalize",
            "outputs": ["dev-evidence-plan.json", "smoke-gate-subject.json", "handoff-to-feature-delivery.json"],
            "acceptance_refs": [str(item.get("ref") or "").strip() for item in checkpoints or [] if str(item.get("ref") or "").strip()],
            "work": "Finalize acceptance coverage, smoke-gate inputs, and downstream handoff artifacts without inventing new scope or rewriting upstream truth.",
            "done_when": "Each acceptance check maps to concrete task output and evidence, and downstream execution can start without reopening upstream FEAT/TECH docs.",
        }
    )
    return steps


def acceptance_checkpoints(
    feature: dict[str, Any],
    package: Any | None = None,
    assessment: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    if package is not None:
        runner_package = is_execution_runner_package(feature, package)
        units = package.tech_json.get("tech_design", {}).get("implementation_unit_mapping") or []
        unit_paths = ", ".join(units[:4]) or "the declared runtime units"
        contracts = ensure_list(package.tech_json.get("tech_design", {}).get("interface_contracts"))
        main_sequence = ensure_list(package.tech_json.get("tech_design", {}).get("main_sequence"))
        integration_points = ensure_list(package.tech_json.get("tech_design", {}).get("integration_points"))
        migration_required = bool((assessment or {}).get("migration_required"))
        observable_outcomes = ensure_list((feature.get("acceptance_and_testability") or {}).get("observable_outcomes"))

        checkpoints = [
            {
                "ref": "AC-001",
                "scenario": "Frozen touch set is implemented without design drift.",
                "expectation": f"The declared touch set is updated and evidence-backed: {unit_paths}.",
            },
            {
                "ref": "AC-002",
                "scenario": "Frozen contracts and runtime sequence execute through the implementation entry.",
                "expectation": "Implementation evidence proves the frozen contract hooks and state transitions are wired. "
                + (contracts[0] if contracts else "Use the upstream interface contracts without shadow redefinition."),
            },
            {
                "ref": "AC-003",
                "scenario": (
                    "Execution-runner lifecycle remains boundary-safe and ready for feature delivery."
                    if runner_package
                    else "Downstream handoff remains boundary-safe and ready for feature delivery."
                ),
                "expectation": (
                    "The implementation package preserves the frozen approve-to-ready-job / runner entry-control-intake / dispatch / feedback / observability boundary, "
                    "does not reinterpret the upstream execution-runner lifecycle, and hands off with smoke inputs ready."
                    if runner_package
                    else "The implementation package exposes only the frozen pending visibility / boundary handoff behavior, "
                    "keeps gate decision issuance / formal publication semantics out of scope, and hands off with smoke inputs ready."
                ),
            },
        ]
        if main_sequence:
            checkpoints[1]["expectation"] += f" Main sequence evidence covers: {'; '.join(main_sequence[:3])}."
        if integration_points:
            checkpoints[2]["expectation"] += f" Integration evidence covers: {'; '.join(integration_points[:2])}."
        if observable_outcomes:
            checkpoints[2]["expectation"] += f" Observable outcomes remain externally visible: {'; '.join(observable_outcomes[:2])}."
        if migration_required:
            checkpoints.append(
                {
                    "ref": "AC-004",
                    "scenario": "Migration and compat controls are explicit before execution.",
                    "expectation": "Rollback, compat-mode, and pending repair handling are explicit enough for downstream execution.",
                }
            )
            if observable_outcomes:
                checkpoints[-1]["expectation"] += f" Migration outcomes remain externally visible: {'; '.join(observable_outcomes[:2])}."
        return checkpoints

    checkpoints: list[dict[str, str]] = []
    for index, check in enumerate(feature.get("acceptance_checks") or [], start=1):
        if not isinstance(check, dict):
            continue
        checkpoints.append(
            {
                "ref": f"AC-{index:03d}",
                "scenario": normalize_boundary_text(str(check.get("scenario") or "").strip()) or f"acceptance-{index}",
                "expectation": normalize_boundary_text(str(check.get("then") or "").strip()) or "Expectation must be confirmed during execution.",
            }
        )
    if checkpoints:
        return checkpoints

    acceptance = feature.get("acceptance_and_testability") or {}
    criteria = ensure_list(acceptance.get("acceptance_criteria"))
    outcomes = ensure_list(acceptance.get("observable_outcomes"))
    authoritative_artifact = str((feature.get("product_objects_and_deliverables") or {}).get("authoritative_output") or feature.get("authoritative_artifact") or "").strip()
    for index, criterion in enumerate(criteria, start=1):
        if outcomes:
            expectation = outcomes[min(index - 1, len(outcomes) - 1)]
        elif authoritative_artifact:
            expectation = f"{authoritative_artifact} 可被外部观察并作为唯一 authoritative result。"
        else:
            expectation = "该验收结果必须形成可外部观察的 authoritative outcome。"
        checkpoints.append(
            {
                "ref": f"AC-{index:03d}",
                "scenario": normalize_boundary_text(criterion.strip()) or f"acceptance-{index}",
                "expectation": normalize_boundary_text(str(expectation).strip()) or "Expectation must be confirmed during execution.",
            }
        )
    return checkpoints


STALE_REENTRY_RULE = "keeping approval and re-entry semantics outside this feat"


def normalize_boundary_text(text: str) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        return normalized
    if STALE_REENTRY_RULE in normalized.lower():
        return (
            "Submission completion only exposes authoritative handoff and pending visibility; "
            "decision-driven revise/retry routing stays in runtime while gate decision issuance and formal publication semantics remain outside this FEAT."
        )
    return normalized
