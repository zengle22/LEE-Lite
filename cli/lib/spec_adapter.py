"""SPEC_ADAPTER_COMPAT bridge: converts ADR-047 spec files to TESTSET-compatible format.

This module parses api-test-spec/*.md and e2e-journey-spec/*.md files and converts them
to SPEC_ADAPTER_COMPAT YAML format that test_exec_runtime.py can consume.

Per ADR-054 §2.2, §5.1 R-1, R-2, R-6.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Input DTO
# ---------------------------------------------------------------------------


@dataclass
class SpecAdapterInput:
    """Input for spec_to_testset conversion."""

    spec_files: list[Path]
    feat_ref: str | None = None
    proto_ref: str | None = None
    modality: str = "api"  # api | web_e2e | cli


# ---------------------------------------------------------------------------
# Selector resolution (ADR-054 §5.1 R-2)
# ---------------------------------------------------------------------------


def _resolve_selector(action: str, step: dict[str, Any]) -> str | None:
    """Resolve selector from a user_step based on target_format.

    Args:
        action: The action name from the step
        step: The step dict containing target and target_format

    Returns:
        Resolved selector string or None if unresolvable
    """
    fmt = step.get("target_format", "css_selector")
    target = step.get("target", "")

    if fmt == "css_selector":
        return target
    elif fmt == "semantic":
        return f"[data-action={action}]"
    elif fmt == "text":
        return f"text={target}"
    elif fmt == "xpath":
        return target

    return None


# ---------------------------------------------------------------------------
# Markdown parsing utilities
# ---------------------------------------------------------------------------


def _parse_table_rows(content: str) -> dict[str, str]:
    """Parse a markdown table into a key-value dict.

    Handles tables with '| field | value |' format.
    """
    result: dict[str, str] = {}
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Remove leading/trailing pipes and split
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2:
            key = parts[0].strip()
            value = parts[1].strip()
            if key and value:
                result[key] = value
    return result


def _extract_code_block(content: str) -> str:
    """Extract JSON/code block from markdown content."""
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()


def _split_sections(content: str) -> dict[str, str]:
    """Split markdown content into sections by ## and ### headings."""
    sections: dict[str, str] = {}
    current_heading = "_preamble"
    current_content: list[str] = []

    for line in content.split("\n"):
        if line.startswith("## ") or line.startswith("### "):
            if current_content:
                sections[current_heading] = "\n".join(current_content).strip()
            m = re.match(r"#{2,3}\s+(.+)", line)
            current_heading = m.group(1) if m else "_other"
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_heading] = "\n".join(current_content).strip()

    return sections


def _parse_yaml_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            pass
    return {}


# ---------------------------------------------------------------------------
# Section mapping with fuzzy matching
# ---------------------------------------------------------------------------

_SECTION_MAP = {
    "case_metadata": ["Case Metadata", "案例元数据"],
    "entry_point": ["entry_point", "Entry Point", "入口点"],
    "user_steps": ["User Steps", "用户步骤", "user_steps"],
    "expected_ui_states": ["Expected UI States", "期望 UI 状态", "expected_ui_states"],
    "expected_network_events": ["Expected Network Events", "期望网络事件", "expected_network_events"],
    "expected_persistence": ["Expected Persistence", "期望持久化", "expected_persistence"],
    "anti_false_pass_checks": ["Anti-False-Pass Checks", "反假阳性检查", "反假阳性", "anti_false_pass_checks"],
    "evidence_required": ["evidence_required", "Evidence Required", "证据要求"],
    "source_refs": ["source_refs", "Source Refs", "来源引用"],
}


def _find_section_fuzzy(keys: list[str], sections: dict[str, str]) -> str:
    """Find section content with fuzzy matching (supports numbered prefixes like '## 2. user_steps')."""
    for key in keys:
        if key in sections:
            return sections[key]
        for section_key in sections:
            if key.lower() in section_key.lower():
                return sections[section_key]
    return ""


def _extract_table_field(content: str, field_name: str) -> str:
    """Extract a specific field value from an Item/Detail table."""
    # Match | Field Name | value | (case-insensitive)
    pattern = re.compile(r"\|\s*" + re.escape(field_name) + r"\s*\|\s*([^\|]+?)\s*\|", re.IGNORECASE)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""


def _parse_flat_table(content: str) -> list[dict[str, str]]:
    """Parse a markdown table with header row into a list of row dicts."""
    lines = content.strip().split("\n")
    headers: list[str] = []
    rows: list[dict[str, str]] = []
    in_table = False

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            if in_table:
                break
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        # Skip separator lines (all dashes/spaces)
        if all(p.replace("-", "").replace(" ", "") == "" for p in parts):
            in_table = True
            continue
        if not in_table:
            headers = parts
            in_table = True
        else:
            if headers:
                row: dict[str, str] = {}
                for i, h in enumerate(headers):
                    if i < len(parts):
                        row[h] = parts[i]
                if row:
                    rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# User steps parsing (three-format support)
# ---------------------------------------------------------------------------


def _parse_step_section_format(user_steps_text: str) -> list[dict[str, Any]]:
    """Parse ### Step N: Title + Item/Detail table format (SRC-006 style)."""
    steps: list[dict[str, Any]] = []
    # Match ### Step N: Title followed by content until next ### Step or end
    pattern = re.compile(r"###\s*Step\s*\d+[A-Z]?:[^\n]*\n+(.*?)(?=###\s*Step|\Z)", re.DOTALL)
    for match in pattern.finditer(user_steps_text):
        section_content = match.group(1)
        action = _extract_table_field(section_content, "User Action")
        if action:
            steps.append({"raw_action": action})
    return steps


def _parse_flat_table_format(user_steps_text: str) -> list[dict[str, Any]]:
    """Parse | Step | Action | Expected UI Feedback | format (SRC-007 style)."""
    rows = _parse_flat_table(user_steps_text)
    steps: list[dict[str, Any]] = []
    for row in rows:
        action = row.get("Action", "")
        # Skip header-like rows
        if action and action.lower() not in ("action", "user action", "detail"):
            steps.append({"raw_action": action})
    return steps


def _parse_numbered_list_format(user_steps_text: str) -> list[dict[str, Any]]:
    """Parse 1. xxx numbered list format (legacy style)."""
    steps: list[dict[str, Any]] = []
    step_pattern = re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE)
    for match in step_pattern.finditer(user_steps_text):
        steps.append({"raw_action": match.group(1).strip()})
    return steps


def _parse_user_steps(user_steps_text: str) -> list[dict[str, Any]]:
    """Parse user steps supporting three formats."""
    if not user_steps_text.strip():
        return []

    # Priority 1: Step section format (SRC-006)
    steps = _parse_step_section_format(user_steps_text)
    if steps:
        return steps

    # Priority 2: Flat table format (SRC-007)
    steps = _parse_flat_table_format(user_steps_text)
    if steps:
        return steps

    # Priority 3: Numbered list format (legacy)
    return _parse_numbered_list_format(user_steps_text)


# ---------------------------------------------------------------------------
# Action normalization (NLU -> Playwright)
# ---------------------------------------------------------------------------

_ACTION_PATTERNS: list[tuple[str, str]] = [
    # NOTE: removed \b word boundaries because they don't work reliably with
    # Chinese characters (which are both \w and adjacent to each other).
    # Order matters: more specific actions should come before generic ones.
    # fill comes before click because "Type X OR click Y" should prefer fill.
    (r"(?:goto|visit|open|打开|进入|访问|导航至|跳转至)", "goto"),
    (r"(?:fill|type|输入|填写|键入)", "fill"),
    (r"(?:click|点击|按下|请求|提交)", "click"),
    (r"(?:check|选择|勾选|启用)", "check"),
    (r"(?:uncheck|取消选择|取消勾选|禁用)", "uncheck"),
    (r"(?:select|下拉选择|从下拉框选择)", "select"),
    (r"(?:press|按|回车|提交)", "press"),
    (r"(?:assert_visible|验证.*可见|出现|显示)", "assert_visible"),
    (r"(?:assert_hidden|验证.*隐藏|消失|关闭)", "assert_hidden"),
    (r"(?:assert_text|验证.*文本|包含.*文字)", "assert_text"),
    (r"(?:assert_url|验证.*URL|页面地址)", "assert_url"),
    (r"(?:assert_title|验证.*标题)", "assert_title"),
    (r"(?:screenshot|截图|截屏)", "screenshot"),
]

_SELECTOR_PATTERNS: list[str] = [
    r"\[data-testid=[\"']([^\"']+)[\"']\]",
    r"\[data-[^=]+=[\"']([^\"']+)[\"']\]",
    r"#([a-zA-Z0-9_-]+)",
    r"\.([a-zA-Z0-9_-]+)",
]


def _clean_ui_text(content: str) -> str:
    """Remove markdown bracket notation from UI text.

    Spec format uses [按钮文字] to denote buttons, but actual UI text
    doesn't include the brackets. Strip leading/trailing [] pairs.
    """
    content = content.strip()
    # Remove outer brackets: [文字] -> 文字
    if content.startswith("[") and content.endswith("]"):
        content = content[1:-1].strip()
    return content


def _extract_selectors_from_text(text: str) -> str | None:
    """Extract CSS selector or data-testid from action text."""
    for pat in _SELECTOR_PATTERNS:
        match = re.search(pat, text)
        if match:
            sel = match.group(0)
            # If it looks like a valid CSS selector, return as-is
            if sel.startswith(("#", ".", "[data-", "[aria-")):
                return sel
            # Otherwise it's probably not a valid CSS selector
            continue
    # Try backtick content — but skip code-like content (HTML tags, JSON, API responses)
    match = re.search(r"`([^`]+)`", text)
    if match:
        content = _clean_ui_text(match.group(1))
        # Skip code-like content: HTML tags, JSON objects, template expressions
        if not re.search(r"<\w+|{.*}|\$\{|\\n", content):
            if re.search(r"[一-鿿]", content):
                return f"text={content}"
            # Short English identifiers could be element names
            if len(content) <= 30 and re.match(r"^[a-zA-Z0-9_-]+$", content):
                return f"[data-testid={content.lower()}]"
    # Try Chinese brackets
    match = re.search(r"「([^」]+)」", text)
    if match:
        content = _clean_ui_text(match.group(1))
        if re.search(r"[一-鿿]", content):
            return f"text={content}"
        return content
    # Fallback: extract Chinese button/link text after click/fill keywords
    # First try: quoted text after click keyword (most specific)
    quoted_btn = re.search(r'(?:点击|click|按下|请求)\s*[\'""「]([^\']+?)[\'""」]', text, re.IGNORECASE)
    if quoted_btn:
        btn_text = _clean_ui_text(quoted_btn.group(1))
        if btn_text and re.search(r"[一-鿿]", btn_text):
            return f"text={btn_text}"
    # Second try: text before "按钮" keyword
    btn_match = re.search(r'(?:点击|click|按下|请求)\s*[\'""「]*([^\']*?)[\'""」]*\s*按钮', text, re.IGNORECASE)
    if btn_match:
        btn_text = _clean_ui_text(btn_match.group(1))
        if btn_text and re.search(r"[一-鿿]", btn_text):
            return f"text={btn_text}"
    # Fallback: extract element name from "在 X 输入/填写" patterns
    elem_match = re.search(r"在\s+([\w一-鿿]+)\s+(?:输入|填写|键入)", text)
    if elem_match:
        elem_name = elem_match.group(1).strip()
        if elem_name and re.search(r"[一-鿿]", elem_name):
            return f"text={elem_name}"
        if elem_name:
            return f"[data-testid={elem_name.lower()}]"
    return None


def _extract_fill_value(action_text: str) -> str | None:
    """Extract quoted value from a fill/type action text."""
    # Match "value", 'value', or “value” (Chinese quotes)
    patterns = [
        r'"([^"]+)"',
        r"'([^']+)'",
        r'“([^”]+)”',
    ]
    for pat in patterns:
        match = re.search(pat, action_text)
        if match:
            val = match.group(1).strip()
            if val:
                return val
    # Fallback: extract parenthesized content like "(empty payload / large text / injection like <script)"
    paren_match = re.search(r"[(（]([^\)）]+)[)）]", action_text)
    if paren_match:
        val = paren_match.group(1).strip()
        if val:
            return val
    return None


