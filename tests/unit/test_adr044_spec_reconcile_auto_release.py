from __future__ import annotations

import json
from pathlib import Path

from cli.lib.job_queue import release_holds_for_spec_reconcile_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_auto_release_promotes_waiting_human_job_to_ready(tmp_path: Path) -> None:
    report_ref = "artifacts/feat-to-tech/run-1/spec-reconcile-report.json"
    _write_json(
        tmp_path / report_ref,
        {
            "artifact_type": "spec_reconcile_report",
            "schema_version": "0.1.0",
            "status": "produced",
            "trace": {"workflow_key": "governance.spec-reconcile", "run_ref": "r-1"},
            "blocking_items": [],
        },
    )

    job_ref = "artifacts/jobs/waiting-human/job-held.json"
    _write_json(
        tmp_path / job_ref,
        {
            "job_id": "job-held",
            "status": "waiting-human",
            "hold_reason": "spec_reconcile_required",
            "required_preconditions": [report_ref],
            "queue_path": job_ref,
        },
    )

    released = release_holds_for_spec_reconcile_report(tmp_path, report_ref=report_ref, actor_ref="operator.test")
    assert released
    assert released[0].startswith("artifacts/jobs/ready/")
    assert (tmp_path / released[0]).exists()


def test_auto_release_ignores_non_spec_reconcile_holds(tmp_path: Path) -> None:
    report_ref = "artifacts/feat-to-tech/run-2/spec-reconcile-report.json"
    _write_json(tmp_path / report_ref, {"blocking_items": []})

    job_ref = "artifacts/jobs/waiting-human/job-other.json"
    _write_json(
        tmp_path / job_ref,
        {
            "job_id": "job-other",
            "status": "waiting-human",
            "hold_reason": "manual_operator_hold",
            "required_preconditions": [report_ref],
            "queue_path": job_ref,
        },
    )

    released = release_holds_for_spec_reconcile_report(tmp_path, report_ref=report_ref, actor_ref="operator.test")
    assert released == []
    assert (tmp_path / job_ref).exists()

