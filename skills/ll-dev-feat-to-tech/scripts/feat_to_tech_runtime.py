#!/usr/bin/env python3
"""
Lite-native runtime support for feat-to-tech.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feat_to_tech_cli_integration import (
    build_gate_result,
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    write_executor_outputs,
)
from feat_to_tech_common import (
    dump_json,
    ensure_list,
    find_feature,
    guess_repo_root_from_input,
    load_feat_package,
    load_json,
    normalize_semantic_lock,
    resolve_input_artifacts_dir,
    validate_input_package,
)
from feat_to_tech_gate_integration import (
    create_gate_ready_package,
    create_handoff_proposal,
    submit_gate_pending,
)
from feat_to_tech_package_builder import GeneratedTechPackage, build_tech_package
from feat_to_tech_validation import validate_output_package
DOWNSTREAM_WORKFLOW = "workflow.dev.tech_to_impl"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def repo_root_from(repo_root: str | None, input_path: str | Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        candidate = Path(str(input_path))
        if candidate.exists():
            return guess_repo_root_from_input(candidate.resolve())
    return Path.cwd().resolve()

def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "feat-to-tech" / run_id


def repo_relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def display_list(values: list[str]) -> str:
    items = [str(item).strip() for item in values if str(item).strip()]
    return ", ".join(items) if items else "None"



def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if errors:
        return False, errors
    gate = load_json(artifacts_dir / "tech-freeze-gate.json")
    checks = gate.get("checks") or {}
    readiness_errors = [name for name, status in checks.items() if status is not True]
    return not readiness_errors, readiness_errors

def executor_run(input_path: str | Path, feat_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, feat_ref, repo_root)
    if errors:
        raise ValueError("; ".join(errors))

    resolved_input_dir, _ = resolve_input_artifacts_dir(input_path, repo_root)
    package = load_feat_package(resolved_input_dir)
    effective_feat_ref = str(validation.get("feat_ref") or feat_ref).strip()
    feature = find_feature(package, effective_feat_ref)
    if feature is None:
        raise ValueError(f"Selected feat_ref not found: {effective_feat_ref}")
    feature = dict(feature)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)

    effective_run_id = run_id or f"{package.run_id}--{effective_feat_ref.lower()}"
    generated = build_tech_package(package, feature, effective_feat_ref, effective_run_id, utc_now)
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    write_executor_outputs(output_dir, repo_root, package, generated, f"python scripts/feat_to_tech.py executor-run --input {input_path} --feat-ref {effective_feat_ref}")
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "input_mode": validation.get("input_mode", "package_dir"),
        "feat_ref": effective_feat_ref,
        "tech_ref": generated.json_payload["tech_ref"],
    }

def supervisor_review(artifacts_dir: Path, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    del allow_update
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts directory not found: {artifacts_dir}")

    package_manifest = load_json(artifacts_dir / "package-manifest.json")
    input_package_dir = Path(str(package_manifest.get("input_artifacts_dir") or "")).resolve()
    feat_ref = str(package_manifest.get("feat_ref") or "").strip()
    if not input_package_dir.exists():
        raise FileNotFoundError(f"Input package directory not found: {input_package_dir}")
    if not feat_ref:
        raise ValueError("package-manifest.json is missing feat_ref.")

    package = load_feat_package(input_package_dir)
    feature = find_feature(package, feat_ref)
    if feature is None:
        raise ValueError(f"Selected feat_ref not found: {feat_ref}")
    feature = dict(feature)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)
    effective_run_id = run_id or artifacts_dir.name
    generated = build_tech_package(package, feature, feat_ref, effective_run_id, utc_now)
    supervision = build_supervision_evidence(artifacts_dir, generated)
    gate = build_gate_result(generated, supervision)
    update_supervisor_outputs(artifacts_dir, repo_root, generated, supervision, gate)

    proposal_ref = ""
    gate_ready_package_ref = ""
    authoritative_handoff_ref = ""
    gate_pending_ref = ""
    if gate["freeze_ready"]:
        proposal_path = create_handoff_proposal(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=effective_run_id,
            feat_ref=feat_ref,
            tech_ref=str(generated.json_payload["tech_ref"]),
        )
        gate_ready_package = create_gate_ready_package(
            artifacts_dir=artifacts_dir,
            run_id=effective_run_id,
            candidate_ref=f"feat-to-tech.{effective_run_id}.tech-design-bundle",
            machine_ssot_ref=repo_relative(repo_root, artifacts_dir / "tech-design-bundle.json"),
            acceptance_ref=repo_relative(repo_root, artifacts_dir / "tech-acceptance-report.json"),
            evidence_bundle_ref=repo_relative(repo_root, artifacts_dir / "supervision-evidence.json"),
        )
        gate_submit = submit_gate_pending(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=effective_run_id,
            proposal_ref=repo_relative(repo_root, proposal_path),
            payload_path=gate_ready_package,
            trace_context_ref=repo_relative(repo_root, artifacts_dir / "execution-evidence.json"),
        )
        gate_submit_data = gate_submit["response"]["data"]
        manifest = load_json(artifacts_dir / "package-manifest.json")
        manifest["handoff_proposal_ref"] = repo_relative(repo_root, proposal_path)
        manifest["gate_ready_package_ref"] = repo_relative(repo_root, gate_ready_package)
        manifest["authoritative_handoff_ref"] = str(gate_submit_data.get("handoff_ref", ""))
        manifest["gate_pending_ref"] = str(gate_submit_data.get("gate_pending_ref", ""))
        manifest["gate_submit_cli_ref"] = repo_relative(repo_root, gate_submit["response_path"])
        dump_json(artifacts_dir / "package-manifest.json", manifest)
        proposal_ref = manifest["handoff_proposal_ref"]
        gate_ready_package_ref = manifest["gate_ready_package_ref"]
        authoritative_handoff_ref = manifest["authoritative_handoff_ref"]
        gate_pending_ref = manifest["gate_pending_ref"]

    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "freeze_ready": gate["freeze_ready"],
        "handoff_proposal_ref": proposal_ref,
        "gate_ready_package_ref": gate_ready_package_ref,
        "authoritative_handoff_ref": authoritative_handoff_ref,
        "gate_pending_ref": gate_pending_ref,
    }

def run_workflow(input_path: str | Path, feat_ref: str, repo_root: Path, run_id: str, allow_update: bool = False) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        feat_ref=feat_ref,
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
        "input_mode": executor_result.get("input_mode", "package_dir"),
        "feat_ref": executor_result["feat_ref"],
        "tech_ref": executor_result["tech_ref"],
        "supervision": supervisor_result,
        "handoff_proposal_ref": supervisor_result.get("handoff_proposal_ref", ""),
        "gate_ready_package_ref": supervisor_result.get("gate_ready_package_ref", ""),
        "authoritative_handoff_ref": supervisor_result.get("authoritative_handoff_ref", ""),
        "gate_pending_ref": supervisor_result.get("gate_pending_ref", ""),
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }
