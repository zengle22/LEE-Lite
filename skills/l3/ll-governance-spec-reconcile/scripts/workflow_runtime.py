#!/usr/bin/env python3
"""Lite-native runtime for ADR-044 spec reconcile (Phase 0/1)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"
REPORT_ARTIFACT_TYPE = "spec_reconcile_report"
PATCH_RECEIPT_ARTIFACT_TYPE = "ssot_patch_receipt"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _emit(ok: bool, **payload: object) -> int:
    print(json.dumps({"ok": ok, **payload}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_ref(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _resolve_repo_root(args: argparse.Namespace, request: dict[str, Any], request_path: Path) -> Path:
    root_value = args.repo_root or request.get("repo_root")
    if isinstance(root_value, str) and root_value.strip():
        return Path(root_value).resolve()
    return request_path.resolve().parent


def _resolve_dir(repo_root: Path, ref_value: str) -> Path:
    candidate = Path(ref_value)
    return candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()


def _extract_target_ssot_paths_from_patch_receipts(repo_root: Path, patch_refs: list[str]) -> list[str]:
    targets: list[str] = []
    for patch_ref in patch_refs:
        patch_ref_value = str(patch_ref or "").strip()
        if not patch_ref_value:
            continue
        path = _resolve_dir(repo_root, patch_ref_value)
        if not path.exists():
            continue
        try:
            payload = _load_json(path)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if str(payload.get("artifact_type") or "").strip() != PATCH_RECEIPT_ARTIFACT_TYPE:
            continue

        applied_updates = payload.get("applied_updates")
        if isinstance(applied_updates, list):
            for item in applied_updates:
                if not isinstance(item, dict):
                    continue
                ssot_path = str(item.get("ssot_path") or "").strip()
                if ssot_path.startswith("ssot/") and ssot_path not in targets:
                    targets.append(ssot_path)

        changed_files = payload.get("changed_files")
        if isinstance(changed_files, list):
            for item in changed_files:
                if not isinstance(item, dict):
                    continue
                changed_path = str(item.get("path") or "").strip().replace("\\", "/")
                if changed_path.startswith("ssot/") and changed_path not in targets:
                    targets.append(changed_path)

    return targets


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _index_by(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        value = str(item.get(key) or "").strip()
        if value:
            result[value] = item
    return result


def _default_decision(finding: dict[str, Any], *, decided_by: dict[str, Any]) -> dict[str, Any]:
    finding_id = str(finding.get("finding_id") or "").strip()
    finding_type = str(finding.get("type") or "").strip()
    if finding_type == "execution_decision":
        return {"finding_id": finding_id, "type": finding_type, "outcome": "recorded", "decided_by": decided_by}
    return {"finding_id": finding_id, "type": finding_type, "outcome": "deferred", "decided_by": decided_by, "owner": "", "next_checkpoint": ""}


def _materialize_decisions(
    *,
    findings: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    decided_by: dict[str, Any],
) -> list[dict[str, Any]]:
    override_by_id = _index_by(overrides, "finding_id")
    decisions: list[dict[str, Any]] = []
    for finding in findings:
        finding_id = str(finding.get("finding_id") or "").strip()
        if not finding_id:
            continue
        base = _default_decision(finding, decided_by=decided_by)
        override = override_by_id.get(finding_id, {})
        merged = {**base, **{k: v for k, v in override.items() if k not in {"type", "finding_id"}}}
        merged.setdefault("decided_by", decided_by)
        if merged.get("type") == "scope_cut":
            merged.setdefault("scope_kind", finding.get("scope_kind"))
            merged.setdefault("affected_refs", finding.get("affected_refs", []))
        merged.setdefault("ssot_patch_refs", merged.get("ssot_patch_refs", []))
        merged.setdefault("rationale", merged.get("rationale", ""))
        merged.setdefault("owner", merged.get("owner", ""))
        merged.setdefault("next_checkpoint", merged.get("next_checkpoint", ""))
        decisions.append(merged)
    return decisions


def _summary(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"total": len(decisions), "backported": 0, "rejected": 0, "deferred": 0, "recorded": 0}
    for item in decisions:
        outcome = str(item.get("outcome") or "").strip()
        if outcome in counts:
            counts[outcome] += 1
    return counts


def _load_findings(package_dir: Path) -> tuple[dict[str, Any] | None, list[str]]:
    findings_path = package_dir / "spec-findings.json"
    if not findings_path.exists():
        return None, ["missing spec-findings.json"]
    try:
        payload = _load_json(findings_path)
    except Exception as exc:
        return None, [f"invalid spec-findings.json: {exc}"]
    findings = payload.get("findings")
    if findings is not None and not isinstance(findings, list):
        return None, ["spec-findings.json findings must be an array"]
    return payload, []


def _update_queue(
    *,
    repo_root: Path,
    queue_ref: str,
    spec_findings_ref: str,
    findings_payload: dict[str, Any] | None,
    decisions: list[dict[str, Any]],
    report_ref: str,
) -> str:
    queue_path = _resolve_dir(repo_root, queue_ref)
    if queue_path.exists():
        queue = _load_json(queue_path)
    else:
        queue = {"artifact_type": "spec_backport_queue", "schema_version": SCHEMA_VERSION, "status": "active", "items": []}

    items = queue.get("items")
    if not isinstance(items, list):
        items = []
    item_by_id = _index_by([item for item in items if isinstance(item, dict)], "finding_id")

    findings = []
    trace = {"workflow_key": "unknown", "run_ref": "unknown"}
    lineage: list[str] = []
    if isinstance(findings_payload, dict):
        findings = [item for item in (findings_payload.get("findings") or []) if isinstance(item, dict)]
        raw_trace = findings_payload.get("trace")
        if isinstance(raw_trace, dict):
            trace = {
                "workflow_key": str(raw_trace.get("workflow_key") or "unknown").strip() or "unknown",
                "run_ref": str(raw_trace.get("run_ref") or "unknown").strip() or "unknown",
                **{k: v for k, v in raw_trace.items() if k not in {"workflow_key", "run_ref"}},
            }
        lineage = _as_str_list(findings_payload.get("lineage"))

    finding_by_id = _index_by(findings, "finding_id")
    decision_by_id = _index_by(decisions, "finding_id")

    def priority_for(finding: dict[str, Any]) -> str:
        must_backport = bool(finding.get("must_backport"))
        finding_type = str(finding.get("type") or "").strip()
        if must_backport and finding_type in {"spec_gap", "scope_cut"}:
            return "high"
        if must_backport:
            return "medium"
        return "low"

    for finding_id, finding in finding_by_id.items():
        finding_type = str(finding.get("type") or "").strip()
        if finding_type not in {"spec_gap", "local_assumption"}:
            continue
        decision = decision_by_id.get(finding_id, {})
        outcome = str(decision.get("outcome") or "pending").strip()
        status = outcome if outcome in {"pending", "in_progress", "backported", "rejected", "deferred"} else "pending"
        owner = str(decision.get("owner") or "").strip()
        existing = item_by_id.get(finding_id, {})

        target_paths = _as_str_list(existing.get("target_ssot_paths"))
        if status == "backported":
            patch_refs = _as_str_list(decision.get("ssot_patch_refs"))
            patch_targets = _extract_target_ssot_paths_from_patch_receipts(repo_root, patch_refs)
            if patch_targets:
                target_paths = _as_str_list(existing.get("target_ssot_paths")) or patch_targets
                for item in patch_targets:
                    if item not in target_paths:
                        target_paths.append(item)
        if not target_paths:
            target_paths = _as_str_list(finding.get("proposed_ssot_targets"))

        existing_source = str(existing.get("source_artifact_ref") or "").strip()
        item = {
            "finding_id": finding_id,
            "source_artifact_ref": existing_source or spec_findings_ref,
            "trace": trace,
            "lineage": lineage or _as_str_list(existing.get("lineage")) or [existing_source or spec_findings_ref],
            "target_ssot_paths": target_paths,
            "reconcile_report_ref": report_ref,
            "owner": owner,
            "priority": str(existing.get("priority") or priority_for(finding)),
            "status": status,
            "notes": str(existing.get("notes") or decision.get("rationale") or "").strip(),
        }
        item_by_id[finding_id] = item

    queue["items"] = sorted(item_by_id.values(), key=lambda item: str(item.get("finding_id") or ""))
    _write_json(queue_path, queue)
    return _canonical_ref(queue_path, repo_root)


def _update_manifest(
    *,
    repo_root: Path,
    package_dir: Path,
    spec_findings_ref: str,
    report_ref: str,
) -> str:
    manifest_path = package_dir / "package-manifest.json"
    if not manifest_path.exists():
        return ""
    try:
        manifest = _load_json(manifest_path)
    except Exception:
        manifest = {}
    if not isinstance(manifest, dict):
        manifest = {}
    manifest["spec_findings_ref"] = str(manifest.get("spec_findings_ref") or spec_findings_ref)
    manifest["spec_reconcile_report_ref"] = report_ref
    _write_json(manifest_path, manifest)
    return _canonical_ref(manifest_path, repo_root)


def command_run(args: argparse.Namespace) -> int:
    request_path = Path(args.input).resolve()
    request = _load_json(request_path)
    repo_root = _resolve_repo_root(args, request, request_path)

    package_dir_ref = str(request.get("package_dir_ref") or "").strip()
    if not package_dir_ref:
        return _emit(False, error="package_dir_ref is required")
    package_dir = _resolve_dir(repo_root, package_dir_ref)

    findings_payload, findings_issues = _load_findings(package_dir)
    findings = [item for item in (findings_payload or {}).get("findings", []) if isinstance(item, dict)]
    overrides = [item for item in (request.get("decisions") or []) if isinstance(item, dict)]

    trace = request.get("trace") if isinstance(request.get("trace"), dict) else {}
    decided_by_cfg = request.get("decided_by") if isinstance(request.get("decided_by"), dict) else {}
    decided_by = {
        "role": str(decided_by_cfg.get("role") or "executor"),
        "ref": str(decided_by_cfg.get("ref") or ""),
    }
    decisions = _materialize_decisions(findings=findings, overrides=overrides, decided_by=decided_by)

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from cli.lib.spec_reconcile_policy import compute_blocking_items  # pylint: disable=import-error

    blocking_items = [*findings_issues, *compute_blocking_items(findings=findings, decisions=decisions)]

    report_path = package_dir / "spec-reconcile-report.json"
    spec_findings_ref = _canonical_ref(package_dir / "spec-findings.json", repo_root)
    report_ref = _canonical_ref(report_path, repo_root)
    queue_ref = str(request.get("queue_ref") or "").strip()

    report = {
        "artifact_type": REPORT_ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "status": "produced",
        "trace": {
            "workflow_key": str(trace.get("workflow_key") or "governance.spec-reconcile"),
            "run_ref": str(trace.get("run_ref") or request.get("request_id") or "reconcile"),
            "produced_at": _utc_now(),
        },
        "input_spec_findings_ref": str(request.get("input_spec_findings_ref") or spec_findings_ref),
        "input_queue_ref": queue_ref,
        "decisions": decisions,
        "summary": _summary(decisions),
        "blocking_items": blocking_items,
    }
    _write_json(report_path, report)

    files: dict[str, str] = {"spec_reconcile_report_ref": report_ref}
    updated_queue_ref = ""
    updated_manifest_ref = ""
    if args.allow_update:
        if queue_ref:
            updated_queue_ref = _update_queue(
                repo_root=repo_root,
                queue_ref=queue_ref,
                spec_findings_ref=spec_findings_ref,
                findings_payload=findings_payload,
                decisions=decisions,
                report_ref=report_ref,
            )
            files["queue_ref"] = updated_queue_ref
        updated_manifest_ref = _update_manifest(repo_root=repo_root, package_dir=package_dir, spec_findings_ref=spec_findings_ref, report_ref=report_ref)
        if updated_manifest_ref:
            files["package_manifest_ref"] = updated_manifest_ref

    return _emit(
        True,
        spec_reconcile_report_ref=report_ref,
        package_dir=str(package_dir),
        files=files,
        blocking_items=blocking_items,
        updated_queue_ref=updated_queue_ref,
        updated_manifest_ref=updated_manifest_ref,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ADR-044 spec reconcile.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--repo-root")
    run.add_argument("--allow-update", action="store_true")
    run.set_defaults(func=command_run)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

