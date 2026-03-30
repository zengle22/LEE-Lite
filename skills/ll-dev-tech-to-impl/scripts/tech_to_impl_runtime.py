#!/usr/bin/env python3
"""
Lite-native runtime support for tech-to-impl.
"""

from __future__ import annotations

import hashlib
from textwrap import shorten
from pathlib import Path
from typing import Any

from tech_to_impl_builder import build_candidate_package
from tech_to_impl_common import (
    dump_json,
    guess_repo_root_from_input,
    load_json,
    load_tech_package,
    resolve_input_artifacts_dir,
    slugify,
    unique_strings,
    validate_input_package,
)
from tech_to_impl_gate_integration import (
    create_gate_ready_package,
    create_handoff_proposal,
    submit_gate_pending,
)
from tech_to_impl_review import (
    build_supervision_evidence,
    collect_evidence_report,
    update_supervisor_outputs,
    validate_output_package,
    validate_package_readiness,
    write_executor_outputs,
)


def _register_impl_candidate(repo_root: Path, artifacts_dir: Path, bundle_json: dict[str, Any]) -> str:
    implementation_root = Path(__file__).resolve().parents[3]
    import sys

    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.lib.registry_store import bind_record

    candidate_ref = f"tech-to-impl.{artifacts_dir.name}.impl-bundle"
    managed_artifact_ref = repo_relative(repo_root, artifacts_dir / "impl-bundle.json")
    metadata = {
        "layer": "candidate",
        "requested_mode": "commit",
        "source_package_ref": repo_relative(repo_root, artifacts_dir),
        "feat_ref": str(bundle_json.get("feat_ref") or "").strip(),
        "tech_ref": str(bundle_json.get("tech_ref") or "").strip(),
        "impl_ref": str(bundle_json.get("impl_ref") or "").strip(),
        "arch_ref": str(bundle_json.get("arch_ref") or "").strip(),
        "api_ref": str(bundle_json.get("api_ref") or "").strip(),
    }
    metadata = {key: value for key, value in metadata.items() if value}
    lineage = [str(item).strip() for item in bundle_json.get("source_refs", []) if str(item).strip()]
    _, record_ref = bind_record(
        repo_root,
        artifact_ref=candidate_ref,
        managed_artifact_ref=managed_artifact_ref,
        status="committed",
        trace={
            "run_ref": str(bundle_json.get("workflow_run_id") or artifacts_dir.name),
            "workflow_key": str(bundle_json.get("workflow_key") or "dev.tech-to-impl"),
        },
        metadata=metadata,
        lineage=lineage,
    )
    return record_ref


def repo_root_from(repo_root: str | None, input_path: Path | None = None) -> Path:
    if repo_root:
        return Path(repo_root).resolve()
    if input_path is not None:
        return guess_repo_root_from_input(input_path.resolve())
    return Path.cwd().resolve()


def output_dir_for(repo_root: Path, run_id: str) -> Path:
    return repo_root / "artifacts" / "tech-to-impl" / run_id


def repo_relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _revision_request_target_path(output_dir: Path) -> Path:
    return output_dir / "revision-request.json"


def _truncate(text: str, limit: int = 180) -> str:
    normalized = " ".join(str(text or "").split())
    return shorten(normalized, width=limit, placeholder="...") if normalized else ""


def _revision_summary(revision_request: dict[str, Any]) -> str:
    decision_target = _truncate(str(revision_request.get("decision_target") or ""), 80)
    decision_reason = _truncate(
        str(revision_request.get("decision_reason") or revision_request.get("reason") or ""),
        180,
    )
    revision_round = str(revision_request.get("revision_round") or "").strip()
    pieces = [piece for piece in [f"round {revision_round}" if revision_round else "", decision_target, decision_reason] if piece]
    summary = " | ".join(pieces) if pieces else "gate revise request"
    return f"Gate revise: {summary}"


