"""Owner-level merge helpers for shared UI and PROTOTYPE publication."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from cli.lib.formalization_snapshot import (
    candidate_source_path,
    extract_src_ref,
    parse_frontmatter,
    read_candidate_snapshot,
)
from cli.lib.fs import canonical_to_path, load_json
from cli.lib.registry_store import record_path, slugify


def _registry_dir(workspace_root: Path) -> Path:
    return workspace_root / "artifacts" / "registry"


def _formal_ref_for_candidate(record: dict[str, Any], target_kind: str) -> str:
    run_ref = str(record.get("trace", {}).get("run_ref") or "").strip()
    return f"formal.{target_kind}.{run_ref}" if run_ref else ""


def _iter_candidate_records(
    workspace_root: Path,
    target_kind: str,
    current_candidate_ref: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(_registry_dir(workspace_root).glob(f"candidate-{target_kind}-*.json")):
        try:
            payload = load_json(path)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        artifact_ref = str(payload.get("artifact_ref") or "").strip()
        if artifact_ref != current_candidate_ref:
            formal_ref = _formal_ref_for_candidate(payload, target_kind)
            if not formal_ref or not record_path(workspace_root, formal_ref).exists():
                continue
        records.append(payload)
    return records


def _sort_key(entry: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(entry.get("feat_ref") or ""),
        str(entry.get("workflow_run_id") or entry.get("run_ref") or ""),
        str(entry.get("candidate_ref") or ""),
    )


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _owner_title(owner_ref: str, fallback: str) -> str:
    parts = [part for part in str(owner_ref or fallback).split("-") if part]
    if len(parts) <= 1:
        return str(owner_ref or fallback)
    return " ".join(part.capitalize() for part in parts[1:])


def collect_ui_owner_contributions(
    workspace_root: Path,
    owner_ref: str,
    src_ref: str,
    current_candidate_ref: str,
) -> list[dict[str, Any]]:
    contributions: list[dict[str, Any]] = []
    for record in _iter_candidate_records(workspace_root, "ui", current_candidate_ref):
        source_path = candidate_source_path(workspace_root, record)
        snapshot = read_candidate_snapshot(workspace_root, source_path, record)
        candidate_json = snapshot["candidate_json"]
        current_owner = str(candidate_json.get("ui_owner_ref") or candidate_json.get("ui_ref") or "").strip()
        if current_owner != owner_ref:
            continue
        current_src = extract_src_ref(snapshot.get("source_refs") or [], "")
        if src_ref and current_src != src_ref:
            continue
        ui_docs = _load_ui_spec_docs(source_path.parent, candidate_json)
        contributions.append(
            {
                "candidate_ref": str(record.get("artifact_ref") or "").strip(),
                "workflow_run_id": snapshot["workflow_run_id"],
                "run_ref": str(record.get("trace", {}).get("run_ref") or "").strip(),
                "candidate_package_ref": snapshot["candidate_package_ref"],
                "source_package_ref": snapshot["candidate_package_ref"],
                "source_refs": snapshot.get("source_refs") or [],
                "feat_ref": str(candidate_json.get("feat_ref") or "").strip(),
                "title": str(candidate_json.get("title") or snapshot["title"]).strip(),
                "surface_map_ref": str(candidate_json.get("surface_map_ref") or "").strip(),
                "ui_action": str(candidate_json.get("ui_action") or "").strip(),
                "body": snapshot["body"].strip(),
                "ui_docs": ui_docs,
            }
        )
    contributions.sort(key=_sort_key)
    return contributions


def _load_ui_spec_docs(source_dir: Path, candidate_json: dict[str, Any]) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    refs = [str(item).strip() for item in (candidate_json.get("ui_spec_refs") or []) if str(item).strip()]
    paths: list[Path] = []
    for ref in refs:
        candidate_path = source_dir / ref
        if candidate_path.exists():
            paths.append(candidate_path)
    if not paths:
        paths = sorted(source_dir.glob("[[]UI-*__ui_spec.md"))
    for path in paths:
        content = path.read_text(encoding="utf-8")
        _, body = parse_frontmatter(content)
        docs.append(
            {
                "path": str(path.name),
                "title": _first_heading(body) or path.stem,
                "body": body.strip(),
            }
        )
    return docs


def _first_heading(markdown_body: str) -> str:
    for line in markdown_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def render_merged_formal_ui_markdown(
    owner_ref: str,
    contributions: list[dict[str, Any]],
    decision_ref: str,
    frozen_at: str,
    current_snapshot: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    related_feat_refs = _unique_strings([item["feat_ref"] for item in contributions])
    surface_map_refs = _unique_strings([item["surface_map_ref"] for item in contributions])
    source_package_refs = _unique_strings([item["source_package_ref"] for item in contributions])
    merged_candidate_refs = _unique_strings([item["candidate_ref"] for item in contributions])
    source_refs = _unique_strings([ref for item in contributions for ref in item.get("source_refs", [])])
    frontmatter = {
        "id": owner_ref,
        "ssot_type": "UI",
        "ui_ref": owner_ref,
        "ui_owner_ref": owner_ref,
        "feat_ref": str(current_snapshot["candidate_json"].get("feat_ref") or "").strip(),
        "title": _owner_title(owner_ref, current_snapshot["title"]),
        "status": "accepted",
        "schema_version": "1.0.0",
        "workflow_key": current_snapshot["workflow_key"],
        "workflow_run_id": current_snapshot["workflow_run_id"],
        "candidate_package_ref": current_snapshot["candidate_package_ref"],
        "gate_decision_ref": decision_ref,
        "frozen_at": frozen_at,
        "related_feat_refs": related_feat_refs,
        "surface_map_refs": surface_map_refs,
        "merged_candidate_refs": merged_candidate_refs,
        "source_package_refs": source_package_refs,
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    lines = [
        f"# {_owner_title(owner_ref, current_snapshot['title'])}",
        "",
        "## Ownership Summary",
        f"- ui_owner_ref: {owner_ref}",
        f"- related_feat_refs: {', '.join(related_feat_refs) if related_feat_refs else 'None'}",
        f"- surface_map_refs: {', '.join(surface_map_refs) if surface_map_refs else 'None'}",
        f"- source_package_count: {len(source_package_refs)}",
        "",
        "## Aggregated UI Specs",
    ]
    for item in contributions:
        lines.extend(
            [
                "",
                f"### {item['feat_ref']} · {item['title']}",
                f"- source_package_ref: {item['source_package_ref']}",
                f"- surface_map_ref: {item['surface_map_ref'] or 'None'}",
                f"- ui_action: {item['ui_action'] or 'update'}",
            ]
        )
        for doc in item["ui_docs"]:
            lines.extend(["", f"#### {doc['title']}", "", doc["body"]])
        if not item["ui_docs"] and item.get("body"):
            lines.extend(["", item["body"]])
    body = "\n".join(lines).rstrip() + "\n"
    metadata = {
        "ui_owner_ref": owner_ref,
        "related_feat_refs": related_feat_refs,
        "surface_map_refs": surface_map_refs,
        "merged_candidate_refs": merged_candidate_refs,
        "source_package_refs": source_package_refs,
        "source_refs": source_refs,
    }
    return f"---\n{header}\n---\n\n{body}", metadata


def collect_prototype_owner_contributions(
    workspace_root: Path,
    owner_ref: str,
    src_ref: str,
    current_candidate_ref: str,
) -> list[dict[str, Any]]:
    contributions: list[dict[str, Any]] = []
    for record in _iter_candidate_records(workspace_root, "prototype", current_candidate_ref):
        source_path = candidate_source_path(workspace_root, record)
        bundle = load_json(source_path.parent.parent / "prototype-bundle.json")
        current_owner = str(bundle.get("prototype_owner_ref") or bundle.get("prototype_ref") or "").strip()
        if current_owner != owner_ref:
            continue
        current_src = extract_src_ref([str(ref) for ref in bundle.get("source_refs") or []], "")
        if src_ref and current_src != src_ref:
            continue
        source_dir = source_path.parent
        contributions.append(
            {
                "candidate_ref": str(record.get("artifact_ref") or "").strip(),
                "workflow_run_id": str(bundle.get("workflow_run_id") or record.get("trace", {}).get("run_ref") or "").strip(),
                "run_ref": str(record.get("trace", {}).get("run_ref") or "").strip(),
                "source_dir": source_dir,
                "source_package_ref": str(record.get("metadata", {}).get("source_package_ref") or "").strip(),
                "feat_ref": str(bundle.get("feat_ref") or "").strip(),
                "feat_title": str(bundle.get("feat_title") or "").strip(),
                "source_refs": [str(ref).strip() for ref in (bundle.get("source_refs") or []) if str(ref).strip()],
                "surface_map_ref": str(bundle.get("surface_map_ref") or "").strip(),
                "prototype_action": str(bundle.get("prototype_action") or "").strip(),
                "ui_owner_ref": str(bundle.get("ui_owner_ref") or "").strip(),
                "ui_action": str(bundle.get("ui_action") or "").strip(),
                "bundle": bundle,
                "mock_data": _load_optional_json(source_dir / "mock-data.json"),
                "journey_model": _load_optional_json(source_dir / "journey-model.json"),
            }
        )
    contributions.sort(key=_sort_key)
    return contributions


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return load_json(path)
    except Exception:
        return {}


def build_merged_prototype_payloads(
    owner_ref: str,
    contributions: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    latest = contributions[-1]
    related_feat_refs = _unique_strings([item["feat_ref"] for item in contributions])
    source_refs = _unique_strings([ref for item in contributions for ref in item.get("source_refs", [])])
    surface_map_refs = _unique_strings([item["surface_map_ref"] for item in contributions])
    pages: list[dict[str, Any]] = []
    seen_page_ids: set[str] = set()
    for item in contributions:
        for page in item.get("mock_data", {}).get("pages") or item.get("bundle", {}).get("pages") or []:
            page_copy = deepcopy(page)
            page_id = str(page_copy.get("page_id") or slugify(page_copy.get("title") or item["feat_ref"])).strip()
            if page_id in seen_page_ids:
                continue
            seen_page_ids.add(page_id)
            page_copy["source_feat_ref"] = item["feat_ref"]
            pages.append(page_copy)
    feat_dependency_order = _merge_feat_dependency_order(contributions, related_feat_refs)
    merged_mock_data = {
        "feat_ref": owner_ref,
        "feat_title": _owner_title(owner_ref, latest["feat_title"] or owner_ref),
        "related_feat_refs": related_feat_refs,
        "source_refs": source_refs,
        "surface_map_refs": surface_map_refs,
        "prototype_owner_ref": owner_ref,
        "prototype_action": "update" if len(contributions) > 1 else (latest["prototype_action"] or "create"),
        "ui_owner_ref": latest["ui_owner_ref"],
        "ui_action": "update" if len(contributions) > 1 else (latest["ui_action"] or "create"),
        "journey_structural_spec_ref": str(latest["bundle"].get("journey_structural_spec_ref") or ""),
        "ui_shell_snapshot_ref": str(latest["bundle"].get("ui_shell_snapshot_ref") or ""),
        "pages": pages,
    }
    merged_journey_model = {
        "journey_id": str(latest.get("journey_model", {}).get("journey_id") or latest["bundle"].get("journey_id") or ""),
        "feat_ref": owner_ref,
        "related_feat_refs": related_feat_refs,
        "journey_surface_inventory": _build_journey_surface_inventory(pages),
        "journey_main_path": _unique_strings(
            [step for item in contributions for step in (item.get("journey_model", {}).get("journey_main_path") or [])]
        ),
        "feat_dependency_order": feat_dependency_order,
        "checked_at": str(latest.get("journey_model", {}).get("checked_at") or ""),
    }
    metadata = {
        "related_feat_refs": related_feat_refs,
        "surface_map_refs": surface_map_refs,
        "source_package_refs": _unique_strings([item["source_package_ref"] for item in contributions]),
        "merged_candidate_refs": _unique_strings([item["candidate_ref"] for item in contributions]),
        "source_refs": source_refs,
    }
    return merged_mock_data, merged_journey_model, metadata


def _merge_feat_dependency_order(contributions: list[dict[str, Any]], fallback: list[str]) -> list[str]:
    longest: list[str] = []
    for item in contributions:
        candidate = [str(ref).strip() for ref in (item.get("journey_model", {}).get("feat_dependency_order") or []) if str(ref).strip()]
        if len(candidate) > len(longest):
            longest = candidate
    return longest or fallback


def _build_journey_surface_inventory(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for index, page in enumerate(pages):
        inventory.append(
            {
                "journey_id": "",
                "journey_loop": "",
                "journey_stage": "",
                "surface_id": str(page.get("page_id") or f"page-{index}"),
                "surface_kind": "page",
                "surface_title": str(page.get("title") or page.get("page_id") or f"Page {index + 1}"),
                "surface_role": "host",
                "host_surface_id": "",
                "composes_feat_refs": _unique_strings([str(page.get("source_feat_ref") or "").strip()]),
                "modes": [],
                "entry_from": [],
                "exit_to": [],
                "shared_state_refs": [],
                "notes": "",
            }
        )
    return inventory


def render_proto_js(global_name: str, payload: dict[str, Any]) -> str:
    return f"window.__{global_name}__ = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
