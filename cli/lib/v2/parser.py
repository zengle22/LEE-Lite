"""Complete Design Package input parser.

Supports two layout modes:
1. Structured: dimension subdirectories (business_design/, product_design/, ...)
2. Flat fallback: filename-pattern mapping for flat Markdown directories

Tier 3 semantic extraction is NOT implemented in Python.
When Tier 2 rule-based extraction fails, a gap report is generated
for the skill agent to handle via natural language reasoning.

Truth source: design.md §Complete Design Package Input Structure.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("frz.parser")


SUPPORTED_EXTENSIONS = {".md", ".yaml", ".yml", ".json"}
DIMENSIONS = {
    "business_design",
    "product_design",
    "architecture_design",
    "engineering_design",
    "ux_design",
    "test_design",
}

REQUIRED_DIMENSIONS = {
    "business_design",
    "product_design",
    "architecture_design",
    "engineering_design",
}

# Flat-directory filename heuristic: keyword -> dimension
_FILENAME_DIMENSION_MAP: dict[str, str] = {
    # business_design
    "blueprint": "business_design",
    "vision": "business_design",
    "business": "business_design",
    "scope": "business_design",
    "goal": "business_design",
    "success_metrics": "business_design",
    # product_design
    "user_stories": "product_design",
    "acceptance_criteria": "product_design",
    "acceptance": "product_design",
    "journey": "product_design",
    "prd": "product_design",
    "feature": "product_design",
    "product": "product_design",
    "stories": "product_design",
    # architecture_design
    "decision_engine": "architecture_design",
    "architecture": "architecture_design",
    "arch": "architecture_design",
    "tech_stack": "architecture_design",
    "tech": "architecture_design",
    "api": "architecture_design",
    "data_model": "architecture_design",
    "system_design": "architecture_design",
    "knowledge_profile": "architecture_design",
    "structured_training": "architecture_design",
    "session_evaluation": "architecture_design",
    "training_state": "architecture_design",
    "runner": "architecture_design",
    # engineering_design
    "implementation": "engineering_design",
    "engineering": "engineering_design",
    "guardrail": "engineering_design",
    "audit": "engineering_design",
    "observability": "engineering_design",
    "deployment": "engineering_design",
    "context_and_ai": "engineering_design",
    # ux_design
    "ux": "ux_design",
    "ui": "ux_design",
    "design_principles": "ux_design",
    "frontend": "ux_design",
    "interaction": "ux_design",
    # test_design
    "test": "test_design",
    "qa": "test_design",
    "validation": "test_design",
    "verification": "test_design",
    "migration_checklist": "test_design",
    "enums_contract": "test_design",
    "contract": "test_design",
    "checklist": "test_design",
}

# ---------------------------------------------------------------------------
# Markdown section helpers
# ---------------------------------------------------------------------------

_JOURNEY_SKIP_KEYWORDS = {
    "目录",
    "附录",
    "图例",
    "统计",
    "范围界定",
    "问题陈述",
    "业务规则",
    "技术约束",
    "可测性",
    "评审结论",
    "旧 PRD",
    "状态转换图",
    "时序图",
    "交互场景",
    "AC → 测试",
    "映射表",
    "指标与数据源",
    "旅程总览",
    "文档说明",
}


def _extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and body from Markdown content.

    Returns (frontmatter_dict, body_text). frontmatter may be empty.
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        try:
            fm = yaml.safe_load(match.group(1)) or {}
            body = content[match.end():]
            return (fm, body)
        except yaml.YAMLError:
            pass
    return ({}, content)


def _extract_markdown_sections(raw: str, level: int = 2) -> list[dict[str, str]]:
    """Extract sections by Markdown heading level.

    Returns list of dicts with keys: title, body.
    """
    pattern = re.compile(rf"^(?:#{{{level}}})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(raw))
    sections: list[dict[str, str]] = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        # Stop early at any higher-level heading (## or #) that appears before
        # the next same-level heading — prevents scooping sibling L2 sections.
        higher_level_match = re.search(r'^#{1,2}\s+', raw[start:end], re.MULTILINE)
        if higher_level_match:
            end = start + higher_level_match.start()
        body = raw[start:end].strip()
        sections.append({"title": title, "body": body})
    return sections


def _extract_structured_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Extract structured fields from Markdown raw content.

    Scans __raw__ text for known heading / list patterns and produces
    compiler-friendly keys (user_journey_map, acceptance_criteria, etc.).
    """
    raw = data.get("__raw__", "")
    source_file = data.get("__source_file__", "")
    if not raw:
        return {}

    result: dict[str, Any] = {}
    source_lower = source_file.lower()

    # --- acceptance_criteria extraction ---
    # Matches list items like:
    #   - **AC-001.1**: Given ... When ... Then ...
    #   - **AC-M12-001.1**: Given ... (module prefix with hyphens)
    ac_pattern = re.compile(
        r'^\s*[-*]\s*\*\*(AC-[A-Za-z0-9._-]+)\*\*:\s*(.*?)(?=\n\s*[-*]\s*\*\*AC-|\n#{1,4}\s|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    ac_matches = ac_pattern.findall(raw)
    if ac_matches:
        ac_list: list[str] = []
        for ac_id, ac_text in ac_matches:
            ac_text = " ".join(ac_text.strip().splitlines())
            ac_list.append(f"{ac_id}: {ac_text}")
        result["acceptance_criteria"] = ac_list

    # --- user_journey_map extraction ---
    # Content-driven heuristic: scan for journey/story headings regardless
    # of filename. Filename hints are used as secondary signals only.
    has_journey_heading = bool(re.search(
        r'^#{2,4}\s*(?:用户旅程|User Journey|用户流程|User Flow|旅程|Journey)',
        raw, re.MULTILINE | re.IGNORECASE,
    ))
    has_story_heading = bool(re.search(
        r'^#{2,4}\s*(?:用户故事|User Story|US-\d+|Acceptance Criteria|验收标准)',
        raw, re.MULTILINE | re.IGNORECASE,
    ))
    # Filename hints (secondary, not blocking)
    is_journey_file = "journey" in source_lower or "user_journey" in source_lower
    is_story_file = "user_stories" in source_lower or "acceptance_criteria" in source_lower

    # Always scan if content signals OR filename signals are present
    if has_journey_heading or has_story_heading or is_journey_file or is_story_file:
        sections = _extract_markdown_sections(raw, level=2)
        journeys: list[dict[str, Any]] = []
        for section in sections:
            title = section["title"]
            body = section["body"]

            # Skip TOC / appendix / metadata sections
            if any(kw in title for kw in _JOURNEY_SKIP_KEYWORDS):
                continue

            # Content-driven: match journey/story headings even without filename hint
            is_story_section = bool(re.search(
                r'^P\d+\s+(?:用户故事|User Story|Story)|(?:用户故事|User Story|Story)\s+P\d+',
                title, re.IGNORECASE,
            ))
            is_journey_section = bool(re.search(
                r'用户旅程|User Journey|用户流程|User Flow|旅程|Journey',
                title, re.IGNORECASE,
            ))

            # For story sections, treat each US-XXX heading as a journey slice
            if is_story_section or (is_story_file and not is_journey_file):
                us_match = re.match(r'^P\d+\s+用户故事$', title)
                if us_match or is_story_section:
                    # This is a container section; extract US-XXX subsections
                    subsections = _extract_markdown_sections(body, level=3)
                    for sub in subsections:
                        sub_title = sub["title"]
                        sub_body = sub["body"]
                        if not re.match(r'^US-\d+[:\s]', sub_title):
                            continue
                        # Extract ACs from this US subsection
                        us_acs = []
                        for ac_id, ac_text in ac_pattern.findall(sub_body):
                            ac_text = " ".join(ac_text.strip().splitlines())
                            us_acs.append(f"{ac_id}: {ac_text}")
                        # First non-empty line as value
                        value = ""
                        for line in sub_body.splitlines():
                            stripped = line.strip()
                            if stripped and not stripped.startswith("#") and not stripped.startswith("```"):
                                value = stripped.lstrip("> ").strip()
                                if value:
                                    break
                        # Extract priority from parent L2 section title (e.g. "P0 用户故事")
                        priority_match = re.search(r'\bP([012])\b', title)
                        priority = f"P{priority_match.group(1)}" if priority_match else "P1"
                        journeys.append({
                            "name": sub_title,
                            "value": value,
                            "steps": us_acs,
                            "scenarios": us_acs,
                            "priority": priority,
                        })
                    continue

            # For journey sections, treat each remaining ## section as a journey
            if is_journey_section or is_journey_file:
                # Extract first descriptive paragraph as value
                value = ""
                for line in body.splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and not stripped.startswith("```"):
                        value = stripped.lstrip("> ").strip()
                        if value:
                            break

                # Extract sub-steps from ### headings
                steps: list[str] = []
                for m in re.finditer(r'^###\s+(.+)$', body, re.MULTILINE):
                    steps.append(m.group(1).strip())

                # Extract bullet list items as scenarios
                scenarios: list[str] = []
                for line in body.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("- ") or stripped.startswith("* "):
                        scenario = stripped[2:].strip()
                        if scenario and len(scenario) > 10 and not scenario.startswith("**AC-"):
                            scenarios.append(scenario)

                journeys.append({
                    "name": title,
                    "value": value,
                    "steps": steps,
                    "scenarios": scenarios,
                })

        if journeys:
            result["user_journey_map"] = journeys

    # --- product_vision extraction ---
    if "vision" in source_lower or "blueprint" in source_lower:
        vision_match = re.search(
            r'^#+\s+(?:Section\s+\d+:\s+)?(?:产品愿景|Product Vision|愿景|Vision).*\n+([*>]?\s*[^\n#].*?)(?:\n\s*\n|\n#{1,2}\s|\Z)',
            raw,
            re.MULTILINE | re.IGNORECASE,
        )
        if vision_match:
            vision_text = vision_match.group(1).strip().lstrip("> ").strip()
            # Strip surrounding bold/italic markdown markers
            vision_text = re.sub(r'^[*_]+|[*_]+$', '', vision_text)
            result["product_vision"] = vision_text
        else:
            first_heading = re.search(r'^#\s+(.+)$', raw, re.MULTILINE)
            if first_heading:
                result["product_vision"] = first_heading.group(1).strip()

    # --- scope_declaration extraction ---
    if "in scope" in raw.lower() or "out of scope" in raw.lower() or "scope" in source_lower:
        in_scope: list[str] = []
        out_scope: list[str] = []
        in_in = False
        in_out = False
        for line in raw.splitlines():
            stripped = line.strip()
            if re.match(r'^#{2,4}\s*In\s*Scope', stripped, re.IGNORECASE):
                in_in = True
                in_out = False
                continue
            if re.match(r'^#{2,4}\s*Out\s*(?:of\s*)?Scope', stripped, re.IGNORECASE):
                in_in = False
                in_out = True
                continue
            if stripped.startswith("## ") or stripped.startswith("# "):
                in_in = False
                in_out = False
                continue
            if in_in and (stripped.startswith("- ") or stripped.startswith("* ")):
                in_scope.append(stripped[2:].strip())
            if in_out and (stripped.startswith("- ") or stripped.startswith("* ")):
                out_scope.append(stripped[2:].strip())
        if in_scope or out_scope:
            result["scope_declaration"] = {"in_scope": in_scope, "out_of_scope": out_scope}

    # --- target_users extraction ---
    if "persona" in source_lower or "用户画像" in raw or "target user" in raw.lower():
        personas: list[dict[str, str]] = []
        # Look for L3 persona container, then extract L4 individual personas
        for section in _extract_markdown_sections(raw, level=3):
            if not any(kw in section["title"] for kw in ["用户画像", "画像", "Persona", "用户层级"]):
                continue
            subsections = _extract_markdown_sections(section["body"], level=4)
            if subsections:
                for sub in subsections:
                    if any(kw in sub["title"] for kw in ["用户画像", "画像", "Persona"]):
                        profile_text = _first_paragraph(sub["body"], max_len=1200)
                        # Table-only bodies (common for persona specs) need flattening
                        if not profile_text:
                            tables = _extract_markdown_tables(sub["body"])
                            if tables:
                                cells: list[str] = []
                                for row in tables[0]:
                                    for val in row.values():
                                        if val and isinstance(val, str) and val not in cells:
                                            cells.append(val)
                                profile_text = " | ".join(cells)[:1200]
                        personas.append({"role": sub["title"], "profile": profile_text})
            else:
                profile_text = _first_paragraph(section["body"], max_len=1200)
                personas.append({"role": section["title"], "profile": profile_text})
        if personas:
            result["target_users"] = personas

    # --- global_constraints extraction ---
    global_constraints: list[str] = []
    all_sections = _extract_markdown_sections(raw, level=2)
    for section in all_sections:
        if any(kw in section["title"] for kw in ["约束", "限制", "Constraint", "全局约束", "Global Constraint"]):
            for line in section["body"].splitlines():
                stripped = line.strip()
                if re.match(r'^\d+\.\s+', stripped) or stripped.startswith("- ") or stripped.startswith("* "):
                    item = re.sub(r'^\d+\.\s+', '', stripped).lstrip("- *").strip()
                    if item:
                        global_constraints.append(item)
    if global_constraints:
        result["global_constraints"] = global_constraints

    # --- tech_stack extraction ---
    is_tech_file = any(k in source_lower for k in [
        "implementation", "engineering", "tech_stack", "architecture",
        "decision_engine", "training_plan", "session_evaluation",
    ])
    has_tech_heading = bool(re.search(r'^#{1,4}\s*(?:技术选型|Tech Stack|技术栈|技术架构|Technology)', raw, re.MULTILINE | re.IGNORECASE))
    if is_tech_file or has_tech_heading:
        tech_stack: list[dict[str, str]] = []
        # Extract tables under tech headings
        tech_sections = _extract_markdown_sections(raw, level=2)
        for section in tech_sections:
            title = section["title"]
            if not re.search(r'技术选型|Tech Stack|技术栈|技术架构|Technology', title, re.IGNORECASE):
                continue
            body = section["body"]
            lines = [l.strip() for l in body.splitlines() if l.strip().startswith("|")]
            if len(lines) < 2:
                continue
            # Try to find header row and separator row
            header_idx = -1
            for idx, line in enumerate(lines):
                if "---" in line.replace(" ", ""):
                    header_idx = idx - 1
                    break
            if header_idx < 0 or header_idx >= len(lines):
                continue
            headers = [h.strip().lower() for h in lines[header_idx].split("|") if h.strip()]
            # Validate that this looks like a tech stack table
            _TECH_STACK_HEADERS = (
                "组件", "component", "技术", "technology", "选型", "stack", "name",
                "模块", "module", "服务", "service", "层", "layer",
                "依赖", "dependency", "框架", "framework",
                "库", "library", "工具", "tool", "平台", "platform",
                "语言", "language", "数据库", "database", "存储", "storage",
            )
            if not any(h in headers for h in _TECH_STACK_HEADERS):
                continue
            data_lines = lines[header_idx + 2:]
            for dline in data_lines:
                cells = [c.strip() for c in dline.split("|")]
                cells = [c for c in cells if c]  # remove empty from edges
                if len(cells) < 2:
                    continue
                entry: dict[str, str] = {}
                for h_idx, h in enumerate(headers):
                    if h_idx < len(cells):
                        entry[h] = cells[h_idx]
                if entry:
                    tech_stack.append(entry)
        if tech_stack:
            result["tech_stack"] = tech_stack

    # --- api_contract extraction ---
    is_api_file = any(k in source_lower for k in [
        "implementation", "engineering", "api", "architecture",
        "decision_engine", "training_plan", "session_evaluation",
    ])
    has_api_heading = bool(re.search(r'^#{1,4}\s*(?:API|接口|Endpoint)', raw, re.MULTILINE | re.IGNORECASE))
    if is_api_file or has_api_heading:
        api_contract: list[dict[str, str]] = []
        api_sections = _extract_markdown_sections(raw, level=2)
        for section in api_sections:
            title = section["title"]
            if not re.search(r'API|接口|Endpoint', title, re.IGNORECASE):
                continue
            body = section["body"]
            lines = [l.strip() for l in body.splitlines() if l.strip().startswith("|")]
            if len(lines) < 2:
                continue
            header_idx = -1
            for idx, line in enumerate(lines):
                if "---" in line.replace(" ", ""):
                    header_idx = idx - 1
                    break
            if header_idx < 0 or header_idx >= len(lines):
                continue
            headers = [h.strip().lower() for h in lines[header_idx].split("|") if h.strip()]
            # Validate that this looks like an API endpoint table
            if not any(h in headers for h in ("方法", "method", "路径", "path", "url", "endpoint", "接口", "route")):
                continue
            data_lines = lines[header_idx + 2:]
            for dline in data_lines:
                cells = [c.strip() for c in dline.split("|")]
                cells = [c for c in cells if c]
                if len(cells) < 2:
                    continue
                entry: dict[str, str] = {}
                for h_idx, h in enumerate(headers):
                    if h_idx < len(cells):
                        entry[h] = cells[h_idx]
                if entry:
                    api_contract.append(entry)
        if api_contract:
            result["api_contract"] = api_contract

    # ========================================================================
    # Phase 2 — Heading-driven extraction (architecture / engineering / ux)
    # ========================================================================
    dim = _infer_dimension(source_file)
    if dim == "architecture_design":
        result.update(_extract_architecture_fields(raw))
    elif dim == "engineering_design":
        result.update(_extract_engineering_fields(raw))
    elif dim == "ux_design":
        result.update(_extract_ux_fields(raw))

    # Phase 3 — API schema enrichment from subsection paragraphs
    api_enrichment = _extract_api_schemas(raw)
    if api_enrichment:
        result["api_schema_enrichment"] = api_enrichment

    return result


# ---------------------------------------------------------------------------
# Phase 2 — Heading-driven dimension extractors
# ---------------------------------------------------------------------------

def _infer_dimension(source_file: str) -> str | None:
    """Infer dimension from filename using the same heuristic as flat mapping."""
    name_lower = source_file.lower().replace("_", "")
    for keyword, dim in sorted(
        _FILENAME_DIMENSION_MAP.items(), key=lambda kv: len(kv[0]), reverse=True
    ):
        if keyword.replace("_", "") in name_lower:
            return dim
    return None


def _merge_field_result(a: Any, b: Any) -> Any:
    """Merge two extraction results (lists extend, dicts update, truthy wins)."""
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    if isinstance(a, dict) and isinstance(b, dict):
        merged = dict(a)
        merged.update(b)
        return merged
    return a if a else b


def _extract_markdown_tables(body: str) -> list[list[dict[str, str]]]:
    """Extract all Markdown tables from a body and return as list-of-list-of-dicts."""
    tables: list[list[dict[str, str]]] = []
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("|"):
            i += 1
            continue
        # Found potential table start; collect contiguous pipe-lines
        table_lines: list[str] = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            table_lines.append(lines[i].strip())
            i += 1
        if len(table_lines) < 2:
            continue
        # Find separator row (contains ---)
        header_idx = -1
        for idx, tl in enumerate(table_lines):
            if "---" in tl.replace(" ", ""):
                header_idx = idx - 1
                break
        if header_idx < 0 or header_idx >= len(table_lines):
            continue
        headers = [h.strip().lower() for h in table_lines[header_idx].split("|") if h.strip()]
        data_lines = table_lines[header_idx + 2:]
        rows: list[dict[str, str]] = []
        for dline in data_lines:
            cells = [c.strip() for c in dline.split("|")]
            cells = [c for c in cells if c]
            if len(cells) < 2:
                continue
            row: dict[str, str] = {}
            for h_idx, h in enumerate(headers):
                if h_idx < len(cells):
                    row[h] = cells[h_idx]
            if row:
                rows.append(row)
        if rows:
            tables.append(rows)
    return tables


def _structure_section_body(body: str, field_hint: str = "") -> Any:
    """Convert a Markdown section body into a structured object.

    Heuristic:
      - If body contains ### subsections, split by them and return list of dicts.
      - If body contains tables, preserve them.
      - Otherwise return cleaned text (first N chars).
    """
    keep_cb = field_hint in _CODE_BLOCK_KEEP_FIELDS
    max_len = 5000 if field_hint in _CODE_BLOCK_KEEP_FIELDS else 3000

    # Check for subsections (level 3 headings)
    subsections = _extract_markdown_sections(body, level=3)
    if len(subsections) >= 2:
        items: list[dict[str, Any]] = []
        for sub in subsections:
            sub_title = sub["title"].strip()
            sub_body = sub["body"]
            # Try to extract id from title patterns like "FC-DE-001：title" or "1.1 title"
            id_match = re.match(r'^(?:\d+\.\d+\s+)?([A-Z]+-[A-Z]+-\d+)[：:]\s*(.+)$', sub_title)
            # For frozen_contracts / data_flow, descriptions may span multiple
            # paragraphs (empty lines separate clauses). Use stop_at_empty=False.
            stop_early = field_hint not in ("frozen_contracts", "data_flow", "constraints")
            if id_match:
                item = {
                    "id": id_match.group(1),
                    "title": id_match.group(2),
                    "description": _first_paragraph(
                        sub_body, stop_at_empty=stop_early, keep_code_blocks=keep_cb
                    ),
                }
            else:
                item = {
                    "title": sub_title,
                    "description": _first_paragraph(
                        sub_body, stop_at_empty=stop_early, keep_code_blocks=keep_cb
                    ),
                }
            tables = _extract_markdown_tables(sub_body)
            if tables:
                item["tables"] = tables
            items.append(item)
        return items

    # Single table-heavy section → return tables
    tables = _extract_markdown_tables(body)
    if tables and len(tables) >= 1:
        # For state-expression / design-tokens, keep tables as primary payload
        if field_hint in ("state_expression", "design_tokens", "action_card_mapping"):
            return {"tables": tables, "text": _first_paragraph(body)}
        if field_hint in ("frozen_contracts", "design_principles", "constraints", "data_flow", "target_architecture"):
            return {"tables": tables, "text": _first_paragraph(body, max_len=max_len, keep_code_blocks=keep_cb)}

    # Fallback: cleaned text
    text = _first_paragraph(body, max_len=max_len, keep_code_blocks=keep_cb)
    if tables:
        return {"text": text, "tables": tables}
    return text


def _first_paragraph(
    body: str,
    max_len: int = 3000,
    stop_at_empty: bool = True,
    keep_code_blocks: bool = False,
) -> str:
    """Return first meaningful paragraph, stripping markdown noise.

    Args:
        stop_at_empty: If False, continue past empty lines (useful for
            frozen_contracts / data_flow where description spans multiple paragraphs).
        keep_code_blocks: If True, preserve text inside ``` fences (useful for
            architecture diagrams and contract clauses written in fenced blocks).
    """
    lines: list[str] = []
    in_code_block = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            # Always skip the fence lines themselves
            continue
        if in_code_block:
            if not keep_code_blocks:
                continue
            # Still skip empty lines inside code blocks so they don't trigger
            # stop_at_empty or add noise.
            if not stripped:
                continue
        if stripped.startswith("<!--"):
            continue
        if not stripped:
            if lines and stop_at_empty:
                break
            continue
        if stripped.startswith("|") and lines:
            # Stop at first table if we already have text
            break
        # Skip table header rows (like "| 维度 | 说明 |")
        if re.match(r'^\|[^|]+\|[^|]+\|', stripped):
            continue
        # Strip markdown inline markers
        cleaned = re.sub(r'^[*\->\s]+', '', stripped)
        # Remove pipe characters left from tables
        cleaned = cleaned.replace("|", " ").strip()
        if cleaned:
            lines.append(cleaned)
    text = " ".join(lines)
    return text[:max_len] if len(text) > max_len else text


# Fields whose primary content lives inside code blocks (architecture diagrams,
# flow charts, frozen contract text) and must NOT be stripped by _first_paragraph.
_CODE_BLOCK_KEEP_FIELDS: set[str] = {
    "target_architecture",
    "data_flow",
    "frozen_contracts",
    "constraints",
}


# --- Architecture ----------------------------------------------------------

_ARCH_HEADING_MAP: dict[str, str] = {
    r"目标架构|架构总览|系统架构": "target_architecture",
    r"模块结构|架构分层|职责边界|Engine/Service\s*分层": "layering",
    r"数据流|核心数据流|链路|流程改造|现有流程改造": "data_flow",
    # Removed "规范化" (matches 07.md input-normalisation fields) and "持久化"
    # (matches 04.md "不持久化" anti-pattern).
    r"存储方案|数据库表|表结构|JSONB": "storage_design",
    # Removed "不可违反" — it appears inside section bodies and causes pollution.
    r"Frozen\s*Contracts|架构契约|Frozen": "frozen_contracts",
    r"架构约束|安全要求|约束与安全": "constraints",
    r"非功能性|NFR|性能目标|并发|降级策略|容量预估": "non_functional_requirements",
    r"同步|异步|调用策略|超时|重试|立即生效|延迟生效": "sync_async_strategy",
    # Tightened "fallback" to avoid matching "Fallback Ladder" load-model sections.
    r"集成点|外部依赖|fallback\s*(策略|方案|设计|机制|降级|provider)|第三方|回调": "integration_points",
    r"时序图|序列图|Sequence\s*Diagram": "sequence_diagrams",
    r"版本策略|版本管理|兼容性": "version_strategy",
}

# Level-3 heading fallback for fields that are often nested under L2 sections
_ARCH_HEADING_MAP_LVL3: dict[str, str] = {
    r"模块结构|Engine/Service|分层.*职责|Handler|Service|Repository": "layering",
    r"数据库表|表结构|DDL|SQL|存储方案|JSONB": "storage_design",
    r"集成点|外部依赖|第三方|回调|fallback\s*(策略|方案|设计|机制|降级|provider)|Webhook": "integration_points",
}


def _extract_by_heading_level(raw: str, level: int, mapping: dict[str, str]) -> dict[str, Any]:
    """Generic heading-based extractor for arbitrary heading level."""
    result: dict[str, Any] = {}
    sections = _extract_markdown_sections(raw, level=level)
    for section in sections:
        title = section["title"]
        body = section["body"]
        for pattern, field_name in mapping.items():
            if re.search(pattern, title, re.IGNORECASE):
                structured = _structure_section_body(body, field_hint=field_name)
                if field_name in result:
                    result[field_name] = _merge_field_result(result[field_name], structured)
                else:
                    result[field_name] = structured
                break
    return result


def _extract_architecture_fields(raw: str) -> dict[str, Any]:
    """Extract architecture-design fields from Markdown headings."""
    result: dict[str, Any] = {}
    sections = _extract_markdown_sections(raw, level=2)
    for section in sections:
        title = section["title"]
        body = section["body"]
        for pattern, field_name in _ARCH_HEADING_MAP.items():
            if re.search(pattern, title, re.IGNORECASE):
                structured = _structure_section_body(body, field_hint=field_name)
                if field_name in result:
                    result[field_name] = _merge_field_result(result[field_name], structured)
                else:
                    result[field_name] = structured
                break

    # Lv3 fallback for critical fields that may be nested under L2 sections
    for field_name in ("layering", "storage_design", "integration_points"):
        if not result.get(field_name):
            lvl3_result = _extract_by_heading_level(raw, level=3, mapping=_ARCH_HEADING_MAP_LVL3)
            if field_name in lvl3_result:
                result[field_name] = lvl3_result[field_name]
    return result


# --- Engineering -----------------------------------------------------------

_ENG_HEADING_MAP: dict[str, str] = {
    r"模块到目录映射|预计修改的文件清单|涉及模块|实施范围|Implementation\s*Scope": "implementation_scope",
    r"关键实现决策|实现决策|决策记录|拍板|已确定": "key_decisions",
    r"依赖关系|前置条件|前置依赖|依赖": "dependencies",
    r"回滚|降级策略|发布失败|Rollback": "rollback_strategy",
    r"容量|性能预估|Token|数据量|QPS|存储增长": "capacity_estimate",
    r"技术选型|Tech\s*Stack|技术栈|Technology": "tech_stack",
    r"API\s*契约|接口|Endpoint|API\s*变更": "api_contract",
    r"架构约束|安全要求|约束": "constraints",
    r"非功能性|NFR|性能|并发|降级": "non_functional_requirements",
    r"风险|Risks|已知风险": "risks",
    r"同步异步|调用策略|超时|重试|立即生效|延迟生效": "sync_async_strategy",
}


def _extract_risks(body: str) -> list[dict[str, str]]:
    """Parse **风险 N**: description  - 缓解: mitigation format."""
    risks: list[dict[str, str]] = []
    pattern = re.compile(
        r'^\s*[-*]\s*\*\*风险\s*(\d+)\s*\*\*[：:]\s*(.+?)(?=\n\s*[-*]\s*\*\*风险|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    for match in pattern.finditer(body):
        risk_num = match.group(1)
        desc_block = match.group(2).strip()
        mitigation = ""
        desc_lines: list[str] = []
        for line in desc_block.splitlines():
            stripped = line.strip()
            if re.match(r'^[-*]\s*缓解[：:]', stripped):
                mitigation = re.sub(r'^[-*]\s*缓解[：:]\s*', '', stripped)
            else:
                desc_lines.append(stripped)
        risks.append({
            "id": f"RISK-{risk_num}",
            "description": " ".join(desc_lines).strip(),
            "mitigation": mitigation,
        })
    return risks


def _extract_engineering_fields(raw: str) -> dict[str, Any]:
    """Extract engineering-design fields from Markdown headings."""
    result: dict[str, Any] = {}
    sections = _extract_markdown_sections(raw, level=2)
    for section in sections:
        title = section["title"]
        body = section["body"]
        for pattern, field_name in _ENG_HEADING_MAP.items():
            if re.search(pattern, title, re.IGNORECASE):
                # Special handling: keep legacy table format for tech_stack / api_contract
                if field_name == "tech_stack":
                    tables = _extract_markdown_tables(body)
                    structured = tables[0] if tables else _structure_section_body(body, field_hint=field_name)
                elif field_name == "api_contract":
                    tables = _extract_markdown_tables(body)
                    endpoints: list[dict[str, str]] = []
                    for table in tables:
                        if table and any(k in table[0] for k in ("方法", "method", "路径", "path", "url", "endpoint", "接口", "route")):
                            endpoints.extend(table)
                    structured = endpoints if endpoints else _structure_section_body(body, field_hint=field_name)
                elif field_name == "implementation_scope":
                    structured = _extract_implementation_scope(body)
                elif field_name == "risks":
                    risks_list = _extract_risks(body)
                    structured = risks_list if risks_list else _structure_section_body(body, field_hint=field_name)
                else:
                    structured = _structure_section_body(body, field_hint=field_name)
                if field_name in result:
                    result[field_name] = _merge_field_result(result[field_name], structured)
                else:
                    result[field_name] = structured
                break
    return result


def _extract_implementation_scope(body: str) -> dict[str, Any]:
    """Extract directories and files from implementation-scope sections."""
    dirs: list[str] = []
    files: list[str] = []
    excluded: list[str] = []

    # Helper to classify a clean path
    def _classify_path(item: str, ctx_line: str) -> None:
        if not item or len(item) < 3:
            return
        if " " in item or "（" in item or "(" in item:
            # Contains spaces or Chinese parens → descriptive text, not a raw path
            return
        if item in ("/", "—", "-", "→"):
            return
        if item.startswith("docs/design/") or item.startswith(".artifacts/") or item.startswith("_bmad"):
            return
        # Must contain at least one alphanumeric char
        if not re.search(r'[a-zA-Z0-9]', item):
            return
        if any(kw in ctx_line.lower() for kw in ("不碰", "exclude", "skip", "不做", "out of scope", "禁止修改")):
            excluded.append(item)
        elif "." in item.split("/")[-1]:
            files.append(item)
        else:
            dirs.append(item)

    # Pass 1: extract ALL backtick-enclosed paths from the entire body
    # (covers both bullet lists and multi-line table cells)
    for match in re.finditer(r'`([^`\n]+)`', body):
        path = match.group(1).strip()
        if "/" in path or "\\" in path:
            # Skip obviously non-code paths
            if path in ("/", "./", "../") or path.startswith("docs/design/") or path.startswith(".artifacts/"):
                continue
            _classify_path(path, body)

    # Pass 2: directory-mapping tables — catch bare paths in cells
    tables = _extract_markdown_tables(body)
    for table in tables:
        for row in table:
            for cell in row.values():
                for match in re.finditer(r'`([^`\n]+)`', cell):
                    path = match.group(1).strip()
                    if "/" in path or "\\" in path:
                        _classify_path(path, cell)
                # Also catch bare paths in table cells
                for part in cell.split():
                    part = part.strip().strip("`")
                    if "/" in part and " " not in part and "（" not in part and "(" not in part:
                        _classify_path(part, cell)

    scope: dict[str, Any] = {}
    if dirs:
        scope["directories"] = list(dict.fromkeys(dirs))
    if files:
        scope["files"] = list(dict.fromkeys(files))
    if excluded:
        scope["excluded_files"] = list(dict.fromkeys(excluded))
    if not scope:
        scope["raw_text"] = _first_paragraph(body)
    return scope


# --- UX --------------------------------------------------------------------

_UX_HEADING_MAP: dict[str, str] = {
    r"设计原则|UX\s*原则|核心原则|UX\s*Design\s*Principles": "design_principles",
    r"交互流程|页面跳转|状态机|关键页面交互|前端状态流转": "interaction_flow",
    r"状态表达|视觉映射|颜色.*映射|State\s*Visualization|状态表达规则": "state_expression",
    r"设计令牌|Design\s*Tokens|variables|令牌引用|Token": "design_tokens",
    r"文案风格|语气|口吻|微文案|禁忌词|Copy\s*Style": "copy_style",
    r"错误状态|异常展示|降级内容|错误.*UX|Error\s*State": "error_state_ux",
    r"平台差异|多端适配|H5.*小程序|响应式|Platform": "platform_strategy",
    r"卡片设计|组件规格|Card.*设计|Component": "component_specs",
    r"Action.*映射|卡片类型映射|显式.*契约|卡片.*映射": "action_card_mapping",
    r"原型|Prototype|Mockup|Wireframe": "prototype",
}


def _extract_ux_fields(raw: str) -> dict[str, Any]:
    """Extract UX-design fields from Markdown headings."""
    result: dict[str, Any] = {}
    sections = _extract_markdown_sections(raw, level=2)
    for section in sections:
        title = section["title"]
        body = section["body"]
        for pattern, field_name in _UX_HEADING_MAP.items():
            if re.search(pattern, title, re.IGNORECASE):
                structured = _structure_section_body(body, field_hint=field_name)
                if field_name in result:
                    result[field_name] = _merge_field_result(result[field_name], structured)
                else:
                    result[field_name] = structured
                break
    return result


# --- API Schema enrichment -------------------------------------------------

_API_METHOD_PATTERN = re.compile(r'\b(GET|POST|PUT|DELETE|PATCH)\b')
_API_PATH_PATTERN = re.compile(r'`?(/v\d+[^`\s]*)`?')


def _extract_api_schemas(raw: str) -> list[dict[str, Any]]:
    """Extract detailed request/response/error schemas from API subsections.

    Looks for level-3/4 headings that look like endpoint descriptions and
    extracts bullet-list parameters / tables underneath.
    """
    schemas: list[dict[str, Any]] = []
    # Match both ### and #### headings
    heading_re = re.compile(r'^(#{3,4})\s+(.+)$', re.MULTILINE)
    matches = list(heading_re.finditer(raw))
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        # Heuristic: does this heading look like an endpoint?
        has_method = _API_METHOD_PATTERN.search(title)
        has_path = _API_PATH_PATTERN.search(title)
        if not (has_method or has_path):
            continue
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        # Stop early at any higher-level heading (## or #) that appears before
        # the next same-level heading — prevents scooping sibling L2 sections.
        higher_level_match = re.search(r'^#{1,2}\s+', raw[start:end], re.MULTILINE)
        if higher_level_match:
            end = start + higher_level_match.start()
        body = raw[start:end]

        schema: dict[str, Any] = {
            "endpoint_title": title,
            "request_schema": {},
            "response_schema": {},
            "error_codes": {},
        }
        current_target: str | None = None

        # Phase 1: extract from bullet lists
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Detect section markers inside the endpoint body
            lower = stripped.lower()
            if any(k in lower for k in ("请求体", "request body", "输入", "input", "参数")):
                current_target = "request"
                continue
            if any(k in lower for k in ("响应", "response", "输出", "output", "返回")):
                current_target = "response"
                continue
            if any(k in lower for k in ("错误码", "错误", "error code", "status code")):
                current_target = "error"
                continue
            if stripped.startswith("##"):
                current_target = None
                continue

            if stripped.startswith("- ") or stripped.startswith("* "):
                item = stripped[2:].strip()
                # Try to parse "name (type, required): description"
                param_match = re.match(r'^`?([^`(:]+)`?\s*(?:\(([^)]+)\))?\s*[:：]\s*(.*)$', item)
                if param_match:
                    name = param_match.group(1).strip()
                    type_req = (param_match.group(2) or "").strip()
                    desc = param_match.group(3).strip()
                    entry: dict[str, Any] = {"description": desc}
                    if type_req:
                        entry["type"] = type_req
                    if current_target == "request":
                        schema["request_schema"][name] = entry
                    elif current_target == "response":
                        schema["response_schema"][name] = entry
                    elif current_target == "error":
                        # Try to parse "400: description" or "400 参数非法"
                        code_match = re.match(r'^(\d{3})\s*[:：]\s*(.*)$', item)
                        if code_match:
                            schema["error_codes"][code_match.group(1)] = code_match.group(2)
                        else:
                            schema["error_codes"][name] = desc
                else:
                    # Loose match: just store as text under current target
                    if current_target == "request":
                        schema["request_schema"]["_notes"] = schema["request_schema"].get("_notes", "") + "\n" + item
                    elif current_target == "response":
                        schema["response_schema"]["_notes"] = schema["response_schema"].get("_notes", "") + "\n" + item
                    elif current_target == "error":
                        schema["error_codes"]["_notes"] = schema["error_codes"].get("_notes", "") + "\n" + item

        # Phase 2: extract from Markdown tables (e.g. | 字段 | 类型 | 必填 | 说明 |)
        tables = _extract_markdown_tables(body)
        for table in tables:
            if not table:
                continue
            headers = [h.lower() for h in table[0].keys()]
            # Detect table type by headers
            is_request = any(k in headers for k in ("字段", "参数", "field", "name", "参数名"))
            is_response = any(k in headers for k in ("返回", "响应字段", "output"))
            is_error = any(k in headers for k in ("错误码", "状态码", "code", "status"))
            # Fallback heuristic: 字段+类型+说明 without 必填/参数 is likely a response table
            if not is_response and not is_error and is_request:
                has_type = any(k in headers for k in ("类型", "type"))
                has_desc = any(k in headers for k in ("说明", "描述", "description"))
                no_required = not any(k in headers for k in ("必填", "required", "参数", "参数名"))
                if has_type and has_desc and no_required:
                    is_response = True
            if not (is_request or is_response or is_error):
                continue
            for row in table:
                # Try to find name and type from row
                name = row.get("字段") or row.get("参数") or row.get("field") or row.get("name") or row.get("参数名", "")
                typ = row.get("类型") or row.get("type", "")
                desc = row.get("说明") or row.get("描述") or row.get("description", "")
                req = row.get("必填") or row.get("required", "")
                # Error-code tables use 错误码/状态码 as the key column
                if is_error and not name:
                    name = row.get("错误码") or row.get("状态码") or row.get("code") or ""
                if not name:
                    continue
                entry = {"description": desc}
                if typ:
                    entry["type"] = typ
                if req:
                    entry["required"] = req in ("是", "true", "True", "TRUE", "yes", "Yes", "Y", "y")
                if is_error:
                    code = row.get("错误码") or row.get("状态码") or row.get("code") or name
                    schema["error_codes"][str(code)] = desc or typ
                elif is_response:
                    schema["response_schema"][name] = entry
                else:
                    schema["request_schema"][name] = entry

        # Only keep endpoints that actually have some schema data
        if schema["request_schema"] or schema["response_schema"] or schema["error_codes"]:
            schemas.append(schema)
    return schemas


def _load_file(path: Path) -> dict[str, Any]:
    """Load a single file into a dict."""
    ext = path.suffix.lower()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if ext in {".yaml", ".yml"}:
        return yaml.safe_load(content) or {}
    if ext == ".json":
        return json.loads(content)
    # Markdown: try frontmatter extraction, fall back to raw body
    frontmatter, body = _extract_frontmatter(content)
    result = dict(frontmatter)
    result["__raw__"] = body
    result["__source_file__"] = path.name
    return result


def _detect_flat_dimensions(root: Path) -> dict[str, list[Path]]:
    """When no dimension subdirectories exist, map files by name heuristic.

    Recursively scans all files under root (including nested subdirectories)
    to support projects that organize docs by type in sub-folders.
    """
    mapping: dict[str, list[Path]] = {}
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        name_lower = file_path.stem.lower()
        matched_dim: str | None = None
        # Try longest keyword first to avoid partial matches winning
        for keyword, dim in sorted(
            _FILENAME_DIMENSION_MAP.items(), key=lambda kv: len(kv[0]), reverse=True
        ):
            if keyword.replace("_", "") in name_lower.replace("_", ""):
                matched_dim = dim
                break
        if matched_dim:
            mapping.setdefault(matched_dim, []).append(file_path)
    return mapping


def _merge_dim_data(merged: dict[str, Any], data: dict[str, Any], file_path: Path) -> None:
    """Merge a single file's data into a dimension dict.

    Preserves __raw__ by appending rather than overwriting.
    Extracts structured fields from Markdown before merging.
    """
    # Extract structured fields from Markdown raw content
    extracted = _extract_structured_fields(data)
    for key, value in extracted.items():
        if key in merged:
            existing = merged[key]
            if isinstance(existing, list) and isinstance(value, list):
                existing.extend(value)
            elif isinstance(existing, dict) and isinstance(value, dict):
                existing.update(value)
            else:
                merged[key] = value
        else:
            merged[key] = value

    # Preserve raw content (append, don't overwrite)
    if "__raw__" in data:
        existing_raw = merged.get("__raw__", "")
        source_marker = f"\n\n<!-- source: {data.get('__source_file__', file_path.name)} -->\n\n"
        if existing_raw:
            merged["__raw__"] = existing_raw + source_marker + data["__raw__"]
        else:
            merged["__raw__"] = data["__raw__"]
        merged.setdefault("__source_files__", []).append(data.get("__source_file__", file_path.name))
    else:
        # Non-Markdown: merge non-metadata keys directly
        for k, v in data.items():
            if not k.startswith("__"):
                merged[k] = v


# ---------------------------------------------------------------------------
# Tier 3 — Gap report generation (for agent-driven semantic extraction)
# ---------------------------------------------------------------------------

# Fields that trigger completeness gates and may need agent semantic extraction.
# Map: dimension -> list of field names with descriptions for the agent.
_GAP_SENSITIVE_FIELDS: dict[str, list[dict[str, str]]] = {
    "business_design": [
        {"field": "product_vision", "description": "产品愿景 / Product Vision — 一句话描述产品要解决什么问题"},
        {"field": "scope_declaration", "description": "范围声明 — in_scope / out_of_scope 列表"},
    ],
    "product_design": [
        {"field": "user_journey_map", "description": "用户旅程 — 用户完成目标的步骤列表，每个步骤包含 name/value/steps/priority"},
        {"field": "acceptance_criteria", "description": "验收标准 — Given/When/Then 格式的 AC 列表"},
        {"field": "target_users", "description": "目标用户画像 — persona 列表，包含 role 和 profile"},
    ],
    "architecture_design": [
        {"field": "tech_stack", "description": "技术选型 — 组件/技术/版本表格"},
        {"field": "api_contract", "description": "API 契约 — endpoint 定义表格（方法、路径、参数）"},
        {"field": "layering", "description": "分层架构 — 模块结构描述"},
        {"field": "storage_design", "description": "存储设计 — 数据库/表结构设计"},
    ],
    "engineering_design": [
        {"field": "implementation_scope", "description": "实施范围 — 目录和文件清单"},
        {"field": "key_decisions", "description": "关键决策 — 技术决策记录"},
        {"field": "risks", "description": "风险列表 — 风险描述和缓解措施"},
    ],
    "ux_design": [
        {"field": "prototype", "description": "原型 — HTML 或原型引用"},
        {"field": "design_principles", "description": "设计原则 — UX 核心原则"},
        {"field": "interaction_flow", "description": "交互流程 — 页面跳转和状态流转"},
    ],
}


def generate_gap_report(design_package: dict[str, Any]) -> dict[str, Any]:
    """Generate a gap report for agent-driven semantic extraction.

    Scans the design package for fields that Tier 2 failed to extract
    (empty or missing) but the dimension has substantive raw content.
    Returns a structured report that the skill agent consumes.
    """
    gaps: list[dict[str, Any]] = []

    for dimension, field_defs in _GAP_SENSITIVE_FIELDS.items():
        dim_data = design_package.get(dimension, {})
        if not isinstance(dim_data, dict):
            continue

        raw = dim_data.get("__raw__", "")
        if not raw or len(raw.strip()) < 200:
            continue  # No substantive content to extract from

        source_files = dim_data.get("__source_files__", [])

        for field_def in field_defs:
            field_name = field_def["field"]
            value = dim_data.get(field_name)

            # Check if field is empty
            is_empty = False
            if value is None:
                is_empty = True
            elif isinstance(value, (list, dict, str)) and len(value) == 0:
                is_empty = True

            if is_empty:
                # Build a preview of the raw content (first 2000 chars)
                raw_preview = raw[:2000].strip()
                if len(raw) > 2000:
                    raw_preview += "\n...[truncated]"

                gaps.append({
                    "dimension": dimension,
                    "field": field_name,
                    "description": field_def["description"],
                    "source_files": source_files,
                    "raw_preview": raw_preview,
                    "tier2_status": "extraction_empty",
                    "suggested_agent_action": (
                        f"Read the source document(s) for {dimension} and extract "
                        f"the '{field_name}' field. Return the result as structured data."
                    ),
                })

    return {
        "total_gaps": len(gaps),
        "has_gaps": len(gaps) > 0,
        "gaps": gaps,
    }


def apply_semantic_extraction(
    design_package: dict[str, Any],
    extraction_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Apply agent-provided semantic extraction results into the design package.

    Args:
        design_package: The current design package dict (will be mutated).
        extraction_results: Map of dimension -> {field_name: extracted_value}
                            as provided by the skill agent.

    Returns:
        The mutated design_package with agent-extracted fields merged in.
    """
    for dimension, fields in extraction_results.items():
        if dimension not in design_package:
            logger.warning(f"Agent extraction targets unknown dimension: {dimension}")
            continue
        dim_data = design_package[dimension]
        if not isinstance(dim_data, dict):
            continue
        for field_name, value in fields.items():
            if value is not None and value != [] and value != {}:
                dim_data[field_name] = value
                logger.info(f"Agent extraction applied: {dimension}.{field_name}")
    return design_package


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_design_package(package_dir: str | Path) -> dict[str, Any]:
    """Parse a Complete Design Package directory.

    Supports two layouts:
    1. Structured: dimension subdirectories with YAML/JSON/Markdown files.
    2. Flat fallback: no subdirectories — files mapped by filename heuristic.

    Args:
        package_dir: Path to the design package root directory.

    Returns:
        Dict keyed by dimension name, each value a merged dict of files.
    """
    root = Path(package_dir)
    if not root.is_dir():
        raise ValueError(f"Design package path is not a directory: {root}")

    result: dict[str, Any] = {}

    # --- Mode 1: structured subdirectories ---
    has_structured = any((root / dim).is_dir() for dim in DIMENSIONS)
    if has_structured:
        for dim in DIMENSIONS:
            dim_dir = root / dim
            if not dim_dir.is_dir():
                continue
            merged: dict[str, Any] = {}
            for file_path in sorted(dim_dir.iterdir()):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    data = _load_file(file_path)
                    if isinstance(data, dict):
                        _merge_dim_data(merged, data, file_path)
            if merged:
                result[dim] = merged
        return result

    # --- Mode 2: flat directory with filename heuristics ---
    flat_mapping = _detect_flat_dimensions(root)
    for dim, files in flat_mapping.items():
        merged: dict[str, Any] = {}
        for file_path in files:
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            data = _load_file(file_path)
            if isinstance(data, dict):
                _merge_dim_data(merged, data, file_path)
        if merged:
            result[dim] = merged
    return result
