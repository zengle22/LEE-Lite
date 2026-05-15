"""Dimension Quality Gate — SSOT chain per-dimension grading.

Each dimension is scored 0-100 against ITERATION-DOCUMENT-CHECKLIST.md
requirements. Score >= 90 = Grade A. Any dimension below A blocks Freeze.

Truth source: ADR-056 §step_4_5_dimension_quality_gate.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DimensionQualityVerdict:
    """Result of a single dimension quality gate."""

    dimension: str
    score: int
    grade: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    auto_repairable: bool = False
    human_required: bool = False


def _score_to_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# NEW: helper functions
# ---------------------------------------------------------------------------

def _is_truncated(text: str | None, min_len: int = 80) -> bool:
    """Detect text truncation or incomplete ending.
    
    For short titles (< min_len), only detect explicit truncation markers.
    For long prose (> min_len), also require sentence-ending punctuation.
    """
    if not text:
        return False
    text = text.strip()
    if text.endswith(("...", "…", "未完待续", "TBD", "TODO")):
        return True
    # Short titles/captions don't need sentence punctuation
    if len(text) < min_len:
        return False
    # For longer prose, check sentence-ending punctuation
    last_punct = max(text.rfind(p) for p in "。！？.!?")
    if last_punct <= 0 or last_punct < len(text) * 0.8:
        return True
    after_last = text[last_punct + 1 :].strip()
    if after_last and not any(after_last.startswith(p) for p in "[(<{【「（"):
        return True
    return False


def _has_chapter_number_prefix(text: str | None) -> bool:
    """Detect source document chapter number leakage like '9.1 '."""
    if not text:
        return False
    return bool(re.search(r"^\d+\.\d*\s+", text.strip()))


def _has_duplicate_items(items: list[Any]) -> bool:
    """Detect duplicate elements in a list."""
    if not items or len(items) < 2:
        return False
    seen = set()
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            return True
        seen.add(key)
    return False


def _is_valid_url_path(path: str | None) -> bool:
    """Validate RESTful URL path format.
    
    Accepts versioned paths (/v1/...) and well-known API prefixes (/api/...).
    """
    if not path:
        return False
    if re.search(r"[\u4e00-\u9fff（）]", path):
        return False
    if "//" in path or path.endswith("/"):
        return False
    # Versioned paths (/v1/users/{id})
    if re.match(r"^/v\d+(/[A-Za-z0-9_\-{}]+)+$", path):
        return True
    # Well-known API prefixes (/api/ai/conversation/stream)
    if re.match(r"^/api(/[A-Za-z0-9_\-{}]+)+$", path):
        return True
    # Generic REST paths with at least 2 segments (/health, /webhook)
    if re.match(r"^/[A-Za-z0-9_\-{}]+(/[A-Za-z0-9_\-{}]+)+$", path):
        return True
    return False


def _has_mixed_language_keys(obj: dict[str, Any]) -> bool:
    """Detect mixed Chinese/English keys in same dict."""
    if not isinstance(obj, dict) or len(obj) < 2:
        return False
    has_cn = False
    has_en = False
    for k in obj.keys():
        if re.search(r"[\u4e00-\u9fff]", str(k)):
            has_cn = True
        elif re.match(r"^[a-z_][a-z0-9_]*$", str(k), re.I):
            has_en = True
    return has_cn and has_en


def _is_structured_list(value: Any) -> bool:
    """Check if value is a structured list of dicts (title+description)."""
    if not isinstance(value, list) or not value:
        return False
    return all(isinstance(item, dict) and ("title" in item or "description" in item) for item in value)


def _has_flat_schema(schema: Any) -> bool:
    """Check if schema uses flat format (field: string) instead of nested."""
    if not isinstance(schema, dict) or not schema:
        return False
    for v in schema.values():
        if isinstance(v, str):
            return True
    return False


def _impl_redundancy_score(impls: list[Any]) -> float:
    """Compute max pairwise similarity of tech_context/arch_context/api_context across IMPL files."""
    if len(impls) < 2:
        return 0.0
    max_sim = 0.0
    contexts = []
    for impl in impls:
        ctx = {}
        for attr in ("tech_context", "arch_context", "api_context"):
            val = getattr(impl, attr, None)
            if val and isinstance(val, dict):
                # Exclude epic-specific diff markers from redundancy calc
                filtered = {k: v for k, v in val.items() if not k.startswith("_")}
                if filtered:
                    ctx[attr] = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
            elif val:
                ctx[attr] = json.dumps(val, sort_keys=True, ensure_ascii=False)
        contexts.append(ctx)
    for i in range(len(contexts)):
        for j in range(i + 1, len(contexts)):
            keys = set(contexts[i].keys()) & set(contexts[j].keys())
            if not keys:
                continue
            matches = sum(1 for k in keys if contexts[i][k] == contexts[j][k])
            sim = matches / len(keys)
            max_sim = max(max_sim, sim)
    return max_sim


def _is_substantive(text: str | None, min_len: int = 50) -> bool:
    """Check that text is not empty, not a document title, and has substance."""
    if not text or len(text) < min_len:
        return False
    low = text.lower()
    noise_phrases = ("文档", "pre-ssot", "design package", "readme", "draft", "todo", "tbd")
    return not any(p in low for p in noise_phrases)


def _has_nonempty(obj: Any, attr: str) -> bool:
    """Safely check that object's attribute is non-empty list/dict/str."""
    if obj is None:
        return False
    val = getattr(obj, attr, None)
    if val is None:
        return False
    if isinstance(val, (list, dict, str)):
        return len(val) > 0
    return True


def _first_item(obj_list: list[Any]) -> Any:
    """Return first item from a list, or None."""
    return obj_list[0] if obj_list else None


# ---------------------------------------------------------------------------
# SRC
# ---------------------------------------------------------------------------

def _check_src(src: Any | None) -> DimensionQualityVerdict:
    score = 0
    blockers: list[str] = []
    warnings: list[str] = []

    if src is None:
        return DimensionQualityVerdict(
            "src", 0, "F",
            blockers=["SRC object missing"],
            human_required=True,
        )

    # 15: problem_domain has substance
    if _is_substantive(getattr(src, "problem_domain", None)):
        score += 15
    else:
        blockers.append("problem_domain is empty or is document title")

    # 15: business_goal has substance
    if _is_substantive(getattr(src, "business_goal", None)):
        score += 15
    else:
        blockers.append("business_goal is empty or is document title")

    # 10: target_users present
    if _has_nonempty(src, "target_users"):
        score += 10
    else:
        blockers.append("target_users is empty")

    # 10: triggering_scenarios present
    if _has_nonempty(src, "triggering_scenarios"):
        score += 10
    else:
        blockers.append("triggering_scenarios is empty")

    # 15: scope_boundaries has In and Out
    sb = getattr(src, "scope_boundaries", []) or []
    has_in = any(str(x).startswith("In:") for x in sb)
    has_out = any(str(x).startswith("Out:") for x in sb)
    if has_in and has_out and len(sb) >= 3:
        score += 15
    elif has_in or has_out:
        warnings.append("scope_boundaries incomplete (missing In or Out)")
        score += 8
    else:
        blockers.append("scope_boundaries is empty")

    # 10: non_goals present
    if _has_nonempty(src, "non_goals"):
        score += 10
    else:
        blockers.append("non_goals is empty")

    # 10: global_constraints present
    if _has_nonempty(src, "global_constraints"):
        score += 10
    else:
        warnings.append("global_constraints is empty")
        score += 5

    # 10: epics with feats
    epics = getattr(src, "epics", []) or []
    if epics and all(len(getattr(e, "feats", []) or []) > 0 for e in epics):
        score += 10
    else:
        warnings.append("Some epics have no feats")
        score += 5

    # NEW: semantic checks for epics
    for epic in epics:
        cn = getattr(epic, "capability_name", "") or ""
        if _has_chapter_number_prefix(cn):
            blockers.append(f"EPIC {getattr(epic, 'epic_id', '?')} capability_name contains chapter number: '{cn[:50]}'")
            score -= 5
        if _is_truncated(cn):
            warnings.append(f"EPIC {getattr(epic, 'epic_id', '?')} capability_name may be truncated")

    # NEW: truncation check for key text fields
    for field in ("problem_domain", "business_goal"):
        val = getattr(src, field, None)
        if val and _is_truncated(val):
            warnings.append(f"{field} may be truncated")

    grade = _score_to_grade(score)
    auto_repairable = len(blockers) > 0 and not any(
        "missing" in b.lower() and "object" in b.lower() for b in blockers
    )
    return DimensionQualityVerdict(
        "src", score, grade,
        blockers=blockers, warnings=warnings,
        auto_repairable=auto_repairable,
    )


