#!/usr/bin/env python3
"""
Pre-SSOT FRZ compilation for raw-to-src.

FRZ (Freeze Package) is a governed, auditable intermediate artifact between RAW and SRC.
It does not live under ssot/; it lives under the workflow's artifacts directory.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


MSC_REQUIRED_DIMENSIONS = (
    "product_boundary",
    "core_journeys",
    "domain_model",
    "state_machine",
    "acceptance_contract",
)


def _is_effectively_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, dict):
        return all(_is_effectively_empty(item) for item in value.values())
    if isinstance(value, list):
        return all(_is_effectively_empty(item) for item in value)
    return False


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [item.strip("- ").strip() for item in re.split(r"[\n,;]", value) if item.strip()]
        return [item for item in parts if item]
    if isinstance(value, list):
        items: list[str] = []
        for entry in value:
            items.extend(_normalize_list(entry))
        return items
    return [str(value)]


def _safe_slug(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "frz"


def _extract_core_journeys(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    journeys: list[dict[str, Any]] = []
    trigger_scenarios = candidate.get("trigger_scenarios")
    if isinstance(trigger_scenarios, list) and any(str(item or "").strip() for item in trigger_scenarios):
        journeys.append(
            {
                "id": "JRN-001",
                "name": "Trigger Scenarios",
                "steps": [str(item).strip() for item in trigger_scenarios if str(item).strip()],
                "source": {"kind": "src_field", "ref": "trigger_scenarios"},
            }
        )
    snapshot = candidate.get("source_snapshot") or {}
    body = str(snapshot.get("body") or "")
    core_loop_match = re.search(r"核心闭环.*?\n\n(.+?)(\n## |\Z)", body, flags=re.DOTALL)
    if core_loop_match:
        excerpt = core_loop_match.group(1).strip()
        if excerpt:
            journeys.append(
                {
                    "id": "JRN-002",
                    "name": "Core Loop Excerpt",
                    "steps": [line.strip() for line in excerpt.splitlines() if line.strip()],
                    "source": {"kind": "raw_excerpt", "ref": "source_snapshot.body#core_loop"},
                }
            )
    return journeys


def _extract_state_machine_sections(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot = candidate.get("source_snapshot") or {}
    sections = snapshot.get("sections") if isinstance(snapshot.get("sections"), dict) else {}
    matches: list[dict[str, Any]] = []
    for key, value in sections.items():
        title = str(key or "").strip()
        if "状态机" in title or "state_machine" in title.lower():
            text = str(value or "").strip()
            if text:
                matches.append({"title": title, "content": text})
    return matches


def compute_msc_missing_dimensions(candidate: dict[str, Any]) -> list[str]:
    # MSC is a hard minimum for product-style sources (raw_requirement / opportunities).
    # For governance/ADR bridge SRCs, the required skeleton differs; do not block freeze-ready
    # routing on the product MSC set.
    if str(candidate.get("input_type") or "").strip().lower() == "adr":
        return []
    if str(candidate.get("source_kind") or "").strip().lower() == "governance_bridge_src":
        return []

    missing: list[str] = []

    if _is_effectively_empty(candidate.get("in_scope")) or _is_effectively_empty(candidate.get("out_of_scope")):
        missing.append("product_boundary")

    if not _extract_core_journeys(candidate):
        missing.append("core_journeys")

    domain_objects = candidate.get("structured_object_contracts")
    if not (
        isinstance(domain_objects, list)
        and any(isinstance(item, dict) and str(item.get("object") or "").strip() for item in domain_objects)
    ):
        missing.append("domain_model")

    has_state_machine = bool(_extract_state_machine_sections(candidate))
    if not has_state_machine and isinstance(domain_objects, list):
        for item in domain_objects:
            if not isinstance(item, dict):
                continue
            required_fields = item.get("required_fields") or []
            if isinstance(required_fields, list) and any(str(x).strip() in {"states", "allowed_transitions"} for x in required_fields):
                has_state_machine = True
                break
    if not has_state_machine:
        missing.append("state_machine")

    expected_outcomes = candidate.get("expected_outcomes")
    acceptance_impact = (candidate.get("bridge_context") or {}).get("acceptance_impact")
    if _is_effectively_empty(expected_outcomes) and _is_effectively_empty(acceptance_impact):
        missing.append("acceptance_contract")

    return missing


@dataclass(frozen=True)
class FrzWriteResult:
    package_dir: Path
    index_md: Path
    freeze_yaml: Path
    evidence_yaml: Path
    package_json: Path


def build_frz_package(*, run_id: str, candidate: dict[str, Any], document: dict[str, Any] | None) -> dict[str, Any]:
    title = str(candidate.get("title") or "").strip() or "FRZ"
    frz_id = f"FRZ-{_safe_slug(run_id)}"

    msc_missing = compute_msc_missing_dimensions(candidate)
    msc = {"required": list(MSC_REQUIRED_DIMENSIONS), "missing": msc_missing, "valid": not msc_missing}

    domain_model = []
    for index, item in enumerate(candidate.get("structured_object_contracts") or [], start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("object") or "").strip()
        if not name:
            continue
        domain_model.append(
            {
                "id": f"ENT-{index:03d}",
                "name": name,
                "contract": item,
                "source": {"kind": "src_field", "ref": "structured_object_contracts"},
            }
        )

    state_machines = []
    for index, sm in enumerate(_extract_state_machine_sections(candidate), start=1):
        state_machines.append(
            {
                "id": f"SM-{index:03d}",
                "name": sm["title"],
                "definition": sm["content"],
                "source": {"kind": "source_snapshot.sections", "ref": sm["title"]},
            }
        )

    frz = {
        "artifact_type": "frz_candidate_package",
        "frz_id": frz_id,
        "workflow_run_id": run_id,
        "title": title,
        "msc": msc,
        "freeze": {
            "product_boundary": {
                "in_scope": _normalize_list(candidate.get("in_scope")),
                "out_of_scope": _normalize_list(candidate.get("out_of_scope")),
                "source": {"kind": "src_field", "ref": "in_scope/out_of_scope"},
            },
            "core_journeys": _extract_core_journeys(candidate),
            "domain_model": domain_model,
            "state_machine": state_machines,
            "acceptance_contract": {
                "expected_outcomes": _normalize_list(candidate.get("expected_outcomes")),
                "acceptance_impact": _normalize_list((candidate.get("bridge_context") or {}).get("acceptance_impact")),
                "source": {"kind": "src_field", "ref": "expected_outcomes/bridge_context.acceptance_impact"},
            },
            "constraints": _normalize_list(candidate.get("key_constraints")),
            "derived_allowed": _normalize_list(candidate.get("downstream_derivation_requirements")),
            "known_unknowns": [
                {
                    "id": f"UNK-{index:03d}",
                    "topic": str(item).strip(),
                    "status": "open",
                    "expires_in": "2 cycles",
                    "owner": "",
                    "source": {"kind": "src_field", "ref": "uncertainties"},
                }
                for index, item in enumerate(candidate.get("uncertainties") or [], start=1)
                if str(item or "").strip()
            ],
        },
        "evidence": {
            "source_refs": list(candidate.get("source_refs") or []),
            "source_snapshot_ref": "source-snapshot.json",
            "normalization_decisions_ref": "normalization-decisions.json",
            "contradiction_register_ref": "contradiction-register.json",
            "source_provenance_map_ref": "source-provenance-map.json",
            "raw_path": (document or {}).get("path", "") if isinstance(document, dict) else "",
        },
    }
    return frz


def render_frz_index_markdown(frz: dict[str, Any]) -> str:
    freeze = frz.get("freeze") or {}
    msc = frz.get("msc") or {}
    lines = [
        f"# FRZ Package: {frz.get('title','')}".strip(),
        "",
        f"- frz_id: {frz.get('frz_id','')}",
        f"- workflow_run_id: {frz.get('workflow_run_id','')}",
        f"- msc_valid: {msc.get('valid')}",
    ]
    if msc.get("missing"):
        lines.append(f"- msc_missing: {', '.join(msc.get('missing') or [])}")
    lines.extend(["", "## Product Boundary", ""])
    boundary = freeze.get("product_boundary") or {}
    for item in boundary.get("in_scope") or []:
        lines.append(f"- in_scope: {item}")
    for item in boundary.get("out_of_scope") or []:
        lines.append(f"- out_of_scope: {item}")
    lines.extend(["", "## Core Journeys", ""])
    for journey in freeze.get("core_journeys") or []:
        name = str(journey.get("name") or "").strip() or journey.get("id") or "journey"
        lines.append(f"- {name}")
    lines.extend(["", "## Domain Model (Anchored)", ""])
    for ent in freeze.get("domain_model") or []:
        lines.append(f"- {ent.get('id')}: {ent.get('name')}")
    lines.extend(["", "## State Machines (Anchored)", ""])
    for sm in freeze.get("state_machine") or []:
        lines.append(f"- {sm.get('id')}: {sm.get('name')}")
    lines.extend(["", "## Acceptance Contract", ""])
    for item in (freeze.get("acceptance_contract") or {}).get("expected_outcomes") or []:
        lines.append(f"- expected: {item}")
    lines.extend(["", "## Known Unknowns", ""])
    for unk in freeze.get("known_unknowns") or []:
        lines.append(f"- {unk.get('id')}: {unk.get('topic')}")
    lines.append("")
    return "\n".join(lines)


def write_frz_package(artifacts_dir: Path, frz: dict[str, Any]) -> FrzWriteResult:
    package_dir = artifacts_dir / "frz-package"
    package_dir.mkdir(parents=True, exist_ok=True)

    freeze_yaml_path = package_dir / "freeze.yaml"
    evidence_yaml_path = package_dir / "evidence.yaml"
    index_md_path = package_dir / "index.md"
    package_json_path = package_dir / "frz-package.json"

    freeze = frz.get("freeze") or {}
    evidence = frz.get("evidence") or {}
    freeze_yaml_path.write_text(yaml.safe_dump(freeze, allow_unicode=True, sort_keys=False), encoding="utf-8")
    evidence_yaml_path.write_text(yaml.safe_dump(evidence, allow_unicode=True, sort_keys=False), encoding="utf-8")
    index_md_path.write_text(render_frz_index_markdown(frz), encoding="utf-8")
    package_json_path.write_text(json.dumps(frz, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return FrzWriteResult(
        package_dir=package_dir,
        index_md=index_md_path,
        freeze_yaml=freeze_yaml_path,
        evidence_yaml=evidence_yaml_path,
        package_json=package_json_path,
    )
