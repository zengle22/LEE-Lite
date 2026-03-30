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
from raw_to_src_high_fidelity import (
    enrich_governance_bridge_candidate,
    enrich_high_fidelity_candidate,
    structural_check,
)
from raw_to_src_render import render_candidate_markdown


WORKFLOW_KEY = "product.raw-to-src"
VALID_INPUT_TYPES = {
    "adr",
    "raw_requirement",
    "business_opportunity",
    "business_opportunity_freeze",
}
FORBIDDEN_STATUSES = {"frozen", "active", "deprecated"}
FORBIDDEN_MARKERS = {"gate-materialize", "gate_materialize"}
SEMANTIC_LOCK_REQUIRED_FIELDS = (
    "domain_type",
    "one_sentence_truth",
    "primary_object",
    "lifecycle_stage",
    "inheritance_rule",
)
REQUIRED_CANDIDATE_SECTIONS = [
    "问题陈述",
    "目标用户",
    "触发场景",
    "业务动因",
    "语义清单",
    "标准化决策",
    "压缩与省略说明",
    "用户入口与控制面",
    "冻结输入与需求源快照",
    "文档语义层级",
    "Frozen Contracts",
    "结构化对象契约",
    "枚举冻结",
    "关键约束",
    "范围边界",
    "内嵌需求源快照",
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


def unique_dicts(items: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for item in items:
        key = tuple(str(item.get(field, "")).strip().casefold() for field in key_fields)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def normalize_semantic_lock(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    normalized = {
        "domain_type": normalize_title(value.get("domain_type"), ""),
        "one_sentence_truth": normalize_title(value.get("one_sentence_truth"), ""),
        "primary_object": normalize_title(value.get("primary_object"), ""),
        "lifecycle_stage": normalize_title(value.get("lifecycle_stage"), ""),
        "allowed_capabilities": normalize_list(value.get("allowed_capabilities")),
        "forbidden_capabilities": normalize_list(value.get("forbidden_capabilities")),
        "inheritance_rule": normalize_title(value.get("inheritance_rule"), ""),
    }
    if not any(normalized.values()):
        return None
    return normalized


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


def build_source_snapshot(document: dict[str, Any]) -> dict[str, Any]:
    source_path = str(document.get("path", ""))
    sections = deepcopy(document.get("sections") or {})
    capture_metadata = {
        "captured_at": iso_now(),
        "captured_by": WORKFLOW_KEY,
        "capture_mode": "normalized_source_snapshot",
        "source_path": source_path,
        "frozen_ref": "",
        "frozen_snapshot_ref": "",
        "content_hash": "",
        "content_hash_algo": "sha256",
        "source_size_bytes": None,
        "source_suffix": Path(source_path).suffix.lower() if source_path else "",
    }
    return {
        "title": str(document.get("title", "")).strip(),
        "input_type": str(document.get("input_type", "")).strip(),
        "body": str(document.get("body", "")),
        "sections": sections,
        "source_refs": deepcopy(document.get("source_refs") or []),
        "source_path": source_path,
        "capture_metadata": capture_metadata,
    }


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
        "sections": sections,
        "path": str(path),
        "semantic_lock": normalize_semantic_lock(
            metadata.get("semantic_lock")
            or find_nested(payload, "semantic_lock", "bridge_context.semantic_lock", "business_output.semantic_lock")
        ),
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
        "key_constraints": normalize_list(metadata.get("constraints")) or normalize_list(find_nested(payload, "constraints", "key_designs.risks_and_boundaries.dependencies", "business_output.key_designs.risks_and_boundaries.dependencies")) or normalize_list(sections.get("关键约束")),
        "non_goals": normalize_list(metadata.get("non_goals")) or normalize_list(find_nested(payload, "non_goals", "key_designs.risks_and_boundaries.out_of_scope", "business_output.key_designs.risks_and_boundaries.out_of_scope")) or normalize_list(sections.get("非目标")),
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
    semantic_lock = document.get("semantic_lock")
    if semantic_lock:
        missing_fields = [field for field in SEMANTIC_LOCK_REQUIRED_FIELDS if not semantic_lock.get(field)]
        if missing_fields:
            issues.append(
                {
                    "code": "semantic_lock_incomplete",
                    "severity": "error",
                    "message": f"semantic_lock is missing required fields: {', '.join(missing_fields)}",
                }
            )
        if not semantic_lock.get("allowed_capabilities"):
            issues.append(
                {
                    "code": "semantic_lock_missing_allowed_capabilities",
                    "severity": "error",
                    "message": "semantic_lock must declare allowed_capabilities.",
                }
            )
        if not semantic_lock.get("forbidden_capabilities"):
            issues.append(
                {
                    "code": "semantic_lock_missing_forbidden_capabilities",
                    "severity": "error",
                    "message": "semantic_lock must declare forbidden_capabilities.",
                }
            )
    return issues, {"valid": not any(item["severity"] == "error" for item in issues), "issue_count": len(issues), "issues": issues}


def normalize_candidate(document: dict[str, Any]) -> dict[str, Any]:
    candidate = {
        "artifact_type": "src_candidate",
        "workflow_key": WORKFLOW_KEY,
        "workflow_run_id": "",
        "title": document["title"],
        "status": "needs_review",
        "input_type": document["input_type"],
        "semantic_lock": deepcopy(document.get("semantic_lock")),
        "problem_statement": document["problem_statement"] or first_paragraph(document["body"]),
        "target_users": deepcopy(document["target_users"]),
        "trigger_scenarios": deepcopy(document["trigger_scenarios"]),
        "business_drivers": deepcopy(document["business_drivers"]),
        "key_constraints": deepcopy(document["key_constraints"]),
        "target_capability_objects": normalize_list(document.get("metadata", {}).get("target_capability_objects")) or normalize_list(heading_sections(document["body"]).get("目标能力对象")),
        "expected_outcomes": normalize_list(document.get("metadata", {}).get("expected_outcomes")) or normalize_list(heading_sections(document["body"]).get("成功结果")),
        "downstream_derivation_requirements": normalize_list(document.get("metadata", {}).get("downstream_derivation_requirements")) or normalize_list(heading_sections(document["body"]).get("下游派生要求")),
        "bridge_summary": normalize_list(document.get("metadata", {}).get("bridge_summary")) or normalize_list(heading_sections(document["body"]).get("桥接摘要")),
        "facet_inference": [],
        "facet_bundle_recommendation": [],
        "selected_facets": [],
        "projector_selection": None,
        "source_snapshot": build_source_snapshot(document),
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
        candidate = enrich_governance_bridge_candidate(candidate)
    return enrich_high_fidelity_candidate(candidate, document)

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
    if "missing_semantic_inventory" in codes and "semantic_inventory" not in working:
        working["semantic_inventory"] = {"actors": [], "product_surfaces": [], "operator_surfaces": [], "entry_points": [], "commands": [], "runtime_objects": [], "states": [], "observability_surfaces": [], "constraints": [], "non_goals": []}
        applied.append({"code": "missing_semantic_inventory", "action": "Filled empty semantic inventory.", "target_fields": ["semantic_inventory"]})
    if "missing_source_provenance_map" in codes and "source_provenance_map" not in working:
        working["source_provenance_map"] = []
        applied.append({"code": "missing_source_provenance_map", "action": "Filled empty source provenance map.", "target_fields": ["source_provenance_map"]})
    if "missing_normalization_decisions" in codes and "normalization_decisions" not in working:
        working["normalization_decisions"] = []
        applied.append({"code": "missing_normalization_decisions", "action": "Filled empty normalization decisions.", "target_fields": ["normalization_decisions"]})
    if "missing_omission_and_compression_report" in codes and "omission_and_compression_report" not in working:
        working["omission_and_compression_report"] = {"omitted_items": [], "compressed_items": [], "summary": ""}
        applied.append({"code": "missing_omission_and_compression_report", "action": "Filled empty omission/compression report.", "target_fields": ["omission_and_compression_report"]})
    if "missing_operator_surface_inventory" in codes and "operator_surface_inventory" not in working:
        working["operator_surface_inventory"] = []
        applied.append({"code": "missing_operator_surface_inventory", "action": "Filled empty operator surface inventory.", "target_fields": ["operator_surface_inventory"]})
    if "missing_contradiction_register" in codes and "contradiction_register" not in working:
        working["contradiction_register"] = []
        applied.append({"code": "missing_contradiction_register", "action": "Filled empty contradiction register.", "target_fields": ["contradiction_register"]})
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


def validate_candidate_markdown(path: Path) -> tuple[list[str], dict[str, Any]]:
    frontmatter, body = parse_frontmatter(read_text(path))
    sections = heading_sections(body)
    errors: list[str] = []
    required_fields = ["artifact_type", "workflow_key", "workflow_run_id", "title", "status", "source_kind", "source_refs", "source_snapshot_mode"]
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
        for section in ["目标能力对象", "成功结果", "下游派生要求", "桥接摘要"]:
            if not sections.get(section):
                errors.append(f"Missing section: {section}")
        if not sections.get("Bridge Context"):
            errors.append("Missing section: Bridge Context")
    for section in ["语义清单", "标准化决策", "压缩与省略说明", "Operator Surface Inventory", "用户入口与控制面", "冲突与未决点"]:
        if not sections.get(section):
            errors.append(f"Missing section: {section}")
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
