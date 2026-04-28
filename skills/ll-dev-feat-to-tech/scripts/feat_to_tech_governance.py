#!/usr/bin/env python3
"""
Governance helpers for feat-to-tech.
"""

from __future__ import annotations

from typing import Any

from feat_to_tech_common import ensure_list, unique_strings
from feat_to_tech_derivation import (
    ARCH_KEYWORDS,
    detect_api_surface_in_scope,
    api_command_specs,
    collaboration_reentry_scope,
    architecture_diagram,
    architecture_topics,
    feature_axis,
    feature_text,
    keyword_hits,
    tech_runtime_view,
)
from feat_to_tech_integration_context import integration_sufficiency_check


def assess_optional_artifacts(feature: dict[str, Any], integration_context: dict[str, Any]) -> dict[str, Any]:
    arch_hits = keyword_hits(feature, ARCH_KEYWORDS)
    api_required = detect_api_surface_in_scope(feature)
    axis = feature_axis(feature)
    arch_required = bool(arch_hits) or axis in {
        "collaboration",
        "formalization",
        "layering",
        "io_governance",
        "first_ai_advice",
        "extended_profile_completion",
        "device_deferred_entry",
        "state_profile_boundary",
        "minimal_onboarding",
        "adoption_e2e",
        "runner_ready_job",
        "runner_operator_entry",
        "runner_control_surface",
        "runner_intake",
        "runner_dispatch",
        "runner_feedback",
        "runner_observability",
    }
    integration_gate = integration_sufficiency_check(integration_context)
    arch_rationale = ["ARCH required by boundary/runtime placement."] if arch_required else ["ARCH omitted because the FEAT does not introduce a dedicated boundary/topology surface."]
    if arch_hits:
        arch_rationale.append(f"Keyword hits: {', '.join(arch_hits[:4])}.")
    api_rationale = ["API required by explicit surface declaration in FEAT scope/outputs."] if api_required else ["API omitted because FEAT scope/outputs do not declare an explicit command-level contract surface."]
    return {
        "arch_required": arch_required,
        "api_required": api_required,
        "integration_context_sufficient": integration_gate["passed"],
        "stateful_design_present": False,
        "arch_hits": arch_hits,
        "api_hits": [],
        "arch_rationale": arch_rationale,
        "api_rationale": api_rationale,
        "integration_context_rationale": [integration_gate["summary"], *integration_gate["issues"]],
        "stateful_design_rationale": ["stateful design not evaluated yet"],
    }


def state_machine(feature: dict[str, Any]) -> list[str]:
    return _fallback_lines(
        feature,
        "state_machine",
        [
            "states: prepared -> executing -> recorded",
            "guards: input validated before execution; evidence written before handoff",
            "field mapping: lifecycle_state tracks runtime progression and must not be owned by IMPL",
        ],
    )


def algorithm_constraints(feature: dict[str, Any], integration_context: dict[str, Any]) -> list[str]:
    items = [
        "decision rule: preserve FEAT acceptance and inherited constraints before selecting runtime shape",
        "determinism: design derivation must stay deterministic for the same FEAT and integration context",
    ]
    items.extend(f"compatibility anchor: {item}" for item in ensure_list(integration_context.get("compatibility_constraints"))[:2])
    return unique_strings(items)


def io_matrix_and_side_effects(feature: dict[str, Any]) -> list[str]:
    feat_ref = str(feature.get("feat_ref") or "").strip() or "selected feat"
    return [
        f"select_{feat_ref}: inputs=feat_freeze_package, feat_ref; outputs=selected_feat snapshot; writes=none; side_effects=none; evidence=input validation; idempotency=repeatable",
        "derive_design: inputs=selected_feat, integration_context; outputs=TECH/ARCH/API blocks; writes=tech-design-bundle.*; side_effects=markdown/json materialization; evidence=execution-evidence; idempotency=run_id scoped",
        "handoff_downstream: inputs=frozen tech package; outputs=handoff-to-tech-impl.json; writes=handoff artifact; side_effects=downstream routing metadata; evidence=freeze gate + supervision",
    ]


def technical_glossary_and_canonical_ownership(feature: dict[str, Any], integration_context: dict[str, Any]) -> list[str]:
    owners = ensure_list(integration_context.get("canonical_ownership"))
    if owners:
        return unique_strings(owners)
    feat_ref = str(feature.get("feat_ref") or "").strip() or "selected feat"
    return [
        f"{feat_ref}: business capability boundary owned by FEAT",
        "TECH package: implementation truth owner for state machine, algorithm, integration, and migration constraints",
        "IMPL package: execution organizer only; must not become a second truth source",
    ]


def migration_constraints(integration_context: dict[str, Any]) -> list[str]:
    items = [f"mode: {item}" for item in ensure_list(integration_context.get("migration_modes"))]
    items.extend(f"legacy invariant: {item}" for item in ensure_list(integration_context.get("legacy_invariants"))[:2])
    return unique_strings(items or ["mode: extend", "legacy invariant: preserve governed handoff lineage"])


def evaluate_stateful_design_present(state_machine_lines: list[str], io_matrix_lines: list[str], glossary_lines: list[str]) -> tuple[bool, list[str]]:
    checks = {
        "state_machine": len(state_machine_lines) >= 2,
        "io_matrix": len(io_matrix_lines) >= 2,
        "canonical_ownership": len(glossary_lines) >= 2,
    }
    return all(checks.values()), [f"{name}={'present' if ok else 'missing'}" for name, ok in checks.items()]


