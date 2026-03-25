from __future__ import annotations

import argparse
from pathlib import Path

from .checks_code import check_code_size_governance
from .checks_repo import check_repo_hygiene, check_ssot_governance
from .checks_runtime import build_cli_surface, check_cli_governance, check_cross_domain_compat, check_skill_governance
from .common import MANIFEST_DIR, ROOT, dump_json, read_changed_files
from .tests import run_test_manifest


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run repository CI validators.")
    sub = ap.add_subparsers(dest="command", required=True)

    def add_common(name: str) -> argparse.ArgumentParser:
        sp = sub.add_parser(name)
        sp.add_argument("--changed-files", type=Path)
        sp.add_argument("--output-dir", type=Path, required=True)
        return sp

    add_common("repo-hygiene")
    add_common("ssot-governance")
    code = add_common("code-size-governance")
    code.add_argument("--base-ref", required=True)
    skill = add_common("skill-governance")
    skill.add_argument("--run-tests", action="store_true")
    cli = add_common("cli-governance")
    cli.add_argument("--run-tests", action="store_true")
    cross = add_common("cross-domain-compat")
    cross.add_argument("--run-tests", action="store_true")

    test_manifest = sub.add_parser("run-test-manifest")
    test_manifest.add_argument("name")
    test_manifest.add_argument("--output-dir", type=Path, required=True)

    snapshot = sub.add_parser("emit-cli-snapshot")
    snapshot.add_argument("--output", type=Path, required=True)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "emit-cli-snapshot":
        dump_json(args.output, build_cli_surface())
        return 0

    if args.command == "run-test-manifest":
        return run_test_manifest(args.name, args.output_dir)

    changed_files = read_changed_files(args.changed_files)
    if not changed_files:
        changed_files = []

    if args.command == "repo-hygiene":
        return check_repo_hygiene(changed_files, args.output_dir)
    if args.command == "ssot-governance":
        return check_ssot_governance(changed_files, args.output_dir, MANIFEST_DIR / "ssot_object_registry.json")
    if args.command == "code-size-governance":
        return check_code_size_governance(changed_files, args.output_dir, args.base_ref)
    if args.command == "skill-governance":
        return check_skill_governance(changed_files, args.output_dir, args.run_tests, MANIFEST_DIR / "test_manifests.json")
    if args.command == "cli-governance":
        return check_cli_governance(
            changed_files,
            args.output_dir,
            MANIFEST_DIR / "cli_surface_snapshot.json",
            args.run_tests,
            MANIFEST_DIR / "test_manifests.json",
        )
    if args.command == "cross-domain-compat":
        return check_cross_domain_compat(changed_files, args.output_dir, MANIFEST_DIR / "dependency_rules.json", args.run_tests)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
