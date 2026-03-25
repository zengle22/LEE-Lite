"""Formal publication helpers built on the managed gateway."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.managed_gateway import commit_governed


def publish_formal(
    workspace_root: Path,
    payload: dict[str, Any],
    trace: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    formal_payload = dict(payload)
    metadata = dict(formal_payload.get("metadata", {}))
    metadata.setdefault("layer", "formal")
    formal_payload["metadata"] = metadata
    formal_payload["status_override"] = "materialized"
    result = commit_governed(workspace_root, formal_payload, trace, "publish-formal", request_id)
    result["formal_artifact_ref"] = str(payload.get("artifact_ref", ""))
    return result
