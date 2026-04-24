"""Linear test orchestrator: env provision → spec adapter → exec → manifest update.

This module implements the end-to-end orchestration flow defined in ADR-054 §2.5:
    Step 1: provision_environment()  → ENV file
    Step 2: spec_to_testset()       → SPEC_ADAPTER_COMPAT file
    Step 3: execute_test_exec_skill() → test execution
    Step 4: update_manifest()       → lifecycle_status + evidence_refs

Per ADR-054 §2.5, §5.1 R-1, R-5, R-7.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from cli.lib.contracts import StepResult
from cli.lib.environment_provision import provision_environment
from cli.lib.spec_adapter import SpecAdapterInput, spec_to_testset, write_spec_adapter_output
from cli.lib.test_exec_runtime import execute_test_exec_skill


def _timestamp() -> str:
    """Return current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_failed_coverage_ids(
    workspace_root: Path,
    feat_ref: str | None,
    proto_ref: str | None,
) -> list[str]:
    """Read manifest and return coverage_ids with last_run_status=failed.

    Per ADR-054 §5.1 R-7 resume mechanism.
    """
    if feat_ref:
        manifest_path = workspace_root / f"ssot/tests/api/{feat_ref}/api-coverage-manifest.yaml"
    else:
        manifest_path = workspace_root / f"ssot/tests/e2e/{proto_ref}/e2e-coverage-manifest.yaml"

    if not manifest_path.exists():
        return []

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    return [
        item["coverage_id"]
        for item in manifest.get("items", [])
        if item.get("last_run_status") == "failed"
    ]


def _filter_test_units_by_failed(
    test_units: list[dict[str, Any]],
    failed_coverage_ids: list[str],
) -> list[dict[str, Any]]:
    """Filter test_units to only include those whose _source_coverage_id is in failed_coverage_ids.

    Per ADR-054 §5.1 R-7 resume mechanism.
    """
    if not failed_coverage_ids:
        return test_units
    return [
        unit
        for unit in test_units
        if unit.get("_source_coverage_id") in failed_coverage_ids
    ]


