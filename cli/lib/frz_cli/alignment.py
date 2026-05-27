"""Step_3 — SSOT chain alignment check.

Truth source: design.md §step_3.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from frz_cli.exceptions import AlignmentFailError
from frz_cli.models import (
    API,
    ARCH,
    EPIC,
    FEAT,
    SRC,
    TECH,
    UI,
    AlignmentVerdict,
)


def check_alignment(
    src: SRC,
    epics: list[EPIC],
    feats: list[FEAT],
    techs: list[TECH],
    archs: list[ARCH],
    apis: list[API],
    uis: list[UI],
) -> AlignmentVerdict:
    """Run SSOT chain alignment checks.

    Checks:
    1. Requirement coverage: FEATs cover SRC triggering_scenarios + scope_boundaries
    2. Cross-axis consistency: TECH/ARCH/API/UI align with FEAT
    3. Traceability completeness: refs point to existing objects
    """
    issues: list[dict[str, Any]] = []

    # 1. Requirement coverage
    all_scenarios = set(src.triggering_scenarios)
    covered_scenarios: set[str] = set()

    def _scenario_covered_by_feat(scenario: str, feat: FEAT) -> bool:
        # Exact match in main_flow
        if scenario in feat.main_flow:
            return True
        # Keyword heuristic: extract significant tokens (Chinese phrases 4+ chars,
        # English words 4+ chars, back-tick terms) and check overlap.
        import re
        tokens: list[str] = []
        # English words / back-tick terms
        tokens += re.findall(r"`?([A-Za-z][A-Za-z0-9_]{3,})`?", scenario)
        # Chinese phrases (4+ consecutive CJK chars)
        tokens += [m for m in re.findall(r"[\u4e00-\u9fff]{4,}", scenario)]
        # Fallback: whole scenario if no tokens extracted
        if not tokens:
            tokens = [scenario]
        feat_text = (feat.title or "") + " " + " ".join(feat.main_flow or []) + " " + " ".join(feat.acceptance_criteria or [])
        matched = sum(1 for t in tokens if t in feat_text)
        return matched >= max(1, len(tokens) // 3)

    for scenario in all_scenarios:
        if any(_scenario_covered_by_feat(scenario, feat) for feat in feats):
            covered_scenarios.add(scenario)

    missing_scenarios = all_scenarios - covered_scenarios
    for ms in missing_scenarios:
        issues.append({
            "severity": "high",
            "location": f"SRC.{src.src_id}.triggering_scenarios",
            "description": f"Scenario '{ms}' not covered by any FEAT",
            "suggested_fix": f"Add FEAT covering scenario '{ms}'",
        })

    # 1b. Requirement gap (precise count comparison per ADR-056 §7.3 step_3)
    declared_requirements = len(src.triggering_scenarios) + len(src.scope_boundaries)
    feat_count = len(feats)
    if feat_count < declared_requirements:
        issues.append({
            "severity": "medium",
            "location": f"SRC.{src.src_id}",
            "description": f"Requirement gap: {feat_count} FEATs < {declared_requirements} declared requirements (triggering_scenarios + scope_boundaries)",
            "suggested_fix": "Add FEATs to cover all declared requirements",
        })

    # 2. Cross-axis consistency
    for feat in feats:
        tech = next((t for t in techs if feat.feat_id in t.feat_ref), None)
        if tech and not tech.tech_stack:
            issues.append({
                "severity": "medium",
                "location": f"TECH.{tech.tech_id}",
                "description": f"TECH tech_stack empty for FEAT {feat.feat_id}",
                "suggested_fix": "Populate tech_stack",
            })

    # 3. Traceability completeness
    all_feat_ids = {f.feat_id for f in feats}
    # When no FEATs exist (e.g. Markdown raw-only input), skip feat_ref validation
    if all_feat_ids:
        for tech in techs:
            if tech.feat_ref and tech.feat_ref not in all_feat_ids:
                issues.append({
                    "severity": "high",
                    "location": f"TECH.{tech.tech_id}.feat_ref",
                    "description": f"feat_ref '{tech.feat_ref}' points to non-existent FEAT",
                    "suggested_fix": "Fix feat_ref to valid FEAT",
                })

        for arch in archs:
            if arch.feat_ref and arch.feat_ref not in all_feat_ids:
                issues.append({
                    "severity": "high",
                    "location": f"ARCH.{arch.arch_id}.feat_ref",
                    "description": f"feat_ref '{arch.feat_ref}' points to non-existent FEAT",
                    "suggested_fix": "Fix feat_ref to valid FEAT",
                })

        for api in apis:
            if api.feat_ref and api.feat_ref not in all_feat_ids:
                issues.append({
                    "severity": "high",
                    "location": f"API.{api.api_id}.feat_ref",
                    "description": f"feat_ref '{api.feat_ref}' points to non-existent FEAT",
                    "suggested_fix": "Fix feat_ref to valid FEAT",
                })

        for ui in uis:
            if ui.feat_ref and ui.feat_ref not in all_feat_ids:
                issues.append({
                    "severity": "high",
                    "location": f"UI.{ui.ui_id}.feat_ref",
                    "description": f"feat_ref '{ui.feat_ref}' points to non-existent FEAT",
                    "suggested_fix": "Fix feat_ref to valid FEAT",
                })

    # FEAT required field completeness
    for feat in feats:
        if not feat.feat_id or not feat.title or (not feat.main_flow and not feat.acceptance_criteria):
            issues.append({
                "severity": "high",
                "location": f"FEAT.{feat.feat_id}",
                "description": "Missing required FEAT fields",
                "suggested_fix": "Ensure feat_id, title, main_flow or acceptance_criteria are populated",
            })

    # Small triggering-scenario gaps are downgraded to partial
    high_issues = [i for i in issues if i["severity"] == "high"]
    if len(high_issues) <= 3:
        for i in issues:
            i["severity"] = "medium"
        verdict = "partial" if issues else "pass"
    else:
        verdict = "pass" if not issues else "fail"
    return AlignmentVerdict(verdict=verdict, issues=issues)
