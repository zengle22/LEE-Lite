"""Projection regeneration after authoritative SSOT updates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.fs import canonical_to_path, load_json, write_json
from cli.lib.review_projection.renderer import ProjectionRenderError, render_projection


class ProjectionRegenerationError(RuntimeError):
    """Raised when a regenerated projection cannot be produced."""


def request_projection_regeneration(
    workspace_root: Path,
    revision_request_ref: str,
    updated_ssot_ref: str,
    template_version: str = "v1",
    review_stage: str = "gate_review",
) -> dict[str, Any]:
    revision_path = canonical_to_path(revision_request_ref, workspace_root)
    revision_request = load_json(revision_path)
    if "regenerated_projection_ref" in revision_request:
        return revision_request
    updated_path = canonical_to_path(updated_ssot_ref, workspace_root)
    if not updated_path.exists():
        revision_request["status"] = "projection_regeneration_pending"
        revision_request["current_projection_allowed"] = False
        write_json(revision_path, revision_request)
        raise ProjectionRegenerationError("ssot_update_missing")
    try:
        projection = render_projection(
            workspace_root,
            {
                "ssot_ref": updated_ssot_ref,
                "template_version": template_version,
                "review_stage": review_stage,
                "projection_key": f"{revision_request_ref}-{updated_ssot_ref}",
            },
        )
    except ProjectionRenderError as exc:
        revision_request["status"] = "projection_regeneration_pending"
        revision_request["current_projection_allowed"] = False
        write_json(revision_path, revision_request)
        raise ProjectionRegenerationError(str(exc)) from exc
    revision_request["updated_ssot_ref"] = updated_ssot_ref
    revision_request["regenerated_projection_ref"] = projection["projection_ref"]
    revision_request["status"] = "projection_regenerated"
    revision_request["current_projection_allowed"] = True
    write_json(revision_path, revision_request)
    return revision_request
