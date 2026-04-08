"""SSOT backport apply helpers for ADR-044 reconcile-as-apply (Phase 1)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure
from cli.lib.fs import to_canonical_path, write_json, write_text


@dataclass(frozen=True)
class ParsedSsotUpdate:
    finding_id: str
    ssot_path: str
    content: str
    content_format: str


_FINDING_BLOCK_RE = re.compile(
    r"(?ms)^\s*\[?\s*(?:FINDING\s+)?(?P<finding_id>[A-Z][A-Z0-9_-]*-\d+)\s*\]?\s*:?\s*$"
    r"(?P<body>.*?)(?=^\s*\[?\s*(?:FINDING\s+)?[A-Z][A-Z0-9_-]*-\d+\s*\]?\s*:?\s*$|\Z)"
)
_PATH_RE = re.compile(r"(?mi)^\s*(?:path|target|file)\s*:\s*(?P<path>ssot/[^\s]+)\s*$")
_CODE_FENCE_RE = re.compile(r"(?ms)```(?P<fmt>[a-zA-Z0-9_-]+)?\s*\n(?P<content>.*?)\n```")


def parse_ssot_updates(text: str) -> list[ParsedSsotUpdate]:
    """Parse natural-language ssot_updates into structured write operations.

    v0 grammar (mechanical; natural language allowed in prose):

    - One or more blocks starting with a finding id heading, e.g.:
      - GAP-104:
      - [FINDING GAP-104]
    - Must include a target path line:
        path: ssot/...
    - Must include a fenced content block:
        ```yaml
        ...
        ```
    """

    normalized = str(text or "").strip()
    ensure(bool(normalized), "INVALID_REQUEST", "ssot_updates must be a non-empty string")

    updates: list[ParsedSsotUpdate] = []
    for match in _FINDING_BLOCK_RE.finditer(normalized):
        finding_id = str(match.group("finding_id") or "").strip()
        body = match.group("body") or ""
        if not finding_id:
            continue
        path_match = _PATH_RE.search(body)
        ensure(bool(path_match), "INVALID_REQUEST", f"ssot_updates block {finding_id} missing path: ssot/...")
        ssot_path = str(path_match.group("path") or "").strip()
        fence = _CODE_FENCE_RE.search(body)
        ensure(bool(fence), "INVALID_REQUEST", f"ssot_updates block {finding_id} missing fenced content ```...```")
        content_format = str(fence.group("fmt") or "").strip()
        content = fence.group("content") or ""
        updates.append(
            ParsedSsotUpdate(
                finding_id=finding_id,
                ssot_path=ssot_path,
                content=content,
                content_format=content_format,
            )
        )

    ensure(bool(updates), "INVALID_REQUEST", "ssot_updates did not contain any parseable finding blocks")
    return updates


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def apply_ssot_updates(
    workspace_root: Path,
    *,
    trace: dict[str, Any],
    request_id: str,
    decided_by: dict[str, str],
    updates: list[ParsedSsotUpdate],
) -> dict[str, list[str]]:
    """Apply updates to ssot/ and return finding_id -> ssot_patch_refs receipts."""

    ssot_root = (workspace_root / "ssot").resolve()
    grouped: dict[str, list[ParsedSsotUpdate]] = {}
    for update in updates:
        grouped.setdefault(update.finding_id, []).append(update)

    receipt_map: dict[str, list[str]] = {}
    now = datetime.now(timezone.utc).replace(microsecond=0)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    for finding_id, items in grouped.items():
        changed_files: list[dict[str, Any]] = []
        applied_updates: list[dict[str, Any]] = []
        for update in items:
            target_path = (workspace_root / update.ssot_path).resolve()
            try:
                target_path.relative_to(ssot_root)
            except ValueError as exc:
                raise CommandError("INVALID_REQUEST", f"ssot_updates path must stay under ssot/: {update.ssot_path}") from exc

            before_bytes = target_path.read_bytes() if target_path.exists() else b""
            before_sha = _sha256_bytes(before_bytes) if before_bytes else ""
            content = update.content
            if content and not content.endswith("\n"):
                content += "\n"
            write_text(target_path, content, mode="w")
            after_bytes = target_path.read_bytes()
            after_sha = _sha256_bytes(after_bytes)
            changed_files.append(
                {
                    "path": to_canonical_path(target_path, workspace_root),
                    "before_sha256": before_sha,
                    "after_sha256": after_sha,
                    "changed": before_sha != after_sha,
                }
            )
            applied_updates.append(
                {
                    "finding_id": finding_id,
                    "ssot_path": update.ssot_path,
                    "content_format": update.content_format,
                }
            )

        receipt_ref = f"artifacts/reports/governance/spec-backport/patch-receipts/{timestamp}--{finding_id}.json"
        receipt_path = workspace_root / receipt_ref
        write_json(
            receipt_path,
            {
                "artifact_type": "ssot_patch_receipt",
                "schema_version": "0.1.0",
                "status": "applied",
                "trace": {
                    "workflow_key": str(trace.get("workflow_key") or "governance.spec-reconcile"),
                    "run_ref": str(trace.get("run_ref") or request_id),
                    "request_id": request_id,
                    "applied_at": now.isoformat().replace("+00:00", "Z"),
                },
                "finding_id": finding_id,
                "decided_by": decided_by,
                "applied_updates": applied_updates,
                "changed_files": changed_files,
            },
        )
        receipt_map[finding_id] = [receipt_ref]

    return receipt_map


def merge_decisions_with_patch_receipts(
    decisions: list[dict[str, Any]],
    *,
    receipt_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Merge backport decisions with ssot_patch_refs evidence for applied updates."""

    by_id: dict[str, dict[str, Any]] = {str(item.get("finding_id") or "").strip(): dict(item) for item in decisions if isinstance(item, dict)}
    result: list[dict[str, Any]] = []

    for finding_id, patch_refs in receipt_map.items():
        ensure(bool(finding_id), "INTERNAL_ERROR", "invalid receipt finding_id")
        existing = by_id.get(finding_id, {})
        outcome = str(existing.get("outcome") or "").strip()
        if outcome and outcome == "rejected":
            raise CommandError("INVALID_REQUEST", f"ssot_updates conflicts with rejected decision for {finding_id}")
        merged = dict(existing)
        merged["finding_id"] = finding_id
        merged["outcome"] = "backported"
        merged.setdefault("ssot_patch_refs", [])
        existing_refs = [str(item).strip() for item in (merged.get("ssot_patch_refs") or []) if str(item).strip()]
        merged["ssot_patch_refs"] = list(dict.fromkeys([*existing_refs, *patch_refs]))
        by_id[finding_id] = merged

    for finding_id, item in by_id.items():
        if not finding_id:
            continue
        result.append(item)

    return sorted(result, key=lambda item: str(item.get("finding_id") or ""))

