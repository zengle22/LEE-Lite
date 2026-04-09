#!/usr/bin/env python3
"""
ADR-043 semantic wiring helpers for feat-to-tech.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cli.lib.tech_semantic_phase1 import build_tech_semantic_artifacts

_DIMENSIONS_PATH = str(Path(__file__).resolve().parents[1] / "resources" / "semantic-dimensions.json")


def attach_executor_semantics(generated: Any) -> None:
    semantic = build_tech_semantic_artifacts(_DIMENSIONS_PATH, generated.json_payload, dict(generated.semantic_drift_check), [])
    for key in ("semantic_dimensions_ref", "semantic_coverage", "semantic_pass", "review_views", "l3_review"):
        generated.json_payload[key] = semantic[key]
        if isinstance(getattr(generated, "review_report", None), dict):
            generated.review_report[key] = semantic[key]
        if isinstance(getattr(generated, "acceptance_report", None), dict):
            generated.acceptance_report[key] = semantic[key]
    if isinstance(getattr(generated, "handoff", None), dict):
        generated.handoff.update(semantic.get("handoff_updates") or {})


def load_l3_review(artifacts_dir: Path, load_json) -> tuple[dict[str, Any], Path]:
    path = artifacts_dir / "l3-review.json"
    payload = load_json(path) if path.exists() else {}
    return payload if isinstance(payload, dict) else {}, path


def persist_l3_review(artifacts_dir: Path, l3_review: dict[str, Any], dump_json) -> Path | None:
    if not isinstance(l3_review, dict) or not l3_review:
        return None
    path = artifacts_dir / "l3-review.json"
    dump_json(path, l3_review)
    return path


def gate_semantic_fields(*, bundle_payload: dict[str, Any], supervision_evidence: dict[str, Any]) -> dict[str, Any]:
    semantic_pass = bool(bundle_payload.get("semantic_pass", False))
    open_gaps = list((bundle_payload.get("semantic_coverage") or {}).get("open_semantic_gaps") or [])
    l3_review = supervision_evidence.get("l3_review") if isinstance(supervision_evidence.get("l3_review"), dict) else {}
    decision = str(l3_review.get("decision") or "").strip().lower()
    return {
        "semantic_pass": semantic_pass,
        "open_semantic_gaps": open_gaps,
        "l3_review_present": decision in {"pass", "revise", "reject"},
        "l3_review_pass": decision == "pass",
    }


def update_handoff_semantic_ready(*, handoff_payload: dict[str, Any], bundle_payload: dict[str, Any], supervision: dict[str, Any]) -> None:
    fields = gate_semantic_fields(bundle_payload=bundle_payload, supervision_evidence=supervision)
    # This handoff is emitted before the external human gate runs, so L3 is advisory here.
    handoff_payload["semantic_ready"] = bool(fields["semantic_pass"])
    handoff_payload["open_semantic_gaps"] = list(fields["open_semantic_gaps"])

