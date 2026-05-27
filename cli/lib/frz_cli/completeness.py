"""Step_1 — 6-dimension completeness check with Q1–Q5 quality gates.

Truth source: design.md §step_1, proposal.md §Q1–Q5.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from frz_cli.exceptions import CompletenessBlockedError
from frz_cli.models import CompletenessVerdict

logger = logging.getLogger("frz.completeness")


def _load_project_rules(config_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load project-specific semantic rules from YAML config.

    Searches for config in order:
      1. Explicit config_path argument
      2. Environment variable FRZ_COMPLETENESS_RULES
      3. Adjacent to this file: ../../../../../skills/ll-v2-frz-ingest/config/completeness-rules.yaml
      4. Empty list (no project-specific rules)
    """
    if config_path:
        path = Path(config_path)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get("rules", [])

    env_path = os.environ.get("FRZ_COMPLETENESS_RULES")
    if env_path:
        path = Path(env_path)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get("rules", [])

    # Fallback: relative to this file's location in cli/lib/v2/
    fallback = Path(__file__).resolve().parent.parent.parent.parent / "skills" / "ll-v2-frz-ingest" / "config" / "completeness-rules.yaml"
    if fallback.exists():
        with open(fallback, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("rules", [])

    logger.debug("No project-specific completeness rules found; running with generic defaults")
    return []


def _evaluate_rules(
    rules: list[dict[str, Any]],
    project_type: str,
    context: dict[str, str],
) -> list[dict[str, Any]]:
    """Evaluate configured rules against the extracted text context.

    Args:
        rules: Loaded rule definitions.
        project_type: Current project type (e.g. 'generic', 'lee-lite').
        context: Dict of target_name -> text strings (combined_raw, ux_lower, etc.)

    Returns:
        List of missing-item dicts for rules that FAIL (i.e. pattern not found).
    """
    if project_type == "generic":
        return []

    results: list[dict[str, Any]] = []
    for rule in rules:
        enabled_for = rule.get("enabled_for", [])
        if enabled_for and project_type not in enabled_for:
            continue

        target_name = rule.get("target", "combined_raw")
        text = context.get(target_name, "")
        patterns = rule.get("patterns", [])
        match_type = rule.get("match_type", "contains")

        matched = False
        if match_type == "contains":
            matched = any(p in text for p in patterns)
        elif match_type == "not_contains":
            matched = all(p not in text for p in patterns)
        elif match_type == "any_contains":
            matched = any(p in text for p in patterns)
        elif match_type == "all_contains":
            matched = all(p in text for p in patterns)

        if not matched:
            results.append({
                "dimension": rule.get("dimension", "semantic_check"),
                "field": rule.get("id", "unknown"),
                "reason": f"{rule.get('id', 'RULE')}: {rule.get('message', 'Rule failed')}",
                "severity": rule.get("severity", "P2"),
                "suggested_fix": rule.get("suggested_fix", ""),
            })

    return results


REQUIRED_DIMENSIONS = {
    "business_design",
    "product_design",
    "architecture_design",
    "engineering_design",
}

OPTIONAL_DIMENSIONS = {"test_design"}

CONDITIONAL_DIMENSIONS = {"ux_design"}


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def _find_field_anywhere(design_package: dict[str, Any], field_name: str) -> Any:
    """Search for a field across all dimensions."""
    for dim_data in design_package.values():
        if isinstance(dim_data, dict) and field_name in dim_data:
            return dim_data[field_name]
    return None


def _has_substantive_content(dim_data: dict[str, Any]) -> bool:
    """Check if a dimension has substantive content.

    For Markdown raw content, uses length heuristic (>>500 chars).
    For structured data, checks any non-empty field.
    """
    raw = dim_data.get("__raw__", "")
    if isinstance(raw, str) and len(raw) >= 500:
        return True
    for key, value in dim_data.items():
        if key.startswith("__"):
            continue
        if _is_non_empty(value):
            return True
    return False


def _dim_has_raw_only(dim_data: dict[str, Any]) -> bool:
    """True when dimension only has __raw__ and metadata fields."""
    keys = [k for k in dim_data.keys() if not k.startswith("__")]
    return len(keys) == 0 and "__raw__" in dim_data


def _check_ux_required(design_package: dict[str, Any]) -> bool:
    """Determine whether ux_design is conditionally required.

    Triggers when product_design hints at UI/frontend needs,
    architecture_design lists frontend tech, or test_design has e2e.
    """
    product = design_package.get("product_design", {})
    arch = design_package.get("architecture_design", {})
    test = design_package.get("test_design", {})

    prd = product.get("prd", "")
    if isinstance(prd, str) and ("UI" in prd or "前端" in prd or "frontend" in prd.lower()):
        return True

    tech_stack = arch.get("tech_stack", {})
    if isinstance(tech_stack, dict):
        stack_str = str(tech_stack).lower()
        if any(k in stack_str for k in ("react", "vue", "angular", "html", "css", "ui")):
            return True

    test_strategy = test.get("test_strategy", "")
    if isinstance(test_strategy, str) and "e2e" in test_strategy.lower():
        return True

    return False


def _raw_fallback(dim_data: dict[str, Any]) -> str:
    """Return __raw__ content if present, for Markdown fallback extraction."""
    raw = dim_data.get("__raw__", "")
    return raw if isinstance(raw, str) else ""


def _post_compile_validation(chain: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Validate compiled SSOT chain for structural and semantic defects."""
    blockers: list[dict] = []
    warnings: list[dict] = []
    
    # 1. IMPL grouping validation
    impls = chain.get("impls", [])
    epics = chain.get("epics", [])
    if impls and epics:
        epic_keys = set()
        for impl in impls:
            req_ctx = getattr(impl, "requirement_context", {}) or {}
            ekey = req_ctx.get("epic_key", "") if isinstance(req_ctx, dict) else getattr(req_ctx, "epic_key", "")
            if ekey in epic_keys:
                blockers.append({
                    "dimension": "impl",
                    "field": "epic_key",
                    "reason": f"Duplicate epic_key in IMPL files: {ekey}",
                    "severity": "P1",
                })
            epic_keys.add(ekey)
        if len(impls) != len(epics):
            warnings.append({
                "dimension": "impl",
                "field": "file_count",
                "reason": f"IMPL file count ({len(impls)}) != epic count ({len(epics)})",
                "severity": "P2",
            })
    
    # 2. API endpoint structural validation
    apis = chain.get("apis", [])
    if apis:
        api = apis[0]
        endpoints = getattr(api, "endpoints", []) or []
        for ep in endpoints:
            if not isinstance(ep, dict):
                continue
            path = ep.get("path", ep.get("路径", ""))
            method = ep.get("method", ep.get("方法", ""))
            # Check mixed language keys
            has_cn = any(re.search(r'[\u4e00-\u9fff]', str(k)) for k in ep.keys())
            has_en = any(re.match(r'^[a-z_][a-z0-9_]*$', str(k), re.I) for k in ep.keys())
            if has_cn and has_en:
                blockers.append({
                    "dimension": "api",
                    "field": f"endpoint_{method}_{path}",
                    "reason": f"API endpoint has mixed Chinese/English keys: {path}",
                    "severity": "P1",
                })
            # Check missing core fields
            for required in ("handler", "priority"):
                if not ep.get(required):
                    blockers.append({
                        "dimension": "api",
                        "field": f"endpoint_{method}_{path}.{required}",
                        "reason": f"API endpoint missing {required}: {path}",
                        "severity": "P1",
                    })
            # Check flat schema
            for schema_field in ("request_schema", "response_schema"):
                schema = ep.get(schema_field)
                if isinstance(schema, dict):
                    for v in schema.values():
                        if isinstance(v, str):
                            warnings.append({
                                "dimension": "api",
                                "field": f"endpoint_{method}_{path}.{schema_field}",
                                "reason": f"API endpoint uses flat schema format: {path}",
                                "severity": "P2",
                            })
                            break
    
    # 3. FRZ statistics validation
    frz = chain.get("frz")
    if frz:
        total_ac = getattr(frz, "total_ac", None)
        covered_ac = getattr(frz, "covered_ac", None)
        if total_ac == 0 or total_ac is None:
            blockers.append({
                "dimension": "frz",
                "field": "total_ac",
                "reason": "FRZ total_ac is 0 or missing",
                "severity": "P2",
            })
        if covered_ac == 0 or covered_ac is None:
            blockers.append({
                "dimension": "frz",
                "field": "covered_ac",
                "reason": "FRZ covered_ac is 0 or missing",
                "severity": "P2",
            })
        if total_ac is not None and covered_ac is not None and covered_ac > total_ac:
            blockers.append({
                "dimension": "frz",
                "field": "covered_ac",
                "reason": "FRZ covered_ac > total_ac",
                "severity": "P1",
            })
    
    # 4. ARCH data_flow chapter number drift
    archs = chain.get("archs", [])
    if archs:
        arch = archs[0]
        data_flow = getattr(arch, "data_flow", None)
        if isinstance(data_flow, dict):
            for title in data_flow.keys():
                if re.match(r'^\d+\.\d*\s+', title):
                    warnings.append({
                        "dimension": "arch",
                        "field": "data_flow",
                        "reason": f"ARCH data_flow title contains chapter number: '{title}'",
                        "severity": "P2",
                    })
    
    # 5. TECH risks duplication
    techs = chain.get("techs", [])
    if techs:
        tech = techs[0]
        risks = getattr(tech, "risks", [])
        if risks and len(risks) > 1:
            seen = set()
            for risk in risks:
                key = risk.get("title", risk.get("id", str(risk))) if isinstance(risk, dict) else str(risk)
                if key in seen:
                    warnings.append({
                        "dimension": "tech",
                        "field": "risks",
                        "reason": f"TECH risks contains duplicate: {key}",
                        "severity": "P2",
                    })
                    break
                seen.add(key)
    
    return blockers, warnings


def check_completeness(
    design_package: dict[str, Any],
    compiled_chain: dict[str, Any] | None = None,
    project_type: str = "generic",
    rules_config_path: str | Path | None = None,
) -> CompletenessVerdict:
    """Run 6-dimension completeness check + Q1–Q5 quality gates.

    Args:
        design_package: The design package to validate.
        compiled_chain: Optional compiled SSOT chain for post-compilation validation.

    Returns:
        CompletenessVerdict with verdict (pass | blocked | partial).

    Raises:
        CompletenessBlockedError: If verdict is blocked and caller wants exception semantics.
    """
    missing_items: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    # --- dimension presence ---
    present_dims = set(design_package.keys())
    for dim in REQUIRED_DIMENSIONS:
        dim_data = design_package.get(dim, {})
        if dim not in present_dims or not _has_substantive_content(dim_data):
            missing_items.append({"dimension": dim, "field": "*", "reason": "required dimension missing or empty", "severity": "P1"})

    ux_required = _check_ux_required(design_package)
    if ux_required and ("ux_design" not in present_dims or not _has_substantive_content(design_package.get("ux_design", {}))):
        missing_items.append({"dimension": "ux_design", "field": "*", "reason": "conditional required dimension missing (UI/frontend detected)"})

    if "test_design" not in present_dims:
        warnings.append({"dimension": "test_design", "field": "*", "reason": "optional dimension missing"})

    # --- Q1–Q5 quality gates ---
    business = design_package.get("business_design", {})
    product = design_package.get("product_design", {})
    arch = design_package.get("architecture_design", {})
    ux = design_package.get("ux_design", {})

    # Detect Markdown raw-only dimensions for relaxed gating
    business_raw = _dim_has_raw_only(business)
    product_raw = _dim_has_raw_only(product)
    arch_raw = _dim_has_raw_only(arch)
    ux_raw = _dim_has_raw_only(ux)

    # Q1: SRC container presence
    q1_vision = _is_non_empty(business.get("product_vision"))
    # scope_declaration may live in product_design or other dimensions
    q1_scope = _is_non_empty(business.get("scope_declaration")) or _is_non_empty(_find_field_anywhere(design_package, "scope_declaration"))
    q1_fail = not q1_vision or not q1_scope
    if q1_fail:
        if business_raw:
            warnings.append({"dimension": "business_design", "field": "product_vision / scope_declaration", "reason": "Q1: raw Markdown content detected; structured fields not extracted (Phase 1 allowed)"})
        else:
            missing_items.append({"dimension": "business_design", "field": "product_vision / scope_declaration", "reason": "Q1 failed: SRC container fields empty", "severity": "P1"})

    # Q2: EPIC chapter presence
    ujm = product.get("user_journey_map", [])
    if not isinstance(ujm, list) or len(ujm) == 0:
        if product_raw:
            warnings.append({"dimension": "product_design", "field": "user_journey_map", "reason": "Q2: raw Markdown content detected; structured fields not extracted (Phase 1 allowed)"})
        else:
            missing_items.append({"dimension": "product_design", "field": "user_journey_map", "reason": "Q2 failed: no journeys found", "severity": "P1"})

    # Q3: FEAT slice presence
    ac = product.get("acceptance_criteria", [])
    if not isinstance(ac, list) or len(ac) == 0:
        if product_raw:
            warnings.append({"dimension": "product_design", "field": "acceptance_criteria", "reason": "Q3: raw Markdown content detected; structured fields not extracted (Phase 1 allowed)"})
        else:
            missing_items.append({"dimension": "product_design", "field": "acceptance_criteria", "reason": "Q3 failed: no acceptance criteria found", "severity": "P1"})

    # Q4: derived object presence (cross-dimensional lookup allowed)
    tech_stack_anywhere = _is_non_empty(_find_field_anywhere(design_package, "tech_stack"))
    api_contract_anywhere = _is_non_empty(_find_field_anywhere(design_package, "api_contract"))
    if not _is_non_empty(arch.get("tech_stack")) and not tech_stack_anywhere:
        if arch_raw:
            warnings.append({"dimension": "architecture_design", "field": "tech_stack", "reason": "Q4: raw Markdown content detected; structured fields not extracted (Phase 1 allowed)"})
        else:
            missing_items.append({"dimension": "architecture_design", "field": "tech_stack", "reason": "Q4 failed: tech_stack empty", "severity": "P1"})
    if not _is_non_empty(arch.get("api_contract")) and not api_contract_anywhere:
        if arch_raw:
            warnings.append({"dimension": "architecture_design", "field": "api_contract", "reason": "Q4: raw Markdown content detected; structured fields not extracted (Phase 1 allowed)"})
        else:
            missing_items.append({"dimension": "architecture_design", "field": "api_contract", "reason": "Q4 failed: api_contract empty", "severity": "P1"})
    if ux_required and not _is_non_empty(ux.get("prototype")):
        if ux_raw:
            warnings.append({"dimension": "ux_design", "field": "prototype", "reason": "Q4: raw Markdown content detected; structured fields not extracted (Phase 1 allowed)"})
        else:
            missing_items.append({"dimension": "ux_design", "field": "prototype", "reason": "Q4 failed: prototype empty (UI required)", "severity": "P1"})

    # Q5: traceability completeness (source_path presence)
    for dim in REQUIRED_DIMENSIONS:
        dim_data = design_package.get(dim, {})
        if isinstance(dim_data, dict) and not dim_data.get("source_path"):
            # Allow placeholder for Phase 1; downgrade to warning per proposal MVP assumption
            warnings.append({"dimension": dim, "field": "source_path", "reason": "Q5: source_path placeholder (Phase 1 allowed)"})

    # --- Semantic completeness scan (FRZ-P2-007) ---
    eng_raw = _raw_fallback(design_package.get("engineering_design", {}))
    product_raw = _raw_fallback(design_package.get("product_design", {}))
    arch_raw = _raw_fallback(design_package.get("architecture_design", {}))
    ux_raw = _raw_fallback(design_package.get("ux_design", {}))
    combined_raw = f"{eng_raw}\n{product_raw}\n{arch_raw}\n{ux_raw}"

    # Only run project-specific semantic scans when there is substantive raw content
    # (skip for minimal test fixtures that lack __raw__ Markdown content)
    _has_substantive_raw = len(combined_raw.strip()) > 200

    # Load and evaluate project-specific rules from external config
    if _has_substantive_raw and project_type != "generic":
        rules = _load_project_rules(rules_config_path)
        ux_lower = ux_raw.lower()
        context = {
            "combined_raw": combined_raw,
            "combined_raw_lower": combined_raw.lower(),
            "ux_lower": ux_lower,
        }
        rule_results = _evaluate_rules(rules, project_type, context)
        for result in rule_results:
            missing_items.append(result)
    elif _has_substantive_raw and project_type == "generic":
        # Generic mode: skip all project-specific semantic scans.
        # Only log at DEBUG level for transparency.
        logger.debug("Project type is 'generic'; skipping project-specific semantic rules")

    # --- Post-Compilation Validation (PCV) ---
    if compiled_chain:
        pcv_blockers, pcv_warnings = _post_compile_validation(compiled_chain)
        for b in pcv_blockers:
            missing_items.append({"dimension": b.get("dimension", "compiled"), "field": b.get("field", ""), "reason": b["reason"], "severity": b.get("severity", "P1")})
        for w in pcv_warnings:
            warnings.append({"dimension": w.get("dimension", "compiled"), "field": w.get("field", ""), "reason": w["reason"], "severity": w.get("severity", "P2")})

    # --- verdict ---
    p1_missing = [m for m in missing_items if m.get("severity") == "P1"]
    p2_missing = [m for m in missing_items if m.get("severity") != "P1"]
    if p1_missing:
        verdict = "blocked"
    elif p2_missing or warnings:
        verdict = "partial"
    else:
        verdict = "pass"

    return CompletenessVerdict(
        verdict=verdict,
        missing_items=missing_items,
        warnings=warnings,
    )
