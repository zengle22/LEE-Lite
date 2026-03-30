"""Gate package, decision, materialization, dispatch, and run closure."""

from __future__ import annotations

from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lib.errors import CommandError, ensure
from cli.lib.execution_return_registry import resolve_execution_return_route
from cli.lib.fs import canonical_to_path, load_json, to_canonical_path, write_json
from cli.lib.formalization import materialize_formal
from cli.lib.gate_collaboration_actions import collaboration_handlers
from cli.lib.protocol import CommandContext, run_with_protocol
from cli.lib.job_queue import list_jobs, release_hold_job
from cli.lib.ready_job_dispatch import (
    build_epic_downstream_dispatch,
    build_feat_downstream_dispatch,
    build_src_downstream_dispatch,
    build_tech_downstream_dispatch,
    build_testset_downstream_dispatch,
)
from cli.lib.registry_store import resolve_registry_record, slugify
from cli.lib.review_projection.renderer import build_gate_human_projection

GATE_DECISIONS = {"approve", "revise", "retry", "handoff", "reject"}
PROGRESSION_MODES = {"auto-continue", "hold"}


def _artifact_path(ctx: CommandContext, relative: str):
    return ctx.workspace_root / relative


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _decision_type(findings: list[dict[str, object]]) -> str:
    blocker_count = sum(1 for item in findings if item.get("severity") == "blocker")
    return "revise" if blocker_count else "approve"


def _load_findings(ctx: CommandContext, refs: list[object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for ref in refs:
        finding_path = canonical_to_path(str(ref), ctx.workspace_root)
        if finding_path.exists():
            findings.extend(load_json(finding_path).get("findings", []))
    return findings


def _load_json_if_exists(ctx: CommandContext, ref_value: str | None) -> dict[str, Any]:
    if not ref_value:
        return {}
    path = canonical_to_path(str(ref_value), ctx.workspace_root)
    if not path.exists():
        return {}
    return load_json(path)


def _gate_key(payload: dict[str, Any]) -> str:
    for field in (
        "_gate_key_hint",
        "handoff_ref",
        "decision_target",
        "candidate_ref",
        "formal_ref",
        "gate_ready_package_ref",
        "proposal_ref",
    ):
        value = str(payload.get(field, "")).strip()
        if value:
            return slugify(value)
    return "gate"


def _gate_paths(payload: dict[str, Any]) -> dict[str, str]:
    key = _gate_key(payload)
    return {
        "brief": f"artifacts/active/gates/briefs/{key}-brief-record.json",
        "pending": f"artifacts/active/gates/pending-human/{key}-pending-human-decision.json",
        "decision": f"artifacts/active/gates/decisions/{key}-decision.json",
        "dispatch": f"artifacts/active/gates/dispatch/{key}-dispatch-receipt.json",
    }


def _normalize_decision(payload: dict[str, Any], findings: list[dict[str, object]]) -> str:
    decision = str(payload.get("decision") or payload.get("human_action") or _decision_type(findings))
    ensure(decision in GATE_DECISIONS, "INVALID_REQUEST", f"unknown gate decision: {decision}")
    return decision


def _dispatch_target(decision: str) -> str:
    mapping = {
        "approve": "formal_publication_trigger",
        "revise": "execution_return",
        "retry": "execution_return",
        "handoff": "delegated_handler",
        "reject": "reject_terminal",
    }
    return mapping[decision]


def _normalize_progression_mode(value: object) -> str:
    progression_mode = str(value or "").strip()
    if not progression_mode:
        return ""
    ensure(
        progression_mode in PROGRESSION_MODES,
        "INVALID_REQUEST",
        f"unknown progression_mode: {progression_mode}",
    )
    return progression_mode


def _default_progression_mode(formal_ref: str) -> str:
    return "hold" if formal_ref.startswith("formal.testset.") else "auto-continue"


def _required_preconditions(payload: dict[str, Any], progression_mode: str, formal_ref: str) -> list[str]:
    value = payload.get("required_preconditions")
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if cleaned:
            return cleaned
    if progression_mode == "hold" and formal_ref.startswith("formal.testset."):
        return ["test_environment_ref"]
    return []


def _resolve_progression_policy(payload: dict[str, Any], decision: dict[str, Any]) -> tuple[str, str, list[str]]:
    requested = _normalize_progression_mode(payload.get("progression_mode"))
    stored = _normalize_progression_mode(decision.get("progression_mode"))
    formal_ref = str(decision.get("formal_ref") or "").strip()
    progression_mode = requested or stored or _default_progression_mode(formal_ref)
    hold_reason = str(
        payload.get("hold_reason") or decision.get("hold_reason") or ""
    ).strip()
    if progression_mode == "hold" and not hold_reason and formal_ref.startswith("formal.testset."):
        hold_reason = "test_environment_pending"
    required_preconditions = _required_preconditions(payload, progression_mode, formal_ref)
    return progression_mode, hold_reason, required_preconditions


def _load_handoff_payload(ctx: CommandContext, handoff_ref: str | None) -> dict[str, Any]:
    handoff = _load_json_if_exists(ctx, handoff_ref)
    payload_ref = str(handoff.get("payload_ref", "")).strip()
    if not payload_ref:
        return {}
    payload_path = canonical_to_path(payload_ref, ctx.workspace_root)
    if not payload_path.exists():
        return {}
    return load_json(payload_path)


def _load_gate_package_payload(ctx: CommandContext, gate_ready_package_ref: str | None) -> dict[str, Any]:
    gate_package = _load_json_if_exists(ctx, gate_ready_package_ref)
    package_payload = gate_package.get("payload", {})
    return package_payload if isinstance(package_payload, dict) else {}


def _raw_to_src_package_dir(ctx: CommandContext, candidate_ref: str) -> Path | None:
    if not candidate_ref:
        return None
    try:
        record = resolve_registry_record(ctx.workspace_root, candidate_ref)
    except CommandError:
        return None
    trace = record.get("trace", {})
    if str(trace.get("workflow_key") or "") != "product.raw-to-src":
        return None
    managed_artifact_ref = str(record.get("managed_artifact_ref") or "").strip()
    if not managed_artifact_ref:
        return None
    return canonical_to_path(managed_artifact_ref, ctx.workspace_root).parent


def _resolve_execution_return_dispatch(decision: dict[str, Any]) -> tuple[str, str, str]:
    candidate_ref = str(decision.get("candidate_ref") or "").strip()
    decision_target = str(decision.get("decision_target") or candidate_ref).strip()
    synthetic_job = {
        "candidate_ref": candidate_ref,
        "decision_target": decision_target,
        "payload_ref": decision_target,
        "authoritative_input_ref": decision_target or candidate_ref,
    }
    try:
        resolution = resolve_execution_return_route(synthetic_job, decision)
    except CommandError as exc:
        if exc.status_code == "REGISTRY_MISS":
            return "", decision_target or candidate_ref, ""
        raise
    authoritative_input_ref = resolution.matched_ref or candidate_ref or decision_target
    return resolution.source_run_id, authoritative_input_ref, resolution.route.workflow_key


def _ensure_raw_to_src_gate_ready(ctx: CommandContext, candidate_ref: str) -> None:
    package_dir = _raw_to_src_package_dir(ctx, candidate_ref)
    if package_dir is None:
        return
    manifest_path = package_dir / "package-manifest.json"
    acceptance_path = package_dir / "acceptance-report.json"
    ensure(manifest_path.exists(), "PRECONDITION_FAILED", f"raw-to-src package manifest missing for {candidate_ref}")
    manifest = load_json(manifest_path)
    ensure(
        str(manifest.get("status") or "") == "freeze_ready",
        "PRECONDITION_FAILED",
        f"raw-to-src candidate is not freeze_ready: {manifest.get('status', '')}",
    )
    if acceptance_path.exists():
        acceptance = load_json(acceptance_path)
        ensure(
            str(acceptance.get("decision") or "") in {"pass", "approve"},
            "PRECONDITION_FAILED",
            f"raw-to-src acceptance did not pass: {acceptance.get('decision', '')}",
        )
    result_summary_path = package_dir / "result-summary.json"
    if result_summary_path.exists():
        result_summary = load_json(result_summary_path)
        ensure(
            str(result_summary.get("recommended_action") or "") == "next_skill",
            "PRECONDITION_FAILED",
            f"raw-to-src candidate is not ready for downstream dispatch: {result_summary.get('recommended_action', '')}",
        )


def _resolve_release_hold_candidates(
    ctx: CommandContext,
    *,
    decision_ref: str,
    dispatch_receipt_ref: str | None = None,
) -> list[str]:
    candidate_refs: list[str] = []
    if dispatch_receipt_ref:
        dispatch_receipt = _load_json_if_exists(ctx, dispatch_receipt_ref)
        raw_refs = []
        materialized_job_ref = str(dispatch_receipt.get("materialized_job_ref") or "").strip()
        if materialized_job_ref:
            raw_refs.append(materialized_job_ref)
        materialized_job_refs = dispatch_receipt.get("materialized_job_refs")
        if isinstance(materialized_job_refs, list):
            raw_refs.extend(str(item).strip() for item in materialized_job_refs if str(item).strip())
        for ref in raw_refs:
            job = _load_json_if_exists(ctx, ref)
            if str(job.get("status") or "").strip() == "waiting-human":
                candidate_refs.append(ref)
    if candidate_refs:
        return list(dict.fromkeys(candidate_refs))
    waiting_jobs = list_jobs(ctx.workspace_root, "waiting-human")
    matched = [
        str(item["job_ref"])
        for item in waiting_jobs
        if str(item["payload"].get("gate_decision_ref") or "").strip() == decision_ref
    ]
    return list(dict.fromkeys(matched))


def _decision_target(
    payload: dict[str, Any],
    package_payload: dict[str, Any],
    handoff_payload: dict[str, Any],
) -> str:
    return str(
        payload.get("decision_target")
        or payload.get("candidate_ref")
        or payload.get("artifact_ref")
        or package_payload.get("candidate_ref")
        or handoff_payload.get("candidate_ref")
        or ""
    )


def _decision_basis_refs(
    payload: dict[str, Any],
    brief_record_ref: str,
    findings_refs: list[object],
    evidence_refs: list[object],
) -> list[str]:
    if payload.get("decision_basis_refs"):
        refs = [str(item) for item in payload.get("decision_basis_refs", []) if str(item).strip()]
    else:
        refs = [brief_record_ref]
        refs.extend(str(item) for item in findings_refs if str(item).strip())
        refs.extend(str(item) for item in evidence_refs if str(item).strip())
    if brief_record_ref not in refs:
        refs.insert(0, brief_record_ref)
    ensure(bool(refs), "INVALID_REQUEST", "decision_basis_refs is required")
    return refs


def _persist_brief_and_pending(
    ctx: CommandContext,
    payload: dict[str, Any],
    handoff_ref: str,
    proposal_ref: str,
    decision_target: str,
    findings: list[dict[str, object]],
) -> tuple[str, str]:
    keyed_payload = dict(payload)
    if decision_target and not keyed_payload.get("_gate_key_hint"):
        keyed_payload["_gate_key_hint"] = decision_target
    paths = _gate_paths(keyed_payload)
    brief = {
        "trace": ctx.trace,
        "handoff_ref": handoff_ref,
        "proposal_ref": proposal_ref,
        "gate_type": str(payload.get("gate_type", "quality_gate")),
        "priority": str(payload.get("priority_hint", "P1")),
        "merge_group": str(payload.get("merge_group_hint", "")),
        "decision_target": decision_target,
        "human_projection": build_gate_human_projection(ctx.workspace_root, payload, decision_target, findings),
    }
    pending = {
        "trace": ctx.trace,
        "handoff_ref": handoff_ref,
        "proposal_ref": proposal_ref,
        "brief_record_ref": paths["brief"],
        "claim_owner": str(ctx.request.get("actor_ref", "")),
        "claim_status": "active",
        "decision_round": int(payload.get("decision_round", 1)),
        "priority": brief["priority"],
        "merge_group": brief["merge_group"],
        "state": "pending_human_decision",
    }
    write_json(_artifact_path(ctx, paths["brief"]), brief)
    write_json(_artifact_path(ctx, paths["pending"]), pending)
    return paths["brief"], paths["pending"]


def _materialize_decision(
    ctx: CommandContext,
    decision_ref: str,
    candidate_ref: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    ensure(candidate_ref, "INVALID_REQUEST", "candidate_ref is required for approve materialization")
    result = materialize_formal(
        ctx.workspace_root,
        trace=ctx.trace,
        candidate_ref=candidate_ref,
        decision_ref=decision_ref,
        target_formal_kind=str(payload["target_formal_kind"]).strip() if payload.get("target_formal_kind") else None,
        formal_artifact_ref=str(payload["formal_artifact_ref"]) if payload.get("formal_artifact_ref") else None,
        materialized_by=str(ctx.request.get("actor_ref", "gate.runtime")),
    )
    handoff_ref = "artifacts/active/handoffs/materialized-handoff.json"
    write_json(
        _artifact_path(ctx, handoff_ref),
        {
            "trace": ctx.trace,
            "gate_decision_ref": decision_ref,
            "handoff_type": "downstream",
            "input_refs": [decision_ref, candidate_ref],
            "formal_ref": result["formal_ref"],
            "published_ref": result["published_ref"],
            "materialized_ssot_ref": result.get("materialized_ssot_ref", ""),
            "assigned_id": result.get("assigned_id", ""),
        },
    )
    return {
        "materialized_handoff_ref": handoff_ref,
        "formal_ref": result["formal_ref"],
        "published_ref": result["published_ref"],
        "formalization_receipt_ref": result["receipt_ref"],
        "materialized_ssot_ref": result.get("materialized_ssot_ref", ""),
        "assigned_id": result.get("assigned_id", ""),
        "materialized_formal_refs": result.get("materialized_formal_refs", []),
        "published_refs": result.get("published_refs", []),
        "assigned_ids": result.get("assigned_ids", []),
    }


def _package_action(ctx: CommandContext):
    payload = ctx.payload
    for field in ("candidate_ref", "acceptance_ref", "evidence_bundle_ref"):
        ensure(field in payload, "INVALID_REQUEST", f"missing gate package field: {field}")
    package_ref = "artifacts/active/gates/packages/gate-ready-package.json"
    if ctx.action == "create":
        write_json(_artifact_path(ctx, package_ref), {"trace": ctx.trace, "payload": payload})
    return "OK", f"gate package {ctx.action} completed", {
        "canonical_path": package_ref,
        "gate_ready_package_ref": package_ref,
        "completeness_result": "complete",
        "validation_summary": {"required_fields_present": True},
    }, [], [package_ref]


def _evaluate_action(ctx: CommandContext):
    payload = ctx.payload
    ensure(
        payload.get("gate_ready_package_ref") or payload.get("handoff_ref"),
        "INVALID_REQUEST",
        "gate evaluate requires gate_ready_package_ref or handoff_ref",
    )
    ensure(payload.get("audit_finding_refs") is not None, "INVALID_REQUEST", "missing gate evaluate field: audit_finding_refs")
    ensure(payload.get("target_matrix") is not None, "INVALID_REQUEST", "missing gate evaluate field: target_matrix")
    if payload.get("guard_required") and not payload.get("guarded_enablement_ref"):
        raise CommandError("PROVISIONAL_SLICE_DISABLED", "guarded slice is not enabled")
    findings_refs = list(payload.get("audit_finding_refs", []))
    evidence_refs = list(payload.get("evidence_refs", []))
    findings = _load_findings(ctx, findings_refs)
    package_payload = _load_gate_package_payload(ctx, str(payload.get("gate_ready_package_ref", "")))
    handoff_ref = str(payload.get("handoff_ref") or package_payload.get("handoff_ref") or "")
    proposal_ref = str(payload.get("proposal_ref") or package_payload.get("proposal_ref") or "")
    handoff_payload = _load_handoff_payload(ctx, handoff_ref)
    if package_payload.get("evidence_bundle_ref"):
        evidence_refs.append(package_payload["evidence_bundle_ref"])
    decision_type = _normalize_decision(payload, findings)
    decision_target = _decision_target(payload, package_payload, handoff_payload)
    ensure(decision_target, "INVALID_REQUEST", "decision_target is required")
    keyed_payload = dict(payload)
    keyed_payload["_gate_key_hint"] = decision_target
    brief_record_ref, pending_human_decision_ref = _persist_brief_and_pending(
        ctx,
        keyed_payload,
        handoff_ref,
        proposal_ref,
        decision_target,
        findings,
    )
    decision_basis_refs = _decision_basis_refs(payload, brief_record_ref, findings_refs, evidence_refs)
    dispatch_target = str(payload.get("dispatch_target") or _dispatch_target(decision_type))
    decision_ref = _gate_paths(keyed_payload)["decision"]
    decision = {
        "trace": ctx.trace,
        "handoff_ref": handoff_ref,
        "proposal_ref": proposal_ref,
        "gate_ready_package_ref": str(payload.get("gate_ready_package_ref", "")),
        "brief_record_ref": brief_record_ref,
        "pending_human_decision_ref": pending_human_decision_ref,
        "decision_type": decision_type,
        "decision": decision_type,
        "decision_reason": str(payload.get("decision_reason", "derived from audit findings and target constraints")),
        "decision_target": decision_target,
        "decision_basis_refs": decision_basis_refs,
        "dispatch_target": dispatch_target,
        "target_matrix": payload["target_matrix"],
        "rationale": "derived from audit findings and target constraints",
        "candidate_ref": decision_target,
    }
    created_refs = [brief_record_ref, pending_human_decision_ref, decision_ref]
    write_json(_artifact_path(ctx, decision_ref), decision)
    if decision_type == "approve":
        _ensure_raw_to_src_gate_ready(ctx, decision_target)
        materialized = _materialize_decision(ctx, decision_ref, decision_target, payload)
        decision.update(materialized)
        decision["materialization_state"] = "materialized"
        progression_mode, hold_reason, required_preconditions = _resolve_progression_policy(payload, decision)
        decision["progression_mode"] = progression_mode
        if hold_reason:
            decision["hold_reason"] = hold_reason
        if required_preconditions:
            decision["required_preconditions"] = required_preconditions
        created_refs.extend(
            [
                materialized["materialized_handoff_ref"],
                materialized["formalization_receipt_ref"],
            ]
        )
    write_json(_artifact_path(ctx, decision_ref), decision)
    return "OK", "gate decision produced", {
        "canonical_path": decision_ref,
        "brief_record_ref": brief_record_ref,
        "pending_human_decision_ref": pending_human_decision_ref,
        "gate_decision_ref": decision_ref,
        "decision_ref": decision_ref,
        "decision": decision_type,
        "decision_target": decision_target,
        "decision_basis_refs": decision_basis_refs,
        "dispatch_target": dispatch_target,
        "progression_mode": decision.get("progression_mode", ""),
        "materialized_handoff_ref": decision.get("materialized_handoff_ref", ""),
        "formal_ref": decision.get("formal_ref", ""),
        "published_ref": decision.get("published_ref", ""),
        "formalization_receipt_ref": decision.get("formalization_receipt_ref", ""),
        "materialized_ssot_ref": decision.get("materialized_ssot_ref", ""),
        "assigned_id": decision.get("assigned_id", ""),
        "materialized_formal_refs": decision.get("materialized_formal_refs", []),
        "published_refs": decision.get("published_refs", []),
        "assigned_ids": decision.get("assigned_ids", []),
        "enablement_scope": "guarded-only" if payload.get("guarded_enablement_ref") else "core",
    }, [], created_refs


def _materialize_action(ctx: CommandContext):
    payload = ctx.payload
    decision_ref = str(payload.get("gate_decision_ref", ""))
    ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref is required")
    decision = load_json(canonical_to_path(decision_ref, ctx.workspace_root))
    ensure(decision.get("decision_type") == "approve", "PRECONDITION_FAILED", "only approve can materialize")
    candidate_ref = str(payload.get("candidate_ref", decision.get("candidate_ref", payload.get("artifact_ref", ""))))
    ensure(candidate_ref, "INVALID_REQUEST", "candidate_ref is required for materialize")
    _ensure_raw_to_src_gate_ready(ctx, candidate_ref)
    materialized = _materialize_decision(ctx, decision_ref, candidate_ref, payload)
    decision.update(materialized)
    progression_mode, hold_reason, required_preconditions = _resolve_progression_policy(payload, decision)
    decision["progression_mode"] = progression_mode
    if hold_reason:
        decision["hold_reason"] = hold_reason
    if required_preconditions:
        decision["required_preconditions"] = required_preconditions
    write_json(_artifact_path(ctx, decision_ref), decision)
    return "OK", "formal handoff materialized", {
        "canonical_path": materialized["materialized_handoff_ref"],
        "gate_decision_ref": decision_ref,
        "materialized_handoff_ref": materialized["materialized_handoff_ref"],
        "materialized_job_ref": "",
        "run_closure_ref": "",
        "enablement_scope": "guarded-only" if payload.get("guarded_only") else "core",
        "progression_mode": decision.get("progression_mode", ""),
        "formal_ref": materialized["formal_ref"],
        "published_ref": materialized["published_ref"],
        "materialized_ssot_ref": materialized.get("materialized_ssot_ref", ""),
        "assigned_id": materialized.get("assigned_id", ""),
        "materialized_formal_refs": materialized.get("materialized_formal_refs", []),
        "published_refs": materialized.get("published_refs", []),
        "assigned_ids": materialized.get("assigned_ids", []),
    }, [], [materialized["materialized_handoff_ref"], materialized["formalization_receipt_ref"]]


def _dispatch_action(ctx: CommandContext):
    payload = ctx.payload
    decision_ref = str(payload.get("gate_decision_ref") or payload.get("decision_ref") or "")
    ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref is required")
    decision = load_json(canonical_to_path(decision_ref, ctx.workspace_root))
    decision_type = str(decision.get("decision_type") or decision.get("decision") or "")
    dispatch_target = str(payload.get("dispatch_target") or decision.get("dispatch_target") or _dispatch_target(decision_type))
    progression_mode, hold_reason, required_preconditions = _resolve_progression_policy(payload, decision)
    if decision_type == "approve":
        decision["progression_mode"] = progression_mode
        if hold_reason:
            decision["hold_reason"] = hold_reason
        if required_preconditions:
            decision["required_preconditions"] = required_preconditions
        write_json(_artifact_path(ctx, decision_ref), decision)
    dispatch_ref = _gate_paths(decision)["dispatch"]
    materialized_job_ref = ""
    materialized_handoff_ref = ""
    materialized_job_refs: list[str] = []
    materialized_handoff_refs: list[str] = []
    if dispatch_target == "formal_publication_trigger":
        ensure(decision_type == "approve", "PRECONDITION_FAILED", "formal_publication_trigger requires approve")
        if decision.get("materialized_handoff_ref"):
            materialized_handoff_ref = str(decision["materialized_handoff_ref"])
        else:
            materialized = _materialize_decision(ctx, decision_ref, str(decision.get("candidate_ref", "")), payload)
            decision.update(materialized)
            write_json(_artifact_path(ctx, decision_ref), decision)
            materialized_handoff_ref = materialized["materialized_handoff_ref"]
        if str(decision.get("formal_ref") or "").startswith("formal.src."):
            materialized_handoff_refs, materialized_job_refs = build_src_downstream_dispatch(
                ctx.workspace_root, ctx.trace, decision_ref, decision
            )
            materialized_handoff_ref = materialized_handoff_refs[0] if materialized_handoff_refs else materialized_handoff_ref
            materialized_job_ref = materialized_job_refs[0] if materialized_job_refs else ""
        elif str(decision.get("formal_ref") or "").startswith("formal.epic."):
            materialized_handoff_refs, materialized_job_refs = build_epic_downstream_dispatch(
                ctx.workspace_root, ctx.trace, decision_ref, decision
            )
            materialized_handoff_ref = materialized_handoff_refs[0] if materialized_handoff_refs else materialized_handoff_ref
            materialized_job_ref = materialized_job_refs[0] if materialized_job_refs else ""
        elif str(decision.get("formal_ref") or "").startswith("formal.feat."):
            materialized_handoff_refs, materialized_job_refs = build_feat_downstream_dispatch(
                ctx.workspace_root, ctx.trace, decision_ref, decision
            )
            materialized_handoff_ref = materialized_handoff_refs[0] if materialized_handoff_refs else materialized_handoff_ref
            materialized_job_ref = materialized_job_refs[0] if materialized_job_refs else ""
        elif str(decision.get("formal_ref") or "").startswith("formal.tech."):
            materialized_handoff_refs, materialized_job_refs = build_tech_downstream_dispatch(
                ctx.workspace_root, ctx.trace, decision_ref, decision
            )
            materialized_handoff_ref = materialized_handoff_refs[0] if materialized_handoff_refs else materialized_handoff_ref
            materialized_job_ref = materialized_job_refs[0] if materialized_job_refs else ""
        elif str(decision.get("formal_ref") or "").startswith("formal.testset."):
            materialized_handoff_refs, materialized_job_refs = build_testset_downstream_dispatch(
                ctx.workspace_root, ctx.trace, decision_ref, decision
            )
            materialized_handoff_ref = materialized_handoff_refs[0] if materialized_handoff_refs else materialized_handoff_ref
            materialized_job_ref = materialized_job_refs[0] if materialized_job_refs else ""
    elif dispatch_target == "delegated_handler":
        materialized_handoff_ref = f"artifacts/active/handoffs/{Path(decision_ref).stem}-delegated.json"
        write_json(
            _artifact_path(ctx, materialized_handoff_ref),
            {
                "trace": ctx.trace,
                "gate_decision_ref": decision_ref,
                "handoff_type": "delegated_handler",
                "input_refs": [decision_ref],
                "decision_target": decision.get("decision_target", ""),
            },
        )
    elif dispatch_target == "execution_return":
        materialized_job_ref = f"artifacts/jobs/waiting-human/{Path(decision_ref).stem}-return.json"
        source_run_id, authoritative_input_ref, workflow_key = _resolve_execution_return_dispatch(decision)
        write_json(
            _artifact_path(ctx, materialized_job_ref),
            {
                "trace": ctx.trace,
                "job_id": f"job-{Path(decision_ref).stem}-return",
                "gate_decision_ref": decision_ref,
                "job_type": "execution_return",
                "status": "waiting-human",
                "queue_path": materialized_job_ref,
                "target_skill": "execution.return",
                "payload_ref": str(decision.get("decision_target", "")),
                "input_refs": [decision_ref, str(decision.get("decision_target", ""))],
                "authoritative_input_ref": authoritative_input_ref,
                "source_run_id": source_run_id,
                "decision_type": decision_type,
                "created_at": _utc_now(),
                "reason": "gate requested execution-side revision before resubmission",
                **({"workflow_key": workflow_key} if workflow_key else {}),
            },
        )
    else:
        ensure(dispatch_target == "reject_terminal", "INVALID_REQUEST", f"unknown dispatch target: {dispatch_target}")
    write_json(
        _artifact_path(ctx, dispatch_ref),
        {
            "trace": ctx.trace,
            "gate_decision_ref": decision_ref,
            "dispatch_target": dispatch_target,
            "progression_mode": progression_mode if decision_type == "approve" else "",
            "materialized_job_ref": materialized_job_ref,
            "materialized_job_refs": materialized_job_refs,
            "materialized_handoff_ref": materialized_handoff_ref,
            "materialized_handoff_refs": materialized_handoff_refs,
        },
    )
    return "OK", "gate decision dispatched", {
        "canonical_path": dispatch_ref,
        "gate_decision_ref": decision_ref,
        "dispatch_receipt_ref": dispatch_ref,
        "dispatch_status": "dispatched",
        "progression_mode": progression_mode if decision_type == "approve" else "",
        "materialized_handoff_ref": materialized_handoff_ref,
        "materialized_handoff_refs": materialized_handoff_refs,
        "materialized_job_ref": materialized_job_ref,
        "materialized_job_refs": materialized_job_refs,
        "run_closure_ref": "",
        "enablement_scope": "core",
    }, [], [dispatch_ref, materialized_handoff_ref, materialized_job_ref, *materialized_handoff_refs, *materialized_job_refs]


def _release_hold_action(ctx: CommandContext):
    payload = ctx.payload
    dispatch_receipt_ref = str(payload.get("dispatch_receipt_ref") or "").strip()
    decision_ref = str(payload.get("gate_decision_ref") or payload.get("decision_ref") or "").strip()
    if dispatch_receipt_ref and not decision_ref:
        dispatch_receipt = _load_json_if_exists(ctx, dispatch_receipt_ref)
        decision_ref = str(dispatch_receipt.get("gate_decision_ref") or "").strip()
    ensure(decision_ref, "INVALID_REQUEST", "gate_decision_ref or dispatch_receipt_ref is required")
    released_job_refs = _resolve_release_hold_candidates(
        ctx,
        decision_ref=decision_ref,
        dispatch_receipt_ref=dispatch_receipt_ref or None,
    )
    ensure(bool(released_job_refs), "PRECONDITION_FAILED", f"no waiting-human hold jobs found for {decision_ref}")
    released: list[dict[str, Any]] = []
    evidence_refs: list[str] = []
    for job_ref in released_job_refs:
        result = release_hold_job(
            ctx.workspace_root,
            job_ref,
            actor_ref=str(ctx.request.get("actor_ref") or "gate.operator"),
            note=str(payload.get("note") or "").strip() or "gate released held downstream progression",
        )
        released.append(result)
        evidence_refs.append(result["released_job_ref"])
    return "OK", "gate hold released", {
        "canonical_path": released[0]["released_job_ref"],
        "gate_decision_ref": decision_ref,
        "dispatch_receipt_ref": dispatch_receipt_ref,
        "released_job_ref": released[0]["released_job_ref"],
        "released_job_refs": [item["released_job_ref"] for item in released],
        "released_count": len(released),
    }, [], evidence_refs


def _close_action(ctx: CommandContext):
    payload = ctx.payload
    run_ref = str(payload.get("run_ref", ctx.trace.get("run_ref", "")))
    ensure(run_ref, "INVALID_REQUEST", "run_ref is required")
    closure_ref = "artifacts/active/closures/run-closure.json"
    write_json(_artifact_path(ctx, closure_ref), {"trace": ctx.trace, "run_ref": run_ref, "final_status": "closed"})
    return "OK", "run closed", {
        "canonical_path": closure_ref,
        "gate_decision_ref": str(payload.get("gate_decision_ref", "")),
        "materialized_handoff_ref": "",
        "materialized_job_ref": "",
        "run_closure_ref": closure_ref,
        "enablement_scope": "core",
    }, [], [closure_ref]


def _gate_handler(ctx: CommandContext):
    handlers = {
        "create": _package_action,
        "verify": _package_action,
        "evaluate": _evaluate_action,
        "materialize": _materialize_action,
        "dispatch": _dispatch_action,
        "release-hold": _release_hold_action,
        "close-run": _close_action,
    }
    handlers.update(collaboration_handlers())
    return handlers[ctx.action](ctx)


def handle(args: Namespace) -> int:
    setattr(args, "action", args.action)
    return run_with_protocol(args, _gate_handler)
