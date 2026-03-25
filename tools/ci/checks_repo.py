from __future__ import annotations

import re
from pathlib import Path

from .common import (
    ROOT,
    Violation,
    build_report,
    dump_json,
    is_json,
    is_markdown,
    is_yaml,
    list_repo_files,
    load_json,
    read_text,
)


ADR_REF_RE = re.compile(r"\bADR-\d{3}\b")
OBJECT_REF_RE = re.compile(r"\b(?:SRC|EPIC|FEAT|TECH|IMPL|TESTSET|ARCH|API|REL|RELEASE_NOTE)-[A-Z0-9-]+\b")


def check_repo_hygiene(changed_files: list[str], output_dir: Path) -> int:
    violations: list[Violation] = []
    banned_prefixes = (".local/", ".workflow/", ".lee/", ".artifacts/", ".project/", "artifacts/", "evidence/")
    banned_suffixes = (".pyc", ".pyo")

    for rel_path in changed_files:
        path = ROOT / rel_path
        if "__pycache__" in rel_path.split("/"):
            violations.append(Violation("repo-hygiene", "forbidden_generated_file", rel_path, "Generated __pycache__ content must not be committed."))
            continue
        if rel_path.endswith(banned_suffixes):
            violations.append(Violation("repo-hygiene", "forbidden_generated_file", rel_path, "Compiled Python residue must not be committed."))
            continue
        if rel_path.startswith(banned_prefixes):
            violations.append(Violation("repo-hygiene", "forbidden_runtime_state_commit", rel_path, "Runtime state paths are not allowed in tracked changes."))
            continue
        if not path.exists():
            continue
        if path.stat().st_size == 0:
            violations.append(Violation("repo-hygiene", "corrupt_or_empty_file", rel_path, "Tracked files must not be empty."))
            continue
        if is_json(rel_path):
            try:
                load_json(path)
            except Exception as exc:  # pragma: no cover - defensive
                violations.append(Violation("repo-hygiene", "parse_error", rel_path, f"Invalid JSON: {exc}"))
        elif is_yaml(rel_path):
            try:
                import yaml

                yaml.safe_load(read_text(path))
            except Exception as exc:  # pragma: no cover - defensive
                violations.append(Violation("repo-hygiene", "parse_error", rel_path, f"Invalid YAML: {exc}"))
        elif is_markdown(rel_path):
            try:
                text = read_text(path)
            except Exception as exc:  # pragma: no cover - defensive
                violations.append(Violation("repo-hygiene", "invalid_markdown_file", rel_path, f"Markdown could not be decoded as UTF-8: {exc}"))
                continue
            if not text.strip():
                violations.append(Violation("repo-hygiene", "invalid_markdown_file", rel_path, "Markdown files must not be empty."))

    dump_json(output_dir / "repo-hygiene-report.json", build_report("repo-hygiene", violations, {"changed_files": changed_files}))
    return 1 if violations else 0


def check_ssot_governance(changed_files: list[str], output_dir: Path, registry_path: Path) -> int:
    changed_ssot = [path for path in changed_files if path.startswith("ssot/")]
    registry = load_json(registry_path)
    objects = registry["objects"]
    allowed_dirs = {item["directory"]: item for item in objects}
    existing_files = list_repo_files()
    existing_adrs = {Path(path).stem.split("-")[1] for path in existing_files if path.startswith("ssot/adr/ADR-")}
    existing_refs = {
        Path(path).name.split("__", 1)[0]: path
        for path in existing_files
        if path.startswith("ssot/") and "__" in Path(path).name
    }
    violations: list[Violation] = []
    summaries: list[dict[str, str]] = []

    for rel_path in changed_ssot:
        path = ROOT / rel_path
        if not path.exists() or path.is_dir():
            continue
        parts = Path(rel_path).parts
        if len(parts) < 2:
            violations.append(Violation("ssot-governance", "invalid_object_path", rel_path, "SSOT files must live under a typed subdirectory."))
            continue
        top_dir = parts[1]
        if rel_path in {"ssot/README.md", "ssot/HISTORICAL-OBJECTS.md"}:
            continue
        if top_dir not in allowed_dirs:
            violations.append(Violation("ssot-governance", "unauthorized_object_kind", rel_path, f"Directory '{top_dir}' is not declared in the object registry."))
            continue
        descriptor = allowed_dirs[top_dir]
        file_name = Path(rel_path).name
        allow_any_nested = bool(descriptor.get("allow_any_nested")) and len(parts) > 3
        if not allow_any_nested and file_name.endswith((".md", ".MD", ".yaml", ".yml", ".json")) and not re.match(descriptor["filename_regex"], file_name):
            violations.append(Violation("ssot-governance", "identifier_drift", rel_path, "Filename does not match the declared registry pattern."))
        text = read_text(path)
        if top_dir == "adr":
            if "# ADR-" not in text and "# ADR：" not in text and "# ADR-" not in text.replace("：", ":"):
                violations.append(Violation("ssot-governance", "adr_metadata_missing", rel_path, "ADR files must contain an ADR heading."))
            for marker in ("状态：", "日期：", "相关 ADR："):
                if marker not in text:
                    violations.append(Violation("ssot-governance", "adr_metadata_missing", rel_path, f"ADR file is missing '{marker}'."))
        for adr_ref in ADR_REF_RE.findall(text):
            if adr_ref.split("-")[1] not in existing_adrs:
                violations.append(Violation("ssot-governance", "broken_reference", rel_path, f"Referenced ADR does not exist: {adr_ref}"))
        for obj_ref in OBJECT_REF_RE.findall(text):
            if obj_ref not in existing_refs:
                violations.append(Violation("ssot-governance", "broken_reference", rel_path, f"Referenced object does not exist: {obj_ref}"))
        summaries.append({"path": rel_path, "directory": top_dir, "classification": descriptor["classification"]})

    dump_json(output_dir / "ssot-change-summary.json", {"changed_ssot_files": summaries})
    dump_json(output_dir / "ssot-governance-report.json", build_report("ssot-governance", violations, {"changed_files": changed_ssot}))
    return 1 if violations else 0
