"""Revision request creation for projection writeback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.fs import load_json, write_json
from cli.lib.registry_store import slugify


def create_revision_request(
    workspace_root: Path,
    projection_ref: str,
    comment_ref: str,
    comment_text: str,
    comment_author: str,
    mapped_field_refs: list[str],
) -> dict[str, Any]:
    revision_request_ref = f"artifacts/active/gates/revision-requests/{slugify(comment_ref)}.json"
    target = workspace_root / revision_request_ref
    if target.exists():
        return load_json(target)
    revision_request = {
        "revision_request_ref": revision_request_ref,
        "projection_ref": projection_ref,
        "comment_ref": comment_ref,
        "mapped_field_refs": mapped_field_refs,
        "status": "ssot_revision_requested",
        "comment_provenance": {
            "comment_text": comment_text,
            "comment_author": comment_author,
        },
    }
    write_json(target, revision_request)
    return revision_request
