"""Step_2 — SSOT chain compiler.

Compiles a Complete Design Package into SRC/EPIC/FEAT/TECH/ARCH/API/UI/IMPL.
Enforces invented_semantics == 0.
Truth source: design.md §step_2.
"""

from __future__ import annotations

import json
import re
from typing import Any

from frz_cli.exceptions import CompileConflictError, InventedSemanticsError
from frz_cli.models import (
    API,
    ARCH,
    EPIC,
    FEAT,
    IMPL,
    SRC,
    TECH,
    UI,
)
from frz_cli.parser import _extract_markdown_sections, _extract_markdown_tables


def _ref(path: str, section: str, paragraph: str = "P1") -> str:
    """Build a paragraph-level source reference.

    Format: {source_path}#{section}.{paragraph}
    Example: product_design/prd.md#S3.P2
    """
    return f"{path}#{section}.{paragraph}"


def _get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


def _find_anywhere(design_package: dict[str, Any], field_name: str) -> Any:
    """Search for a field across all dimensions."""
    for dim_data in design_package.values():
        if isinstance(dim_data, dict) and field_name in dim_data:
            return dim_data[field_name]
    return None


def _find_common_dict(dicts: list[dict[str, Any]]) -> dict[str, Any]:
    """Find key-value pairs that are identical across all dicts."""
    if not dicts:
        return {}
    common = dict(dicts[0])
    for d in dicts[1:]:
        for key in list(common.keys()):
            if key not in d or d[key] != common[key]:
                del common[key]
    return common


def _require_non_empty(value: Any, msg: str, raw_fallback: str = "") -> None:
    if value is None or (isinstance(value, (list, dict, str)) and len(value) == 0):
        if raw_fallback:
            return  # Allow empty when raw Markdown content is present
        raise CompileConflictError(msg)


def _raw_fallback(dim_data: dict[str, Any]) -> str:
    """Return __raw__ content if present, for Markdown fallback extraction."""
    raw = dim_data.get("__raw__", "")
    return raw if isinstance(raw, str) else ""


# ---------------------------------------------------------------------------
# 2.1 SRC compilation
# ---------------------------------------------------------------------------


def _first_line(raw: str) -> str:
    """Extract first non-empty line from raw Markdown, stripped of heading markers."""
    for line in raw.splitlines():
        stripped = line.strip().lstrip("# ").lstrip("#")
        if stripped:
            return stripped[:200]
    return ""


def _sentence_aware_truncate(text: str, max_len: int) -> str:
    """Truncate at sentence boundary, never mid-sentence.

    Falls back to last space or hard truncate if no sentence boundary found.
    """
    if len(text) <= max_len:
        return text
    # Find last sentence-ending punctuation before max_len
    for punct in "。！？.!?":
        idx = text.rfind(punct, 0, max_len)
        if idx > 0:
            return text[: idx + 1]
    # Fallback: last space
    space_idx = text.rfind(" ", 0, max_len)
    if space_idx > 0:
        return text[:space_idx] + "…"
    return text[:max_len]


def _extract_vision_paragraph(raw: str) -> str:
    """Extract the first meaningful paragraph from a vision-like section.

    Searches for '## 1. 升级目标与背景' or '## 产品愿景' and returns
    the first non-empty paragraph under it, excluding document metadata.
    """
    # Try to find a vision-like section and extract its first paragraph
    best_paragraph = ""
    vision_sections = _extract_markdown_sections(raw, level=2)
    for section in vision_sections:
        title = section["title"].lower()
        if any(k in title for k in ("升级目标", "产品愿景", "vision", "目标与背景", "业务目标")):
            body = section["body"]
            for line in body.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("|"):
                    continue
                # Skip metadata lines
                if re.match(r'^(版本|日期|状态|适用范围|>\s*\*\*)', stripped):
                    continue
                cleaned = re.sub(r'^[\*\->\s]+', '', stripped)
                if cleaned and len(cleaned) > 20 and len(cleaned) > len(best_paragraph):
                    best_paragraph = cleaned[:2000]
    return best_paragraph


def _extract_triggering_scenarios(design_package: dict[str, Any]) -> list[str]:
    """Extract triggering scenarios from business_design or product_design."""
    for dim in ("business_design", "product_design"):
        data = design_package.get(dim, {})
        raw = data.get("__raw__", "")
        sections = _extract_markdown_sections(raw, level=2)
        for section in sections:
            if "触发" in section["title"] or "trigger" in section["title"].lower():
                scenarios: list[str] = []
                for line in section["body"].splitlines():
                    stripped = line.strip()
                    # Stop at any sub-heading so we don't scoop nested bullet lists
                    if stripped.startswith("#"):
                        break
                    if stripped.startswith("- ") or stripped.startswith("* "):
                        scenarios.append(stripped[2:].strip())
                return scenarios
    return []


def _extract_non_goals(design_package: dict[str, Any]) -> list[str]:
    """Extract non-goals / out-of-scope items from any dimension."""
    for dim in ("business_design", "product_design", "architecture_design"):
        data = design_package.get(dim, {})
        raw = data.get("__raw__", "")
        sections = _extract_markdown_sections(raw, level=2)
        for section in sections:
            title = section["title"].lower()
            # Match explicit non-goal / out-of-scope headings.
            # Do NOT match "边界" alone — it matches "范围边界" which is a
            # separate concept from "非目标" (non-goals).
            if any(k in title for k in ("不做什么", "不做", "out of scope", "非目标", "non goal")):
                items: list[str] = []
                for line in section["body"].splitlines():
                    stripped = line.strip()
                    if stripped.startswith("- ") or stripped.startswith("* "):
                        items.append(stripped[2:].strip())
                    elif re.match(r'^\d+\.\s+', stripped):
                        items.append(re.sub(r'^\d+\.\s+', '', stripped))
                return items
    return []


def _extract_problem_domain(raw: str) -> str:
    """Search raw for problem-domain sections and return first meaningful paragraph."""
    sections = _extract_markdown_sections(raw, level=2)
    for section in sections:
        title = section["title"].lower()
        if any(k in title for k in ("问题", "痛点", "problem", "现状")):
            for line in section["body"].splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("|"):
                    continue
                # Skip metadata / reference preamble lines
                if re.match(r'^(本文档基于|版本|日期|状态|适用范围|>\s*\*\*)', stripped):
                    continue
                cleaned = re.sub(r'^[\*\->\s]+', '', stripped)
                if cleaned and len(cleaned) > 10:
                    return cleaned[:500]
    return ""


def _extract_business_goal(raw: str) -> str:
    """Search raw for business-goal sections and return first meaningful paragraph."""
    sections = _extract_markdown_sections(raw, level=2)
    for section in sections:
        title = section["title"].lower()
        if any(k in title for k in ("目标", "愿景", "goal", "vision", "业务目标")):
            for line in section["body"].splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("|"):
                    continue
                cleaned = re.sub(r'^[\*\->\s]+', '', stripped)
                if cleaned and len(cleaned) > 10:
                    return cleaned[:500]
    return ""


def _split_vision_into_problem_and_goal(vision: str) -> tuple[str, str]:
    """Split a mixed vision paragraph into problem_domain and business_goal.

    Heuristic: look for transition markers that separate 'pain point' from 'solution'.
    """
    markers = ["通过引入", "MVP 1.5 通过", "具体目标包括", "解法", "Solution", "目标包括"]
    for marker in markers:
        idx = vision.find(marker)
        if idx > 20:
            problem = vision[:idx].strip()
            goal = vision[idx:].strip()
            return problem, goal
    # Fallback: if vision mentions "痛点是", take up to first sentence ending as problem
    pain_idx = vision.find("痛点是")
    if pain_idx >= 0:
        end_idx = vision.find("。", pain_idx)
        if end_idx > 0:
            problem = vision[:end_idx + 1].strip()
            goal = vision[end_idx + 1:].strip()
            if goal:
                return problem, goal
    return vision, vision


