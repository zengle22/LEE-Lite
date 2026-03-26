#!/usr/bin/env python3
"""
Gate pending integration helpers for feat-to-tech.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _repo_relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def create_handoff_proposal(
    repo_root: Path,
    artifacts_dir: Path,
    run_id: str,
    feat_ref: str,
    tech_ref: str,
) -> Path:
    proposal_path = artifacts_dir / "handoff-proposal.json"
    _write_json(
        proposal_path,
        {
            "handoff_id": f"handoff-{run_id}-to-gate",
            "from_skill": "ll-dev-feat-to-tech",
            "to_skill": "governance.gate-human-orchestrator",
            "source_run_id": run_id,
            "feat_ref": feat_ref,
            "tech_ref": tech_ref,
            "primary_artifact_ref": _repo_relative(repo_root, artifacts_dir / "tech-design-bundle.md"),
            "supporting_artifact_refs": [
                _repo_relative(repo_root, artifacts_dir / "tech-design-bundle.json"),
                _repo_relative(repo_root, artifacts_dir / "tech-spec.md"),
                _repo_relative(repo_root, artifacts_dir / "tech-review-report.json"),
                _repo_relative(repo_root, artifacts_dir / "tech-acceptance-report.json"),
                _repo_relative(repo_root, artifacts_dir / "tech-defect-list.json"),
                _repo_relative(repo_root, artifacts_dir / "handoff-to-tech-impl.json"),
            ],
            "required_context": [
                "selected feat boundary",
                "frozen technical design",
                "implementation carrier constraints",
                "downstream impl admission intent",
            ],
            "expected_output_type": "gate_decision_package",
            "status_reason": "Awaiting external gate review before TECH formalization and downstream IMPL admission.",
        },
    )
    return proposal_path


def create_gate_ready_package(
    artifacts_dir: Path,
    run_id: str,
    candidate_ref: str,
    machine_ssot_ref: str,
    acceptance_ref: str,
    evidence_bundle_ref: str,
) -> Path:
    package_path = artifacts_dir / "input" / "gate-ready-package.json"
    _write_json(
        package_path,
        {
            "trace": {
                "run_ref": run_id,
                "workflow_key": "dev.feat-to-tech",
            },
            "payload": {
                "candidate_ref": candidate_ref,
                "machine_ssot_ref": machine_ssot_ref,
                "acceptance_ref": acceptance_ref,
                "evidence_bundle_ref": evidence_bundle_ref,
            },
        },
    )
    return package_path


def submit_gate_pending(
    repo_root: Path,
    artifacts_dir: Path,
    run_id: str,
    proposal_ref: str,
    payload_path: Path,
    trace_context_ref: str,
) -> dict[str, Any]:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.ll import main as cli_main

    request_path = artifacts_dir / "_cli" / "gate-submit-handoff.request.json"
    response_path = artifacts_dir / "_cli" / "gate-submit-handoff.response.json"
    request = {
        "api_version": "v1",
        "command": "gate.submit-handoff",
        "request_id": f"req-feat-to-tech-{run_id}-gate-submit",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-dev-feat-to-tech",
        "trace": {
            "run_ref": run_id,
            "workflow_key": "dev.feat-to-tech",
        },
        "payload": {
            "producer_ref": "ll-dev-feat-to-tech",
            "proposal_ref": proposal_ref,
            "payload_ref": _repo_relative(repo_root, payload_path),
            "pending_state": "gate_pending",
            "trace_context_ref": trace_context_ref,
        },
    }
    _write_json(request_path, request)
    exit_code = cli_main(["gate", "submit-handoff", "--request", str(request_path), "--response-out", str(response_path)])
    response = json.loads(response_path.read_text(encoding="utf-8"))
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"feat-to-tech gate submit failed: {response.get('status_code')} {response.get('message')}")
    return {
        "request_path": request_path,
        "response_path": response_path,
        "response": response,
    }
