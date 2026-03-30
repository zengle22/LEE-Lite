#!/usr/bin/env python3
"""
Runtime orchestration for raw-to-src.
"""

from __future__ import annotations

from pathlib import Path

from raw_to_src_agent_phases import executor_run, supervisor_review
from raw_to_src_runtime_support import collect_evidence_report, validate_output_package, validate_package_readiness


def repo_root_from(arg: str | None) -> Path:
    return Path(arg).resolve() if arg else Path(__file__).resolve().parents[3]


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
    return supervisor_review(
        artifacts_dir=Path(executor_result["artifacts_dir"]),
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
    )