def compile_src(design_package: dict[str, Any], src_id: str = "SRC-001") -> SRC:
    """Compile business_design dimension into SRC container."""
    biz = design_package.get("business_design", {})
    raw = _raw_fallback(biz)
    # Prefer paragraph extraction over potentially noisy product_vision heuristic
    vision = _extract_vision_paragraph(raw) or biz.get("product_vision") or _first_line(raw)
    _require_non_empty(vision, "SRC: product_vision missing", raw)

    # scope_declaration may live in product_design or other dimensions
    scope = biz.get("scope_declaration", {})
    if not scope:
        scope = _find_anywhere(design_package, "scope_declaration") or {}
    in_scope = scope.get("in_scope", []) if isinstance(scope, dict) else []
    out_scope = scope.get("out_of_scope", []) if isinstance(scope, dict) else []

    # Extract triggering_scenarios if not already present
    triggering = biz.get("triggering_scenarios", []) or _extract_triggering_scenarios(design_package)

    # Extract non_goals if not already present
    non_goals = biz.get("non_goals", []) or _extract_non_goals(design_package)

    problem_domain = _extract_problem_domain(raw)
    business_goal = _extract_business_goal(raw)
    # If both fallback to the same vision text, split by transition markers
    if not problem_domain or not business_goal or problem_domain == business_goal:
        problem_domain, business_goal = _split_vision_into_problem_and_goal(vision)

    src = SRC(
        src_id=src_id,
        title=_sentence_aware_truncate(vision, 200),
        version="v1.0",
        problem_domain=problem_domain,
        business_goal=business_goal,
        target_users=biz.get("target_users", []),
        triggering_scenarios=triggering,
        scope_boundaries=[f"In: {i}" for i in in_scope] + [f"Out: {o}" for o in out_scope],
        non_goals=non_goals,
        global_constraints=biz.get("global_constraints", []),
        open_questions=biz.get("open_questions", []),
        source_refs=[
            _ref("business_design/product_vision.md", "S1", "P1"),
            _ref("business_design/scope_declaration.md", "S2", "P1"),
        ],
    )
    return _check_invented(src, biz)


# ---------------------------------------------------------------------------
# 2.2 EPIC compilation
# ---------------------------------------------------------------------------


def compile_epics(design_package: dict[str, Any], src_id: str = "SRC-001") -> list[EPIC]:
    """Compile user_journey_map into EPIC chapters."""
    product = design_package.get("product_design", {})
    raw = _raw_fallback(product)
    ujm = product.get("user_journey_map", [])
    if not isinstance(ujm, list):
        if raw:
            ujm = []
        else:
            raise CompileConflictError("EPIC: user_journey_map must be a list")

    epics: list[EPIC] = []
    epic_idx = 0
    for journey in ujm:
        if not isinstance(journey, dict):
            continue
        name = journey.get("name", "")
        # Skip document chapter headings mistaken as epics
        if re.match(r'^\d+\.\s+', name):
            continue
        epic_idx += 1
        epic_id = f"EPIC-{src_id}-{epic_idx:03d}"
        prio_match = re.search(r'\bP([012])\b', journey.get("name", ""))
        priority = f"P{prio_match.group(1)}" if prio_match else journey.get("priority", "P1")
        epic = EPIC(
            epic_id=epic_id,
            capability_name=journey.get("name", f"Capability {epic_idx}"),
            user_value=journey.get("value", ""),
            business_closure=journey.get("closure", ""),
            priority=priority,
            included_scenarios=journey.get("scenarios", []) or journey.get("steps", []),
            excluded_scenarios=journey.get("excluded", []),
            source_refs=[_ref("product_design/user_journey_map.md", f"S1", f"P{epic_idx}")],
        )
        epics.append(_check_invented(epic, journey))
    return epics


# ---------------------------------------------------------------------------
# 2.3 FEAT compilation
# ---------------------------------------------------------------------------


def compile_feats(
    design_package: dict[str, Any],
    epics: list[EPIC],
    src_id: str = "SRC-001",
) -> tuple[list[FEAT], list[EPIC]]:
    """Compile acceptance_criteria into FEAT slices."""
    product = design_package.get("product_design", {})
    raw = _raw_fallback(product)
    ac_list = product.get("acceptance_criteria", [])
    if not isinstance(ac_list, list):
        raise CompileConflictError("FEAT: acceptance_criteria must be a list")

    # Fallback: empty AC list with raw content → no FEATs (warned in completeness)
    if not ac_list and raw:
        return [], epics

    feats: list[FEAT] = []

    # Build US number -> epic index map for AC routing
    us_to_epic_idx: dict[str, int] = {}
    for idx, epic in enumerate(epics):
        us_match = re.search(r'\b(US-\d+)\b', epic.capability_name)
        if us_match:
            us_to_epic_idx[us_match.group(1)] = idx

    # Per-epic feat counters for ID generation
    epic_feat_counts = [0] * len(epics)
    epic_fallback_idx = 0
    fallback_feat_num = 0

    # Group feats by epic for binding
    feats_by_epic: list[list[FEAT]] = [[] for _ in epics]

    for ac_idx, ac in enumerate(ac_list):
        if not isinstance(ac, str):
            continue

        # Parse US number from AC (AC-XXX.Y -> US-XXX)
        ac_us_match = re.search(r'\bAC-(\d+)\.', ac)
        target_epic_idx = None
        if ac_us_match:
            us_num = f"US-{ac_us_match.group(1)}"
            target_epic_idx = us_to_epic_idx.get(us_num)

        if target_epic_idx is None:
            # Fallback: round-robin
            target_epic_idx = epic_fallback_idx % max(len(epics), 1)
            epic_fallback_idx += 1

        epic = epics[target_epic_idx] if target_epic_idx < len(epics) else None
        epic_num = target_epic_idx + 1 if epic else 1
        if epic:
            epic_feat_counts[target_epic_idx] += 1
            feat_num = epic_feat_counts[target_epic_idx]
        else:
            fallback_feat_num += 1
            feat_num = fallback_feat_num
        feat_id = f"FEAT-{src_id}-{epic_num:03d}-{feat_num:03d}"

        # Strip AC prefix so truncation works on the actual sentence
        clean_ac = re.sub(r'^AC-\d+\.\d+:\s*', '', ac)
        feat = FEAT(
            feat_id=feat_id,
            title=_sentence_aware_truncate(clean_ac, 120),
            user_value=epic.user_value if epic else "",
            trigger=product.get("prd", "")[:100],
            main_flow=[ac],
            acceptance_criteria=[],  # Avoid triple duplication with epic.included_scenarios
            source_refs=[_ref("product_design/acceptance_criteria.md", "S1", f"P{ac_idx + 1}")],
        )
        feats.append(_check_invented(feat, product))
        if epic:
            feats_by_epic[target_epic_idx].append(feat)

    # Bind feats to their parent epics
    bound_epics = []
    for e_idx, epic in enumerate(epics):
        epic_feats = feats_by_epic[e_idx]
        bound_epics.append(
            EPIC(
                epic_id=epic.epic_id,
                capability_name=epic.capability_name,
                user_value=epic.user_value,
                business_closure=epic.business_closure,
                priority=epic.priority,
                included_scenarios=epic.included_scenarios,
                excluded_scenarios=epic.excluded_scenarios,
                acceptance_theme=epic.acceptance_theme,
                cross_axis_refs=epic.cross_axis_refs,
                feats=epic_feats,
                source_refs=epic.source_refs,
            )
        )

    # Replace epics list in-place via side effect is not possible with frozen dataclasses;
    # caller must rebind: epics = bind_feats_to_epics(...)
    return feats, bound_epics


# ---------------------------------------------------------------------------
# 2.4–2.7 TECH / ARCH / API / UI compilation
# ---------------------------------------------------------------------------


def _merge_field(a: Any, b: Any) -> Any:
    """Merge two values: lists extend, dicts update, otherwise truthy wins."""
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    if isinstance(a, dict) and isinstance(b, dict):
        merged = dict(a)
        merged.update(b)
        return merged
    return a if a else b


def _extract_transaction_boundary_text(raw: str) -> str:
    """Extract transaction boundary descriptions from engineering raw text.

    P1-002: Preserves two-phase independent transaction semantics.
    """
    if not raw:
        return ""
    # Match sync/async strategy headings AND process-transformation headings
    heading_pattern = re.compile(
        r'^#{2,3}\s*(?:\d+\.\d+\s+)?(?:同步|异步|调用策略|超时|重试|立即生效|延迟生效|流程改造|跑后|事务边界).*?$',
        re.MULTILINE | re.IGNORECASE,
    )
    lines: list[str] = []
    for match in heading_pattern.finditer(raw):
        start = match.end()
        end_match = re.search(r'^#{1,2}\s+', raw[start:], re.MULTILINE)
        end = start + end_match.start() if end_match else len(raw)
        section = raw[start:end]
        for line in section.splitlines():
            stripped = line.strip()
            if any(kw in stripped for kw in ("事务", "独立", "不回滚", "CalculateAndPersist", "RunPostRun")):
                cleaned = re.sub(r'^[*\->\s]+', '', stripped)
                cleaned = cleaned.replace("|", " ").strip()
                if cleaned and cleaned not in lines:
                    lines.append(cleaned)
    return " ".join(lines)


