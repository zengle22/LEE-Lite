"""Helpers for emitting runner-consumable downstream jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, write_json
from cli.lib.registry_store import resolve_registry_record, slugify


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _base_handoff(
    *,
    trace: dict[str, Any],
    decision_ref: str,
    formal_ref: str,
    published_ref: str,
    target_skill: str,
    target_kind: str,
    source_package_ref: str,
    authoritative_input_ref: str,
    progression_mode: str = "auto-continue",
) -> dict[str, Any]:
    return {
        "trace": trace,
        "gate_decision_ref": decision_ref,
        "handoff_type": "downstream",
        "input_refs": [decision_ref, formal_ref],
        "formal_ref": formal_ref,
        "published_ref": published_ref,
        "target_skill": target_skill,
        "target_kind": target_kind,
        "source_package_ref": source_package_ref,
        "authoritative_input_ref": authoritative_input_ref,
        "progression_mode": progression_mode,
        "created_at": _utc_now(),
    }


def _base_job(
    *,
    trace: dict[str, Any],
    decision_ref: str,
    handoff_ref: str,
    target_skill: str,
    source_run_id: str,
    published_ref: str,
    formal_ref: str,
    source_package_ref: str,
    authoritative_input_ref: str,
    input_refs: list[str],
    queue_path: str,
    slug: str,
    progression_mode: str = "auto-continue",
    status: str = "ready",
) -> dict[str, Any]:
    return {
        "trace": trace,
        "job_id": f"job-{Path(decision_ref).stem}-{slug}",
        "job_type": "next_skill",
        "from_skill": "governance.gate-human-orchestrator",
        "target_skill": target_skill,
        "handoff_ref": handoff_ref,
        "source_run_id": source_run_id,
        "source_artifacts": input_refs,
        "input_refs": input_refs,
        "authoritative_input_ref": authoritative_input_ref,
        "gate_decision_ref": decision_ref,
        "priority": "normal",
        "status": status,
        "created_at": _utc_now(),
        "queue_path": queue_path,
        "consumer_type": "skill_loop",
        "retry_count": 0,
        "retry_budget": 0,
        "formal_ref": formal_ref,
        "published_ref": published_ref,
        "source_package_ref": source_package_ref,
        "progression_mode": progression_mode,
    }


def build_feat_downstream_dispatch(
    workspace_root: Path,
    trace: dict[str, Any],
    decision_ref: str,
    decision: dict[str, Any],
) -> tuple[list[str], list[str]]:
    group_formal_ref = str(decision.get("formal_ref") or "").strip()
    ensure(group_formal_ref, "PRECONDITION_FAILED", "formal_ref is required for FEAT dispatch")
    group_record = resolve_registry_record(workspace_root, group_formal_ref)
    group_metadata = group_record.get("metadata", {}) if isinstance(group_record.get("metadata"), dict) else {}
    child_formal_refs = [
        str(item).strip()
        for item in (decision.get("materialized_formal_refs") or group_metadata.get("materialized_formal_refs") or [])
        if str(item).strip()
    ]
    ensure(child_formal_refs, "PRECONDITION_FAILED", "formal FEAT dispatch requires materialized_formal_refs")

    handoff_refs: list[str] = []
    job_refs: list[str] = []
    source_run_id = str(trace.get("run_ref", ""))
    dispatch_targets = [("workflow.dev.feat_to_tech", "TECH"), ("workflow.qa.feat_to_testset", "TESTSET")]

    for child_formal_ref in child_formal_refs:
        child_record = resolve_registry_record(workspace_root, child_formal_ref)
        metadata = child_record.get("metadata", {}) if isinstance(child_record.get("metadata"), dict) else {}
        feat_ref = str(metadata.get("feat_ref") or metadata.get("assigned_id") or "").strip()
        ensure(feat_ref, "PRECONDITION_FAILED", f"formal FEAT record missing feat_ref: {child_formal_ref}")
        published_ref = str(child_record.get("managed_artifact_ref") or "").strip()
        source_package_ref = str(metadata.get("source_package_ref") or "").strip()
        authoritative_input_ref = child_formal_ref
        input_refs = [decision_ref, child_formal_ref]

        for target_skill, target_kind in dispatch_targets:
            slug = f"{slugify(feat_ref)}-{slugify(target_skill)}"
            handoff_ref = f"artifacts/active/handoffs/{Path(decision_ref).stem}-{slug}.json"
            handoff_payload = _base_handoff(
                trace=trace,
                decision_ref=decision_ref,
                formal_ref=child_formal_ref,
                published_ref=published_ref,
                target_skill=target_skill,
                target_kind=target_kind,
                source_package_ref=source_package_ref,
                authoritative_input_ref=authoritative_input_ref,
                progression_mode="auto-continue",
            )
            handoff_payload["feat_ref"] = feat_ref
            write_json(canonical_to_path(handoff_ref, workspace_root), handoff_payload)

            job_ref = f"artifacts/jobs/ready/{Path(decision_ref).stem}-{slug}.json"
            job_payload = _base_job(
                trace=trace,
                decision_ref=decision_ref,
                handoff_ref=handoff_ref,
                target_skill=target_skill,
                source_run_id=source_run_id,
                published_ref=published_ref,
                formal_ref=child_formal_ref,
                source_package_ref=source_package_ref,
                authoritative_input_ref=authoritative_input_ref,
                input_refs=input_refs,
                queue_path=job_ref,
                slug=slug,
                progression_mode="auto-continue",
                status="ready",
            )
            job_payload["feat_ref"] = feat_ref
            job_payload["reason"] = f"Approved FEAT {feat_ref} is ready for downstream {target_kind} derivation."
            write_json(canonical_to_path(job_ref, workspace_root), job_payload)

            handoff_refs.append(handoff_ref)
            job_refs.append(job_ref)
    return handoff_refs, job_refs


def build_src_downstream_dispatch(
    workspace_root: Path,
    trace: dict[str, Any],
    decision_ref: str,
    decision: dict[str, Any],
) -> tuple[list[str], list[str]]:
    formal_ref = str(decision.get("formal_ref") or "").strip()
    ensure(formal_ref, "PRECONDITION_FAILED", "formal_ref is required for SRC dispatch")
    record = resolve_registry_record(workspace_root, formal_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    src_ref = str(metadata.get("assigned_id") or metadata.get("src_ref") or "").strip()
    ensure(src_ref, "PRECONDITION_FAILED", f"formal SRC record missing src_ref: {formal_ref}")
    published_ref = str(record.get("managed_artifact_ref") or "").strip()
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    handoff_ref = f"artifacts/active/handoffs/{Path(decision_ref).stem}-{slugify(src_ref)}-src-to-epic.json"
    job_ref = f"artifacts/jobs/ready/{Path(decision_ref).stem}-{slugify(src_ref)}-src-to-epic.json"
    authoritative_input_ref = formal_ref
    input_refs = [decision_ref, formal_ref]

    handoff_payload = _base_handoff(
        trace=trace,
        decision_ref=decision_ref,
        formal_ref=formal_ref,
        published_ref=published_ref,
        target_skill="workflow.product.src_to_epic",
        target_kind="EPIC",
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        progression_mode="auto-continue",
    )
    handoff_payload["src_ref"] = src_ref
    write_json(canonical_to_path(handoff_ref, workspace_root), handoff_payload)

    job_payload = _base_job(
        trace=trace,
        decision_ref=decision_ref,
        handoff_ref=handoff_ref,
        target_skill="workflow.product.src_to_epic",
        source_run_id=str(trace.get("run_ref", "")),
        published_ref=published_ref,
        formal_ref=formal_ref,
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        input_refs=input_refs,
        queue_path=job_ref,
        slug=f"{slugify(src_ref)}-src-to-epic",
        progression_mode="auto-continue",
        status="ready",
    )
    job_payload["src_ref"] = src_ref
    job_payload["reason"] = f"Approved SRC {src_ref} is ready for downstream EPIC derivation."
    write_json(canonical_to_path(job_ref, workspace_root), job_payload)
    return [handoff_ref], [job_ref]


def build_epic_downstream_dispatch(
    workspace_root: Path,
    trace: dict[str, Any],
    decision_ref: str,
    decision: dict[str, Any],
) -> tuple[list[str], list[str]]:
    formal_ref = str(decision.get("formal_ref") or "").strip()
    ensure(formal_ref, "PRECONDITION_FAILED", "formal_ref is required for EPIC dispatch")
    record = resolve_registry_record(workspace_root, formal_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    epic_ref = str(metadata.get("assigned_id") or metadata.get("epic_ref") or "").strip()
    ensure(epic_ref, "PRECONDITION_FAILED", f"formal EPIC record missing epic_ref: {formal_ref}")
    src_ref = str(metadata.get("src_ref") or "").strip()
    published_ref = str(record.get("managed_artifact_ref") or "").strip()
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    handoff_ref = f"artifacts/active/handoffs/{Path(decision_ref).stem}-{slugify(epic_ref)}-epic-to-feat.json"
    job_ref = f"artifacts/jobs/ready/{Path(decision_ref).stem}-{slugify(epic_ref)}-epic-to-feat.json"
    authoritative_input_ref = formal_ref
    input_refs = [decision_ref, formal_ref]

    handoff_payload = _base_handoff(
        trace=trace,
        decision_ref=decision_ref,
        formal_ref=formal_ref,
        published_ref=published_ref,
        target_skill="workflow.product.epic_to_feat",
        target_kind="FEAT",
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        progression_mode="auto-continue",
    )
    handoff_payload["epic_ref"] = epic_ref
    handoff_payload["src_ref"] = src_ref
    write_json(canonical_to_path(handoff_ref, workspace_root), handoff_payload)

    job_payload = _base_job(
        trace=trace,
        decision_ref=decision_ref,
        handoff_ref=handoff_ref,
        target_skill="workflow.product.epic_to_feat",
        source_run_id=str(trace.get("run_ref", "")),
        published_ref=published_ref,
        formal_ref=formal_ref,
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        input_refs=input_refs,
        queue_path=job_ref,
        slug=f"{slugify(epic_ref)}-epic-to-feat",
        progression_mode="auto-continue",
        status="ready",
    )
    job_payload["epic_ref"] = epic_ref
    job_payload["src_ref"] = src_ref
    job_payload["reason"] = f"Approved EPIC {epic_ref} is ready for downstream FEAT derivation."
    write_json(canonical_to_path(job_ref, workspace_root), job_payload)
    return [handoff_ref], [job_ref]


def build_tech_downstream_dispatch(
    workspace_root: Path,
    trace: dict[str, Any],
    decision_ref: str,
    decision: dict[str, Any],
) -> tuple[list[str], list[str]]:
    formal_ref = str(decision.get("formal_ref") or "").strip()
    ensure(formal_ref, "PRECONDITION_FAILED", "formal_ref is required for TECH dispatch")
    record = resolve_registry_record(workspace_root, formal_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    tech_ref = str(metadata.get("tech_ref") or metadata.get("assigned_id") or "").strip()
    feat_ref = str(metadata.get("feat_ref") or "").strip()
    published_ref = str(record.get("managed_artifact_ref") or "").strip()
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    handoff_ref = f"artifacts/active/handoffs/{Path(decision_ref).stem}-{slugify(tech_ref or formal_ref)}-tech-to-impl.json"
    job_ref = f"artifacts/jobs/ready/{Path(decision_ref).stem}-{slugify(tech_ref or formal_ref)}-tech-to-impl.json"
    authoritative_input_ref = formal_ref
    input_refs = [decision_ref, formal_ref]

    handoff_payload = _base_handoff(
        trace=trace,
        decision_ref=decision_ref,
        formal_ref=formal_ref,
        published_ref=published_ref,
        target_skill="workflow.dev.tech_to_impl",
        target_kind="IMPL",
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        progression_mode="auto-continue",
    )
    handoff_payload["feat_ref"] = feat_ref
    handoff_payload["tech_ref"] = tech_ref
    write_json(canonical_to_path(handoff_ref, workspace_root), handoff_payload)

    job_payload = _base_job(
        trace=trace,
        decision_ref=decision_ref,
        handoff_ref=handoff_ref,
        target_skill="workflow.dev.tech_to_impl",
        source_run_id=str(trace.get("run_ref", "")),
        published_ref=published_ref,
        formal_ref=formal_ref,
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        input_refs=input_refs,
        queue_path=job_ref,
        slug=f"{slugify(tech_ref or formal_ref)}-tech-to-impl",
        progression_mode="auto-continue",
        status="ready",
    )
    job_payload["feat_ref"] = feat_ref
    job_payload["tech_ref"] = tech_ref
    job_payload["reason"] = f"Approved TECH {tech_ref or formal_ref} is ready for downstream IMPL derivation."
    write_json(canonical_to_path(job_ref, workspace_root), job_payload)
    return [handoff_ref], [job_ref]


def build_testset_downstream_dispatch(
    workspace_root: Path,
    trace: dict[str, Any],
    decision_ref: str,
    decision: dict[str, Any],
) -> tuple[list[str], list[str]]:
    formal_ref = str(decision.get("formal_ref") or "").strip()
    ensure(formal_ref, "PRECONDITION_FAILED", "formal_ref is required for TESTSET dispatch")
    record = resolve_registry_record(workspace_root, formal_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    test_set_ref = str(metadata.get("test_set_ref") or metadata.get("assigned_id") or "").strip()
    feat_ref = str(metadata.get("feat_ref") or "").strip()
    target_skill = str(metadata.get("target_skill") or "").strip()
    ensure(target_skill, "PRECONDITION_FAILED", "formal TESTSET record missing target_skill")
    published_ref = str(record.get("managed_artifact_ref") or "").strip()
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    handoff_ref = f"artifacts/active/handoffs/{Path(decision_ref).stem}-{slugify(test_set_ref or formal_ref)}-test-exec.json"
    progression_mode = str(decision.get("progression_mode") or "hold").strip()
    ensure(
        progression_mode in {"auto-continue", "hold"},
        "INVALID_REQUEST",
        f"unsupported progression_mode for TESTSET dispatch: {progression_mode}",
    )
    job_dir = "artifacts/jobs/ready" if progression_mode == "auto-continue" else "artifacts/jobs/waiting-human"
    job_status = "ready" if progression_mode == "auto-continue" else "waiting-human"
    job_ref = f"{job_dir}/{Path(decision_ref).stem}-{slugify(test_set_ref or formal_ref)}-test-exec.json"
    authoritative_input_ref = published_ref or formal_ref
    input_refs = [decision_ref, formal_ref, published_ref] if published_ref else [decision_ref, formal_ref]
    required_preconditions = decision.get("required_preconditions")
    if isinstance(required_preconditions, list):
        required_preconditions = [str(item).strip() for item in required_preconditions if str(item).strip()]
    else:
        required_preconditions = []
    if progression_mode == "hold" and not required_preconditions:
        required_preconditions = ["test_environment_ref"]
    hold_reason = str(decision.get("hold_reason") or "").strip()
    if progression_mode == "hold" and not hold_reason:
        hold_reason = "test_environment_pending"

    handoff_payload = _base_handoff(
        trace=trace,
        decision_ref=decision_ref,
        formal_ref=formal_ref,
        published_ref=published_ref,
        target_skill=target_skill,
        target_kind="TEST_EXEC",
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        progression_mode=progression_mode,
    )
    handoff_payload["feat_ref"] = feat_ref
    handoff_payload["test_set_ref"] = test_set_ref
    if required_preconditions:
        handoff_payload["required_preconditions"] = required_preconditions
    if hold_reason:
        handoff_payload["hold_reason"] = hold_reason
    write_json(canonical_to_path(handoff_ref, workspace_root), handoff_payload)

    job_payload = _base_job(
        trace=trace,
        decision_ref=decision_ref,
        handoff_ref=handoff_ref,
        target_skill=target_skill,
        source_run_id=str(trace.get("run_ref", "")),
        published_ref=published_ref,
        formal_ref=formal_ref,
        source_package_ref=source_package_ref,
        authoritative_input_ref=authoritative_input_ref,
        input_refs=input_refs,
        queue_path=job_ref,
        slug=f"{slugify(test_set_ref or formal_ref)}-test-exec",
        progression_mode=progression_mode,
        status=job_status,
    )
    job_payload["feat_ref"] = feat_ref
    job_payload["test_set_ref"] = test_set_ref
    if required_preconditions:
        job_payload["required_preconditions"] = required_preconditions
    if hold_reason:
        job_payload["hold_reason"] = hold_reason
    if progression_mode == "auto-continue":
        job_payload["reason"] = f"Approved TESTSET {test_set_ref or formal_ref} is ready for downstream execution."
    else:
        job_payload["reason"] = (
            f"Approved TESTSET {test_set_ref or formal_ref} is held until downstream execution preconditions are released."
        )
    write_json(canonical_to_path(job_ref, workspace_root), job_payload)
    return [handoff_ref], [job_ref]
