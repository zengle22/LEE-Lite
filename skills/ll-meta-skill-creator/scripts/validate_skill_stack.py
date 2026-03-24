#!/usr/bin/env python3
"""
Run standard skill validation and LL governed validation as a single stack.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def default_standard_validator() -> Path | None:
    codex_home = os.environ.get("CODEX_HOME")
    candidates = []
    if codex_home:
        candidates.append(Path(codex_home).expanduser() / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py")
    candidates.append(Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def governed_validator_path() -> Path:
    return Path(__file__).resolve().parent / "validate_lee_workflow_skill.py"


def run_validator(label: str, validator_path: Path, skill_path: Path) -> int:
    cmd = [sys.executable, str(validator_path), str(skill_path)]
    print(f"[RUN] {label}: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the standard and LL governed validators.")
    parser.add_argument("skill_path", help="Path to the skill directory")
    parser.add_argument("--standard-validator", help="Path to quick_validate.py")
    parser.add_argument("--skip-standard", action="store_true")
    parser.add_argument("--skip-governed", action="store_true")
    args = parser.parse_args()

    skill_path = Path(args.skill_path).resolve()
    if not skill_path.exists():
        print(f"[ERROR] Skill directory not found: {skill_path}")
        return 1

    failures = 0

    if not args.skip_standard:
        standard_validator = Path(args.standard_validator).resolve() if args.standard_validator else default_standard_validator()
        if standard_validator is None:
            print("[WARN] Standard validator not found. Skipping standard validation.")
        else:
            failures += 1 if run_validator("standard", standard_validator, skill_path) else 0

    if not args.skip_governed:
        if (skill_path / "ll.contract.yaml").exists():
            failures += 1 if run_validator("governed", governed_validator_path(), skill_path) else 0
        else:
            print("[WARN] ll.contract.yaml not found. Skipping governed validation.")

    if failures:
        print(f"[ERROR] Validation stack failed with {failures} failing validator(s).")
        return 1

    print("[OK] Validation stack passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
