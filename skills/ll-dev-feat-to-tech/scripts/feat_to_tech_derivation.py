#!/usr/bin/env python3
"""
Derivation helpers for the lite-native feat-to-tech runtime.
"""

from __future__ import annotations

from typing import Any

from feat_to_tech_common import ensure_list, unique_strings


ARCH_KEYWORDS = [
    "架构",
    "architecture",
    "boundary",
    "边界",
    "module",
    "模块",
    "subsystem",
    "topology",
    "调用链",
    "io",
    "path",
    "registry",
    "external gate",
    "cross-skill",
]

STRONG_API_KEYWORDS = [
    "api",
    "接口",
    "contract",
    "schema",
    "request",
    "response",
    "webhook",
]

WEAK_API_KEYWORDS = [
    "event",
    "message",
    "proposal",
    "decision",
    "consumer",
    "provider",
    "handoff",
    "queue",
]

NEGATION_MARKERS = [
    "不",
    "无",
    "without",
    "no ",
    "not ",
    "do not",
]


def feature_text(feature: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            parts.append(value)
    for key in ["scope", "constraints", "dependencies", "outputs", "non_goals"]:
        parts.extend(ensure_list(feature.get(key)))
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            parts.extend(
                [
                    str(check.get("scenario") or ""),
                    str(check.get("given") or ""),
                    str(check.get("when") or ""),
                    str(check.get("then") or ""),
                ]
            )
    return "\n".join(parts).lower()


def keyword_hits(feature: dict[str, Any], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    segments: list[str] = []
    for key in ["title", "goal", "derived_axis"]:
        value = str(feature.get(key) or "").strip()
        if value:
            segments.append(value)
    for key in ["scope", "constraints", "dependencies", "outputs", "non_goals"]:
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

    for segment in segments:
        lowered = segment.lower().strip()
        if not lowered:
            continue
        if any(marker in lowered for marker in NEGATION_MARKERS):
            continue
        for keyword in keywords:
            if keyword in lowered and keyword not in hits:
                hits.append(keyword)
    return hits


def build_refs(feature: dict[str, Any], package: Any) -> dict[str, str]:
    feat_ref = str(feature.get("feat_ref") or "").strip()
    feat_suffix = feat_ref.replace("FEAT-", "", 1) if feat_ref.startswith("FEAT-") else feat_ref
    return {
        "feat_ref": feat_ref,
        "tech_ref": f"TECH-{feat_ref}",
        "arch_ref": f"ARCH-{feat_suffix}" if feat_suffix else "",
        "api_ref": f"API-{feat_suffix}" if feat_suffix else "",
        "epic_ref": str(package.feat_json.get("epic_freeze_ref") or ""),
        "src_ref": str(package.feat_json.get("src_root_id") or ""),
    }


def assess_optional_artifacts(feature: dict[str, Any], package: Any) -> dict[str, Any]:
    arch_hits = keyword_hits(feature, ARCH_KEYWORDS)
    strong_api_hits = keyword_hits(feature, STRONG_API_KEYWORDS)
    weak_api_hits = keyword_hits(feature, WEAK_API_KEYWORDS)
    source_refs = ensure_list(feature.get("source_refs")) + ensure_list(package.feat_json.get("source_refs"))

    arch_reasons: list[str] = []
    api_reasons: list[str] = []

    if any(ref.startswith("ARCH-") for ref in source_refs):
        arch_reasons.append("Inherited source refs already point to an upstream architecture object.")
    if len(ensure_list(feature.get("dependencies"))) >= 2:
        arch_reasons.append("The FEAT exposes multiple boundary dependencies that need explicit architectural placement.")
    if len(arch_hits) >= 2:
        arch_reasons.append(f"Architecture-impacting language appears in the FEAT boundary: {', '.join(arch_hits[:4])}.")

    if strong_api_hits:
        api_reasons.append(f"Explicit API/contract language appears in the FEAT boundary: {', '.join(strong_api_hits[:4])}.")
    if any("contract" in item.lower() or "proposal" in item.lower() or "decision" in item.lower() for item in ensure_list(feature.get("outputs"))):
        api_reasons.append("The FEAT outputs already imply a boundary contract or exchange object.")
    if any("consumer" in item.lower() or "provider" in item.lower() for item in ensure_list(feature.get("dependencies"))):
        api_reasons.append("The FEAT depends on explicit consumer/provider coordination.")
    if len(weak_api_hits) >= 3 and any(hit in weak_api_hits for hit in ["decision", "queue", "event", "message"]):
        api_reasons.append(f"Cross-loop exchange semantics require an explicit boundary contract: {', '.join(weak_api_hits[:4])}.")

    arch_required = bool(arch_reasons)
    api_required = bool(api_reasons)

    if not arch_required:
        arch_reasons.append("No architecture-impacting module placement or topology change was detected.")
    if not api_required:
        api_reasons.append("No explicit cross-boundary contract surface was detected.")

    return {
        "arch_required": arch_required,
        "api_required": api_required,
        "arch_rationale": arch_reasons,
        "api_rationale": api_reasons,
    }


def design_focus(feature: dict[str, Any]) -> list[str]:
    items = ensure_list(feature.get("scope"))[:4]
    if len(items) < 3:
        items.extend(ensure_list(feature.get("constraints"))[: 3 - len(items)])
    return unique_strings(items)[:4]


def implementation_rules(feature: dict[str, Any]) -> list[str]:
    rules = ensure_list(feature.get("constraints"))[:4]
    for check in feature.get("acceptance_checks") or []:
        if isinstance(check, dict):
            scenario = str(check.get("scenario") or "").strip()
            then = str(check.get("then") or "").strip()
            if scenario and then:
                rules.append(f"{scenario}: {then}")
    return unique_strings(rules)[:6]


def non_functional_requirements(feature: dict[str, Any], package: Any) -> list[str]:
    refs = ensure_list(feature.get("source_refs")) + ensure_list(package.feat_json.get("source_refs"))
    requirements = [
        "Preserve FEAT, EPIC, and SRC traceability across every emitted design object.",
        "Keep the package freeze-ready by recording execution evidence and supervision evidence.",
        "Do not bypass the FEAT acceptance boundary with task-level sequencing or implementation tickets.",
    ]
    if any(ref.startswith("ADR-") for ref in refs):
        requirements.append("Respect inherited ADR constraints when defining runtime carriers, boundary contracts, and rollout safety.")
    return unique_strings(requirements)


def architecture_topics(feature: dict[str, Any]) -> list[str]:
    topics = ensure_list(feature.get("dependencies"))[:3]
    if len(topics) < 2:
        topics.extend(ensure_list(feature.get("scope"))[: 2 - len(topics)])
    return unique_strings(topics)[:3]


def responsibility_splits(feature: dict[str, Any]) -> list[str]:
    splits: list[str] = []
    for item in ensure_list(feature.get("constraints")) + ensure_list(feature.get("non_goals")):
        lowered = item.lower()
        if any(marker in lowered for marker in ["不", "只", "不得", "only", "must not", "do not", "not ", "leave", "留给"]):
            splits.append(item)
    if len(splits) < 2:
        splits.extend(ensure_list(feature.get("dependencies")))
    if len(splits) < 2:
        splits.extend(ensure_list(feature.get("scope")))
    return unique_strings(splits)[:3]


def api_surfaces(feature: dict[str, Any]) -> list[str]:
    surfaces: list[str] = []
    text = feature_text(feature)
    if "handoff" in text:
        surfaces.append("handoff object contract")
    if "decision" in text or "gate" in text:
        surfaces.append("gate decision contract")
    if "proposal" in text:
        surfaces.append("proposal exchange contract")
    if "consumer" in text or "provider" in text:
        surfaces.append("consumer/provider boundary contract")
    if "event" in text or "message" in text or "queue" in text:
        surfaces.append("event or message contract")
    if not surfaces:
        surfaces.append("feature-specific boundary contract")
    return unique_strings(surfaces)[:4]


def traceability_rows(feature: dict[str, Any], package: Any, refs: dict[str, str]) -> list[dict[str, Any]]:
    source_refs = unique_strings(
        [f"product.epic-to-feat::{package.run_id}", refs["feat_ref"], refs["epic_ref"], refs["src_ref"]]
        + ensure_list(feature.get("source_refs"))
    )
    return [
        {
            "design_section": "Need Assessment",
            "feat_fields": ["scope", "dependencies", "acceptance_checks"],
            "source_refs": source_refs[:4],
        },
        {
            "design_section": "TECH Design",
            "feat_fields": ["goal", "scope", "constraints"],
            "source_refs": source_refs[:4],
        },
        {
            "design_section": "Cross-Artifact Consistency",
            "feat_fields": ["dependencies", "outputs", "acceptance_checks"],
            "source_refs": source_refs[:4],
        },
    ]


def consistency_check(feature: dict[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    checks.append(
        {
            "name": "TECH mandatory",
            "passed": True,
            "detail": "TECH is always emitted for the selected FEAT.",
        }
    )

    if assessment["arch_required"]:
        passed = len(architecture_topics(feature)) >= 2
        checks.append(
            {
                "name": "ARCH coverage",
                "passed": passed,
                "detail": "ARCH is required and carries system-boundary topics.",
            }
        )
        if not passed:
            issues.append("ARCH was required but architecture topics could not be resolved clearly.")
    else:
        checks.append(
            {
                "name": "ARCH omission justified",
                "passed": True,
                "detail": "ARCH is omitted because the FEAT does not require boundary or topology redesign.",
            }
        )

    if assessment["api_required"]:
        passed = len(api_surfaces(feature)) >= 1
        checks.append(
            {
                "name": "API coverage",
                "passed": passed,
                "detail": "API is required and carries at least one contract surface.",
            }
        )
        if not passed:
            issues.append("API was required but no contract surfaces were derived.")
    else:
        checks.append(
            {
                "name": "API omission justified",
                "passed": True,
                "detail": "API is omitted because no explicit cross-boundary contract surface was detected.",
            }
        )

    return {
        "passed": not issues,
        "checks": checks,
        "issues": issues,
    }
