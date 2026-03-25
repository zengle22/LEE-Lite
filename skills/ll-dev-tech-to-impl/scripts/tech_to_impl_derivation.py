#!/usr/bin/env python3
"""
Derivation helpers for the lite-native tech-to-impl runtime.
"""

from __future__ import annotations

from typing import Any

from tech_to_impl_common import ensure_list, unique_strings


FRONTEND_KEYWORDS = [
    "ui",
    "ux",
    "page",
    "screen",
    "view",
    "component",
    "frontend",
    "front-end",
    "页面",
    "交互",
    "前端",
    "组件",
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


def feature_segments(feature: dict[str, Any]) -> list[str]:
    segments: list[str] = []
    for key in ["title", "goal"]:
        value = str(feature.get(key) or "").strip()
        if value:
            segments.append(value)
    for key in ["scope", "constraints", "dependencies"]:
        segments.extend(ensure_list(feature.get(key)))
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


def keyword_hits(feature: dict[str, Any], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    for segment in feature_segments(feature):
        lowered = segment.lower()
        if any(marker in lowered for marker in NEGATION_MARKERS):
            continue
        for keyword in keywords:
            if keyword in lowered and keyword not in hits:
                hits.append(keyword)
    return hits


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


def assess_workstreams(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    frontend_hits = keyword_hits(feature, FRONTEND_KEYWORDS)
    backend_hits = keyword_hits(feature, BACKEND_KEYWORDS)
    migration_hits = keyword_hits(feature, MIGRATION_KEYWORDS)

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

    frontend_required = bool(frontend_hits)
    backend_required = bool(backend_hits) or bool(package.tech_json.get("api_required")) or bool(package.tech_json.get("arch_required"))
    migration_required = bool(migration_hits)

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


def implementation_scope(feature: dict[str, Any]) -> list[str]:
    scope = ensure_list(feature.get("scope"))[:4]
    constraints = ensure_list(feature.get("constraints"))[:2]
    return unique_strings(scope + constraints)[:6]


def implementation_steps(feature: dict[str, Any], assessment: dict[str, Any]) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = [
        {
            "title": "Freeze upstream refs and implementation boundary",
            "work": "Align feat_ref, tech_ref, optional arch/api refs, file touch scope, and blocked conditions before touching execution surfaces.",
            "done_when": "The implementation entry uses only frozen upstream refs and does not redefine technical decisions.",
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
                "title": "Implement backend and contract surface",
                "work": "Apply runtime/service/storage/workflow/contract changes required by the selected TECH package.",
                "done_when": "Backend-side changes satisfy the selected technical design without introducing shadow design drift.",
            }
        )
    if assessment["migration_required"]:
        steps.append(
            {
                "title": "Prepare migration and cutover controls",
                "work": "Define rollout, rollback, compat-mode, or cutover sequencing needed to land the change safely.",
                "done_when": "Migration prerequisites, guardrails, and fallback actions are explicit enough for downstream execution.",
            }
        )
    steps.append(
        {
            "title": "Integrate, evidence, and handoff",
            "work": "Complete integration ordering, evidence collection hooks, smoke subject packaging, and downstream handoff.",
            "done_when": "The package can enter template.dev.feature_delivery_l2 without reinterpreting FEAT or TECH boundaries.",
        }
    )
    return steps


def risk_items(feature: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("constraints"))[:3] + ensure_list(feature.get("dependencies"))[:2]
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
    return checkpoints


def integration_plan_items(feature: dict[str, Any], assessment: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("dependencies"))[:3]
    if assessment["frontend_required"] and assessment["backend_required"]:
        items.append("Freeze frontend/backend integration order before smoke review.")
    if assessment["migration_required"]:
        items.append("Migration or cutover can execute only after implementation evidence is complete.")
    if not items:
        items.append("Single-surface execution still preserves one explicit integration checkpoint before smoke review.")
    return unique_strings(items)[:5]


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


def backend_workstream_items(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("constraints"))[:3] + ensure_list(feature.get("dependencies"))[:2]
    return unique_strings(items or ensure_list(feature.get("scope"))[:4])[:5]


def migration_plan_items(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("constraints"))[:2] + ensure_list(feature.get("dependencies"))[:2]
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

