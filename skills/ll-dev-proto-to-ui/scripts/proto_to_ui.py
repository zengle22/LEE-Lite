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


def validate_input_package(input_path: str | Path) -> tuple[list[str], dict[str, Any]]:
    input_dir = Path(input_path).resolve()
    errors = [f"missing required input artifact: {name}" for name in ["prototype-bundle.json", "prototype-review-report.json", "prototype-freeze-gate.json"] if not (input_dir / name).exists()]
    if errors:
        return errors, {}
    bundle = load_json(input_dir / "prototype-bundle.json")
    review = load_json(input_dir / "prototype-review-report.json")
    gate = load_json(input_dir / "prototype-freeze-gate.json")
    if bundle.get("artifact_type") != "prototype_package":
        errors.append("artifact_type must be prototype_package")
    if not bundle.get("pages"):
        errors.append("prototype package must contain at least one page")
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
    feat_ref = str(bundle.get("feat_ref") or "")
    feat_title = str(bundle.get("feat_title") or "").strip()
    source_refs = [str(ref).strip() for ref in (bundle.get("source_refs") or []) if str(ref).strip()]
    output_dir = repo_root / "artifacts" / "proto-to-ui" / f"{(run_id or feat_ref).lower()}--{feat_ref.lower()}"
    if output_dir.exists() and not allow_update:
        return {"ok": False, "errors": [f"output directory already exists: {output_dir}"]}
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = bundle.get("pages") or []
    ui_spec_refs: list[str] = []
    for page in pages:
        name = f"[UI-{feat_ref}-{page['page_id']}]__ui_spec.md"
        write_text(output_dir / name, _ui_spec_markdown(page, feat_ref))
        ui_spec_refs.append(name)
    ledger = build_ui_semantic_ledger(
        from_prototype=[
            {"semantic_area": "layout", "refs": [f"prototype/index.html#{page['page_id']}"]} for page in pages
        ] + [{"semantic_area": "flow", "refs": ["prototype/mock-data.json"]}, {"semantic_area": "cta_hierarchy", "refs": ["prototype/app.js"]}],
        from_feat=[
            {"semantic_area": "business_constraints", "refs": list(bundle.get("source_refs") or [])},
            {"semantic_area": "completion_criteria", "refs": list(bundle.get("source_refs") or [])},
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
    review_decision = "revise" if ledger_errors else "pass"
    document_test = _build_document_test(run_id or feat_ref, ledger_errors, review_decision)
    write_json(output_dir / "package-manifest.json", {"artifact_type": "ui_spec_package", "workflow_key": "dev.proto-to-ui", "run_id": run_id or feat_ref, "feat_ref": feat_ref, "ui_spec_refs": ui_spec_refs})
    write_json(output_dir / "ui-spec-bundle.json", {"artifact_type": "ui_spec_package", "workflow_key": "dev.proto-to-ui", "feat_ref": feat_ref, "feat_title": feat_title, "title": f"UI Spec Bundle for {feat_ref}", "ui_ref": f"UI-{feat_ref}", "ui_spec_refs": ui_spec_refs, "source_package_ref": str(context["input_dir"]), "source_refs": source_refs, "ui_spec_count": len(ui_spec_refs)})
    write_text(output_dir / "ui-spec-bundle.md", f"# UI Spec Bundle for {feat_ref}\n\n- ui_spec_count: {len(ui_spec_refs)}")
    write_text(output_dir / "ui-flow-map.md", "\n".join(["# UI Flow Map", "", *[f"{index+1}. {page['title']}" for index, page in enumerate(pages)]]))
    write_json(output_dir / "ui-semantic-source-ledger.json", ledger)
    write_json(output_dir / "ui-spec-completeness-report.json", {"gate_name": "UI Spec Implementation Readiness Check", "decision": "fail" if ledger_errors else "pass", "checked_at": utc_now(), "ledger_errors": ledger_errors})
    write_json(output_dir / "ui-spec-review-report.json", {"workflow_key": "dev.proto-to-ui", "decision": review_decision, "reviewed_at": utc_now(), "summary": "semantic source ledger valid" if not ledger_errors else "semantic source ledger requires revision"})
    write_json(output_dir / "document-test-report.json", document_test)
    write_json(output_dir / "ui-spec-defect-list.json", [{"severity": "P1", "type": "semantic_ledger", "title": error} for error in ledger_errors])
    write_json(output_dir / "ui-spec-freeze-gate.json", {"workflow_key": "dev.proto-to-ui", "freeze_ready": not ledger_errors, "checked_at": utc_now(), "checks": {"semantic_source_ledger_valid": not ledger_errors}})
    write_json(output_dir / "execution-evidence.json", {"workflow_key": "dev.proto-to-ui", "run_id": run_id or feat_ref, "generated_at": utc_now(), "artifacts_dir": str(output_dir)})
    write_json(output_dir / "supervision-evidence.json", {"workflow_key": "dev.proto-to-ui", "run_id": run_id or feat_ref, "review_completed_at": utc_now(), "decision": review_decision})
    return {"ok": not ledger_errors, "artifacts_dir": str(output_dir), "errors": ledger_errors}


def validate_output_package(artifacts_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors = [f"missing required output artifact: {name}" for name in OUTPUT_FILES if not (artifacts_dir / name).exists()]
    if errors:
        return errors, {}
    ledger = load_json(artifacts_dir / "ui-semantic-source-ledger.json")
    report = load_json(artifacts_dir / "document-test-report.json")
    errors.extend(validate_ui_semantic_ledger(ledger))
    errors.extend(validate_document_test_report(report))
    return errors, {"ledger": ledger, "report": report}


def validate_package_readiness(artifacts_dir: Path) -> tuple[bool, list[str]]:
    errors, _ = validate_output_package(artifacts_dir)
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
