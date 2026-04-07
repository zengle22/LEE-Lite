"""Helpers for publishing TECH supporting ARCH/API artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import ensure
from cli.lib.formalization_snapshot import (
    extract_first_heading,
    extract_src_ref,
    metadata_for,
    normalize_list,
    parse_frontmatter,
)
from cli.lib.fs import load_json, read_text, to_canonical_path
from cli.lib.managed_gateway import governed_write
from cli.lib.registry_store import bind_record, record_path, slugify


def _existing_formal_record(workspace_root: Path, formal_ref: str) -> dict[str, Any] | None:
    target = record_path(workspace_root, formal_ref)
    if not target.exists():
        return None
    return load_json(target)


def _child_title(tech_title: str, assigned_id: str, child_kind: str, body: str) -> str:
    heading = extract_first_heading(body)
    if heading and heading.upper() != assigned_id.upper():
        return heading
    suffix = "Architecture Overview" if child_kind == "arch" else "API Contract"
    return f"{tech_title} {suffix}".strip()


def _compliant_child_path(path: Path, workspace_root: Path, child_kind: str) -> bool:
    canonical = to_canonical_path(path, workspace_root)
    if child_kind == "arch":
        return canonical.startswith("ssot/architecture/ARCH-") and path.suffix.lower() == ".md"
    return canonical.startswith("ssot/api/API-") and path.suffix.lower() in {".md", ".yaml", ".yml"}


def _formal_child_output_path(
    workspace_root: Path,
    child_kind: str,
    assigned_id: str,
    title: str,
    source_refs: list[str],
) -> Path:
    filename = f"{assigned_id}__{slugify(title)}"
    if child_kind == "arch":
        return workspace_root / "ssot" / "architecture" / f"{filename}.md"
    src_ref = extract_src_ref(source_refs)
    api_dir = workspace_root / "ssot" / "api"
    if src_ref:
        api_dir = api_dir / src_ref
    return api_dir / f"{filename}.md"


def _render_child_markdown(
    *,
    child_kind: str,
    assigned_id: str,
    tech_ref: str,
    feat_ref: str,
    title: str,
    workflow_key: str,
    workflow_run_id: str,
    candidate_package_ref: str,
    decision_ref: str,
    frozen_at: str,
    source_refs: list[str],
    body: str,
    surface_map_ref: str,
    related_feat_refs: list[str],
    last_updated_by: list[str],
    open_deltas: list[str],
) -> str:
    frontmatter: dict[str, Any] = {
        "id": assigned_id,
        "ssot_type": child_kind.upper(),
        f"{child_kind}_ref": assigned_id,
        "tech_ref": tech_ref,
        "feat_ref": feat_ref,
        "surface_map_ref": surface_map_ref,
        "title": title,
        "status": "accepted",
        "schema_version": "1.0.0",
        "workflow_key": workflow_key,
        "workflow_run_id": workflow_run_id,
        "candidate_package_ref": candidate_package_ref,
        "gate_decision_ref": decision_ref,
        "frozen_at": frozen_at,
        "source_refs": source_refs,
        "related_feat_refs": related_feat_refs,
        "last_updated_by": last_updated_by,
        "open_deltas": open_deltas,
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    body_text = body.strip()
    if not body_text.startswith("# "):
        body_text = f"# {assigned_id}\n\n{body_text}".strip()
    return f"---\n{header}\n---\n\n{body_text}\n"


def _materialize_optional_child(
    *,
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    snapshot: dict[str, Any],
    decision_ref: str,
    child_kind: str,
    child_filename: str,
    assigned_id: str,
    feat_ref: str,
    tech_ref: str,
    frozen_at: str,
) -> dict[str, str]:
    child_path = source_path.parent / child_filename
    ensure(child_path.exists(), "PRECONDITION_FAILED", f"required {child_filename} missing for {tech_ref}")
    markdown_text = read_text(child_path)
    _, body = parse_frontmatter(markdown_text)
    title = _child_title(snapshot["title"], assigned_id, child_kind, body)
    child_formal_ref = f"formal.{child_kind}.{slugify(assigned_id)}"
    related_feat_refs = [feat_ref] if feat_ref else []
    last_updated_by = [feat_ref] if feat_ref else []
    open_deltas = [item for item in normalize_list((snapshot["candidate_json"].get("selected_feat") or {}).get("scope")) if item][:3]
    surface_map_ref = str(snapshot["candidate_json"].get("surface_map_ref") or "").strip()

    existing = _existing_formal_record(workspace_root, child_formal_ref)
    target_path: Path | None = None
    if existing:
        existing_path = workspace_root / str(existing.get("managed_artifact_ref") or "")
        if existing_path.exists() and _compliant_child_path(existing_path, workspace_root, child_kind):
            target_path = existing_path
    if target_path is None:
        target_path = _formal_child_output_path(workspace_root, child_kind, assigned_id, title, snapshot["source_refs"])

    write_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=f"materialize-{slugify(child_formal_ref)}",
        artifact_ref=child_formal_ref,
        workspace_path=to_canonical_path(target_path, workspace_root),
        requested_mode="promote",
        content=_render_child_markdown(
            child_kind=child_kind,
            assigned_id=assigned_id,
            tech_ref=tech_ref,
            feat_ref=feat_ref,
            title=title,
            workflow_key=snapshot["workflow_key"],
            workflow_run_id=snapshot["workflow_run_id"],
            candidate_package_ref=snapshot["candidate_package_ref"],
            decision_ref=decision_ref,
            frozen_at=frozen_at,
            source_refs=snapshot["source_refs"],
            body=body,
            surface_map_ref=surface_map_ref,
            related_feat_refs=related_feat_refs,
            last_updated_by=last_updated_by,
            open_deltas=open_deltas,
        ),
        overwrite=True,
    )
    published_ref = write_result["managed_artifact_ref"]
    bind_record(
        workspace_root,
        child_formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata=metadata_for(
            workspace_root,
            candidate,
            source_path,
            child_kind,
            published_ref,
            assigned_id=assigned_id,
            extra_metadata={
                f"{child_kind}_ref": assigned_id,
                "tech_ref": tech_ref,
                "feat_ref": feat_ref,
                "surface_map_ref": surface_map_ref,
                "related_feat_refs": related_feat_refs,
                "last_updated_by": last_updated_by,
                "open_deltas": open_deltas,
                "source_package_ref": snapshot["candidate_package_ref"],
            },
        ),
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    return {
        "formal_ref": child_formal_ref,
        "published_ref": published_ref,
        "assigned_id": assigned_id,
        "receipt_ref": write_result["receipt_ref"],
    }


def materialize_tech_supporting_artifacts(
    *,
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    snapshot: dict[str, Any],
    decision_ref: str,
    frozen_at: str,
) -> dict[str, list[str]]:
    candidate_json = snapshot["candidate_json"]
    feat_ref = str(candidate_json.get("feat_ref") or "").strip()
    tech_ref = str(candidate_json.get("tech_ref") or "").strip()
    materialized_formal_refs: list[str] = []
    published_refs: list[str] = []
    assigned_ids: list[str] = []
    gateway_receipt_refs: list[str] = []

    child_specs = [
        ("arch", bool(candidate_json.get("arch_required")), str(candidate_json.get("arch_ref") or "").strip(), "arch-design.md"),
        ("api", bool(candidate_json.get("api_required")), str(candidate_json.get("api_ref") or "").strip(), "api-contract.md"),
    ]
    for child_kind, required, assigned_id, child_filename in child_specs:
        if not required:
            continue
        ensure(assigned_id, "PRECONDITION_FAILED", f"{child_kind}_required is true but {child_kind}_ref is missing for {tech_ref}")
        result = _materialize_optional_child(
            workspace_root=workspace_root,
            trace=trace,
            candidate=candidate,
            source_path=source_path,
            snapshot=snapshot,
            decision_ref=decision_ref,
            child_kind=child_kind,
            child_filename=child_filename,
            assigned_id=assigned_id,
            feat_ref=feat_ref,
            tech_ref=tech_ref,
            frozen_at=frozen_at,
        )
        materialized_formal_refs.append(result["formal_ref"])
        published_refs.append(result["published_ref"])
        assigned_ids.append(result["assigned_id"])
        gateway_receipt_refs.append(result["receipt_ref"])

    return {
        "materialized_formal_refs": materialized_formal_refs,
        "published_refs": published_refs,
        "assigned_ids": assigned_ids,
        "gateway_receipt_refs": gateway_receipt_refs,
    }
