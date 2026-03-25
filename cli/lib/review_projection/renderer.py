"""Human review projection rendering and gate integration."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from cli.lib.fs import canonical_to_path, load_json, read_text, write_json
from cli.lib.registry_store import resolve_registry_record, slugify
from cli.lib.review_projection.focus import build_review_focus_or_empty
from cli.lib.review_projection.markers import ProjectionMarkerError, attach_projection_markers
from cli.lib.review_projection.prompt_blocks import compose_prompt_blocks
from cli.lib.review_projection.snapshot import build_authoritative_snapshot_or_flag
from cli.lib.review_projection.template import DEFAULT_TEMPLATE_VERSION, build_review_blocks, load_projection_template


class ProjectionRenderError(RuntimeError):
    """Raised when projection rendering cannot satisfy the frozen contract."""


def render_projection(workspace_root: Path, request: dict[str, Any]) -> dict[str, Any]:
    template = load_projection_template(str(request.get("template_version", DEFAULT_TEMPLATE_VERSION)))
    if template is None:
        raise ProjectionRenderError("template_missing")
    try:
        ssot_payload, resolved_ssot_ref = load_machine_ssot(workspace_root, str(request["ssot_ref"]))
    except Exception as exc:
        raise ProjectionRenderError("ssot_not_ready") from exc
    if not _is_freeze_ready(ssot_payload):
        raise ProjectionRenderError("ssot_not_ready")
    review_stage = str(request.get("review_stage", "gate_review"))
    projection_ref = _projection_ref(request.get("projection_key"), resolved_ssot_ref, template["version"], review_stage)
    base_blocks = build_review_blocks(ssot_payload, template)
    snapshot = build_authoritative_snapshot_or_flag(workspace_root, resolved_ssot_ref, projection_ref, ssot_payload)
    block_sources = {block["id"]: block.get("source_fields", []) for block in base_blocks}
    field_trace_refs = snapshot.get("field_refs", {})
    focus_result = build_review_focus_or_empty(
        workspace_root,
        resolved_ssot_ref,
        projection_ref,
        ssot_payload,
        base_blocks,
        field_trace_refs,
    )
    prompt_blocks = compose_prompt_blocks(focus_result)
    prompt_trace_refs = []
    for block in prompt_blocks:
        prompt_trace_refs.extend(block.get("source_trace_refs", []))
    try:
        marker_result = attach_projection_markers(
            resolved_ssot_ref,
            template["version"],
            projection_ref,
            block_sources,
            snapshot.get("field_refs", {}),
            prompt_trace_refs,
        )
    except ProjectionMarkerError as exc:
        raise ProjectionRenderError(str(exc)) from exc
    status = marker_result["status"]
    if snapshot.get("traceability_status") != "traceable_to_ssot":
        status = "traceability_pending"
    projection = {
        "projection_ref": projection_ref,
        "ssot_ref": resolved_ssot_ref,
        "template_version": template["version"],
        "review_stage": review_stage,
        "review_blocks": _with_trace_refs(base_blocks, marker_result["block_trace_refs"]) + [snapshot["block"]] + prompt_blocks,
        "derived_markers": marker_result["derived_markers"],
        "trace_refs": marker_result["trace_refs"],
        "derived_only": True,
        "non_authoritative": True,
        "non_inheritable": True,
        "status": status,
        "traceability_notes": marker_result["traceability_notes"],
        "snapshot_ref": snapshot["snapshot_ref"],
        "focus_ref": focus_result["focus_ref"],
    }
    write_json(workspace_root / projection_ref, projection)
    return projection


def build_gate_human_projection(
    workspace_root: Path,
    payload: dict[str, Any],
    decision_target: str,
    findings: list[dict[str, object]],
) -> dict[str, Any]:
    ssot_ref = _resolve_ssot_ref(payload, decision_target)
    if not ssot_ref:
        return _unavailable_projection("", "ssot_not_ready", findings)
    try:
        projection = render_projection(
            workspace_root,
            {
                "ssot_ref": ssot_ref,
                "template_version": payload.get("template_version", DEFAULT_TEMPLATE_VERSION),
                "review_stage": payload.get("review_stage", "gate_review"),
            },
        )
    except ProjectionRenderError as exc:
        return _unavailable_projection(ssot_ref, str(exc), findings)
    projection["finding_count"] = len(findings)
    return projection


def load_machine_ssot(workspace_root: Path, ssot_ref: str) -> tuple[dict[str, Any], str]:
    try:
        record = resolve_registry_record(workspace_root, ssot_ref)
        payload_path = canonical_to_path(str(record["managed_artifact_ref"]), workspace_root)
        return _load_payload(payload_path), str(record["artifact_ref"])
    except Exception:
        payload_path = canonical_to_path(ssot_ref, workspace_root)
        return _load_payload(payload_path), ssot_ref


def _load_payload(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        return load_json(path)
    return {"raw_text": read_text(path)}


def _projection_ref(projection_key: object, ssot_ref: str, template_version: str, review_stage: str) -> str:
    key = str(projection_key or f"{ssot_ref}-{template_version}-{review_stage}")
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"artifacts/active/gates/projections/{slugify(ssot_ref)}-{digest}.json"


def _resolve_ssot_ref(payload: dict[str, Any], decision_target: str) -> str:
    for field in ("ssot_ref", "machine_ssot_ref", "candidate_ref", "artifact_ref"):
        value = str(payload.get(field, "")).strip()
        if value:
            return value
    return decision_target


def _is_freeze_ready(ssot_payload: dict[str, Any]) -> bool:
    explicit = ssot_payload.get("freeze_ready")
    if explicit is False:
        return False
    status = str(ssot_payload.get("status", "")).strip().lower()
    return status not in {"draft", "not_ready", "blocked"}


def _with_trace_refs(base_blocks: list[dict[str, Any]], trace_map: dict[str, list[str]]) -> list[dict[str, Any]]:
    traced_blocks: list[dict[str, Any]] = []
    for block in base_blocks:
        cloned = dict(block)
        cloned["source_trace_refs"] = trace_map.get(block["id"], [])
        traced_blocks.append(cloned)
    return traced_blocks


def _unavailable_projection(ssot_ref: str, reason: str, findings: list[dict[str, object]]) -> dict[str, Any]:
    return {
        "projection_ref": "",
        "ssot_ref": ssot_ref,
        "template_version": DEFAULT_TEMPLATE_VERSION,
        "review_stage": "gate_review",
        "review_blocks": [
            {
                "id": "projection_unavailable",
                "title": "Human Review Projection",
                "content": [
                    "Projection is unavailable for this gate round; inspect Machine SSOT directly before deciding.",
                    f"Reason: {reason}",
                ],
                "status": reason,
                "source_trace_refs": [ssot_ref] if ssot_ref else [],
            }
        ],
        "derived_markers": {
            "derived_only": True,
            "non_authoritative": True,
            "non_inheritable": True,
            "template_version": DEFAULT_TEMPLATE_VERSION,
            "source_ssot_ref": ssot_ref,
            "projection_ref": "",
        },
        "trace_refs": [ssot_ref] if ssot_ref else [],
        "derived_only": True,
        "non_authoritative": True,
        "non_inheritable": True,
        "status": reason,
        "finding_count": len(findings),
    }
