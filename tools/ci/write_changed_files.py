from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def resolve_base_ref(event_name: str, event_path: Path, fallback_head: str) -> str:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    if event_name == "pull_request":
        return event["pull_request"]["base"]["sha"]
    before = event.get("before")
    if before and before != "0" * 40:
        return before
    return fallback_head


def main() -> int:
    parser = argparse.ArgumentParser(description="Write changed files for the current GitHub event.")
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-output", type=Path)
    args = parser.parse_args()

    base_ref = resolve_base_ref(args.event_name, args.event_path, args.head_sha)
    command = ["git", "diff", "--name-only", base_ref, args.head_sha]
    if base_ref == args.head_sha:
        command = ["git", "ls-files"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(result.stderr, end="")
        return result.returncode
    args.output.write_text(result.stdout, encoding="utf-8")
    if args.base_output is not None:
        args.base_output.write_text(base_ref, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
