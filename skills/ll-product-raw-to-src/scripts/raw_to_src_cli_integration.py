#!/usr/bin/env python3
"""
CLI runtime integration helpers for raw-to-src.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def commit_candidate_markdown(
    repo_root: Path,
    artifacts_dir: Path,
    run_id: str,
    candidate_markdown: str,
) -> dict[str, Any]:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.ll import main as cli_main

    staging_path = repo_root / ".workflow" / "runs" / run_id / "generated" / "raw-to-src" / "src-candidate.md"
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path.write_text(candidate_markdown, encoding="utf-8")

    request_path = artifacts_dir / "_cli" / "artifact-commit.request.json"
    response_path = artifacts_dir / "_cli" / "artifact-commit.response.json"
    payload = {
        "api_version": "v1",
        "command": "artifact.commit",
        "request_id": f"req-raw-to-src-{run_id}-candidate-commit",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-product-raw-to-src",
        "trace": {"run_ref": run_id, "workflow_key": "product.raw-to-src"},
        "payload": {
            "artifact_ref": f"raw-to-src.{run_id}.src-candidate",
            "workspace_path": f"artifacts/raw-to-src/{run_id}/src-candidate.md",
            "requested_mode": "commit",
            "content_ref": staging_path.relative_to(repo_root).as_posix(),
        },
    }
    _write_json(request_path, payload)

    exit_code = cli_main(
        [
            "artifact",
            "commit",
            "--request",
            str(request_path),
            "--response-out",
            str(response_path),
        ]
    )
    response = json.loads(response_path.read_text(encoding="utf-8"))
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"raw-to-src candidate commit failed: {response.get('status_code')} {response.get('message')}")
    return {
        "request_path": request_path,
        "response_path": response_path,
        "response": response,
    }
