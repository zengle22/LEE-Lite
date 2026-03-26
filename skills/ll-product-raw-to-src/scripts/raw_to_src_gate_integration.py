#!/usr/bin/env python3
"""
Gate pending integration helpers for raw-to-src.
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


def create_gate_ready_package(
    repo_root: Path,
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
                "workflow_key": "product.raw-to-src",
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
        "request_id": f"req-raw-to-src-{run_id}-gate-submit",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-product-raw-to-src",
        "trace": {
            "run_ref": run_id,
            "workflow_key": "product.raw-to-src",
        },
        "payload": {
            "producer_ref": "ll-product-raw-to-src",
            "proposal_ref": proposal_ref,
            "payload_ref": _repo_relative(repo_root, payload_path),
            "pending_state": "gate_pending",
            "trace_context_ref": trace_context_ref,
        },
    }
    _write_json(request_path, request)

    exit_code = cli_main(
        [
            "gate",
            "submit-handoff",
            "--request",
            str(request_path),
            "--response-out",
            str(response_path),
        ]
    )
    response = json.loads(response_path.read_text(encoding="utf-8"))
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"raw-to-src gate submit failed: {response.get('status_code')} {response.get('message')}")
    return {
        "request_path": request_path,
        "response_path": response_path,
        "response": response,
    }
