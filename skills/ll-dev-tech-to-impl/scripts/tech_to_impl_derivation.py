#!/usr/bin/env python3
"""
Derivation helpers for the lite-native tech-to-impl runtime.
"""

from __future__ import annotations

import re
from typing import Any

from tech_to_impl_common import ensure_list, unique_strings


FRONTEND_KEYWORDS = [
    "ui",
    "ux",
    "page",
    "screen",
    "view",
    "frontend",
    "front-end",
    "页面",
    "交互",
    "前端",
    "文案",
]

BACKEND_KEYWORDS = [
    "backend",
    "service",
    "worker",
    "job",
    "api",
    "contract",
    "schema",
    "database",
    "storage",
    "queue",
    "event",
    "message",
    "gate",
    "workflow",
    "runtime",
    "path",
    "io",
    "registry",
    "后端",
    "服务",
    "接口",
    "契约",
    "数据库",
    "事件",
    "消息",
    "发布",
]

MIGRATION_KEYWORDS = [
    "migration",
    "cutover",
    "rollout",
    "fallback",
    "rollback",
    "compat",
    "切换",
    "迁移",
    "灰度",
    "回滚",
    "兼容",
]

NEGATION_MARKERS = ["不", "无", "without", "no ", "not ", "do not", "must not"]
GENERIC_MIGRATION_PHRASES = ["rollout_required", "adoption_e2e", "overlay"]
STALE_REENTRY_RULE = "keeping approval and re-entry semantics outside this feat"


