#!/usr/bin/env python3
"""
Derivation helpers for the lite-native tech-to-impl runtime.
"""

from __future__ import annotations

import re
from typing import Any

from tech_to_impl_common import ensure_list, normalize_semantic_lock, unique_strings
from tech_to_impl_workstreams import STALE_REENTRY_RULE, acceptance_checkpoints, assess_workstreams, implementation_steps



















def build_refs(package: Any) -> dict[str, str | None]:
    tech_ref = package.tech_ref
    impl_ref = tech_ref.replace("TECH-", "IMPL-", 1) if tech_ref.startswith("TECH-") else f"IMPL-{package.feat_ref}"
    return {
        "feat_ref": package.feat_ref,
        "tech_ref": tech_ref,
        "impl_ref": impl_ref,
        "arch_ref": package.arch_ref,
        "api_ref": package.api_ref,
    }


def tech_design_payload(package: Any) -> dict[str, Any]:
    payload = package.tech_json.get("tech_design") or {}
    return payload if isinstance(payload, dict) else {}


def tech_list(package: Any, key: str) -> list[str]:
    return ensure_list(tech_design_payload(package).get(key))


def _strip_inline_markup(text: str) -> str:
    return text.replace("`", "").replace("**", "").strip()


def implementation_units(package: Any) -> list[dict[str, str]]:
    units: list[dict[str, str]] = []
    for raw in tech_list(package, "implementation_unit_mapping"):
        cleaned = _strip_inline_markup(raw)
        match = re.match(r"(?P<path>[^(:：]+?)\s*\((?P<mode>[^)]+)\)\s*[:：]\s*(?P<detail>.+)", cleaned)
        if match:
            units.append(
                {
                    "path": match.group("path").strip(),
                    "mode": match.group("mode").strip(),
                    "detail": match.group("detail").strip(),
                }
            )
            continue
        units.append({"path": cleaned, "mode": "touch", "detail": cleaned})
    return units


def filtered_implementation_rules(package: Any) -> list[str]:
    rules = tech_list(package, "implementation_rules")
    filtered: list[str] = []
    replaced_stale_rule = False
    for rule in rules:
        if STALE_REENTRY_RULE in rule.lower():
            replaced_stale_rule = True
            continue
        filtered.append(rule)
    if replaced_stale_rule:
        filtered.append(
            "Submission completion only exposes authoritative handoff and pending visibility; "
            "decision-driven revise/retry routing stays in runtime while gate decision issuance and formal publication semantics remain outside this FEAT."
        )
    return unique_strings(filtered)


def normalize_collaboration_boundary_text(text: str) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        return normalized
    if STALE_REENTRY_RULE in normalized.lower():
        return (
            "Submission completion only exposes authoritative handoff and pending visibility; "
            "decision-driven revise/retry routing stays in runtime while gate decision issuance and formal publication semantics remain outside this FEAT."
        )
    return normalized








def implementation_scope(feature: dict[str, Any], package: Any) -> list[str]:
    items = [
        f"{unit['path']} ({unit['mode']}): {unit['detail']}"
        for unit in implementation_units(package)[:5]
    ]
    if not items:
        items = ensure_list(feature.get("scope"))[:4]
    items.extend(tech_list(package, "integration_points")[:2])
    return unique_strings(items)[:6]




def risk_items(feature: dict[str, Any], assessment: dict[str, Any], package: Any) -> list[str]:
    items = (
        tech_list(package, "exception_and_compensation")[:3]
        + ensure_list(feature.get("constraints"))[:2]
        + ensure_list(feature.get("dependencies"))[:2]
    )
    if assessment["migration_required"]:
        items.append("Migration or cutover requires an explicit rollback or compat-mode path.")
    return unique_strings(items)[:6]