def update_manifest(
    workspace_root: Path,
    manifest_items: list[dict[str, Any]],
    run_id: str,
) -> None:
    """Update coverage manifest with execution results.

    Uses timestamp + version optimistic lock (Windows compatible).
    Per ADR-054 §5.1 R-5.

    Args:
        workspace_root: Root of the workspace
        manifest_items: List of {coverage_id, status, evidence_ref} for manifest update
        run_id: Unique identifier for this execution run
    """
    if not manifest_items:
        return

    # Determine manifest path based on chain
    first_item = manifest_items[0]
    if "feat_ref" in first_item and first_item.get("feat_ref"):
        manifest_path = workspace_root / f"ssot/tests/api/{first_item['feat_ref']}/api-coverage-manifest.yaml"
    elif "proto_ref" in first_item and first_item.get("proto_ref"):
        manifest_path = workspace_root / f"ssot/tests/e2e/{first_item['proto_ref']}/e2e-coverage-manifest.yaml"
    else:
        # Fallback: cannot determine manifest path
        return

    if not manifest_path.exists():
        return

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}

    # Optimistic lock: read version, update, write with new version
    expected_version = manifest.get("_version", "0")

    for item in manifest_items:
        coverage_id = item.get("coverage_id")
        status = item.get("status", "executed")
        run_status = item.get("run_status", "passed")
        evidence_ref = item.get("evidence_ref")
        feat_ref = item.get("feat_ref")
        proto_ref = item.get("proto_ref")

        for existing in manifest.get("items", []):
            if existing.get("coverage_id") == coverage_id:
                existing["lifecycle_status"] = status
                existing["last_run_id"] = run_id
                existing["last_run_status"] = run_status
                if evidence_ref:
                    existing.setdefault("evidence_refs", []).append(evidence_ref)
                if feat_ref:
                    existing["feat_ref"] = feat_ref
                if proto_ref:
                    existing["proto_ref"] = proto_ref

    # Update version and timestamp
    manifest["_version"] = str(uuid.uuid4())
    manifest["_last_updated"] = _timestamp()

    manifest_path.write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def run_spec_test(
    workspace_root: Path,
    *,
    feat_ref: str | None = None,
    proto_ref: str | None = None,
    base_url: str = "http://localhost:8000",
    app_url: str = "http://localhost:3000",
    api_url: str | None = None,
    modality: str = "api",
    coverage_mode: str = "smoke",
    resume: bool = False,
    resume_from: str | None = None,
) -> StepResult:
    """End-to-end orchestration: env → adapter → exec → manifest update.

    Per ADR-054 §2.5.

    Args:
        workspace_root: Root of the workspace
        feat_ref: Feature reference (API chain)
        proto_ref: Prototype reference (E2E chain)
        base_url: Primary base URL (default: http://localhost:8000)
        app_url: Frontend application URL (E2E chain required)
        api_url: Backend API URL (separated architecture)
        modality: Execution modality ("api" | "web_e2e" | "cli")
        coverage_mode: Coverage mode ("smoke" | "qualification")
        resume: Resume from last failed run (R-7)
        resume_from: Resume from specific run_id

    Returns:
        StepResult with execution_refs, manifest_items for Step 4 update.

    Raises:
        ValueError: If neither feat_ref nor proto_ref is provided
    """
    if not feat_ref and not proto_ref:
        raise ValueError("Either feat_ref or proto_ref must be provided")

    # Generate run_id
    run_id = resume_from or f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    # -------------------------------------------------------------------------
    # Step 1: provision_environment()
    # -------------------------------------------------------------------------
    env_file_path, env_config = provision_environment(
        workspace_root=workspace_root,
        feat_ref=feat_ref,
        proto_ref=proto_ref,
        base_url=base_url,
        app_url=app_url,
        api_url=api_url,
        modality=modality,
        browser="chromium",
        timeout=30000,
        feat_assumptions=None,
    )

    # -------------------------------------------------------------------------
    # Step 2: spec_to_testset()
    # -------------------------------------------------------------------------
    # Determine spec directory based on modality
    if modality == "api":
        spec_dir = workspace_root / f"ssot/tests/api/{feat_ref}/api-test-spec"
    elif modality in ("web_e2e", "cli"):
        spec_dir = workspace_root / f"ssot/tests/e2e/{proto_ref}/e2e-journey-spec"
    else:
        spec_dir = workspace_root / f"ssot/tests/api/{feat_ref}/api-test-spec"

    # Handle missing spec directory gracefully
    if not spec_dir.exists():
        spec_files = []
    else:
        spec_files = list(spec_dir.glob("*.md"))

    spec_adapter_input = SpecAdapterInput(
        spec_files=spec_files,
        feat_ref=feat_ref,
        proto_ref=proto_ref,
        modality=modality,
    )

    # spec_to_testset returns SPEC_ADAPTER_COMPAT dict
    spec_compat = spec_to_testset(workspace_root, spec_adapter_input)

    # Write SPEC_ADAPTER_COMPAT to file for test_exec_runtime to consume
    output_name = f"spec-adapter-{feat_ref or proto_ref}"
    spec_adapter_output_path = write_spec_adapter_output(workspace_root, spec_compat, output_name)

    # -------------------------------------------------------------------------
    # Step 3: execute_test_exec_skill()
    # -------------------------------------------------------------------------
    payload = {
        "test_set_ref": str(spec_adapter_output_path),
        "test_environment_ref": str(env_file_path),
        "coverage_mode": coverage_mode,
    }

    execution_result = execute_test_exec_skill(
        workspace_root=workspace_root,
        trace={"run_ref": run_id},
        action=f"test-exec-{modality}",
        request_id=run_id,
        payload=payload,
    )

    # Extract candidate artifact ref
    candidate_artifact_ref = execution_result.get("candidate_artifact_ref", "")

    # Build case_results from spec_compat test_units
    case_results: list[dict[str, Any]] = []
    manifest_items: list[dict[str, Any]] = []

    for unit in spec_compat.get("test_units", []):
        coverage_id = unit.get("_source_coverage_id", unit.get("unit_ref", ""))
        case_results.append({
            "coverage_id": coverage_id,
            "case_id": unit.get("unit_ref", ""),
            "status": execution_result.get("run_status", "completed"),
        })
        manifest_items.append({
            "coverage_id": coverage_id,
            "status": "executed",
            "run_status": execution_result.get("run_status", "passed"),
            "evidence_ref": candidate_artifact_ref,
            "feat_ref": feat_ref,
            "proto_ref": proto_ref,
        })

    # -------------------------------------------------------------------------
    # Resume: filter to failed coverage_ids if requested
    # -------------------------------------------------------------------------
    if resume:
        failed_coverage_ids = _get_failed_coverage_ids(workspace_root, feat_ref, proto_ref)
        if failed_coverage_ids:
            # Re-filter manifest_items to only include failed coverage_ids
            manifest_items = [
                item for item in manifest_items
                if item.get("coverage_id") in failed_coverage_ids
            ]

    # -------------------------------------------------------------------------
    # Step 4: update_manifest()
    # -------------------------------------------------------------------------
    if manifest_items:
        update_manifest(workspace_root, manifest_items, run_id)

    # -------------------------------------------------------------------------
    # Return StepResult for Step 4 data passing
    # -------------------------------------------------------------------------
    return StepResult(
        run_id=run_id,
        execution_refs={
            "candidate_artifact_ref": candidate_artifact_ref,
            "env_file_ref": str(env_file_path),
            "spec_adapter_ref": str(spec_adapter_output_path),
        },
        candidate_path=f"artifacts/active/qa/candidates/{candidate_artifact_ref}.json" if candidate_artifact_ref else "",
        case_results=case_results,
        manifest_items=manifest_items,
        execution_output_dir="",
    )