def _normalize_action(action_text: str) -> tuple[str, str | None]:
    """Map natural language action to Playwright action keyword and optional selector.

    Returns:
        (playwright_action, selector_or_none)
    """
    text = action_text.strip()

    # Passive observation steps
    if re.search(r"(?:passive|observing|waiting|awaiting)", text, re.IGNORECASE):
        return "screenshot", None

    # System/backend behavior (non-user action) -> convert to assertion or screenshot
    if re.search(r"^(?:LLM|系统|页面|服务端|server|backend|API|SSE)", text, re.IGNORECASE):
        selector = _extract_selectors_from_text(text)
        if re.search(r"(?:显示|可见|appear|render|show)", text, re.IGNORECASE):
            return "assert_visible", selector
        if re.search(r"(?:错误|error|fail)", text, re.IGNORECASE):
            return "assert_visible", selector
        return "screenshot", selector

    # Special handling for "OR" cases - pick the most actionable one
    if re.search(r"\s+OR\s+|\s+或\s+", text, re.IGNORECASE):
        # Prefer click over fill for FAB-style actions
        if re.search(r"(?:click|点击|FAB|button|按钮)", text, re.IGNORECASE):
            selector = _extract_selectors_from_text(text)
            return "click", selector

    for pattern, action in _ACTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            selector = _extract_selectors_from_text(text)
            return action, selector

    # Default fallback: screenshot to capture state
    return "screenshot", None


def _extract_afc_assertions(afcs_text: str) -> list[dict[str, Any]]:
    """Extract Playwright assertions from anti-false-pass checks."""
    assertions: list[dict[str, Any]] = []
    locator_pattern = re.compile(r"page\.locator\(['\"](.+?)['\"]\)")
    expect_pattern = re.compile(
        r"expect\((.+?)\)\.(toBeVisible|toBeHidden|toContainText|toBeEnabled|toHaveCount|toHaveTitle|not\.toBeVisible|not\.toBeHidden)\((.*?)\)"
    )

    for line in afcs_text.split("\n"):
        line = line.strip()
        locators = locator_pattern.findall(line)
        expects = expect_pattern.findall(line)
        if locators or expects:
            assertions.append({
                "selector": locators[0] if locators else "",
                "assertion": expects[0][1] if expects else "toBeVisible",
                "args": expects[0][2] if expects else "",
                "raw": line,
            })
    return assertions


# ---------------------------------------------------------------------------
# API spec parsing (ADR-054 §2.2.2)
# ---------------------------------------------------------------------------


def spec_parse_api_spec(spec_path: Path) -> dict[str, Any]:
    """Parse a single api-test-spec/*.md file into a TESTSET unit dict.

    Args:
        spec_path: Path to the api-test-spec markdown file

    Returns:
        Dict with TESTSET unit fields plus _source_coverage_id and _api_extension
    """
    content = spec_path.read_text(encoding="utf-8")
    sections = _split_sections(content)

    # Parse case metadata table
    metadata: dict[str, str] = {}
    if "Case Metadata" in sections:
        metadata = _parse_table_rows(sections["Case Metadata"])

    # Parse request body if present
    request_body: dict[str, Any] = {}
    if "Request" in sections:
        request_text = _extract_code_block(sections["Request"])
        try:
            # Try to parse as JSON
            request_body = yaml.safe_load(request_text) or {}
        except yaml.YAMLError:
            pass

    # Parse assertions
    pass_conditions: list[str] = []
    fail_conditions: list[str] = []

    for section_key in ["Response Assertions", "Side Effect Assertions"]:
        if section_key in sections:
            for line in sections[section_key].split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    assertion = line.lstrip("- ").strip()
                    if assertion.startswith("!"):
                        fail_conditions.append(assertion.lstrip("! "))
                    else:
                        pass_conditions.append(assertion)

    # Build unit_ref from case_id
    case_id = metadata.get("case_id", spec_path.stem)

    # Build title from capability + scenario_type
    capability = metadata.get("capability", "")
    scenario_type = metadata.get("scenario_type", "")
    title = f"{capability}: {scenario_type}" if capability and scenario_type else metadata.get("coverage_id", case_id)

    # Extract endpoint from Request section
    endpoint_match = re.search(r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/\S+)", sections.get("Request", ""))
    if not endpoint_match:
        endpoint_match = re.search(r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/\S+)", content)
    if endpoint_match:
        method = endpoint_match.group(1)
        path = endpoint_match.group(2)
        trigger_action = f"{method} {path}"
    else:
        trigger_action = metadata.get("endpoint", metadata.get("coverage_id", ""))

    unit: dict[str, Any] = {
        "unit_ref": case_id,
        "title": title,
        "trigger_action": trigger_action,
        "pass_conditions": pass_conditions,
        "fail_conditions": fail_conditions,
        "preconditions": [s.strip() for s in sections.get("Preconditions", "").split("\n") if s.strip()],
        "test_data": request_body,
        "acceptance_ref": metadata.get("source_feat_ref", ""),
        "priority": metadata.get("priority", "P1"),
        "required_evidence": [e.strip() for e in metadata.get("Evidence Required", "").split("\n") if e.strip()],
        # Extension fields for traceability (ADR-054 §5.1 R-1, R-6)
        "_source_coverage_id": metadata.get("coverage_id", ""),
        "_api_extension": {
            "scenario_type": scenario_type,
            "dimension": metadata.get("dimension", ""),
            "coverage_id": metadata.get("coverage_id", ""),
            "capability": capability,
            "source_feat_ref": metadata.get("source_feat_ref", ""),
        },
    }

    return unit