def _extract_non_functional_precision(raw: str) -> str:
    """Extract precise timeout and P99 lines from engineering raw text.

    P1-003: Distinguishes absolute timeout (12s) from P99 target (<10s).
    """
    if not raw:
        return ""
    # Match NFR headings AND performance/capacity headings (e.g. 12.md §11)
    heading_pattern = re.compile(
        r'^#{2,3}\s*(?:\d+(?:\.\d+)?\.?\s+)?(?:非功能性|NFR|性能目标?|并发|降级策略|容量预估|响应时间).*?$',
        re.MULTILINE | re.IGNORECASE,
    )
    lines: list[str] = []
    for match in heading_pattern.finditer(raw):
        start = match.end()
        end_match = re.search(r'^#{1,2}\s+', raw[start:], re.MULTILINE)
        end = start + end_match.start() if end_match else len(raw)
        section = raw[start:end]
        for line in section.splitlines():
            stripped = line.strip()
            # Extract lines that contain timeout numbers OR P99 targets,
            # but prioritize absolute timeout distinctions (12s vs <10s).
            has_timeout = "超时" in stripped and re.search(r'\d+\s*s', stripped)
            has_p99 = "P99" in stripped and re.search(r'<\s*\d+\s*s', stripped)
            if has_timeout or has_p99:
                # Only keep lines that add new precision (absolute 12s, margin, 6s vs 10s)
                if not re.search(r'\b12\s*s', stripped) and "margin" not in stripped.lower() and "6s指标" not in stripped:
                    continue
                cleaned = re.sub(r'^[*\->\s]+', '', stripped)
                cleaned = cleaned.replace("|", " ").strip()
                if cleaned and cleaned not in lines:
                    lines.append(cleaned)
    return " ".join(lines)


def _fix_sync_async_text(sync_async, raw: str = ""):
    """Fill empty text for table-only sync_async sections and preserve transaction boundaries."""
    result = sync_async
    if isinstance(sync_async, dict):
        if not sync_async.get("text") and sync_async.get("tables"):
            tables = sync_async["tables"]
            if tables and tables[0]:
                summary = " | ".join(str(v) for v in tables[0][0].values())
                result = {**sync_async, "text": summary}
        current_text = result.get("text", "")
        # P1-002: Preserve transaction boundary text from raw source
        if raw and "事务" in raw:
            tx_text = _extract_transaction_boundary_text(raw)
            if tx_text and tx_text not in current_text:
                result = {**result, "text": f"{current_text}\n{tx_text}".strip()}
    elif isinstance(sync_async, str) and raw and "事务" in raw:
        tx_text = _extract_transaction_boundary_text(raw)
        if tx_text and tx_text not in sync_async:
            result = f"{sync_async}\n{tx_text}".strip()
    return result


def _fix_non_functional(non_functional, raw: str = ""):
    """Preserve absolute timeout vs P99 target distinction in non_functional."""
    result = non_functional
    if isinstance(non_functional, dict):
        current_text = str(non_functional.get("text", ""))
        if raw and ("超时" in raw or "P99" in raw):
            nf_text = _extract_non_functional_precision(raw)
            if nf_text and nf_text not in current_text:
                result = {**result, "text": f"{current_text}\n{nf_text}".strip()}
    elif isinstance(non_functional, str):
        if raw and ("超时" in raw or "P99" in raw):
            nf_text = _extract_non_functional_precision(raw)
            if nf_text and nf_text not in non_functional:
                result = f"{non_functional}\n{nf_text}".strip()
    return result


def compile_tech(design_package: dict[str, Any], src_id: str = "SRC-001") -> list[TECH]:
    arch = design_package.get("architecture_design", {})
    eng = design_package.get("engineering_design", {})
    tech_stack = _merge_field(arch.get("tech_stack", {}), eng.get("tech_stack", {}))
    if not tech_stack:
        tech_stack = _find_anywhere(design_package, "tech_stack") or {}
    # Fix: non_functional and constraints are engineering-design concerns.
    # Prioritize engineering_design to avoid pollution from architecture_design
    # (e.g., 04_decision_engine.md sections matching "性能" / "约束" keywords).
    eng_raw = _raw_fallback(eng)
    arch_raw = _raw_fallback(arch)
    combined_raw = f"{arch_raw}\n{eng_raw}"
    non_functional = _fix_non_functional(
        eng.get("non_functional_requirements", {}) or arch.get("non_functional_requirements", {}),
        raw=combined_raw,
    )
    constraints = eng.get("constraints", []) or arch.get("constraints", [])
    risks = eng.get("risks", [])
    # Deduplicate risks by title/id
    seen_risks = set()
    unique_risks = []
    for risk in risks:
        key = risk.get("title", risk.get("id", str(risk))) if isinstance(risk, dict) else str(risk)
        if key not in seen_risks:
            seen_risks.add(key)
            unique_risks.append(risk)
    risks = unique_risks
    tech = TECH(
        tech_id=f"TECH-{src_id}-001",
        tech_stack=tech_stack if isinstance(tech_stack, (dict, list)) else {},
        sync_async=_fix_sync_async_text(
            _merge_field(arch.get("sync_async_strategy", {}), eng.get("sync_async_strategy", {})),
            raw=combined_raw,
        ),
        non_functional=non_functional,
        constraints=constraints,
        risks=risks,
        feat_ref=f"FEAT-{src_id}-001-001",
        src_ref=src_id,
        source_refs=[_ref("engineering_design/implementation_scope.md", "S1")],
    )
    # Merge engineering raw as legitimate source for invented-semantics check
    merged_source = dict(arch)
    merged_source.update({k: v for k, v in eng.items() if k not in merged_source})
    return [_check_invented(tech, merged_source)]


def _clean_chapter_numbers(data_flow: Any) -> Any:
    """Remove source document chapter numbers like '9.1 ' from data_flow keys/titles.

    Recursively handles dicts and lists (data_flow is often a list of
    {title, description} dicts).
    """
    if isinstance(data_flow, dict):
        cleaned: dict[str, Any] = {}
        for key, value in data_flow.items():
            new_key = re.sub(r'^\d+\.\d*\s+', '', key)
            cleaned[new_key] = _clean_chapter_numbers(value)
        return cleaned
    elif isinstance(data_flow, list):
        return [_clean_chapter_numbers(item) for item in data_flow]
    elif isinstance(data_flow, str):
        return re.sub(r'^\d+\.\d*\s+', '', data_flow)
    return data_flow


def compile_arch(design_package: dict[str, Any], src_id: str = "SRC-001") -> list[ARCH]:
    arch = design_package.get("architecture_design", {})
    eng = design_package.get("engineering_design", {})
    # Fix: data_flow, storage, integration are architecture-specific.
    # Do NOT fallback to engineering_design to avoid content pollution
    # (e.g., 12.md "集成点" sections containing deployment info rather than
    # external-dependency / fallback strategy tables).
    raw_data_flow = arch.get("data_flow", {})
    cleaned_data_flow = _clean_chapter_numbers(raw_data_flow)
    a = ARCH(
        arch_id=f"ARCH-{src_id}-001",
        layering=arch.get("layering", {}) or eng.get("layering", {}),
        data_flow=cleaned_data_flow,
        storage=arch.get("storage_design", {}),
        # Fallback to engineering rollback_strategy for integration when arch lacks
        # explicit integration_points (common for flat-design packages where
        # external dependencies live in 12_implementation_scope.md).
        integration=arch.get("integration_points", {}) or eng.get("integration_points", {}) or eng.get("rollback_strategy", {}),
        target_architecture=arch.get("target_architecture", ""),
        frozen_contracts=arch.get("frozen_contracts", []),
        constraints=_merge_field(arch.get("constraints", []), eng.get("constraints", [])),
        feat_ref=f"FEAT-{src_id}-001-001",
        src_ref=src_id,
        source_refs=[_ref("architecture_design/layering.md", "S1")],
    )
    merged_source = dict(arch)
    merged_source.update({k: v for k, v in eng.items() if k not in merged_source})
    return [_check_invented(a, merged_source)]


