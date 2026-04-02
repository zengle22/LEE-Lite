#!/usr/bin/env python3
"""Lite-native runtime for the ll-governance-failure-capture workflow."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

SCHEMA_VERSION = "0.1.0"
ARTIFACT_TYPE = "failure_capture_request"
PACKAGE_ARTIFACT_TYPE = "failure_capture_package"
TRIAGE_LEVELS = {"P0", "P1", "P2"}
FAILURE_SCOPES = {"run", "artifact", "field_cluster"}
ROOT_CAUSES = {
    "definition_weakness",
    "input_contamination",
    "generation_freedom",
    "detection_weakness",
    "repair_fault",
}
EXPECTED_DETECTORS = {
    "schema_validator",
    "relation_validator",
    "semantic_review",
    "document_test",
    "impl_spec_testing",
    "human_final_review",
}
ERROR_CLASSES = {
    "structure_error",
    "relation_error",
    "semantic_drift",
    "granularity_error",
    "detection_miss",
    "repair_side_effect",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _emit(ok: bool, **payload: object) -> int:
    print(json.dumps({"ok": ok, **payload}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def _string_list(value: object) -> list[str]:
    if value is None or not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _repo_root(args: argparse.Namespace, request: dict, request_path: Path) -> Path:
    root_value = args.repo_root or request.get("repo_root")
    if isinstance(root_value, str) and root_value.strip():
        return Path(root_value).resolve()
    return request_path.resolve().parent


def _resolve_output_root(repo_root: Path, request: dict) -> Path:
    output_root = request.get("output_root")
    if isinstance(output_root, str) and output_root.strip():
        candidate = Path(output_root)
        normalized = candidate.as_posix().rstrip("/")
        # Treat the previous default as a legacy alias so older requests inherit the new canonical root.
        if normalized == "artifacts/reports/governance":
            return (repo_root / "tests" / "defect").resolve()
        return candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    return (repo_root / "tests" / "defect").resolve()


def _canonical_ref(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _slug_seed(value: str) -> str:
    seed = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return seed[:8] if seed else uuid4().hex[:4].upper()


def _capture_id(prefix: str, artifact_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{timestamp}-{_slug_seed(artifact_id)}"


def _validate_request(request: dict) -> list[str]:
    errors: list[str] = []
    required_strings = [
        "artifact_type",
        "schema_version",
        "status",
        "skill_id",
        "sku",
        "run_id",
        "artifact_id",
        "failure_scope",
        "detected_stage",
        "detected_by",
        "severity",
        "triage_level",
        "symptom_summary",
        "problem_description",
        "failed_artifact_ref",
        "repair_goal",
    ]
    for field in required_strings:
        value = request.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required")
    if request.get("artifact_type") != ARTIFACT_TYPE:
        errors.append(f"artifact_type must be {ARTIFACT_TYPE}")
    if request.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if request.get("triage_level") not in TRIAGE_LEVELS:
        errors.append("triage_level must be one of P0, P1, P2")
    if request.get("failure_scope") not in FAILURE_SCOPES:
        errors.append("failure_scope must be one of run, artifact, field_cluster")
    if not _string_list(request.get("upstream_refs")):
        errors.append("upstream_refs must include at least one ref")
    if "evidence_refs" in request and not isinstance(request.get("evidence_refs"), list):
        errors.append("evidence_refs must be an array when provided")
    if "suggested_edit_scope" in request and not isinstance(request.get("suggested_edit_scope"), list):
        errors.append("suggested_edit_scope must be an array when provided")
    if "do_not_modify" in request and not isinstance(request.get("do_not_modify"), list):
        errors.append("do_not_modify must be an array when provided")
    return errors


def _infer_error_class(request: dict) -> str:
    provided = request.get("error_class")
    if isinstance(provided, str) and provided in ERROR_CLASSES:
        return provided
    text = " ".join([str(request.get("symptom_summary") or ""), str(request.get("problem_description") or "")]).lower()
    if any(token in text for token in ("relation", "binding", "implements", "trace")):
        return "relation_error"
    if any(token in text for token in ("schema", "field", "format", "structure")):
        return "structure_error"
    if any(token in text for token in ("semantic", "drift", "meaning", "scope expansion")):
        return "semantic_drift"
    if any(token in text for token in ("granularity", "too coarse", "too fine")):
        return "granularity_error"
    if any(token in text for token in ("repair", "patch", "hotfix", "side effect")):
        return "repair_side_effect"
    return "detection_miss"


def _infer_expected_detector(request: dict) -> str:
    provided = request.get("expected_detector")
    if isinstance(provided, str) and provided in EXPECTED_DETECTORS:
        return provided
    stage = str(request.get("detected_stage") or "").lower()
    if "schema" in stage:
        return "schema_validator"
    if "relation" in stage or "trace" in stage:
        return "relation_validator"
    if "document_test" in stage:
        return "document_test"
    if "impl_spec" in stage:
        return "impl_spec_testing"
    if "human" in stage or "gate" in stage or "final" in stage:
        return "human_final_review"
    return "semantic_review"


def _infer_root_cause(request: dict) -> str:
    provided = request.get("root_cause_primary")
    if isinstance(provided, str) and provided in ROOT_CAUSES:
        return provided
    text = " ".join([str(request.get("symptom_summary") or ""), str(request.get("problem_description") or "")]).lower()
    if any(token in text for token in ("ambiguous", "unclear rule", "undefined")):
        return "definition_weakness"
    if any(token in text for token in ("upstream", "missing context", "conflicting input", "old wording", "old version")):
        return "input_contamination"
    if any(token in text for token in ("repair", "patch", "hotfix", "regression")):
        return "repair_fault"
    stage = str(request.get("detected_stage") or "").lower()
    if any(token in stage for token in ("review", "gate", "document_test", "impl_spec", "human")):
        return "detection_weakness"
    return "generation_freedom"


def _remediation_hint(request: dict) -> str:
    provided = request.get("remediation_hint")
    if isinstance(provided, str) and provided.strip():
        return provided.strip()
    scope = _string_list(request.get("suggested_edit_scope"))
    if scope:
        return f"Only edit the approved scope: {', '.join(scope)}"
    return "Keep the fix local to the reported artifact and preserve untouched sections."


def _package_kind(triage_level: str) -> str:
    return "issue_log" if triage_level == "P2" else "failure_case"


def _package_dir(output_root: Path, package_kind: str, capture_id: str) -> Path:
    bucket = "issue-log" if package_kind == "issue_log" else "failure-cases"
    return (output_root / bucket / capture_id).resolve()


def _build_failure_case(request: dict, capture_id: str) -> dict:
    return {
        "artifact_type": "failure_case",
        "schema_version": SCHEMA_VERSION,
        "status": "open",
        "failure_id": capture_id,
        "skill_id": request["skill_id"],
        "sku": request["sku"],
        "run_id": request["run_id"],
        "artifact_id": request["artifact_id"],
        "failure_scope": request["failure_scope"],
        "detected_stage": request["detected_stage"],
        "detected_by": request["detected_by"],
        "severity": request["severity"],
        "triage_level": request["triage_level"],
        "symptom_summary": request["symptom_summary"],
        "problem_description": request["problem_description"],
        "failed_artifact_ref": request["failed_artifact_ref"],
        "upstream_refs": _string_list(request.get("upstream_refs")),
        "evidence_refs": _string_list(request.get("evidence_refs")),
    }


def _build_issue_log(request: dict, capture_id: str) -> dict:
    return {
        "artifact_type": "issue_log",
        "schema_version": SCHEMA_VERSION,
        "status": "open",
        "issue_id": capture_id,
        "skill_id": request["skill_id"],
        "sku": request["sku"],
        "run_id": request["run_id"],
        "artifact_id": request["artifact_id"],
        "failure_scope": request["failure_scope"],
        "triage_level": request["triage_level"],
        "severity": request["severity"],
        "symptom_summary": request["symptom_summary"],
        "problem_description": request["problem_description"],
        "failed_artifact_ref": request["failed_artifact_ref"],
        "evidence_refs": _string_list(request.get("evidence_refs")),
        "upgrade_rule": "Upgrade to failure_case when the same P2 pattern reaches the ADR-037 threshold.",
    }


def _build_diagnosis_stub(request: dict) -> dict:
    return {
        "artifact_type": "diagnosis_stub",
        "schema_version": SCHEMA_VERSION,
        "status": "stubbed",
        "error_class": _infer_error_class(request),
        "root_cause_primary": _infer_root_cause(request),
        "expected_detector": _infer_expected_detector(request),
        "remediation_hint": _remediation_hint(request),
        "note": "This is an initial capture-time stub, not a final diagnosis report.",
    }


def _build_repair_context(request: dict) -> dict:
    allowed_scope = _string_list(request.get("suggested_edit_scope")) or [request["failed_artifact_ref"]]
    protected = _string_list(request.get("do_not_modify"))
    return {
        "artifact_type": "repair_context",
        "schema_version": SCHEMA_VERSION,
        "status": "ready_for_manual_repair",
        "repair_mode": "manual_or_human_directed_ai",
        "automatic_repair_allowed": False,
        "repair_goal": request["repair_goal"],
        "problem_focus": request["symptom_summary"],
        "allowed_edit_scope": allowed_scope,
        "protected_refs": protected,
        "do_not_modify": protected,
        "repair_instructions": [
            "Only edit the approved scope.",
            "Do not restructure unaffected sections.",
            "Keep the fix diff reviewable and minimal.",
            "Re-run minimum validation after repair."
        ]
    }


def _build_manifest(request: dict, repo_root: Path, package_dir: Path, package_kind: str, capture_id: str, refs: dict[str, str], request_ref: str) -> dict:
    return {
        "artifact_type": PACKAGE_ARTIFACT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "status": "captured",
        "workflow_key": "governance.failure-capture",
        "package_kind": package_kind,
        "package_id": capture_id,
        "triage_level": request["triage_level"],
        "skill_id": request["skill_id"],
        "sku": request["sku"],
        "run_id": request["run_id"],
        "artifact_id": request["artifact_id"],
        "failure_scope": request["failure_scope"],
        "package_dir_ref": _canonical_ref(package_dir, repo_root),
        "request_ref": request_ref,
        "source_refs": [request_ref, request["failed_artifact_ref"], *_string_list(request.get("upstream_refs"))],
        "evidence_refs": _string_list(request.get("evidence_refs")),
        "files": refs,
    }


def command_validate_input(args: argparse.Namespace) -> int:
    path = Path(args.input).resolve()
    try:
        request = _load_json(path)
    except Exception as exc:
        return _emit(False, errors=[f"failed to load request json: {exc}"], input=str(path))
    return _emit(not _validate_request(request), errors=_validate_request(request), input=str(path))


def command_run(args: argparse.Namespace) -> int:
    request_path = Path(args.input).resolve()
    try:
        request = _load_json(request_path)
    except Exception as exc:
        return _emit(False, errors=[f"failed to load request json: {exc}"], input=str(request_path))
    errors = _validate_request(request)
    if errors:
        return _emit(False, errors=errors, input=str(request_path))

    repo_root = _repo_root(args, request, request_path)
    output_root = _resolve_output_root(repo_root, request)
    package_kind = _package_kind(str(request["triage_level"]))
    capture_id = _capture_id("IL" if package_kind == "issue_log" else "FC", str(request["artifact_id"]))
    package_dir = _package_dir(output_root, package_kind, capture_id)
    if package_dir.exists() and not args.allow_update:
        return _emit(False, errors=[f"package directory already exists: {package_dir}"])

    primary_name = "issue_log.json" if package_kind == "issue_log" else "failure_case.json"
    primary_path = package_dir / primary_name
    diagnosis_path = package_dir / "diagnosis_stub.json"
    repair_path = package_dir / "repair_context.json"
    manifest_path = package_dir / "capture_manifest.json"

    primary_payload = _build_issue_log(request, capture_id) if package_kind == "issue_log" else _build_failure_case(request, capture_id)
    diagnosis_stub = _build_diagnosis_stub(request)
    repair_context = _build_repair_context(request)

    _write_json(primary_path, primary_payload)
    _write_json(diagnosis_path, diagnosis_stub)
    _write_json(repair_path, repair_context)

    request_ref = _canonical_ref(request_path, repo_root)
    refs = {
        "capture_manifest_ref": _canonical_ref(manifest_path, repo_root),
        "diagnosis_stub_ref": _canonical_ref(diagnosis_path, repo_root),
        "repair_context_ref": _canonical_ref(repair_path, repo_root),
    }
    if package_kind == "issue_log":
        refs["issue_log_ref"] = _canonical_ref(primary_path, repo_root)
    else:
        refs["failure_case_ref"] = _canonical_ref(primary_path, repo_root)

    _write_json(manifest_path, _build_manifest(request, repo_root, package_dir, package_kind, capture_id, refs, request_ref))
    return _emit(True, package_kind=package_kind, package_id=capture_id, package_dir=str(package_dir), capture_manifest_ref=_canonical_ref(manifest_path, repo_root), files=refs)


def _validate_manifest(manifest: dict, artifacts_dir: Path) -> list[str]:
    errors: list[str] = []
    if manifest.get("artifact_type") != PACKAGE_ARTIFACT_TYPE:
        errors.append(f"artifact_type must be {PACKAGE_ARTIFACT_TYPE}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    package_kind = manifest.get("package_kind")
    if package_kind not in {"failure_case", "issue_log"}:
        errors.append("package_kind must be failure_case or issue_log")
    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("files must be an object")
        return errors
    for key in ("capture_manifest_ref", "diagnosis_stub_ref", "repair_context_ref"):
        if not isinstance(files.get(key), str) or not files[key].strip():
            errors.append(f"files.{key} is required")
    if package_kind == "failure_case" and "failure_case_ref" not in files:
        errors.append("failure_case package must include files.failure_case_ref")
    if package_kind == "issue_log" and "issue_log_ref" not in files:
        errors.append("issue_log package must include files.issue_log_ref")
    for filename in ("capture_manifest.json", "diagnosis_stub.json", "repair_context.json"):
        if not (artifacts_dir / filename).exists():
            errors.append(f"missing file: {filename}")
    primary = "issue_log.json" if package_kind == "issue_log" else "failure_case.json"
    if package_kind in {"failure_case", "issue_log"} and not (artifacts_dir / primary).exists():
        errors.append(f"missing file: {primary}")
    return errors


def _validate_json_file(path: Path, required_fields: list[str]) -> list[str]:
    try:
        payload = _load_json(path)
    except Exception as exc:
        return [f"{path.name} is not valid json: {exc}"]
    errors: list[str] = []
    for field in required_fields:
        value = payload.get(field)
        if isinstance(value, str):
            if not value.strip():
                errors.append(f"{path.name}.{field} is required")
        elif value is None:
            errors.append(f"{path.name}.{field} is required")
    return errors


def command_validate_output(args: argparse.Namespace) -> int:
    artifacts_dir = Path(args.artifacts_dir).resolve()
    manifest_path = artifacts_dir / "capture_manifest.json"
    if not manifest_path.exists():
        return _emit(False, errors=[f"missing manifest: {manifest_path}"], artifacts_dir=str(artifacts_dir))
    manifest = _load_json(manifest_path)
    errors = _validate_manifest(manifest, artifacts_dir)
    primary = artifacts_dir / ("issue_log.json" if manifest.get("package_kind") == "issue_log" else "failure_case.json")
    errors.extend(_validate_json_file(primary, ["schema_version", "status", "skill_id", "sku", "artifact_id"]))
    errors.extend(_validate_json_file(artifacts_dir / "diagnosis_stub.json", ["error_class", "root_cause_primary", "expected_detector", "remediation_hint"]))
    errors.extend(_validate_json_file(artifacts_dir / "repair_context.json", ["repair_goal", "repair_mode"]))
    return _emit(not errors, errors=errors, artifacts_dir=str(artifacts_dir))


def command_validate_package_readiness(args: argparse.Namespace) -> int:
    artifacts_dir = Path(args.artifacts_dir).resolve()
    manifest_path = artifacts_dir / "capture_manifest.json"
    if not manifest_path.exists():
        return _emit(False, errors=[f"missing manifest: {manifest_path}"], artifacts_dir=str(artifacts_dir))
    manifest = _load_json(manifest_path)
    errors = _validate_manifest(manifest, artifacts_dir)
    diagnosis = _load_json(artifacts_dir / "diagnosis_stub.json")
    repair_context = _load_json(artifacts_dir / "repair_context.json")
    if diagnosis.get("note") != "This is an initial capture-time stub, not a final diagnosis report.":
        errors.append("diagnosis_stub.note must preserve stub semantics")
    if repair_context.get("automatic_repair_allowed") is not False:
        errors.append("repair_context.automatic_repair_allowed must be false")
    if repair_context.get("repair_mode") != "manual_or_human_directed_ai":
        errors.append("repair_context.repair_mode must be manual_or_human_directed_ai")
    return _emit(not errors, errors=errors, artifacts_dir=str(artifacts_dir))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the ll-governance-failure-capture workflow.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_input_parser = subparsers.add_parser("validate-input")
    validate_input_parser.add_argument("--input", required=True)
    validate_input_parser.set_defaults(func=command_validate_input)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--input", required=True)
    run_parser.add_argument("--repo-root")
    run_parser.add_argument("--allow-update", action="store_true")
    run_parser.set_defaults(func=command_run)

    validate_output_parser = subparsers.add_parser("validate-output")
    validate_output_parser.add_argument("--artifacts-dir", required=True)
    validate_output_parser.set_defaults(func=command_validate_output)

    readiness_parser = subparsers.add_parser("validate-package-readiness")
    readiness_parser.add_argument("--artifacts-dir", required=True)
    readiness_parser.set_defaults(func=command_validate_package_readiness)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