# ---------------------------------------------------------------------------
# E2E spec parsing (ADR-054 §2.2.3)
# ---------------------------------------------------------------------------


def _build_login_steps(page_path: str) -> list[dict[str, Any]]:
    """Build login steps for protected pages.

    When the target page requires authentication (e.g., conversation page),
    inject steps to login via test account and dismiss onboarding dialog.
    """
    # Pages that require auth (everything except login/auth pages)
    protected_prefixes = ["/conversation", "/training-plan", "/feedback", "/onboarding", "/tool"]
    is_root_conversation = page_path in ("/", "/conversation-home")
    needs_auth = is_root_conversation or any(page_path.startswith(p) for p in protected_prefixes)
    if not needs_auth:
        return []

    return [
        # Step 1: Click test account to login
        {
            "action": "click",
            "selector": "text=dev_user_001",
            "target": "text=dev_user_001",
            "raw_action": "auto-login: click test account dev_user_001",
        },
        # Step 2: Wait for redirect
        {
            "action": "screenshot",
            "raw_action": "auto-login: wait for redirect after login",
        },
        # Step 3: Force-dismiss onboarding dialog overlay via JS
        {
            "action": "evaluate",
            "value": "document.querySelectorAll('.dialog-overlay').forEach(el => el.style.display = 'none')",
            "raw_action": "auto-login: dismiss onboarding dialog overlay",
        },
    ]