def deliverable_files(assessment: dict[str, Any]) -> list[str]:
    deliverables = [
        "impl-bundle.md",
        "impl-bundle.json",
        "impl-task.md",
        "upstream-design-refs.json",
        "integration-plan.md",
        "dev-evidence-plan.json",
        "smoke-gate-subject.json",
        "impl-review-report.json",
        "impl-acceptance-report.json",
        "impl-defect-list.json",
        "handoff-to-feature-delivery.json",
        "execution-evidence.json",
        "supervision-evidence.json",
    ]
    if assessment["frontend_required"]:
        deliverables.append("frontend-workstream.md")
    if assessment["backend_required"]:
        deliverables.append("backend-workstream.md")
    if assessment["migration_required"]:
        deliverables.append("migration-cutover-plan.md")
    return deliverables


def workstream_required_inputs(assessment: dict[str, Any]) -> list[str]:
    required = ["impl-task.md", "integration-plan.md", "dev-evidence-plan.json"]
    if assessment["frontend_required"]:
        required.append("frontend-workstream.md")
    if assessment["backend_required"]:
        required.append("backend-workstream.md")
    if assessment["migration_required"]:
        required.append("migration-cutover-plan.md")
    return required




def integration_plan_items(feature: dict[str, Any], assessment: dict[str, Any], package: Any) -> list[str]:
    items = tech_list(package, "integration_points")[:3] + ensure_list(feature.get("dependencies"))[:2]
    main_sequence = tech_list(package, "main_sequence")
    if main_sequence:
        items.append(f"按已冻结主时序接线：{'; '.join(main_sequence[:3])}。")
    if assessment["frontend_required"] and assessment["backend_required"]:
        items.append("Freeze frontend/backend integration order before smoke review.")
    if assessment["migration_required"]:
        items.append("Migration or cutover can execute only after implementation evidence is complete.")
    if not items:
        items.append("Single-surface execution still preserves one explicit integration checkpoint before smoke review.")
    return unique_strings(items)[:6]


def evidence_rows(
    feature: dict[str, Any],
    assessment: dict[str, Any],
    checkpoints: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    evidence_types: list[str] = []
    if assessment["frontend_required"]:
        evidence_types.append("frontend-verification")
    if assessment["backend_required"]:
        evidence_types.append("backend-verification")
    if assessment["migration_required"]:
        evidence_types.append("migration-verification")
    evidence_types.append("smoke-review-input")

    rows: list[dict[str, Any]] = []
    for checkpoint in checkpoints or acceptance_checkpoints(feature):
        rows.append(
            {
                "acceptance_ref": checkpoint["ref"],
                "scenario": checkpoint["scenario"],
                "evidence_types": evidence_types,
            }
        )
    return rows


def frontend_workstream_items(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("scope"))[:3]
    for checkpoint in acceptance_checkpoints(feature):
        items.append(f"{checkpoint['ref']}: {checkpoint['scenario']} -> {checkpoint['expectation']}")
    return unique_strings(items)[:5]


def backend_workstream_items(feature: dict[str, Any], package: Any) -> list[str]:
    items = [
        f"{unit['path']} ({unit['mode']}): {unit['detail']}"
        for unit in implementation_units(package)[:4]
    ]
    items.extend(tech_list(package, "interface_contracts")[:2])
    items.extend(tech_list(package, "exception_and_compensation")[:1])
    return unique_strings(items or ensure_list(feature.get("scope"))[:4])[:6]


def migration_plan_items(feature: dict[str, Any], package: Any) -> list[str]:
    del feature
    items = [
        item
        for item in tech_list(package, "integration_points") + tech_list(package, "exception_and_compensation")
        if any(marker in item.lower() for marker in ["compat", "cutover", "rollback", "fallback", "pending"])
    ]
    items.append("Define rollback or compat-mode behavior if the rollout path cannot complete cleanly.")
    return unique_strings(items)[:5]


def consistency_check(assessment: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    surface_selected = assessment["frontend_required"] or assessment["backend_required"]
    checks.append(
        {
            "name": "Execution surface selected",
            "passed": surface_selected,
            "detail": "At least one frontend or backend execution surface must be present.",
        }
    )
    if not surface_selected:
        issues.append("The selected TECH package exposes no executable frontend or backend workstream.")

    checks.append(
        {
            "name": "Migration is conditional",
            "passed": True,
            "detail": "Migration or cutover planning remains conditional instead of unconditional output.",
        }
    )

    return {
        "passed": not issues,
        "checks": checks,
        "issues": issues,
    }