def _materialize_revision_request(
    output_dir: Path,
    revision_request_path: str | Path | None,
) -> tuple[str, dict[str, Any], int]:
    target_path = _revision_request_target_path(output_dir)
    if revision_request_path:
        source_path = Path(revision_request_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Revision request not found: {source_path}")
        revision_request = load_json(source_path)
        previous_round = 0
        if target_path.exists():
            previous_round = int(load_json(target_path).get("revision_round") or 0)
        revision_round = previous_round + 1 if previous_round else int(revision_request.get("revision_round") or 1)
        revision_request["revision_round"] = revision_round
        dump_json(target_path, revision_request)
        return str(target_path), revision_request, revision_round
    if target_path.exists():
        revision_request = load_json(target_path)
        revision_round = int(revision_request.get("revision_round") or 1)
        return str(target_path), revision_request, revision_round
    return "", {}, 0


def _apply_revision_request(generated: dict[str, Any], revision_request_ref: str, revision_request: dict[str, Any]) -> str:
    if not revision_request:
        return ""
    revision_summary = _revision_summary(revision_request)
    revision_context = {
        "revision_request_ref": revision_request_ref,
        "workflow_key": str(revision_request.get("workflow_key") or "").strip(),
        "run_id": str(revision_request.get("run_id") or "").strip(),
        "source_run_id": str(revision_request.get("source_run_id") or "").strip(),
        "decision_type": str(revision_request.get("decision_type") or "").strip(),
        "decision_target": str(revision_request.get("decision_target") or "").strip(),
        "decision_reason": str(revision_request.get("decision_reason") or revision_request.get("reason") or "").strip(),
        "revision_round": int(revision_request.get("revision_round") or 0),
        "basis_refs": unique_strings([str(item).strip() for item in revision_request.get("basis_refs") or [] if str(item).strip()]),
        "source_gate_decision_ref": str(revision_request.get("source_gate_decision_ref") or "").strip(),
        "source_return_job_ref": str(revision_request.get("source_return_job_ref") or "").strip(),
        "authoritative_input_ref": str(revision_request.get("authoritative_input_ref") or "").strip(),
        "candidate_ref": str(revision_request.get("candidate_ref") or "").strip(),
        "original_input_path": str(revision_request.get("original_input_path") or "").strip(),
        "triggered_by_request_id": str(revision_request.get("triggered_by_request_id") or "").strip(),
        "summary": revision_summary,
    }
    generated["revision_request_ref"] = revision_request_ref
    generated["revision_request"] = revision_request
    generated["revision_summary"] = revision_summary

    bundle_json = generated.get("bundle_json")
    if isinstance(bundle_json, dict):
        bundle_json["revision_context"] = revision_context
        selected_scope = bundle_json.get("selected_scope")
        if isinstance(selected_scope, dict):
            selected_scope["constraints"] = unique_strings(
                [str(item).strip() for item in selected_scope.get("constraints") or [] if str(item).strip()] + [revision_summary]
            )

    upstream_design_refs = generated.get("upstream_design_refs")
    if isinstance(upstream_design_refs, dict):
        upstream_design_refs["revision_context"] = revision_context
        frozen_decisions = upstream_design_refs.get("frozen_decisions")
        if isinstance(frozen_decisions, dict):
            frozen_decisions["implementation_rules"] = unique_strings(
                [str(item).strip() for item in frozen_decisions.get("implementation_rules") or [] if str(item).strip()] + [revision_summary]
            )

    for key in [
        "bundle_frontmatter",
        "impl_task_frontmatter",
        "integration_frontmatter",
        "frontend_frontmatter",
        "backend_frontmatter",
        "migration_frontmatter",
    ]:
        frontmatter = generated.get(key)
        if isinstance(frontmatter, dict):
            frontmatter["revision_request_ref"] = revision_request_ref
            frontmatter["revision_round"] = revision_context["revision_round"]

    for key in ["review_report", "acceptance_report", "smoke_gate_subject", "handoff"]:
        payload = generated.get(key)
        if isinstance(payload, dict):
            payload["revision_request_ref"] = revision_request_ref
            payload["revision_summary"] = revision_summary

    evidence_plan = generated.get("evidence_plan")
    if isinstance(evidence_plan, dict):
        evidence_plan["revision_request_ref"] = revision_request_ref
        evidence_plan["revision_summary"] = revision_summary

    semantic_drift_check = generated.get("semantic_drift_check")
    if isinstance(semantic_drift_check, dict):
        semantic_drift_check["revision_request_ref"] = revision_request_ref
        semantic_drift_check["revision_summary"] = revision_summary

    generated.setdefault("execution_decisions", []).append(f"Applied revision request {revision_request_ref}.")
    generated.setdefault("execution_uncertainties", []).append(f"Revision context absorbed: {revision_summary}.")
    return revision_summary


def default_run_id(package: Any, tech_ref: str) -> str:
    candidate = f"{package.run_id}--{slugify(tech_ref).lower()}"
    # Keep artifact paths comfortably below Windows path-length trouble spots.
    if len(candidate) <= 80:
        return candidate
    tail = slugify(tech_ref).lower().split("-")[-1]
    digest = hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:8]
    base = slugify(package.run_id).lower()[:48].rstrip("-")
    return f"{base}--{tail}-{digest}"