def spec_parse_e2e_spec(spec_path: Path) -> dict[str, Any]:
    """Parse a single e2e-journey-spec/*.md file into a TESTSET unit dict.

    Args:
        spec_path: Path to the e2e-journey-spec markdown file

    Returns:
        Dict with TESTSET unit fields plus _source_coverage_id and _e2e_extension
    """
    content = spec_path.read_text(encoding="utf-8")
    sections = _split_sections(content)

    # Parse YAML frontmatter (canonical spec format)
    frontmatter = _parse_yaml_frontmatter(content)

    # Parse case metadata table (fallback for legacy format)
    metadata: dict[str, str] = {}
    case_metadata_text = _find_section_fuzzy(_SECTION_MAP["case_metadata"], sections)
    if case_metadata_text:
        metadata = _parse_table_rows(case_metadata_text)

    # Merge frontmatter into metadata (frontmatter takes precedence)
    for key, value in frontmatter.items():
        if value is not None:
            metadata[key] = str(value)

    # Parse entry_point for page_path
    entry_point_text = _find_section_fuzzy(_SECTION_MAP["entry_point"], sections)
    page_path = metadata.get("entry_point", "")
    if entry_point_text and not page_path:
        page_path = (
            _extract_table_field(entry_point_text, "URL/Page")
            or _extract_table_field(entry_point_text, "Page / URL")
            or _extract_table_field(entry_point_text, "URL")
            or _extract_table_field(entry_point_text, "Page")
        )

    # Clean page_path: extract only the path portion (remove markdown backticks and descriptions)
    if page_path:
        # Extract content inside backticks if present
        backtick_match = re.search(r"`([^`]+)`", page_path)
        if backtick_match:
            page_path = backtick_match.group(1).strip()
        # Take only the first word (the actual path), drop trailing descriptions
        page_path = page_path.split()[0].strip()

    # Parse user steps (three-format support)
    user_steps_text = _find_section_fuzzy(_SECTION_MAP["user_steps"], sections)
    raw_steps = _parse_user_steps(user_steps_text)

    # Fallback: _split_sections may have split ### Step N: into separate sections.
    # Collect User Action from any standalone Step N sections.
    if not raw_steps:
        for section_key, section_content in sorted(sections.items()):
            if re.match(r"Step\s*\d+[A-Z]?:", section_key, re.IGNORECASE):
                action = _extract_table_field(section_content, "User Action")
                if action:
                    raw_steps.append({"raw_action": action})

    # Normalize actions and extract selectors
    user_steps: list[dict[str, Any]] = []
    selectors: dict[str, str] = {}

    for i, raw_step in enumerate(raw_steps):
        action_text = raw_step["raw_action"]
        normalized_action, selector = _normalize_action(action_text)

        step_dict: dict[str, Any] = {
            "action": normalized_action,
            "raw_action": action_text,
        }
        if selector:
            step_dict["target"] = selector
            step_dict["selector"] = selector
            selectors[f"step_{i + 1}"] = selector

        # Extract fill value for fill/type actions
        if normalized_action in ("fill", "type"):
            value = _extract_fill_value(action_text)
            if value:
                step_dict["value"] = value

        user_steps.append(step_dict)

    # Parse expected UI states as pass_conditions
    pass_conditions: list[str] = []
    expected_ui_states_text = _find_section_fuzzy(_SECTION_MAP["expected_ui_states"], sections)
    if expected_ui_states_text:
        for line in expected_ui_states_text.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                pass_conditions.append(line.lstrip("-* ").strip())

    # Parse expected network events
    required_evidence = [e.strip() for e in metadata.get("Evidence Required", "").split("\n") if e.strip()]
    expected_network_events_text = _find_section_fuzzy(_SECTION_MAP["expected_network_events"], sections)
    if expected_network_events_text:
        for line in expected_network_events_text.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                required_evidence.append(f"network_log: {line.lstrip('- ')}")

    # Parse expected persistence as pass_conditions
    expected_persistence_text = _find_section_fuzzy(_SECTION_MAP["expected_persistence"], sections)
    if expected_persistence_text:
        for line in expected_persistence_text.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                pass_conditions.append(line.lstrip("-* ").strip())

    # Parse anti-false-pass checks
    fail_conditions: list[str] = []
    anti_false_pass_text = _find_section_fuzzy(_SECTION_MAP["anti_false_pass_checks"], sections)
    if anti_false_pass_text:
        # Add raw AFC lines as fail_conditions (textual)
        for line in anti_false_pass_text.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                fail_conditions.append(line.lstrip("-* ").strip())

        # Extract structured assertions from AFC and add as ui_steps
        af_assertions = _extract_afc_assertions(anti_false_pass_text)
        action_map = {
            "toBeVisible": "assert_visible",
            "toBeHidden": "assert_hidden",
            "toContainText": "assert_text",
            "toBeEnabled": "assert_visible",
            "toHaveCount": "assert_visible",
            "toHaveTitle": "assert_title",
            "not.toBeVisible": "assert_hidden",
            "not.toBeHidden": "assert_visible",
        }
        for afc in af_assertions:
            action = action_map.get(afc["assertion"], "assert_visible")
            step_dict = {
                "action": action,
                "selector": afc["selector"],
                "target": afc["selector"],
                "raw_action": afc["raw"],
                "source": "afc",
            }
            user_steps.append(step_dict)
            if afc["selector"]:
                selectors[f"afc_{afc['selector']}"] = afc["selector"]

    # Build ui_steps list as dicts with selector metadata for downstream binding
    ui_steps: list[dict[str, Any] | str] = []
    for step in user_steps:
        step_meta: dict[str, Any] = {"action": step["action"]}
        if "selector" in step:
            step_meta["selector"] = step["selector"]
        if "target" in step:
            step_meta["target"] = step["target"]
        if "value" in step:
            step_meta["value"] = step["value"]
        if "text" in step:
            step_meta["text"] = step["text"]
        ui_steps.append(step_meta)

    # Build _e2e_extension with ui_step_metadata
    ui_step_metadata: list[dict[str, Any]] = []
    for step in user_steps:
        meta: dict[str, Any] = {"action": step["action"]}
        if "target" in step:
            meta["target"] = step["target"]
        if "selector" in step:
            meta["selector"] = step["selector"]
        if "type" in step:
            meta["type"] = step["type"]
        if "timeout" in step:
            meta["timeout"] = step["timeout"]
        if "raw_action" in step:
            meta["raw_action"] = step["raw_action"]
        if "source" in step:
            meta["source"] = step["source"]
        if "value" in step:
            meta["value"] = step["value"]
        ui_step_metadata.append(meta)

    # Inject login steps if the target page requires authentication
    # (detected by page_path pointing to a protected route like /conversation-home or /)
    if page_path and ui_steps:
        login_steps = _build_login_steps(page_path)
        if login_steps:
            # After login, we're already on the conversation page — skip any initial goto step
            filtered_steps = []
            for i, step in enumerate(ui_steps):
                if step.get("action") in ("goto", "visit", "open") and i == 0 and not filtered_steps:
                    continue  # Skip goto after login — we're already on the target page
                filtered_steps.append(step)
            ui_steps = login_steps + filtered_steps
            # Rebuild ui_step_metadata with login steps
            login_meta = [{"action": s["action"], "selector": s.get("selector", ""), "raw_action": s.get("raw_action", "auto-login"), "source": "auto_login"} for s in login_steps]
            ui_step_metadata = login_meta + [m for i, m in enumerate(ui_step_metadata) if not (m.get("action") in ("goto", "visit", "open") and i == 0)]

    # Inject plan proposal form filling steps for SRC-006 style tests
    # (detected by any step containing "生成计划" or "去创建")
    has_plan_generation_step = any(
        "生成计划" in (step.get("raw_action", "") or "") or
        "去创建" in (step.get("selector", "") or "") or
        "去创建" in (step.get("target", "") or "")
        for step in ui_steps
    )
    if has_plan_generation_step:
        # Find the position where we need to inject the form filling steps
        # (right after the "去创建" / "生成计划" click)
        inject_position = len(ui_steps)  # Default to end
        for i, step in enumerate(ui_steps):
            selector_text = step.get("selector", "") or step.get("target", "") or ""
            raw_action = step.get("raw_action", "") or ""
            if "去创建" in selector_text or "生成计划" in raw_action or "去创建" in raw_action:
                inject_position = i + 1
                break

        # Build plan proposal form filling steps using the test hooks
        plan_form_steps = [
            # Wait a bit for dialog to open
            {
                "action": "screenshot",
                "raw_action": "wait for plan proposal dialog to open",
                "source": "auto_plan_form",
            },
            # Use test hook to set plan form data
            {
                "action": "evaluate",
                "value": """window.__CONVERSATION_TEST_HOOK__.setPlanForm({
                    plan_type: 'half_marathon',
                    goal_sub_type: 'finish',
                    goal_target_time: '',
                    target_date: '2025-06-01',
                    start_date: '',
                    weekly_frequency: '4'
                })""",
                "raw_action": "auto-fill plan form using test hook",
                "source": "auto_plan_form",
            },
            # Wait a bit
            {
                "action": "screenshot",
                "raw_action": "after setting plan form data",
                "source": "auto_plan_form",
            },
            # Use test hook to submit the form
            {
                "action": "evaluate",
                "value": "window.__CONVERSATION_TEST_HOOK__.submitPlanProposal()",
                "raw_action": "submit plan proposal form using test hook",
                "source": "auto_plan_form",
            },
        ]

        # Inject the form steps at the right position
        ui_steps = ui_steps[:inject_position] + plan_form_steps + ui_steps[inject_position:]

        # Also update ui_step_metadata
        plan_form_meta = [{"action": s["action"], "value": s.get("value", ""), "raw_action": s.get("raw_action", "auto-plan-form"), "source": "auto_plan_form"} for s in plan_form_steps]
        ui_step_metadata = ui_step_metadata[:inject_position] + plan_form_meta + ui_step_metadata[inject_position:]

    unit: dict[str, Any] = {
        "unit_ref": metadata.get("spec_id", metadata.get("case_id", spec_path.stem)),
        "title": metadata.get("title", metadata.get("journey_id", spec_path.stem)),
        "priority": metadata.get("priority", "P1"),
        "page_path": page_path,
        "ui_steps": ui_steps,
        "selectors": selectors,
        "pass_conditions": pass_conditions,
        "fail_conditions": fail_conditions,
        "required_evidence": required_evidence,
        "acceptance_ref": metadata.get("coverage_id_ref", metadata.get("coverage_id", "")),
        "supporting_refs": [r.strip() for r in metadata.get("source_prototype_ref", "").split("\n") if r.strip()],
        # Extension fields for traceability (ADR-054 §5.1 R-1, R-8)
        "_source_coverage_id": metadata.get("coverage_id", metadata.get("coverage_id_ref", "")),
        "_e2e_extension": {
            "ui_step_metadata": ui_step_metadata,
            "expected_persistence": [p for p in pass_conditions if "persistence" in p.lower()],
            "scenario_type": metadata.get("journey_type", metadata.get("journey_type", "main")),
        },
    }

    return unit


