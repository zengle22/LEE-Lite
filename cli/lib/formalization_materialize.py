"""Materialization workflow for formal publication."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.formalization_render import (
    render_formal_epic_markdown,
    render_formal_feat_markdown,
    render_formal_impl_markdown,
    render_formal_src_markdown,
    render_formal_tech_markdown,
    render_formal_testset_yaml,
)
from cli.lib.formalization_snapshot import (
    assigned_id_from_path,
    candidate_source_path,
    compliant_epic_path,
    compliant_feat_path,
    compliant_impl_path,
    compliant_src_path,
    compliant_tech_path,
    compliant_testset_path,
    default_formal_ref,
    formal_epic_output_path,
    formal_feat_output_path,
    formal_impl_output_path,
    formal_src_output_path,
    formal_tech_output_path,
    formal_testset_output_path,
    infer_target_formal_kind,
    metadata_for,
    extract_numeric_src_ref,
    next_epic_id,
    next_epic_lineage_id,
    next_src_id,
    read_candidate_snapshot,
    run_ref_for,
)
from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json
from cli.lib.managed_gateway import governed_write
from cli.lib.registry_store import bind_record, record_path, resolve_registry_record, slugify


def existing_formal_record(workspace_root: Path, formal_ref: str) -> dict[str, Any] | None:
    target = record_path(workspace_root, formal_ref)
    if not target.exists():
        return None
    return load_json(target)


def materialize_handoff(workspace_root: Path, trace: dict[str, Any], candidate: dict[str, Any]) -> dict[str, str]:
    source_path = candidate_source_path(workspace_root, candidate)
    published_ref = to_canonical_path(source_path, workspace_root)
    materialized_ssot_ref = "artifacts/active/ssot/materialized-handoff.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(candidate['artifact_ref'])}",
            "ssot_type": "HANDOFF",
            "candidate_ref": candidate["artifact_ref"],
            "published_ref": published_ref,
            "managed_artifact_ref": candidate["managed_artifact_ref"],
        },
    )
    bind_record(
        workspace_root,
        default_formal_ref("handoff"),
        published_ref,
        "materialized",
        trace,
        metadata={"candidate_ref": candidate["artifact_ref"], "materialized_ssot_ref": materialized_ssot_ref},
        lineage=[candidate["artifact_ref"]],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": "",
        "gateway_receipt_ref": "",
    }


def materialize_generic(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, str]:
    published_ref = to_canonical_path(source_path, workspace_root)
    materialized_ssot_ref = f"artifacts/active/ssot/materialized-{slugify(formal_ref)}.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(formal_ref)}",
            "ssot_type": "GENERIC",
            "formal_ref": formal_ref,
            "published_ref": published_ref,
            "materialized_by": materialized_by,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata={"target_kind": "generic", "published_ref": published_ref},
        lineage=[candidate["artifact_ref"]],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": "",
        "gateway_receipt_ref": to_canonical_path(workspace_root / materialized_ssot_ref, workspace_root),
    }


def _resolve_src_target_path(workspace_root: Path, formal_ref: str, title: str) -> tuple[str, Path]:
    existing = existing_formal_record(workspace_root, formal_ref)
    if existing:
        existing_path = canonical_to_path(str(existing.get("managed_artifact_ref", "")), workspace_root)
        if existing_path.exists() and compliant_src_path(existing_path, workspace_root):
            return assigned_id_from_path(existing_path) or next_src_id(workspace_root), existing_path
    assigned_id = next_src_id(workspace_root)
    return assigned_id, formal_src_output_path(workspace_root, assigned_id, title)


def materialize_src(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    decision_ref: str,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, str]:
    snapshot = read_candidate_snapshot(workspace_root, source_path, candidate)
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    assigned_id, target_path = _resolve_src_target_path(workspace_root, formal_ref, snapshot["title"])
    write_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=f"materialize-{slugify(assigned_id)}",
        artifact_ref=formal_ref,
        workspace_path=to_canonical_path(target_path, workspace_root),
        requested_mode="promote",
        content=render_formal_src_markdown(snapshot, assigned_id, decision_ref, frozen_at),
        overwrite=True,
    )
    published_ref = write_result["managed_artifact_ref"]
    materialized_ssot_ref = "artifacts/active/ssot/materialized-src.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(assigned_id)}",
            "ssot_type": "SRC",
            "assigned_id": assigned_id,
            "version": snapshot["version"],
            "output_path": published_ref,
            "source_run_id": snapshot["workflow_run_id"],
            "source_skill": snapshot["workflow_key"] or "product.raw-to-src",
            "candidate_package_ref": snapshot["candidate_package_ref"],
            "gate_decision_ref": decision_ref,
            "source_refs": snapshot["source_refs"],
            "workflow_lineage_ref": snapshot["workflow_lineage_ref"],
            "materialized_by": materialized_by,
            "materialized_at": frozen_at,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata=metadata_for(workspace_root, candidate, source_path, "src", published_ref, assigned_id=assigned_id),
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": assigned_id,
        "gateway_receipt_ref": write_result["receipt_ref"],
    }


def _resolve_epic_target_path(
    workspace_root: Path,
    formal_ref: str,
    title: str,
    snapshot: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[str, Path]:
    explicit_id = str(snapshot["candidate_json"].get("epic_freeze_ref") or "").strip()
    lineage_explicit_id = explicit_id if re.fullmatch(r"EPIC-SRC-\d+-\d+", explicit_id.upper()) else ""
    numeric_explicit_id = explicit_id if explicit_id and explicit_id.upper().startswith("EPIC-") and explicit_id[5:].isdigit() else ""
    src_ref = extract_numeric_src_ref(snapshot.get("source_refs") or [], fallback=str(snapshot["candidate_json"].get("src_root_id") or ""))
    assigned_id = lineage_explicit_id or (next_epic_lineage_id(workspace_root, src_ref) if src_ref else "") or numeric_explicit_id or next_epic_id(workspace_root)
    target_path = formal_epic_output_path(workspace_root, assigned_id, title)
    existing = existing_formal_record(workspace_root, formal_ref)
    if existing:
        existing_path = canonical_to_path(str(existing.get("managed_artifact_ref", "")), workspace_root)
        if existing_path.exists() and compliant_epic_path(existing_path, workspace_root):
            existing_assigned_id = assigned_id_from_path(existing_path) or assigned_id
            if not (
                re.fullmatch(r"EPIC-SRC-\d+-\d+", existing_assigned_id.upper())
                or (existing_assigned_id.upper().startswith("EPIC-") and existing_assigned_id[5:].isdigit())
            ):
                return assigned_id, target_path
            normalized_existing_target = formal_epic_output_path(workspace_root, existing_assigned_id, title)
            if existing_path.name == normalized_existing_target.name:
                return existing_assigned_id, existing_path
            return existing_assigned_id, normalized_existing_target
    return assigned_id, target_path


def materialize_epic(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    decision_ref: str,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, str]:
    snapshot = read_candidate_snapshot(workspace_root, source_path, candidate)
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    assigned_id, target_path = _resolve_epic_target_path(workspace_root, formal_ref, snapshot["title"], snapshot, candidate)
    write_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=f"materialize-{slugify(assigned_id)}",
        artifact_ref=formal_ref,
        workspace_path=to_canonical_path(target_path, workspace_root),
        requested_mode="promote",
        content=render_formal_epic_markdown(snapshot, assigned_id, decision_ref, frozen_at),
        overwrite=True,
    )
    published_ref = write_result["managed_artifact_ref"]
    materialized_ssot_ref = "artifacts/active/ssot/materialized-epic.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(assigned_id)}",
            "ssot_type": "EPIC",
            "assigned_id": assigned_id,
            "version": snapshot["version"],
            "output_path": published_ref,
            "source_run_id": snapshot["workflow_run_id"],
            "source_skill": snapshot["workflow_key"] or "product.src-to-epic",
            "candidate_package_ref": snapshot["candidate_package_ref"],
            "gate_decision_ref": decision_ref,
            "source_refs": snapshot["source_refs"],
            "workflow_lineage_ref": snapshot["workflow_lineage_ref"],
            "materialized_by": materialized_by,
            "materialized_at": frozen_at,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata=metadata_for(workspace_root, candidate, source_path, "epic", published_ref, assigned_id=assigned_id),
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": assigned_id,
        "gateway_receipt_ref": write_result["receipt_ref"],
    }


def materialize_feat(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    decision_ref: str,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, Any]:
    snapshot = read_candidate_snapshot(workspace_root, source_path, candidate)
    features = [
        feature
        for feature in snapshot["candidate_json"].get("features") or []
        if isinstance(feature, dict) and str(feature.get("feat_ref") or "").strip()
    ]
    ensure(features, "PRECONDITION_FAILED", "feat candidate must include non-empty features")
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    materialized_formal_refs: list[str] = []
    published_refs: list[str] = []
    assigned_ids: list[str] = []
    gateway_receipt_refs: list[str] = []
    for feature in features:
        assigned_id = str(feature.get("feat_ref") or "").strip()
        title = str(feature.get("title") or assigned_id).strip() or assigned_id
        child_formal_ref = f"formal.feat.{slugify(assigned_id)}"
        existing = existing_formal_record(workspace_root, child_formal_ref)
        target_path: Path | None = None
        if existing:
            existing_path = canonical_to_path(str(existing.get("managed_artifact_ref", "")), workspace_root)
            if existing_path.exists() and compliant_feat_path(existing_path, workspace_root):
                target_path = existing_path
        if target_path is None:
            target_path = formal_feat_output_path(workspace_root, assigned_id, title)
        write_result = governed_write(
            workspace_root,
            trace=trace,
            request_id=f"materialize-{slugify(child_formal_ref)}",
            artifact_ref=child_formal_ref,
            workspace_path=to_canonical_path(target_path, workspace_root),
            requested_mode="promote",
            content=render_formal_feat_markdown(snapshot, feature, assigned_id, decision_ref, frozen_at),
            overwrite=True,
        )
        published_ref = write_result["managed_artifact_ref"]
        bind_record(
            workspace_root,
            child_formal_ref,
            published_ref,
            "materialized",
            trace,
            metadata={
                **metadata_for(workspace_root, candidate, source_path, "feat", published_ref, assigned_id=assigned_id),
                "feat_ref": assigned_id,
            },
            lineage=[candidate["artifact_ref"], decision_ref],
        )
        materialized_formal_refs.append(child_formal_ref)
        published_refs.append(published_ref)
        assigned_ids.append(assigned_id)
        gateway_receipt_refs.append(write_result["receipt_ref"])
    return _finalize_feat_materialization(
        workspace_root,
        trace,
        candidate,
        source_path,
        formal_ref,
        decision_ref,
        materialized_by,
        snapshot,
        frozen_at,
        materialized_formal_refs,
        published_refs,
        assigned_ids,
        gateway_receipt_refs,
    )


def materialize_tech(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    decision_ref: str,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, Any]:
    snapshot = read_candidate_snapshot(workspace_root, source_path, candidate)
    candidate_json = snapshot["candidate_json"]
    assigned_id = str(candidate_json.get("tech_ref") or "").strip() or str(candidate["artifact_ref"]).replace("candidate.", "TECH-", 1)
    title = str(candidate_json.get("title") or snapshot["title"]).strip() or assigned_id
    existing = existing_formal_record(workspace_root, formal_ref)
    target_path: Path | None = None
    if existing:
        existing_path = canonical_to_path(str(existing.get("managed_artifact_ref", "")), workspace_root)
        if existing_path.exists() and compliant_tech_path(existing_path, workspace_root):
            target_path = existing_path
    if target_path is None:
        target_path = formal_tech_output_path(workspace_root, assigned_id, title, snapshot["source_refs"])
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=f"materialize-{slugify(assigned_id)}",
        artifact_ref=formal_ref,
        workspace_path=to_canonical_path(target_path, workspace_root),
        requested_mode="promote",
        content=render_formal_tech_markdown(snapshot, assigned_id, decision_ref, frozen_at),
        overwrite=True,
    )
    published_ref = write_result["managed_artifact_ref"]
    materialized_ssot_ref = "artifacts/active/ssot/materialized-tech.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(assigned_id)}",
            "ssot_type": "TECH",
            "assigned_id": assigned_id,
            "output_path": published_ref,
            "source_run_id": snapshot["workflow_run_id"],
            "source_skill": snapshot["workflow_key"] or "dev.feat-to-tech",
            "candidate_package_ref": snapshot["candidate_package_ref"],
            "gate_decision_ref": decision_ref,
            "source_refs": snapshot["source_refs"],
            "workflow_lineage_ref": snapshot["workflow_lineage_ref"],
            "materialized_by": materialized_by,
            "materialized_at": frozen_at,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata=metadata_for(
            workspace_root,
            candidate,
            source_path,
            "tech",
            published_ref,
            assigned_id=assigned_id,
            extra_metadata={
                "tech_ref": assigned_id,
                "feat_ref": str(candidate_json.get("feat_ref") or "").strip(),
                "source_package_ref": snapshot["candidate_package_ref"],
            },
        ),
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": assigned_id,
        "gateway_receipt_ref": write_result["receipt_ref"],
    }


def materialize_testset(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    decision_ref: str,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, Any]:
    snapshot = read_candidate_snapshot(workspace_root, source_path, candidate)
    artifacts_dir = source_path.parent
    test_set_path = artifacts_dir / "test-set.yaml"
    ensure(test_set_path.exists(), "PRECONDITION_FAILED", "test-set.yaml is required for TESTSET formalization")
    test_set_yaml = load_json(test_set_path) if test_set_path.suffix.lower() == ".json" else None
    if test_set_yaml is None:
        import yaml
        test_set_yaml = yaml.safe_load(test_set_path.read_text(encoding="utf-8")) or {}
    candidate_json = snapshot["candidate_json"]
    assigned_id = str(candidate_json.get("test_set_ref") or test_set_yaml.get("id") or "").strip() or formal_ref.split(".")[-1].upper()
    title = str(candidate_json.get("title") or snapshot["title"]).strip() or assigned_id
    existing = existing_formal_record(workspace_root, formal_ref)
    target_path: Path | None = None
    if existing:
        existing_path = canonical_to_path(str(existing.get("managed_artifact_ref", "")), workspace_root)
        if existing_path.exists() and compliant_testset_path(existing_path, workspace_root):
            target_path = existing_path
    if target_path is None:
        target_path = formal_testset_output_path(workspace_root, assigned_id, title)
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=f"materialize-{slugify(assigned_id)}",
        artifact_ref=formal_ref,
        workspace_path=to_canonical_path(target_path, workspace_root),
        requested_mode="promote",
        content=render_formal_testset_yaml(test_set_yaml, assigned_id, decision_ref, frozen_at, snapshot["candidate_package_ref"]),
        overwrite=True,
    )
    published_ref = write_result["managed_artifact_ref"]
    materialized_ssot_ref = "artifacts/active/ssot/materialized-testset.json"
    handoff = load_json(artifacts_dir / "handoff-to-test-execution.json")
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata=metadata_for(
            workspace_root,
            candidate,
            source_path,
            "testset",
            published_ref,
            assigned_id=assigned_id,
            extra_metadata={
                "test_set_ref": assigned_id,
                "feat_ref": str(candidate_json.get("feat_ref") or "").strip(),
                "target_skill": str(handoff.get("target_skill") or candidate_json.get("downstream_target") or "").strip(),
                "source_package_ref": snapshot["candidate_package_ref"],
            },
        ),
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(assigned_id)}",
            "ssot_type": "TESTSET",
            "assigned_id": assigned_id,
            "output_path": published_ref,
            "source_run_id": snapshot["workflow_run_id"],
            "source_skill": snapshot["workflow_key"] or "qa.feat-to-testset",
            "candidate_package_ref": snapshot["candidate_package_ref"],
            "gate_decision_ref": decision_ref,
            "target_skill": str(handoff.get("target_skill") or ""),
            "materialized_by": materialized_by,
            "materialized_at": frozen_at,
        },
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": assigned_id,
        "gateway_receipt_ref": write_result["receipt_ref"],
    }


def materialize_impl(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    decision_ref: str,
    formal_ref: str,
    materialized_by: str,
) -> dict[str, Any]:
    snapshot = read_candidate_snapshot(workspace_root, source_path, candidate)
    candidate_json = snapshot["candidate_json"]
    assigned_id = str(candidate_json.get("impl_ref") or "").strip() or formal_ref.split(".")[-1].upper()
    title = str(candidate_json.get("title") or snapshot["title"]).strip() or assigned_id
    existing = existing_formal_record(workspace_root, formal_ref)
    target_path: Path | None = None
    if existing:
        existing_path = canonical_to_path(str(existing.get("managed_artifact_ref", "")), workspace_root)
        if existing_path.exists() and compliant_impl_path(existing_path, workspace_root):
            target_path = existing_path
    if target_path is None:
        target_path = formal_impl_output_path(workspace_root, assigned_id, title)
    frozen_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    write_result = governed_write(
        workspace_root,
        trace=trace,
        request_id=f"materialize-{slugify(assigned_id)}",
        artifact_ref=formal_ref,
        workspace_path=to_canonical_path(target_path, workspace_root),
        requested_mode="promote",
        content=render_formal_impl_markdown(snapshot, assigned_id, decision_ref, frozen_at),
        overwrite=True,
    )
    published_ref = write_result["managed_artifact_ref"]
    materialized_ssot_ref = "artifacts/active/ssot/materialized-impl.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(assigned_id)}",
            "ssot_type": "IMPL",
            "assigned_id": assigned_id,
            "output_path": published_ref,
            "source_run_id": snapshot["workflow_run_id"],
            "source_skill": snapshot["workflow_key"] or "dev.tech-to-impl",
            "candidate_package_ref": snapshot["candidate_package_ref"],
            "gate_decision_ref": decision_ref,
            "materialized_by": materialized_by,
            "materialized_at": frozen_at,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata=metadata_for(
            workspace_root,
            candidate,
            source_path,
            "impl",
            published_ref,
            assigned_id=assigned_id,
            extra_metadata={
                "impl_ref": assigned_id,
                "tech_ref": str(candidate_json.get("tech_ref") or "").strip(),
                "feat_ref": str(candidate_json.get("feat_ref") or "").strip(),
                "source_package_ref": snapshot["candidate_package_ref"],
            },
        ),
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": assigned_id,
        "gateway_receipt_ref": write_result["receipt_ref"],
    }


def _finalize_feat_materialization(
    workspace_root: Path,
    trace: dict[str, Any],
    candidate: dict[str, Any],
    source_path: Path,
    formal_ref: str,
    decision_ref: str,
    materialized_by: str,
    snapshot: dict[str, Any],
    frozen_at: str,
    materialized_formal_refs: list[str],
    published_refs: list[str],
    assigned_ids: list[str],
    gateway_receipt_refs: list[str],
) -> dict[str, Any]:
    index_path = workspace_root / "artifacts" / "active" / "formal" / "feat" / run_ref_for(candidate, source_path) / "formal-feat-index.json"
    write_json(
        index_path,
        {
            "formal_artifact_ref": formal_ref,
            "workflow_key": snapshot["workflow_key"],
            "workflow_run_id": snapshot["workflow_run_id"],
            "candidate_ref": candidate["artifact_ref"],
            "candidate_package_ref": snapshot["candidate_package_ref"],
            "materialized_formal_refs": materialized_formal_refs,
            "published_refs": published_refs,
            "assigned_ids": assigned_ids,
            "materialized_at": frozen_at,
        },
    )
    published_ref = to_canonical_path(index_path, workspace_root)
    materialized_ssot_ref = "artifacts/active/ssot/materialized-feat.json"
    write_json(
        workspace_root / materialized_ssot_ref,
        {
            "materialization_id": f"materialization-{slugify(formal_ref)}",
            "ssot_type": "FEAT",
            "assigned_ids": assigned_ids,
            "output_path": published_ref,
            "published_refs": published_refs,
            "source_run_id": snapshot["workflow_run_id"],
            "source_skill": snapshot["workflow_key"] or "product.epic-to-feat",
            "candidate_package_ref": snapshot["candidate_package_ref"],
            "gate_decision_ref": decision_ref,
            "source_refs": snapshot["source_refs"],
            "workflow_lineage_ref": snapshot["workflow_lineage_ref"],
            "materialized_by": materialized_by,
            "materialized_at": frozen_at,
        },
    )
    bind_record(
        workspace_root,
        formal_ref,
        published_ref,
        "materialized",
        trace,
        metadata={
            **metadata_for(workspace_root, candidate, source_path, "feat", published_ref),
            "materialized_formal_refs": materialized_formal_refs,
            "published_refs": published_refs,
            "assigned_ids": assigned_ids,
        },
        lineage=[candidate["artifact_ref"], decision_ref],
    )
    return {
        "published_ref": published_ref,
        "materialized_ssot_ref": materialized_ssot_ref,
        "assigned_id": assigned_ids[0] if len(assigned_ids) == 1 else "",
        "materialized_formal_refs": materialized_formal_refs,
        "published_refs": published_refs,
        "assigned_ids": assigned_ids,
        "gateway_receipt_refs": gateway_receipt_refs,
    }


def materialize_formal(
    workspace_root,
    trace: dict[str, Any],
    candidate_ref: str,
    decision_ref: str,
    target_formal_kind: str | None,
    formal_artifact_ref: str | None = None,
    materialized_by: str | None = None,
) -> dict[str, str]:
    decision = load_json(canonical_to_path(decision_ref, workspace_root))
    ensure(decision.get("decision_type") in {"approve", "handoff"}, "PRECONDITION_FAILED", "decision_not_approvable")
    candidate = resolve_registry_record(workspace_root, candidate_ref)
    source_path = candidate_source_path(workspace_root, candidate)
    effective_target_kind = infer_target_formal_kind(candidate, source_path, target_formal_kind)
    run_ref = run_ref_for(candidate, source_path)
    default_ref = _default_formal_artifact_ref(effective_target_kind, run_ref)
    formal_ref = str(formal_artifact_ref or default_ref).strip() or default_ref
    materialized_by_value = str(materialized_by or decision.get("decided_by") or "gate").strip() or "gate"

    if effective_target_kind == "handoff":
        result = materialize_handoff(workspace_root, trace, candidate)
    elif effective_target_kind == "src":
        result = materialize_src(
            workspace_root, trace, candidate, source_path, decision_ref, formal_ref, materialized_by_value
        )
    elif effective_target_kind == "epic":
        result = materialize_epic(
            workspace_root, trace, candidate, source_path, decision_ref, formal_ref, materialized_by_value
        )
    elif effective_target_kind == "feat":
        result = materialize_feat(
            workspace_root, trace, candidate, source_path, decision_ref, formal_ref, materialized_by_value
        )
    elif effective_target_kind == "tech":
        result = materialize_tech(
            workspace_root, trace, candidate, source_path, decision_ref, formal_ref, materialized_by_value
        )
    elif effective_target_kind == "testset":
        result = materialize_testset(
            workspace_root, trace, candidate, source_path, decision_ref, formal_ref, materialized_by_value
        )
    elif effective_target_kind == "impl":
        result = materialize_impl(
            workspace_root, trace, candidate, source_path, decision_ref, formal_ref, materialized_by_value
        )
    else:
        result = materialize_generic(
            workspace_root, trace, candidate, source_path, formal_ref, materialized_by_value
        )

    return {
        "formal_ref": formal_ref,
        "formal_artifact_ref": formal_ref,
        "target_formal_kind": effective_target_kind,
        "published_ref": str(result["published_ref"]),
        "materialized_ssot_ref": str(result["materialized_ssot_ref"]),
        "assigned_id": str(result.get("assigned_id") or ""),
        "materialized_formal_refs": list(result.get("materialized_formal_refs") or []),
        "published_refs": list(result.get("published_refs") or []),
        "assigned_ids": list(result.get("assigned_ids") or []),
        "receipt_ref": str(result.get("gateway_receipt_ref") or ""),
        "gateway_receipt_ref": str(result.get("gateway_receipt_ref") or ""),
        "run_ref": run_ref,
    }


def _default_formal_artifact_ref(target_kind: str, run_ref: str) -> str:
    if target_kind in {"src", "epic", "feat", "tech", "testset", "impl"} and run_ref:
        return f"formal.{target_kind}.{run_ref}"
    return default_formal_ref(target_kind)
