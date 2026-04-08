"""SSOT backport apply helpers for ADR-044 reconcile-as-apply (Phase 1)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

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
    - Target path line is optional:
        path: ssot/...
      When omitted, the caller must resolve the target from findings/queue.
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
        ssot_path = str(path_match.group("path") or "").strip() if path_match else ""
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


def resolve_ssot_update_paths(
    updates: list[ParsedSsotUpdate],
    *,
    target_paths_by_finding_id: dict[str, list[str]],
) -> list[ParsedSsotUpdate]:
    """Fill missing ssot_path fields using a finding_id -> candidate targets map.

    Candidate targets may include anchors (e.g. ssot/foo/bar.yaml#section). When
    resolving, we keep the raw target string on ParsedSsotUpdate so receipts stay
    auditable, but we require that the target identifies exactly one ssot file.
    """

    resolved: list[ParsedSsotUpdate] = []
    for update in updates:
        if str(update.ssot_path or "").strip():
            resolved.append(update)
            continue
        candidates = [str(item).strip() for item in (target_paths_by_finding_id.get(update.finding_id) or []) if str(item).strip()]
        ssot_candidates = [item for item in candidates if item.startswith("ssot/")]
        unique_files: list[str] = []
        for candidate in ssot_candidates:
            file_part = candidate.split("#", 1)[0].strip()
            if file_part and file_part not in unique_files:
                unique_files.append(file_part)
        ensure(bool(unique_files), "INVALID_REQUEST", f"ssot_updates block {update.finding_id} missing path and no ssot targets available")
        ensure(len(unique_files) == 1, "INVALID_REQUEST", f"ssot_updates block {update.finding_id} missing path and has ambiguous ssot targets: {', '.join(unique_files)}")
        # Prefer the first ssot candidate string (may contain anchor) that matches the unique file.
        chosen = next((item for item in ssot_candidates if item.split('#', 1)[0].strip() == unique_files[0]), unique_files[0])
        resolved.append(
            ParsedSsotUpdate(
                finding_id=update.finding_id,
                ssot_path=chosen,
                content=update.content,
                content_format=update.content_format,
            )
        )
    return resolved


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = dict(base)
        for key, value in patch.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
    return patch


def _apply_yaml_patch(existing_bytes: bytes, patch_text: str) -> bytes:
    existing_obj: Any = {}
    if existing_bytes:
        existing_obj = yaml.safe_load(existing_bytes.decode("utf-8"))
    if existing_obj is None:
        existing_obj = {}
    patch_obj = yaml.safe_load(patch_text or "")
    ensure(isinstance(patch_obj, dict), "INVALID_REQUEST", "yaml-patch content must be a YAML mapping/object")
    if existing_obj is None:
        existing_obj = {}
    ensure(isinstance(existing_obj, dict), "INVALID_REQUEST", "target YAML must be a mapping/object for yaml-patch")
    merged = _deep_merge(existing_obj, patch_obj)
    rendered = yaml.safe_dump(merged, allow_unicode=True, sort_keys=False)
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered.encode("utf-8")


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
            ssot_path_value = str(update.ssot_path or "").strip()
            ensure(bool(ssot_path_value), "INVALID_REQUEST", f"ssot_updates missing ssot_path for {finding_id}")
            target_file = ssot_path_value.split("#", 1)[0].strip()
            ensure(target_file.startswith("ssot/"), "INVALID_REQUEST", f"ssot_updates path must start with ssot/: {ssot_path_value}")
            target_path = (workspace_root / target_file).resolve()
            try:
                target_path.relative_to(ssot_root)
            except ValueError as exc:
                raise CommandError("INVALID_REQUEST", f"ssot_updates path must stay under ssot/: {ssot_path_value}") from exc

            before_bytes = target_path.read_bytes() if target_path.exists() else b""
            before_sha = _sha256_bytes(before_bytes) if before_bytes else ""
            content_format = str(update.content_format or "").strip().lower()
            if content_format in {"yaml-patch", "yml-patch"}:
                after_bytes = _apply_yaml_patch(before_bytes, update.content)
                write_text(target_path, after_bytes.decode("utf-8"), mode="w")
            else:
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
                    "ssot_path": ssot_path_value,
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
