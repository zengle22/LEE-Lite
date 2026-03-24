#!/usr/bin/env python3
"""
Shared parsing, normalization, and validation helpers for raw-to-src.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from raw_to_src_bridge import synthesize_adr_bridge_candidate


WORKFLOW_KEY = "product.raw-to-src"
VALID_INPUT_TYPES = {
    "adr",
    "raw_requirement",
    "business_opportunity",
    "business_opportunity_freeze",
}
FORBIDDEN_STATUSES = {"frozen", "active", "deprecated"}
FORBIDDEN_MARKERS = {"gate-materialize", "gate_materialize"}
REQUIRED_CANDIDATE_SECTIONS = [
    "问题陈述",
    "目标用户",
    "触发场景",
    "业务动因",
    "关键约束",
    "范围边界",
    "来源追溯",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "src"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def safe_stem(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip() or "Untitled"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    frontmatter = yaml.safe_load(match.group(1)) or {}
    return frontmatter if isinstance(frontmatter, dict) else {}, match.group(2)


def heading_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        heading_match = re.match(r"^##\s+(.+?)\s*$", line)
        if heading_match:
            current = heading_match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [item.strip("- ").strip() for item in re.split(r"[\n,;]", value) if item.strip()]
        return [item for item in parts if item]
    if isinstance(value, list):
        items: list[str] = []
        for entry in value:
            items.extend(normalize_list(entry))
        return items
    return [str(value)]


def find_nested(payload: Any, *paths: str) -> Any:
    for path in paths:
        current = payload
        found = True
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
                continue
            found = False
            break
        if found and current not in (None, "", [], {}):
            return current
    return None


def first_paragraph(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return paragraphs[0] if paragraphs else ""


def extract_refs(text: str) -> list[str]:
    refs = re.findall(r"\bADR-\d+\b", text, flags=re.IGNORECASE)
    ordered: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        upper = ref.upper()
        if upper not in seen:
            seen.add(upper)
            ordered.append(upper)
    return ordered


def contains_marker(payload: Any, markers: set[str]) -> bool:
    if isinstance(payload, dict):
        return any(contains_marker(key, markers) or contains_marker(value, markers) for key, value in payload.items())
    if isinstance(payload, list):
        return any(contains_marker(item, markers) for item in payload)
    if isinstance(payload, str):
        return payload.strip().lower() in markers
    return False


def detect_input_type(metadata: dict[str, Any], payload: Any, title: str, refs: list[str]) -> str:
    raw = metadata.get("input_type") or metadata.get("type") or find_nested(payload, "input_type", "type")
    if isinstance(raw, str) and raw.strip().lower() in VALID_INPUT_TYPES:
        return raw.strip().lower()
    adr_refs = [
        str(ref).strip().upper()
        for ref in refs
        if isinstance(ref, str) and re.fullmatch(r"ADR-\d+", ref.strip(), flags=re.IGNORECASE)
    ]
    if adr_refs or re.search(r"\bADR-\d+\b", title, flags=re.IGNORECASE):
        return "adr"
    if find_nested(payload, "freeze_meta.status") == "frozen":
        return "business_opportunity_freeze"
    if find_nested(payload, "requirement_overview", "business_output.requirement_overview"):
        return "business_opportunity"
    return "raw_requirement"


def normalize_title(value: Any, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def build_structured_body(payload: Any) -> str:
    candidates = [
        find_nested(payload, "requirement_overview.description", "business_output.requirement_overview.description"),
        find_nested(payload, "description"),
        find_nested(payload, "context", "requirement_overview.context", "business_output.requirement_overview.context"),
    ]
    return "\n\n".join(str(item).strip() for item in candidates if isinstance(item, str) and item.strip())


def load_raw_input(path: Path) -> dict[str, Any]:
    text = read_text(path)
    metadata: dict[str, Any] = {}
    payload: Any = None
    body = text

    if path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(text) or {}
        body = ""
    elif path.suffix.lower() == ".json":
        payload = json.loads(text)
        body = ""
    elif path.suffix.lower() == ".md":
        metadata, body = parse_frontmatter(text)

    if isinstance(payload, dict) and not metadata:
        metadata = dict(payload)
    if isinstance(payload, dict) and not body:
        body = build_structured_body(payload)

    sections = heading_sections(body)
    title = normalize_title(
        metadata.get("title"),
        normalize_title(
            find_nested(payload, "title", "contract_info.title", "business_output.contract_info.title"),
            safe_stem(path),
        ),
    )
    source_refs = normalize_list(metadata.get("source_refs")) or normalize_list(
        find_nested(
            payload,
            "source_refs",
            "business_output.source_refs",
            "bridge_context.governed_by_adrs",
            "business_output.bridge_context.governed_by_adrs",
        )
    )
    for ref in extract_refs(f"{title}\n{body}\n{json.dumps(payload, ensure_ascii=False) if payload is not None else ''}"):
        if ref not in source_refs:
            source_refs.append(ref)
    if not source_refs:
        source_refs.append(path.name)

    return {
        "artifact_type": "raw-input",
        "input_type": detect_input_type(metadata, payload, title, source_refs),
        "title": title,
        "body": body,
        "source_refs": source_refs,
        "topics": normalize_list(metadata.get("topics")) or normalize_list(find_nested(payload, "topics", "problem_domains")),
        "metadata": metadata,
        "payload": payload,
        "path": str(path),
        "problem_statement": normalize_title(
            find_nested(
                payload,
                "problem_statement",
                "requirement_overview.description",
                "business_output.requirement_overview.description",
                "description",
            ),
            sections.get("问题陈述") or sections.get("Problem Statement") or first_paragraph(body),
        ),
        "target_users": normalize_list(find_nested(payload, "target_users", "requirement_overview.target_users", "business_output.requirement_overview.target_users")) or normalize_list(sections.get("目标用户")),
        "trigger_scenarios": normalize_list(find_nested(payload, "trigger_scenarios", "scenarios")) or normalize_list(sections.get("触发场景")),
        "business_drivers": normalize_list(find_nested(payload, "business_drivers", "key_designs.value_chain.direct_value.description", "business_output.key_designs.value_chain.direct_value.description", "context", "requirement_overview.context", "business_output.requirement_overview.context")) or normalize_list(sections.get("业务动因")),
        "key_constraints": normalize_list(find_nested(payload, "constraints", "key_designs.risks_and_boundaries.dependencies", "business_output.key_designs.risks_and_boundaries.dependencies")) or normalize_list(sections.get("关键约束")),
        "non_goals": normalize_list(find_nested(payload, "non_goals", "key_designs.risks_and_boundaries.out_of_scope", "business_output.key_designs.risks_and_boundaries.out_of_scope")) or normalize_list(sections.get("非目标")),
    }


def validate_input_document(document: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    issues: list[dict[str, str]] = []
    metadata = document.get("metadata") or {}
    payload = document.get("payload")
    status = metadata.get("status") or find_nested(payload, "status", "freeze_meta.status") or ""
    ssot_type = metadata.get("ssot_type") or find_nested(payload, "ssot_type")
    if ssot_type and str(status).strip().lower() in FORBIDDEN_STATUSES:
        issues.append({"code": "input_already_ssot", "severity": "error", "message": "Input already appears to be a governed SSOT object."})
    if contains_marker(metadata, FORBIDDEN_MARKERS) or contains_marker(payload, FORBIDDEN_MARKERS):
        issues.append({"code": "gate_materialize_placeholder", "severity": "error", "message": "Input contains a gate-materialize placeholder marker."})
    if document["input_type"] not in VALID_INPUT_TYPES:
        issues.append({"code": "unsupported_input_type", "severity": "error", "message": f"Unsupported input type: {document['input_type']}"})
    if len(document.get("topics", [])) > 1:
        issues.append({"code": "multi_topic_input_detected", "severity": "error", "message": "Input contains multiple explicit topics and should be split before SRC freeze."})
    if len(document["title"].strip()) < 3:
        issues.append({"code": "missing_title", "severity": "error", "message": "Input title is missing or too short."})
    if len(document["body"].strip()) < 10 and not document["problem_statement"]:
        issues.append({"code": "missing_body", "severity": "error", "message": "Input body is too short to normalize safely."})
    return issues, {"valid": not any(item["severity"] == "error" for item in issues), "issue_count": len(issues), "issues": issues}


def normalize_candidate(document: dict[str, Any]) -> dict[str, Any]:
    candidate = {
        "artifact_type": "src_candidate",
        "workflow_key": WORKFLOW_KEY,
        "workflow_run_id": "",
        "title": document["title"],
        "status": "needs_review",
        "input_type": document["input_type"],
        "problem_statement": document["problem_statement"] or first_paragraph(document["body"]),
        "target_users": deepcopy(document["target_users"]),
        "trigger_scenarios": deepcopy(document["trigger_scenarios"]),
        "business_drivers": deepcopy(document["business_drivers"]),
        "key_constraints": deepcopy(document["key_constraints"]),
        "in_scope": [f"围绕《{document['title']}》建立稳定、可追溯的需求源。"],
        "out_of_scope": deepcopy(document["non_goals"]),
        "source_refs": deepcopy(document["source_refs"]),
        "source_kind": document["input_type"],
        "bridge_context": None,
        "governance_change_summary": [],
        "uncertainties": [],
    }
    if not candidate["target_users"]:
        candidate["target_users"] = ["受该问题影响的业务角色"]
        candidate["uncertainties"].append("源输入未显式给出目标用户，已填入通用占位。")
    if not candidate["trigger_scenarios"]:
        candidate["trigger_scenarios"] = ["当原始问题被触发并需要正式需求源时。"]
        candidate["uncertainties"].append("源输入未显式给出触发场景，已生成保守场景。")
    if not candidate["business_drivers"]:
        candidate["business_drivers"] = ["将原始问题收敛为下游可复用的正式需求源。"]
    if not candidate["key_constraints"]:
        candidate["key_constraints"] = ["保持与原始输入同题，不扩展到 EPIC、FEAT、TASK 或实现设计。"]
    if not candidate["out_of_scope"]:
        candidate["out_of_scope"] = ["下游 EPIC/FEAT/TASK 分解与实现细节。"]
    if document["input_type"] == "adr":
        candidate["source_kind"] = "governance_bridge_src"
        candidate = synthesize_adr_bridge_candidate(candidate, document)
    return candidate


def structural_check(candidate: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not candidate["problem_statement"]:
        issues.append({"code": "missing_problem_statement", "severity": "error", "message": "Problem statement is required."})
    if not candidate["source_refs"]:
        issues.append({"code": "missing_source_refs", "severity": "error", "message": "Source refs are required."})
    if candidate["source_kind"] == "governance_bridge_src" and not candidate.get("bridge_context"):
        issues.append({"code": "missing_bridge_context", "severity": "error", "message": "ADR-derived candidate requires bridge context."})
    return issues


def apply_structural_patch(candidate: dict[str, Any], issues: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    working = deepcopy(candidate)
    applied: list[dict[str, Any]] = []
    codes = {item["code"] for item in issues}
    if "missing_bridge_context" in codes and working["source_kind"] == "governance_bridge_src":
        working["bridge_context"] = working.get("bridge_context") or {
            "governed_by_adrs": deepcopy(working["source_refs"]),
            "change_scope": working["problem_statement"],
            "governance_objects": deepcopy(working["key_constraints"]),
            "current_failure_modes": [working["problem_statement"]],
            "downstream_inheritance_requirements": deepcopy(working["key_constraints"]),
            "expected_downstream_objects": ["EPIC", "FEAT", "TASK"],
            "acceptance_impact": deepcopy(working["key_constraints"]),
            "non_goals": deepcopy(working["out_of_scope"]),
        }
        applied.append(
            {
                "code": "missing_bridge_context",
                "action": "Filled deterministic ADR bridge context.",
                "target_fields": ["bridge_context"],
            }
        )
    for key, default_value, code in [
        ("target_users", ["受该问题影响的业务角色"], "missing_target_users"),
        ("trigger_scenarios", ["当原始问题被触发并需要正式需求源时。"], "missing_trigger_scenarios"),
        ("business_drivers", ["将原始问题收敛为下游可复用的正式需求源。"], "missing_business_drivers"),
        ("key_constraints", ["保持与原始输入同题，不扩展到下游实现方案。"], "missing_key_constraints"),
        ("out_of_scope", ["下游分解与实现细节。"], "missing_out_of_scope"),
    ]:
        if not working[key]:
            working[key] = default_value
            applied.append(
                {
                    "code": code,
                    "action": f"Filled default value for {key}.",
                    "target_fields": [key],
                }
            )
    return working, applied


def parse_existing_src(path: Path) -> dict[str, Any]:
    frontmatter, _ = parse_frontmatter(read_text(path))
    return {"path": path, "title": frontmatter.get("title", path.stem), "slug": slugify(frontmatter.get("title", path.stem))}


def find_duplicate_src(repo_root: Path, title: str) -> Path | None:
    src_dir = repo_root / "ssot" / "src"
    if not src_dir.exists():
        return None
    slug = slugify(title)
    for path in sorted(src_dir.glob("SRC-*.md")):
        if parse_existing_src(path)["slug"] == slug:
            return path
    return None


def render_candidate_markdown(candidate: dict[str, Any]) -> str:
    def one_line(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value)).strip()

    frontmatter = {
        "artifact_type": "src_candidate",
        "workflow_key": WORKFLOW_KEY,
        "workflow_run_id": candidate["workflow_run_id"],
        "title": candidate["title"],
        "status": candidate["status"],
        "source_kind": candidate["source_kind"],
        "source_refs": candidate["source_refs"],
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    lines = ["---", header, "---", "", f"# {candidate['title']}", "", "## 问题陈述", "", one_line(candidate["problem_statement"]), "", "## 目标用户", ""]
    lines.extend(f"- {one_line(item)}" for item in candidate["target_users"])
    lines.extend(["", "## 触发场景", ""])
    lines.extend(f"- {one_line(item)}" for item in candidate["trigger_scenarios"])
    lines.extend(["", "## 业务动因", ""])
    lines.extend(f"- {one_line(item)}" for item in candidate["business_drivers"])
    if candidate["source_kind"] == "governance_bridge_src" and candidate.get("governance_change_summary"):
        lines.extend(["", "## 治理变更摘要", ""])
        lines.extend(f"- {one_line(item)}" for item in candidate["governance_change_summary"])
    lines.extend(["", "## 关键约束", ""])
    lines.extend(f"- {one_line(item)}" for item in candidate["key_constraints"])
    lines.extend(["", "## 范围边界", ""])
    lines.extend(f"- In scope: {one_line(item)}" for item in candidate["in_scope"])
    lines.extend(f"- Out of scope: {one_line(item)}" for item in candidate["out_of_scope"])
    lines.extend(["", "## 来源追溯", ""])
    lines.append(f"- Source refs: {', '.join(candidate['source_refs'])}")
    lines.append(f"- Input type: {candidate['input_type']}")
    if candidate["source_kind"] == "governance_bridge_src" and candidate.get("bridge_context"):
        bridge = candidate["bridge_context"]
        lines.extend(["", "## Bridge Context", ""])
        lines.append("- 结构化继承元数据区：本节仅用于机器消费与下游继承，不承担正文展开解释。")
        lines.append(f"- governed_by_adrs: {', '.join(bridge['governed_by_adrs'])}")
        lines.append(f"- change_scope: {one_line(bridge['change_scope'])}")
        lines.append(f"- governance_objects: {'; '.join(one_line(item) for item in bridge['governance_objects'])}")
        lines.append(f"- current_failure_modes: {'; '.join(one_line(item) for item in bridge['current_failure_modes'])}")
        lines.append(f"- downstream_inheritance_requirements: {'; '.join(one_line(item) for item in bridge['downstream_inheritance_requirements'])}")
        lines.append(f"- expected_downstream_objects: {', '.join(bridge['expected_downstream_objects'])}")
        lines.append(f"- acceptance_impact: {'; '.join(one_line(item) for item in bridge['acceptance_impact'])}")
        lines.append(f"- non_goals: {'; '.join(one_line(item) for item in bridge['non_goals'])}")
    return "\n".join(lines).rstrip() + "\n"


def validate_candidate_markdown(path: Path) -> tuple[list[str], dict[str, Any]]:
    frontmatter, body = parse_frontmatter(read_text(path))
    sections = heading_sections(body)
    errors: list[str] = []
    required_fields = ["artifact_type", "workflow_key", "workflow_run_id", "title", "status", "source_kind", "source_refs"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing frontmatter field: {field}")
    for section in REQUIRED_CANDIDATE_SECTIONS:
        if not sections.get(section):
            errors.append(f"Missing section: {section}")
    if frontmatter.get("artifact_type") != "src_candidate":
        errors.append("artifact_type must be src_candidate")
    if frontmatter.get("source_kind") == "governance_bridge_src":
        if not sections.get("治理变更摘要") and not sections.get("本次治理变化"):
            errors.append("Missing section: 治理变更摘要")
        if not sections.get("Bridge Context"):
            errors.append("Missing section: Bridge Context")
    result = {
        "valid": not errors,
        "artifact_type": frontmatter.get("artifact_type", ""),
        "workflow_key": frontmatter.get("workflow_key", ""),
        "workflow_run_id": frontmatter.get("workflow_run_id", ""),
        "title": frontmatter.get("title", ""),
        "status": frontmatter.get("status", ""),
        "source_kind": frontmatter.get("source_kind", ""),
        "source_refs": frontmatter.get("source_refs", []),
        "sections_present": sorted(sections.keys()),
        "errors": errors,
    }
    return errors, result
