#!/usr/bin/env python3
"""
Workstream analysis helpers for tech-to-impl.
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
EXECUTION_RUNNER_AXIS_IDS = {
    "ready-job-emission",
    "runner-operator-entry",
    "runner-control-surface",
    "execution-runner-intake",
    "next-skill-dispatch",
    "execution-result-feedback",
    "runner-observability-surface",
}
FRONTEND_SURFACE_MARKERS = [
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
BACKEND_SURFACE_MARKERS = [
    "service",
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
    "handler",
    "store",
    "service",
    "后端",
    "服务",
    "接口",
    "契约",
]
MIGRATION_SURFACE_MARKERS = [
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


def marker_present_in_segments(segments: list[str], markers: list[str]) -> bool:
    for segment in segments:
        lowered = segment.lower()
        for marker in markers:
            if "/" in marker or "\\" in marker:
                if marker in lowered:
                    return True
                continue
            if _keyword_present(lowered, marker):
                return True
    return False


def is_review_projection_package(feature: dict[str, Any], package: Any) -> bool:
    lock = package.semantic_lock if isinstance(package.semantic_lock, dict) else {}
    domain_type = str((feature.get("semantic_lock") or lock).get("domain_type") or "").strip().lower()
    if domain_type == "review_projection_rule":
        return True
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
    return axis_id in {"projection-generation", "authoritative-snapshot", "review-focus-risk", "feedback-writeback"}


def is_execution_runner_package(feature: dict[str, Any], package: Any) -> bool:
    lock = package.semantic_lock if isinstance(package.semantic_lock, dict) else {}
    domain_type = str((feature.get("semantic_lock") or lock).get("domain_type") or "").strip().lower()
    if domain_type == "execution_runner_rule":
        return True
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
    return axis_id in EXECUTION_RUNNER_AXIS_IDS


def _assess_review_projection(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    return {
        "frontend_required": False,
        "backend_required": True,
        "migration_required": False,
        "execution_surface_count": 1,
        "rationale": {
            "frontend": ["Review projection implementation does not introduce an end-user UI/page/component surface."],
            "backend": ["Review projection implementation is carried by renderer/extractor/writeback runtime modules and SSOT integration code."],
            "migration": ["Review projection FEATs do not require migration, cutover, rollback, or compat-mode planning."],
        },
    }


def _assess_execution_runner(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    return {
        "frontend_required": False,
        "backend_required": True,
        "migration_required": False,
        "execution_surface_count": 1,
        "rationale": {
            "frontend": ["Execution runner implementation is CLI/runtime-facing and does not introduce end-user UI/page/component work."],
            "backend": ["Execution runner implementation is carried by loop/job commands, queue/runtime modules, and operator-facing backend surfaces."],
            "migration": ["Execution runner FEATs do not require rollout/cutover planning inside this IMPL package unless a separate migration FEAT owns that scope."],
        },
    }


def _assess_general(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    segments = implementation_surface_segments(feature, package)
    feature_only_segments = feature_segments(feature)
    frontend_hits = keyword_hits_in_segments(segments, FRONTEND_KEYWORDS)
    backend_hits = keyword_hits_in_segments(segments, BACKEND_KEYWORDS)
    migration_hits = keyword_hits_in_segments(segments, MIGRATION_KEYWORDS)
    feature_frontend_hits = keyword_hits_in_segments(feature_only_segments, FRONTEND_KEYWORDS)
    feature_migration_hits = keyword_hits_in_segments(feature_only_segments, MIGRATION_KEYWORDS)
    tech_design = package.tech_json.get("tech_design", {}) or {}
    implementation_units = ensure_list(tech_design.get("implementation_unit_mapping"))
    integration_points = ensure_list(tech_design.get("integration_points"))
    exception_items = ensure_list(tech_design.get("exception_and_compensation"))
    interface_contracts = ensure_list(tech_design.get("interface_contracts"))
    tech_surface_segments = implementation_units + integration_points + interface_contracts
    migration_segments = implementation_units + integration_points + exception_items
    explicit_frontend_surface = marker_present_in_segments(tech_surface_segments, FRONTEND_SURFACE_MARKERS)
    explicit_backend_surface = marker_present_in_segments(tech_surface_segments, BACKEND_SURFACE_MARKERS)
    has_explicit_unit_mapping = bool(implementation_units)
    implementation_unit_text = " ".join(implementation_units).lower()
    explicit_frontend_unit_surface = marker_present_in_segments(implementation_units, FRONTEND_SURFACE_MARKERS)
    explicit_migration_unit_surface = marker_present_in_segments(implementation_units, MIGRATION_SURFACE_MARKERS)
    explicit_migration_integration_surface = marker_present_in_segments(integration_points, ["migration", "cutover", "rollout", "切换", "迁移", "灰度"])
    explicit_migration_exception_surface = marker_present_in_segments(exception_items, ["migration", "cutover", "rollback", "fallback", "回滚", "迁移", "切换"])
    explicit_migration_surface = (
        explicit_migration_unit_surface
        or (bool(feature_migration_hits) and has_explicit_unit_mapping)
        or (bool(feature_migration_hits) and (explicit_migration_integration_surface or explicit_migration_exception_surface))
    )
    frontend_rationale = (
        [f"Detected explicit UI or interaction surface: {', '.join((feature_frontend_hits or frontend_hits)[:4])}."]
        if (explicit_frontend_surface or feature_frontend_hits)
        else ["No explicit UI/page/component implementation surface was detected."]
    )
    backend_rationale: list[str] = []
    if explicit_backend_surface or backend_hits:
        backend_rationale.append(f"Detected runtime/service/contract surface: {', '.join(backend_hits[:4])}.")
    if bool(package.tech_json.get("api_required")) and not backend_hits:
        backend_rationale.append("Upstream TECH package already requires API/contract implementation support.")
    if bool(package.tech_json.get("arch_required")) and not backend_hits:
        backend_rationale.append("Upstream TECH package already requires architecture-aligned execution work.")
    if not backend_rationale:
        backend_rationale.append("No runtime/service/storage/workflow implementation surface was detected.")
    migration_rationale = (
        [f"Detected migration/cutover language: {', '.join((feature_migration_hits or migration_hits)[:4])}."]
        if explicit_migration_surface
        else ["No migration, cutover, rollback, or compat-mode surface was detected."]
    )
    frontend_required = explicit_frontend_surface or bool(feature_frontend_hits)
    backend_required = explicit_backend_surface or bool(package.tech_json.get("api_required")) or bool(package.tech_json.get("arch_required"))
    migration_required = explicit_migration_surface
    axis_id = str(feature.get("axis_id") or feature.get("slice_id") or "").strip().lower()
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


def assess_workstreams(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    if is_review_projection_package(feature, package):
        return _assess_review_projection(feature, package)
    if is_execution_runner_package(feature, package):
        return _assess_execution_runner(feature, package)
    return _assess_general(feature, package)