# ---------------------------------------------------------------------------
# TECH
# ---------------------------------------------------------------------------

def _check_tech(techs: list[Any]) -> DimensionQualityVerdict:
    score = 0
    blockers: list[str] = []
    warnings: list[str] = []

    tech = _first_item(techs)
    if tech is None:
        return DimensionQualityVerdict(
            "tech", 0, "F",
            blockers=["TECH object missing"],
            human_required=True,
        )

    # 20: tech_stack present
    ts = getattr(tech, "tech_stack", None)
    if isinstance(ts, list) and len(ts) >= 5:
        score += 20
    elif isinstance(ts, list) and len(ts) >= 1:
        warnings.append("tech_stack has fewer than 5 items")
        score += 12
    elif isinstance(ts, dict) and len(ts) >= 3:
        score += 20
    else:
        blockers.append("tech_stack is empty")

    # 20: sync_async present
    sa = getattr(tech, "sync_async", None)
    if sa and len(sa) > 0:
        score += 20
    else:
        blockers.append("sync_async is empty")

    # 20: non_functional present
    nf = getattr(tech, "non_functional", None)
    if nf and len(nf) > 0:
        score += 20
    else:
        blockers.append("non_functional is empty")

    # 20: constraints present
    if _has_nonempty(tech, "constraints"):
        score += 20
    else:
        blockers.append("constraints is empty")

    # 20: risks present
    if _has_nonempty(tech, "risks"):
        score += 20
    else:
        blockers.append("risks is empty")

    # NEW: check for duplicate risks
    risks = getattr(tech, "risks", [])
    if _has_duplicate_items(risks):
        blockers.append("risks contains duplicate entries")
        score -= 10

    # NEW: check constraints and non_functional are structured
    constraints = getattr(tech, "constraints", None)
    if constraints and isinstance(constraints, list) and not _is_structured_list(constraints):
        warnings.append("TECH constraints should be structured list (title+description)")

    non_functional = getattr(tech, "non_functional", None)
    if non_functional and isinstance(non_functional, (str, list)):
        if isinstance(non_functional, str) or (isinstance(non_functional, list) and non_functional and isinstance(non_functional[0], str)):
            warnings.append("TECH non_functional should be structured list (title+description)")

    grade = _score_to_grade(score)
    return DimensionQualityVerdict(
        "tech", score, grade,
        blockers=blockers, warnings=warnings,
        auto_repairable=len(blockers) > 0,
    )


# ---------------------------------------------------------------------------
# ARCH
# ---------------------------------------------------------------------------

