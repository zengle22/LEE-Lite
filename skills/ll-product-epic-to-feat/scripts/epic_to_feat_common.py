#!/usr/bin/env python3
"""
Shared helpers for the lite-native epic-to-feat runtime.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_INPUT_FILES = [
    "package-manifest.json",
    "epic-freeze.md",
    "epic-freeze.json",
    "epic-review-report.json",
    "epic-acceptance-report.json",
    "epic-defect-list.json",
    "epic-freeze-gate.json",
    "handoff-to-epic-to-feat.json",
    "execution-evidence.json",
    "supervision-evidence.json",
]
SEMANTIC_LOCK_REQUIRED_FIELDS = (
    "domain_type",
    "one_sentence_truth",
    "primary_object",
    "lifecycle_stage",
    "inheritance_rule",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_markdown_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
    if not markdown_text.startswith("---\n"):
        return {}, markdown_text
    end_marker = "\n---\n"
    end_index = markdown_text.find(end_marker, 4)
    if end_index == -1:
        return {}, markdown_text
    frontmatter_text = markdown_text[4:end_index]
    body = markdown_text[end_index + len(end_marker) :]
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        return {}, body
    return data, body


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    fm = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{fm}\n---\n\n{body.strip()}\n"


def ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def normalize_semantic_lock(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    normalized = {
        "domain_type": str(value.get("domain_type") or "").strip(),
        "one_sentence_truth": str(value.get("one_sentence_truth") or "").strip(),
        "primary_object": str(value.get("primary_object") or "").strip(),
        "lifecycle_stage": str(value.get("lifecycle_stage") or "").strip(),
        "allowed_capabilities": ensure_list(value.get("allowed_capabilities")),
        "forbidden_capabilities": ensure_list(value.get("forbidden_capabilities")),
        "inheritance_rule": str(value.get("inheritance_rule") or "").strip(),
    }
    if not any(normalized.values()):
        return None
    return normalized


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized or "UNSPECIFIED"


def shorten_identifier(value: str, limit: int = 48) -> str:
    slug = slugify(value)
    if len(slug) <= limit:
        return slug
    head = slug[: limit - 9].rstrip("-")
    tail = slug[-8:]
    return f"{head}-{tail}"


def summarize_text(value: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def guess_repo_root_from_input(input_path: Path) -> Path:
    parts = list(input_path.parts)
    for index, part in enumerate(parts):
        if part.lower() == "artifacts" and index > 0:
            return Path(*parts[:index])
    return input_path.parent


def resolve_input_artifacts_dir(input_value: str | Path, repo_root: Path) -> tuple[Path, dict[str, Any]]:
    candidate_path = Path(str(input_value))
    if candidate_path.exists() and candidate_path.is_dir():
        return candidate_path.resolve(), {"input_mode": "package_dir", "requested_ref": str(candidate_path.resolve())}

    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.lib.admission import validate_admission
    from cli.lib.fs import canonical_to_path
    from cli.lib.registry_store import resolve_registry_record

    requested_ref = str(input_value)
    admission = validate_admission(
        repo_root,
        consumer_ref="product.epic-to-feat",
        requested_ref=requested_ref,
    )
    record = resolve_registry_record(repo_root, requested_ref)
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    source_package_ref = str(metadata.get("source_package_ref") or "").strip()
    if not source_package_ref:
        raise ValueError("formal epic record is missing metadata.source_package_ref")
    artifacts_dir = canonical_to_path(source_package_ref, repo_root)
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        raise FileNotFoundError(f"resolved epic package directory not found: {artifacts_dir}")
    return artifacts_dir.resolve(), {
        "input_mode": "formal_admission",
        "requested_ref": requested_ref,
        "resolved_formal_ref": admission["resolved_formal_ref"],
        "managed_artifact_ref": record.get("managed_artifact_ref", ""),
        "resolved_epic_ref": str(metadata.get("assigned_id") or "").strip(),
        "resolved_src_ref": extract_src_ref(ensure_list(metadata.get("source_refs")), fallback=str(metadata.get("src_ref") or "")),
    }


def extract_src_ref(values: list[str], fallback: str = "") -> str:
    for value in values:
        normalized = str(value).strip().upper()
        if re.fullmatch(r"SRC-\d+", normalized):
            return normalized
        legacy_match = re.fullmatch(r"SRC(\d+)", normalized)
        if legacy_match:
            return f"SRC-{legacy_match.group(1)}"
        if normalized.startswith("SRC-"):
            return normalized
    for value in values:
        match = re.search(r"(SRC-\d+)", value.upper())
        if match:
            return match.group(1)
        legacy_match = re.search(r"(SRC)(\d+)", value.upper())
        if legacy_match:
            return f"SRC-{legacy_match.group(2)}"
        generic_match = re.search(r"(SRC-[A-Z0-9-]+)", value.upper())
        if generic_match:
            return generic_match.group(1)
    if fallback:
        match = re.search(r"(SRC-\d+)", fallback.upper())
        if match:
            return match.group(1)
        legacy_match = re.search(r"(SRC)(\d+)", fallback.upper())
        if legacy_match:
            return f"SRC-{legacy_match.group(2)}"
        generic_match = re.search(r"(SRC-[A-Z0-9-]+)", fallback.upper())
        if generic_match:
            return generic_match.group(1)
    return ""


def resolve_formal_lineage_refs(repo_root: Path, artifacts_dir: Path) -> dict[str, str]:
    implementation_root = Path(__file__).resolve().parents[3]
    if str(implementation_root) not in sys.path:
        sys.path.insert(0, str(implementation_root))
    from cli.lib.fs import to_canonical_path
    from cli.lib.registry_store import list_registry_records

    source_package_ref = to_canonical_path(artifacts_dir.resolve(), repo_root)
    resolved_epic_ref = ""
    resolved_src_ref = ""
    for record in list_registry_records(repo_root):
        metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
        if str(metadata.get("source_package_ref") or "").strip() != source_package_ref:
            continue
        assigned_id = str(metadata.get("assigned_id") or "").strip().upper()
        target_kind = str(metadata.get("target_kind") or "").strip().lower()
        if target_kind == "epic" and re.fullmatch(r"EPIC-SRC-\d+-\d+", assigned_id):
            resolved_epic_ref = assigned_id
            resolved_src_ref = extract_src_ref(ensure_list(metadata.get("source_refs")), fallback=str(metadata.get("src_ref") or ""))
            break
    return {"resolved_epic_ref": resolved_epic_ref, "resolved_src_ref": resolved_src_ref}


@dataclass
class EpicPackage:
    artifacts_dir: Path
    manifest: dict[str, Any]
    epic_json: dict[str, Any]
    epic_frontmatter: dict[str, Any]
    epic_markdown_body: str
    review_report: dict[str, Any]
    acceptance_report: dict[str, Any]
    defect_list: list[dict[str, Any]]
    execution_evidence: dict[str, Any]
    supervision_evidence: dict[str, Any]
    gate: dict[str, Any]
    handoff: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(
            self.epic_json.get("workflow_run_id")
            or self.manifest.get("run_id")
            or self.artifacts_dir.name
        )


def load_epic_package(artifacts_dir: Path) -> EpicPackage:
    markdown_text = (artifacts_dir / "epic-freeze.md").read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(markdown_text)
    return EpicPackage(
        artifacts_dir=artifacts_dir,
        manifest=load_json(artifacts_dir / "package-manifest.json"),
        epic_json=load_json(artifacts_dir / "epic-freeze.json"),
        epic_frontmatter=frontmatter,
        epic_markdown_body=body,
        review_report=load_json(artifacts_dir / "epic-review-report.json"),
        acceptance_report=load_json(artifacts_dir / "epic-acceptance-report.json"),
        defect_list=load_json(artifacts_dir / "epic-defect-list.json"),
        execution_evidence=load_json(artifacts_dir / "execution-evidence.json"),
        supervision_evidence=load_json(artifacts_dir / "supervision-evidence.json"),
        gate=load_json(artifacts_dir / "epic-freeze-gate.json"),
        handoff=load_json(artifacts_dir / "handoff-to-epic-to-feat.json"),
    )


def validate_input_package(input_value: str | Path, repo_root: Path) -> tuple[list[str], dict[str, Any]]:
    artifacts_dir, input_resolution = resolve_input_artifacts_dir(input_value, repo_root)
    errors: list[str] = []
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        return [f"Input package not found: {artifacts_dir}"], {"valid": False}

    for required_file in REQUIRED_INPUT_FILES:
        if not (artifacts_dir / required_file).exists():
            errors.append(f"Missing required input artifact: {required_file}")

    if errors:
        return errors, {"valid": False, "missing_files": errors}

    package = load_epic_package(artifacts_dir)

    artifact_type = str(package.epic_json.get("artifact_type") or "")
    if artifact_type != "epic_freeze_package":
        errors.append(f"epic-freeze.json artifact_type must be epic_freeze_package, got: {artifact_type or '<missing>'}")

    workflow_key = str(package.epic_json.get("workflow_key") or package.gate.get("workflow_key") or "")
    if workflow_key != "product.src-to-epic":
        errors.append(f"Upstream workflow must be product.src-to-epic, got: {workflow_key or '<missing>'}")

    status = str(package.epic_json.get("status") or package.manifest.get("status") or "")
    if status not in {"accepted", "frozen"}:
        errors.append(f"epic-freeze status must be accepted or frozen, got: {status or '<missing>'}")

    if package.gate.get("freeze_ready") is not True:
        errors.append("epic-freeze-gate.json must mark the package as freeze_ready.")

    handoff_target = str(package.handoff.get("to_skill") or "")
    if handoff_target and handoff_target != "product.epic-to-feat":
        errors.append(f"handoff target must be product.epic-to-feat when present, got: {handoff_target}")

    required_fields = [
        "artifact_type",
        "workflow_key",
        "workflow_run_id",
        "title",
        "status",
        "epic_freeze_ref",
        "src_root_id",
        "source_refs",
        "business_value_problem",
        "product_positioning",
        "actors_and_roles",
        "scope",
        "upstream_and_downstream",
        "epic_success_criteria",
        "non_goals",
        "decomposition_rules",
        "product_behavior_slices",
        "constraints_and_dependencies",
    ]
    for field in required_fields:
        if package.epic_json.get(field) in (None, "", []):
            errors.append(f"epic-freeze.json is missing required field: {field}")

    source_refs = ensure_list(package.epic_json.get("source_refs"))
    if not source_refs:
        errors.append("epic-freeze.json must include source_refs.")
    semantic_lock = normalize_semantic_lock(package.epic_json.get("semantic_lock") or package.epic_frontmatter.get("semantic_lock"))
    if semantic_lock:
        missing_fields = [field for field in SEMANTIC_LOCK_REQUIRED_FIELDS if not semantic_lock.get(field)]
        if missing_fields:
            errors.append(f"epic-freeze semantic_lock is missing required fields: {', '.join(missing_fields)}")
        if not semantic_lock.get("allowed_capabilities"):
            errors.append("epic-freeze semantic_lock must include allowed_capabilities.")
        if not semantic_lock.get("forbidden_capabilities"):
            errors.append("epic-freeze semantic_lock must include forbidden_capabilities.")

    src_ref = extract_src_ref(source_refs, fallback=str(package.epic_json.get("src_root_id") or ""))
    if not src_ref:
        errors.append("Input package must retain an SRC-* ref in source_refs or src_root_id.")

    if not ensure_list(package.epic_json.get("capability_axes")) and len(ensure_list(package.epic_json.get("scope"))) < 1:
        errors.append("Input package must provide capability_axes or a non-empty scope list.")

    result = {
        "valid": not errors,
        "input_mode": input_resolution["input_mode"],
        "requested_ref": input_resolution["requested_ref"],
        "resolved_formal_ref": input_resolution.get("resolved_formal_ref", ""),
        "workflow_key": workflow_key,
        "run_id": package.run_id,
        "status": status,
        "epic_freeze_ref": package.epic_json.get("epic_freeze_ref"),
        "src_root_id": package.epic_json.get("src_root_id"),
        "source_refs": source_refs,
        "src_ref": src_ref,
        "semantic_lock": semantic_lock,
    }
    return errors, result
