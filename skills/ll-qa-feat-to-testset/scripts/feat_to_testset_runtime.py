#!/usr/bin/env python3
"""
Lite-native runtime support for feat-to-testset.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feat_to_testset_candidate import build_candidate_package, write_executor_outputs
from feat_to_testset_cli_integration import refresh_supervisor_bundle
from feat_to_testset_common import (
    dump_json,
    find_feature,
    guess_repo_root_from_input,
    load_feat_package,
    load_json,
    normalize_semantic_lock,
    resolve_input_artifacts_dir,
    validate_input_package,
)
from feat_to_testset_gate_integration import (
    create_gate_ready_package,
    create_handoff_proposal,
    submit_gate_pending,
)
from feat_to_testset_review import (
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    validate_output_package,
    validate_package_readiness,
)


DOWNSTREAM_WORKFLOW = "skill.qa.test_exec_cli"


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
    return repo_root / "artifacts" / "feat-to-testset" / run_id


def repo_relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _repo_relative_or_abs(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _load_revision_request(revision_request_path: str | Path | None, artifacts_dir: Path | None = None) -> tuple[dict[str, Any] | None, Path | None]:
    candidate_paths: list[Path] = []
    if revision_request_path:
        candidate_paths.append(Path(revision_request_path).resolve())
    if artifacts_dir is not None:
        candidate_paths.append((artifacts_dir / "revision-request.json").resolve())
    for candidate in candidate_paths:
        if candidate.exists():
            payload = load_json(candidate)
            if isinstance(payload, dict):
                return payload, candidate
    return None, None


def _build_revision_context(repo_root: Path, revision_request: dict[str, Any] | None, revision_request_path: Path | None) -> dict[str, Any] | None:
    if not revision_request:
        return None
    revision_round = revision_request.get("revision_round")
    decision_reason = str(revision_request.get("decision_reason") or "").strip()
    decision_target = str(revision_request.get("decision_target") or "").strip()
    summary = decision_reason
    if revision_round not in (None, ""):
        summary = f"Revision round {revision_round}: {decision_reason or decision_target or 'apply reviewer feedback.'}"
    elif decision_target and decision_reason:
        summary = f"{decision_target}: {decision_reason}"
    elif decision_target:
        summary = decision_target
    elif not summary:
        summary = "Revision request received."
    return {
        "revision_request_ref": _repo_relative_or_abs(repo_root, revision_request_path) if revision_request_path else "",
        "revision_round": revision_round,
        "decision_type": str(revision_request.get("decision_type") or "").strip(),
        "decision_target": decision_target,
        "decision_reason": decision_reason,
        "source_gate_decision_ref": str(revision_request.get("source_gate_decision_ref") or "").strip(),
        "source_return_job_ref": str(revision_request.get("source_return_job_ref") or "").strip(),
        "authoritative_input_ref": str(revision_request.get("authoritative_input_ref") or "").strip(),
        "summary": summary,
    }


def _materialize_revision_request(artifacts_dir: Path, revision_request: dict[str, Any] | None) -> None:
    revision_request_path = artifacts_dir / "revision-request.json"
    if revision_request:
        dump_json(revision_request_path, revision_request)
    elif revision_request_path.exists():
        revision_request_path.unlink()


def yaml_load(path: Path) -> dict[str, Any]:
    import yaml

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def executor_run(
    input_path: str | Path,
    feat_ref: str,
    repo_root: Path,
    run_id: str,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, feat_ref, repo_root)
    if errors:
        raise ValueError("; ".join(errors))

    resolved_input_dir, _ = resolve_input_artifacts_dir(input_path, repo_root)
    package = load_feat_package(resolved_input_dir)
    revision_request, loaded_revision_request_path = _load_revision_request(revision_request_path)
    revision_context = _build_revision_context(repo_root, revision_request, loaded_revision_request_path)
    effective_feat_ref = str(validation.get("feat_ref") or feat_ref).strip()
    feature = find_feature(package, effective_feat_ref)
    if feature is None:
        raise ValueError(f"Selected feat_ref not found: {effective_feat_ref}")
    feature = dict(feature)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)

    effective_run_id = run_id or f"{package.run_id}--{effective_feat_ref.lower()}"
    generated = build_candidate_package(package, feature, effective_feat_ref, effective_run_id, revision_request=revision_context)
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    _materialize_revision_request(output_dir, revision_request)
    write_executor_outputs(output_dir, repo_root, package, generated, f"python scripts/feat_to_testset.py executor-run --input {input_path} --feat-ref {effective_feat_ref}")
    return {
        "ok": True,
        "run_id": effective_run_id,
        "artifacts_dir": str(output_dir),
        "input_validation": validation,
        "input_mode": validation.get("input_mode", "package_dir"),
        "feat_ref": effective_feat_ref,
        "test_set_ref": generated.bundle_json["test_set_ref"],
        "revision_request_ref": revision_context["revision_request_ref"] if revision_context else "",
    }


def supervisor_review(
    artifacts_dir: Path,
    repo_root: Path,
    run_id: str,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
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
    revision_request, loaded_revision_request_path = _load_revision_request(revision_request_path, artifacts_dir)
    revision_context = _build_revision_context(repo_root, revision_request, loaded_revision_request_path)
    feature = find_feature(package, feat_ref)
    if feature is None:
        raise ValueError(f"Selected feat_ref not found: {feat_ref}")
    feature = dict(feature)
    feature["semantic_lock"] = normalize_semantic_lock(feature.get("semantic_lock") or package.semantic_lock)
    effective_run_id = run_id or artifacts_dir.name
    generated = build_candidate_package(package, feature, feat_ref, effective_run_id, revision_request=revision_context)
    supervision = build_supervision_evidence(artifacts_dir)
    supervisor_commit = update_supervisor_outputs(artifacts_dir, repo_root, supervision)

    proposal_ref = ""
    gate_ready_package_ref = ""
    authoritative_handoff_ref = ""
    gate_pending_ref = ""
    if supervision["decision"] == "pass":
        proposal_path = create_handoff_proposal(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=effective_run_id,
            feat_ref=feat_ref,
            test_set_ref=str(generated.bundle_json["test_set_ref"]),
            target_skill=str(generated.bundle_json.get("downstream_target") or DOWNSTREAM_WORKFLOW),
        )
        gate_ready_package = create_gate_ready_package(
            artifacts_dir=artifacts_dir,
            run_id=effective_run_id,
            candidate_ref=f"feat-to-testset.{effective_run_id}.test-set-bundle",
            machine_ssot_ref=repo_relative(repo_root, artifacts_dir / "test-set-bundle.json"),
            acceptance_ref=repo_relative(repo_root, artifacts_dir / "test-set-acceptance-report.json"),
            evidence_bundle_ref=repo_relative(repo_root, artifacts_dir / "supervision-evidence.json"),
        )
        handoff_result = submit_gate_pending(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=effective_run_id,
            proposal_ref=repo_relative(repo_root, proposal_path),
            payload_path=gate_ready_package,
            trace_context_ref=repo_relative(repo_root, artifacts_dir / "execution-evidence.json"),
        )
        gate_submit_data = handoff_result["response"]["data"]
        manifest = load_json(artifacts_dir / "package-manifest.json")
        manifest["handoff_proposal_ref"] = repo_relative(repo_root, proposal_path)
        manifest["gate_ready_package_ref"] = repo_relative(repo_root, gate_ready_package)
        manifest["authoritative_handoff_ref"] = str(gate_submit_data.get("handoff_ref", ""))
        manifest["gate_pending_ref"] = str(gate_submit_data.get("gate_pending_ref", ""))
        manifest["gate_submit_cli_ref"] = repo_relative(repo_root, Path(handoff_result["response_path"]))
        manifest["cli_supervisor_commit_ref"] = str(supervisor_commit["response_path"])
        dump_json(artifacts_dir / "package-manifest.json", manifest)
        proposal_ref = repo_relative(repo_root, proposal_path)
        gate_ready_package_ref = repo_relative(repo_root, gate_ready_package)
        authoritative_handoff_ref = manifest["authoritative_handoff_ref"]
        gate_pending_ref = manifest["gate_pending_ref"]
    collect_evidence_report(artifacts_dir)

    return {
        "ok": True,
        "run_id": effective_run_id,
        "proposal_ref": proposal_ref,
        "gate_ready_package_ref": gate_ready_package_ref,
        "authoritative_handoff_ref": authoritative_handoff_ref,
        "gate_pending_ref": gate_pending_ref,
        "artifacts_dir": str(artifacts_dir),
        "revision_request_ref": revision_context["revision_request_ref"] if revision_context else "",
    }


def run_workflow(
    input_path: str | Path,
    feat_ref: str,
    repo_root: Path | None = None,
    run_id: str | None = None,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
    root = repo_root or repo_root_from(None, input_path)
    effective_run_id = run_id or ""
    executor_result = executor_run(
        input_path=input_path,
        feat_ref=feat_ref,
        repo_root=root,
        run_id=effective_run_id,
        allow_update=allow_update,
        revision_request_path=revision_request_path,
    )
    supervisor_result = supervisor_review(
        Path(executor_result["artifacts_dir"]),
        root,
        effective_run_id,
        allow_update=allow_update,
        revision_request_path=revision_request_path,
    )
    return {**executor_result, **supervisor_result}