def _check_arch(archs: list[Any]) -> DimensionQualityVerdict:
    score = 0
    blockers: list[str] = []
    warnings: list[str] = []

    arch = _first_item(archs)
    if arch is None:
        return DimensionQualityVerdict(
            "arch", 0, "F",
            blockers=["ARCH object missing"],
            human_required=True,
        )

    # 15: target_architecture present
    if _is_substantive(getattr(arch, "target_architecture", None), min_len=30):
        score += 15
    else:
        blockers.append("target_architecture is empty")

    # 15: layering present
    if _has_nonempty(arch, "layering"):
        score += 15
    else:
        blockers.append("layering is empty")

    # 15: data_flow present
    if _has_nonempty(arch, "data_flow"):
        score += 15
    else:
        blockers.append("data_flow is empty")

    # 15: storage present
    if _has_nonempty(arch, "storage"):
        score += 15
    else:
        blockers.append("storage is empty")

    # 15: integration present
    if _has_nonempty(arch, "integration"):
        score += 15
    else:
        blockers.append("integration is empty")

    # 15: frozen_contracts present
    if _has_nonempty(arch, "frozen_contracts"):
        score += 15
    else:
        warnings.append("frozen_contracts is empty")
        score += 5

    # 10: constraints present
    if _has_nonempty(arch, "constraints"):
        score += 10
    else:
        warnings.append("constraints is empty")
        score += 5

    # NEW: check data_flow titles for chapter number drift
    data_flow = getattr(arch, "data_flow", None)
    if isinstance(data_flow, dict):
        for title in data_flow.keys():
            if _has_chapter_number_prefix(title):
                blockers.append(f"ARCH data_flow title contains chapter number: '{title}'")
                score -= 5

    # NEW: check layering has module names
    layering = getattr(arch, "layering", None)
    if isinstance(layering, dict):
        layer_text = json.dumps(layering, ensure_ascii=False).lower()
        if not any(mod in layer_text for mod in ("transport", "handler", "service", "repository", "controller", "dao")):
            warnings.append("ARCH layering may lack key module names")

    grade = _score_to_grade(score)
    return DimensionQualityVerdict(
        "arch", score, grade,
        blockers=blockers, warnings=warnings,
        auto_repairable=len(blockers) > 0,
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _check_api(apis: list[Any]) -> DimensionQualityVerdict:
    score = 0
    blockers: list[str] = []
    warnings: list[str] = []

    api = _first_item(apis)
    if api is None:
        return DimensionQualityVerdict(
            "api", 0, "F",
            blockers=["API object missing"],
            human_required=True,
        )

    endpoints = getattr(api, "endpoints", []) or []
    if not endpoints:
        blockers.append("endpoints is empty")
        return DimensionQualityVerdict("api", 0, "F", blockers=blockers, warnings=warnings)

    # Per-unit integrity check for each endpoint
    required_fields = ["path", "method", "handler", "priority", "request_schema", "response_schema", "error_codes"]
    enriched_count = 0
    error_count = 0
    flat_schema_count = 0
    mixed_key_count = 0
    invalid_path_count = 0

    for idx, ep in enumerate(endpoints):
        if not isinstance(ep, dict):
            blockers.append(f"Endpoint[{idx}] is not a dict")
            continue

        ep_path = ep.get("path", ep.get("路径", ""))
        ep_method = ep.get("method", ep.get("方法", ""))

        # Check core fields per endpoint (no averaging allowed)
        # GET endpoints may legitimately have no request body
        _fields = list(required_fields)
        if ep_method and str(ep_method).upper() == "GET":
            _fields = [f for f in _fields if f != "request_schema"]
        missing = []
        source_issues = []
        ep_source = ep.get("_source", {})
        for field in _fields:
            if not ep.get(field):
                missing.append(field)
            else:
                # Source tracing check: auto_generated fields are treated as missing
                # auto_derived (naming convention) is acceptable for handler/priority
                src = ep_source.get(field, "unknown")
                if src == "auto_generated":
                    source_issues.append(f"{field}=auto_generated")
                    missing.append(f"{field}(auto_generated)")
                elif src == "inferred":
                    source_issues.append(f"{field}=inferred")
                elif src == "auto_derived" and field not in ("handler", "priority"):
                    source_issues.append(f"{field}=auto_derived")
        if missing:
            blockers.append(f"Endpoint {ep_method} {ep_path} missing: {', '.join(missing)}")
        elif source_issues:
            # Fields exist but are auto-generated/inferred — downgrade to partial credit
            enriched_count += 0.5
            warnings.append(f"Endpoint {ep_method} {ep_path} has inferred/auto_generated fields: {', '.join(source_issues)}")
        else:
            enriched_count += 1

        # URL path validity
        if ep_path and not _is_valid_url_path(ep_path):
            invalid_path_count += 1
            blockers.append(f"Endpoint path invalid or contains non-ASCII: {ep_path}")

        # Mixed language keys
        if _has_mixed_language_keys(ep):
            mixed_key_count += 1
            blockers.append(f"Endpoint {ep_path} has mixed Chinese/English keys")

        # Schema format consistency (flat vs nested)
        for schema_field in ("request_schema", "response_schema"):
            schema = ep.get(schema_field)
            if schema and _has_flat_schema(schema):
                flat_schema_count += 1
                warnings.append(f"Endpoint {ep_path} {schema_field} uses flat format")

        # Error codes presence
        if ep.get("error_codes"):
            error_count += 1

    # Scoring: per-endpoint integrity must be 100%, not averaged
    if enriched_count == len(endpoints):
        score += 50
    elif enriched_count >= len(endpoints) * 0.9:
        score += 30
        warnings.append(f"Only {enriched_count}/{len(endpoints)} endpoints have all core fields")
    else:
        score += 10
        warnings.append(f"Only {enriched_count}/{len(endpoints)} endpoints have all core fields")

    if error_count == len(endpoints):
        score += 20
    elif error_count >= len(endpoints) * 0.9:
        score += 10
        warnings.append(f"Only {error_count}/{len(endpoints)} endpoints have error_codes")
    else:
        warnings.append(f"Only {error_count}/{len(endpoints)} endpoints have error_codes")

    if invalid_path_count == 0:
        score += 10
    else:
        warnings.append(f"{invalid_path_count} endpoint paths invalid")

    if mixed_key_count == 0:
        score += 10
    else:
        warnings.append(f"{mixed_key_count} endpoints have mixed language keys")

    if flat_schema_count == 0:
        score += 10
    else:
        warnings.append(f"{flat_schema_count} schemas use flat format")

    # version_strategy
    vs = getattr(api, "version_strategy", "")
    if vs and vs != "semver":
        score += 10
    else:
        warnings.append("version_strategy is default 'semver'")
        score += 5

    # sequence_diagrams
    sd = getattr(api, "sequence_diagrams", None)
    if sd and len(sd) > 0:
        score += 20
    else:
        blockers.append("sequence_diagrams is empty")

    grade = _score_to_grade(score)
    return DimensionQualityVerdict(
        "api", score, grade,
        blockers=blockers, warnings=warnings,
        auto_repairable=len(blockers) > 0,
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def _check_ui(uis: list[Any]) -> DimensionQualityVerdict:
    score = 0
    blockers: list[str] = []
    warnings: list[str] = []

    ui = _first_item(uis)
    if ui is None:
        return DimensionQualityVerdict(
            "ui", 0, "F",
            blockers=["UI object missing"],
            human_required=True,
        )

    checks = [
        ("design_principles", 15, "设计原则"),
        ("interaction_flow", 15, "交互流程"),
        ("state_expression", 15, "状态表达"),
        ("design_tokens", 10, "设计令牌"),
        ("copy_style", 10, "文案风格"),
        ("platform_strategy", 10, "平台差异策略"),
        ("error_state_ux", 15, "错误状态 UX"),
    ]

    for attr, points, label in checks:
        if _has_nonempty(ui, attr):
            score += points
        else:
            blockers.append(f"{attr} ({label}) is empty")

    # 10: prototype present or referenced
    proto = getattr(ui, "prototype", "")
    if proto and len(str(proto)) > 5:
        score += 10
    else:
        warnings.append("prototype is empty")
        score += 5

    # NEW: semantic checks for UI content
    proto = getattr(ui, "prototype", "")
    if proto and isinstance(proto, str):
        if _is_truncated(proto):
            warnings.append("prototype may be truncated")

    # Check card specs, acknowledge, input normalization hints
    ui_raw = json.dumps({k: v for k, v in ui.__dict__.items() if not k.startswith("_")}, ensure_ascii=False).lower()
    if "card" not in ui_raw:
        warnings.append("UI may lack card specifications")
    if "acknowledge" not in ui_raw:
        warnings.append("UI may lack acknowledge flow")
    if "normalization" not in ui_raw:
        warnings.append("UI may lack input normalization spec")

    grade = _score_to_grade(score)
    return DimensionQualityVerdict(
        "ui", score, grade,
        blockers=blockers, warnings=warnings,
        auto_repairable=len(blockers) > 0,
    )


# ---------------------------------------------------------------------------
# IMPL
# ---------------------------------------------------------------------------

def _check_impl(impls: list[Any]) -> DimensionQualityVerdict:
    score = 0
    blockers: list[str] = []
    warnings: list[str] = []

    if not impls:
        return DimensionQualityVerdict(
            "impl", 0, "F",
            blockers=["IMPL list empty"],
            human_required=True,
        )

    # Check all files, not just first one
    epic_keys = []
    all_test_layering = []
    for idx, impl in enumerate(impls):
        allowed = getattr(impl, "allowed_scope", {}) or {}
        forbidden = getattr(impl, "forbidden_scope", {}) or {}
        test_g = getattr(impl, "test_guidance", {}) or {}
        req_ctx = getattr(impl, "requirement_context", {}) or {}

        # Track epic_keys for grouping validation
        ekey = req_ctx.get("epic_key", "") if isinstance(req_ctx, dict) else getattr(req_ctx, "epic_key", "")
        if ekey:
            epic_keys.append(ekey)

        # Per-file checks
        if not allowed.get("directories"):
            blockers.append(f"IMPL[{idx}] allowed_scope.directories is empty")
        if not allowed.get("files"):
            blockers.append(f"IMPL[{idx}] allowed_scope.files is empty")
        if not (forbidden.get("files") or forbidden.get("directories")):
            blockers.append(f"IMPL[{idx}] forbidden_scope is empty")
        if not test_g.get("boundary_conditions"):
            blockers.append(f"IMPL[{idx}] test_guidance.boundary_conditions is empty")
        if not test_g.get("test_layering"):
            blockers.append(f"IMPL[{idx}] test_guidance.test_layering is empty")

        trigger = req_ctx.get("trigger", "") if isinstance(req_ctx, dict) else getattr(req_ctx, "trigger", "")
        if not trigger or len(str(trigger)) < 5:
            blockers.append(f"IMPL[{idx}] requirement_context.trigger is empty")

        # AC prefix matching check
        acs = req_ctx.get("acceptance_criteria", []) if isinstance(req_ctx, dict) else []
        tl = test_g.get("test_layering", []) if isinstance(test_g, dict) else []
        if acs and tl:
            ac_prefixes = set()
            for ac in acs:
                m = re.search(r'AC-(\d+)', str(ac))
                if m:
                    ac_prefixes.add(m.group(1))
            mismatched = 0
            for line in tl:
                if isinstance(line, str) and re.search(r'AC-\d+', line):
                    if not any(f"AC-{p}" in line for p in ac_prefixes):
                        mismatched += 1
            if mismatched > 0:
                warnings.append(f"IMPL[{idx}] {mismatched} test_layering entries don't match epic AC prefixes")

        if tl:
            all_test_layering.extend(tl)

    # Cross-file grouping validation
    if len(set(epic_keys)) != len(epic_keys):
        blockers.append("Duplicate epic_key across IMPL files")
    if len(impls) > 1 and len(impls) > len(set(epic_keys)) * 2:
        warnings.append(f"IMPL count {len(impls)} seems high vs {len(set(epic_keys))} unique epics")

    # Cross-file redundancy detection
    redundancy = _impl_redundancy_score(impls)
    if redundancy > 0.95:
        blockers.append(f"IMPL files have {int(redundancy*100)}% redundant cross-axis contexts (tech/arch/api)")
    elif redundancy > 0.8:
        warnings.append(f"IMPL files have {int(redundancy*100)}% similar cross-axis contexts")

    # Aggregate scoring
    score = min(100, max(0, 100 - len(blockers) * 15 - len(warnings) * 5))

    grade = _score_to_grade(score)
    return DimensionQualityVerdict(
        "impl", score, grade,
        blockers=blockers, warnings=warnings,
        auto_repairable=len(blockers) > 0,
    )


# ---------------------------------------------------------------------------
# Cross-axis traceability
# ---------------------------------------------------------------------------

def _check_cross_axis_traceability(chain: dict[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    src = chain.get("src")
    epics = chain.get("epics", [])
    impls = chain.get("impls", [])
    apis = chain.get("apis", [])
    feats = chain.get("feats", [])

    # SRC epic count vs IMPL file count
    if src and epics and impls:
        if len(impls) != len(epics):
            warnings.append(f"SRC has {len(epics)} epics but {len(impls)} IMPL files")

    # API endpoint completeness: check FEAT AC references
    api_list = []
    if apis:
        api_list = getattr(apis[0], "endpoints", []) or []
    api_paths = {ep.get("path", ep.get("路径", "")) for ep in api_list if isinstance(ep, dict)}

    if feats:
        for feat in feats:
            ac_list = getattr(feat, "main_flow", []) or []
            for ac in ac_list:
                if isinstance(ac, str):
                    for path in api_paths:
                        if path and path in ac:
                            break
                    else:
                        # Check if AC contains path-like strings
                        paths_in_ac = re.findall(r'/v\d+/[\w\-/{}]+', ac)
                        for p in paths_in_ac:
                            if p not in api_paths:
                                warnings.append(f"FEAT {getattr(feat, 'feat_id', '?')} AC references endpoint {p} not found in API")

    # FRZ statistics anomaly
    frz = chain.get("frz")
    if frz:
        total_ac = getattr(frz, "total_ac", None)
        covered_ac = getattr(frz, "covered_ac", None)
        if total_ac == 0 or total_ac is None:
            blockers.append("FRZ total_ac is 0 or missing")
        if covered_ac == 0 or covered_ac is None:
            blockers.append("FRZ covered_ac is 0 or missing")
        if total_ac is not None and covered_ac is not None and covered_ac > total_ac:
            blockers.append("FRZ covered_ac > total_ac")

    return blockers, warnings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_dimension_quality(chain: dict[str, Any]) -> list[DimensionQualityVerdict]:
    """Run all dimension quality gates against the compiled SSOT chain.

    Args:
        chain: Dict with keys src, epics, feats, techs, archs, apis, uis, impls.

    Returns:
        List of DimensionQualityVerdict, one per dimension.
    """
    verdicts = [
        _check_src(chain.get("src")),
        _check_tech(chain.get("techs", [])),
        _check_arch(chain.get("archs", [])),
        _check_api(chain.get("apis", [])),
        _check_ui(chain.get("uis", [])),
        _check_impl(chain.get("impls", [])),
    ]

    # Cross-axis traceability checks
    cross_axis_blockers, cross_axis_warnings = _check_cross_axis_traceability(chain)
    if cross_axis_blockers or cross_axis_warnings:
        # Attach to impl dimension as the aggregation point, or create a new pseudo-dimension
        impl_verdict = next((v for v in verdicts if v.dimension == "impl"), None)
        if impl_verdict:
            impl_verdict.blockers.extend(cross_axis_blockers)
            impl_verdict.warnings.extend(cross_axis_warnings)
            # Re-score
            penalty = len(cross_axis_blockers) * 10 + len(cross_axis_warnings) * 3
            impl_verdict.score = max(0, impl_verdict.score - penalty)
            impl_verdict.grade = _score_to_grade(impl_verdict.score)

    return verdicts


def all_dimensions_grade_a(verdicts: list[DimensionQualityVerdict]) -> bool:
    """Return True if every dimension is Grade A (score >= 90)."""
    return all(v.grade == "A" for v in verdicts)


def get_quality_report(verdicts: list[DimensionQualityVerdict]) -> dict[str, Any]:
    """Generate a structured quality report for YAML/JSON output."""
    return {
        "verdict": "pass" if all_dimensions_grade_a(verdicts) else "blocked",
        "dimensions": [
            {
                "dimension": v.dimension,
                "score": v.score,
                "grade": v.grade,
                "blockers": v.blockers,
                "warnings": v.warnings,
                "auto_repairable": v.auto_repairable,
                "human_required": v.human_required,
            }
            for v in verdicts
        ],
        "summary": {
            "total_dimensions": len(verdicts),
            "a_grade_count": sum(1 for v in verdicts if v.grade == "A"),
            "blocker_count": sum(len(v.blockers) for v in verdicts),
            "warning_count": sum(len(v.warnings) for v in verdicts),
        },
    }
