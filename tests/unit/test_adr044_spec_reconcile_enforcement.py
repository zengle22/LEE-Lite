from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.lib.errors import CommandError
from cli.lib.formalization_materialize import ensure_spec_reconcile_ready_for_materialization
from cli.lib.job_queue import release_hold_job
from cli.lib.ready_job_dispatch import build_feat_downstream_dispatch, build_tech_downstream_dispatch
from cli.lib.registry_store import bind_record
from cli.lib.spec_reconcile_enforcement import evaluate_spec_reconcile_hold


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_evaluate_spec_reconcile_hold_missing_findings(tmp_path: Path) -> None:
    package_ref = "artifacts/feat-to-proto/run-1--feat-1"
    (tmp_path / package_ref).mkdir(parents=True, exist_ok=True)
    result = evaluate_spec_reconcile_hold(tmp_path, source_package_ref=package_ref)
    assert result["in_scope"] is True
    assert result["hold"] is True
    assert "missing spec-findings.json" in result["blocking_items"][0]


def test_evaluate_spec_reconcile_hold_missing_report(tmp_path: Path) -> None:
    package_ref = "artifacts/feat-to-proto/run-2--feat-2"
    package_dir = tmp_path / package_ref
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "spec-findings.json",
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "dev.feat-to-proto", "run_ref": "run-2"},
            "findings": [],
        },
    )
    result = evaluate_spec_reconcile_hold(tmp_path, source_package_ref=package_ref)
    assert result["hold"] is True
    assert "missing spec-reconcile-report.json" in result["blocking_items"][0]


def test_evaluate_spec_reconcile_hold_blocks_when_blocking_items_present(tmp_path: Path) -> None:
    package_ref = "artifacts/feat-to-tech/run-3--feat-3"
    package_dir = tmp_path / package_ref
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "spec-findings.json",
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-3"},
            "findings": [],
        },
    )
    _write_json(
        package_dir / "spec-reconcile-report.json",
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-3"},
            "input_spec_findings_ref": f"{package_ref}/spec-findings.json",
            "decisions": [],
            "summary": {"total": 0, "backported": 0, "rejected": 0, "deferred": 0, "recorded": 0},
            "blocking_items": ["missing decisions for findings: GAP-001"],
        },
    )
    result = evaluate_spec_reconcile_hold(tmp_path, source_package_ref=package_ref)
    assert result["hold"] is True


def test_evaluate_spec_reconcile_hold_passes_when_blocking_items_empty(tmp_path: Path) -> None:
    package_ref = "artifacts/feat-to-tech/run-4--feat-4"
    package_dir = tmp_path / package_ref
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "spec-findings.json",
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-4"},
            "findings": [],
        },
    )
    _write_json(
        package_dir / "spec-reconcile-report.json",
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-4"},
            "input_spec_findings_ref": f"{package_ref}/spec-findings.json",
            "decisions": [],
            "summary": {"total": 0, "backported": 0, "rejected": 0, "deferred": 0, "recorded": 0},
            "blocking_items": [],
        },
    )
    result = evaluate_spec_reconcile_hold(tmp_path, source_package_ref=package_ref)
    assert result["hold"] is False


def test_feat_dispatch_holds_jobs_until_spec_reconcile_done(tmp_path: Path) -> None:
    decision_ref = "artifacts/active/gates/decisions/dec-1.json"
    group_ref = "formal.feat.FEAT-GROUP"
    child_ref = "formal.feat.FEAT-001"
    package_ref = "artifacts/epic-to-feat/run-5"
    package_dir = tmp_path / package_ref
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "spec-findings.json",
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "product.epic-to-feat", "run_ref": "run-5"},
            "findings": [],
        },
    )

    bind_record(tmp_path, group_ref, "ssot/formal/feat-group.md", "materialized", {"workflow_key": "test", "run_ref": "t"}, metadata={})
    bind_record(
        tmp_path,
        child_ref,
        "ssot/formal/feat-001.md",
        "materialized",
        {"workflow_key": "test", "run_ref": "t"},
        metadata={"feat_ref": "FEAT-001", "source_package_ref": package_ref},
    )
    handoff_refs, job_refs = build_feat_downstream_dispatch(
        tmp_path,
        {"workflow_key": "test", "run_ref": "t"},
        decision_ref,
        {"formal_ref": group_ref, "materialized_formal_refs": [child_ref]},
    )
    assert handoff_refs
    assert job_refs
    assert any(ref.startswith("artifacts/jobs/waiting-human/") for ref in job_refs)

    held_job_path = tmp_path / job_refs[0]
    payload = json.loads(held_job_path.read_text(encoding="utf-8"))
    assert payload["status"] == "waiting-human"
    assert payload["hold_reason"] == "spec_reconcile_required"
    assert payload["required_preconditions"][0].startswith(package_ref)
    assert payload["required_preconditions"][0].endswith("spec-reconcile-report.json")
    assert payload["spec_reconcile_report_ref"].endswith("spec-reconcile-report.json")


def test_tech_dispatch_releases_when_spec_reconcile_report_has_no_blockers(tmp_path: Path) -> None:
    decision_ref = "artifacts/active/gates/decisions/dec-2.json"
    tech_ref = "formal.tech.TECH-001"
    package_ref = "artifacts/feat-to-tech/run-6"
    package_dir = tmp_path / package_ref
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "spec-findings.json",
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-6"},
            "findings": [],
        },
    )
    _write_json(
        package_dir / "spec-reconcile-report.json",
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-6"},
            "input_spec_findings_ref": f"{package_ref}/spec-findings.json",
            "decisions": [],
            "summary": {"total": 0, "backported": 0, "rejected": 0, "deferred": 0, "recorded": 0},
            "blocking_items": [],
        },
    )
    bind_record(
        tmp_path,
        tech_ref,
        "ssot/formal/tech-001.md",
        "materialized",
        {"workflow_key": "test", "run_ref": "t"},
        metadata={"tech_ref": "TECH-001", "feat_ref": "FEAT-001", "source_package_ref": package_ref},
    )
    handoff_refs, job_refs = build_tech_downstream_dispatch(
        tmp_path,
        {"workflow_key": "test", "run_ref": "t"},
        decision_ref,
        {"formal_ref": tech_ref},
    )
    assert handoff_refs
    assert job_refs
    assert job_refs[0].startswith("artifacts/jobs/ready/")


def test_release_hold_job_denies_missing_precondition_artifact(tmp_path: Path) -> None:
    job_ref = "artifacts/jobs/waiting-human/job-missing-precondition.json"
    job_path = tmp_path / job_ref
    _write_json(
        job_path,
        {
            "job_id": "job-missing-precondition",
            "status": "waiting-human",
            "hold_reason": "manual_operator_hold",
            "required_preconditions": ["artifacts/reports/governance/spec-reconcile/nope.json"],
        },
    )
    with pytest.raises(CommandError) as excinfo:
        release_hold_job(tmp_path, job_ref, actor_ref="operator.test")
    assert excinfo.value.status_code == "PRECONDITION_FAILED"
    assert "missing hold precondition artifact" in excinfo.value.message


def test_release_hold_job_denies_spec_reconcile_without_report_ref(tmp_path: Path) -> None:
    precondition_ref = "artifacts/reports/governance/spec-reconcile/some-other.json"
    _write_json(tmp_path / precondition_ref, {"ok": True})

    job_ref = "artifacts/jobs/waiting-human/job-missing-report-ref.json"
    _write_json(
        tmp_path / job_ref,
        {
            "job_id": "job-missing-report-ref",
            "status": "waiting-human",
            "hold_reason": "spec_reconcile_required",
            "required_preconditions": [precondition_ref],
        },
    )
    with pytest.raises(CommandError) as excinfo:
        release_hold_job(tmp_path, job_ref, actor_ref="operator.test")
    assert excinfo.value.status_code == "PRECONDITION_FAILED"
    assert "spec reconcile hold requires spec-reconcile-report.json ref" in excinfo.value.message