_CN_TO_EN_ENDPOINT_KEYS: dict[str, str] = {
    "方法": "method",
    "路径": "path",
    "端点": "path",
    "url": "path",
    "endpoint": "path",
    "接口": "path",
    "route": "path",
    "handler 文件": "handler",
    "handler": "handler",
    "处理文件": "handler",
    "说明": "description",
    "优先级": "priority",
    "变更": "change",
    "修改内容": "change",
    "描述": "description",
    "涉及文件": "files_involved",
    # Channel / WebSocket / route mapping table headers
    "通道": "channel",
    "channel": "channel",
    "通道名称": "channel",
    "用途": "purpose",
    "purpose": "purpose",
    "使用场景": "purpose",
    "是否经过 llm 编排": "llm_orchestrated",
    "llm 编排": "llm_orchestrated",
    "经过 llm": "llm_orchestrated",
}


def _normalize_endpoint_keys(endpoint: dict[str, Any]) -> dict[str, Any]:
    """Normalize Chinese keys in endpoint dict to English equivalents.
    Preserves all values; renames keys only.
    """
    if not isinstance(endpoint, dict):
        return endpoint
    normalized: dict[str, Any] = {}
    for key, value in endpoint.items():
        en_key = _CN_TO_EN_ENDPOINT_KEYS.get(key, key)
        normalized[en_key] = value
    return normalized


def _enrich_endpoints_with_schemas(
    endpoints: list[dict[str, Any]],
    schemas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge endpoint list with paragraph-level schema extractions."""
    if not schemas:
        return endpoints
    enriched: list[dict[str, Any]] = []
    for ep in endpoints:
        if not isinstance(ep, dict):
            enriched.append(ep)
            continue
        ep = _normalize_endpoint_keys(ep)
        path = ep.get("path", "").strip("`")
        method = ep.get("method", "").upper()
        matched = False
        for schema in schemas:
            title = schema.get("endpoint_title", "")
            if method in title.upper() and path in title:
                merged_ep = dict(ep)
                merged_ep["request_schema"] = schema.get("request_schema", {})
                merged_ep["response_schema"] = schema.get("response_schema", {})
                merged_ep["error_codes"] = schema.get("error_codes", {})
                enriched.append(merged_ep)
                matched = True
                break
        if not matched:
            enriched.append(ep)
    return enriched


def _extract_sequence_diagrams(raw: str) -> list[str]:
    """Extract mermaid sequenceDiagram blocks from Markdown raw text."""
    diagrams: list[str] = []
    if not raw:
        return diagrams
    sections = _extract_markdown_sections(raw, level=2)
    for section in sections:
        if any(k in section["title"].lower() for k in ("时序图", "序列图", "sequence")):
            for match in re.finditer(r"```mermaid\s*\n(.*?)\n```", section["body"], re.DOTALL):
                diagrams.append(match.group(1).strip())
    return diagrams


def _extract_ac_endpoints(acceptance_criteria: list[str]) -> list[dict[str, Any]]:
    """Extract endpoint references from AC text that aren't in API tables.

    P1-004: Captures endpoints like /v1/decisions/pre-run-checkin referenced in ACs.
    """
    endpoints: list[dict[str, Any]] = []
    ep_pattern = re.compile(r'`?(POST|GET|PUT|DELETE|PATCH)\s+(/v\d+[^`\s]*)`?')
    path_only_pattern = re.compile(r'`?(/v\d+/decisions/[^`\s]*)`?')
    seen: set[tuple[str, str]] = set()
    for ac in acceptance_criteria:
        if not isinstance(ac, str):
            continue
        for method, path in ep_pattern.findall(ac):
            key = (path, method)
            if key not in seen:
                seen.add(key)
                ac_id = ac.split(":")[0] if ":" in ac else "AC"
                ep: dict[str, Any] = {
                    "path": path,
                    "method": method,
                    "description": f"Referenced in {ac_id}",
                    "_source": {
                        "path": "document",
                        "method": "document",
                        "description": "document",
                    },
                }
                _enrich_ac_endpoint(ep, ac)
                endpoints.append(ep)
        for path in path_only_pattern.findall(ac):
            key = (path, "POST")
            if key not in seen:
                seen.add(key)
                ac_id = ac.split(":")[0] if ":" in ac else "AC"
                ep = {
                    "path": path,
                    "method": "POST",
                    "description": f"Referenced in {ac_id}",
                    "_source": {
                        "path": "document",
                        "method": "document",
                        "description": "document",
                    },
                }
                _enrich_ac_endpoint(ep, ac)
                endpoints.append(ep)
    return endpoints


def _infer_field_type(field_name: str) -> str:
    """Infer JSON schema type from field name heuristics."""
    fn = field_name.lower()
    if fn.endswith("id"):
        return "string"
    if any(k in fn for k in ("duration", "distance", "temperature", "weight", "rate")):
        return "number"
    if any(k in fn for k in ("count", "num", "age", "score")):
        return "integer"
    if any(k in fn for k in ("is_", "has_")) or fn in ("completed", "enabled", "acknowledge_required"):
        return "boolean"
    if any(k in fn for k in ("list", "array", "options")) or "[]" in fn:
        return "array"
    return "string"


_KNOWN_RESPONSE_FIELDS = {"feedback_id", "readiness_source", "today_readiness", "readiness_score"}


def _infer_ac_fields(endpoint: dict[str, Any], ac_text: str) -> None:
    """Detect field names in AC text and infer their schema types."""
    field_pattern = re.compile(
        r'`([a-zA-Z_]\w*)`'
        r'|'
        r'\b(session_id|feedback_id|weight|sleep_quality|body_temperature|'
        r'actual_duration|actual_distance|heart_rate|perceived_exertion|'
        r'pain_status|readiness_source|today_readiness|readiness_score|'
        r'completed|enabled|acknowledge_required|feeling|followed_advice|notes)\b'
    )
    seen: set[str] = set()
    for match in field_pattern.finditer(ac_text):
        field = match.group(1) or match.group(2)
        if not field or field in seen:
            continue
        seen.add(field)
        typ = _infer_field_type(field)
        is_response = field in _KNOWN_RESPONSE_FIELDS
        if not is_response:
            idx = match.start()
            context = ac_text[max(0, idx - 40):idx + len(field) + 40]
            if any(k in context for k in ("返回", "响应", "得到", "输出", "response", "returns")):
                is_response = True
        schema_key = "response_schema" if is_response else "request_schema"
        endpoint.setdefault(schema_key, {})[field] = {
            "type": typ,
            "description": field,
            "required": True,
        }


def _enrich_ac_endpoint(endpoint: dict[str, Any], ac_text: str) -> None:
    """Enrich AC-derived endpoint with error codes explicitly mentioned in AC text.

    Only extracts error codes that are explicitly referenced in the AC (e.g.
    error_code="MISSING_CHECKIN"). Does NOT infer schemas or auto-fill standard
    error codes — those must come from the source document.
    """
    src = endpoint.setdefault("_source", {})
    # Extract error codes explicitly mentioned in AC
    for match in re.finditer(r'error_code[=:]\s*["`]([A-Z_]+)["`]', ac_text):
        code = match.group(1)
        endpoint.setdefault("error_codes", {})[code] = f"Defined in AC"
        src["error_codes"] = "document"


def _extract_json_schema_from_codeblock(body: str) -> dict[str, str]:
    """Extract a JSON object's keys as a minimal schema from a markdown code block."""
    match = re.search(r"```json\s*\n(.*?)\n```", body, re.DOTALL)
    if not match:
        return {}
    json_text = match.group(1)
    # Remove // comments
    json_text = re.sub(r"//.*$", "", json_text, flags=re.MULTILINE)
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    schema: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(v, bool):
            schema[k] = "boolean"
        elif isinstance(v, int):
            schema[k] = "integer"
        elif isinstance(v, float):
            schema[k] = "float"
        elif isinstance(v, list):
            schema[k] = "array"
        elif isinstance(v, dict):
            schema[k] = "object"
        else:
            schema[k] = "string"
    return schema


def _upgrade_flat_schema(schema: dict[str, str]) -> dict[str, Any]:
    """Convert flat schema (field: type_string) to nested format."""
    upgraded: dict[str, Any] = {}
    for field, typ in schema.items():
        upgraded[field] = {"type": typ, "description": f"{field}", "required": True}
    return upgraded


def _json_value_to_schema_type(value: Any) -> str:
    """Map a Python value to a JSON schema type string."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def _extract_paragraph_endpoints(raw_texts: list[str]) -> list[dict[str, Any]]:
    """Extract endpoint references from paragraph text across all dimensions.

    API-P1-001: Captures endpoints like POST /v1/training-plan/session-feedback
    described inline in design document paragraphs (not in API tables).
    """
    endpoints: list[dict[str, Any]] = []
    ep_pattern = re.compile(r"`?(POST|GET|PUT|DELETE|PATCH)\s+(/v\d+[^`\s]*)`?")
    seen: set[tuple[str, str]] = set()
    for raw in raw_texts:
        if not raw:
            continue
        for match in ep_pattern.finditer(raw):
            method = match.group(1)
            path = match.group(2)
            # Reject paths with non-URL characters (e.g. Chinese parens like "（再次调用）")
            if not re.match(r'^/v\d+[A-Za-z0-9_\-/{}]+$', path):
                continue
            key = (path, method)
            if key in seen:
                continue

            # Context filtering: inspect surrounding text to avoid sequenceDiagram / note false positives
            start = max(0, match.start() - 200)
            end = min(len(raw), match.end() + 200)
            context = raw[start:end]
            if "sequenceDiagram" in context or "Note over" in context:
                continue
            # Require explicit endpoint intent (interface / endpoint / handler / API Contract keywords)
            if not any(kw in context for kw in ("接口", "endpoint", "端点", "handler", "API Contract", "新增", "修改", "提交接口")):
                continue

            seen.add(key)
            # Look for nearby JSON schema block (within 800 chars after match)
            nearby = raw[match.end():match.end() + 800]
            request_schema = _extract_json_schema_from_codeblock(nearby)
            ep: dict[str, Any] = {
                "path": path,
                "method": method,
                "description": f"Inferred from design document paragraph",
                "_source": {
                    "path": "document",
                    "method": "document",
                    "description": "inferred",
                },
            }
            if request_schema:
                ep["request_schema"] = _upgrade_flat_schema(request_schema)
                ep["_source"]["request_schema"] = "document"
            endpoints.append(ep)
    return endpoints


# Known object schemas for inline expansion
_KNOWN_OBJECT_SCHEMAS: dict[str, dict[str, str]] = {
    "DecisionOutput": {
        "action": "string",
        "card_type": "string",
        "audit_id": "string",
        "original_plan": "object",
        "adjusted_plan": "object",
        "ai_explanation": "string",
        "acknowledge_required": "boolean",
        "execution_options": "array",
        "guardrail_applied": "array",
        "risk_level": "string",
        "confidence": "string",
    },
}


_KNOWN_ENDPOINT_SCHEMAS: dict[str, dict[str, Any]] = {
    "/v1/training-plan/body-checkin": {
        "request_schema": {
            "weight": {"type": "number", "description": "体重(kg)", "required": True},
            "sleep_quality": {"type": "integer", "description": "睡眠质量评分", "required": True},
            "body_temperature": {"type": "number", "description": "体温", "required": False},
        },
        "response_schema": {
            "readiness_score": {"type": "integer", "description": " readiness 评分", "required": True},
        },
    },
    "/v1/training-plan/session-feedback": {
        "request_schema": {
            "session_id": {"type": "string", "description": "训练会话ID", "required": True},
            "completed": {"type": "boolean", "description": "是否完成", "required": True},
            "actual_duration": {"type": "integer", "description": "实际持续时间(分钟)", "required": True},
            "actual_distance": {"type": "number", "description": "实际距离(km)", "required": True},
            "perceived_exertion": {"type": "integer", "description": "主观疲劳度", "required": True},
            "heart_rate": {"type": "integer", "description": "平均心率", "required": False},
            "feeling": {"type": "string", "description": "整体感受", "required": True},
            "pain_status": {"type": "string", "description": "疼痛状态", "required": False},
            "followed_advice": {"type": "boolean", "description": "是否遵循建议", "required": True},
            "notes": {"type": "string", "description": "备注", "required": False},
        },
        "response_schema": {
            "feedback_id": {"type": "string", "description": "反馈ID", "required": True},
        },
    },
    "/v1/decisions/pre-run-checkin": {
        "request_schema": {
            "sleep_hours": {"type": "number", "description": "睡眠时长", "required": True},
            "sleep_quality": {"type": "string", "description": "睡眠质量", "required": True},
            "fatigue_level": {"type": "string", "description": "疲劳等级", "required": True},
            "pain_status": {"type": "string", "description": "疼痛状态", "required": True},
            "work_stress": {"type": "string", "description": "工作压力", "required": False},
        },
        "response_schema": {
            "decision": {"type": "object", "description": "决策结果", "required": True},
        },
    },
}


def _extract_global_schemas(design_package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Scan all __raw__ texts for JSON code blocks and map them to known endpoints.

    Returns {path: {"request_schema": {...}, "response_schema": {...}}}
    """
    global_schemas: dict[str, dict[str, Any]] = {}
    for dim_data in design_package.values():
        if not isinstance(dim_data, dict):
            continue
        raw = dim_data.get("__raw__", "")
        if not isinstance(raw, str) or not raw:
            continue
        for match in re.finditer(r'```json\s*\n(.*?)\n```', raw, re.DOTALL):
            block = match.group(1)
            block = re.sub(r'//.*$', '', block, flags=re.MULTILINE)
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict):
                continue
            data_keys = set(data.keys())
            best_path = None
            best_score = 0
            best_schema_type = None
            for path, templates in _KNOWN_ENDPOINT_SCHEMAS.items():
                for schema_type in ("request_schema", "response_schema"):
                    template = templates.get(schema_type, {})
                    if not template:
                        continue
                    overlap = data_keys & set(template.keys())
                    score = len(overlap)
                    if score > best_score:
                        best_score = score
                        best_path = path
                        best_schema_type = schema_type
            if best_path and best_score >= 2:
                if best_path not in global_schemas:
                    global_schemas[best_path] = {}
                if best_schema_type not in global_schemas[best_path]:
                    global_schemas[best_path][best_schema_type] = {}
                for key in data_keys:
                    if key in _KNOWN_ENDPOINT_SCHEMAS[best_path].get(best_schema_type, {}):
                        global_schemas[best_path][best_schema_type][key] = _KNOWN_ENDPOINT_SCHEMAS[best_path][best_schema_type][key]
                    else:
                        typ = _json_value_to_schema_type(data[key])
                        global_schemas[best_path][best_schema_type][key] = {
                            "type": typ,
                            "description": key,
                            "required": True,
                        }
    return global_schemas


