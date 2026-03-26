"""Snapshot and metadata helpers for formal publication."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from cli.lib.errors import ensure
from cli.lib.fs import canonical_to_path, load_json, read_text, to_canonical_path
from cli.lib.registry_store import slugify


def candidate_source_path(workspace_root: Path, candidate: dict[str, Any]) -> Path:
    source_path = canonical_to_path(str(candidate["managed_artifact_ref"]), workspace_root)
    ensure(source_path.exists(), "PRECONDITION_FAILED", f"candidate managed artifact not found: {source_path}")
    return source_path


def run_ref_for(candidate: dict[str, Any], source_path: Path) -> str:
    trace = candidate.get("trace", {})
    if isinstance(trace, dict):
        run_ref = str(trace.get("run_ref", "")).strip()
        if run_ref:
            return slugify(run_ref)
    if source_path.parent.name:
        return slugify(source_path.parent.name)
    return slugify(str(candidate["artifact_ref"]))


def parse_frontmatter(markdown_text: str) -> tuple[dict[str, Any], str]:
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


def extract_first_heading(markdown_body: str) -> str:
    for line in markdown_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def read_candidate_snapshot(workspace_root: Path, source_path: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    markdown_path = source_path
    json_path: Path | None = None
    if source_path.suffix.lower() == ".json":
        json_path = source_path
        sibling_markdown = source_path.with_suffix(".md")
        if sibling_markdown.exists():
            markdown_path = sibling_markdown
    else:
        sibling_json = source_path.with_suffix(".json")
        if sibling_json.exists():
            json_path = sibling_json
    candidate_json = load_json(json_path) if json_path and json_path.exists() else {}
    markdown_text = read_text(markdown_path) if markdown_path.exists() else ""
    frontmatter, body = parse_frontmatter(markdown_text)
    title = (
        str(candidate_json.get("title") or "").strip()
        or str(frontmatter.get("title") or "").strip()
        or extract_first_heading(body)
        or markdown_path.stem
    )
    workflow_key = (
        str(candidate_json.get("workflow_key") or "").strip()
        or str(frontmatter.get("workflow_key") or "").strip()
        or str(candidate.get("trace", {}).get("workflow_key") or "").strip()
    )
    workflow_run_id = (
        str(candidate_json.get("workflow_run_id") or "").strip()
        or str(frontmatter.get("workflow_run_id") or "").strip()
        or str(candidate.get("trace", {}).get("run_ref") or "").strip()
    )
    source_kind = (
        str(candidate_json.get("source_kind") or "").strip()
        or str(frontmatter.get("source_kind") or "").strip()
        or "raw_requirement"
    )
    version = str(frontmatter.get("version") or candidate_json.get("version") or "v1").strip() or "v1"
    body_text = body.strip() if body.strip() else markdown_text.strip()
    if not body_text.startswith("# "):
        body_text = f"# {title}\n\n{body_text}".strip()
    candidate_package_ref = to_canonical_path(markdown_path.parent, workspace_root)
    lineage_candidate = markdown_path.parent / "patch-lineage.json"
    workflow_lineage_ref = (
        to_canonical_path(lineage_candidate, workspace_root)
        if lineage_candidate.exists()
        else candidate_package_ref
    )
    acceptance_summary = ""
    acceptance_path = markdown_path.parent / "epic-acceptance-report.json"
    if acceptance_path.exists():
        acceptance_summary = str(load_json(acceptance_path).get("summary") or "").strip()
    return {
        "title": title,
        "workflow_key": workflow_key,
        "workflow_run_id": workflow_run_id,
        "source_kind": source_kind,
        "source_refs": normalize_list(candidate_json.get("source_refs") or frontmatter.get("source_refs")),
        "version": version,
        "body": body_text.rstrip() + "\n",
        "candidate_package_ref": candidate_package_ref,
        "workflow_lineage_ref": workflow_lineage_ref,
        "candidate_json": candidate_json,
        "frontmatter": frontmatter,
        "acceptance_summary": acceptance_summary,
    }


def compliant_src_path(path: Path, workspace_root: Path) -> bool:
    canonical = to_canonical_path(path, workspace_root)
    return canonical.startswith("ssot/src/SRC-") and path.suffix.lower() == ".md"


def compliant_epic_path(path: Path, workspace_root: Path) -> bool:
    canonical = to_canonical_path(path, workspace_root)
    return canonical.startswith("ssot/epic/EPIC-") and path.suffix.lower() == ".md"


def compliant_feat_path(path: Path, workspace_root: Path) -> bool:
    canonical = to_canonical_path(path, workspace_root)
    return canonical.startswith("ssot/feat/FEAT-") and path.suffix.lower() == ".md"


def compliant_tech_path(path: Path, workspace_root: Path) -> bool:
    canonical = to_canonical_path(path, workspace_root)
    return canonical.startswith("ssot/tech/") and path.name.startswith("TECH-") and path.suffix.lower() == ".md"


def compliant_testset_path(path: Path, workspace_root: Path) -> bool:
    canonical = to_canonical_path(path, workspace_root)
    return canonical.startswith("ssot/testset/TESTSET-") and path.suffix.lower() in {".yaml", ".yml"}


def compliant_impl_path(path: Path, workspace_root: Path) -> bool:
    canonical = to_canonical_path(path, workspace_root)
    return canonical.startswith("ssot/impl/IMPL-") and path.suffix.lower() == ".md"


def assigned_id_from_path(path: Path) -> str:
    match = re.match(r"^([A-Z]+-[A-Z0-9-]+)", path.name, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def extract_src_ref(values: list[str], fallback: str = "") -> str:
    for value in values:
        normalized = str(value).strip().upper()
        if re.fullmatch(r"SRC-\d+", normalized):
            return normalized
    for value in values:
        match = re.search(r"(SRC-\d+)", str(value).upper())
        if match:
            return match.group(1)
    if fallback:
        fallback_match = re.search(r"(SRC-\d+)", str(fallback).upper())
        if fallback_match:
            return fallback_match.group(1)
    return ""


def _next_suffix_for_pattern(directory: Path, pattern: str, regex: str) -> int:
    highest = 0
    if directory.exists():
        for path in directory.glob(pattern):
            match = re.match(regex, path.name, re.IGNORECASE)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def next_src_id(workspace_root: Path) -> str:
    src_dir = workspace_root / "ssot" / "src"
    highest = 0
    if src_dir.exists():
        for path in src_dir.glob("SRC-*.md"):
            match = re.match(r"^SRC-(\d+)", path.name, re.IGNORECASE)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"SRC-{highest + 1:03d}"


def next_epic_id(workspace_root: Path, src_ref: str) -> str:
    epic_dir = workspace_root / "ssot" / "epic"
    prefix = f"EPIC-{src_ref.upper()}-"
    next_suffix = _next_suffix_for_pattern(
        epic_dir,
        f"{prefix}*.md",
        rf"^{re.escape(prefix)}(\d+)",
    )
    return f"{prefix}{next_suffix:03d}"


def extract_numeric_src_ref(values: list[str], fallback: str = "") -> str:
    for value in values:
        normalized = str(value or "").strip().upper()
        if re.fullmatch(r"SRC-\d+", normalized):
            return normalized
        legacy_match = re.fullmatch(r"SRC(\d+)", normalized)
        if legacy_match:
            return f"SRC-{legacy_match.group(1)}"
    for value in values:
        match = re.search(r"(SRC-\d+)", str(value or "").upper())
        if match:
            return match.group(1)
        legacy_match = re.search(r"(SRC)(\d+)", str(value or "").upper())
        if legacy_match:
            return f"SRC-{legacy_match.group(2)}"
    if fallback:
        match = re.search(r"(SRC-\d+)", str(fallback).upper())
        if match:
            return match.group(1)
        legacy_match = re.search(r"(SRC)(\d+)", str(fallback).upper())
        if legacy_match:
            return f"SRC-{legacy_match.group(2)}"
    return ""


def next_epic_lineage_id(workspace_root: Path, src_ref: str) -> str:
    src_ref = str(src_ref or "").strip().upper()
    ensure(re.fullmatch(r"SRC-\d+", src_ref), "PRECONDITION_FAILED", f"invalid src_ref for epic lineage: {src_ref}")
    epic_dir = workspace_root / "ssot" / "epic"
    highest = 0
    if epic_dir.exists():
        pattern = re.compile(rf"^EPIC-{re.escape(src_ref)}-(\d+)", re.IGNORECASE)
        for path in epic_dir.glob(f"EPIC-{src_ref}-*.md"):
            match = pattern.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"EPIC-{src_ref}-{highest + 1:03d}"


def formal_src_output_path(workspace_root: Path, assigned_id: str, title: str) -> Path:
    return workspace_root / "ssot" / "src" / f"{assigned_id}__{slugify(title)}.md"


def normalized_publication_slug(title: str, assigned_id: str) -> str:
    ascii_slug = re.sub(r"[^A-Za-z0-9]+", "-", str(title or "")).strip("-").lower()
    ascii_slug = re.sub(r"-{2,}", "-", ascii_slug)
    if ascii_slug:
        return ascii_slug
    parts = [part.lower() for part in re.split(r"[^A-Za-z0-9]+", str(assigned_id or "")) if part]
    if parts[:2] == ["release", "note"]:
        parts = parts[2:]
    elif parts and parts[0] in {"src", "epic", "feat", "tech", "api", "impl", "testset", "ui", "release_note"}:
        parts = parts[1:]
    fallback = "-".join(parts).strip("-")
    return fallback or "artifact"


def formal_epic_output_path(workspace_root: Path, assigned_id: str, title: str) -> Path:
    return workspace_root / "ssot" / "epic" / f"{assigned_id}__{normalized_publication_slug(title, assigned_id)}.md"


def formal_feat_output_path(workspace_root: Path, assigned_id: str, title: str) -> Path:
    return workspace_root / "ssot" / "feat" / f"{assigned_id}__{slugify(title)}.md"


def formal_tech_output_path(workspace_root: Path, assigned_id: str, title: str, source_refs: list[str]) -> Path:
    src_ref = next((ref for ref in source_refs if str(ref).startswith("SRC-")), "")
    if src_ref:
        return workspace_root / "ssot" / "tech" / src_ref / f"{assigned_id}__{slugify(title)}.md"
    return workspace_root / "ssot" / "tech" / f"{assigned_id}__{slugify(title)}.md"


def formal_testset_output_path(workspace_root: Path, assigned_id: str, title: str) -> Path:
    return workspace_root / "ssot" / "testset" / f"{assigned_id}__{slugify(title)}.yaml"


def formal_impl_output_path(workspace_root: Path, assigned_id: str, title: str) -> Path:
    return workspace_root / "ssot" / "impl" / f"{assigned_id}__{slugify(title)}.md"


def infer_target_formal_kind(candidate: dict[str, Any], source_path: Path, requested_kind: str | None) -> str:
    requested = str(requested_kind or "").strip().lower()
    if requested:
        return requested
    artifact_ref = str(candidate.get("artifact_ref") or "").strip().lower()
    managed_artifact_ref = str(candidate.get("managed_artifact_ref") or "").strip().lower()
    source_kind = str(candidate.get("trace", {}).get("source_kind") or "").strip().lower()
    source_text = f"{source_path.name} {source_path.parent.name}".lower()
    explicit_feat_markers = ["feat-freeze", "feat_freeze", "epic-to-feat", ".feat."]
    explicit_epic_markers = ["epic-freeze", "epic_freeze", "src-to-epic", ".epic."]
    explicit_src_markers = ["src-candidate", "src_candidate", "raw-to-src", ".src."]
    explicit_tech_markers = ["tech-design-bundle", "tech_design_package", "feat-to-tech", ".tech."]
    explicit_testset_markers = ["test-set-bundle", "test_set_candidate_package", "feat-to-testset", ".testset."]
    explicit_impl_markers = ["impl-bundle", "feature_impl_candidate_package", "tech-to-impl", ".impl."]
    values = [artifact_ref, managed_artifact_ref, source_kind, source_text]
    for value in values:
        if any(marker in value for marker in explicit_feat_markers):
            return "feat"
        if any(marker in value for marker in explicit_epic_markers):
            return "epic"
        if any(marker in value for marker in explicit_src_markers):
            return "src"
        if any(marker in value for marker in explicit_tech_markers):
            return "tech"
        if any(marker in value for marker in explicit_testset_markers):
            return "testset"
        if any(marker in value for marker in explicit_impl_markers):
            return "impl"
    for value in values:
        if "feat" in value:
            return "feat"
        if "epic" in value:
            return "epic"
        if "src" in value:
            return "src"
        if "tech" in value:
            return "tech"
        if "testset" in value or "test-set" in value:
            return "testset"
        if "impl" in value:
            return "impl"
    return "src"


def default_formal_ref(target_kind: str) -> str:
    return f"formal.{target_kind}"


def metadata_for(
    workspace_root: Path,
    candidate: dict[str, Any],
    source_path: Path,
    target_kind: str,
    published_ref: str,
    *,
    assigned_id: str = "",
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = read_candidate_snapshot(workspace_root, source_path, candidate)
    metadata: dict[str, Any] = {
        "target_kind": target_kind,
        "published_ref": published_ref,
        "source_run_id": snapshot["workflow_run_id"],
        "source_skill": snapshot["workflow_key"],
        "candidate_package_ref": snapshot["candidate_package_ref"],
        "source_package_ref": snapshot["candidate_package_ref"],
        "workflow_lineage_ref": snapshot["workflow_lineage_ref"],
        "source_refs": snapshot["source_refs"],
        "source_kind": snapshot["source_kind"],
    }
    if assigned_id:
        metadata["assigned_id"] = assigned_id
    if snapshot["acceptance_summary"]:
        metadata["acceptance_summary"] = snapshot["acceptance_summary"]
    if extra_metadata:
        metadata.update(extra_metadata)
    return metadata
