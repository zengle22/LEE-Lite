"""Markdown rendering helpers for formal publication."""

from __future__ import annotations

from typing import Any

import yaml

from cli.lib.formalization_snapshot import normalize_list


def render_formal_src_markdown(
    snapshot: dict[str, Any],
    assigned_id: str,
    decision_ref: str,
    frozen_at: str,
) -> str:
    frontmatter = {
        "id": assigned_id,
        "ssot_type": "SRC",
        "title": snapshot["title"],
        "status": "frozen",
        "version": snapshot["version"],
        "schema_version": "1.0.0",
        "src_root_id": f"src-root-{assigned_id.lower()}",
        "workflow_key": snapshot["workflow_key"],
        "workflow_run_id": snapshot["workflow_run_id"],
        "source_kind": snapshot["source_kind"],
        "source_refs": snapshot["source_refs"],
        "candidate_package_ref": snapshot["candidate_package_ref"],
        "gate_decision_ref": decision_ref,
        "frozen_at": frozen_at,
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{header}\n---\n\n{snapshot['body'].strip()}\n"


def render_formal_epic_markdown(
    snapshot: dict[str, Any],
    assigned_id: str,
    decision_ref: str,
    frozen_at: str,
) -> str:
    candidate_json = snapshot["candidate_json"]
    depends_on = normalize_list(candidate_json.get("prerequisite_foundations") or candidate_json.get("source_refs"))
    frontmatter = {
        "id": assigned_id,
        "ssot_type": "EPIC",
        "src_ref": str(candidate_json.get("src_root_id") or "").strip(),
        "title": snapshot["title"],
        "status": "accepted",
        "schema_version": "1.0.0",
        "epic_root_id": assigned_id,
        "workflow_key": snapshot["workflow_key"],
        "workflow_run_id": snapshot["workflow_run_id"],
        "candidate_package_ref": snapshot["candidate_package_ref"],
        "gate_decision_ref": decision_ref,
        "depends_on": depends_on,
        "frozen_at": frozen_at,
    }
    if snapshot.get("acceptance_summary"):
        frontmatter["acceptance_summary"] = snapshot["acceptance_summary"]
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{header}\n---\n\n{snapshot['body'].strip()}\n"


def render_acceptance_checks(checks: list[dict[str, Any]]) -> str:
    if not checks:
        return "- None."
    lines: list[str] = []
    for idx, check in enumerate(checks, start=1):
        scenario = str(check.get("scenario") or f"Check {idx}").strip()
        then = str(check.get("then") or "").strip()
        lines.append(f"{idx}. {scenario}")
        if then:
            lines.append(f"   Then: {then}")
    return "\n".join(lines)


def render_formal_feat_markdown(
    snapshot: dict[str, Any],
    feature: dict[str, Any],
    assigned_id: str,
    decision_ref: str,
    frozen_at: str,
) -> str:
    feat_ref = str(feature.get("feat_ref") or assigned_id).strip() or assigned_id
    title = str(feature.get("title") or feat_ref).strip() or feat_ref
    frontmatter = {
        "id": assigned_id,
        "ssot_type": "FEAT",
        "feat_ref": feat_ref,
        "epic_ref": str(snapshot["candidate_json"].get("epic_freeze_ref") or "").strip(),
        "title": title,
        "status": "accepted",
        "schema_version": "1.0.0",
        "workflow_key": snapshot["workflow_key"],
        "workflow_run_id": snapshot["workflow_run_id"],
        "candidate_package_ref": snapshot["candidate_package_ref"],
        "gate_decision_ref": decision_ref,
        "frozen_at": frozen_at,
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    scope = "\n".join(f"- {item}" for item in normalize_list(feature.get("scope"))) or "- None."
    constraints = "\n".join(f"- {item}" for item in normalize_list(feature.get("constraints"))) or "- None."
    checks = render_acceptance_checks(feature.get("acceptance_checks") or [])
    body = "\n".join(
        [
            f"# {title}",
            "",
            "## Goal",
            str(feature.get("goal") or "").strip() or "TBD",
            "",
            "## Scope",
            scope,
            "",
            "## Constraints",
            constraints,
            "",
            "## Acceptance Checks",
            checks,
        ]
    )
    return f"---\n{header}\n---\n\n{body}\n"


def render_formal_tech_markdown(
    snapshot: dict[str, Any],
    assigned_id: str,
    decision_ref: str,
    frozen_at: str,
) -> str:
    candidate_json = snapshot["candidate_json"]
    frontmatter = {
        "id": assigned_id,
        "ssot_type": "TECH",
        "tech_ref": str(candidate_json.get("tech_ref") or assigned_id).strip() or assigned_id,
        "feat_ref": str(candidate_json.get("feat_ref") or "").strip(),
        "title": snapshot["title"],
        "status": "accepted",
        "schema_version": "1.0.0",
        "workflow_key": snapshot["workflow_key"],
        "workflow_run_id": snapshot["workflow_run_id"],
        "candidate_package_ref": snapshot["candidate_package_ref"],
        "gate_decision_ref": decision_ref,
        "frozen_at": frozen_at,
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{header}\n---\n\n{snapshot['body'].strip()}\n"


def render_formal_testset_yaml(
    test_set_yaml: dict[str, Any],
    assigned_id: str,
    decision_ref: str,
    frozen_at: str,
    candidate_package_ref: str,
) -> str:
    payload = dict(test_set_yaml)
    payload["id"] = assigned_id
    payload["ssot_type"] = "TESTSET"
    payload["status"] = "frozen"
    payload["candidate_package_ref"] = candidate_package_ref
    payload["gate_decision_ref"] = decision_ref
    payload["frozen_at"] = frozen_at
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)


def render_formal_impl_markdown(
    snapshot: dict[str, Any],
    assigned_id: str,
    decision_ref: str,
    frozen_at: str,
) -> str:
    candidate_json = snapshot["candidate_json"]
    frontmatter = {
        "id": assigned_id,
        "ssot_type": "IMPL",
        "impl_ref": str(candidate_json.get("impl_ref") or assigned_id).strip() or assigned_id,
        "tech_ref": str(candidate_json.get("tech_ref") or "").strip(),
        "feat_ref": str(candidate_json.get("feat_ref") or "").strip(),
        "title": snapshot["title"],
        "status": "accepted",
        "schema_version": "1.0.0",
        "workflow_key": snapshot["workflow_key"],
        "workflow_run_id": snapshot["workflow_run_id"],
        "candidate_package_ref": snapshot["candidate_package_ref"],
        "gate_decision_ref": decision_ref,
        "frozen_at": frozen_at,
    }
    header = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{header}\n---\n\n{snapshot['body'].strip()}\n"