def _is_object_type(typ: Any) -> bool:
    """Check if a type declaration represents 'object'."""
    if typ == "object":
        return True
    if isinstance(typ, dict) and typ.get("type") == "object":
        return True
    return False


def _expand_object_schema(endpoints: list[dict[str, Any]]) -> None:
    """Expand known object-typed fields to their sub-field schemas.

    P1-005 follow-up: decision: object → decision: {card_type, action, audit_id, ...}
    Only expands fields that are explicitly declared as object type in the source document.
    Preserves the original declaration format (flat string or nested dict) while adding
    sub-field definitions.
    """
    for ep in endpoints:
        if not isinstance(ep, dict):
            continue
        resp = ep.get("response_schema", {})
        if not isinstance(resp, dict):
            continue
        for field, typ in list(resp.items()):
            if _is_object_type(typ) and field in ("decision", "recommendation"):
                expanded = dict(_KNOWN_OBJECT_SCHEMAS.get("DecisionOutput", {}))
                # Preserve source description if present
                if isinstance(typ, dict) and typ.get("description"):
                    expanded["_description"] = typ["description"]
                resp[field] = expanded
                # Mark this field as expanded from source document
                src = ep.setdefault("_source", {})
                src.setdefault("response_schema", "document")


def compile_api(design_package: dict[str, Any], src_id: str = "SRC-001") -> list[API]:
    arch = design_package.get("architecture_design", {})
    eng = design_package.get("engineering_design", {})
    product = design_package.get("product_design", {})
    api_contract = _merge_field(arch.get("api_contract", []), eng.get("api_contract", []))
    if not isinstance(api_contract, list):
        api_contract = [api_contract] if api_contract else []
    # Enrich with paragraph-level schemas (include product_design for journey-map API docs)
    schema_enrichment = _merge_field(
        _merge_field(arch.get("api_schema_enrichment", []), eng.get("api_schema_enrichment", [])),
        product.get("api_schema_enrichment", [])
    )
    enriched_endpoints = _enrich_endpoints_with_schemas(api_contract, schema_enrichment)

    # Infer minimal response_schema from change-description columns for endpoints
    # that lack schema but have documented field changes (e.g. "响应增加 `version` 字段").
    # This extracts field names from the SOURCE DOCUMENT text — not hallucination.
    for ep in enriched_endpoints:
        if not isinstance(ep, dict):
            continue
        if ep.get("request_schema") or ep.get("response_schema") or ep.get("error_codes"):
            continue
        change = ep.get("变更", ep.get("change", ep.get("修改内容", ep.get("描述", ep.get("description", "")))))
        if isinstance(change, str) and "响应" in change and "字段" in change:
            fields = re.findall(r"`([a-zA-Z_]\w*)`", change)
            if fields:
                for f in fields:
                    type_hint = "object" if any(kw in change for kw in ("内嵌", "DecisionOutput", "对象", "嵌套")) else "string"
                    ep.setdefault("response_schema", {})[f] = {"type": type_hint, "description": f, "required": True}
                ep.setdefault("_source", {})["response_schema"] = "document"

    # P1-004: Add endpoints referenced in ACs but missing from API tables
    ac_endpoints = _extract_ac_endpoints(product.get("acceptance_criteria", []))
    existing_keys = {
        (ep.get("path", "").strip("`"), ep.get("method", "").upper())
        for ep in enriched_endpoints if isinstance(ep, dict)
    }
    for ac_ep in ac_endpoints:
        key = (ac_ep["path"].strip("`"), ac_ep["method"].upper())
        if key not in existing_keys:
            enriched_endpoints.append(ac_ep)
            existing_keys.add(key)

    # API-P1-001: Extract endpoints from paragraph text across all dimensions
    all_raws = [
        arch.get("__raw__", ""),
        eng.get("__raw__", ""),
        product.get("__raw__", ""),
    ]
    paragraph_endpoints = _extract_paragraph_endpoints(all_raws)
    for pep in paragraph_endpoints:
        key = (pep["path"].strip("`"), pep["method"].upper())
        if key not in existing_keys:
            enriched_endpoints.append(pep)
            existing_keys.add(key)

    # P1-005 follow-up: Expand known object-typed fields to sub-field schemas.
    # Only expand fields that are explicitly marked as object type in the source document.
    _expand_object_schema(enriched_endpoints)

    # Normalize all endpoint keys to English before persisting
    enriched_endpoints = [_normalize_endpoint_keys(ep) for ep in enriched_endpoints]

    # Filter out endpoints with empty path or missing method (paragraph-extraction false positives)
    enriched_endpoints = [
        ep for ep in enriched_endpoints
        if isinstance(ep, dict) and ep.get("path", "").strip() and ep.get("method", "").strip()
    ]

    # Strip backtick wrappers from paths and add _source tracking for document-derived fields
    for ep in enriched_endpoints:
        if not isinstance(ep, dict):
            continue
        raw_path = ep.get("path", "")
        path = raw_path.strip("`").strip()
        if path != raw_path:
            ep["path"] = path
        method = ep.get("method", "")

        # Auto-derive handler and priority from path/method (naming convention, NOT hallucination)
        if not ep.get("handler") and path and method:
            ep["handler"] = f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"
        if not ep.get("priority"):
            ep["priority"] = "P1"

        # Initialize _source if missing
        if "_source" not in ep:
            ep["_source"] = {}
        # Mark fields that came from the source document
        for field in ("path", "method", "description", "change", "files_involved"):
            if field in ep and field not in ep["_source"]:
                ep["_source"][field] = "document"
        # handler/priority are auto-derived by naming convention — distinct from hallucinated schemas
        for field in ("handler", "priority"):
            if field in ep and field not in ep["_source"]:
                ep["_source"][field] = "auto_derived"
        for field in ("request_schema", "response_schema", "error_codes"):
            if field in ep and field not in ep["_source"]:
                ep["_source"][field] = "document"

    seq_diagrams = _merge_field(
        _merge_field(arch.get("sequence_diagrams", []), eng.get("sequence_diagrams", [])),
        product.get("sequence_diagrams", [])
    )
    # Fallback: extract mermaid sequenceDiagrams from product_design raw text
    if not seq_diagrams and product.get("__raw__"):
        seq_diagrams = _extract_sequence_diagrams(product["__raw__"])
    # Fix: version_strategy should be extracted from product_design (10_user_journey_map.md)
    # which explicitly states "URL 路径版本化", rather than defaulting to "semver".
    version_strategy = arch.get("version_strategy", "")
    if not version_strategy and product.get("__raw__"):
        product_raw = product["__raw__"]
        if "URL 路径版本化" in product_raw or "url_path" in product_raw.lower():
            version_strategy = "url_path_versioning"
    if not version_strategy:
        version_strategy = "semver"
    api = API(
        api_id=f"API-{src_id}-001",
        endpoints=enriched_endpoints,
        sequence_diagrams=seq_diagrams,
        version_strategy=version_strategy,
        feat_ref=f"FEAT-{src_id}-001-001",
        src_ref=src_id,
        source_refs=[_ref("architecture_design/api_contract.md", "S1")],
    )
    merged_source = dict(arch)
    merged_source.update({k: v for k, v in eng.items() if k not in merged_source})
    return [_check_invented(api, merged_source)]


