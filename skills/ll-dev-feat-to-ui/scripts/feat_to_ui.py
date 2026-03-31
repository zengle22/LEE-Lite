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

from cli.lib.registry_store import bind_record
from cli.lib.workflow_revision import load_revision_request, materialize_revision_request, normalize_revision_context
from feat_to_ui_document_test import build_document_test, validate_document_test
from feat_to_ui_gate_integration import create_gate_ready_package, create_handoff_proposal, submit_gate_pending
from feat_to_ui_spec import assess_unit, build_units, d_list, first, render_spec, s_list, slugify

INPUT_FILES = [
    "package-manifest.json",
    "feat-freeze-bundle.md",
    "feat-freeze-bundle.json",
    "feat-review-report.json",
    "feat-acceptance-report.json",
    "feat-defect-list.json",
    "feat-freeze-gate.json",
    "handoff-to-feat-downstreams.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
OUTPUT_FILES = [
    "package-manifest.json",
    "ui-spec-bundle.md",
    "ui-spec-bundle.json",
    "ui-flow-map.md",
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


def repo_root_from(repo_root: str | None) -> Path:
    return Path(repo_root).resolve() if repo_root else Path.cwd().resolve()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _render_bundle_markdown(feat_ref: str, bundle: dict[str, Any], units: list[dict[str, Any]], overall: str) -> str:
    return "\n".join(
        [
            f"# UI Spec Bundle for {feat_ref}",
            "",
            "## Selected FEAT",
            f"- feat_ref: {feat_ref}",
            f"- title: {bundle['feat_title']}",
            f"- ui_spec_count: {bundle['ui_spec_count']}",
            f"- completeness_result: {overall}",
            "",
            "## UI Spec Inventory",
            *[f"- {unit['ui_spec_id']} | {unit['page_name']} | {unit['completeness_result']}" for unit in units],
            "",
            "## Traceability",
            *[f"- {item}" for item in bundle["source_refs"]],
        ]
    )


def _render_flow_map(feat_ref: str, bundle: dict[str, Any], units: list[dict[str, Any]], flow_edges: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            f"# UI Flow Map for {feat_ref}",
            "",
            "## Package Entry / Exit",
            f"- package_entry_spec_id: {bundle['package_entry_spec_id']}",
            f"- package_exit_spec_id: {bundle['package_exit_spec_id']}",
            "",
            "## UI Spec Order",
            *[
                f"{index}. {unit['ui_spec_id']} | {unit['page_name']} | {'主页面' if index == 1 else '后续页面'}"
                for index, unit in enumerate(units, start=1)
            ],
            "",
            "## Flow Edges",
            *([f"- {edge['from']} -> {edge['to']} ({edge['relation']})" for edge in flow_edges] or ["- 单页场景，无跨页面边。"]),
            "",
            "## Package Flow Notes",
            "- 本文件用于多 UI Spec 场景下的包级总览。",
            "- 单页场景仍保留该文件，以固定 package-level index 形态。",
        ]
    )


def _recompute_review_gate(
    *,
    artifacts_dir: Path,
    bundle: dict[str, Any],
    units: list[dict[str, Any]],
    flow_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    missing_ui_spec_files: list[str] = []
    stale_ui_specs: list[str] = []
    for unit in units:
        spec_path = artifacts_dir / Path(str(unit["output_ref"])).name
        if not spec_path.exists():
            missing_ui_spec_files.append(unit["ui_spec_id"])
            continue
        expected_body = render_spec(unit).rstrip() + "\n"
        if spec_path.read_text(encoding="utf-8") != expected_body:
            stale_ui_specs.append(unit["ui_spec_id"])
    expected_bundle_markdown = _render_bundle_markdown(str(bundle.get("feat_ref") or ""), bundle, units, str(bundle.get("completeness_result") or ""))
    expected_flow_map = _render_flow_map(str(bundle.get("feat_ref") or ""), bundle, units, flow_edges)
    bundle_index_matches = (artifacts_dir / "ui-spec-bundle.md").read_text(encoding="utf-8") == expected_bundle_markdown.rstrip() + "\n"
    flow_map_matches = (artifacts_dir / "ui-flow-map.md").read_text(encoding="utf-8") == expected_flow_map.rstrip() + "\n"
    review_gate_ok = not missing_ui_spec_files and not stale_ui_specs and bundle_index_matches and flow_map_matches
    return {
        "review_gate_ok": review_gate_ok,
        "missing_ui_spec_files": missing_ui_spec_files,
        "stale_ui_specs": stale_ui_specs,
        "bundle_index_matches": bundle_index_matches,
        "flow_map_matches": flow_map_matches,
        "summary": "Current UI artifacts match the canonical bundle." if review_gate_ok else "Current UI artifacts drift from the canonical bundle.",
    }


def _update_document_test_report(
    document_test_report: dict[str, Any],
    *,
    overall: str,
    review_gate: dict[str, Any],
) -> dict[str, Any]:
    blocking_items = [str(item).strip() for item in review_gate.get("missing_ui_spec_files", []) if str(item).strip()]
    blocking_items.extend(str(item).strip() for item in review_gate.get("stale_ui_specs", []) if str(item).strip())
    if review_gate.get("bundle_index_matches") is False:
        blocking_items.append("ui-spec-bundle.md")
    if review_gate.get("flow_map_matches") is False:
        blocking_items.append("ui-flow-map.md")
    blocking_detected = overall == "fail" or bool(blocking_items)
    document_test_report = dict(document_test_report)
    document_test_report["tested_at"] = utc_now()
    document_test_report["test_outcome"] = "blocking_defect_found" if blocking_detected else "no_blocking_defect_found"
    document_test_report["defect_counts"] = {"blocking": len(blocking_items), "non_blocking": 0}
    document_test_report["recommended_next_action"] = "workflow_rebuild" if blocking_detected else "external_gate_review"
    document_test_report["recommended_actor"] = "workflow_rebuild" if blocking_detected else "external_gate_review"
    sections = document_test_report.get("sections") if isinstance(document_test_report.get("sections"), dict) else {}
    semantic_drift = dict(sections.get("semantic_drift") or {})
    semantic_drift.update(
        {
            "drift_detected": bool(blocking_items),
            "drift_items": blocking_items,
            "semantic_lock_preserved": not blocking_items,
        }
    )
    downstream = dict(sections.get("downstream_readiness") or {})
    downstream.update(
        {
            "ready_for_gate_review": not blocking_detected,
            "blocking_gaps": blocking_items,
        }
    )
    fixability = dict(sections.get("fixability") or {})
    fixability.update(
        {
            "recommended_next_action": "workflow_rebuild" if blocking_detected else "external_gate_review",
            "recommended_actor": "workflow_rebuild" if blocking_detected else "external_gate_review",
            "rebuild_required": len(blocking_items),
        }
    )
    document_test_report["sections"] = {**sections, "semantic_drift": semantic_drift, "downstream_readiness": downstream, "fixability": fixability}
    return document_test_report

def validate_input_package(input_path: str | Path, feat_ref: str, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    input_dir = Path(input_path).resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        return [f"input path is not a directory: {input_dir}"], {}
    errors = [f"missing required input artifact: {name}" for name in INPUT_FILES if not (input_dir / name).exists()]
    if errors:
        return errors, {}
    bundle = load_json(input_dir / "feat-freeze-bundle.json")
    gate = load_json(input_dir / "feat-freeze-gate.json")
    feature = next((item for item in d_list(bundle.get("features")) if str(item.get("feat_ref")) == feat_ref), None)
    if bundle.get("artifact_type") != "feat_freeze_package":
        errors.append("artifact_type must be feat_freeze_package")
    if bundle.get("workflow_key") != "product.epic-to-feat":
        errors.append("workflow_key must be product.epic-to-feat")
    if str(bundle.get("status") or "").strip() not in {"accepted", "frozen"}:
        errors.append("status must be accepted or frozen")
    if not gate.get("freeze_ready"):
        errors.append("feat-freeze-gate.json freeze_ready must be true")
    if feature is None:
        errors.append(f"selected feat_ref not found in bundle: {feat_ref}")
    if feature and feature.get("ui_required") is False:
        errors.append(f"selected FEAT {feat_ref} explicitly disables UI derivation via ui_required=false")
    return errors, {"input_dir": input_dir, "bundle": bundle, "feature": feature, "feat_ref": feat_ref, "repo_root": repo_root}

def build_package(context: dict[str, Any], repo_root: Path, run_id: str, allow_update: bool) -> dict[str, Any]:
    feat_ref = context["feat_ref"]
    feature = context["feature"]
    output_dir = repo_root / "artifacts" / "feat-to-ui" / f"{slugify(run_id or feat_ref)}--{slugify(feat_ref)}"
    if output_dir.exists() and not allow_update:
        return {"ok": False, "errors": [f"output directory already exists: {output_dir}"], "artifacts_dir": str(output_dir)}
    if allow_update and (output_dir / "package-manifest.json").exists():
        _withdraw_previous_gate_submission(repo_root, load_json(output_dir / "package-manifest.json"))
    output_dir.mkdir(parents=True, exist_ok=True)
    revision_request, loaded_revision_path = load_revision_request(context.get("revision_request_path"), artifacts_dir=output_dir, load_json=load_json)
    revision_request_ref, _, _ = materialize_revision_request(
        output_dir,
        revision_request=revision_request,
        load_json=load_json,
        dump_json=write_json,
        delete_if_missing=True,
    )
    revision_context = normalize_revision_context(revision_request, repo_root=repo_root, revision_request_path=loaded_revision_path or (Path(revision_request_ref) if revision_request_ref else None)) or None
    for stale in output_dir.glob("*__ui_spec.md"):
        stale.unlink()
    units, questions = [], []
    for unit in build_units(feature, feat_ref):
        decision, checklist, unit_questions = assess_unit(unit)
        spec_id = f"UI-{feat_ref}-{unit['slug']}"
        output_name = f"[{spec_id}]__ui_spec.md"
        unit.update({"ui_spec_id": spec_id, "linked_feat": feat_ref, "output_ref": rel(output_dir / output_name, repo_root), "completeness_result": decision, "checklist": checklist, "open_questions": unit_questions})
        write_text(output_dir / output_name, render_spec(unit))
        units.append(unit)
        questions.extend(unit_questions)
    overall = "fail" if any(unit["completeness_result"] == "fail" for unit in units) else "pass" if all(unit["completeness_result"] == "pass" for unit in units) else "conditional_pass"
    flow_edges = [{"from": units[index]["ui_spec_id"], "to": units[index + 1]["ui_spec_id"], "relation": "next"} for index in range(len(units) - 1)]
    bundle = {
        "artifact_type": "ui_spec_package",
        "workflow_key": "dev.feat-to-ui",
        "workflow_run_id": run_id or slugify(feat_ref),
        "status": overall,
        "schema_version": "1.0.0",
        "feat_ref": feat_ref,
        "feat_title": first(feature.get("title"), feat_ref),
        "ui_spec_count": len(units),
        "ui_spec_refs": [unit["output_ref"] for unit in units],
        "ui_specs": units,
        "package_entry_spec_id": units[0]["ui_spec_id"],
        "package_exit_spec_id": units[-1]["ui_spec_id"],
        "flow_edges": flow_edges,
        "completeness_result": overall,
        "gate_name": "UI Spec Completeness Check",
        "source_refs": s_list(feature.get("source_refs")) or s_list(context["bundle"].get("source_refs")),
        "open_questions": sorted(set(questions)),
        "source_package_ref": rel(context["input_dir"], repo_root),
    }
    if revision_context:
        bundle.update({"revision_context": revision_context, "revision_request_ref": revision_context["revision_request_ref"], "revision_summary": revision_context["summary"]})
    defects = [{"ui_spec_id": unit["ui_spec_id"], "check": name} for unit in units for name, ok in unit["checklist"].items() if not ok]
    document_test_report = _persist_package_outputs(
        output_dir=output_dir,
        repo_root=repo_root,
        input_dir=Path(context["input_dir"]),
        feat_ref=feat_ref,
        run_id=run_id,
        overall=overall,
        bundle=bundle,
        units=units,
        flow_edges=flow_edges,
        defects=defects,
        revision_context=revision_context,
    )
    return {"ok": overall != "fail", "artifacts_dir": str(output_dir), "artifacts_ref": rel(output_dir, repo_root), "ui_spec_refs": bundle["ui_spec_refs"], "ui_spec_count": len(units), "completeness_result": overall, "open_questions": bundle["open_questions"], "document_test_outcome": document_test_report["test_outcome"]}


def _persist_package_outputs(
    *,
    output_dir: Path,
    repo_root: Path,
    input_dir: Path,
    feat_ref: str,
    run_id: str,
    overall: str,
    bundle: dict[str, Any],
    units: list[dict[str, Any]],
    flow_edges: list[dict[str, Any]],
    defects: list[dict[str, Any]],
    revision_context: dict[str, Any] | None,
) -> dict[str, Any]:
    document_test_report = build_document_test(run_id=bundle["workflow_run_id"], tested_at=utc_now(), bundle=bundle, defects=defects, revision_context=revision_context)
    document_test_non_blocking = document_test_report.get("test_outcome") == "no_blocking_defect_found"
    manifest = {"artifact_type": "ui_spec_package", "workflow_key": "dev.feat-to-ui", "run_id": run_id or slugify(feat_ref), "feat_ref": feat_ref, "status": overall, "ui_spec_refs": bundle["ui_spec_refs"], "source_package_ref": bundle["source_package_ref"], "ui_flow_map_ref": rel(output_dir / "ui-flow-map.md", repo_root), "document_test_report_ref": rel(output_dir / "document-test-report.json", repo_root)}
    if revision_context:
        manifest.update({"revision_request_ref": revision_context["revision_request_ref"], "revision_summary": revision_context["summary"]})
        document_test_report["revision_context"] = revision_context
    write_json(output_dir / "package-manifest.json", manifest)
    write_text(output_dir / "ui-spec-bundle.md", _render_bundle_markdown(feat_ref, bundle, units, overall))
    write_text(output_dir / "ui-flow-map.md", _render_flow_map(feat_ref, bundle, units, flow_edges))
    write_json(output_dir / "ui-spec-bundle.json", bundle)
    review_gate = _recompute_review_gate(artifacts_dir=output_dir, bundle=bundle, units=units, flow_edges=flow_edges)
    document_test_report = _update_document_test_report(document_test_report, overall=overall, review_gate=review_gate)
    document_test_non_blocking = document_test_report.get("test_outcome") == "no_blocking_defect_found"
    completeness_report = {
        "gate_name": "UI Spec Completeness Check",
        "decision": overall,
        "freeze_ready": overall != "fail" and review_gate["review_gate_ok"],
        "ui_specs": [{"ui_spec_id": unit["ui_spec_id"], "decision": unit["completeness_result"], "checklist": unit["checklist"], "open_questions": unit["open_questions"]} for unit in units],
        "open_questions": bundle["open_questions"],
        "checked_at": utc_now(),
        "review_gate": review_gate,
    }
    review_report = {
        "workflow_key": "dev.feat-to-ui",
        "decision": "pass" if overall != "fail" and review_gate["review_gate_ok"] else "revise",
        "summary": review_gate["summary"],
        "reviewed_at": utc_now(),
        "open_questions": bundle["open_questions"],
        "review_gate": review_gate,
    }
    freeze_gate = {
        "workflow_key": "dev.feat-to-ui",
        "gate_name": "UI Spec Completeness Check",
        "decision": overall,
        "freeze_ready": overall != "fail" and document_test_non_blocking and review_gate["review_gate_ok"],
        "checked_at": utc_now(),
        "checks": {
            "document_test_report_present": True,
            "document_test_non_blocking": document_test_non_blocking,
            "review_gate_ok": review_gate["review_gate_ok"],
        },
        "review_gate": review_gate,
    }
    execution_evidence = {"workflow_key": "dev.feat-to-ui", "run_id": run_id or slugify(feat_ref), "input_path": str(input_dir), "artifacts_dir": str(output_dir), "decision": overall, "generated_at": utc_now(), "document_test_report_ref": str(output_dir / "document-test-report.json"), "key_decisions": ([f"Applied revision context: {revision_context['summary']}"] if revision_context else []), "structural_results": {"document_test_outcome": document_test_report["test_outcome"], "review_gate_ok": review_gate["review_gate_ok"]}}
    supervision_evidence = {"workflow_key": "dev.feat-to-ui", "run_id": run_id or slugify(feat_ref), "artifacts_dir": str(output_dir), "decision": review_report["decision"], "review_completed_at": utc_now(), "gate_name": "UI Spec Completeness Check", "document_test_report_ref": str(output_dir / "document-test-report.json"), "document_test_outcome": document_test_report["test_outcome"], "review_gate": review_gate}
    if revision_context:
        for payload in [completeness_report, review_report, freeze_gate, execution_evidence, supervision_evidence]:
            payload["revision_context"] = revision_context
    write_json(output_dir / "document-test-report.json", document_test_report)
    write_json(output_dir / "ui-spec-defect-list.json", defects)
    write_json(output_dir / "ui-spec-completeness-report.json", completeness_report)
    write_json(output_dir / "ui-spec-review-report.json", review_report)
    write_json(output_dir / "ui-spec-freeze-gate.json", freeze_gate)
    write_json(output_dir / "execution-evidence.json", execution_evidence)
    write_json(output_dir / "supervision-evidence.json", supervision_evidence)
    write_text(output_dir / "evidence-report.md", "\n".join(["# Evidence Report", "", f"- decision: {overall}", f"- generated_at: {utc_now()}", *([f"- revision_request_ref: {revision_context['revision_request_ref']}"] if revision_context else []), "", "## Document Test", f"- test_outcome: {document_test_report['test_outcome']}", f"- report_ref: {rel(output_dir / 'document-test-report.json', repo_root)}"]))
    return document_test_report

def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"artifacts_dir does not exist: {artifacts_dir}"], {}
    errors = [f"missing required output artifact: {name}" for name in OUTPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {}
    bundle = load_json(artifacts_dir / "ui-spec-bundle.json")
    report = load_json(artifacts_dir / "ui-spec-completeness-report.json")
    review_report = load_json(artifacts_dir / "ui-spec-review-report.json")
    gate = load_json(artifacts_dir / "ui-spec-freeze-gate.json")
    document_test_report = load_json(artifacts_dir / "document-test-report.json")
    if bundle.get("artifact_type") != "ui_spec_package":
        errors.append("ui-spec-bundle.json artifact_type must be ui_spec_package")
    if bundle.get("workflow_key") != "dev.feat-to-ui":
        errors.append("ui-spec-bundle.json workflow_key must be dev.feat-to-ui")
    if bundle.get("schema_version") != "1.0.0":
        errors.append("ui-spec-bundle.json schema_version must be 1.0.0")
    if int(bundle.get("ui_spec_count") or 0) != len(bundle.get("ui_spec_refs") or []):
        errors.append("ui_spec_count must match ui_spec_refs length")
    if str(bundle.get("revision_request_ref") or "").strip() and not (artifacts_dir / "revision-request.json").exists():
        errors.append("revision-request.json must exist when ui-spec-bundle.json revision_request_ref is present")
    if report.get("decision") != gate.get("decision"):
        errors.append("completeness report decision must match freeze gate decision")
    review_gate = _recompute_review_gate(
        artifacts_dir=artifacts_dir,
        bundle=bundle,
        units=d_list(bundle.get("ui_specs")),
        flow_edges=d_list(bundle.get("flow_edges")),
    )
    for payload_name, payload in [
        ("ui-spec-completeness-report.json", report),
        ("ui-spec-review-report.json", review_report),
        ("ui-spec-freeze-gate.json", gate),
    ]:
        if payload.get("review_gate") != review_gate:
            errors.append(f"{payload_name} review_gate must match current UI artifacts.")
    expected_review_decision = "pass" if bundle.get("completeness_result") != "fail" and review_gate["review_gate_ok"] else "revise"
    if review_report.get("decision") != expected_review_decision:
        errors.append("ui-spec-review-report.json decision must match the recomputed review gate.")
    if bool((gate.get("checks") or {}).get("review_gate_ok")) != review_gate["review_gate_ok"]:
        errors.append("ui-spec-freeze-gate.json checks.review_gate_ok must match the recomputed review gate.")
    expected_document_test = _update_document_test_report(document_test_report, overall=str(bundle.get("completeness_result") or ""), review_gate=review_gate)
    if document_test_report.get("test_outcome") != expected_document_test.get("test_outcome"):
        errors.append("document-test-report.json test_outcome must match the recomputed review gate.")
    errors.extend(validate_document_test(document_test_report))
    return errors, {"bundle": bundle, "report": report, "review_report": review_report, "gate": gate, "review_gate": review_gate, "document_test_report": document_test_report}

def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, result = validate_output_package(artifacts_dir)
    if errors:
        if "document-test-report.json test_outcome must match the recomputed review gate." in errors:
            return False, ["document_test_non_blocking must be satisfied."]
        return False, errors
    if result["gate"].get("decision") == "fail":
        return False, ["UI Spec Completeness Check failed."]
    if result["review_report"].get("decision") != "pass":
        return False, ["review_gate_ok must be satisfied."]
    if result["document_test_report"].get("test_outcome") != "no_blocking_defect_found":
        return False, ["document_test_non_blocking must be satisfied."]
    return True, []

def collect_evidence_report(artifacts_dir: Path) -> Path:
    report_path = artifacts_dir / "evidence-report.md"
    if not report_path.exists():
        write_text(report_path, "# Evidence Report\n")
    return report_path


def _ui_candidate_ref(artifacts_dir: Path) -> str:
    return f"feat-to-ui.{artifacts_dir.name}.ui-spec-bundle"


def _ui_formal_ref(artifacts_dir: Path) -> str:
    return f"formal.ui.{artifacts_dir.name}"


def _drop_pending_index_entry(repo_root: Path, *, handoff_ref: str, gate_pending_ref: str) -> None:
    index_path = repo_root / "artifacts" / "active" / "gates" / "pending" / "index.json"
    if not index_path.exists():
        return
    index = load_json(index_path)
    handoffs = index.get("handoffs")
    if not isinstance(handoffs, dict):
        return
    keys_to_remove = [
        key
        for key, value in handoffs.items()
        if isinstance(value, dict)
        and (
            str(value.get("handoff_ref") or "") == handoff_ref
            or str(value.get("gate_pending_ref") or "") == gate_pending_ref
            or key in {Path(handoff_ref).stem, Path(gate_pending_ref).stem}
        )
    ]
    for key in keys_to_remove:
        handoffs.pop(key, None)
    write_json(index_path, index)


def _withdraw_previous_gate_submission(repo_root: Path, manifest: dict[str, Any]) -> None:
    handoff_ref = str(manifest.get("authoritative_handoff_ref") or "").strip()
    gate_pending_ref = str(manifest.get("gate_pending_ref") or "").strip()
    if handoff_ref:
        handoff_path = repo_root / handoff_ref
        if handoff_path.exists():
            handoff_path.unlink()
    if gate_pending_ref:
        pending_path = repo_root / gate_pending_ref
        if pending_path.exists():
            pending_path.unlink()
    if handoff_ref or gate_pending_ref:
        _drop_pending_index_entry(repo_root, handoff_ref=handoff_ref, gate_pending_ref=gate_pending_ref)


def _bind_ui_candidate_record(repo_root: Path, artifacts_dir: Path, feat_ref: str) -> str:
    candidate_ref = _ui_candidate_ref(artifacts_dir)
    bind_record(
        repo_root,
        candidate_ref,
        rel(artifacts_dir / "ui-spec-bundle.md", repo_root),
        "candidate",
        {"run_ref": artifacts_dir.name, "workflow_key": "dev.feat-to-ui"},
        metadata={
            "layer": "candidate",
            "target_kind": "ui",
            "feat_ref": feat_ref,
            "workflow_run_id": artifacts_dir.name,
            "machine_ssot_ref": rel(artifacts_dir / "ui-spec-bundle.json", repo_root),
            "source_package_ref": rel(artifacts_dir, repo_root),
        },
        lineage=[feat_ref] if feat_ref else [],
    )
    return candidate_ref


def _clear_gate_artifacts(artifacts_dir: Path, manifest: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    _withdraw_previous_gate_submission(repo_root, manifest)
    for path in [
        artifacts_dir / "handoff-proposal.json",
        artifacts_dir / "input" / "gate-ready-package.json",
        artifacts_dir / "_cli" / "gate-submit-handoff.request.json",
        artifacts_dir / "_cli" / "gate-submit-handoff.response.json",
    ]:
        if path.exists():
            path.unlink()
    for key in ["handoff_proposal_ref", "gate_ready_package_ref", "authoritative_handoff_ref", "gate_pending_ref", "gate_submit_cli_ref"]:
        manifest.pop(key, None)
    return manifest

def supervisor_review(
    artifacts_dir: Path,
    repo_root: Path,
    run_id: str = "",
    revision_request_path: str | Path | None = None,
    allow_update: bool = False,
) -> dict[str, Any]:
    gate = load_json(artifacts_dir / "ui-spec-freeze-gate.json") if (artifacts_dir / "ui-spec-freeze-gate.json").exists() else {}
    bundle = load_json(artifacts_dir / "ui-spec-bundle.json") if (artifacts_dir / "ui-spec-bundle.json").exists() else {}
    completeness = load_json(artifacts_dir / "ui-spec-completeness-report.json") if (artifacts_dir / "ui-spec-completeness-report.json").exists() else {}
    review_report = load_json(artifacts_dir / "ui-spec-review-report.json") if (artifacts_dir / "ui-spec-review-report.json").exists() else {}
    document_test_report = load_json(artifacts_dir / "document-test-report.json") if (artifacts_dir / "document-test-report.json").exists() else {}
    revision_request, loaded_revision_path = load_revision_request(revision_request_path, artifacts_dir=artifacts_dir, load_json=load_json)
    revision_context = normalize_revision_context(revision_request, repo_root=repo_root, revision_request_path=loaded_revision_path) or None
    review_gate = _recompute_review_gate(
        artifacts_dir=artifacts_dir,
        bundle=bundle,
        units=d_list(bundle.get("ui_specs")),
        flow_edges=d_list(bundle.get("flow_edges")),
    )
    overall = str(bundle.get("completeness_result") or gate.get("decision") or "fail")
    document_test_report = _update_document_test_report(document_test_report, overall=overall, review_gate=review_gate)
    review_decision = "pass" if overall != "fail" and review_gate["review_gate_ok"] else "revise"
    freeze_ready = overall != "fail" and document_test_report.get("test_outcome") == "no_blocking_defect_found" and review_gate["review_gate_ok"]
    completeness["freeze_ready"] = overall != "fail" and review_gate["review_gate_ok"]
    completeness["checked_at"] = utc_now()
    completeness["review_gate"] = review_gate
    review_report["workflow_key"] = "dev.feat-to-ui"
    review_report["decision"] = review_decision
    review_report["summary"] = review_gate["summary"]
    review_report["reviewed_at"] = utc_now()
    review_report["open_questions"] = bundle.get("open_questions") or []
    review_report["review_gate"] = review_gate
    gate["workflow_key"] = "dev.feat-to-ui"
    gate["gate_name"] = "UI Spec Completeness Check"
    gate["decision"] = overall
    gate["freeze_ready"] = freeze_ready
    gate["checked_at"] = utc_now()
    gate["checks"] = {
        "document_test_report_present": True,
        "document_test_non_blocking": document_test_report.get("test_outcome") == "no_blocking_defect_found",
        "review_gate_ok": review_gate["review_gate_ok"],
    }
    gate["review_gate"] = review_gate
    write_json(artifacts_dir / "document-test-report.json", document_test_report)
    write_json(artifacts_dir / "ui-spec-completeness-report.json", completeness)
    write_json(artifacts_dir / "ui-spec-review-report.json", review_report)
    write_json(artifacts_dir / "ui-spec-freeze-gate.json", gate)
    ok, errors = validate_package_readiness(artifacts_dir)
    supervision = {"workflow_key": "dev.feat-to-ui", "run_id": run_id, "artifacts_dir": str(artifacts_dir), "decision": review_decision, "review_completed_at": utc_now(), "gate_name": "UI Spec Completeness Check", "errors": errors, "document_test_report_ref": str(artifacts_dir / "document-test-report.json"), "document_test_outcome": document_test_report.get("test_outcome", ""), "review_gate": review_gate}
    if revision_context:
        supervision["revision_context"] = revision_context
    write_json(artifacts_dir / "supervision-evidence.json", supervision)
    manifest = load_json(artifacts_dir / "package-manifest.json") if (artifacts_dir / "package-manifest.json").exists() else {}
    active_run_id = run_id or str(manifest.get("run_id") or artifacts_dir.name)
    proposal_ref = ""
    gate_ready_package_ref = ""
    authoritative_handoff_ref = ""
    gate_pending_ref = ""
    if ok:
        feat_ref = str(manifest.get("feat_ref") or load_json(artifacts_dir / "ui-spec-bundle.json").get("feat_ref") or "")
        candidate_ref = _bind_ui_candidate_record(repo_root, artifacts_dir, feat_ref)
        if allow_update:
            _withdraw_previous_gate_submission(repo_root, manifest)
        proposal_path = create_handoff_proposal(repo_root=repo_root, artifacts_dir=artifacts_dir, run_id=active_run_id, feat_ref=feat_ref)
        gate_ready_package = create_gate_ready_package(
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
            candidate_ref=candidate_ref,
            machine_ssot_ref=rel(artifacts_dir / "ui-spec-bundle.json", repo_root),
            acceptance_ref=rel(artifacts_dir / "ui-spec-completeness-report.json", repo_root),
            evidence_bundle_ref=rel(artifacts_dir / "supervision-evidence.json", repo_root),
            target_formal_kind="ui",
            formal_artifact_ref=_ui_formal_ref(artifacts_dir),
        )
        gate_submit = submit_gate_pending(
            repo_root=repo_root,
            artifacts_dir=artifacts_dir,
            run_id=active_run_id,
            proposal_ref=rel(proposal_path, repo_root),
            payload_path=gate_ready_package,
            trace_context_ref=rel(artifacts_dir / "execution-evidence.json", repo_root),
        )
        gate_submit_data = gate_submit["response"]["data"]
        manifest["handoff_proposal_ref"] = rel(proposal_path, repo_root)
        manifest["gate_ready_package_ref"] = rel(gate_ready_package, repo_root)
        manifest["authoritative_handoff_ref"] = str(gate_submit_data.get("handoff_ref", ""))
        manifest["gate_pending_ref"] = str(gate_submit_data.get("gate_pending_ref", ""))
        manifest["gate_submit_cli_ref"] = rel(Path(gate_submit["response_path"]), repo_root)
        write_json(artifacts_dir / "package-manifest.json", manifest)
        proposal_ref = manifest["handoff_proposal_ref"]
        gate_ready_package_ref = manifest["gate_ready_package_ref"]
        authoritative_handoff_ref = manifest["authoritative_handoff_ref"]
        gate_pending_ref = manifest["gate_pending_ref"]
    else:
        write_json(artifacts_dir / "package-manifest.json", _clear_gate_artifacts(artifacts_dir, manifest, repo_root))
    return {
        "ok": ok,
        "freeze_ready": ok,
        "errors": errors,
        "artifacts_dir": str(artifacts_dir),
        "evidence_report_ref": rel(collect_evidence_report(artifacts_dir), repo_root),
        "handoff_proposal_ref": proposal_ref,
        "gate_ready_package_ref": gate_ready_package_ref,
        "authoritative_handoff_ref": authoritative_handoff_ref,
        "gate_pending_ref": gate_pending_ref,
    }

def run_workflow(input_path: str | Path, feat_ref: str, repo_root: Path, run_id: str = "", allow_update: bool = False, revision_request_path: str | Path | None = None) -> dict[str, Any]:
    errors, context = validate_input_package(input_path, feat_ref, repo_root)
    if errors:
        return {"ok": False, "errors": errors, "input_path": str(Path(input_path).resolve())}
    context["revision_request_path"] = revision_request_path
    executor_result = build_package(context, repo_root, run_id, allow_update)
    if not executor_result.get("artifacts_dir"):
        return executor_result
    supervisor_result = supervisor_review(
        Path(executor_result["artifacts_dir"]).resolve(),
        repo_root,
        run_id or "",
        revision_request_path,
        allow_update=allow_update,
    )
    return {**executor_result, "supervision": supervisor_result, "handoff_proposal_ref": supervisor_result.get("handoff_proposal_ref", ""), "gate_ready_package_ref": supervisor_result.get("gate_ready_package_ref", ""), "authoritative_handoff_ref": supervisor_result.get("authoritative_handoff_ref", ""), "gate_pending_ref": supervisor_result.get("gate_pending_ref", "")}

def _run_build_command(args: argparse.Namespace, *, strict: bool) -> int:
    result = run_workflow(args.input, args.feat_ref, repo_root_from(args.repo_root), args.run_id or "", args.allow_update, args.revision_request or None)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") or not strict else 1

def command_run(args: argparse.Namespace) -> int:
    return _run_build_command(args, strict=True)
def command_executor_run(args: argparse.Namespace) -> int:
    return _run_build_command(args, strict=False)
def command_supervisor_review(args: argparse.Namespace) -> int:
    result = supervisor_review(
        Path(args.artifacts_dir).resolve(),
        repo_root_from(args.repo_root),
        args.run_id or "",
        args.revision_request or None,
        allow_update=args.allow_update,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("freeze_ready") else 1

def command_validate_input(args: argparse.Namespace) -> int:
    errors, result = validate_input_package(args.input, args.feat_ref, repo_root_from(args.repo_root))
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1

def command_validate_output(args: argparse.Namespace) -> int:
    errors, result = validate_output_package(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": not errors, "result": result, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1

def command_collect_evidence(args: argparse.Namespace) -> int:
    print(json.dumps({"ok": True, "report_path": str(collect_evidence_report(Path(args.artifacts_dir).resolve()))}, ensure_ascii=False))
    return 0
def command_validate_package_readiness(args: argparse.Namespace) -> int:
    ok, errors = validate_package_readiness(Path(args.artifacts_dir).resolve())
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the feat-to-ui workflow.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in [("run", command_run), ("executor-run", command_executor_run)]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--input", required=True)
        cmd.add_argument("--feat-ref", required=True)
        cmd.add_argument("--repo-root")
        cmd.add_argument("--run-id")
        cmd.add_argument("--allow-update", action="store_true")
        cmd.add_argument("--revision-request")
        cmd.set_defaults(func=func)
    review = sub.add_parser("supervisor-review")
    review.add_argument("--artifacts-dir", required=True)
    review.add_argument("--repo-root")
    review.add_argument("--run-id")
    review.add_argument("--revision-request")
    review.add_argument("--allow-update", action="store_true")
    review.set_defaults(func=command_supervisor_review)
    vin = sub.add_parser("validate-input")
    vin.add_argument("--input", required=True)
    vin.add_argument("--feat-ref", required=True)
    vin.add_argument("--repo-root")
    vin.set_defaults(func=command_validate_input)
    vout = sub.add_parser("validate-output")
    vout.add_argument("--artifacts-dir", required=True)
    vout.set_defaults(func=command_validate_output)
    ev = sub.add_parser("collect-evidence")
    ev.add_argument("--artifacts-dir", required=True)
    ev.set_defaults(func=command_collect_evidence)
    ready = sub.add_parser("validate-package-readiness")
    ready.add_argument("--artifacts-dir", required=True)
    ready.set_defaults(func=command_validate_package_readiness)
    freeze = sub.add_parser("freeze-guard")
    freeze.add_argument("--artifacts-dir", required=True)
    freeze.set_defaults(func=command_validate_package_readiness)
    return parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
if __name__ == "__main__":
    sys.exit(main())
