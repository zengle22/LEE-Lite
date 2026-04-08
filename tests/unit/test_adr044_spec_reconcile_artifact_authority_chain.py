from __future__ import annotations

import json
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path


def _load_spec_reconcile_runtime_module() -> object:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "skills" / "l3" / "ll-governance-spec-reconcile" / "scripts" / "workflow_runtime.py"
    loader = SourceFileLoader("lee_lite_spec_reconcile_runtime", str(script_path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_authority_chain_queue_bootstraps_plan_from_findings_when_missing(tmp_path: Path) -> None:
    runtime = _load_spec_reconcile_runtime_module()
    queue_ref = "artifacts/reports/governance/spec-backport/spec-backport-queue.json"
    spec_findings_ref = "artifacts/feat-to-tech/run-1/spec-findings.json"
    report_ref = "artifacts/feat-to-tech/run-1/spec-reconcile-report.json"
    findings_payload = {
        "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-1"},
        "lineage": [spec_findings_ref],
        "findings": [
            {
                "finding_id": "GAP-100",
                "type": "spec_gap",
                "title": "Missing error code semantics",
                "description": "error_code semantics not defined",
                "affects_future_work": "yes",
                "must_backport": True,
                "status": "open",
                "proposed_ssot_targets": ["ssot/api_contract/API-011.yaml"],
            }
        ],
    }
    decisions = [{"finding_id": "GAP-100", "outcome": "pending", "rationale": ""}]
    updated = runtime._update_queue(
        repo_root=tmp_path,
        queue_ref=queue_ref,
        spec_findings_ref=spec_findings_ref,
        findings_payload=findings_payload,
        decisions=decisions,
        report_ref=report_ref,
    )
    assert updated == queue_ref
    queue = json.loads((tmp_path / queue_ref).read_text(encoding="utf-8"))
    assert queue["items"][0]["finding_id"] == "GAP-100"
    assert queue["items"][0]["target_ssot_paths"] == ["ssot/api_contract/API-011.yaml"]


def test_authority_chain_queue_preserves_existing_plan_over_findings_proposal(tmp_path: Path) -> None:
    runtime = _load_spec_reconcile_runtime_module()
    queue_ref = "artifacts/reports/governance/spec-backport/spec-backport-queue.json"
    queue_path = tmp_path / queue_ref
    _write_json(
        queue_path,
        {
            "artifact_type": "spec_backport_queue",
            "schema_version": "0.1.0",
            "status": "active",
            "items": [
                {
                    "finding_id": "GAP-101",
                    "source_artifact_ref": "artifacts/feat-to-tech/run-2/spec-findings.json",
                    "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-2"},
                    "lineage": ["artifacts/feat-to-tech/run-2/spec-findings.json"],
                    "target_ssot_paths": ["ssot/api_contract/API-011.yaml#planned"],
                    "reconcile_report_ref": "artifacts/feat-to-tech/run-2/spec-reconcile-report.json",
                    "owner": "ssot_owner",
                    "priority": "high",
                    "status": "pending",
                    "notes": "",
                }
            ],
        },
    )

    spec_findings_ref = "artifacts/feat-to-tech/run-2/spec-findings.json"
    report_ref = "artifacts/feat-to-tech/run-2/spec-reconcile-report.json"
    findings_payload = {
        "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-2"},
        "lineage": [spec_findings_ref],
        "findings": [
            {
                "finding_id": "GAP-101",
                "type": "spec_gap",
                "title": "Missing idempotency semantics",
                "description": "idempotency not defined",
                "affects_future_work": "yes",
                "must_backport": True,
                "status": "open",
                "proposed_ssot_targets": ["ssot/api_contract/API-011.yaml#proposal"],
            }
        ],
    }
    decisions = [{"finding_id": "GAP-101", "outcome": "pending", "rationale": ""}]
    runtime._update_queue(
        repo_root=tmp_path,
        queue_ref=queue_ref,
        spec_findings_ref=spec_findings_ref,
        findings_payload=findings_payload,
        decisions=decisions,
        report_ref=report_ref,
    )
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert queue["items"][0]["target_ssot_paths"] == ["ssot/api_contract/API-011.yaml#planned"]


def test_scope_cut_is_not_backport_queue_tracked_in_phase0(tmp_path: Path) -> None:
    runtime = _load_spec_reconcile_runtime_module()
    queue_ref = "artifacts/reports/governance/spec-backport/spec-backport-queue.json"
    spec_findings_ref = "artifacts/feat-to-tech/run-3/spec-findings.json"
    report_ref = "artifacts/feat-to-tech/run-3/spec-reconcile-report.json"
    findings_payload = {
        "trace": {"workflow_key": "dev.feat-to-tech", "run_ref": "run-3"},
        "lineage": [spec_findings_ref],
        "findings": [
            {
                "finding_id": "CUT-300",
                "type": "scope_cut",
                "title": "Skip offline mode",
                "description": "skip offline mode",
                "affects_future_work": "yes",
                "must_backport": True,
                "status": "open",
                "scope_kind": "formal",
                "affected_refs": ["ACCEPT-009"],
            },
            {
                "finding_id": "GAP-300",
                "type": "spec_gap",
                "title": "Missing api default",
                "description": "default missing",
                "affects_future_work": "yes",
                "must_backport": True,
                "status": "open",
                "proposed_ssot_targets": ["ssot/api_contract/API-099.yaml"],
            },
        ],
    }
    decisions = [
        {"finding_id": "CUT-300", "outcome": "deferred", "owner": "ssot_owner", "next_checkpoint": "release"},
        {"finding_id": "GAP-300", "outcome": "pending"},
    ]
    runtime._update_queue(
        repo_root=tmp_path,
        queue_ref=queue_ref,
        spec_findings_ref=spec_findings_ref,
        findings_payload=findings_payload,
        decisions=decisions,
        report_ref=report_ref,
    )
    queue = json.loads((tmp_path / queue_ref).read_text(encoding="utf-8"))
    finding_ids = [item["finding_id"] for item in queue["items"]]
    assert "GAP-300" in finding_ids
    assert "CUT-300" not in finding_ids

