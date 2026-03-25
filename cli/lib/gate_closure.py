"""Run closure helpers for gate outcomes."""

from __future__ import annotations

from pathlib import Path

from cli.lib.fs import to_canonical_path, write_json
from cli.lib.registry_store import slugify


def close_run(
    workspace_root: Path,
    trace: dict[str, object],
    run_ref: str,
    request_id: str,
    gate_decision_ref: str = "",
) -> dict[str, str]:
    slug = slugify(f"{run_ref or trace.get('run_ref', 'run')}-{request_id}")
    closure_path = workspace_root / "artifacts" / "active" / "closures" / f"run-closure-{slug}.json"
    write_json(
        closure_path,
        {
            "trace": trace,
            "run_ref": run_ref,
            "gate_decision_ref": gate_decision_ref,
            "final_status": "closed",
            "request_id": request_id,
        },
    )
    return {"run_closure_ref": to_canonical_path(closure_path, workspace_root)}