def executor_run(
    input_path: str | Path,
    feat_ref: str,
    tech_ref: str,
    repo_root: Path,
    run_id: str,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
    errors, validation = validate_input_package(input_path, feat_ref, tech_ref, repo_root)
    if errors:
        raise ValueError("; ".join(errors))

    resolved_input_dir, _ = resolve_input_artifacts_dir(input_path, repo_root)
    package = load_tech_package(resolved_input_dir)
    effective_run_id = run_id or default_run_id(package, tech_ref)
    output_dir = output_dir_for(repo_root, effective_run_id)
    if output_dir.exists() and not allow_update:
        raise FileExistsError(f"Output directory already exists: {output_dir}")

    generated = build_candidate_package(package, effective_run_id)
    revision_request_ref, revision_request, revision_round = _materialize_revision_request(output_dir, revision_request_path)
    revision_summary = _apply_revision_request(generated, revision_request_ref, revision_request)
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
        "input_mode": validation.get("input_mode", "package_dir"),
        "feat_ref": str(validation.get("feat_ref") or feat_ref).strip(),
        "tech_ref": str(validation.get("tech_ref") or tech_ref).strip(),
        "impl_ref": generated["bundle_json"]["impl_ref"],
        "revision_request_ref": revision_request_ref,
        "revision_round": revision_round,
        "revision_summary": revision_summary,
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
    revision_request_ref, revision_request, revision_round = _materialize_revision_request(artifacts_dir, revision_request_path)

    supervision = build_supervision_evidence(artifacts_dir)
    if revision_request:
        supervision["revision_request_ref"] = revision_request_ref
        supervision["revision_summary"] = _revision_summary(revision_request)
        supervision["revision_round"] = revision_round
    update_supervisor_outputs(artifacts_dir, supervision)
    smoke_gate = load_json(artifacts_dir / "smoke-gate-subject.json")
    proposal_ref = ""
    gate_ready_package_ref = ""
    authoritative_handoff_ref = ""
    gate_pending_ref = ""
    if smoke_gate.get("ready_for_execution") is True:
        bundle_json = load_json(artifacts_dir / "impl-bundle.json")
        registry_record_ref = _register_impl_candidate(repo_root, artifacts_dir, bundle_json)
        active_run_id = str(bundle_json.get("workflow_run_id") or run_id or artifacts_dir.name)
        proposal_path = create_handoff_proposal(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
            feat_ref=str(bundle_json.get("feat_ref") or ""),
            tech_ref=str(bundle_json.get("tech_ref") or ""),
            impl_ref=str(bundle_json.get("impl_ref") or ""),
        )
        gate_ready_package = create_gate_ready_package(
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
            candidate_ref=f"tech-to-impl.{active_run_id}.impl-bundle",
            machine_ssot_ref=repo_relative(repo_root, artifacts_dir / "impl-bundle.json"),
            acceptance_ref=repo_relative(repo_root, artifacts_dir / "impl-acceptance-report.json"),
            evidence_bundle_ref=repo_relative(repo_root, artifacts_dir / "supervision-evidence.json"),
        )
        gate_submit = submit_gate_pending(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
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
        manifest["candidate_registry_ref"] = registry_record_ref
        dump_json(artifacts_dir / "package-manifest.json", manifest)
        proposal_ref = manifest["handoff_proposal_ref"]
        gate_ready_package_ref = manifest["gate_ready_package_ref"]
        authoritative_handoff_ref = manifest["authoritative_handoff_ref"]
        gate_pending_ref = manifest["gate_pending_ref"]
    return {
        "ok": True,
        "run_id": supervision["run_id"],
        "artifacts_dir": str(artifacts_dir),
        "decision": supervision["decision"],
        "execution_ready": smoke_gate.get("ready_for_execution") is True,
        "handoff_proposal_ref": proposal_ref,
        "gate_ready_package_ref": gate_ready_package_ref,
        "authoritative_handoff_ref": authoritative_handoff_ref,
        "gate_pending_ref": gate_pending_ref,
    }


def run_workflow(
    input_path: str | Path,
    feat_ref: str,
    tech_ref: str,
    repo_root: Path,
    run_id: str,
    allow_update: bool = False,
    revision_request_path: str | Path | None = None,
) -> dict[str, Any]:
    executor_result = executor_run(
        input_path=input_path,
        feat_ref=feat_ref,
        tech_ref=tech_ref,
        repo_root=repo_root,
        run_id=run_id,
        allow_update=allow_update,
        revision_request_path=revision_request_path,
    )
    artifacts_dir = Path(executor_result["artifacts_dir"])
    supervisor_result = supervisor_review(
        artifacts_dir,
        repo_root,
        run_id or executor_result["run_id"],
        allow_update=True,
        revision_request_path=None,
    )
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
        "impl_ref": executor_result["impl_ref"],
        "revision_request_ref": executor_result.get("revision_request_ref", ""),
        "revision_round": executor_result.get("revision_round", 0),
        "revision_summary": executor_result.get("revision_summary", ""),
        "supervision": supervisor_result,
        "handoff_proposal_ref": supervisor_result.get("handoff_proposal_ref", ""),
        "gate_ready_package_ref": supervisor_result.get("gate_ready_package_ref", ""),
        "authoritative_handoff_ref": supervisor_result.get("authoritative_handoff_ref", ""),
        "gate_pending_ref": supervisor_result.get("gate_pending_ref", ""),
        "output_validation": output_result,
        "readiness_errors": readiness_errors,
        "evidence_report": str(report_path),
    }

