#!/usr/bin/env python3
"""
Integration-context helpers for feat-to-tech.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


INTEGRATION_CONTEXT_FILENAME = "integration-context.json"
REQUIRED_CONTEXT_LIST_FIELDS = {
    "workflow_inventory": "workflow / loop / skill / CLI inventory",
    "module_boundaries": "module and directory boundaries",
    "legacy_fields_states_interfaces": "legacy fields / states / interfaces",
    "canonical_ownership": "canonical ownership snapshot",
    "compatibility_constraints": "compatibility constraints",
    "migration_modes": "migration mode assumptions",
    "legacy_invariants": "legacy invariants",
    "gate_audit_evidence": "gate / audit / repair / evidence semantics",
    "source_refs": "source / arch / tech / api refs",
}


def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def normalize_integration_context(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    return {
        "artifact_type": str(payload.get("artifact_type") or "integration_context").strip(),
        "schema_version": str(payload.get("schema_version") or "1.0.0").strip(),
        "context_ref": str(payload.get("context_ref") or "").strip(),
        **{name: _ensure_list(payload.get(name)) for name in REQUIRED_CONTEXT_LIST_FIELDS},
    }


def integration_context_errors(payload: Any) -> list[str]:
    context = normalize_integration_context(payload)
    if not context:
        return ["integration_context is required."]
    errors: list[str] = []
    if context.get("artifact_type") != "integration_context":
        errors.append("integration_context artifact_type must be integration_context.")
    for field, label in REQUIRED_CONTEXT_LIST_FIELDS.items():
        if not context.get(field):
            errors.append(f"integration_context missing required field: {field} ({label})")
    return errors


def load_integration_context(artifacts_dir: Path, load_json_fn, feat_bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    artifact_path = artifacts_dir / INTEGRATION_CONTEXT_FILENAME
    if artifact_path.exists():
        return normalize_integration_context(load_json_fn(artifact_path))
    if isinstance(feat_bundle, dict) and isinstance(feat_bundle.get("integration_context"), dict):
        return normalize_integration_context(feat_bundle.get("integration_context"))
    return {}


def integration_context_ref(context: dict[str, Any]) -> str:
    explicit_ref = str(context.get("context_ref") or "").strip()
    return explicit_ref or INTEGRATION_CONTEXT_FILENAME


def integration_sufficiency_check(context: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    issues: list[str] = []
    normalized = normalize_integration_context(context)
    if not normalized:
        return {
            "passed": False,
            "checks": [],
            "issues": ["integration_context missing"],
            "summary": "integration_context missing",
        }
    for field, label in REQUIRED_CONTEXT_LIST_FIELDS.items():
        values = normalized.get(field) or []
        passed = len(values) >= 1
        checks.append({"name": field, "passed": passed, "detail": f"{label}: {len(values)} item(s)"})
        if not passed:
            issues.append(f"Missing {label}.")
    passed = not issues
    return {
        "passed": passed,
        "checks": checks,
        "issues": issues,
        "summary": "integration_context sufficient" if passed else "integration_context missing required system facts",
    }