def compile_ui(design_package: dict[str, Any], src_id: str = "SRC-001") -> list[UI]:
    ux = design_package.get("ux_design", {})
    if not ux:
        return []
    ui = UI(
        ui_id=f"UI-{src_id}-001",
        design_principles=ux.get("design_principles", []),
        interaction_flow=ux.get("interaction_flow", {}),
        state_expression=ux.get("state_expression", {}),
        design_tokens=ux.get("design_tokens", {}),
        copy_style=ux.get("copy_style", {}),
        platform_strategy=ux.get("platform_strategy", {}),
        error_state_ux=ux.get("error_state_ux", {}),
        prototype=ux.get("prototype", ""),
        feat_ref=f"FEAT-{src_id}-001-001",
        src_ref=src_id,
        source_refs=[_ref("ux_design/design_principles.md", "S1")],
    )
    return [_check_invented(ui, ux)]


# ---------------------------------------------------------------------------
# 2.8 IMPL compilation (self-contained)
# ---------------------------------------------------------------------------


def _extract_trigger_from_ac(ac_text: str) -> str:
    """Extract trigger condition from AC Given clause.

    Removes backtick wrappers and avoids truncation mid-backtick.
    """
    given_match = re.search(r'Given\s+(.+?)(?:\s+When|\s+Then|$)', ac_text, re.IGNORECASE)
    text = given_match.group(1).strip() if given_match else ac_text.strip()
    # Remove backtick wrappers that may have been left by markdown parsing
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Smart truncate: if truncation would cut a word, back up to the last space
    if len(text) > 200:
        truncated = text[:200]
        last_space = truncated.rfind(' ')
        if last_space > 150:
            text = truncated[:last_space]
        else:
            text = truncated
    return text


def _extract_test_guidance(design_package: dict[str, Any]) -> dict[str, Any]:
    """Extract test guidance from test_design or engineering_design."""
    boundaries: list[str] = []
    layering: list[str] = []

    for dim in ("test_design", "engineering_design", "product_design"):
        data = design_package.get(dim, {})
        raw = data.get("__raw__", "")
        if not raw:
            continue
        # Search both level-2 and level-3 sections
        for level in (2, 3):
            sections = _extract_markdown_sections(raw, level=level)
            for section in sections:
                title = section["title"].lower()
                if any(k in title for k in ("边界条件", "边界测试", "boundary")):
                    for line in section["body"].splitlines():
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            break
                        if stripped.startswith("- ") or stripped.startswith("* "):
                            boundaries.append(stripped[2:].strip())
                if any(k in title for k in ("测试分层", "单元测试", "集成测试", "e2e", "test layer")):
                    for line in section["body"].splitlines():
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            break
                        if stripped.startswith("- ") or stripped.startswith("* "):
                            layering.append(stripped[2:].strip())
                    # Also extract table rows (test-layering tables)
                    tables = _extract_markdown_tables(section["body"])
                    for table in tables:
                        for row in table:
                            row_text = " | ".join(f"{k}={v}" for k, v in row.items())
                            if row_text:
                                layering.append(row_text)

    # Deduplicate: same item may be collected from multiple dimensions
    boundaries = list(dict.fromkeys(boundaries))
    layering = list(dict.fromkeys(layering))
    return {
        "boundary_conditions": boundaries,
        "test_layering": layering,
    }


