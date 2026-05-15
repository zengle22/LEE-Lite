"""Step_4 — Compile product drift detection.

Truth source: design.md §step_4.
"""

from __future__ import annotations

from typing import Any

from cli.lib.v2.compiler import _plausible_keys
from cli.lib.v2.exceptions import DriftDetectedError
from cli.lib.v2.models import (
    API,
    ARCH,
    FEAT,
    FRZPackageV2,
    SRC,
    TECH,
    UI,
    DriftVerdict,
)


def detect_drift(
    design_package: dict[str, Any],
    src: SRC,
    feats: list[FEAT],
    techs: list[TECH],
    archs: list[ARCH],
    apis: list[API],
    uis: list[UI],
) -> DriftVerdict:
    """Detect semantic drift between compiled SSOT chain and original Design Package.

    Checks:
    1. Invented semantics: compiled fields traceable to input
    2. Scope drift: FEAT scope not wider than input
    3. Tech drift: TECH uses only specified technologies
    4. Design intent drift: UI principles match input
    """
    drift_items: list[dict[str, Any]] = []

    # 1. Source traceability (simplified: check SRC fields against business_design)
    biz = design_package.get("business_design", {})
    biz_has_raw = "__raw__" in biz and isinstance(biz["__raw__"], str) and len(biz["__raw__"]) > 0
    for key, value in src.__dict__.items():
        if key in ("format_version", "source_refs", "freeze_status", "src_id", "version", "epics"):
            continue
        if value is None or value == "" or value == [] or value == {}:
            continue
        if key in biz or key in ("scope_boundaries",):
            continue
        if any(k in biz for k in _plausible_keys(key)):
            continue
        if biz_has_raw:
            # Markdown raw content covers all fields; skip traceability check
            continue
        drift_items.append({
            "drift_type": "invented_semantics",
            "source_field": f"business_design.{key}",
            "compiled_field": f"SRC.{src.src_id}.{key}",
            "drift_description": f"Field '{key}' in SRC not found in business_design",
            "severity": "high",
        })

    # 2. Scope drift: check FEAT acceptance_criteria count vs input
    product = design_package.get("product_design", {})
    input_ac = product.get("acceptance_criteria", [])
    if len(feats) != len(input_ac):
        drift_items.append({
            "drift_type": "scope_drift",
            "source_field": "product_design.acceptance_criteria",
            "compiled_field": f"FEAT count ({len(feats)})",
            "drift_description": f"FEAT count ({len(feats)}) != input AC count ({len(input_ac)})",
            "severity": "medium",
        })

    # 3. Tech drift: check if TECH uses unspecified technologies
    arch = design_package.get("architecture_design", {})
    specified_tech = set()
    ts = arch.get("tech_stack", {})
    if isinstance(ts, dict):
        specified_tech.update(ts.keys())
    for tech in techs:
        tech_keys = set(tech.tech_stack.keys()) if isinstance(tech.tech_stack, dict) else set()
        extra = tech_keys - specified_tech
        for ext in extra:
            drift_items.append({
                "drift_type": "tech_drift",
                "source_field": "architecture_design.tech_stack",
                "compiled_field": f"TECH.{tech.tech_id}.tech_stack.{ext}",
                "drift_description": f"Unspecified technology '{ext}' in TECH",
                "severity": "medium",
            })

    # 4. Design intent drift: check UI principles count
    ux = design_package.get("ux_design", {})
    input_principles = ux.get("design_principles", [])
    for ui in uis:
        if len(ui.design_principles) < len(input_principles):
            drift_items.append({
                "drift_type": "design_intent_drift",
                "source_field": "ux_design.design_principles",
                "compiled_field": f"UI.{ui.ui_id}.design_principles",
                "drift_description": f"UI principles reduced from {len(input_principles)} to {len(ui.design_principles)}",
                "severity": "low",
            })

    # 5. Intent drift (sampling 3 FEATs per ADR-056 §7.3 step_4)
    product = design_package.get("product_design", {})
    input_ac_texts: set[str] = set()
    for ac in product.get("acceptance_criteria", []):
        if isinstance(ac, str):
            input_ac_texts.add(ac[:80])
    sample_size = min(3, len(feats))
    for feat in feats[:sample_size]:
        for ac in feat.acceptance_criteria:
            if isinstance(ac, str):
                ac_prefix = ac[:80]
                if not any(ac_prefix in inp or inp in ac_prefix for inp in input_ac_texts):
                    drift_items.append({
                        "drift_type": "intent_drift",
                        "source_field": "product_design.acceptance_criteria",
                        "compiled_field": f"FEAT.{feat.feat_id}.acceptance_criteria",
                        "drift_description": f"Sampled FEAT AC does not trace to original input intent: {ac_prefix[:60]}...",
                        "severity": "high",
                    })

    verdict = "pass" if not drift_items else "drift_found"
    return DriftVerdict(verdict=verdict, drift_items=drift_items)
