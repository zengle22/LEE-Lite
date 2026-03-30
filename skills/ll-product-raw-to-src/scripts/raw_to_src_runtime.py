#!/usr/bin/env python3
"""
Runtime orchestration for raw-to-src.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from raw_to_src_agent_phases import executor_run, supervisor_review
from raw_to_src_common import render_candidate_markdown
from raw_to_src_runtime_support import collect_evidence_report, validate_output_package, validate_package_readiness


def repo_root_from(arg: str | None) -> Path:
    return Path(arg).resolve() if arg else Path(__file__).resolve().parents[3]


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _freeze_source_input(input_path: Path, artifacts_dir: Path, repo_root: Path) -> dict[str, object]:
    input_dir = artifacts_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    frozen_name = f"source-input{input_path.suffix.lower()}"
    frozen_path = input_dir / frozen_name
    shutil.copy2(input_path, frozen_path)

    payload = frozen_path.read_bytes()
    content_hash = hashlib.sha256(payload).hexdigest()
    metadata = {
        "run_id": artifacts_dir.name,
        "captured_at": _iso_now(),
        "source_path": str(input_path),
        "frozen_ref": str(frozen_path.resolve().relative_to(repo_root.resolve()).as_posix()),
        "frozen_name": frozen_name,
        "source_size_bytes": frozen_path.stat().st_size,
        "source_hash_algo": "sha256",
        "source_hash": content_hash,
        "source_suffix": input_path.suffix.lower(),
    }
    snapshot_path = input_dir / "source-snapshot.json"
    snapshot_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metadata["frozen_snapshot_ref"] = str(snapshot_path.resolve().relative_to(repo_root.resolve()).as_posix())
    return metadata


def _augment_candidate_with_source_snapshot(candidate_path: Path, snapshot_metadata: dict[str, object]) -> dict[str, object]:
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    source_snapshot = candidate.get("source_snapshot") or {}
    capture_metadata = source_snapshot.get("capture_metadata") or {}
    capture_metadata.update(
        {
            "captured_at": snapshot_metadata.get("captured_at", capture_metadata.get("captured_at")),
            "frozen_ref": snapshot_metadata.get("frozen_ref", capture_metadata.get("frozen_ref", "")),
            "frozen_snapshot_ref": snapshot_metadata.get("frozen_snapshot_ref", capture_metadata.get("frozen_snapshot_ref", "")),
            "content_hash": snapshot_metadata.get("source_hash", capture_metadata.get("content_hash", "")),
            "content_hash_algo": snapshot_metadata.get("source_hash_algo", capture_metadata.get("content_hash_algo", "sha256")),
            "source_size_bytes": snapshot_metadata.get("source_size_bytes", capture_metadata.get("source_size_bytes")),
            "source_path": snapshot_metadata.get("source_path", capture_metadata.get("source_path", "")),
        }
    )
    source_snapshot["capture_metadata"] = capture_metadata
    source_snapshot.setdefault("source_path", snapshot_metadata.get("source_path", ""))
    candidate["source_snapshot"] = source_snapshot

    provenance = candidate.get("source_provenance_map") or []
    snapshot_row_found = False
    for row in provenance:
        if row.get("target_field") == "source_snapshot":
            row["frozen_ref"] = str(snapshot_metadata.get("frozen_ref", row.get("frozen_ref", "")))
            row["preservation_mode"] = "frozen_snapshot"
            snapshot_row_found = True
    if not snapshot_row_found:
        provenance.append(
            {
                "target_field": "source_snapshot",
                "source_ref": (candidate.get("source_refs") or [candidate_path.name])[0],
                "source_section": "source_snapshot",
                "source_excerpt": str(source_snapshot.get("title") or candidate.get("title") or ""),
                "preservation_mode": "frozen_snapshot",
                "frozen_ref": str(snapshot_metadata.get("frozen_ref", "")),
            }
        )
    candidate["source_provenance_map"] = provenance
    candidate_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    candidate_path.with_suffix(".md").write_text(render_candidate_markdown(candidate), encoding="utf-8")
    return candidate


def run_workflow(
    input_path: Path,
    repo_root: Path,
    run_id: str,
    allow_update: bool,
    revision_request_path: Path | None = None,
) -> dict[str, object]:
    executor_result = executor_run(
        input_path=input_path,
        repo_root=repo_root,
        run_id=run_id,
        revision_request_path=revision_request_path,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    snapshot_metadata = _freeze_source_input(input_path, artifacts_dir, repo_root)
    _augment_candidate_with_source_snapshot(artifacts_dir / "src-candidate.json", snapshot_metadata)
    return supervisor_review(
        artifacts_dir=artifacts_dir,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
    )
