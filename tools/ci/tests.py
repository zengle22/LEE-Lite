from __future__ import annotations

from pathlib import Path

from .common import MANIFEST_DIR, load_json, run_pytest


def run_test_manifest(name: str, output_dir: Path) -> int:
    manifest = load_json(MANIFEST_DIR / "test_manifests.json")
    tests = manifest[name]
    exit_code, _ = run_pytest(tests, output_dir / f"{name}-pytest-report.json")
    return exit_code