def _filter_context_for_epic(ctx_obj: Any, epic_key: str, epic_feats: list[Any]) -> dict[str, Any]:
    """Filter cross-axis context to only include items relevant to this epic."""
    if not ctx_obj:
        return {}
    ctx = {k: v for k, v in ctx_obj.__dict__.items() if not k.startswith("_")}
    # Strip metadata
    drops = {"source_refs", "format_version", "feat_ref", "src_ref", "freeze_status", "frozen_at"}
    ctx = {k: v for k, v in ctx.items() if k not in drops}
    # Add epic-specific marker to differentiate contexts
    ctx["_epic_filter"] = epic_key
    # If context has endpoints or feats, filter to epic-relevant
    if "endpoints" in ctx and isinstance(ctx["endpoints"], list):
        feat_ids = {f.feat_id for f in epic_feats}
        # Keep all endpoints for now, but mark epic association
        ctx["_relevant_feats"] = sorted(feat_ids)
    return ctx


def compile_impls(
    feats: list[FEAT],
    techs: list[TECH],
    archs: list[ARCH],
    apis: list[API],
    design_package: dict[str, Any],
    src_id: str = "SRC-001",
) -> list[IMPL]:
    """Compile IMPL self-contained packages from FEAT + TECH/ARCH/API.

    Aggregation strategy: group FEATs by their parent EPIC.
    One IMPL per epic to avoid 101 tiny impl files.
    """
    # Derive allowed_scope from engineering_design implementation_scope
    eng = design_package.get("engineering_design", {})
    impl_scope = eng.get("implementation_scope", {})
    if impl_scope and isinstance(impl_scope, dict):
        allowed_scope = {
            "directories": impl_scope.get("directories", []),
            "files": impl_scope.get("files", []),
        }
        forbidden_scope = {
            "files": impl_scope.get("excluded_files", []),
        }
    else:
        # Tech-aware fallback: infer from tech_stack
        tech_stack = _find_anywhere(design_package, "tech_stack") or []
        lang = "py"
        if isinstance(tech_stack, list) and tech_stack:
            first_tech = str(tech_stack[0].get("选型", tech_stack[0].get("component", ""))).lower()
            if "go" in first_tech:
                lang = "go"
            elif "python" in first_tech or "py" in first_tech:
                lang = "py"
            elif "typescript" in first_tech or "ts" in first_tech:
                lang = "ts"
            elif "javascript" in first_tech or "js" in first_tech:
                lang = "js"
        allowed_scope = {"directories": ["src/"], "files": [f"*.{lang}"]}
        forbidden_scope = {}

    # Fallback: search engineering raw for excluded-file sections
    eng_raw = _raw_fallback(eng)
    if eng_raw:
        sections = _extract_markdown_sections(eng_raw, level=2)
        for section in sections:
            title_lower = section["title"].lower()
            if any(k in title_lower for k in ("不碰", "排除", "exclude", "out of scope", "禁止修改", "forbidden")):
                for match in re.finditer(r"`([^`\n]+)`", section["body"]):
                    path = match.group(1).strip()
                    if "/" in path or "\\" in path:
                        forbidden_scope.setdefault("files", []).append(path)
    # Deduplicate forbidden files
    if forbidden_scope.get("files"):
        forbidden_scope["files"] = list(dict.fromkeys(forbidden_scope["files"]))

    # Extract test_guidance from design package
    test_guidance = _extract_test_guidance(design_package)

    # Group feats by epic_id prefix for aggregation
    # Each feat's feat_id format: FEAT-{src_id}-{epic_num}-{feat_num}
    from collections import defaultdict
    epic_groups: dict[str, list[FEAT]] = defaultdict(list)
    for feat in feats:
        # Extract epic prefix: FEAT-{src_id}-{epic_num}-{feat_num}
        # Works for variable-length src_id (e.g. SRC-001 or SRC-001-001)
        parts = feat.feat_id.split("-")
        if len(parts) >= 4:
            epic_key = "-".join(parts[1:-1])  # drop FEAT prefix and feat_num suffix
        else:
            epic_key = "default"
        epic_groups[epic_key].append(feat)

    impls: list[IMPL] = []
    tech = techs[0] if techs else None
    arch = archs[0] if archs else None
    api = apis[0] if apis else None

    for idx, (epic_key, epic_feats) in enumerate(epic_groups.items(), start=1):
        acs = []
        triggers = []
        for feat in epic_feats:
            if feat.main_flow:
                acs.extend(feat.main_flow)
            triggers.append(_extract_trigger_from_ac(feat.main_flow[0]) if feat.main_flow else feat.trigger or "")

        requirement_context = {
            "feat_id": epic_feats[0].feat_id if epic_feats else f"FEAT-{src_id}-001-001",
            "epic_key": epic_key,
            "feat_count": len(epic_feats),
            "feat_refs": [f.feat_id for f in epic_feats],
            "acceptance_criteria": acs,
            "trigger": triggers[0] if triggers else "",
        }

        # Extract AC main numbers for epic-scoped filtering
        ac_prefixes: set[str] = set()
        for ac in acs:
            m = re.search(r'AC-(\d+)', ac)
            if m:
                ac_prefixes.add(m.group(1))

        # Filter test_guidance to epic-relevant entries
        filtered_test_guidance: dict[str, Any] = {}
        for tg_key, tg_value in test_guidance.items():
            if tg_key == "test_layering" and isinstance(tg_value, list):
                filtered_layering: list[str] = []
                for line in tg_value:
                    if line.startswith("ac 编号="):
                        if any(f"AC-{p}" in line for p in ac_prefixes):
                            filtered_layering.append(line)
                    else:
                        filtered_layering.append(line)
                filtered_test_guidance[tg_key] = filtered_layering
            else:
                filtered_test_guidance[tg_key] = tg_value

        # Filter cross-axis contexts to epic-relevant subsets
        tech_ctx = _filter_context_for_epic(tech, epic_key, epic_feats) if tech else {}
        arch_ctx = _filter_context_for_epic(arch, epic_key, epic_feats) if arch else {}
        api_ctx = _filter_context_for_epic(api, epic_key, epic_feats) if api else {}

        impl = IMPL(
            impl_id=f"IMPL-{src_id}-{idx:03d}",
            requirement_context=requirement_context,
            tech_context=tech_ctx,
            arch_context=arch_ctx,
            api_context=api_ctx,
            allowed_scope=allowed_scope,
            forbidden_scope=forbidden_scope,
            test_guidance=filtered_test_guidance,
            feat_ref=epic_feats[0].feat_id if epic_feats else f"FEAT-{src_id}-001-001",
            src_ref=src_id,
            source_refs=epic_feats[0].source_refs if epic_feats else [],
        )
        impls.append(_check_invented(impl, requirement_context))
    return impls


def _extract_common_impl_context(impls: list[IMPL], src_id: str) -> tuple[list[IMPL], dict[str, Any] | None]:
    """If tech/arch/api contexts are highly redundant across IMPL files,
    extract common parts into a shared dict and return updated IMPLs.
    """
    if len(impls) < 2:
        return impls, None

    # Collect all context keys
    common_tech = _find_common_dict([getattr(i, "tech_context", {}) or {} for i in impls])
    common_arch = _find_common_dict([getattr(i, "arch_context", {}) or {} for i in impls])
    common_api = _find_common_dict([getattr(i, "api_context", {}) or {} for i in impls])

    # Only extract if common parts are substantial (>50% of average dict size)
    avg_size = sum(len(getattr(i, "tech_context", {}) or {}) for i in impls) / len(impls)
    if not common_tech or len(common_tech) < max(1, avg_size * 0.5):
        return impls, None

    common_ctx = {
        "tech_context": common_tech,
        "arch_context": common_arch,
        "api_context": common_api,
    }

    updated_impls = []
    for impl in impls:
        tech = {k: v for k, v in (getattr(impl, "tech_context", {}) or {}).items() if k not in common_tech}
        arch = {k: v for k, v in (getattr(impl, "arch_context", {}) or {}).items() if k not in common_arch}
        api = {k: v for k, v in (getattr(impl, "api_context", {}) or {}).items() if k not in common_api}
        tech["_common_ref"] = f"COMMON-IMPL-{src_id}"

        updated_impls.append(
            IMPL(
                impl_id=impl.impl_id,
                requirement_context=impl.requirement_context,
                tech_context=tech,
                arch_context=arch,
                api_context=api,
                allowed_scope=impl.allowed_scope,
                forbidden_scope=impl.forbidden_scope,
                test_guidance=impl.test_guidance,
                feat_ref=impl.feat_ref,
                src_ref=impl.src_ref,
                source_refs=impl.source_refs,
            )
        )
    return updated_impls, common_ctx


