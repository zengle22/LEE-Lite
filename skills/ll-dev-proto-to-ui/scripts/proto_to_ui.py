#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from cli.lib.prototype_review_contract import validate_prototype_review
from cli.lib.ui_semantic_ledger import build_ui_semantic_ledger, validate_ui_semantic_ledger
from cli.lib.workflow_document_test import build_document_test_report, build_fixability_section, validate_document_test_report

OUTPUT_FILES = [
    "package-manifest.json",
    "spec-findings.json",
    "ui-spec-bundle.md",
    "ui-spec-bundle.json",
    "ui-flow-map.md",
    "ui-semantic-source-ledger.json",
    "ui-spec-completeness-report.json",
    "ui-spec-review-report.json",
    "document-test-report.json",
    "ui-spec-defect-list.json",
    "ui-spec-freeze-gate.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def repo_root_from(repo_root: str | None) -> Path:
    return Path(repo_root).resolve() if repo_root else Path.cwd().resolve()


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _shift_markdown_headings(markdown: str, shift: int) -> str:
    if shift <= 0:
        return markdown
    shifted: list[str] = []
    for line in markdown.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            shifted.append(line)
            continue
        hashes = 0
        for ch in stripped:
            if ch == "#":
                hashes += 1
            else:
                break
        if hashes and stripped[hashes : hashes + 1] == " ":
            new_level = min(6, hashes + shift)
            leading_spaces = len(line) - len(stripped)
            shifted.append((" " * leading_spaces) + ("#" * new_level) + stripped[hashes:])
        else:
            shifted.append(line)
    return "\n".join(shifted)


def _resolve_ref_to_path(ref: str, *, input_dir: Path, repo_root: Path) -> Path | None:
    cleaned = str(ref or "").strip()
    if not cleaned:
        return None
    candidate = Path(cleaned)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    input_candidate = (input_dir / candidate).resolve()
    if input_candidate.exists():
        return input_candidate
    repo_candidate = (repo_root / candidate).resolve()
    if repo_candidate.exists():
        return repo_candidate
    return None


def _normalize_ui_spec_filename(ref: str, *, feat_ref: str, index: int) -> str:
    name = Path(str(ref or "").strip()).name
    if name.lower().endswith(".md") and name:
        return name
    if feat_ref:
        return f"[UI-{feat_ref}-{index:03d}]__ui_spec.md"
    return f"[UI-SPEC-{index:03d}]__ui_spec.md"


def _render_expanded_ui_spec_bundle_markdown(
    *,
    feat_ref: str,
    ui_owner_ref: str,
    ui_action: str,
    ui_spec_refs: list[str],
    source_refs: list[str],
    journey_structural_spec_ref: str,
    ui_shell_snapshot_ref: str,
    surface_map_ref: str,
    journey_text: str,
    shell_text: str,
    ui_spec_texts: dict[str, str],
) -> str:
    lines: list[str] = [
        f"# UI Spec Bundle for {feat_ref}",
        "",
        f"- ui_ref: {ui_owner_ref}",
        f"- ui_action: {ui_action}",
        f"- ui_spec_count: {len(ui_spec_refs)}",
        f"- journey_structural_spec_ref: {journey_structural_spec_ref}",
        f"- ui_shell_snapshot_ref: {ui_shell_snapshot_ref}",
        f"- surface_map_ref: {surface_map_ref}",
    ]
    if source_refs:
        lines.extend(["", "## Source Refs", *[f"- {ref}" for ref in source_refs]])
    lines.extend(
        [
            "",
            "## UI Spec Refs",
            *([f"- {ref}" for ref in ui_spec_refs] if ui_spec_refs else ["- (none)"]),
            "",
            "## Journey Structural Spec (Embedded)",
            "",
            _shift_markdown_headings(journey_text.strip(), 1) if journey_text.strip() else "_Missing journey structural spec content._",
            "",
            "## UI Shell Snapshot (Embedded)",
            "",
            _shift_markdown_headings(shell_text.strip(), 1) if shell_text.strip() else "_Missing ui shell snapshot content._",
            "",
            "## UI Specs (Embedded)",
        ]
    )
    if not ui_spec_refs:
        lines.extend(["", "_No UI spec documents resolved._"])
        return "\n".join(lines).rstrip() + "\n"
    for ref in ui_spec_refs:
        content = (ui_spec_texts.get(ref) or "").strip()
        lines.extend(["", f"### {ref}", ""])
        if content:
            lines.append(_shift_markdown_headings(content, 1))
        else:
            lines.append("_Missing UI spec content._")
    return "\n".join(lines).rstrip() + "\n"


JOURNEY_REQUIRED_SECTIONS = (
    "## 1. Journey Main Chain",
    "## 2. Page Map",
    "## 3. Decision Points",
    "## 4. CTA Hierarchy",
    "## 5. Container Hints",
    "## 6. Error / Degraded / Retry Paths",
    "## 7. Open Questions / Frozen Assumptions",
)
SHELL_REQUIRED_SECTIONS = (
    "## App Shell",
    "## Container Rules",
    "## CTA Placement",
    "## State Expression",
    "## Common Structural Components",
    "## Governance",
)


def _resolve_package_ref(input_dir: Path, ref: str) -> Path:
    candidate = Path(str(ref or "").strip())
    return candidate if candidate.is_absolute() else (input_dir / candidate)


def _collect_section_body(text: str, heading: str) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip():
            body.append(line.strip())
    return "\n".join(body).strip()


def _validate_structured_sections(text: str, label: str, headings: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for heading in headings:
        if heading not in text:
            errors.append(f"{label} missing section: {heading}")
            continue
        if not _collect_section_body(text, heading):
            errors.append(f"{label} section has no content: {heading}")
    return errors


def validate_input_package(input_path: str | Path) -> tuple[list[str], dict[str, Any]]:
    input_dir = Path(input_path).resolve()
    errors = [
        f"missing required input artifact: {name}"
        for name in ["prototype-bundle.json", "journey-ux-ascii.md", "ui-shell-spec.md", "prototype-review-report.json", "prototype-freeze-gate.json"]
        if not (input_dir / name).exists()
    ]
    if errors:
        return errors, {}
    bundle = load_json(input_dir / "prototype-bundle.json")
    review = load_json(input_dir / "prototype-review-report.json")
    gate = load_json(input_dir / "prototype-freeze-gate.json")
    if bundle.get("artifact_type") != "prototype_package":
        errors.append("artifact_type must be prototype_package")
    if not bundle.get("pages") and not bundle.get("ui_spec_refs"):
        errors.append("prototype package must contain at least one page or ui_spec_refs")
    for key in (
        "journey_structural_spec_ref",
        "ui_shell_snapshot_ref",
        "ui_shell_source_ref",
        "ui_shell_version",
        "ui_shell_snapshot_hash",
        "shell_change_policy",
        "surface_map_ref",
        "prototype_owner_ref",
        "prototype_action",
    ):
        if not str(bundle.get(key) or "").strip():
            errors.append(f"prototype bundle missing {key}")
    if str(bundle.get("prototype_action") or "").strip() not in {"update", "create"}:
        errors.append("prototype_action must be update or create")
    if not str(bundle.get("ui_owner_ref") or "").strip():
        errors.append("prototype bundle missing ui_owner_ref")
    if str(bundle.get("ui_action") or "").strip() not in {"update", "create"}:
        errors.append("prototype bundle missing valid ui_action")
    journey_ref = _resolve_package_ref(input_dir, str(bundle.get("journey_structural_spec_ref") or ""))
    shell_ref = _resolve_package_ref(input_dir, str(bundle.get("ui_shell_snapshot_ref") or ""))
    if journey_ref.exists():
        errors.extend(_validate_structured_sections(journey_ref.read_text(encoding="utf-8"), "journey structural spec", JOURNEY_REQUIRED_SECTIONS))
    else:
        errors.append(f"referenced journey structural spec missing: {journey_ref}")
    if shell_ref.exists():
        errors.extend(_validate_structured_sections(shell_ref.read_text(encoding="utf-8"), "ui shell snapshot", SHELL_REQUIRED_SECTIONS))
    else:
        errors.append(f"referenced ui shell snapshot missing: {shell_ref}")
    errors.extend(validate_prototype_review(review))
    if review.get("verdict") != "approved":
        errors.append("prototype review verdict must be approved")
    if review.get("blocking_points"):
        errors.append("prototype review must not contain blocking_points")
    if review.get("coverage_declaration", {}).get("not_checked"):
        errors.append("prototype review coverage must not contain not_checked items")
    if not str(review.get("reviewer_identity") or "").strip() or str(review.get("reviewer_identity")) == "pending_human_review":
        errors.append("prototype review must record a real human reviewer identity")
    if not gate.get("freeze_ready"):
        errors.append("prototype-freeze-gate.json freeze_ready must be true")
    return errors, {"input_dir": input_dir, "bundle": bundle, "review": review}


def _ui_spec_markdown(page: dict[str, Any], feat_ref: str) -> str:
    return "\n".join(
        [
            f"# UI Spec {page['page_id']}",
            "",
            f"- feat_ref: {feat_ref}",
            f"- page_title: {page['title']}",
            f"- journey_structural_spec_ref: {page.get('journey_structural_spec_ref', '')}",
            f"- ui_shell_snapshot_ref: {page.get('ui_shell_snapshot_ref', '')}",
            "",
            "## Page Goal",
            page["page_goal"],
            "",
            "## Main Path",
            *[f"- {step}" for step in page["main_path"]],
            "",
            "## Branch Paths",
            *[f"- {branch['title']}: {' / '.join(branch['steps'])}" for branch in page["branch_paths"]],
            "",
            "## States",
            *[f"- {state['name']}: {state['ui_behavior']}" for state in page["states"]],
            "",
            "## Actions",
            *[f"- {button['label']} ({button['action']})" for button in page["buttons"]],
        ]
    )


def _build_document_test(run_id: str, ledger_errors: list[str], review_decision: str) -> dict[str, Any]:
    return build_document_test_report(
        workflow_key="dev.proto-to-ui",
        run_id=run_id,
        tested_at=utc_now(),
        defect_list=[{"severity": "P1", "type": "semantic_ledger", "title": error} for error in ledger_errors],
        structural={"package_integrity": True, "traceability_integrity": True, "blocking": False},
        logic_consistency={"checked_topics": ["prototype_alignment", "semantic_ledger"], "conflicts_found": ledger_errors, "severity": "blocking" if ledger_errors else "none", "blocking": bool(ledger_errors)},
        downstream_readiness={"downstream_target": "ui_implementation_consumer", "consumption_contract_ref": "skills/ll-dev-proto-to-ui/ll.contract.yaml", "ready_for_gate_review": review_decision == "pass", "blocking_gaps": ledger_errors, "missing_contracts": [], "assumption_leaks": []},
        semantic_drift={"revision_context_present": False, "drift_detected": bool(ledger_errors), "drift_items": ledger_errors, "semantic_lock_preserved": not ledger_errors},
        fixability=build_fixability_section(
            recommended_next_action="workflow_rebuild" if ledger_errors else "external_gate_review",
            recommended_actor="workflow_rebuild" if ledger_errors else "external_gate_review",
            rebuild_required=len(ledger_errors),
        ),
    )


def build_package(context: dict[str, Any], repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    bundle = context["bundle"]
    input_dir: Path = context["input_dir"]
    feat_ref = str(bundle.get("feat_ref") or "")
    feat_title = str(bundle.get("feat_title") or "").strip()
    source_refs = [str(ref).strip() for ref in (bundle.get("source_refs") or []) if str(ref).strip()]
    output_dir = repo_root / "artifacts" / "proto-to-ui" / f"{(run_id or feat_ref).lower()}--{feat_ref.lower()}"
    if output_dir.exists() and not allow_update:
        return {"ok": False, "errors": [f"output directory already exists: {output_dir}"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = bundle.get("pages") or []
    requested_ui_spec_refs = [str(item).strip() for item in (bundle.get("ui_spec_refs") or []) if str(item).strip()]
    ui_spec_refs: list[str] = []
    ui_spec_missing: list[str] = []
    ui_spec_texts: dict[str, str] = {}
    ui_spec_sources: list[dict[str, str]] = []
    if requested_ui_spec_refs:
        for index, ref in enumerate(requested_ui_spec_refs, start=1):
            resolved = _resolve_ref_to_path(ref, input_dir=input_dir, repo_root=repo_root)
            if resolved is None:
                ui_spec_missing.append(ref)
                continue
            name = _normalize_ui_spec_filename(ref, feat_ref=feat_ref, index=index)
            content = resolved.read_text(encoding="utf-8")
            write_text(output_dir / name, content)
            ui_spec_refs.append(name)
            ui_spec_texts[name] = content
            ui_spec_sources.append({"requested_ref": ref, "resolved_ref": rel(resolved, repo_root), "local_ref": name})
    else:
        for page in pages:
            page = dict(page)
            page["journey_structural_spec_ref"] = str(bundle.get("journey_structural_spec_ref") or "")
            page["ui_shell_snapshot_ref"] = str(bundle.get("ui_shell_snapshot_ref") or "")
            name = f"[UI-{feat_ref}-{page['page_id']}]__ui_spec.md"
            content = _ui_spec_markdown(page, feat_ref)
            write_text(output_dir / name, content)
            ui_spec_refs.append(name)
            ui_spec_texts[name] = content
            ui_spec_sources.append({"requested_ref": name, "resolved_ref": rel(output_dir / name, repo_root), "local_ref": name})

    journey_ref = _resolve_ref_to_path(str(bundle.get("journey_structural_spec_ref") or ""), input_dir=input_dir, repo_root=repo_root)
    shell_ref = _resolve_ref_to_path(str(bundle.get("ui_shell_snapshot_ref") or ""), input_dir=input_dir, repo_root=repo_root)
    journey_text = journey_ref.read_text(encoding="utf-8") if journey_ref and journey_ref.exists() else ""
    shell_text = shell_ref.read_text(encoding="utf-8") if shell_ref and shell_ref.exists() else ""
    ledger = build_ui_semantic_ledger(
        from_prototype=[
            {"semantic_area": "layout", "refs": [f"prototype/index.html#{page['page_id']}"]} for page in pages
        ] + [{"semantic_area": "flow", "refs": ["prototype/mock-data.json"]}, {"semantic_area": "cta_hierarchy", "refs": ["prototype/app.js"]}],
        from_feat=[
            {"semantic_area": "business_constraints", "refs": list(bundle.get("source_refs") or [])},
            {"semantic_area": "completion_criteria", "refs": list(bundle.get("source_refs") or [])},
        ],
        from_other_authority=[
            {"semantic_area": "journey_structure", "refs": [str(bundle.get("journey_structural_spec_ref") or "")]},
            {"semantic_area": "journey_container_hints", "refs": [str(bundle.get("journey_structural_spec_ref") or "")]},
            {"semantic_area": "shell_frame", "refs": [str(bundle.get("ui_shell_snapshot_ref") or "")]},
            {"semantic_area": "shell_container_rules", "refs": [str(bundle.get("ui_shell_snapshot_ref") or "")]},
        ],
        inferred_by_ai=[
            {
                "semantic_area": "field_defaults",
                "rationale": "prototype package does not carry field-level defaults; generated UI spec leaves implementation-facing defaults explicit.",
                "confidence": "medium",
                "requires_explicit_review": False,
            }
        ],
    )
    ledger_errors = validate_ui_semantic_ledger(ledger)
    completeness_errors: list[str] = []
    if ui_spec_missing:
        completeness_errors.append(f"unresolved ui_spec_refs: {', '.join(ui_spec_missing)}")
    if not ui_spec_refs:
        completeness_errors.append("no ui_spec_refs resolved; ui-spec bundle must embed at least one UI spec document")
    all_errors = [*ledger_errors, *completeness_errors]
    review_decision = "revise" if all_errors else "pass"
    document_test = _build_document_test(run_id or feat_ref, all_errors, review_decision)
    ui_owner_ref = str(bundle.get("ui_owner_ref") or "").strip()
    ui_action = str(bundle.get("ui_action") or "").strip()
    related_feat_refs = [str(item).strip() for item in (bundle.get("related_feat_refs") or []) if str(item).strip()]
    if feat_ref not in related_feat_refs:
        related_feat_refs = [feat_ref, *[item for item in related_feat_refs if item != feat_ref]]

    spec_findings_path = output_dir / "spec-findings.json"
    write_json(
        spec_findings_path,
        {
            "artifact_type": "spec_findings",
            "schema_version": "0.1.0",
            "status": "open",
            "trace": {"workflow_key": "dev.proto-to-ui", "run_ref": run_id or feat_ref},
            "lineage": [],
            "findings": [],
        },
    )

    write_json(
        output_dir / "package-manifest.json",
        {
            "artifact_type": "ui_spec_package",
            "workflow_key": "dev.proto-to-ui",
            "run_id": run_id or feat_ref,
            "feat_ref": feat_ref,
            "ui_ref": ui_owner_ref,
            "ui_owner_ref": ui_owner_ref,
            "ui_action": ui_action,
            "ui_spec_refs": ui_spec_refs,
            "journey_structural_spec_ref": str(bundle.get("journey_structural_spec_ref") or ""),
            "ui_shell_snapshot_ref": str(bundle.get("ui_shell_snapshot_ref") or ""),
            "surface_map_ref": str(bundle.get("surface_map_ref") or ""),
            "spec_findings_ref": rel(spec_findings_path, repo_root),
        },
    )
    write_json(
        output_dir / "ui-spec-bundle.json",
        {
            "artifact_type": "ui_spec_package",
            "workflow_key": "dev.proto-to-ui",
            "feat_ref": feat_ref,
            "feat_title": feat_title,
            "title": f"UI Spec Bundle for {feat_ref}",
            "ui_ref": ui_owner_ref,
            "ui_owner_ref": ui_owner_ref,
            "ui_action": ui_action,
            "ui_spec_refs": ui_spec_refs,
            "ui_spec_source_refs": ui_spec_sources,
            "ui_spec_unresolved_refs": ui_spec_missing,
            "source_package_ref": str(context["input_dir"]),
            "source_refs": source_refs,
            "ui_spec_count": len(ui_spec_refs),
            "journey_structural_spec_ref": str(bundle.get("journey_structural_spec_ref") or ""),
            "ui_shell_snapshot_ref": str(bundle.get("ui_shell_snapshot_ref") or ""),
            "surface_map_ref": str(bundle.get("surface_map_ref") or ""),
            "prototype_owner_ref": str(bundle.get("prototype_owner_ref") or ""),
            "prototype_action": str(bundle.get("prototype_action") or ""),
            "related_feat_refs": related_feat_refs,
        },
    )
    write_text(
        output_dir / "ui-spec-bundle.md",
        _render_expanded_ui_spec_bundle_markdown(
            feat_ref=feat_ref,
            ui_owner_ref=ui_owner_ref,
            ui_action=ui_action,
            ui_spec_refs=ui_spec_refs,
            source_refs=source_refs,
            journey_structural_spec_ref=str(bundle.get("journey_structural_spec_ref") or ""),
            ui_shell_snapshot_ref=str(bundle.get("ui_shell_snapshot_ref") or ""),
            surface_map_ref=str(bundle.get("surface_map_ref") or ""),
            journey_text=journey_text,
            shell_text=shell_text,
            ui_spec_texts=ui_spec_texts,
        ),
    )
    if pages:
        flow_items = [f"{index+1}. {page['title']}" for index, page in enumerate(pages)]
    else:
        flow_items = [f"{index+1}. {ref}" for index, ref in enumerate(ui_spec_refs)]
    write_text(output_dir / "ui-flow-map.md", "\n".join(["# UI Flow Map", "", *flow_items]))
    write_json(output_dir / "ui-semantic-source-ledger.json", ledger)
    write_json(
        output_dir / "ui-spec-completeness-report.json",
        {
            "gate_name": "UI Spec Completeness Check",
            "decision": "fail" if all_errors else "pass",
            "checked_at": utc_now(),
            "ledger_errors": ledger_errors,
            "completeness_errors": completeness_errors,
            "unresolved_ui_spec_refs": ui_spec_missing,
            "resolved_ui_spec_refs": ui_spec_refs,
        },
    )
    write_json(
        output_dir / "ui-spec-review-report.json",
        {
            "workflow_key": "dev.proto-to-ui",
            "decision": review_decision,
            "reviewed_at": utc_now(),
            "summary": "ui spec package ready for gate review" if not all_errors else "ui spec package requires revision",
        },
    )
    write_json(output_dir / "document-test-report.json", document_test)
    defect_list: list[dict[str, str]] = [{"severity": "P1", "type": "semantic_ledger", "title": error} for error in ledger_errors]
    defect_list.extend([{"severity": "P1", "type": "completeness", "title": error} for error in completeness_errors])
    write_json(output_dir / "ui-spec-defect-list.json", defect_list)
    write_json(
        output_dir / "ui-spec-freeze-gate.json",
        {
            "workflow_key": "dev.proto-to-ui",
            "freeze_ready": not all_errors,
            "checked_at": utc_now(),
            "checks": {
                "semantic_source_ledger_valid": not ledger_errors,
                "ui_spec_completeness_valid": not completeness_errors,
                "ui_spec_refs_resolved": not ui_spec_missing,
            },
        },
    )
    write_json(output_dir / "execution-evidence.json", {"workflow_key": "dev.proto-to-ui", "run_id": run_id or feat_ref, "generated_at": utc_now(), "artifacts_dir": str(output_dir)})
    write_json(output_dir / "supervision-evidence.json", {"workflow_key": "dev.proto-to-ui", "run_id": run_id or feat_ref, "review_completed_at": utc_now(), "decision": review_decision})
    return {"ok": not all_errors, "artifacts_dir": str(output_dir), "errors": all_errors}


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors = [f"missing required output artifact: {name}" for name in OUTPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {}
    ledger = load_json(artifacts_dir / "ui-semantic-source-ledger.json")
    report = load_json(artifacts_dir / "document-test-report.json")
    bundle = load_json(artifacts_dir / "ui-spec-bundle.json")
    errors.extend(validate_ui_semantic_ledger(ledger))
    errors.extend(validate_document_test_report(report))
    for key in ("journey_structural_spec_ref", "ui_shell_snapshot_ref", "surface_map_ref", "ui_ref", "ui_owner_ref", "ui_action"):
        if not str(bundle.get(key) or "").strip():
            errors.append(f"ui-spec bundle missing {key}")
    for ref in [str(item).strip() for item in (bundle.get("ui_spec_refs") or []) if str(item).strip()]:
        path = artifacts_dir / ref
        if not path.exists():
            errors.append(f"ui-spec bundle references missing ui spec doc: {ref}")
            continue
        if not path.read_text(encoding="utf-8").strip():
            errors.append(f"ui spec doc is empty: {ref}")
    if str(bundle.get("ui_ref") or "").strip() != str(bundle.get("ui_owner_ref") or "").strip():
        errors.append("ui-spec bundle ui_ref must equal ui_owner_ref")
    return errors, {"ledger": ledger, "report": report, "bundle": bundle}


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
    if not errors:
        completeness = load_json(artifacts_dir / "ui-spec-completeness-report.json")
        if str(completeness.get("decision") or "").strip() != "pass":
            errors.append("ui spec completeness report did not pass")
        gate = load_json(artifacts_dir / "ui-spec-freeze-gate.json")
        if gate.get("freeze_ready") is not True:
            errors.append("ui spec freeze gate is not ready")
    return (not errors, errors)


def collect_evidence_report(artifacts_dir: Path) -> Path:
    report_path = artifacts_dir / "evidence-report.md"
    if not report_path.exists():
        write_text(report_path, "# Proto to UI Evidence Report\n")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the proto-to-ui workflow.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--repo-root")
    run.add_argument("--run-id")
    run.add_argument("--allow-update", action="store_true")
    run.set_defaults(func=command_run)
    vin = sub.add_parser("validate-input")
    vin.add_argument("--input", required=True)
    vin.set_defaults(func=command_validate_input)
    vout = sub.add_parser("validate-output")
    vout.add_argument("--artifacts-dir", required=True)
    vout.set_defaults(func=command_validate_output)
    ready = sub.add_parser("validate-package-readiness")
    ready.add_argument("--artifacts-dir", required=True)
    ready.set_defaults(func=command_validate_package_readiness)
    ev = sub.add_parser("collect-evidence")
    ev.add_argument("--artifacts-dir", required=True)
    ev.set_defaults(func=command_collect_evidence)
    freeze = sub.add_parser("freeze-guard")
    freeze.add_argument("--artifacts-dir", required=True)
    freeze.set_defaults(func=command_validate_package_readiness)
    return parser


def command_run(args: argparse.Namespace) -> int:
    errors, context = validate_input_package(args.input)
    result = {"ok": False, "errors": errors}
    if not errors:
        result = build_package(context, repo_root_from(args.repo_root), args.run_id or "", args.allow_update)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def command_validate_input(args: argparse.Namespace) -> int:
    errors, _ = validate_input_package(args.input)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


def command_validate_output(args: argparse.Namespace) -> int:
    errors, _ = validate_output_package(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


def command_validate_package_readiness(args: argparse.Namespace) -> int:
    ok, errors = validate_package_readiness(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


def command_collect_evidence(args: argparse.Namespace) -> int:
    print(json.dumps({"ok": True, "report_path": str(collect_evidence_report(Path(args.artifacts_dir).resolve()))}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
