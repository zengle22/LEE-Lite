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
    """Split markdown content into sections by ## headings."""
    sections: dict[str, str] = {}
    current_heading = "_preamble"
    current_content: list[str] = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_content:
                sections[current_heading] = "\n".join(current_content).strip()
            m = re.match(r"##\s+(.+)", line)
            current_heading = m.group(1) if m else "_other"
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_heading] = "\n".join(current_content).strip()

    return sections


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
    endpoint_match = re.search(r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\\s+(/\\S+)", sections.get("Request", ""))
    if not endpoint_match:
        endpoint_match = re.search(r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\\s+(/\\S+)", content)
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


def spec_parse_e2e_spec(spec_path: Path) -> dict[str, Any]:
    """Parse a single e2e-journey-spec/*.md file into a TESTSET unit dict.

    Args:
        spec_path: Path to the e2e-journey-spec markdown file

    Returns:
        Dict with TESTSET unit fields plus _source_coverage_id and _e2e_extension
    """
    content = spec_path.read_text(encoding="utf-8")
    sections = _split_sections(content)

    # Parse case metadata table
    metadata: dict[str, str] = {}
    if "Case Metadata" in sections:
        metadata = _parse_table_rows(sections["Case Metadata"])

    # Parse user steps
    user_steps_text = sections.get("User Steps", "")
    user_steps: list[dict[str, Any]] = []
    selectors: dict[str, str] = {}

    # Parse numbered user steps
    step_pattern = re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE)
    for i, match in enumerate(step_pattern.finditer(user_steps_text)):
        step_text = match.group(1)
        # Try to extract action and target
        step_parts = re.split(r"\s+(?:->|→)\s+", step_text)
        action = step_parts[0].strip() if step_parts else f"step_{i + 1}"
        target = step_parts[1].strip() if len(step_parts) > 1 else ""

        step_dict: dict[str, Any] = {"action": action}
        if target:
            step_dict["target"] = target
            resolved = _resolve_selector(action, step_dict)
            if resolved:
                selectors[action] = resolved

        user_steps.append(step_dict)

    # Parse expected UI states as pass_conditions
    pass_conditions: list[str] = []
    if "Expected UI States" in sections:
        for line in sections["Expected UI States"].split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                pass_conditions.append(line.lstrip("-* ").strip())

    # Parse expected network events
    required_evidence = [e.strip() for e in metadata.get("Evidence Required", "").split("\n") if e.strip()]
    if "Expected Network Events" in sections:
        for line in sections["Expected Network Events"].split("\n"):
            line = line.strip()
            if line.startswith("-"):
                required_evidence.append(f"network_log: {line.lstrip('- ')}")

    # Parse expected persistence as pass_conditions
    if "Expected Persistence" in sections:
        for line in sections["Expected Persistence"].split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                pass_conditions.append(line.lstrip("-* ").strip())

    # Parse anti-false-pass checks as fail_conditions
    fail_conditions: list[str] = []
    if "Anti-False-Pass Checks" in sections:
        for line in sections["Anti-False-Pass Checks"].split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                fail_conditions.append(line.lstrip("-* ").strip())

    # Build ui_steps list (action names only)
    ui_steps = [s["action"] for s in user_steps]

    # Build _e2e_extension with ui_step_metadata
    ui_step_metadata: list[dict[str, Any]] = []
    for step in user_steps:
        meta: dict[str, Any] = {"action": step["action"]}
        if "target" in step:
            meta["target"] = step["target"]
        if "type" in step:
            meta["type"] = step["type"]
        if "timeout" in step:
            meta["timeout"] = step["timeout"]
        ui_step_metadata.append(meta)

    unit: dict[str, Any] = {
        "unit_ref": metadata.get("spec_id", metadata.get("case_id", spec_path.stem)),
        "title": metadata.get("title", metadata.get("journey_id", spec_path.stem)),
        "priority": metadata.get("priority", "P1"),
        "page_path": metadata.get("entry_point", ""),
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
            "scenario_type": metadata.get("journey_type", "main"),
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
