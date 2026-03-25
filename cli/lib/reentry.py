"""Decision-driven reentry routing."""

from __future__ import annotations

from pathlib import Path

from cli.lib.fs import load_json, write_json


def build_reentry_directive(
    workspace_root: Path,
    trace: dict[str, object],
    handoff_ref: str,
    decision_ref: str,
    decision: str,
    routing_hint: str,
    producer_ref: str,
) -> dict[str, str]:
    directive_ref = f"artifacts/active/reentry/{Path(handoff_ref).stem}-{decision}.json"
    path = workspace_root / directive_ref
    if path.exists():
        existing = load_json(path)
        if existing.get("decision_ref") == decision_ref:
            return {"boundary_handoff_ref": "", "reentry_directive_ref": directive_ref}
    write_json(
        path,
        {
            "trace": trace,
            "handoff_ref": handoff_ref,
            "decision_ref": decision_ref,
            "decision": decision,
            "routing_hint": routing_hint,
            "producer_ref": producer_ref,
            "replay_guard": f"{handoff_ref}|{decision_ref}",
        },
    )
    return {"boundary_handoff_ref": "", "reentry_directive_ref": directive_ref}
