#!/usr/bin/env python3
"""
Lite-native runtime support for tech-to-impl.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tech_to_impl_builder import build_candidate_package
from tech_to_impl_common import guess_repo_root_from_input, load_tech_package, slugify, validate_input_package
from tech_to_impl_review import (
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    validate_output_package,
    validate_package_readiness,
    write_executor_outputs,
)


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "tech-to-impl" / run_id


def default_run_id(package: Any, tech_ref: str) -> str:
    candidate = f"{package.run_id}--{slugify(tech_ref).lower()}"
    # Keep artifact paths comfortably below Windows path-length trouble spots.
    if len(candidate) <= 80:
        return candidate
    tail = slugify(tech_ref).lower().split("-")[-1]
    digest = hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:8]
    base = slugify(package.run_id).lower()[:48].rstrip("-")
    return f"{base}--{tail}-{digest}"


def executor_run(input_path: Path, feat_ref: str, tech_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, feat_ref, tech_ref)
    if errors:
        raise ValueError("; ".join(errors))

    package = load_tech_package(input_path)
    effective_run_id = run_id or default_run_id(package, tech_ref)
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    generated = build_candidate_package(package, effective_run_id)
    write_executor_outputs(
        output_dir,
        package,
        generated,
        f"python scripts/tech_to_impl.py executor-run --input {input_path} --feat-ref {feat_ref} --tech-ref {tech_ref}",
    )
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "impl_ref": generated["bundle_json"]["impl_ref"],
    }


def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del repo_root, run_id, allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    supervision = build_supervision_evidence(artifacts_dir)
    update_supervisor_outputs(artifacts_dir, supervision)
    from tech_to_impl_common import load_json

    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    return {
        "ok": True,
        "run_id": supervision["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "execution_ready": smoke_gate.get("ready_for_execution") is True,
    }


def run_workflow(input_path: Path, feat_ref: str, tech_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        feat_ref=feat_ref,
        tech_ref=tech_ref,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(artifacts_dir, repo_root, run_id or executor_result["run_id"], allow_update=True)
    output_errors, output_result = validate_output_package(artifacts_dir)
    if output_errors:
        raise ValueError("; ".join(output_errors))
    readiness_ok, readiness_errors = validate_package_readiness(artifacts_dir)
    report_path = collect_evidence_report(artifacts_dir)
    return {
        "ok": readiness_ok,
        "run_id": executor_result["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "feat_ref": feat_ref,
        "tech_ref": tech_ref,
        "impl_ref": executor_result["impl_ref"],
        "supervision": supervisor_result,
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }

