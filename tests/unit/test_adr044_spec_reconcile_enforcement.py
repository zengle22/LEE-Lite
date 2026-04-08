from __future__ import annotations

import json
from pathlib import Path

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
    assert payload["required_preconditions"] == ["spec_reconcile_report_ref"]
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
