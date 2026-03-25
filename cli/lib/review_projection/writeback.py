"""Comment writeback for review projections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.fs import canonical_to_path, load_json, write_json
from cli.lib.registry_store import slugify
from cli.lib.review_projection.revision_request import create_revision_request


class ProjectionWritebackError(RuntimeError):
    """Raised when a comment cannot be mapped back to Machine SSOT."""


def writeback_projection_comment(
    workspace_root: Path,
    projection_ref: str,
    comment_ref: str,
    comment_text: str,
    comment_author: str,
    target_block: str | None = None,
) -> dict[str, Any]:
    comment_path = workspace_root / _comment_ref(comment_ref)
    if comment_path.exists():
        cached = load_json(comment_path)
        if cached.get("revision_request_ref"):
            return cached
    projection = load_json(canonical_to_path(projection_ref, workspace_root))
    comment = {
        "comment_ref": comment_ref,
        "projection_ref": projection_ref,
        "comment_text": comment_text,
        "comment_author": comment_author,
        "target_block": target_block or "",
        "status": "review_comment_captured",
    }
    mapped_field_refs = _map_comment_to_ssot_fields(comment, projection)
    if not mapped_field_refs:
        comment["status"] = "comment_mapping_pending"
        write_json(comment_path, comment)
        raise ProjectionWritebackError("mapping_failed")
    revision_request = create_revision_request(
        workspace_root,
        projection_ref,
        comment_ref,
        comment_text,
        comment_author,
        mapped_field_refs,
    )
    comment["mapped_field_refs"] = mapped_field_refs
    comment["revision_request_ref"] = revision_request["revision_request_ref"]
    comment["status"] = "ssot_revision_requested"
    write_json(comment_path, comment)
    return comment


def _map_comment_to_ssot_fields(comment: dict[str, str], projection: dict[str, Any]) -> list[str]:
    target_block = comment.get("target_block", "").strip().lower()
    comment_text = comment.get("comment_text", "").lower()
    for block in projection.get("review_blocks", []):
        block_id = str(block.get("id", "")).lower()
        title = str(block.get("title", "")).lower()
        if target_block and target_block == block_id:
            return list(block.get("source_trace_refs", []))
        if not target_block and any(token in comment_text for token in block_id.split("_")):
            return list(block.get("source_trace_refs", []))
        if not target_block and title and title in comment_text:
            return list(block.get("source_trace_refs", []))
    return []


def _comment_ref(comment_ref: str) -> str:
    return f"artifacts/active/gates/comments/{slugify(comment_ref)}.json"
