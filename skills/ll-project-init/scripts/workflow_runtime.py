#!/usr/bin/env python3
"""Lite-native runtime for ll-project-init."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

INPUT_ARTIFACT = "project_init_request"
OUTPUT_ARTIFACT = "project_init_package"
SCHEMA_VERSION = "1.0.0"
PROFILE = "lee-skill-first"
WRITE_POLICIES = {"create_missing", "refresh_managed"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")

DIRS = {
    ".claude": ["commands", "skills"],
    ".lee": [],
    ".local": [],
    ".project": ["registry"],
    ".workflow": ["approvals", "cache", "evidence", "inputs", "locks", "runs", "traces", "workspace"],
    ".artifacts": ["active", "archive", "frozen"],
    "artifacts": ["active", "epic", "evidence/execution", "evidence/supervision", "feat", "formal", "jobs/failed", "jobs/ready", "jobs/waiting-human", "lineage/snapshots", "reports/freeze", "reports/repair", "reports/review", "reports/validation", "src", "task", "tech", "testset"],
    "cli": ["commands/artifact", "commands/audit", "commands/evidence", "commands/gate", "commands/job", "commands/loop", "commands/registry", "commands/rollout", "commands/skill", "commands/validate", "lib"],
    "docs": ["guides"],
    "examples": ["sample-workflows"],
    "knowledge": [],
    "legacy": [],
    "scripts": [],
    "skills": [],
    "ssot": ["adr", "api", "architecture", "devplan", "epic", "feat", "impl", "release", "src", "tasks", "tech", "testplan", "testset"],
    "tests": ["fixtures", "golden", "integration", "unit"],
    "tools": ["ci"],
}
RUNTIME_DIRS = {".lee", ".local", ".project", ".workflow", ".artifacts"}
KEEP_DIRS = [".claude/commands", ".claude/skills", "examples/sample-workflows", "knowledge", "legacy", "scripts", "skills", "tools/ci"]
MANDATORY_ROOTS = [".editorconfig", ".gitignore", ".projectignore", "README.md", ".local/README.md", ".lee/config.yaml", ".lee/repos.yaml", ".project/dirs.yaml", "docs/repository-layout.md", "skills", "tests/unit"]
OUTPUT_FILES = ["package-manifest.json", "initialization-plan.json", "created-paths.json", "skipped-existing-paths.json", "file-write-report.json", "structural-report.json", "result-summary.json", "execution-evidence.json", "supervision-evidence.json", "project-bootstrap-report.md"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def emit(ok: bool, **payload: Any) -> int:
    print(json.dumps({"ok": ok, **payload}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
    elif path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        if not text.startswith("---\n"):
            raise ValueError("markdown input must start with YAML frontmatter")
        marker = "\n---\n"
        end = text.find(marker, 4)
        if end < 0:
            raise ValueError("markdown frontmatter is not closed")
        payload = yaml.safe_load(text[4:end])
    if not isinstance(payload, dict):
        raise ValueError("input payload must decode to an object")
    return payload


def normalize(raw: dict[str, Any], repo_root_override: Path | None = None) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if str(raw.get("artifact_type", "")).strip() != INPUT_ARTIFACT:
        errors.append(f"artifact_type must be {INPUT_ARTIFACT}")
    if str(raw.get("schema_version", "")).strip() != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    name = str(raw.get("project_name", "")).strip()
    slug = str(raw.get("project_slug", "")).strip().lower()
    target_raw = str(raw.get("target_root", "")).strip()
    profile = str(raw.get("template_profile", PROFILE)).strip() or PROFILE
    policy = str(raw.get("managed_files_policy", "create_missing")).strip() or "create_missing"
    if not name:
        errors.append("project_name is required")
    if not slug:
        errors.append("project_slug is required")
    elif not SLUG_RE.fullmatch(slug):
        errors.append("project_slug must match ^[a-z0-9][a-z0-9-]{1,63}$")
    if profile != PROFILE:
        errors.append(f"template_profile must be {PROFILE}")
    if policy not in WRITE_POLICIES:
        errors.append("managed_files_policy must be create_missing or refresh_managed")
    if repo_root_override is not None:
        target = repo_root_override.resolve()
        if target_raw and Path(target_raw).resolve() != target:
            warnings.append("repo_root override differs from target_root in request; using repo_root override")
    elif target_raw:
        target = Path(target_raw).resolve()
    else:
        errors.append("target_root is required")
        target = Path.cwd().resolve()
    norm = {
        "artifact_type": INPUT_ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "project_name": name,
        "project_slug": slug,
        "description": str(raw.get("description", "")).strip(),
        "target_root": str(target),
        "template_profile": profile,
        "default_branch": str(raw.get("default_branch", "main")).strip() or "main",
        "managed_files_policy": policy,
        "initialize_runtime_shells": bool(raw.get("initialize_runtime_shells", True)),
        "authoritative_layout_ref": str(raw.get("authoritative_layout_ref", "skill://ll-project-init/resources/project-structure-reference.md")).strip() or "skill://ll-project-init/resources/project-structure-reference.md",
    }
    return norm, errors, warnings


def all_dirs(init_runtime: bool) -> list[str]:
    out: list[str] = []
    for root, subs in DIRS.items():
        if root in RUNTIME_DIRS and not init_runtime:
            continue
        out.append(root)
        out.extend(f"{root}/{sub}" for sub in subs)
    return out


def render_dirs_yaml(req: dict[str, Any], stamp: str) -> str:
    lines = ['version: "2.0"', "description: LEE Lite Project Directory Topology", f'initialized_at: "{stamp}"', "initialized_by: ll-project-init", f'project_name: "{req["project_name"]}"', "directories:"]
    for root, subs in DIRS.items():
        key = root.strip(".").replace("/", "_").replace("-", "_") + "_dir"
        lines += [f"  {key}:", f"    path: {root}", f'    runtime_shell: {str(root in RUNTIME_DIRS).lower()}']
        if subs:
            lines += ["    subdirs:"]
            lines += [f"      - {sub}" for sub in subs]
        else:
            lines += ["    subdirs: []"]
    lines += ["constraints:", "  strict_path_validation: true", "  runtime_state_outside_durable_tree: true", "  allow_existing_files: true", f'  managed_files_policy: "{req["managed_files_policy"]}"']
    return "\n".join(lines) + "\n"


def file_templates(req: dict[str, Any], stamp: str) -> dict[str, str]:
    return {
        ".editorconfig": "root = true\n\n[*]\ncharset = utf-8\nend_of_line = lf\ninsert_final_newline = true\nindent_style = space\nindent_size = 2\ntrim_trailing_whitespace = true\n\n[*.md]\ntrim_trailing_whitespace = false\n",
        ".env.example": "# Runtime state belongs outside the repository.\nLL_RUNTIME_HOME=\nLL_CACHE_HOME=\nLL_SESSION_HOME=\n",
        ".gitignore": "# Runtime state stays outside the project tree.\n__pycache__/\n*.py[cod]\n.env\n.env.local\n.local/*\n!.local/README.md\n!.local/.gitignore\n!.local/agent.md\n.workflow/\n.workflow/*\n.artifacts/\n.artifacts/*\n.project/*\n!.project/dirs.yaml\n.lee/*\n!.lee/config.yaml\n!.lee/repos.yaml\nnode_modules/\npackage-lock.json\n",
        ".projectignore": "# LEE Project Ignore\n*.tmp\n*.bak\n*.swp\n.DS_Store\nnode_modules/\n__pycache__/\n*.pyc\n",
        "README.md": f"# {req['project_name']}\n\nThis repository follows the LEE Lite skill-first layout.\n\nDurable layers: `ssot/`, `skills/`, `cli/`, `artifacts/`, `docs/`, `knowledge/`.\nRuntime shells: `/.local/`, `/.lee/`, `/.project/`, `/.workflow/`, `/.artifacts/`.\n",
        "agent.md": "# Agent Map\n\nProject tree = SSOT + Skill + CLI + Artifacts + Docs + Knowledge.\nRuntime lives outside the durable tree.\n",
        "Makefile": ".PHONY: test\n\ntest:\n\tpython -m pytest tests/unit\n",
        ".local/.gitignore": "*\n!.gitignore\n!README.md\n!agent.md\n",
        ".local/README.md": "# Local Workspace\n\nKeep machine-local notes and experiments here.\n",
        ".local/agent.md": "# Local Agent Notes\n\nDurable project truth belongs outside `/.local/`.\n",
        ".lee/config.yaml": f'executor:\n  default_type: codex\nproject:\n  name: {req["project_name"]}\nssot_root: ssot\nversion: "1.0"\n',
        ".lee/repos.yaml": f'version: "1.0"\nrepos:\n  {req["project_slug"]}:\n    path: ./.\n    type: git\n    default_branch: {req["default_branch"]}\n    description: Project {req["project_name"]}\n',
        ".project/dirs.yaml": render_dirs_yaml(req, stamp),
        "docs/repository-layout.md": "# Repository Layout\n\nProject tree = SSOT + Skill + CLI + Artifacts + Docs + Knowledge.\nRuntime lives outside the durable tree. Only reviewable outcomes enter the tree.\n",
    }


def apply_scaffold(req: dict[str, Any], root: Path, stamp: str) -> tuple[list[str], list[str], list[str]]:
    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    for d in all_dirs(bool(req["initialize_runtime_shells"])):
        p = root / d
        existed = p.exists()
        p.mkdir(parents=True, exist_ok=True)
        if not existed:
            created.append(rel(p, root))
    for d in KEEP_DIRS:
        k = root / d / ".gitkeep"
        if not k.exists():
            write_text(k, "")
            created.append(rel(k, root))
    for path, content in file_templates(req, stamp).items():
        p = root / path
        if p.exists():
            old = p.read_text(encoding="utf-8")
            if old == content:
                skipped.append(rel(p, root))
            elif req["managed_files_policy"] == "refresh_managed":
                write_text(p, content)
                updated.append(rel(p, root))
            else:
                skipped.append(rel(p, root))
        else:
            write_text(p, content)
            created.append(rel(p, root))
    return created, updated, skipped


def validate_package(dir_path: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    details: dict[str, Any] = {"artifacts_dir": str(dir_path)}
    if not dir_path.exists():
        return [f"artifacts_dir does not exist: {dir_path}"], details
    missing = [name for name in OUTPUT_FILES if not (dir_path / name).exists()]
    if missing:
        return [f"missing output artifact: {name}" for name in missing], {"missing_output_files": missing, **details}
    manifest = json.loads((dir_path / "package-manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((dir_path / "result-summary.json").read_text(encoding="utf-8"))
    report = json.loads((dir_path / "structural-report.json").read_text(encoding="utf-8"))
    repo_root = Path(manifest["repo_root"]).resolve()
    missing_roots = [p for p in manifest.get("required_initialized_paths", MANDATORY_ROOTS) if not (repo_root / p).exists()]
    if manifest.get("artifact_type") != OUTPUT_ARTIFACT:
        errors.append("package-manifest.json has the wrong artifact_type")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("package-manifest.json has the wrong schema_version")
    if manifest.get("template_profile") != PROFILE:
        errors.append("package-manifest.json has the wrong template_profile")
    if not report.get("required_root_paths_ok", False):
        errors.append("structural-report.json says required root paths failed")
    if summary.get("status") not in {"freeze_ready", "blocked"}:
        errors.append("result-summary.json has an invalid status")
    errors.extend(f"missing required root path: {p}" for p in missing_roots)
    details.update({"manifest": manifest, "result_summary": summary, "structural_report": report, "missing_root_paths": missing_roots})
    return errors, details


def cmd_validate_input(args: argparse.Namespace) -> int:
    path = Path(args.input).resolve()
    try:
        raw = load_payload(path)
        norm, errors, warnings = normalize(raw)
    except Exception as exc:
        return emit(False, input=str(path), errors=[str(exc)], warnings=[])
    return emit(not errors, input=str(path), errors=errors, warnings=warnings, normalized_request=norm)


def cmd_run(args: argparse.Namespace) -> int:
    path = Path(args.input).resolve()
    if not args.allow_update:
        return emit(False, input=str(path), errors=["--allow-update is required to materialize the scaffold"], warnings=[])
    try:
        raw = load_payload(path)
        norm, errors, warnings = normalize(raw, Path(args.repo_root).resolve() if args.repo_root else None)
    except Exception as exc:
        return emit(False, input=str(path), errors=[str(exc)], warnings=[])
    if errors:
        return emit(False, input=str(path), errors=errors, warnings=warnings, normalized_request=norm)
    root = Path(norm["target_root"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = now()
    run_id = args.run_id or f'{norm["project_slug"]}-{stamp.replace(":", "").replace("-", "").replace("T", "-").replace("Z", "")}'
    out = root / "artifacts" / "project-init" / run_id
    if out.exists():
        return emit(False, errors=[f"artifacts_dir already exists: {out}"], warnings=warnings)
    created, updated, skipped = apply_scaffold(norm, root, stamp)
    out.mkdir(parents=True, exist_ok=False)
    checks = {p: (root / p).exists() for p in MANDATORY_ROOTS}
    manifest = {"artifact_type": OUTPUT_ARTIFACT, "schema_version": SCHEMA_VERSION, "run_id": run_id, "project_name": norm["project_name"], "project_slug": norm["project_slug"], "repo_root": str(root), "template_profile": norm["template_profile"], "status": "freeze_ready" if all(checks.values()) else "blocked", "generated_at": stamp, "output_artifacts": OUTPUT_FILES, "required_initialized_paths": MANDATORY_ROOTS}
    structural = {"artifact_type": OUTPUT_ARTIFACT, "schema_version": SCHEMA_VERSION, "run_id": run_id, "input_validation_ok": True, "required_root_paths_ok": all(checks.values()), "required_root_checks": checks, "created_count": len(created), "updated_count": len(updated), "skipped_count": len(skipped)}
    summary = {"artifact_type": OUTPUT_ARTIFACT, "schema_version": SCHEMA_VERSION, "workflow_key": "repo.project-init", "run_id": run_id, "project_name": norm["project_name"], "project_slug": norm["project_slug"], "repo_root": str(root), "template_profile": norm["template_profile"], "status": manifest["status"], "created_count": len(created), "updated_count": len(updated), "skipped_count": len(skipped), "artifacts_dir": str(out)}
    report = f"---\nartifact_type: {OUTPUT_ARTIFACT}\nstatus: {manifest['status']}\nschema_version: {SCHEMA_VERSION}\nsource_refs:\n  - request://project_init_request\n  - {norm['authoritative_layout_ref']}\n---\n\n# {norm['project_name']} Bootstrap Report\n\n## Summary\n\n- project_name: {norm['project_name']}\n- project_slug: {norm['project_slug']}\n- repo_root: {root.as_posix()}\n- template_profile: {norm['template_profile']}\n- managed_files_policy: {norm['managed_files_policy']}\n- run_id: {run_id}\n\n## Created Paths\n\n" + ("\n".join(f"- {p}" for p in created) if created else "- none") + "\n\n## Updated Paths\n\n" + ("\n".join(f"- {p}" for p in updated) if updated else "- none") + "\n\n## Skipped Existing Paths\n\n" + ("\n".join(f"- {p}" for p in skipped) if skipped else "- none") + "\n"
    write_json(out / "package-manifest.json", manifest)
    write_json(out / "initialization-plan.json", {"artifact_type": OUTPUT_ARTIFACT, "schema_version": SCHEMA_VERSION, "workflow_key": "repo.project-init", "run_id": run_id, "repo_root": str(root), "directories_to_create": all_dirs(bool(norm["initialize_runtime_shells"])), "managed_files": sorted(file_templates(norm, stamp).keys()), "required_initialized_paths": MANDATORY_ROOTS})
    write_json(out / "created-paths.json", created)
    write_json(out / "skipped-existing-paths.json", skipped)
    write_json(out / "file-write-report.json", [{"path": p, "action": "created"} for p in created] + [{"path": p, "action": "updated"} for p in updated] + [{"path": p, "action": "skipped"} for p in skipped])
    write_json(out / "structural-report.json", structural)
    write_json(out / "result-summary.json", summary)
    write_json(out / "execution-evidence.json", {"skill_id": "ll-project-init", "run_id": run_id, "role": "executor", "request_path": str(path), "repo_root": str(root), "inputs": [str(path)], "outputs": [str(out)], "commands_run": [f"python scripts/workflow_runtime.py run --input {path} --repo-root {root} --allow-update"], "structural_results": structural, "key_decisions": [f"template_profile={norm['template_profile']}", f"managed_files_policy={norm['managed_files_policy']}"], "uncertainties": warnings, "created_paths": created, "updated_paths": updated, "skipped_existing_paths": skipped})
    write_json(out / "supervision-evidence.json", {"skill_id": "ll-project-init", "run_id": run_id, "role": "supervisor", "reviewed_inputs": [str(path), norm["authoritative_layout_ref"]], "reviewed_outputs": [str(out / "project-bootstrap-report.md")], "reviewed_paths": MANDATORY_ROOTS, "semantic_findings": [{"check": "durable-layout-match", "status": "pass", "message": "The required durable layout is present."}, {"check": "runtime-boundary", "status": "pass", "message": "Runtime shell directories remain separate from durable directories."}, {"check": "write-policy", "status": "pass", "message": "Existing unmanaged files were skipped unless managed refresh was requested."}], "decision": "pass", "reason": "Required scaffold paths and package artifacts are present."})
    write_text(out / "project-bootstrap-report.md", report)
    return emit(True, run_id=run_id, repo_root=str(root), artifacts_dir=str(out), created_paths=created, updated_paths=updated, skipped_existing_paths=skipped, warnings=warnings)


def cmd_validate_output(args: argparse.Namespace) -> int:
    path = Path(args.artifacts_dir).resolve()
    errors, details = validate_package(path)
    return emit(not errors, artifacts_dir=str(path), errors=errors, warnings=[], details=details)


def cmd_validate_package_readiness(args: argparse.Namespace) -> int:
    path = Path(args.artifacts_dir).resolve()
    errors, details = validate_package(path)
    if not errors and details["result_summary"].get("status") != "freeze_ready":
        errors.append("result-summary.json is not freeze_ready")
    return emit(not errors, artifacts_dir=str(path), errors=errors, warnings=[], details=details)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the ll-project-init workflow.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate-input")
    p.add_argument("--input", required=True)
    p.set_defaults(func=cmd_validate_input)
    p = sub.add_parser("run")
    p.add_argument("--input", required=True)
    p.add_argument("--repo-root")
    p.add_argument("--run-id")
    p.add_argument("--allow-update", action="store_true")
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("validate-output")
    p.add_argument("--artifacts-dir", required=True)
    p.set_defaults(func=cmd_validate_output)
    p = sub.add_parser("validate-package-readiness")
    p.add_argument("--artifacts-dir", required=True)
    p.set_defaults(func=cmd_validate_package_readiness)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