def test_release_hold_job_denies_spec_reconcile_when_blocking_items_present(tmp_path: Path) -> None:
    report_ref = "artifacts/feat-to-tech/run-777/spec-reconcile-report.json"
    _write_json(
        tmp_path / report_ref,
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-777"},
            "blocking_items": ["missing decisions for findings: GAP-777"],
        },
    )

    job_ref = "artifacts/jobs/waiting-human/job-blocking-items.json"
    _write_json(
        tmp_path / job_ref,
        {
            "job_id": "job-blocking-items",
            "status": "waiting-human",
            "hold_reason": "spec_reconcile_required",
            "required_preconditions": [report_ref],
        },
    )
    with pytest.raises(CommandError) as excinfo:
        release_hold_job(tmp_path, job_ref, actor_ref="operator.test")
    assert excinfo.value.status_code == "PRECONDITION_FAILED"
    assert "spec reconcile report still has blocking_items" in excinfo.value.message


def test_release_hold_job_allows_spec_reconcile_when_blocking_items_empty(tmp_path: Path) -> None:
    report_ref = "artifacts/feat-to-tech/run-778/spec-reconcile-report.json"
    _write_json(
        tmp_path / report_ref,
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-778"},
            "blocking_items": [],
        },
    )

    job_ref = "artifacts/jobs/waiting-human/job-no-blockers.json"
    _write_json(
        tmp_path / job_ref,
        {
            "job_id": "job-no-blockers",
            "status": "waiting-human",
            "hold_reason": "spec_reconcile_required",
            "required_preconditions": [report_ref],
        },
    )

    released = release_hold_job(tmp_path, job_ref, actor_ref="operator.test")
    assert released["status"] == "ready"
    assert (tmp_path / released["job_ref"]).exists()


def test_materialization_gate_skips_out_of_scope_candidates(tmp_path: Path) -> None:
    candidate = {"metadata": {"source_package_ref": "artifacts/some-other-workflow/run-1"}}
    ensure_spec_reconcile_ready_for_materialization(tmp_path, candidate=candidate)


def test_materialization_gate_blocks_when_findings_missing(tmp_path: Path) -> None:
    package_ref = "artifacts/feat-to-tech/run-71"
    (tmp_path / package_ref).mkdir(parents=True, exist_ok=True)
    candidate = {"metadata": {"source_package_ref": package_ref}}
    with pytest.raises(CommandError) as excinfo:
        ensure_spec_reconcile_ready_for_materialization(tmp_path, candidate=candidate)
    assert excinfo.value.status_code == "PRECONDITION_FAILED"
    assert "spec reconcile blocks formal materialization" in excinfo.value.message


def test_materialization_gate_blocks_when_report_has_blocking_items(tmp_path: Path) -> None:
    package_ref = "artifacts/feat-to-tech/run-72"
    package_dir = tmp_path / package_ref
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "spec-findings.json",
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-72"},
            "findings": [],
        },
    )
    _write_json(
        package_dir / "spec-reconcile-report.json",
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-72"},
            "blocking_items": ["missing decisions for findings: GAP-001"],
        },
    )
    candidate = {"metadata": {"source_package_ref": package_ref}}
    with pytest.raises(CommandError):
        ensure_spec_reconcile_ready_for_materialization(tmp_path, candidate=candidate)


def test_materialization_gate_allows_clean_reconcile_report(tmp_path: Path) -> None:
    package_ref = "artifacts/feat-to-tech/run-73"
    package_dir = tmp_path / package_ref
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "spec-findings.json",
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-73"},
            "findings": [],
        },
    )
    _write_json(
        package_dir / "spec-reconcile-report.json",
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-73"},
            "blocking_items": [],
        },
    )
    candidate = {"metadata": {"source_package_ref": package_ref}}
    ensure_spec_reconcile_ready_for_materialization(tmp_path, candidate=candidate)
