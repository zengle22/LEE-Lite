"""Shared FEAT input resolution for downstream workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.admission import validate_admission
from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path
from cli.lib.registry_store import resolve_registry_record


def guess_repo_root_from_input(input_path: Path) -> Path:
    parts = list(input_path.parts)
    for index, part in enumerate(parts):
        if part.lower() == "artifacts" and index > 0:
            return Path(*parts[:index])
    return input_path.parent


def _fallback_source_package_dir(repo_root: Path, record: dict[str, Any]) -> Path | None:
    trace = record.get("trace", {}) if isinstance(record.get("trace"), dict) else {}
    run_ref = str(trace.get("run_ref") or "").strip()
    if not run_ref:
        return None
    candidate = (repo_root / "artifacts" / "epic-to-feat" / run_ref).resolve()
    if candidate.exists() and candidate.is_dir():
        return candidate
    return None


def resolve_feat_input_artifacts_dir(
    input_value: str | Path,
    repo_root: Path,
    *,
    consumer_ref: str,
) -> tuple[Path, dict[str, Any]]:
    candidate_path = Path(str(input_value))
    if candidate_path.exists() and candidate_path.is_dir():
        resolved = candidate_path.resolve()
        return resolved, {"input_mode": "package_dir", "requested_ref": str(resolved)}

    requested_ref = str(input_value).strip()
    ensure(requested_ref, "INVALID_REQUEST", "feat input ref is required")
    admission = validate_admission(repo_root, consumer_ref=consumer_ref, requested_ref=requested_ref)
    record = resolve_registry_record(repo_root, requested_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}

    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    if source_package_ref:
        artifacts_dir = canonical_to_path(source_package_ref, repo_root)
    else:
        artifacts_dir = _fallback_source_package_dir(repo_root, record)
        ensure(
            artifacts_dir is not None,
            "PRECONDITION_FAILED",
            "formal feat record is missing metadata.source_package_ref and no trace-run fallback exists",
        )

    ensure(
        artifacts_dir.exists() and artifacts_dir.is_dir(),
        "PRECONDITION_FAILED",
        f"resolved feat package directory not found: {artifacts_dir}",
    )
    return artifacts_dir.resolve(), {
        "input_mode": "formal_admission",
        "requested_ref": requested_ref,
        "resolved_formal_ref": admission.get("resolved_formal_ref", ""),
        "managed_artifact_ref": record.get("managed_artifact_ref", ""),
        "resolved_feat_ref": str(metadata.get("feat_ref") or metadata.get("assigned_id") or "").strip(),
        "source_package_ref": source_package_ref or "",
    }
