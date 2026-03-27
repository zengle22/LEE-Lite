#!/usr/bin/env python3
"""Governed commit helpers for feat-to-testset."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from feat_to_testset_common import dump_json, load_json, parse_markdown_frontmatter, render_markdown


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def commit_bundle_markdown(repo_root: Path, artifacts_dir: Path, run_id: str, markdown_text: str, request_suffix: str) -> dict[str, Any]:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.ll import main as cli_main

    staging_path = repo_root / ".workflow" / "runs" / run_id / "generated" / "feat-to-testset" / f"{request_suffix}.md"
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path.write_text(markdown_text, encoding="utf-8")

    request_path = artifacts_dir / "_cli" / f"{request_suffix}.request.json"
    response_path = artifacts_dir / "_cli" / f"{request_suffix}.response.json"
    payload = {
        "api_version": "v1",
        "command": "artifact.commit",
        "request_id": f"req-feat-to-testset-{run_id}-{request_suffix}",
        "workspace_root": repo_root.as_posix(),
        "actor_ref": "ll-qa-feat-to-testset",
        "trace": {"run_ref": run_id, "workflow_key": "qa.feat-to-testset"},
        "payload": {
            "artifact_ref": f"feat-to-testset.{run_id}.test-set-bundle",
            "workspace_path": f"artifacts/feat-to-testset/{run_id}/test-set-bundle.md",
            "requested_mode": "commit",
            "content_ref": staging_path.relative_to(repo_root).as_posix(),
        },
    }
    _write_json(request_path, payload)
    exit_code = cli_main(["artifact", "commit", "--request", str(request_path), "--response-out", str(response_path)])
    response = load_json(response_path)
    if exit_code != 0 or response.get("status_code") != "OK":
        raise RuntimeError(f"feat-to-testset bundle commit failed: {response.get('status_code')} {response.get('message')}")
    return {"request_path": request_path, "response_path": response_path, "response": response}


def refresh_supervisor_bundle(repo_root: Path, artifacts_dir: Path, status: str) -> dict[str, Any]:
    markdown_path = artifacts_dir / "test-set-bundle.md"
    markdown_text = markdown_path.read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    frontmatter["status"] = status
    updated_markdown = render_markdown(frontmatter, body)
    markdown_path.write_text(updated_markdown, encoding="utf-8")
    return commit_bundle_markdown(repo_root, artifacts_dir, artifacts_dir.name, updated_markdown, "test-set-bundle-supervisor-commit")