def consistency_check(feature: dict[str, Any], assessment: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []
    minor_open_items: list[str] = []
    structural: list[bool] = []
    semantic: list[bool] = []

    def add_check(category: str, name: str, passed: bool, detail: str, issue: str | None = None) -> None:
        checks.append({"category": category, "name": name, "passed": passed, "detail": detail})
        (structural if category == "structural" else semantic).append(passed)
        if not passed and issue:
            issues.append(issue)

    add_check("structural", "TECH mandatory", True, "TECH is always emitted for the selected FEAT.")
    add_check("structural", "Integration context sufficient", assessment["integration_context_sufficient"], assessment["integration_context_rationale"][0] if assessment["integration_context_rationale"] else "integration context checked", "integration_context is not sufficient for current-system design freeze.")
    add_check("structural", "Traceability present", bool(ensure_list(feature.get("source_refs"))), "Selected FEAT carries authoritative source refs for downstream design derivation.", "Selected FEAT did not carry enough source refs to support traceability.")
    add_check("structural", "State machine frozen", assessment["stateful_design_present"], "TECH includes explicit state machine, I/O matrix, and canonical ownership sections.", "TECH is still missing explicit stateful-design facts.")
    add_check("structural", "ARCH coverage" if assessment["arch_required"] else "ARCH omission justified", (len(architecture_topics(feature)) >= 2) if assessment["arch_required"] else True, "ARCH coverage matches the selected FEAT boundary needs." if assessment["arch_required"] else "ARCH is omitted because the FEAT does not require boundary or topology redesign.", "ARCH was required but architecture topics could not be resolved clearly.")
    add_check("structural", "API coverage" if assessment["api_required"] else "API omission justified", bool(api_command_specs(feature)) if assessment["api_required"] else True, "API coverage includes concrete command-level contracts." if assessment["api_required"] else "API is omitted because no explicit cross-boundary contract surface was detected.", "API was required but no concrete command contract specs were derived.")
    add_check("semantic", "ARCH / TECH separation", (architecture_diagram(feature) != tech_runtime_view(feature)) if assessment["arch_required"] else True, "ARCH keeps boundary placement while TECH keeps implementation carriers.", "ARCH and TECH still appear to share the same runtime topology.")
    api_complete = True
    if assessment["api_required"]:
        specs = api_command_specs(feature)
        api_complete = bool(specs) and all(spec.get("request_schema") and spec.get("response_schema") and spec.get("field_semantics") and spec.get("enum_domain") is not None and spec.get("invariants") and spec.get("canonical_refs") for spec in specs)
    add_check("semantic", "API contract completeness", api_complete, "API contracts carry schema, semantics, invariants, and canonical refs.", "API is still too thin; command specs are missing schema, invariants, or canonical ref semantics.")
    if assessment["api_required"]:
        specs = api_command_specs(feature)
        preconditions_complete = bool(specs) and all(
            spec.get("caller_context") and spec.get("idempotency_key_strategy")
            and spec.get("post_conditions") and spec.get("system_dependency_pre_state")
            and spec.get("side_effects") is not None and spec.get("ui_surface_impact") and spec.get("event_outputs") is not None
            for spec in specs
        )
        add_check("semantic", "API preconditions completeness", preconditions_complete, "API contracts carry caller context, idempotency strategy, post-conditions, and state transition fields.", "API is missing preconditions/post-conditions chapter fields.")
    if feature_axis(feature) == "collaboration":
        scope = collaboration_reentry_scope(feature)
        add_check("semantic", "Collaboration re-entry boundary", scope != "ambiguous", "Collaboration FEATs keep decision-driven runtime routing in scope without claiming gate/publication ownership.", "The FEAT carries ambiguous or unresolved revise/retry re-entry ownership.")
    add_check("semantic", "Integration points explicit", len(context["integrations"]) >= 2, "TECH carries concrete current-system integration points.", "TECH integration points are too thin to freeze current-system hookup.")
    add_check("semantic", "Algorithm constraints explicit", len(context["algorithm_constraints"]) >= 2, "TECH carries explicit decision and algorithm constraints.", "TECH is missing explicit algorithm / decision constraints.")
    if assessment["api_required"]:
        minor_open_items.append("Freeze a command-level error mapping table for `code -> retryable -> idempotent_replay` in a later API revision if validator-grade contract testing needs a closed semantics table.")
    if assessment["arch_required"] or assessment["api_required"]:
        minor_open_items.append("Optional ARCH/API summaries are still embedded in the bundle for one-shot review; a later revision may collapse them to pure references to reduce duplication risk.")
    if not feature_text(feature).strip():
        minor_open_items.append("Selected FEAT text is unusually thin; recheck upstream FEAT prose if downstream implementation pressure rises.")
    return {"passed": all(structural) and all(semantic), "structural_passed": all(structural), "semantic_passed": all(semantic), "checks": checks, "issues": issues, "minor_open_items": minor_open_items}


def _fallback_lines(feature: dict[str, Any], key: str, defaults: list[str]) -> list[str]:
    from feat_to_tech_axis_content import axis_content

    content = axis_content(feature_axis(feature), key)
    if isinstance(content, list) and content:
        return [str(item).strip() for item in content if str(item).strip()]
    return defaults
