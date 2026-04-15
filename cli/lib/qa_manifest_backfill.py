"""Atomic manifest backfill module.

Updates api-coverage-manifest.yaml with execution results after test runs.
Follows immutability pattern: read full manifest -> build new dict -> write atomically.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from cli.lib.qa_schemas import validate_manifest


def backfill_manifest(
    manifest_path: str | Path,
    results: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    """Atomically update manifest with execution results.

    Args:
        manifest_path: Path to api-coverage-manifest.yaml
        results: List of dicts with keys:
            - coverage_id: str
            - passed: bool
            - evidence_path: str (relative path to evidence YAML)
        run_id: Execution run identifier (e.g., "run-1234567890-12345")

    Returns:
        Dict with updated_count, run_id, manifest_path
    """
    manifest_p = Path(manifest_path)
    if not manifest_p.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_p}")

    # Read and validate current manifest
    with open(manifest_p, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    manifest = validate_manifest(raw)

    # Build a lookup from results by coverage_id
    results_map: dict[str, dict[str, Any]] = {}
    for r in results:
        _require_result_keys(r)
        results_map[r["coverage_id"]] = r

    # Build new items list (immutability: new list, new dicts)
    new_items: list[dict[str, Any]] = []
    updated_count = 0

    for item in manifest.items:
        item_dict = _manifest_item_to_dict(item)
        cov_id = item.coverage_id

        if cov_id in results_map:
            result = results_map[cov_id]
            item_dict["lifecycle_status"] = "passed" if result["passed"] else "failed"
            item_dict["evidence_status"] = "complete"

            # Append evidence_path to evidence_refs
            existing_refs = list(item_dict.get("evidence_refs") or [])
            existing_refs.append(result["evidence_path"])
            item_dict["evidence_refs"] = existing_refs

            item_dict["last_run_id"] = run_id
            item_dict["rerun_count"] = item.rerun_count + 1
            updated_count += 1

        new_items.append(item_dict)

    # Write to temp file first, then os.replace() for atomicity
    new_manifest = {"api_coverage_manifest": {"items": new_items}}

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".tmp",
        dir=str(manifest_p.parent),
        delete=False,
        encoding="utf-8",
    ) as tmp:
        yaml.safe_dump(new_manifest, tmp, sort_keys=False, allow_unicode=True)
        tmp_path = tmp.name

    try:
        # Re-validate before replacing
        with open(tmp_path, encoding="utf-8") as f:
            recheck = yaml.safe_load(f) or {}
        validate_manifest(recheck)

        os.replace(tmp_path, str(manifest_p))
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    return {
        "updated_count": updated_count,
        "run_id": run_id,
        "manifest_path": str(manifest_p),
    }


def _manifest_item_to_dict(item) -> dict[str, Any]:
    """Convert a ManifestItem dataclass to a plain dict for YAML writing."""
    return {
        "coverage_id": item.coverage_id,
        "feature_id": item.feature_id,
        "capability": item.capability,
        "endpoint": item.endpoint,
        "scenario_type": item.scenario_type,
        "priority": item.priority,
        "source_feat_ref": item.source_feat_ref,
        "dimensions_covered": item.dimensions_covered,
        "mapped_case_ids": item.mapped_case_ids,
        "lifecycle_status": item.lifecycle_status,
        "mapping_status": item.mapping_status,
        "evidence_status": item.evidence_status,
        "waiver_status": item.waiver_status,
        "evidence_refs": item.evidence_refs,
        "rerun_count": item.rerun_count,
        "last_run_id": item.last_run_id,
        "obsolete": item.obsolete,
        "superseded_by": item.superseded_by,
    }


def _require_result_keys(result: dict[str, Any]) -> None:
    """Validate that a result dict has the required keys."""
    for key in ("coverage_id", "passed", "evidence_path"):
        if key not in result:
            raise ValueError(f"Result missing required key '{key}': {result}")