def _string_segments(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        segments: list[str] = []
        for item in value:
            segments.extend(_string_segments(item))
        return segments
    if isinstance(value, dict):
        segments: list[str] = []
        for item in value.values():
            segments.extend(_string_segments(item))
        return segments
    return []


def feature_segments(feature: dict[str, Any]) -> list[str]:
    segments: list[str] = []
    for key in ["title", "goal", "axis_id", "slice_id", "track"]:
        value = str(feature.get(key) or "").strip()
        if value:
            segments.append(value)
    for key in [
        "scope",
        "constraints",
        "dependencies",
        "inputs",
        "processing",
        "outputs",
        "non_goals",
        "upstream_feat",
        "downstream_feat",
        "consumes",
        "produces",
    ]:
        segments.extend(ensure_list(feature.get(key)))
    for key in [
        "identity_and_scenario",
        "business_flow",
        "product_objects_and_deliverables",
        "collaboration_and_timeline",
        "acceptance_and_testability",
        "frozen_downstream_boundary",
        "dependency_kinds",
    ]:
        segments.extend(_string_segments(feature.get(key)))
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            segments.extend(
                [
                    str(check.get("scenario") or ""),
                    str(check.get("given") or ""),
                    str(check.get("when") or ""),
                    str(check.get("then") or ""),
                ]
            )
    return [segment for segment in segments if segment.strip()]


def implementation_surface_segments(feature: dict[str, Any], package: Any) -> list[str]:
    segments: list[str] = []
    for key in ["title", "goal", "axis_id", "slice_id", "track", "resolved_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            segments.append(value)

    for key in [
        "scope",
        "constraints",
        "dependencies",
        "inputs",
        "processing",
        "outputs",
        "upstream_feat",
        "downstream_feat",
        "consumes",
        "produces",
    ]:
        segments.extend(ensure_list(feature.get(key)))

    tech_design = package.tech_json.get("tech_design") or {}
    if isinstance(tech_design, dict):
        for key in [
            "design_focus",
            "implementation_rules",
            "module_plan",
            "implementation_strategy",
            "implementation_unit_mapping",
            "interface_contracts",
            "integration_points",
            "implementation_architecture",
            "state_model",
            "main_sequence",
            "exception_and_compensation",
        ]:
            segments.extend(_string_segments(tech_design.get(key)))
        carrier_view = tech_design.get("implementation_carrier_view") or {}
        if isinstance(carrier_view, dict):
            segments.extend(_string_segments(carrier_view.get("summary")))
            segments.extend(_string_segments(carrier_view.get("diagram")))
    return [segment for segment in segments if segment.strip()]


def _keyword_present(lowered: str, keyword: str) -> bool:
    ascii_keyword = keyword.isascii()
    if ascii_keyword and keyword.isalnum() and len(keyword) <= 3:
        return bool(re.search(rf"(?<![A-Za-z0-9_]){re.escape(keyword)}(?![A-Za-z0-9_])", lowered))
    if ascii_keyword and re.fullmatch(r"[A-Za-z0-9_-]+", keyword):
        return bool(re.search(rf"(?<![A-Za-z0-9_]){re.escape(keyword)}(?![A-Za-z0-9_])", lowered))
    return keyword in lowered


def keyword_hits_in_segments(segments: list[str], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    for segment in segments:
        lowered = segment.lower()
        if any(marker in lowered for marker in NEGATION_MARKERS):
            continue
        for keyword in keywords:
            if keyword in MIGRATION_KEYWORDS and any(phrase in lowered for phrase in GENERIC_MIGRATION_PHRASES):
                continue
            if _keyword_present(lowered, keyword) and keyword not in hits:
                hits.append(keyword)
    return hits


def keyword_hits(feature: dict[str, Any], keywords: list[str]) -> list[str]:
    return keyword_hits_in_segments(feature_segments(feature), keywords)


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
            "decision-driven revise/retry routing stays in runtime while formalization semantics remain outside this FEAT."
        )
    return unique_strings(filtered)


def assess_workstreams(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
    segments = implementation_surface_segments(feature, package)
    frontend_hits = keyword_hits_in_segments(segments, FRONTEND_KEYWORDS)
    backend_hits = keyword_hits_in_segments(segments, BACKEND_KEYWORDS)
    migration_hits = keyword_hits_in_segments(segments, MIGRATION_KEYWORDS)
    tech_surface_text = " ".join(
        tech_list(package, "implementation_unit_mapping")
        + tech_list(package, "integration_points")
        + tech_list(package, "interface_contracts")
    ).lower()
    tech_migration_text = " ".join(
        tech_list(package, "implementation_unit_mapping")
        + tech_list(package, "integration_points")
        + tech_list(package, "main_sequence")
        + tech_list(package, "exception_and_compensation")
    ).lower()
    explicit_frontend_surface = any(
        marker in tech_surface_text
        for marker in [
            "/ui/",
            "\\ui\\",
            "/frontend/",
            "\\frontend\\",
            "frontend",
            "front-end",
            "page",
            "screen",
            "view",
            "页面",
            "前端",
            "交互",
        ]
    )
    explicit_migration_surface = any(
        marker in tech_migration_text
        for marker in [
            "migration",
            "cutover",
            "rollout",
            "fallback",
            "rollback",
            "compat",
            "迁移",
            "切换",
            "回滚",
            "灰度",
        ]
    )

    frontend_rationale = (
        [f"Detected explicit UI or interaction surface: {', '.join(frontend_hits[:4])}."]
        if frontend_hits
        else ["No explicit UI/page/component implementation surface was detected."]
    )

    backend_rationale: list[str] = []
    if backend_hits:
        backend_rationale.append(f"Detected runtime/service/contract surface: {', '.join(backend_hits[:4])}.")
    if bool(package.tech_json.get("api_required")) and not backend_hits:
        backend_rationale.append("Upstream TECH package already requires API/contract implementation support.")
    if bool(package.tech_json.get("arch_required")) and not backend_hits:
        backend_rationale.append("Upstream TECH package already requires architecture-aligned execution work.")
    if not backend_rationale:
        backend_rationale.append("No runtime/service/storage/workflow implementation surface was detected.")

    migration_rationale = (
        [f"Detected migration/cutover language: {', '.join(migration_hits[:4])}."]
        if migration_hits
        else ["No migration, cutover, rollback, or compat-mode surface was detected."]
    )

    frontend_required = explicit_frontend_surface or bool(frontend_hits)
    backend_required = bool(backend_hits) or bool(package.tech_json.get("api_required")) or bool(package.tech_json.get("arch_required"))
    migration_required = bool(migration_hits)

    if axis_id in {"object-layering", "formalization", "collaboration-loop", "io-governance"} and not frontend_hits:
        frontend_required = False
    if axis_id in {"object-layering", "formalization"} and not explicit_migration_surface:
        migration_hits = []
        migration_required = False

    return {
        "frontend_required": frontend_required,
        "backend_required": backend_required,
        "migration_required": migration_required,
        "execution_surface_count": int(frontend_required) + int(backend_required),
        "rationale": {
            "frontend": frontend_rationale,
            "backend": backend_rationale,
            "migration": migration_rationale,
        },
    }


def implementation_scope(feature: dict[str, Any], package: Any) -> list[str]:
    items = [
        f"{unit['path']} ({unit['mode']}): {unit['detail']}"
        for unit in implementation_units(package)[:5]
    ]
    if not items:
        items = ensure_list(feature.get("scope"))[:4]
    items.extend(tech_list(package, "integration_points")[:2])
    return unique_strings(items)[:6]


def implementation_steps(feature: dict[str, Any], assessment: dict[str, Any], package: Any) -> list[dict[str, str]]:
    del feature
    units = implementation_units(package)
    unit_paths = [unit["path"] for unit in units]
    unit_preview = ", ".join(unit_paths[:4]) or "the frozen TECH implementation units"
    interface_preview = "; ".join(tech_list(package, "interface_contracts")[:2])
    sequence_preview = "; ".join(tech_list(package, "main_sequence")[:3])
    integration_preview = "; ".join(tech_list(package, "integration_points")[:2])

    steps: list[dict[str, str]] = [
        {
            "title": "Freeze upstream refs and touch set",
            "work": f"Lock feat_ref, tech_ref, optional arch/api refs, and the concrete touch set before coding: {unit_preview}.",
            "done_when": "The implementation entry references frozen upstream objects only and the concrete file/module touch set is explicit.",
        }
    ]
    if assessment["frontend_required"]:
        steps.append(
            {
                "title": "Implement frontend surface",
                "work": "Apply the selected UI/page/component changes and keep interaction behavior aligned to the frozen TECH/API boundary.",
                "done_when": "Frontend changes are wired, bounded to the selected scope, and traceable to acceptance checks.",
            }
        )
    if assessment["backend_required"]:
        steps.append(
            {
                "title": "Implement frozen runtime units",
                "work": (
                    f"Update only the declared runtime units: {unit_preview}. "
                    f"Honor the frozen contracts and sequence: {interface_preview or 'use upstream interface contracts'}."
                ),
                "done_when": (
                    "The listed units implement the upstream state transitions, contract hooks, and evidence points "
                    "without redefining ownership or decision semantics."
                ),
            }
        )
    if assessment["migration_required"]:
        steps.append(
            {
                "title": "Prepare migration and cutover controls",
                "work": integration_preview
                or "Define compat-mode, rollout, rollback, or cutover sequencing needed to land the change safely.",
                "done_when": "Migration prerequisites, guardrails, and fallback actions are explicit enough for downstream execution.",
            }
        )
    steps.append(
        {
            "title": "Integrate, evidence, and handoff",
            "work": (
                "Wire the concrete sequence and integration hooks into the package handoff. "
                + (sequence_preview or "Follow the frozen upstream runtime sequence.")
            ),
            "done_when": "The package can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries.",
        }
    )
    return steps


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


def acceptance_checkpoints(feature: dict[str, Any]) -> list[dict[str, str]]:
    checkpoints: list[dict[str, str]] = []
    for index, check in enumerate(feature.get("acceptance_checks") or [], start=1):
        if not isinstance(check, dict):
            continue
        checkpoints.append(
            {
                "ref": f"AC-{index:03d}",
                "scenario": str(check.get("scenario") or "").strip() or f"acceptance-{index}",
                "expectation": str(check.get("then") or "").strip() or "Expectation must be confirmed during execution.",
            }
        )
    if checkpoints:
        return checkpoints

    acceptance = feature.get("acceptance_and_testability") or {}
    criteria = ensure_list(acceptance.get("acceptance_criteria"))
    outcomes = ensure_list(acceptance.get("observable_outcomes"))
    authoritative_artifact = (
        str(
            (feature.get("product_objects_and_deliverables") or {}).get("authoritative_output")
            or feature.get("authoritative_artifact")
            or ""
        ).strip()
    )
    for index, criterion in enumerate(criteria, start=1):
        if outcomes:
            expectation = outcomes[min(index - 1, len(outcomes) - 1)]
        elif authoritative_artifact:
            expectation = f"{authoritative_artifact} 可被外部观察并作为唯一 authoritative result。"
        else:
            expectation = f"该验收结果必须形成可外部观察的 authoritative outcome。"
        checkpoints.append(
            {
                "ref": f"AC-{index:03d}",
                "scenario": criterion.strip() or f"acceptance-{index}",
                "expectation": str(expectation).strip() or "Expectation must be confirmed during execution.",
            }
        )
    return checkpoints


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


def evidence_rows(feature: dict[str, Any], assessment: dict[str, Any]) -> list[dict[str, Any]]:
    evidence_types: list[str] = []
    if assessment["frontend_required"]:
        evidence_types.append("frontend-verification")
    if assessment["backend_required"]:
        evidence_types.append("backend-verification")
    if assessment["migration_required"]:
        evidence_types.append("migration-verification")
    evidence_types.append("smoke-review-input")

    rows: list[dict[str, Any]] = []
    for checkpoint in acceptance_checkpoints(feature):
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