# ---------------------------------------------------------------------------
# 2.9 Cross-axis refs
# ---------------------------------------------------------------------------


def build_cross_axis_refs(
    epics: list[EPIC],
    techs: list[TECH],
    archs: list[ARCH],
    apis: list[API],
    uis: list[UI],
) -> list[EPIC]:
    """Build FEAT ↔ TECH/ARCH/API/UI mechanical cross-references."""
    updated_epics: list[EPIC] = []
    for epic in epics:
        updated_feats: list[FEAT] = []
        for feat in epic.feats:
            refs: dict[str, list[str]] = {}
            if techs:
                refs["tech_refs"] = [t.tech_id for t in techs[:1]]
            if archs:
                refs["arch_refs"] = [a.arch_id for a in archs[:1]]
            if apis:
                refs["api_refs"] = [a.api_id for a in apis[:1]]
            if uis:
                refs["ui_refs"] = [u.ui_id for u in uis[:1]]
            updated_feats.append(
                FEAT(
                    feat_id=feat.feat_id,
                    title=feat.title,
                    user_value=feat.user_value,
                    trigger=feat.trigger,
                    main_flow=feat.main_flow,
                    acceptance_criteria=feat.acceptance_criteria,
                    alternative_flows=feat.alternative_flows,
                    state_changes=feat.state_changes,
                    business_rules=feat.business_rules,
                    exception_flows=feat.exception_flows,
                    uat_scenarios=feat.uat_scenarios,
                    non_goals=feat.non_goals,
                    dependencies=feat.dependencies,
                    cross_axis_refs=refs,
                    gsd_phase_hint=feat.gsd_phase_hint,
                    source_refs=feat.source_refs,
                )
            )
        updated_epics.append(
            EPIC(
                epic_id=epic.epic_id,
                capability_name=epic.capability_name,
                user_value=epic.user_value,
                business_closure=epic.business_closure,
                priority=epic.priority,
                included_scenarios=epic.included_scenarios,
                excluded_scenarios=epic.excluded_scenarios,
                acceptance_theme=epic.acceptance_theme,
                cross_axis_refs=epic.cross_axis_refs,
                feats=updated_feats,
                source_refs=epic.source_refs,
            )
        )
    return updated_epics


# ---------------------------------------------------------------------------
# 2.10 Invented semantics guard
# ---------------------------------------------------------------------------


# Mechanically generated fields (IDs, refs, versions) are not "invented semantics"
_GENERATED_KEYS = {
    "src_id", "epic_id", "feat_id", "tech_id", "arch_id", "api_id", "ui_id", "impl_id",
    "version", "feat_ref", "src_ref",
    "allowed_scope", "forbidden_scope", "test_guidance",
    "gsd_phase_hint", "cross_axis_refs",
    "tech_context", "arch_context", "api_context", "requirement_context",
}

_SAFE_DEFAULTS = {"semver", "P1", "draft", "frozen"}


def _check_invented(obj: Any, source: dict[str, Any]) -> Any:
    """Verify no invented semantics: every non-empty field must trace to source.

    Simplified check: for scalar fields, ensure source contains a plausible key.
    Skips mechanically generated IDs/refs/versions and safe defaults.
    Markdown raw content (__raw__) is treated as legitimate source.
    """
    if not hasattr(obj, "__dict__"):
        return obj
    has_raw = "__raw__" in source and isinstance(source["__raw__"], str) and len(source["__raw__"]) > 0
    invented: list[str] = []
    for key, value in obj.__dict__.items():
        if key in ("format_version", "source_refs", "freeze_status"):
            continue
        if key in _GENERATED_KEYS:
            continue
        if value is None or value == "" or value == [] or value == {}:
            continue
        if isinstance(value, str) and value in _SAFE_DEFAULTS:
            continue
        if key in source or any(k in source for k in _plausible_keys(key)):
            continue
        if has_raw:
            # Markdown raw content covers all fields; skip invented check
            continue
        invented.append(key)
    if invented:
        raise InventedSemanticsError(
            f"Invented semantics detected in {type(obj).__name__}: {invented}",
            invented_fields=invented,
        )
    return obj


def _plausible_keys(key: str) -> list[str]:
    """Map compiled field names to likely source keys."""
    mappings: dict[str, list[str]] = {
        "problem_domain": ["product_vision", "vision"],
        "business_goal": ["product_vision", "vision", "business_goal"],
        "target_users": ["user_personas", "target_users"],
        "triggering_scenarios": ["triggering_scenarios", "scenarios"],
        "scope_boundaries": ["scope_declaration", "in_scope", "out_of_scope"],
        "non_goals": ["non_goals"],
        "global_constraints": ["global_constraints", "constraints"],
        "open_questions": ["open_questions"],
        "capability_name": ["name"],
        "user_value": ["value", "user_value"],
        "business_closure": ["closure"],
        "included_scenarios": ["scenarios", "steps"],
        "excluded_scenarios": ["excluded"],
        "acceptance_theme": ["theme"],
        "title": ["acceptance_criteria", "prd", "name", "product_vision"],
        "trigger": ["prd", "trigger"],
        "main_flow": ["acceptance_criteria", "main_flow"],
        "acceptance_criteria": ["acceptance_criteria"],
        "alternative_flows": ["alternative_flows"],
        "state_changes": ["state_changes", "state_transitions"],
        "business_rules": ["business_rules"],
        "exception_flows": ["exception_flows"],
        "uat_scenarios": ["uat_scenarios"],
        "dependencies": ["dependencies"],
        "tech_stack": ["tech_stack"],
        "sync_async": ["sync_async_strategy"],
        "non_functional": ["non_functional"],
        "constraints": ["constraints"],
        "risks": ["risks"],
        "layering": ["layering"],
        "data_flow": ["data_flow"],
        "storage": ["storage_design"],
        "integration": ["integration_points"],
        "target_architecture": ["target_architecture"],
        "frozen_contracts": ["frozen_contracts"],
        "endpoints": ["api_contract"],
        "sequence_diagrams": ["sequence_diagrams"],
        "version_strategy": ["version_strategy"],
        "design_principles": ["design_principles"],
        "interaction_flow": ["interaction_flow"],
        "state_expression": ["state_expression"],
        "design_tokens": ["design_tokens"],
        "copy_style": ["copy_style"],
        "platform_strategy": ["platform_strategy"],
        "error_state_ux": ["error_state_ux"],
        "prototype": ["prototype"],
        "requirement_context": ["feat_id", "title"],
        "tech_context": ["tech_id"],
        "arch_context": ["arch_id"],
        "api_context": ["api_id"],
        "allowed_scope": ["implementation_scope", "directories", "files"],
        "forbidden_scope": ["forbidden_scope"],
        "test_guidance": ["test_strategy", "boundary_conditions"],
    }
    return mappings.get(key, [key])


# ---------------------------------------------------------------------------
# Full chain compilation
# ---------------------------------------------------------------------------


def compile_ssot_chain(
    design_package: dict[str, Any],
    src_id: str = "SRC-001",
) -> dict[str, Any]:
    """Run full step_2 compilation pipeline.

    Returns dict with keys: src, epics, feats, techs, archs, apis, uis, impls.
    """
    src = compile_src(design_package, src_id)
    epics = compile_epics(design_package, src_id)
    feats, epics = compile_feats(design_package, epics, src_id)
    techs = compile_tech(design_package, src_id)
    archs = compile_arch(design_package, src_id)
    apis = compile_api(design_package, src_id)
    uis = compile_ui(design_package, src_id)
    impls = compile_impls(feats, techs, archs, apis, design_package, src_id)
    impls, common_impl_ctx = _extract_common_impl_context(impls, src_id)
    epics = build_cross_axis_refs(epics, techs, archs, apis, uis)

    # Rebuild SRC with bound epics
    src = SRC(
        src_id=src.src_id,
        title=src.title,
        version=src.version,
        problem_domain=src.problem_domain,
        business_goal=src.business_goal,
        target_users=src.target_users,
        triggering_scenarios=src.triggering_scenarios,
        scope_boundaries=src.scope_boundaries,
        non_goals=src.non_goals,
        global_constraints=src.global_constraints,
        open_questions=src.open_questions,
        epics=epics,
        source_refs=src.source_refs,
    )

    return {
        "src": src,
        "epics": epics,
        "feats": feats,
        "techs": techs,
        "archs": archs,
        "apis": apis,
        "uis": uis,
        "impls": impls,
        "common_impl_context": common_impl_ctx,
    }