# ---------------------------------------------------------------------------
# Main conversion function
# ---------------------------------------------------------------------------


def spec_to_testset(workspace_root: Path, input: SpecAdapterInput) -> dict[str, Any]:
    """Convert spec files to SPEC_ADAPTER_COMPAT format.

    Args:
        workspace_root: Root of the workspace for path resolution
        input: SpecAdapterInput containing spec files and metadata

    Returns:
        dict with ssot_type=SPEC_ADAPTER_COMPAT and test_units list

    Raises:
        ValueError: If no spec files provided or modality invalid
    """
    if not input.spec_files:
        raise ValueError("spec_files must not be empty")

    test_units: list[dict[str, Any]] = []

    for spec_path in input.spec_files:
        spec_path = Path(spec_path)
        if not spec_path.is_absolute():
            spec_path = workspace_root / spec_path

        if not spec_path.exists():
            raise ValueError(f"Spec file not found: {spec_path}")

        if input.modality == "api":
            unit = spec_parse_api_spec(spec_path)
            test_units.append(unit)
        elif input.modality in ("web_e2e", "cli"):
            unit = spec_parse_e2e_spec(spec_path)
            test_units.append(unit)
        else:
            raise ValueError(f"Invalid modality: {input.modality}. Must be 'api', 'web_e2e', or 'cli'.")

    # Build SPEC_ADAPTER_COMPAT document
    feat_ref = input.feat_ref or ""
    proto_ref = input.proto_ref or ""

    # Determine test_set_id
    if feat_ref:
        test_set_id = f"spec-adapter-{feat_ref}"
    elif proto_ref:
        test_set_id = f"spec-adapter-{proto_ref}"
    else:
        test_set_id = "spec-adapter-unknown"

    result: dict[str, Any] = {
        "ssot_type": "SPEC_ADAPTER_COMPAT",
        "test_set_id": test_set_id,
        "feat_ref": feat_ref if input.modality == "api" else None,
        "prototype_ref": proto_ref if input.modality in ("web_e2e", "cli") else None,
        "execution_modality": input.modality,
        "source_chain": "api" if input.modality == "api" else "spec_e2e",
        "test_units": test_units,
    }

    # Remove None values for cleanliness
    result = {k: v for k, v in result.items() if v is not None and v != ""}

    return result


def write_spec_adapter_output(workspace_root: Path, output: dict[str, Any], output_name: str) -> Path:
    """Write SPEC_ADAPTER_COMPAT dict to a YAML file.

    Args:
        workspace_root: Root of the workspace
        output: The SPEC_ADAPTER_COMPAT dict
        output_name: Name for the output file (without extension)

    Returns:
        Path to the written file
    """
    output_dir = workspace_root / "ssot" / "tests" / ".spec-adapter"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{output_name}.yaml"
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(output, f, allow_unicode=True, sort_keys=False)

    return output_path
